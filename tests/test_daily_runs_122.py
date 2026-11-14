from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import daily_features_118 as daily
from forex_demo_lab import daily_runs_122 as runs
from forex_demo_lab.daily_runs_fixture_122 import CASES, fixture
from test_daily_bars_121 import audit_aggregation
from test_daily_fills_120 import audit_ledger

ROOT = Path(__file__).resolve().parents[1]
F = lambda x: Fraction(str(x))


def audit_statistics(compiled, report, part, actual):
    """Independent rational summaries of independently audited fill records."""
    def number(value, expected):
        if expected is None:
            assert value is None
        else:
            assert abs(F(value) - expected) <= F("1e-35"), (value, str(expected))
    ledger = report["final_state"]["ledger"]
    entries = {r["position_id"]: r for r in ledger if r["kind"] == "entry_fill"}
    exits = [r for r in ledger if r["kind"] == "exit_fill"]
    nets = [F(r["net_trade_usd"]) for r in exits]
    positive = [v for v in nets if v > 0]
    negative = [v for v in nets if v < 0]
    gross = sum((F(r["gross_usd"]) for r in exits), F(0))
    commissions = sum((F(r["fee_usd"]) for r in ledger if "fee_usd" in r), F(0))
    financing = sum((F(r["amount_usd"]) for r in ledger if r["kind"] == "financing"), F(0))
    net = gross - commissions + financing
    assert abs(sum(nets, F(0)) - net) <= F("1e-35")
    assert actual["partition"] == part and actual["profile"] == report["profile"] and actual["candidate"] == report["candidate"]
    assert actual["trades"] == len(exits) and actual["wins"] == len(positive) and actual["losses"] == len(negative)
    assert actual["breakeven"] == sum(v == 0 for v in nets)
    expected = {"initial_cash_usd": F(10000), "final_cash_usd": F(10000) + net, "toy_net_usd": net,
                "gross_usd": gross, "commissions_usd": commissions, "financing_usd": financing,
                "toy_win_fraction": None if not nets else F(len(positive)) / len(nets),
                "net_expectancy_usd": None if not nets else net / len(nets),
                "payoff_ratio": None if not positive or not negative else (sum(positive) / len(positive)) / (-sum(negative) / len(negative)),
                "profit_factor": None if not negative else sum(positive, F(0)) / -sum(negative),
                "largest_loss_usd": max([F(0)] + [-v for v in nets]), "max_drawdown": F(report["summary"]["max_drawdown"])}
    fills = [r for r in ledger if r["kind"] in ("entry_fill", "exit_fill")]
    units = sum((F(r["lots"]) * 100000 for r in fills), F(0))
    notional = sum((F(r["lots"]) * F(r["price"]) * 100000 for r in fills), F(0))
    expected.update(turnover_eur_units=units, turnover_usd_notional=notional, turnover_over_initial_cash=notional / 10000)
    flat, intervals, cursor = [], [], part["start_msc"]
    for row in exits:
        start, end = entries[row["position_id"]]["source_msc"], row["source_msc"]
        assert cursor <= start <= end < part["end_msc"]
        if start > cursor:
            flat.append({"start_msc": cursor, "end_msc": start, "duration_msc": start - cursor})
        intervals.append((start, end))
        cursor = end
    if cursor < part["end_msc"]:
        flat.append({"start_msc": cursor, "end_msc": part["end_msc"], "duration_msc": part["end_msc"] - cursor})
    exposure = sum(b - a for a, b in intervals)
    assert actual["flat_intervals"] == flat and actual["exposure_msc"] == exposure
    assert exposure + sum(r["duration_msc"] for r in flat) == part["end_msc"] - part["start_msc"]
    expected["exposure_fraction"] = F(exposure) / (part["end_msc"] - part["start_msc"])
    for k, v in expected.items():
        number(actual[k], v)
    breaches = [r for r in exits if -F(r["net_trade_usd"]) > F(r["estimated_stop_risk_usd"])]
    assert len(actual["loss_beyond_entry_estimate"]) == len(breaches)
    for expected_row, row in zip(breaches, actual["loss_beyond_entry_estimate"]):
        assert row["position_id"] == expected_row["position_id"]
        number(row["loss_usd"], -F(expected_row["net_trade_usd"]))
        number(row["entry_estimate_usd"], F(expected_row["estimated_stop_risk_usd"]))
        number(row["excess_usd"], -F(expected_row["net_trade_usd"]) - F(expected_row["estimated_stop_risk_usd"]))
    slip, floor = (F(.00002), F(0)) if report["profile"] == "base" else (F(.00005), F(.00012))
    memos = {k: F(0) for k in ("entry_spread_usd", "entry_slippage_usd", "nonlimit_exit_spread_usd", "nonlimit_exit_slippage_usd")}
    for row in fills:
        quote = compiled["events"][row["sequence"]]
        spread = max(F(quote["ask"]) - F(quote["bid"]), floor)
        volume = F(row["lots"]) * 100000
        prefix = "entry" if row["kind"] == "entry_fill" else "nonlimit_exit" if row["reason"] != "target" else None
        if prefix:
            memos[prefix + "_spread_usd"] += spread * volume / 2
            memos[prefix + "_slippage_usd"] += slip * volume
    for k, v in memos.items():
        number(actual["embedded_price_adjustment_memos"][k], v)
    assert actual["memos_are_extra_debits"] is False and actual["target_exit_spread_decomposition"] is None
    marks = []
    for i, (event, outcome) in enumerate(zip(compiled["events"], report["final_state"]["outcomes"])):
        if outcome["execution_quote"]:
            marks.append((event["source_msc"], F(report["final_state"]["equity_usd"] if i == len(compiled["events"]) - 1 else outcome["account"]["equity_usd"])))
    assert actual["observed_quote_gaps"] == [{"start_msc": a, "end_msc": b, "duration_msc": b - a} for (a, _), (b, _) in zip(marks, marks[1:])]
    def date(ms):
        return datetime.fromtimestamp(ms / 1000, timezone.utc)
    for key, width in (("monthly", 1), ("quarterly", 3)):
        anchor = F(10000)
        first = date(part["start_msc"])
        month = first.month if width == 1 else 1 + 3 * ((first.month - 1) // 3)
        current = datetime(first.year, month, 1, tzinfo=timezone.utc)
        count = 0
        total_change = F(0)
        while int(current.timestamp() * 1000) < part["end_msc"]:
            year, month = current.year, current.month + width
            if month > 12:
                year, month = year + 1, month - 12
            next_date = datetime(year, month, 1, tzinfo=timezone.utc)
            a, b = int(current.timestamp() * 1000), int(next_date.timestamp() * 1000)
            record = actual[key][count]
            name = current.strftime("%Y-%m") if width == 1 else f"{current.year}-Q{1 + (current.month - 1) // 3}"
            assert record["period"] == name
            assert record["partial_calendar_period"] is (part["start_msc"] > a or part["end_msc"] < b)
            assert (record["start_msc"], record["end_msc"]) == (max(a, part["start_msc"]), min(b, part["end_msc"]))
            observed = [(t, v) for t, v in marks if a <= t < b]
            closing = observed[-1][1] if observed else None
            change = F(0)
            for row in ledger:
                if a <= row["source_msc"] < b:
                    change += F(row.get("gross_usd", 0)) - F(row.get("fee_usd", 0)) + F(row.get("amount_usd", 0))
            total_change += change
            number(record["opening_equity_usd"], anchor)
            number(record["closing_equity_usd"], closing)
            number(record["observed_window_return"], None if anchor is None or anchor <= 0 or closing is None else (closing - anchor) / anchor)
            number(record["ledger_cash_change_usd"], change)
            assert record["status"] == ("unobservable" if closing is None else "observed" if anchor is not None and anchor > 0 else "observed_without_positive_anchor")
            assert record["kind"] == "observed_window_not_certified_calendar_close"
            assert record["first_observation_msc"] == (observed[0][0] if observed else None)
            assert record["last_observation_msc"] == (observed[-1][0] if observed else None)
            anchor, current, count = closing, next_date, count + 1
        assert count == len(actual[key]) and abs(total_change - net) <= F("1e-35")
    assert actual["sample_status"] == "insufficient"
    assert "fewer_than_24_calendar_months" in actual["insufficiency_reasons"]
    assert "fewer_than_24_observed_monthly_marks" in actual["insufficiency_reasons"]
    assert ("fewer_than_50_closed_trades" in actual["insufficiency_reasons"]) == (report["candidate"] != "CASH" and len(exits) < 50)
    for key in ("untouched_validation_confirmed", "strategy_selected", "orders_available", "real_money_execution_available"):
        assert actual[key] is False
    assert actual["qualified_monthly_marks"] == 0 and actual["market_assessment"] == "unavailable_invented_unqualified"
    return {"accounts": 1, "trades": len(exits), "monthly_windows": len(actual["monthly"]), "quarterly_windows": len(actual["quarterly"])}


class Runs122Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0

    def bundle(self, value=None):
        self.serial += 1
        path, manifest = self.root / f"input{self.serial}.json", self.root / f"freeze{self.serial}.json"
        daily.write_new(path, fixture() if value is None else value)
        runs.freeze_fixture(path, manifest)
        return path, manifest

    def controller(self, case="targets"):
        return runs.Coordinator(*self.bundle(fixture(case)))

    def rewrite(self, checkpoint, change):
        value = json.loads(checkpoint); change(value["payload"])
        value["sha256"] = daily._digest(value["payload"])
        return json.dumps(value)

    def verify_partition(self, run, record, root):
        directory = root / record["attempt_directory"]
        if (directory / "prefix-input.json").exists():
            prefix = json.loads((directory / "prefix-input.json").read_bytes())
            aggregation = json.loads((directory / "aggregation.json").read_bytes())
            audit_aggregation(prefix, aggregation["final_state"])
            self.assertTrue(all(m["receipt_msc"] < record["partition"]["end_msc"] for m in prefix["messages"]))
        if record["computed_comparisons"]:
            compiled = json.loads((directory / "fills-input.json").read_bytes())
            reports = json.loads((directory / "fills-report.json").read_bytes())["results"]
            self.assertEqual(compiled["initial_account"]["balance_usd"], 10000)
            self.assertEqual(compiled["initial_account"]["available_msc"], record["partition"]["start_msc"])
            for report, statistic in zip(reports, record["statistics"]):
                audit_ledger(compiled, report)
                audit_statistics(compiled, report, record["partition"], statistic)
        else:
            self.assertIsNone(record["returns"])
            self.assertEqual(record["statistics"], [])
            self.assertFalse((directory / "fills-report.json").exists())

    def test_fixed_matrix_independent_all_stages_and_statistics(self):
        expected = {"missing_history": ("incomplete_required_session", "incomplete_required_session"),
                    "missing_endpoint": ("missing_declared_endpoint", None),
                    "stale_endpoint": ("invalid_endpoint_quote", "incomplete_required_session")}
        for case in CASES:
            with self.subTest(case=case):
                run = self.controller(case); root = self.root / case
                report = run.run(root)
                self.assertEqual([r["reason"] for r in report["partitions"]], list(expected.get(case, (None, None))))
                for record in report["partitions"]:
                    self.verify_partition(run, record, root)

    def test_fresh_later_cash_and_no_inherited_positions_after_dev_gain(self):
        run = self.controller(); root = self.root / "fresh"
        run.run(root)
        dev, later = run.state["partitions"]
        self.assertTrue(any(F(s["toy_net_usd"]) > 0 for s in dev["statistics"]))
        for statistic in later["statistics"]:
            self.assertEqual(statistic["initial_cash_usd"], "10000")
        compiled = json.loads((root / later["attempt_directory"] / "fills-input.json").read_bytes())
        execution = runs.fills.Replay(root / later["attempt_directory"] / "fills-input.json", root / later["attempt_directory"] / "fills-frozen.json")
        self.assertEqual(execution.state["balance_usd"], "10000")
        self.assertIsNone(execution.state["held"])
        self.assertIsNone(execution.state["reservation"])
        self.assertEqual(execution.state["consumed_sessions"], [])
        self.assertFalse(execution.state["paused"])
        self.assertTrue(all(e["source_msc"] >= later["partition"]["start_msc"] for e in compiled["events"]))

    def test_cash_no_trade_ratios_null_and_full_flat_interval(self):
        run = self.controller("no_signal"); report = run.run(self.root / "cash")
        for record in report["partitions"]:
            for statistic in record["statistics"]:
                self.assertEqual((statistic["trades"], statistic["toy_net_usd"], statistic["turnover_eur_units"], statistic["exposure_msc"]), (0, "0", "0", 0))
                for key in ("net_expectancy_usd", "toy_win_fraction", "payoff_ratio", "profit_factor"):
                    self.assertIsNone(statistic[key])
                self.assertEqual(len(statistic["flat_intervals"]), 1)

    def test_month_quarter_boundary_and_actual_boundary_close_mark(self):
        run = self.controller("missing_endpoint"); root = self.root / "months"
        run.run(root); later = run.state["partitions"][1]
        statistic = next(s for s in later["statistics"] if s["candidate"] == "MIX50_D" and s["profile"] == "base")
        self.assertEqual([r["period"] for r in statistic["monthly"]], ["2001-12", "2002-01"])
        self.assertEqual([r["period"] for r in statistic["quarterly"]], ["2001-Q4", "2002-Q1"])
        self.assertTrue(all(r["partial_calendar_period"] for r in statistic["monthly"]))
        self.assertEqual(statistic["monthly"][-1]["closing_equity_usd"], statistic["final_cash_usd"])

    def test_largest_gap_loss_excess_and_financing_are_reported(self):
        run = self.controller("weekend_gap"); root = self.root / "gap"
        run.run(root); record = run.state["partitions"][0]
        statistic = next(s for s in record["statistics"] if s["candidate"] == "MIX50_D" and s["profile"] == "base")
        self.assertGreater(F(statistic["largest_loss_usd"]), 25)
        self.assertGreater(F(statistic["loss_beyond_entry_estimate"][0]["excess_usd"]), 0)
        self.assertLess(F(statistic["financing_usd"]), 0)
        self.assertGreater(statistic["exposure_msc"], runs.daily.DAY)

    def test_price_adjustment_memos_not_subtracted_twice(self):
        run = self.controller(); record = run.run(self.root / "memos")["partitions"][0]
        for statistic in record["statistics"]:
            self.assertEqual(F(statistic["toy_net_usd"]), F(statistic["gross_usd"]) - F(statistic["commissions_usd"]) + F(statistic["financing_usd"]))
            self.assertIs(statistic["memos_are_extra_debits"], False)

    def test_future_valid_quotes_and_calendar_do_not_change_early_prefix(self):
        value = fixture(); altered = deepcopy(value)
        cutoff = value["partitions"][0]["end_msc"]
        for q in altered["stream"]["messages"]:
            if q["kind"] == "quote" and q["receipt_msc"] >= cutoff:
                q.update(bid=.9, ask=.9001)
        altered["stream"]["calendar"]["sessions"][-1]["status"] = "closure"
        a, b = runs.Coordinator(*self.bundle(value)), runs.Coordinator(*self.bundle(altered))
        self.assertEqual(a._prefix(value["partitions"][0]), b._prefix(altered["partitions"][0]))
        a.step(self.root / "future_a"); b.step(self.root / "future_b")
        for x, y in zip(a.state["partitions"][0]["statistics"], b.state["partitions"][0]["statistics"]):
            self.assertEqual({k:v for k,v in x.items() if k not in ("fill_fixture_sha256", "fill_manifest_sha256")},
                             {k:v for k,v in y.items() if k not in ("fill_fixture_sha256", "fill_manifest_sha256")})

    def test_late_endpoint_after_cutoff_is_missing_not_fallback(self):
        value = fixture("missing_endpoint")
        part = value["partitions"][0]
        part["endpoint_source_msc"] = part["end_msc"] - 1000
        q = next(q for q in value["stream"]["messages"] if q["kind"] == "quote" and q["source_msc"] == part["endpoint_source_msc"])
        q["receipt_msc"] = part["end_msc"] + 1
        run = runs.Coordinator(*self.bundle(value)); run.step(self.root / "late")
        self.assertEqual(run.state["partitions"][0]["reason"], "missing_declared_endpoint")

    def test_repeated_endpoint_invalid_even_for_cash(self):
        value = fixture("no_signal"); part = value["partitions"][0]
        index = next(i for i,q in enumerate(value["stream"]["messages"]) if q["kind"] == "quote" and q["source_msc"] == part["endpoint_source_msc"])
        q = value["stream"]["messages"][index]
        value["stream"]["messages"].insert(index + 1, {**q, "receipt_msc": q["receipt_msc"] + 20})
        for i,m in enumerate(value["stream"]["messages"]): m["sequence"] = i
        run = runs.Coordinator(*self.bundle(value)); run.step(self.root / "repeat")
        self.assertEqual(run.state["partitions"][0]["reason"], "invalid_endpoint_quote")
        self.assertEqual(run.state["partitions"][0]["computed_comparisons"], 0)

    def test_closed_endpoint_is_not_a_trading_quote(self):
        value = fixture(); part = value["partitions"][0]
        closure = next(s for s in value["stream"]["calendar"]["sessions"] if s["status"] == "closure" and s["start_msc"] > part["start_msc"])
        source = closure["start_msc"] + runs.daily.DAY // 2
        quote = {"sequence": 0, "kind": "quote", "source_msc": source, "receipt_msc": source + 2, "bid": 1.1, "ask": 1.1001}
        value["stream"]["messages"].append(quote)
        value["stream"]["messages"].sort(key=lambda m:m["receipt_msc"])
        for i,m in enumerate(value["stream"]["messages"]):m["sequence"] = i
        part.update(end_msc=source + 1000, endpoint_source_msc=source)
        run = runs.Coordinator(*self.bundle(value)); run.step(self.root / "closure")
        self.assertEqual(run.state["partitions"][0]["reason"], "invalid_endpoint_quote")

    def test_no_observed_prefix_and_empty_partition_unavailable(self):
        value = fixture(); part = value["partitions"][0]
        start = value["stream"]["calendar"]["sessions"][0]["start_msc"]
        part.update(start_msc=start, end_msc=start + 1000, endpoint_source_msc=start + 500)
        run = runs.Coordinator(*self.bundle(value)); root = self.root / "empty"
        run.step(root)
        self.assertEqual(run.state["partitions"][0]["reason"], "no_observed_prefix")
        self.assertIsNone(run.state["partitions"][0]["returns"])

    def test_restore_completed_prefix_only_never_later_partition(self):
        paths = self.bundle(); run = runs.Coordinator(*paths); root = self.root / "prefix"
        run.step(root)
        original = runs.Coordinator._calculate
        def bounded(instance, part, directory, write):
            if part["name"] != "development" or write:
                raise AssertionError("future_partition_or_write")
            return original(instance, part, directory, write)
        with patch.object(runs.Coordinator, "_calculate", bounded):
            restored = runs.Coordinator.restore(*paths, run.checkpoint(), root)
        self.assertEqual(restored.state, run.state)
        restored.run(root)
        self.assertEqual(len(restored.state["partitions"]), 2)

    def test_finished_restore_and_repeated_run_idempotent(self):
        paths = self.bundle(fixture("no_signal")); run = runs.Coordinator(*paths); root = self.root / "finished"
        report = run.run(root); before = run.checkpoint()
        self.assertEqual(run.run(root), report)
        self.assertFalse(run.step(root))
        self.assertEqual(run.checkpoint(), before)
        restored = runs.Coordinator.restore(*paths, before, root)
        self.assertEqual(restored.report(), report)
        self.assertEqual(len(list(root.glob('*-attempt*'))), 2)

    def test_interrupted_attempt_preserved_and_not_counted_on_resume(self):
        paths = self.bundle(fixture("no_signal")); run = runs.Coordinator(*paths); root = self.root / "interruption"
        checkpoint = run.checkpoint()
        with patch.object(runs, "_statistics", side_effect=RuntimeError("invented_interruption")):
            with self.assertRaisesRegex(RuntimeError, "invented_interruption"):
                run.step(root)
        self.assertEqual(run.state["cursor"], 0)
        old = {p.name:p.read_bytes() for p in (root / 'development-attempt00').iterdir()}
        restored = runs.Coordinator.restore(*paths, checkpoint, root)
        report = restored.run(root)
        self.assertEqual(report["partitions"][0]["attempt_directory"], "development-attempt01")
        self.assertEqual(len(report["partitions"]), 2)
        self.assertEqual(old, {p.name:p.read_bytes() for p in (root / 'development-attempt00').iterdir()})

    def test_rehashed_controller_statistics_cursor_and_bounds_rejected(self):
        paths = self.bundle(fixture("no_signal")); run = runs.Coordinator(*paths); root = self.root / "forged"
        run.step(root)
        for change, reason in ((lambda p:p.update(cursor=False), "checkpoint_cursor"),
                               (lambda p:p["state"]["partitions"][0]["statistics"][0].update(toy_net_usd="1"), "checkpoint_reconstructed_state"),
                               (lambda p:p["state"]["partitions"][0]["partition"].update(end_msc=p["state"]["partitions"][0]["partition"]["end_msc"] + 1), "checkpoint_reconstructed_state"),
                               (lambda p:p["state"].update(cursor=False), "checkpoint_reconstructed_state")):
            with self.assertRaisesRegex(ValueError, reason):
                runs.Coordinator.restore(*paths, self.rewrite(run.checkpoint(), change), root)

    def test_changed_artifacts_and_wrong_output_owner_reject(self):
        paths = self.bundle(fixture("no_signal")); run = runs.Coordinator(*paths); root = self.root / "artifacts"
        run.step(root)
        statistic = root / run.state["partitions"][0]["attempt_directory"] / "statistics.json"
        statistic.write_bytes(statistic.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, "partition_artifact_binding"):
            runs.Coordinator.restore(*paths, run.checkpoint(), root)
        marker = root / 'run-binding.json'; marker.write_text('{}')
        with self.assertRaisesRegex(ValueError, "output_binding"):
            runs.Coordinator.restore(*paths, run.checkpoint(), root)

    def test_statistics_artifact_and_all_hashes_reforged_still_reject(self):
        paths = self.bundle(fixture("no_signal")); run = runs.Coordinator(*paths); root = self.root / "reforged"
        run.step(root)
        checkpoint = json.loads(run.checkpoint())
        record = checkpoint['payload']['state']['partitions'][0]
        directory = root / record['attempt_directory']
        statistics_path = directory / 'statistics.json'
        statistics = json.loads(statistics_path.read_bytes())
        statistics['results'][0]['toy_net_usd'] = '999'
        statistics_path.write_text(json.dumps(statistics))
        record['statistics'][0]['toy_net_usd'] = '999'
        record['derived_files']['statistics.json'] = hashlib.sha256(statistics_path.read_bytes()).hexdigest()
        artifact = {k:v for k,v in record.items() if k not in ('attempt_directory','partition_report_sha256')}
        report_path = directory / 'partition-report.json'; report_path.write_text(json.dumps(artifact))
        record['partition_report_sha256'] = hashlib.sha256(report_path.read_bytes()).hexdigest()
        checkpoint['sha256'] = daily._digest(checkpoint['payload'])
        with self.assertRaisesRegex(ValueError,'partition_results_changed'):
            runs.Coordinator.restore(*paths,json.dumps(checkpoint),root)

    def test_freeze_types_rules_partitions_and_input_bindings(self):
        for mutation, reason in ((lambda m:m.update(orders_available=0), "run_freeze_binding"),
                                 (lambda m:m.update(untouched_validation_confirmed=0), "run_freeze_binding"),
                                 (lambda m:m["run_rules"].update(fresh_cash_usd=True), "run_freeze_binding"),
                                 (lambda m:m.update(sources={}), "run_freeze_binding"),
                                 (lambda m:m["partitions"][0].update(endpoint_source_msc=m["partitions"][0]["endpoint_source_msc"]-1), "run_freeze_partitions"),
                                 (lambda m:m.update(frozen_at_utc='2001-01-01T00:00:00'), "freeze_time")):
            path, manifest = self.bundle(); data = json.loads(manifest.read_bytes()); mutation(data); manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, reason):runs.Coordinator(path,manifest)

    def test_partition_bounds_order_overlap_and_unknown_flags_reject(self):
        for change, reason in ((lambda v:v["partitions"].reverse(), "partition_order"),
                               (lambda v:v["partitions"][1].update(start_msc=v["partitions"][0]["start_msc"]), "partition_overlap"),
                               (lambda v:v["partitions"][0].update(endpoint_source_msc=v["partitions"][0]["end_msc"]), "partition_bounds"),
                               (lambda v:v["partitions"][0].update(start_msc=False), "partition_time"),
                               (lambda v:v.update(qualified=True), "run_fixture_fields"),
                               (lambda v:v["partitions"][1].update(untouched=True), "partition_fields"),
                               (lambda v:v["stream"].update(execution_start_msc=v["partitions"][0]["start_msc"] + 3000), "unfunded_stream_required")):
            value = fixture(); change(value)
            with self.assertRaisesRegex(ValueError, reason):runs.validate_fixture(value)

    def test_fixed_capital_demo_type_credentials_and_market_clock_reject(self):
        for mode in (1,2,False):
            value = fixture(); value["stream"]["initial_account"]["trade_mode"] = mode
            with self.assertRaisesRegex(ValueError,"synthetic_demo_account_required"):runs.validate_fixture(value)
        value = fixture(); value["stream"]["initial_account"]["balance_usd"] = 20000
        with self.assertRaisesRegex(ValueError,"fixed_fresh_capital_required"):runs.validate_fixture(value)
        value = fixture(); value["stream"]["initial_account"]["password"] = 0
        with self.assertRaisesRegex(ValueError,"fill_account_fields"):runs.validate_fixture(value)
        value = fixture(); value["clock"] = "broker_clock"
        with self.assertRaisesRegex(ValueError,"invented_daily_run_required"):runs.validate_fixture(value)

    def test_missing_month_breaks_anchor_without_invented_returns(self):
        def ms(text):return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()*1000)
        times = [ms('2001-01-15'), ms('2001-03-15')]
        part = {'name':'development','start_msc':ms('2001-01-01'),'end_msc':ms('2001-04-01'),'endpoint_source_msc':times[-1]}
        events = [{'source_msc':t,'bid':1.1,'ask':1.1001} for t in times]
        compiled = {'initial_account':{'balance_usd':10000},'events':events}
        report = {'profile':'base','candidate':'CASH','fixture_sha256':'test','manifest_sha256':'test',
                  'summary':{'toy_net_usd':'0','max_drawdown':'0'},'final_state':{'ledger':[],'equity_usd':'10000','balance_usd':'10000',
                  'outcomes':[{'execution_quote':True,'account':{'equity_usd':'10000'}} for _ in times]}}
        actual = runs._statistics(compiled,report,part)
        audit_statistics(compiled,report,part,actual)
        self.assertEqual([r['status'] for r in actual['monthly']], ['observed','unobservable','observed_without_positive_anchor'])
        self.assertIsNone(actual['monthly'][-1]['opening_equity_usd'])
        self.assertIsNone(actual['monthly'][-1]['observed_window_return'])

    def test_nonpositive_month_anchor_does_not_create_ratio(self):
        def ms(text):return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()*1000)
        times=[ms('2001-01-15'),ms('2001-02-15')]
        part={'name':'development','start_msc':ms('2001-01-01'),'end_msc':ms('2001-03-01'),'endpoint_source_msc':times[-1]}
        compiled={'initial_account':{'balance_usd':10000},'events':[{'source_msc':t,'bid':1.1,'ask':1.1001} for t in times]}
        report={'profile':'base','candidate':'CASH','fixture_sha256':'test','manifest_sha256':'test','summary':{'toy_net_usd':'0','max_drawdown':'0'},
                'final_state':{'ledger':[],'equity_usd':'10000','balance_usd':'10000','outcomes':[
                 {'execution_quote':True,'account':{'equity_usd':'-1'}},{'execution_quote':True,'account':{'equity_usd':'10000'}}]}}
        actual=runs._statistics(compiled,report,part)
        self.assertIsNone(actual['monthly'][1]['observed_window_return'])
        self.assertEqual(actual['monthly'][1]['status'],'observed_without_positive_anchor')

    def test_strict_JSON_checkpoint_shape_and_limits(self):
        for i,raw in enumerate(('{"x":1,"x":2}','{"x":NaN}')):
            path=self.root/f'bad{i}.json';path.write_text(raw)
            with self.assertRaises(ValueError):runs.freeze_fixture(path,self.root/f'bad{i}-frozen.json')
        paths=self.bundle();run=runs.Coordinator(*paths)
        with self.assertRaisesRegex(ValueError,'unfinished_run_report'):run.report()
        with self.assertRaisesRegex(ValueError,'checkpoint_size'):runs.Coordinator.restore(*paths,'x'*(daily.MAX_BYTES+1),self.root/'none')

    def test_cli_run_artifacts_and_existing_root_no_overwrite(self):
        script=str(ROOT/'scripts/daily-runs-122.py')
        path,manifest,output=(self.root/n for n in ('cli.json','cli-freeze.json','cli-run'))
        for args in (('create-fixture','no_signal',str(path)),('freeze',str(path),str(manifest)),('evaluate',str(path),str(manifest),str(output))):
            result=subprocess.run([sys.executable,script,*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            self.assertIs(json.loads(result.stdout)['orders_available'],False)
        saved=(output/'run-report.json').read_bytes()
        result=subprocess.run([sys.executable,script,'evaluate',str(path),str(manifest),str(output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(json.loads(result.stdout)['reason'],'artifact_exists')
        self.assertEqual((output/'run-report.json').read_bytes(),saved)


if __name__ == '__main__':
    unittest.main()
