"""Control parity, causal partitions and replay restart through public raw quotes."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.elliott_full import controls as c
from forex_demo_lab.elliott_full.contracts import digest
from forex_demo_lab.elliott_execution_fixture_125 import fixture
from test_elliott_execution_125 import audit_account
from test_daily_fills_120 import audit_ledger


class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.TemporaryDirectory()
        cls.root = Path(cls.home.name)
        cls.cache = {}

    @classmethod
    def tearDownClass(cls):
        cls.home.cleanup()

    def frozen(self, case="long_target", value=None):
        home = Path(tempfile.mkdtemp(dir=self.root))
        path, manifest = home/"input.json", home/"freeze.json"
        c.daily.write_new(path, fixture(case) if value is None else value)
        c.freeze(path, manifest)
        return path, manifest, home

    def prepared(self, case="long_target", partition="development"):
        key = case, partition
        if key not in self.cache:
            path, manifest, home = self.frozen(case)
            c.prepare(path, manifest, partition, home/"prepared")
            self.cache[key] = home/"prepared"
        return self.cache[key]

    def original(self, directory, candidate, profile):
        if candidate == "EWPB_D124":
            return c.old_elliott.Account(directory/"compiled-input.json", directory/"compiled-frozen.json", profile, candidate)
        return c.fills.Replay(directory/"control-fills-input.json", directory/"control-fills-frozen.json", profile, candidate)

    def test_original_reports_and_independent_accounting_both_sides_profiles(self):
        for case in ("long_target", "short_target", "long_gap", "short_gap", "wide_exit", "quote_guards"):
            directory = self.prepared(case)
            for profile in c.PROFILES:
                for candidate in c.CANDIDATES:
                    with self.subTest(case=case, profile=profile, candidate=candidate):
                        wrapped = c.ControlReplay(directory, candidate, profile)
                        report = wrapped.run()
                        direct = self.original(directory, candidate, profile)
                        self.assertEqual(direct.run(), report["original_report"])
                        auditor = audit_account if candidate == "EWPB_D124" else audit_ledger
                        auditor(direct._fixture, report["original_report"])
                        self.assertEqual(direct.state, wrapped.state)
                        self.assertFalse(report["orders_available"])
                        self.assertFalse(report["market_data_qualified"])
                        if candidate == "CASH":
                            self.assertEqual("10000", report["summary"]["final_cash_usd"])
                            self.assertFalse(wrapped.state["ledger"])

    def test_preserved_target_and_gap_results_are_not_strategy_reselection(self):
        target = c.ControlReplay(self.prepared(), "EWPB_D124").run()
        self.assertEqual(Fraction("48.54"), Fraction(target["summary"]["toy_net_usd"]))
        for candidate in ("EWPB_D124", "T12_D"):
            loss = c.ControlReplay(self.prepared("long_gap"), candidate).run()
            self.assertLess(Fraction(loss["summary"]["toy_net_usd"]), 0)
            state = loss["original_report"]["final_state"]
            self.assertTrue(any(e["kind"] == "exit_fill" and e["reason"] == "stop" for e in state["ledger"]))

    def test_checkpoint_before_entry_while_held_and_after_finish(self):
        directory = self.prepared()
        for candidate in c.CANDIDATES:
            for profile in c.PROFILES:
                with self.subTest(candidate=candidate, profile=profile):
                    replay = c.ControlReplay(directory, candidate, profile)
                    self.assertEqual(replay.state, c.ControlReplay.restore(directory, replay.checkpoint()).state)
                    saw_held = False
                    while replay.step():
                        if replay.state["held"] is not None:
                            saw_held = True
                            break
                    checkpoint = replay.checkpoint()
                    resumed = c.ControlReplay.restore(directory, checkpoint)
                    self.assertEqual(replay.state, resumed.state)
                    self.assertEqual(replay.run(), resumed.run())
                    final = resumed.checkpoint()
                    restored = c.ControlReplay.restore(directory, final)
                    self.assertEqual(final, restored.checkpoint())
                    self.assertFalse(restored.finish())
                    self.assertEqual(resumed.report(), restored.run())
                    self.assertEqual(candidate != "CASH", saw_held)

    def test_forged_checkpoint_state_rejected_even_with_both_hashes_rebuilt(self):
        directory = self.prepared()
        for candidate in c.CANDIDATES:
            replay = c.ControlReplay(directory, candidate)
            replay.step()
            cp = replay.checkpoint()
            legacy = cp["payload"]["original_checkpoint"]
            inner = c.daily._json(legacy) if type(legacy) is str else legacy
            inner["payload"]["state"]["balance_usd"] = "1000000"
            inner["sha256"] = c.daily._digest(inner["payload"])
            cp["payload"]["original_checkpoint"] = json.dumps(inner) if type(legacy) is str else inner
            cp["digest"] = digest(cp["payload"])
            with self.assertRaisesRegex(ValueError, "reconstructed_state"):
                c.ControlReplay.restore(directory, cp)

    def test_cross_partition_checkpoint_and_wrong_source_revision_reject(self):
        directory = self.prepared()
        cp = c.ControlReplay(directory, "T12_D").checkpoint()
        with self.assertRaisesRegex(ValueError, "checkpoint_partition"):
            c.ControlReplay.restore(self.prepared(partition="later_validation"), cp)
        cp["payload"]["sources"]["current"]["controls.py"] = "0"*64
        cp["digest"] = digest(cp["payload"])
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            c.ControlReplay.restore(directory, cp)

    def test_duplicate_and_conflicting_events_do_not_change_account_state(self):
        directory = self.prepared()
        for candidate in c.CANDIDATES:
            replay = c.ControlReplay(directory, candidate)
            first = replay.events[0]
            replay.step(first)
            state = replay.state
            self.assertFalse(replay.step(first))
            self.assertEqual(state, replay.state)
            bad = {**first, "bid": first["bid"]-0.00001}
            with self.assertRaisesRegex(ValueError, "event_binding"):
                replay.step(bad)
            self.assertEqual(state, replay.state)

    def test_later_prices_cannot_change_development_economics(self):
        value = fixture()
        cut = value["partitions"][0]["end_msc"]
        for message in value["stream"]["messages"]:
            if message["kind"] == "quote" and message["source_msc"] >= cut:
                message["bid"] *= 1.7
                message["ask"] *= 1.7
        path, manifest, home = self.frozen(value=value)
        c.prepare(path, manifest, "development", home/"prepared")
        for candidate in c.CANDIDATES:
            original = c.ControlReplay(self.prepared(), candidate).run()
            changed = c.ControlReplay(home/"prepared", candidate).run()
            # Freeze timestamps and whole-input provenance legitimately differ.
            # The development economic path and as-known-then decisions must not.
            self.assertEqual(original["summary"], changed["summary"])
            self.assertEqual(original["original_report"]["final_state"], changed["original_report"]["final_state"])

    def test_each_partition_starts_fresh_and_retains_same_quote_stream(self):
        for partition in ("development", "later_validation"):
            directory = self.prepared(partition=partition)
            expected = None
            for candidate in c.CANDIDATES:
                replay = c.ControlReplay(directory, candidate)
                self.assertEqual("10000", replay.state["balance_usd"])
                self.assertFalse(replay.state["held"])
                self.assertFalse(replay.state["paused"])
                quote_fields = [{k:e[k] for k in ("sequence", "source_msc", "receipt_msc", "bid", "ask")} for e in replay.events]
                if expected is None:
                    expected = quote_fields
                self.assertEqual(expected, quote_fields)
                self.assertTrue(all(e["source_msc"] >= replay.prepared["partition"]["start_msc"] for e in quote_fields))

    def test_missing_stale_and_repeated_endpoints_unavailable_even_for_cash(self):
        for case in ("missing_endpoint", "stale_endpoint"):
            path, manifest, home = self.frozen(case)
            with self.assertRaisesRegex(ValueError, "endpoint"):
                c.prepare(path, manifest, "development", home/"prepared")
        value = fixture()
        end = value["partitions"][0]["end_msc"]
        messages = value["stream"]["messages"]
        index = max(i for i,m in enumerate(messages) if m["kind"] == "quote" and m["receipt_msc"] < end)
        repeated = {**messages[index], "receipt_msc": messages[index]["receipt_msc"]+1}
        messages.insert(index+1, repeated)
        for i,m in enumerate(messages):
            m["sequence"] = i
        path, manifest, home = self.frozen(value=value)
        with self.assertRaisesRegex(ValueError, "invalid_endpoint_quote"):
            c.prepare(path, manifest, "development", home/"prepared")

    def test_all_declared_cells_retained_and_market_results_unavailable(self):
        path, manifest, home = self.frozen()
        report = c.evaluate(path, manifest, home/"run")
        self.assertEqual(16, len(report["cells"]))
        self.assertEqual(12, report["computed_control_cells"])
        self.assertEqual(0, report["market_cells_run"])
        self.assertFalse(report["capital_summed_as_portfolio"])
        self.assertTrue(all(r["market_status"] == "UNAVAILABLE" and r["market_returns"] is None for r in report["cells"]))
        self.assertEqual(4, sum(r["invented_status"] == "unavailable" for r in report["cells"]))
        with self.assertRaises(FileExistsError):
            c.evaluate(path, manifest, home/"run")

    def test_input_and_manifest_mutations_rejected_before_replay(self):
        path, manifest, home = self.frozen()
        frozen = c.daily._json(manifest.read_bytes())
        frozen["orders_available"] = 0
        manifest.write_text(json.dumps(frozen))
        with self.assertRaisesRegex(ValueError, "freeze_binding"):
            c.prepare(path, manifest, "development", home/"prepared")
        self.assertFalse((home/"prepared").exists())
        path, manifest, home = self.frozen()
        value = c.daily._json(path.read_bytes())
        value["stream"]["messages"][0]["bid"] -= .00001
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "freeze_binding"):
            c.evaluate(path, manifest, home/"run")
        self.assertFalse((home/"run").exists())

    def test_real_contest_unknown_account_and_market_wrapper_rejected(self):
        for mode in (1, 2, None, "demo", False):
            value = fixture()
            value["stream"]["initial_account"]["trade_mode"] = mode
            with self.assertRaises(ValueError):
                self.frozen(value=value)
        value = fixture()
        value["kind"] = "qualified_market"
        with self.assertRaises(ValueError):
            self.frozen(value=value)

    def test_artifact_change_rejected_and_unknown_candidate_rejected(self):
        path, manifest, home = self.frozen()
        directory = home/"prepared"
        c.prepare(path, manifest, "development", directory)
        compiled = directory/"control-fills-input.json"
        compiled.write_bytes(compiled.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError, "artifact_binding"):
            c.ControlReplay(directory, "CASH")
        for candidate in ("EW_FULL_V1", "MR20_D", None):
            with self.assertRaisesRegex(ValueError, "candidate_or_profile"):
                c.ControlReplay(directory, candidate)


if __name__ == "__main__":
    unittest.main()
