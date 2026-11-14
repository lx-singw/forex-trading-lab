from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
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
from forex_demo_lab import daily_bars_121 as bars
from forex_demo_lab.daily_bars_fixture_121 import CASES, fixture
from test_daily_fills_120 import audit_ledger

ROOT = Path(__file__).resolve().parents[1]
F = lambda x: Fraction(str(x))


def audit_aggregation(value, state):
    """Independent Fraction midpoint/coverage/publication oracle from raw messages."""
    encode = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    digest = lambda x: hashlib.sha256(encode(x)).hexdigest()
    def decimal_string(v):
        with localcontext() as ctx:
            ctx.prec = 70
            d = Decimal(v.numerator) / Decimal(v.denominator)
            return "0" if d == 0 else format(d.normalize(), "f")
    expected = {"cursor": 0, "last_event": None, "last_quote": None, "clock_msc": None,
                "next_session": 0, "pending": {}, "bars": [], "publications": [], "outcomes": [], "prefix_sha256": "0" * 64}
    calendar = value["calendar"]
    for message in value["messages"][:state["cursor"]]:
        expected["prefix_sha256"] = hashlib.sha256(bytes.fromhex(expected["prefix_sha256"]) + encode(message)).hexdigest()
        finalized = []
        while expected["next_session"] < len(calendar["sessions"]):
            i = expected["next_session"]
            session = calendar["sessions"][i]
            if session["end_msc"] + 2000 > message["receipt_msc"]:
                break
            observations = expected["pending"].pop(str(i), [])
            times = [o["source_msc"] for o in observations]
            first = times[0] - session["start_msc"] if times else None
            last = session["end_msc"] - times[-1] if times else None
            gap = max((times[j] - times[j - 1] for j in range(1, len(times))), default=0)
            complete = len(times) >= 4 and first <= 60000 and last <= 60000 and gap <= 43200000
            coverage = {"count": len(times), "first_edge_msc": first, "last_edge_msc": last,
                        "max_gap_msc": gap, "complete": complete}
            status = "closure" if session["status"] == "closure" else "completed" if complete else "incomplete"
            bar = None
            if status == "completed":
                points = [F(o["midpoint"]) for o in observations]
                bar = {"session_id": i, "start_msc": session["start_msc"], "end_msc": session["end_msc"],
                       "observation_msc": times[-1], "available_msc": message["receipt_msc"],
                       "open": float(points[0]), "high": float(max(points)), "low": float(min(points)), "close": float(points[-1])}
                bar["lineage_sha256"] = digest({"format": "FXDL_DAILY118_V1", "kind": "invented_daily_fixture",
                    "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": value["case"],
                    "calendar_id": calendar["calendar_id"], "session": session, "bar": bar})
                expected["bars"].append(bar)
            evidence = {"session_id": i, "status": status, "published_msc": message["receipt_msc"],
                        "finalizer_sequence": message["sequence"], "finalizer_sha256": digest(message),
                        "quote_evidence": observations, "coverage": coverage,
                        "bar_lineage_sha256": None if bar is None else bar["lineage_sha256"],
                        "calendar_prefix_sha256": digest({**calendar, "sessions": calendar["sessions"][:i + 1]}),
                        "message_prefix_sha256": expected["prefix_sha256"]}
            evidence["publication_sha256"] = digest(evidence)
            expected["publications"].append(evidence)
            expected["next_session"] += 1
            finalized.append(i)
        session_id, midpoint, reason = None, None, "clock_advance"
        if message["kind"] == "quote":
            session = next(s for s in calendar["sessions"] if s["start_msc"] <= message["source_msc"] < s["end_msc"])
            session_id = session["session_id"]
            repeated = expected["last_quote"] is not None and message["source_msc"] == expected["last_quote"]["source_msc"]
            if session_id < expected["next_session"]:
                reason = "finalized_quote"
            elif message["receipt_msc"] - message["source_msc"] > 2000:
                reason = "stale_quote"
            elif repeated:
                reason = "repeated_source"
            elif session["status"] == "closure":
                reason = "closed_quote"
            else:
                reason = "accepted_quote"
                midpoint = decimal_string((F(message["bid"]) + F(message["ask"])) / 2)
                expected["pending"].setdefault(str(session_id), []).append({"sequence": message["sequence"],
                    "source_msc": message["source_msc"], "receipt_msc": message["receipt_msc"],
                    "midpoint": midpoint, "quote_sha256": digest(message)})
            expected["last_quote"] = message
        expected["outcomes"].append({"sequence": message["sequence"], "reason": reason, "session_id": session_id,
                                     "midpoint": midpoint, "finalized_sessions": finalized,
                                     "prefix_sha256": expected["prefix_sha256"]})
        expected.update(cursor=expected["cursor"] + 1, last_event=message, clock_msc=message["receipt_msc"])
    assert encode(state) == encode(expected), "independent_aggregation_state"
    return {"messages": state["cursor"], "completed": len(state["bars"]),
            "incomplete": sum(p["status"] == "incomplete" for p in state["publications"]),
            "closures": sum(p["status"] == "closure" for p in state["publications"]),
            "pending": len(state["pending"])}


def renumber(value):
    for i, message in enumerate(value["messages"]):
        message["sequence"] = i
    return value


def small():
    value = fixture()
    value["calendar"]["sessions"] = value["calendar"]["sessions"][:4]
    end = value["calendar"]["sessions"][2]["end_msc"] + 2000
    value["messages"] = [m for m in value["messages"] if m["receipt_msc"] <= end]
    value["execution_start_msc"] = None
    value["initial_account"]["available_msc"] = value["calendar"]["available_msc"]
    return renumber(value)


class Bars121Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0

    def bundle(self, value=None):
        self.serial += 1
        path, manifest = self.root / f"input{self.serial}.json", self.root / f"freeze{self.serial}.json"
        daily.write_new(path, small() if value is None else value)
        bars.freeze_fixture(path, manifest)
        return path, manifest

    def run_value(self, value):
        obj = bars.Replay(*self.bundle(value))
        report = obj.run()
        audit_aggregation(value, report["final_state"])
        return obj

    def first_publication(self, value):
        return self.run_value(value).state["publications"][0]

    def reject(self, value, reason):
        with self.assertRaisesRegex(ValueError, "^" + reason + "$"):
            bars.validate_fixture(value)

    def rewrite(self, checkpoint, change):
        result = json.loads(checkpoint)
        change(result["payload"])
        result["sha256"] = daily._digest(result["payload"])
        return json.dumps(result)

    def test_all_coherent_matrix_aggregation_and_accounting(self):
        for case in CASES:
            with self.subTest(case=case):
                value = fixture(case)
                path, manifest = self.bundle(value)
                output = self.root / (case + "-output")
                result = bars.evaluate_fixture(path, manifest, output)
                aggregation = json.loads((output / "aggregation.json").read_bytes())
                audit_aggregation(value, aggregation["final_state"])
                if case in ("missing_coverage", "stale_coverage"):
                    self.assertEqual((result["status"], result["reason"], result["returns"]),
                                     ("unavailable", "incomplete_required_session", None))
                    self.assertFalse((output / "fills-report.json").exists())
                else:
                    self.assertEqual(result["comparisons"], 8)
                    compiled = json.loads((output / "fills-input.json").read_bytes())
                    quotes = [m for m in value["messages"] if m["kind"] == "quote" and m["source_msc"] >= value["execution_start_msc"]]
                    for q, event in zip(quotes, compiled["events"]):
                        self.assertEqual({k: event[k] for k in ("source_msc", "receipt_msc", "bid", "ask")},
                                         {k: q[k] for k in ("source_msc", "receipt_msc", "bid", "ask")})
                        self.assertLessEqual(event["feature_decision_msc"], event["receipt_msc"])
                    report = json.loads((output / "fills-report.json").read_bytes())
                    for r in report["results"]:
                        audit_ledger(compiled, r)

    def test_ohlc_first_max_min_last_exact_midpoints(self):
        obj = self.run_value(small())
        bar = obj.state["bars"][0]
        self.assertEqual((bar["open"], bar["high"], bar["low"], bar["close"]), (1., 1.0004, .9996, 1.))
        self.assertEqual(obj.state["publications"][0]["quote_evidence"][1]["midpoint"], "1.0004")

    def test_no_publication_before_deadline_or_unobserved_clock(self):
        value = small()
        value["messages"] = value["messages"][:4]
        obj = self.run_value(value)
        self.assertEqual(obj.state["bars"], [])
        self.assertEqual(len(obj.state["pending"]["0"]), 4)
        with self.assertRaisesRegex(ValueError, "no_completed_bar"):
            obj.features()

    def test_deadline_inclusive_and_available_at_observed_receipt(self):
        value = small()
        value["messages"][4]["receipt_msc"] -= 1
        obj = bars.Replay(*self.bundle(value))
        for e in value["messages"][:5]:
            obj.step(e)
        self.assertEqual(obj.state["bars"], [])
        obj.step(value["messages"][5])
        self.assertEqual(obj.state["bars"][0]["available_msc"], value["messages"][5]["receipt_msc"])

    def test_late_finalizer_does_not_backdate(self):
        value = small()
        value["messages"].pop(4)
        renumber(value)
        obj = self.run_value(value)
        self.assertEqual(obj.state["bars"][0]["available_msc"], value["messages"][4]["receipt_msc"])
        self.assertGreater(obj.state["bars"][0]["available_msc"], value["calendar"]["sessions"][0]["end_msc"] + 2000)

    def test_fresh_last_quote_arriving_after_end_is_included(self):
        value = small()
        end = value["calendar"]["sessions"][0]["end_msc"]
        value["messages"][3].update(source_msc=end - 1, receipt_msc=end + 1999)
        p = self.first_publication(value)
        self.assertEqual(p["status"], "completed")
        self.assertEqual(p["quote_evidence"][-1]["source_msc"], end - 1)

    def test_deadline_arrival_is_stale_and_cannot_revise(self):
        value = small()
        end = value["calendar"]["sessions"][0]["end_msc"]
        value["messages"][3].update(source_msc=end - 1, receipt_msc=end + 2000)
        obj = self.run_value(value)
        self.assertEqual(obj.state["publications"][0]["status"], "incomplete")
        self.assertEqual(obj.state["outcomes"][3]["reason"], "finalized_quote")

    def test_half_open_boundary_quote_belongs_to_next_session(self):
        value = small()
        value["messages"][5].update(source_msc=value["calendar"]["sessions"][1]["start_msc"],
                                    receipt_msc=value["calendar"]["sessions"][1]["start_msc"] + 2000)
        obj = self.run_value(value)
        self.assertEqual(obj.state["outcomes"][5]["session_id"], 1)
        self.assertEqual(obj.state["publications"][0]["coverage"]["count"], 4)

    def test_first_edge_exact_boundary_then_beyond(self):
        for offset, status in ((60000, "completed"), (60001, "incomplete")):
            value = small()
            start = value["calendar"]["sessions"][0]["start_msc"]
            value["messages"][0].update(source_msc=start + offset, receipt_msc=start + offset + 2)
            self.assertEqual(self.first_publication(value)["status"], status)

    def test_last_edge_exact_boundary_then_beyond(self):
        for offset, status in ((60000, "completed"), (60001, "incomplete")):
            value = small()
            end = value["calendar"]["sessions"][0]["end_msc"]
            value["messages"][3].update(source_msc=end - offset, receipt_msc=end - offset + 2)
            self.assertEqual(self.first_publication(value)["status"], status)

    def test_successive_gap_exact_boundary_then_beyond(self):
        for extra, status in ((0, "completed"), (1, "incomplete")):
            value = small()
            source = value["messages"][1]["source_msc"] + daily.DAY // 2 + extra
            value["messages"][2].update(source_msc=source, receipt_msc=source + 2)
            self.assertEqual(self.first_publication(value)["status"], status)

    def test_minimum_four_sources_no_counting_duplicate(self):
        value = small()
        value["messages"].pop(1)
        duplicate = {**value["messages"][0], "receipt_msc": value["messages"][0]["receipt_msc"] + 20}
        value["messages"].insert(1, duplicate)
        renumber(value)
        p = self.first_publication(value)
        self.assertEqual((p["status"], p["coverage"]["count"]), ("incomplete", 3))

    def test_age2000_qualifies_age2001_does_not(self):
        for age, status in ((2000, "completed"), (2001, "incomplete")):
            value = small()
            value["messages"][0]["receipt_msc"] = value["messages"][0]["source_msc"] + age
            self.assertEqual(self.first_publication(value)["status"], status)

    def test_closure_quotes_excluded_without_inventing_bar(self):
        value = small()
        value["calendar"]["sessions"][0]["status"] = "closure"
        obj = self.run_value(value)
        self.assertEqual(obj.state["publications"][0]["status"], "closure")
        self.assertEqual(obj.state["bars"][0]["session_id"], 1)
        self.assertEqual(obj.state["outcomes"][0]["reason"], "closed_quote")
        self.assertEqual(len(daily.snapshot(obj.features()).history), 2)

    def test_empty_trading_session_is_incomplete_not_closure(self):
        value = small()
        value["messages"] = value["messages"][4:]
        renumber(value)
        obj = self.run_value(value)
        self.assertEqual(obj.state["publications"][0]["status"], "incomplete")
        with self.assertRaisesRegex(ValueError, "missing_required_session"):
            obj.features()

    def test_wide_quotes_are_observed_not_replaced(self):
        value = small()
        value["messages"][1]["ask"] = 1.1
        obj = self.run_value(value)
        expected = float((F(value["messages"][1]["bid"]) + F(1.1)) / 2)
        self.assertEqual(obj.state["bars"][0]["high"], expected)
        self.assertEqual(obj.state["outcomes"][1]["reason"], "accepted_quote")

    def test_late_old_quote_does_not_change_published_bar(self):
        value = small()
        late = {**value["messages"][3], "receipt_msc": value["messages"][4]["receipt_msc"] + 1}
        value["messages"].insert(5, late)
        renumber(value)
        obj = bars.Replay(*self.bundle(value))
        for e in value["messages"][:5]:
            obj.step(e)
        old = obj.state["bars"]
        obj.step(value["messages"][5])
        self.assertEqual(obj.state["bars"], old)
        self.assertEqual(obj.state["outcomes"][-1]["reason"], "finalized_quote")

    def test_features_bind_observed_bar_prefix(self):
        obj = self.run_value(fixture("half_risk"))
        compiled = bars.compile_fills(obj)
        first = compiled["events"][0]
        request = {**compiled["features"], "target_session_id": first["target_session_id"],
                   "decision_msc": first["feature_decision_msc"]}
        decision = daily.decisions(request)["MIX50_D"]
        self.assertEqual((decision.side, decision.risk_multiplier), (1, .5))
        self.assertEqual(len(decision.used_bar_hashes), 253)
        self.assertLess(decision.available_msc, first["source_msc"])

    def test_partial_session_not_used_as_feature(self):
        obj = self.run_value(fixture("partial_session"))
        compiled = bars.compile_fills(obj)
        last = compiled["events"][-1]
        row = next(s for s in compiled["features"]["calendar"]["sessions"] if s["start_msc"] <= last["source_msc"] < s["end_msc"])
        self.assertNotIn(row["session_id"], [b["session_id"] for b in compiled["features"]["bars"]])
        self.assertLess(last["target_session_id"], row["session_id"])
        self.assertIn(str(row["session_id"]), obj.state["pending"])

    def test_coherent_weekend_gap_financing_and_consumed_opportunity(self):
        value = fixture("weekend_gap")
        path, manifest = self.bundle(value)
        output = self.root / "weekend"
        bars.evaluate_fixture(path, manifest, output)
        compiled = json.loads((output / "fills-input.json").read_bytes())
        reports = json.loads((output / "fills-report.json").read_bytes())["results"]
        r = next(r for r in reports if r["candidate"] == "MIX50_D" and r["profile"] == "base")
        audit_ledger(compiled, r)
        self.assertLess(F(r["summary"]["toy_net_usd"]), -25)
        rollovers = [e for e in r["final_state"]["ledger"] if e["kind"] == "financing"]
        self.assertIn(5, [e["weekday"] for e in rollovers])
        self.assertIn(6, [e["weekday"] for e in rollovers])
        self.assertTrue(any(o["reason"] == "held_position" for o in r["final_state"]["outcomes"]))

    def test_future_prices_receipts_calendar_do_not_change_earlier_state(self):
        value = small()
        altered = deepcopy(value)
        altered["messages"][-2].update(bid=.9, ask=.9001, receipt_msc=altered["messages"][-2]["receipt_msc"] + 10)
        altered["calendar"]["sessions"][-1]["status"] = "closure"
        a, b = bars.Replay(*self.bundle(value)), bars.Replay(*self.bundle(altered))
        for i in range(10):
            a.step(value["messages"][i]); b.step(altered["messages"][i])
            self.assertEqual(a.state, b.state)
            if a.state["bars"]:
                self.assertEqual(daily.decisions(a.features()), daily.decisions(b.features()))

    def test_every_small_prefix_restart_only_observed_messages(self):
        value = small()
        paths = self.bundle(value)
        obj = bars.Replay(*paths)
        original = bars.Replay.step
        for cursor in range(len(value["messages"]) + 1):
            def bounded(instance, message):
                if message["sequence"] >= cursor:
                    raise AssertionError("future_message")
                return original(instance, message)
            with patch.object(bars.Replay, "step", bounded):
                restored = bars.Replay.restore(*paths, obj.checkpoint())
            self.assertEqual(restored.state, obj.state)
            audit_aggregation(value, restored.state)
            if cursor < len(value["messages"]):
                obj.step(value["messages"][cursor])

    def test_restart_before_deadline_and_after_publication_no_duplicates(self):
        value = small()
        paths = self.bundle(value)
        obj = bars.Replay(*paths)
        for e in value["messages"][:4]:
            obj.step(e)
        restored = bars.Replay.restore(*paths, obj.checkpoint())
        self.assertEqual(restored.state["bars"], [])
        restored.step(value["messages"][4])
        state = restored.state
        self.assertFalse(restored.step(value["messages"][4]))
        self.assertEqual(restored.state, state)
        self.assertEqual(bars.Replay.restore(*paths, restored.checkpoint()).state, state)

    def test_rehashed_pending_publication_and_clock_forgery(self):
        value = small()
        paths = self.bundle(value)
        obj = bars.Replay(*paths)
        for e in value["messages"][:6]:
            obj.step(e)
        changes = [lambda p:p["state"]["pending"]["1"][0].update(midpoint="999"),
                   lambda p:p["state"]["bars"][0].update(close=2.),
                   lambda p:p["state"]["bars"][0].update(available_msc=p["state"]["bars"][0]["available_msc"] - 1),
                   lambda p:p["state"]["publications"][0]["coverage"].update(count=5),
                   lambda p:p["state"].update(clock_msc=p["state"]["clock_msc"] + 1),
                   lambda p:p["state"].update(prefix_sha256="0" * 64),
                   lambda p:p["state"].update(next_session=0)]
        for change in changes:
            with self.assertRaisesRegex(ValueError, "checkpoint_reconstructed_state"):
                bars.Replay.restore(*paths, self.rewrite(obj.checkpoint(), change))

    def test_checkpoint_boolean_cursor_input_manifest_and_checksum_binding(self):
        paths = self.bundle()
        obj = bars.Replay(*paths)
        with self.assertRaisesRegex(ValueError, "checkpoint_cursor"):
            bars.Replay.restore(*paths, self.rewrite(obj.checkpoint(), lambda p:p.update(cursor=False)))
        changed = small(); changed["messages"][-2].update(bid=.9, ask=.9001)
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            bars.Replay.restore(*self.bundle(changed), obj.checkpoint())
        bad = json.loads(obj.checkpoint()); bad["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            bars.Replay.restore(*paths, json.dumps(bad))

    def test_latest_idempotent_changed_or_older_message_rejected(self):
        value = small()
        obj = bars.Replay(*self.bundle(value))
        obj.step(value["messages"][0])
        before = obj.checkpoint()
        self.assertFalse(obj.step(value["messages"][0]))
        self.assertEqual(obj.checkpoint(), before)
        with self.assertRaisesRegex(ValueError, "message_binding"):
            obj.step({**value["messages"][1], "ask": 1.1})
        self.assertEqual(obj.checkpoint(), before)
        obj.step(value["messages"][1])
        with self.assertRaisesRegex(ValueError, "message_binding"):
            obj.step(value["messages"][0])

    def test_defensive_state_cannot_alter_quotes_bars_or_evidence(self):
        obj = self.run_value(small())
        before = obj.checkpoint()
        state = obj.state
        state["bars"][0]["close"] = 999
        state["publications"][0]["quote_evidence"][0]["midpoint"] = "999"
        self.assertEqual(obj.checkpoint(), before)

    def test_missing_required_coverage_unavailable_not_zero_return(self):
        obj = self.run_value(fixture("missing_coverage"))
        with self.assertRaisesRegex(ValueError, "incomplete_required_session"):
            bars.compile_fills(obj)

    def test_excluded_final_quote_is_retained_and_cannot_liquidate(self):
        for fault in ("stale", "repeated"):
            with self.subTest(fault=fault):
                value = fixture("partial_session")
                if fault == "stale":
                    value["messages"][-1]["receipt_msc"] = value["messages"][-1]["source_msc"] + 2001
                else:
                    last = value["messages"][-1]
                    value["messages"].append({**last, "sequence": len(value["messages"]),
                                              "receipt_msc": last["receipt_msc"] + 20})
                path, manifest = self.bundle(value)
                output = self.root / (fault + "-endpoint")
                report = bars.evaluate_fixture(path, manifest, output)
                self.assertEqual((report["status"], report["reason"], report["returns"]),
                                 ("unavailable", "missing_executable_endpoint", None))
                compiled = json.loads((output / "fills-input.json").read_bytes())
                self.assertEqual(compiled["events"][-1]["source_msc"], value["messages"][-1]["source_msc"])
                self.assertEqual(compiled["events"][-1]["receipt_msc"], value["messages"][-1]["receipt_msc"])
                self.assertFalse((output / "fills-report.json").exists())

    def test_no_execution_partition_and_no_execution_quotes(self):
        obj = self.run_value(small())
        with self.assertRaisesRegex(ValueError, "aggregation_only"):
            bars.compile_fills(obj)
        value = small()
        value["execution_start_msc"] = value["messages"][-1]["receipt_msc"] + 1
        obj = self.run_value(value)
        with self.assertRaisesRegex(ValueError, "no_execution_quotes"):
            bars.compile_fills(obj)

    def test_no_completed_feature_available_cannot_start_pipeline(self):
        value = small()
        value["execution_start_msc"] = value["messages"][0]["source_msc"]
        obj = self.run_value(value)
        with self.assertRaisesRegex(ValueError, "no_available_feature"):
            bars.compile_fills(obj)

    def test_input_no_bars_positions_marks_credentials_or_real_mode(self):
        for key in ("bars", "features", "qualified", "account_id"):
            value = small(); value[key] = 0
            self.reject(value, "bars_fixture_fields")
        for key in ("held", "equity_usd", "free_margin_usd", "password"):
            value = small(); value["initial_account"][key] = 0
            self.reject(value, "fill_account_fields")
        for mode in (1, 2, False, True):
            value = small(); value["initial_account"]["trade_mode"] = mode
            self.reject(value, "synthetic_demo_account_required")

    def test_structural_source_receipt_sequence_and_price_rejections(self):
        for change, reason in ((lambda v:v["messages"][1].update(sequence=4), "message_sequence"),
                               (lambda v:v["messages"][1].update(receipt_msc=v["messages"][0]["receipt_msc"] - 1), "quote_clock"),
                               (lambda v:v["messages"][1].update(source_msc=v["messages"][0]["source_msc"] - 1), "source_order"),
                               (lambda v:v["messages"][1].update(source_msc=v["messages"][0]["source_msc"]), "source_price_conflict"),
                               (lambda v:v["messages"][0].update(bid=2.), "quote_price"),
                               (lambda v:v["messages"][0].update(receipt_msc=True), "message_time"),
                               (lambda v:v["messages"][4].update(receipt_msc=v["messages"][0]["receipt_msc"]), "receipt_order")):
            value = small(); change(value)
            self.reject(value, reason)

    def test_strict_calendar_and_clock_no_boundary_guessing(self):
        value = small(); value["clock"] = "broker_clock"
        self.reject(value, "invented_quote_pipeline_required")
        value = small(); value["calendar"]["available_msc"] = value["calendar"]["sessions"][0]["start_msc"] + 1
        self.reject(value, "calendar_not_predeclared")
        value = small(); value["calendar"]["sessions"][1]["session_id"] = 3
        self.reject(value, "calendar_sequence")
        value = small(); value["calendar"]["sessions"][0]["start_msc"] += 1
        self.reject(value, "invented_day_boundary")

    def test_nonfinite_unknown_message_and_partition_numbers_rejected(self):
        for new in (True, float("nan"), float("inf"), 0, -1):
            value = small(); value["messages"][0]["bid"] = new
            self.reject(value, "quote_price")
        value = small(); value["messages"][0]["kind"] = "trade"
        self.reject(value, "message_kind")
        value = small(); value["execution_start_msc"] = False
        self.reject(value, "execution_start")

    def test_freeze_strict_types_rules_sources_and_time(self):
        for mutation, reason in ((lambda m:m.update(orders_available=0), "bars_freeze_binding"),
                                 (lambda m:m["aggregation_rules"].update(minimum_distinct_quotes=True), "bars_freeze_binding"),
                                 (lambda m:m.update(sources={}), "bars_freeze_binding"),
                                 (lambda m:m.update(fixture_sha256="0" * 64), "bars_freeze_binding"),
                                 (lambda m:m.update(frozen_at_utc="2001-01-01T00:00:00"), "freeze_time")):
            path, manifest = self.bundle()
            data = json.loads(manifest.read_bytes()); mutation(data); manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, reason):
                bars.Replay(path, manifest)

    def test_strict_JSON_limits_incomplete_report_and_compilation(self):
        for i, raw in enumerate(('{"x":1,"x":2}', '{"x":NaN}')):
            path = self.root / f"invalid{i}.json"; path.write_text(raw)
            with self.assertRaises(ValueError):
                bars.freeze_fixture(path, self.root / f"invalid{i}-freeze.json")
        obj = bars.Replay(*self.bundle())
        with self.assertRaisesRegex(ValueError, "unfinished_aggregation_report"):
            obj.report()
        with self.assertRaisesRegex(ValueError, "unfinished_compilation"):
            bars.compile_fills(obj)
        with self.assertRaisesRegex(ValueError, "checkpoint_size"):
            bars.Replay.restore(*self.bundle(), "x" * (daily.MAX_BYTES + 1))

    def test_cli_coherent_outputs_bindings_and_exclusive_directory(self):
        script = str(ROOT / "scripts/daily-bars-121.py")
        path, manifest, output = (self.root / n for n in ("cli.json", "cli-frozen.json", "cli-output"))
        for args in (("create-fixture", "no_signal", str(path)), ("freeze", str(path), str(manifest)),
                     ("evaluate", str(path), str(manifest), str(output))):
            result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIs(json.loads(result.stdout)["orders_available"], False)
        saved = (output / "pipeline-report.json").read_bytes()
        result = subprocess.run([sys.executable, script, "evaluate", str(path), str(manifest), str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["reason"], "artifact_exists")
        self.assertEqual((output / "pipeline-report.json").read_bytes(), saved)
        report = json.loads(saved)
        for n, h in report["derived_bindings"].items():
            self.assertEqual(hashlib.sha256((output / n).read_bytes()).hexdigest(), h)


if __name__ == "__main__":
    unittest.main()
