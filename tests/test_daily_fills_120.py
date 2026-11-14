from copy import deepcopy
from dataclasses import asdict
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
from forex_demo_lab import daily_fills_120 as fills
from forex_demo_lab.daily_fills_fixture_120 import CASES, fixture
from test_daily_features_118 import oracle, reline

ROOT = Path(__file__).resolve().parents[1]
F = lambda x: Fraction(str(x))


def audit_ledger(value, report):
    """Independent rational accounting/guard reference, with hardcoded contracts.

    Production fill, sizing, quote, mark and financing methods are never called.
    Retained118 features are checked against the independent moments/TR oracle.
    """
    name, candidate = report["profile"], report["candidate"]
    slip, fee, floor, long_rate, short_rate = ((F(.00002), F(7), F(0), F(-3), F(-1.5)) if name == "base"
                                             else (F(.00005), F(10), F(.00012), F(-4.5), F(-2.25)))
    cash = equity = peak = F(value["initial_account"]["balance_usd"])
    dd, held, reserved, last, day, anchor, paused = F(0), None, False, None, None, equity, False
    used = set()
    rows = report["final_state"]["ledger"]
    cursor = 0
    gross_total = commissions = finance_total = F(0)
    count = 0

    def close_number(actual, expected):
        assert abs(F(actual) - expected) <= F("1e-35"), (actual, str(expected))

    def record(kind, event, numbers=None, **fields):
        nonlocal cursor
        assert cursor < len(rows), kind
        row = rows[cursor]
        assert row["index"] == cursor and row["kind"] == kind and row["sequence"] == event["sequence"], row
        assert row["source_msc"] == event["source_msc"]
        for k, v in fields.items():
            assert row[k] == v, (k, row[k], v)
        for k, v in (numbers or {}).items():
            close_number(row[k], v)
        cursor += 1
        return row

    def quotes(event):
        bid = F(event["bid"])
        spread = max(F(event["ask"]) - bid, floor)
        return bid, bid + spread, spread

    def mark():
        nonlocal equity, peak, dd, paused
        equity = cash
        margin = F(0)
        if held:
            bid, ask, _ = quotes(last)
            equity += held["side"] * ((bid if held["side"] == 1 else ask) - held["entry"]) * held["lots"] * 100000
            margin = held["margin"]
        peak = max(peak, equity)
        dd = max(dd, (peak - equity) / peak)
        paused = paused or equity <= anchor * F(.99)
        return {"balance_usd": cash, "equity_usd": equity, "margin_usd": margin, "free_margin_usd": equity - margin}

    def exit_position(event, reason, price):
        nonlocal cash, held, reserved, gross_total, commissions, count
        assert held and reserved
        gross = held["side"] * (price - held["entry"]) * held["lots"] * 100000
        charge = held["lots"] * fee / 2
        cash += gross - charge
        net = gross - charge - held["entry_fee"] + held["financing"]
        record("exit_fill", event, {"price": price, "lots": held["lots"], "gross_usd": gross,
                "fee_usd": charge, "financing_usd": held["financing"], "net_trade_usd": net,
                "balance_usd": cash, "estimated_stop_risk_usd": held["estimate"]},
               position_id=held["id"], side=held["side"], reason=reason)
        record("release", event, position_id=held["id"])
        gross_total += gross
        commissions += charge
        count += 1
        held, reserved = None, False

    outcomes = report["final_state"]["outcomes"]
    assert len(outcomes) == len(value["events"])
    for i, event in enumerate(value["events"]):
        out = outcomes[i]
        request = {**value["features"], "target_session_id": event["target_session_id"],
                   "decision_msc": event["feature_decision_msc"]}
        feature = daily.decisions(request)[candidate]
        bars = [b for b in request["bars"] if b["session_id"] <= request["target_session_id"]]
        if candidate != "CASH" and len(bars) >= 253:
            ret, (old, new), distance = oracle(request)
            trend = (ret > 0) - (ret < 0)
            mr = 0 if old is None or new is None else 1 if old < -2 <= new else -1 if old > 2 >= new else 0
            score = trend if candidate == "T12_D" else mr if candidate == "MR20_D" else (trend + mr) / 2
            side = (score > 0) - (score < 0) if distance else 0
            assert feature.side == side and feature.risk_multiplier == (abs(score) if distance else 0)
            assert abs(feature.stop_distance - distance) <= 1e-12
        assert out["feature_binding"] == daily._digest(asdict(feature))
        assert (out["feature_side"], out["risk_multiplier"]) == (feature.side, feature.risk_multiplier)
        new_day = event["source_msc"] // daily.DAY
        if day != new_day:
            day, anchor, paused = new_day, equity, False
        had_position = held is not None
        if held:
            for old_day in range(held["day"], day):
                weekday = datetime.fromtimestamp(old_day * daily.DAY / 1000, timezone.utc).weekday()
                multiplier = 0 if weekday >= 5 else 3 if weekday == 2 else 1
                amount = (long_rate if held["side"] == 1 else short_rate) * held["lots"] * multiplier
                cash += amount
                held["financing"] += amount
                finance_total += amount
                record("financing", event, {"amount_usd": amount, "balance_usd": cash}, position_id=held["id"],
                       rollover_msc=(old_day + 1) * daily.DAY, weekday=weekday, multiplier=multiplier)
            held["day"] = day
        bid, ask, spread = quotes(event)
        previous = value["events"][i - 1] if i else None
        repeated = previous is not None and event["source_msc"] == previous["source_msc"]
        session = next(s for s in request["calendar"]["sessions"] if s["start_msc"] <= event["source_msc"] < s["end_msc"])
        executable = not repeated and event["receipt_msc"] - event["source_msc"] <= 2000 and session["status"] == "trading"
        assert out["execution_quote"] is executable and out["held_at_arrival"] is had_position
        if executable:
            last = event
            if held:
                price = bid if held["side"] == 1 else ask
                if held["side"] * (price - held["stop"]) <= 0:
                    exit_position(event, "stop", price - held["side"] * slip)
                elif held["side"] * (price - held["target"]) >= 0:
                    exit_position(event, "target", held["target"])
        account = mark()
        for k, v in account.items():
            close_number(out["pre_entry_account"][k], v)
        key = str(feature.target_session_id)
        latest = max((b["session_id"] for b in request["bars"] if b["available_msc"] <= event["receipt_msc"]), default=None)
        if event["source_msc"] <= feature.decision_msc:
            reason = "before_feature"
        elif event["receipt_msc"] - event["source_msc"] > 2000:
            reason = "stale_quote"
        elif repeated:
            reason = "repeated_source"
        elif session["status"] != "trading":
            reason = "closed_quote"
        elif latest != feature.target_session_id:
            reason = "stale_feature"
        elif spread > F(.00015):
            reason = "wide_quote"
        elif key in used:
            reason = "session_consumed"
        else:
            used.add(key)
            if had_position:
                reason = "held_position"
            elif paused:
                reason = "daily_pause"
            elif not feature.side or not feature.risk_multiplier:
                reason = "inactive_signal"
            elif equity <= 0:
                reason = "nonpositive_equity"
            else:
                side, distance = feature.side, F(feature.stop_distance)
                entry = ask + slip if side == 1 else bid - slip
                stop, target = entry - side * distance, entry + side * 2 * distance
                budget = equity * F(.0025) * F(feature.risk_multiplier)
                stop_per = (distance + slip) * 100000 + fee
                immediate_per = (spread + 2 * slip) * 100000 + fee
                margin_per = entry * 100000 / 30
                risk_lots, margin_lots = budget / stop_per, max(F(0), account["free_margin_usd"]) / (margin_per + fee / 2)
                lots = F(int(min(risk_lots, margin_lots, F(1)) * 100)) / 100
                if distance <= spread + slip or min(entry, stop, target) <= 0:
                    reason = "price_geometry"
                elif lots < F(.01):
                    reason = "minimum_lot_risk" if risk_lots < F(.01) else "minimum_lot_margin"
                elif equity - lots * immediate_per <= anchor * F(.99):
                    reason = "daily_headroom"
                else:
                    reason = "entry_filled"
                    p = out["proposal"]
                    assert p and not held and not reserved
                    for k, v in {"lots": lots, "entry": entry, "stop": stop, "target": target,
                                  "risk_fraction": F(.0025) * F(feature.risk_multiplier), "risk_budget_usd": budget,
                                  "estimated_stop_risk_usd": lots * stop_per, "margin_usd": lots * margin_per,
                                  "entry_fee_usd": lots * fee / 2, "immediate_liquidation_debit_usd": lots * immediate_per}.items():
                        close_number(p[k], v)
                    assert daily._digest({k: v for k, v in p.items() if k != "proposal_id"}) == p["proposal_id"]
                    record("reserve", event, position_id=p["proposal_id"])
                    reserved = True
                    cash -= lots * fee / 2
                    commissions += lots * fee / 2
                    held = {"side": side, "lots": lots, "entry": entry, "stop": stop, "target": target,
                            "margin": lots * margin_per, "entry_fee": lots * fee / 2, "financing": F(0),
                            "estimate": lots * stop_per, "id": p["proposal_id"], "day": day}
                    record("entry_fill", event, {"lots": lots, "price": entry, "fee_usd": lots * fee / 2,
                           "balance_usd": cash}, position_id=p["proposal_id"], side=side)
                    account = mark()
        assert out["reason"] == reason, (i, out["reason"], reason)
        assert (out["proposal"] is not None) == (reason == "entry_filled")
        for k, v in account.items():
            close_number(out["account"][k], v)
        close_number(out["day_start_equity"], anchor)
        close_number(out["peak_equity_usd"], peak)
        close_number(out["max_drawdown"], dd)
        assert out["paused"] is paused
    if held:
        assert outcomes[-1]["execution_quote"]
        bid, ask, _ = quotes(value["events"][-1])
        exit_position(value["events"][-1], "boundary", (bid if held["side"] == 1 else ask) - held["side"] * slip)
        mark()
    assert cursor == len(rows) and report["final_state"]["held"] is None and report["final_state"]["reservation"] is None
    for k, v in mark().items():
        close_number(report["final_state"][k], v)
    close_number(report["final_state"]["max_drawdown"], dd)
    initial = F(value["initial_account"]["balance_usd"])
    for k, v in {"initial_cash_usd": initial, "final_cash_usd": cash, "toy_net_usd": cash - initial,
                  "toy_return": (cash - initial) / initial, "gross_usd": gross_total,
                  "commissions_usd": commissions, "financing_usd": finance_total, "max_drawdown": dd}.items():
        close_number(report["summary"][k], v)
    assert report["summary"]["closed_positions"] == count
    assert cash - initial == gross_total - commissions + finance_total
    return {"ledger_records": len(rows), "marks": len(outcomes), "closed_positions": count}


class Fills120Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0

    def bundle(self, value=None):
        self.serial += 1
        path, manifest = self.root / f"case{self.serial}.json", self.root / f"freeze{self.serial}.json"
        daily.write_new(path, fixture() if value is None else value)
        fills.freeze_fixture(path, manifest)
        return path, manifest

    def replay(self, case="long_target", profile="base", candidate="MIX50_D"):
        return fills.Replay(*self.bundle(fixture(case)), profile, candidate)

    def run_value(self, value, profile="base", candidate="MIX50_D"):
        report = fills.Replay(*self.bundle(value), profile, candidate).run()
        audit_ledger(value, report)
        return report

    def rewrite(self, checkpoint, change):
        value = json.loads(checkpoint)
        change(value["payload"])
        value["sha256"] = daily._digest(value["payload"])
        return json.dumps(value)

    def reject(self, value, reason):
        with self.assertRaisesRegex(ValueError, "^" + reason + "$"):
            fills.validate_fixture(value)

    def test_matrix_independent_every_fill_and_mark(self):
        for case in CASES:
            value = fixture(case)
            for profile in ("base", "adverse"):
                for candidate in daily.CANDIDATES:
                    with self.subTest(case=case, profile=profile, candidate=candidate):
                        self.run_value(value, profile, candidate)

    def test_long_and_short_entry_spread_slippage_fee(self):
        for case, expected in (("long_target", "1.10012"), ("short_target", "1.09998")):
            obj = self.replay(case)
            obj.step(fixture(case)["events"][0])
            held = obj.state["held"]
            self.assertEqual(held["entry"], expected)
            self.assertEqual(F(obj.state["balance_usd"]), 10000 - F(held["lots"]) * F(3.5))
            self.assertEqual([r["kind"] for r in obj.state["ledger"]], ["reserve", "entry_fill"])
            self.assertEqual(obj.state["reservation"]["status"], "held")

    def test_adverse_floor_and_entry_cost_once(self):
        obj = self.replay(profile="adverse")
        obj.step(fixture()["events"][0])
        held = obj.state["held"]
        self.assertEqual(held["entry"], "1.10017")
        self.assertEqual(F(obj.state["equity_usd"]), 10000 - F(held["lots"]) * (F(17) + F(5)))

    def test_both_targets_fill_original_limit_not_overshoot(self):
        for case in ("long_target", "short_target"):
            report = self.run_value(fixture(case))
            proposal = report["final_state"]["outcomes"][0]["proposal"]
            exit_row = next(r for r in report["final_state"]["ledger"] if r["kind"] == "exit_fill")
            self.assertEqual((exit_row["reason"], exit_row["price"]), ("target", proposal["target"]))
            self.assertGreater(F(report["summary"]["toy_net_usd"]), 0)

    def test_both_stops_use_observed_side_price(self):
        for case, price in (("long_stop", F("1.08998")), ("short_stop", F("1.11012"))):
            report = self.run_value(fixture(case))
            exit_row = next(r for r in report["final_state"]["ledger"] if r["kind"] == "exit_fill")
            self.assertEqual(exit_row["reason"], "stop")
            self.assertEqual(F(exit_row["price"]), price)

    def test_adverse_gaps_exceed_risk_estimate_and_pause(self):
        for case in ("long_gap", "short_gap"):
            report = self.run_value(fixture(case))
            p = report["final_state"]["outcomes"][0]["proposal"]
            self.assertGreater(-F(report["summary"]["toy_net_usd"]), F(p["risk_budget_usd"]))
            self.assertTrue(report["final_state"]["paused"])
            self.assertGreater(F(report["summary"]["max_drawdown"]), F(.01))

    def test_target_equity_no_favorable_raw_quote_peak(self):
        report = self.run_value(fixture("long_target"))
        state = report["final_state"]
        self.assertEqual(state["peak_equity_usd"], state["balance_usd"])
        self.assertEqual(state["outcomes"][-1]["account"]["equity_usd"], state["balance_usd"])

    def test_short_spread_gap_pause_uses_actual_slipped_exit(self):
        value = fixture("short_target")
        value["events"][1].update(bid=1.1, ask=1.3)
        report = self.run_value(value)
        exit_row = next(r for r in report["final_state"]["ledger"] if r["kind"] == "exit_fill")
        self.assertEqual(F(exit_row["price"]), F("1.30002"))
        self.assertTrue(report["final_state"]["paused"])

    def test_boundary_liquidation_costs_once_and_finish_idempotent(self):
        value = fixture("half_risk")
        obj = fills.Replay(*self.bundle(value))
        report = obj.run()
        audit_ledger(value, report)
        self.assertEqual(report["summary"]["toy_net_usd"], "-1.47")
        before = obj.checkpoint()
        self.assertFalse(obj.finish())
        self.assertEqual(obj.checkpoint(), before)
        self.assertEqual([r["reason"] for r in obj.state["ledger"] if r["kind"] == "exit_fill"], ["boundary"])

    def test_invalid_endpoint_not_retroactive_liquidation(self):
        value = fixture("half_risk")
        value["events"][-1]["receipt_msc"] += 2000
        obj = fills.Replay(*self.bundle(value))
        for e in value["events"]:
            obj.step(e)
        before = obj.checkpoint()
        with self.assertRaisesRegex(ValueError, "^missing_executable_endpoint$"):
            obj.finish()
        self.assertEqual(obj.checkpoint(), before)
        self.assertIsNotNone(obj.state["held"])

    def test_repeated_endpoint_cannot_force_exit(self):
        value = fixture("half_risk")
        value["events"][1].update(source_msc=value["events"][0]["source_msc"])
        with self.assertRaisesRegex(ValueError, "missing_executable_endpoint"):
            fills.Replay(*self.bundle(value)).run()

    def test_flat_invalid_endpoint_permitted(self):
        value = fixture("opposing")
        value["events"][-1]["receipt_msc"] += 2000
        report = self.run_value(value)
        self.assertEqual(report["summary"]["toy_net_usd"], "0")

    def test_weekend_financing_all_rollovers_including_zero(self):
        report = self.run_value(fixture("weekend_financing"))
        rows = [r for r in report["final_state"]["ledger"] if r["kind"] == "financing"]
        self.assertEqual([r["weekday"] for r in rows], [2, 3, 4, 5, 6])
        self.assertEqual([r["multiplier"] for r in rows], [3, 1, 1, 0, 0])
        lots = F(report["final_state"]["outcomes"][0]["proposal"]["lots"])
        self.assertEqual(F(report["summary"]["financing_usd"]), -15 * lots)

    def test_short_financing_and_adverse_debits(self):
        for profile in ("base", "adverse"):
            value = fixture("weekend_financing")
            value["features"] = fixture("short_target")["features"]
            report = self.run_value(value, profile, "T12_D")
            lots = F(report["final_state"]["outcomes"][0]["proposal"]["lots"])
            self.assertEqual(F(report["summary"]["financing_usd"]), lots * (F(-7.5) if profile == "base" else F(-11.25)))

    def test_financing_not_charged_before_exact_midnight_entry(self):
        value = fixture("weekend_financing")
        value["events"][0]["source_msc"] = value["events"][0]["source_msc"] // daily.DAY * daily.DAY
        value["events"][0]["receipt_msc"] = value["events"][0]["source_msc"] + 2
        value["initial_account"]["available_msc"] = value["events"][0]["source_msc"] - 1
        bar = max((b for b in value["features"]["bars"] if b["available_msc"] <= value["events"][0]["source_msc"]),
                  key=lambda b: b["session_id"])
        value["events"][0].update(target_session_id=bar["session_id"], feature_decision_msc=bar["available_msc"])
        report = self.run_value(value)
        rows = [r for r in report["final_state"]["ledger"] if r["kind"] == "financing"]
        self.assertEqual(len(rows), 5)
        self.assertGreater(rows[0]["rollover_msc"], value["events"][0]["source_msc"])

    def test_release_only_after_closed_accounting_and_next_session_entry(self):
        report = self.run_value(fixture("release_next_session"))
        state = report["final_state"]
        self.assertEqual(report["summary"]["closed_positions"], 2)
        self.assertEqual([o["reason"] for o in state["outcomes"]],
                         ["entry_filled", "session_consumed", "session_consumed", "entry_filled", "session_consumed"])
        for i, row in enumerate(state["ledger"]):
            if row["kind"] == "release":
                self.assertEqual(state["ledger"][i - 1]["kind"], "exit_fill")
        self.assertIsNone(state["reservation"])

    def test_held_first_opportunity_consumed_even_when_exits(self):
        value = fixture("release_next_session")
        value["events"][1].update(bid=1.1, ask=1.1001)
        value["events"][3].update(bid=1.12, ask=1.1201)
        report = self.run_value(value)
        self.assertEqual(report["final_state"]["outcomes"][3]["reason"], "held_position")
        self.assertEqual(report["final_state"]["outcomes"][4]["reason"], "session_consumed")
        self.assertEqual(report["summary"]["closed_positions"], 1)

    def test_held_signal_change_retains_original_size_levels(self):
        value = fixture("release_next_session")
        for e in value["events"]:
            e.update(bid=1.1, ask=1.1001)
        obj = fills.Replay(*self.bundle(value))
        obj.step(value["events"][0])
        original = obj.state["held"]
        for e in value["events"][1:]:
            obj.step(e)
        for key in ("lots", "entry", "stop", "target", "risk_fraction"):
            self.assertEqual(obj.state["held"][key], original[key])
        self.assertEqual(obj.state["outcomes"][3]["risk_multiplier"], .5)

    def test_quality_guards_wide_exit_stale_and_repeat_no_fills(self):
        report = self.run_value(fixture("quality_guards"))
        self.assertEqual([o["reason"] for o in report["final_state"]["outcomes"]],
                         ["wide_quote", "stale_quote", "entry_filled", "repeated_source", "wide_quote", "session_consumed"])
        self.assertEqual([r["sequence"] for r in report["final_state"]["ledger"] if r["kind"] == "exit_fill"], [4])

    def test_stale_breach_keeps_previous_mark_then_valid_gap_fills(self):
        value = fixture("long_gap")
        value["events"][1]["receipt_msc"] += 2000
        e = {**value["events"][1], "sequence": 2, "source_msc": value["events"][1]["source_msc"] + 3000}
        e["receipt_msc"] = e["source_msc"] + 2
        value["events"].append(e)
        report = self.run_value(value)
        outs = report["final_state"]["outcomes"]
        self.assertEqual(outs[1]["account"], outs[0]["account"])
        self.assertEqual([r["sequence"] for r in report["final_state"]["ledger"] if r["kind"] == "exit_fill"], [2])

    def test_closure_quote_no_fill_but_rollovers_debited(self):
        value = fixture("weekend_financing")
        begin = value["events"][0]["source_msc"]
        saturday = {**value["events"][0], "sequence": 1, "source_msc": begin + 3 * daily.DAY,
                    "receipt_msc": begin + 3 * daily.DAY + 2, "bid": .9, "ask": .9001}
        value["events"][-1]["sequence"] = 2
        value["events"].insert(1, saturday)
        report = self.run_value(value)
        self.assertEqual(report["final_state"]["outcomes"][1]["reason"], "closed_quote")
        self.assertFalse(report["final_state"]["outcomes"][1]["execution_quote"])

    def test_stale_feature_blocks_entry_but_not_exit(self):
        value = fixture("release_next_session")
        value["events"][1].update(bid=1.1, ask=1.1001)
        value["events"][3].update(bid=.9, ask=.9001, target_session_id=value["events"][0]["target_session_id"],
                                 feature_decision_msc=value["events"][0]["feature_decision_msc"])
        report = self.run_value(value)
        self.assertEqual(report["final_state"]["outcomes"][3]["reason"], "stale_feature")
        self.assertTrue(report["final_state"]["outcomes"][3]["paused"])
        self.assertEqual(report["final_state"]["outcomes"][4]["reason"], "daily_pause")

    def test_day_anchor_precedes_financing_and_gap(self):
        value = fixture("weekend_financing")
        value["events"][-1].update(bid=.9, ask=.9001)
        report = self.run_value(value)
        outs = report["final_state"]["outcomes"]
        self.assertEqual(outs[1]["day_start_equity"], outs[0]["account"]["equity_usd"])
        self.assertTrue(outs[1]["paused"])

    def test_pause_latched_after_same_day_recovery(self):
        value = fixture("long_gap")
        value["events"].append({**value["events"][0], "sequence": 2,
                                "source_msc": value["events"][-1]["source_msc"] + 1000,
                                "receipt_msc": value["events"][-1]["receipt_msc"] + 1000})
        report = self.run_value(value)
        self.assertTrue(report["final_state"]["outcomes"][-1]["paused"])

    def test_day_reset_after_loss_does_not_increase_stakes(self):
        value = fixture("release_next_session")
        value["events"][1].update(bid=.9, ask=.9001)
        report = self.run_value(value)
        outs = report["final_state"]["outcomes"]
        self.assertTrue(outs[1]["paused"])
        self.assertFalse(outs[3]["paused"])
        self.assertLess(F(outs[3]["proposal"]["risk_budget_usd"]), F(outs[0]["proposal"]["risk_budget_usd"]))

    def test_minimum_capital_abstains_without_fees(self):
        report = self.run_value(fixture("minimum_capital"))
        self.assertEqual(report["final_state"]["outcomes"][0]["reason"], "minimum_lot_risk")
        self.assertEqual(report["final_state"]["ledger"], [])

    def test_minimum_margin_abstains_on_large_notional(self):
        value = fixture("half_risk")
        for e in value["events"]:
            e.update(bid=100000., ask=100000.0001)
        report = self.run_value(value)
        self.assertEqual(report["final_state"]["outcomes"][0]["reason"], "minimum_lot_margin")
        self.assertEqual(report["final_state"]["ledger"], [])

    def test_exact_margin_boundary_and_volume_floor(self):
        value = fixture()
        feature = daily.decisions(value["features"])["MIX50_D"]
        event = {**value["events"][0], "bid": 1.19988, "ask": 1.19998}
        with localcontext() as ctx:
            ctx.prec = 50
            proposal, reason = fills._size(feature, event, fills.risk.profiles()["base"], Decimal(10000),
                                           Decimal("40.035"), Decimal(0), "boundary", "MIX50_D")
            self.assertEqual((proposal["lots"], proposal["entry"], reason), ("0.01", "1.2", "entry_filled"))
            proposal, reason = fills._size(feature, event, fills.risk.profiles()["base"], Decimal(10000),
                                           Decimal("40.034999999999"), Decimal(0), "boundary", "MIX50_D")
            self.assertEqual((proposal, reason), (None, "minimum_lot_margin"))

    def test_daily_headroom_after_wide_gap_exit_without_consumption(self):
        value = fixture("release_next_session")
        for e in value["events"]:
            e.update(bid=1.1, ask=1.1001)
        feature = daily.decisions(value["features"])["MIX50_D"]
        lots = F(int(F(25) / ((F(feature.stop_distance) + F(.00002)) * 100000 + 7) * 100)) / 100
        anchor = 10000 - lots * F(15.5)
        desired_cash = anchor * F(.99) + F(.01)
        financing = F(0)
        for day in range(value["events"][0]["source_msc"] // daily.DAY, value["events"][3]["source_msc"] // daily.DAY):
            weekday = datetime.fromtimestamp(day * daily.DAY / 1000, timezone.utc).weekday()
            financing -= lots * 3 * (0 if weekday >= 5 else 3 if weekday == 2 else 1)
        price = F("1.10012") + (desired_cash - 10000 + lots * 7 - financing) / (lots * 100000) + F(.00002)
        value["events"][3].update(bid=float(price), ask=float(price + F(.0002)))
        report = self.run_value(value)
        outs = report["final_state"]["outcomes"]
        self.assertEqual(outs[3]["reason"], "wide_quote")
        self.assertFalse(outs[3]["paused"])
        self.assertEqual(outs[4]["reason"], "daily_headroom")
        self.assertEqual(report["summary"]["closed_positions"], 1)

    def test_open_financing_loss_pause_then_equity_recovery_stays_latched(self):
        value = fixture("half_risk")
        features = value["features"]
        for bar in features["bars"]:
            price = 1.09 if bar["session_id"] < features["target_session_id"] - 25 else 1.1
            bar.update(open=price, high=price + .00002, low=price - .00002, close=price)
            reline(features, bar)
        # Extend the already declared invented calendar; no market data is read.
        for _ in range(80):
            previous = features["calendar"]["sessions"][-1]
            start = previous["end_msc"]
            weekday = datetime.fromtimestamp(start / 1000, timezone.utc).weekday()
            row = {"session_id": previous["session_id"] + 1, "start_msc": start, "end_msc": start + daily.DAY,
                   "status": "closure" if weekday >= 5 else "trading"}
            features["calendar"]["sessions"].append(row)
            if row["status"] == "trading":
                bar = {"session_id": row["session_id"], "start_msc": start, "end_msc": start + daily.DAY,
                       "observation_msc": start + daily.DAY - 1000, "available_msc": start + daily.DAY + 1000,
                       "open": 1.1, "high": 1.10002, "low": 1.09998, "close": 1.1}
                reline(features, bar)
                features["bars"].append(bar)
        value["events"] = value["events"][:1]
        value["events"][0].update(bid=1.1, ask=1.10001)
        end = next(r["start_msc"] + 2000 for r in features["calendar"]["sessions"]
                   if r["start_msc"] >= value["events"][0]["source_msc"] + 35 * daily.DAY and r["status"] == "trading")
        bar = max((b for b in features["bars"] if b["available_msc"] <= end), key=lambda b: b["session_id"])
        for seq, bid in ((1, 1.1), (2, 1.1003)):
            time = end + (seq - 1) * 1000
            value["events"].append({"sequence": seq, "source_msc": time, "receipt_msc": time + 2,
                                    "bid": bid, "ask": bid + .00001, "target_session_id": bar["session_id"],
                                    "feature_decision_msc": bar["available_msc"]})
        report = self.run_value(value, candidate="T12_D")
        outs = report["final_state"]["outcomes"]
        self.assertTrue(outs[1]["paused"])
        self.assertTrue(outs[1]["held_at_arrival"])
        self.assertGreater(F(outs[2]["account"]["equity_usd"]), F(outs[2]["day_start_equity"]) * F(.99))
        self.assertTrue(outs[2]["paused"])

    def test_nonpositive_slipped_exit_rejected_without_state_change(self):
        value = fixture("long_gap")
        value["events"][1].update(bid=.000001, ask=.000101)
        obj = fills.Replay(*self.bundle(value))
        obj.step(value["events"][0])
        before = obj.checkpoint()
        with self.assertRaisesRegex(ValueError, "^nonpositive_exit_price$"):
            obj.step(value["events"][1])
        self.assertEqual(obj.checkpoint(), before)

    def test_maximum_volume_one_aggregate_position(self):
        value = fixture("half_risk")
        value["initial_account"]["balance_usd"] = 1e6
        report = self.run_value(value)
        self.assertEqual(report["final_state"]["outcomes"][0]["proposal"]["lots"], "1")
        self.assertEqual(report["summary"]["closed_positions"], 1)

    def test_half_full_and_zero_risk(self):
        for case, expected in (("long_target", "0.0025"), ("half_risk", "0.00125"), ("opposing", None)):
            report = self.run_value(fixture(case))
            p = report["final_state"]["outcomes"][0]["proposal"]
            self.assertEqual(p["risk_fraction"] if p else None, expected)

    def test_cash_and_warmup_and_zero_range_no_trades(self):
        for case, candidate in (("long_gap", "CASH"), ("warmup", "MIX50_D"), ("zero_range", "MIX50_D")):
            report = self.run_value(fixture(case), candidate=candidate)
            self.assertEqual(report["summary"]["closed_positions"], 0)
            self.assertEqual(report["summary"]["toy_net_usd"], "0")

    def test_latest_event_idempotent_and_older_event_rejected(self):
        obj = self.replay()
        value = fixture()
        obj.step(value["events"][0])
        checkpoint = obj.checkpoint()
        self.assertFalse(obj.step(value["events"][0]))
        self.assertEqual(obj.checkpoint(), checkpoint)
        obj.step(value["events"][1])
        with self.assertRaisesRegex(ValueError, "event_binding"):
            obj.step(value["events"][0])

    def test_mutated_event_rejected_transactionally(self):
        obj = self.replay()
        e = fixture()["events"][0]
        before = obj.checkpoint()
        with self.assertRaisesRegex(ValueError, "event_binding"):
            obj.step({**e, "bid": 1.0999})
        self.assertEqual(obj.checkpoint(), before)

    def test_state_copy_cannot_change_cash_or_held(self):
        obj = self.replay()
        obj.step(fixture()["events"][0])
        before = obj.checkpoint()
        state = obj.state
        state["held"]["lots"] = "1"
        state["balance_usd"] = "999999"
        self.assertEqual(obj.checkpoint(), before)

    def test_all_prefix_restarts_and_finished_checkpoint(self):
        value = fixture("release_next_session")
        paths = self.bundle(value)
        obj = fills.Replay(*paths)
        for event in value["events"]:
            restored = fills.Replay.restore(*paths, obj.checkpoint())
            self.assertEqual(restored.state, obj.state)
            with patch.object(fills.Replay, "finish", side_effect=AssertionError("future_finish")):
                fills.Replay.restore(*paths, obj.checkpoint())
            obj.step(event)
        obj.finish()
        restored = fills.Replay.restore(*paths, obj.checkpoint())
        self.assertEqual(restored.report(), obj.report())

    def test_restore_never_steps_future(self):
        value = fixture("weekend_financing")
        paths = self.bundle(value)
        obj = fills.Replay(*paths)
        obj.step(value["events"][0])
        original = fills.Replay.step
        def bounded(instance, event):
            if event["sequence"] >= 1:
                raise AssertionError("future_event")
            return original(instance, event)
        with patch.object(fills.Replay, "step", bounded):
            self.assertEqual(fills.Replay.restore(*paths, obj.checkpoint()).state, obj.state)

    def test_rehashed_economic_forgery_rejected(self):
        paths = self.bundle(fixture("weekend_financing"))
        obj = fills.Replay(*paths)
        obj.step(fixture("weekend_financing")["events"][0])
        mutations = [lambda p: p["state"].update(balance_usd="10000"),
                     lambda p: p["state"]["held"].update(lots="1"),
                     lambda p: p["state"]["held"].update(stop="1"),
                     lambda p: p["state"]["held"].update(financing_usd="-999"),
                     lambda p: p["state"].update(free_margin_usd="1"),
                     lambda p: p["state"].update(paused=True),
                     lambda p: p["state"].update(reservation=None),
                     lambda p: p["state"].update(consumed_sessions=[]),
                     lambda p: p["state"]["ledger"][1].update(fee_usd="0")]
        for change in mutations:
            with self.assertRaisesRegex(ValueError, "checkpoint_reconstructed_state"):
                fills.Replay.restore(*paths, self.rewrite(obj.checkpoint(), change))

    def test_checkpoint_cursor_boolean_and_finish_type(self):
        paths = self.bundle()
        obj = fills.Replay(*paths)
        for field, new, reason in (("cursor", False, "checkpoint_cursor"), ("finished", 1, "checkpoint_binding")):
            with self.assertRaisesRegex(ValueError, reason):
                fills.Replay.restore(*paths, self.rewrite(obj.checkpoint(), lambda p: p.update({field: new})))

    def test_checkpoint_profile_candidate_checksum_and_fixture_binding(self):
        paths = self.bundle()
        obj = fills.Replay(*paths)
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            fills.Replay.restore(*paths, obj.checkpoint(), "adverse")
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            fills.Replay.restore(*paths, obj.checkpoint(), candidate="CASH")
        bad = json.loads(obj.checkpoint())
        bad["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            fills.Replay.restore(*paths, json.dumps(bad))
        with self.assertRaisesRegex(ValueError, "checkpoint_binding"):
            fills.Replay.restore(*self.bundle(fixture("short_gap")), obj.checkpoint())

    def test_future_valid_prices_do_not_change_prefix_or_proposal_id(self):
        value = fixture("release_next_session")
        altered = deepcopy(value)
        altered["events"][-1].update(bid=.9, ask=.9001)
        bar = altered["features"]["bars"][-1]
        bar.update(high=1.2, close=1.15)
        reline(altered["features"], bar)
        a, b = fills.Replay(*self.bundle(value)), fills.Replay(*self.bundle(altered))
        for i in range(3):
            a.step(value["events"][i])
            b.step(altered["events"][i])
            self.assertEqual(a.state, b.state)

    def test_feature_identity_change_rejected_transactionally(self):
        value = fixture()
        value["events"][1]["feature_decision_msc"] += 1
        obj = fills.Replay(*self.bundle(value))
        obj.step(value["events"][0])
        before = obj.checkpoint()
        with self.assertRaisesRegex(ValueError, "session_identity_changed"):
            obj.step(value["events"][1])
        self.assertEqual(obj.checkpoint(), before)

    def test_real_contest_boolean_modes_rejected(self):
        for mode in (1, 2, False, True):
            value = fixture()
            value["initial_account"]["trade_mode"] = mode
            self.reject(value, "synthetic_demo_account_required")

    def test_supplied_marks_held_and_credentials_not_accepted(self):
        for key in ("equity_usd", "free_margin_usd", "held", "account_id", "password"):
            value = fixture()
            value["initial_account"][key] = 0
            self.reject(value, "fill_account_fields")
        value = fixture()
        value["events"][0]["equity_usd"] = 10000
        self.reject(value, "fill_event_fields")

    def test_market_clock_and_qualification_flags_rejected(self):
        value = fixture()
        value["clock"] = "broker_time"
        self.reject(value, "invented_fills_fixture_required")
        value = fixture()
        value["qualified"] = True
        self.reject(value, "fill_fixture_fields")

    def test_invalid_numbers_initial_cash_and_crossed_prices(self):
        for new in (True, float("nan"), float("inf"), 0, -1, 1e9 + 1):
            value = fixture()
            value["initial_account"]["balance_usd"] = new
            with self.assertRaises(ValueError):
                fills.validate_fixture(value)
        value = fixture()
        value["events"][0]["bid"] = 2
        self.reject(value, "quote_price")

    def test_event_chronology_conflicts_and_future_feature(self):
        for change, reason in ((lambda v: v["events"][1].update(sequence=3), "event_sequence"),
                               (lambda v: v["events"][1].update(source_msc=v["events"][0]["source_msc"] - 1), "event_order"),
                               (lambda v: v["events"][1].update(source_msc=v["events"][0]["source_msc"]), "source_price_conflict"),
                               (lambda v: v["events"][0].update(receipt_msc=v["events"][0]["source_msc"] - 1), "quote_clock"),
                               (lambda v: v["events"][0].update(feature_decision_msc=v["events"][0]["receipt_msc"] + 1), "future_feature_request")):
            value = fixture()
            change(value)
            self.reject(value, reason)

    def test_missing_completed_session_no_fallback(self):
        value = fixture("release_next_session")
        new_target = value["events"][3]["target_session_id"]
        value["features"]["bars"] = [b for b in value["features"]["bars"] if b["session_id"] != new_target]
        with self.assertRaises(ValueError):
            fills.validate_fixture(value)

    def test_manifest_types_rules_source_and_fixture_tamper(self):
        for mutation in (lambda m: m.update(orders_available=0), lambda m: m.update(market_data_qualified=0),
                         lambda m: m["rules"].update(max_positions=True), lambda m: m.update(sources={}),
                         lambda m: m.update(fixture_sha256="0" * 64)):
            path, manifest = self.bundle()
            data = json.loads(manifest.read_bytes())
            mutation(data)
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "fill_freeze_binding"):
                fills.Replay(path, manifest)

    def test_freeze_time_UTC_required(self):
        path, manifest = self.bundle()
        data = json.loads(manifest.read_bytes())
        data["frozen_at_utc"] = "2001-01-01T00:00:00"
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "freeze_time"):
            fills.Replay(path, manifest)

    def test_strict_JSON_duplicate_nonfinite_and_size(self):
        for raw in ('{"format":1,"format":2}', '{"x":NaN}'):
            path = self.root / f"bad{self.serial}.json"
            self.serial += 1
            path.write_text(raw)
            with self.assertRaises(ValueError):
                fills.freeze_fixture(path, self.root / f"m{self.serial}.json")
        with self.assertRaisesRegex(ValueError, "checkpoint_size"):
            fills.Replay.restore(*self.bundle(), "x" * (daily.MAX_BYTES + 1))

    def test_outputs_and_report_cannot_enable_orders(self):
        report = self.run_value(fixture("long_target"))
        for key in ("orders_available", "real_money_execution_available", "paper_evaluation_available", "market_data_qualified", "strategy_selected"):
            self.assertIs(report[key], False)

    def test_incomplete_report_finish_and_unknown_profile_rejected(self):
        obj = self.replay()
        with self.assertRaisesRegex(ValueError, "unfinished_fills_report"):
            obj.report()
        with self.assertRaisesRegex(ValueError, "unfinished_fills"):
            obj.finish()
        with self.assertRaisesRegex(ValueError, "profile_or_candidate"):
            fills.Replay(*self.bundle(), "live")

    def test_cli_freeze_evaluate_and_no_overwrite(self):
        script = str(ROOT / "scripts/daily-fills-120.py")
        path, manifest, report = (self.root / n for n in ("cli.json", "cli-freeze.json", "cli-report.json"))
        for args in (("create-fixture", "long_target", str(path)), ("freeze", str(path), str(manifest)),
                     ("evaluate", str(path), str(manifest), str(report))):
            result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIs(json.loads(result.stdout)["orders_available"], False)
        saved = report.read_bytes()
        result = subprocess.run([sys.executable, script, "evaluate", str(path), str(manifest), str(report)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["reason"], "artifact_exists")
        self.assertEqual(report.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
