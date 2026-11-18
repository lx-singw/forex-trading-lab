"""Phase 6 setup acceptance against frozen component and candle examples."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace
import unittest

from forex_demo_lab.trendline import breaks, context, entries, fills, geometry, lines
from test_trendline_bounce_177 import fixture as bounce_fixture, run as bounce_replay
from test_trendline_data_163 import calendar, descriptor, rows_for, stream_for
from test_trendline_dly_178 import fixture as dly_fixture, run as dly_replay
from test_trendline_entries_174 import opening_hour
from test_trendline_pivots_166 import bars_for, golden, source_for


def replay(source, bars, profile="TRL_BRK3_E1"):
    result = breaks.BreakReplay(source, "0.1", profile)
    for bar in bars:
        result.observe(bar)
    return result


def opposing_breaks():
    rows = []
    for index in range(51):
        support = Decimal(100) + Decimal(".2") * (index - 51)
        resistance = Decimal(100) - Decimal(".2") * (index - 50)
        padding = min(Decimal(".7"), (resistance - support) / 4)
        low = support if index in (16, 23, 30) else support + padding
        high = resistance if index in (17, 24, 31) else resistance - padding
        rows.append(["99.9", str(high), str(low), "99.9"])
    rows.append(["99.9", "100.1", "99.7", "99.9"])
    return bars_for(rows)


def context_break(side, daily_bias):
    value = descriptor(calendar((4,) * 32 + (24,) * 9, partial=True))
    value["calendar"]["finalization_delay_ms"] = 0
    prehistory = []
    for index in range(32):
        low = 80 + Decimal(".1") * index + (0 if index in (16, 22, 28) else 2)
        high = Decimal(130)
        if daily_bias == "NEUTRAL":
            high = 120 - Decimal(".1") * index - (0 if index in (17, 23, 29) else 2)
        row = (Decimal(104), high, low, Decimal(104))
        if daily_bias == "BEARISH":
            row = (200 - row[0], 200 - row[2], 200 - row[1], 200 - row[3])
        prehistory.append(tuple(map(str, row)))
    prices = prehistory + golden(35, side)["inputs"]["ohlc"]
    hours = rows_for(value)[:len(prices) * 4]
    for index, hour in enumerate(hours):
        hour.update(dict(zip(("open", "high", "low", "close"), prices[index // 4])))
        hour["available_at"] = hour["end"]
    stream = stream_for(value, hours)
    return stream.source, tuple(bar for bar in stream.bars() if bar.timeframe in ("H4", "D1"))


class TrendlineSetupAcceptanceTests(unittest.TestCase):
    def test_g01_declared_pair_exact_stop_and_priced_open_in_both_directions(self):
        for side in ("LONG", "SHORT"):
            case = golden(1, side)
            supplied, expected = case["inputs"], case["expected"]
            index = supplied["bar_index"]
            price = Decimal(supplied["close"])
            previous = SimpleNamespace(close=Decimal(supplied["previous_close"]))
            current = SimpleNamespace(close=price)

            def ray(role):
                anchors = supplied[f"{role}_pivots"]
                start, end = anchors[0], anchors[-1]
                return geometry.Ray(supplied[f"{role}_kind"], *start, *end)

            action, safety = ray("action"), ray("safety")
            state = SimpleNamespace(line_id="declared", line=SimpleNamespace(ray=action))
            self.assertLess(supplied["formed_index"], index)
            self.assertEqual(expected["touches"], len(supplied["action_pivots"]))
            self.assertEqual(Fraction(expected["action_value"]), action.value(index))
            self.assertEqual((state,), breaks._triggered((state,), ("declared",), previous, current,
                                                        index, Fraction(supplied["tick"])))
            self.assertEqual(Fraction(expected["safety_value"]), safety.value(index))
            _, stop = breaks._stop(safety.value(index), Fraction(supplied["atr"]), Fraction(supplied["tick"]), side)
            self.assertEqual(Fraction(expected["stop"]), stop)

            source = source_for(40)
            model = fills.PriceModel(source)
            close = source.calendar.frame("H4")[index].end
            spread = Fraction(supplied["ask"]) - Fraction(supplied["bid"])
            hour = opening_hour(model.entry_window(close), supplied["bid"], fills.text(spread / fills.PIP))
            opening = fills.Opening.from_hour(hour, 1)
            request = {
                "kind": "invented_b_price_request", "direction": side, "trigger_end": close,
                "decision_at": fills.Event(close, 0).record(), "stop": fills.text(stop),
                "target": None, "atr": supplied["atr"], "tick": supplied["tick"], "exit_model": "E1",
            }
            result = model.entry(request, opening)
            self.assertEqual("FILLED", result["status"])
            slip = Fraction(model.costs["slippage_pips"]) * fills.PIP
            self.assertEqual(Fraction(expected["distance"]) + slip, Fraction(result["stop_distance"]))

    def test_g15_opposing_close_breaks_consume_both_after_restart(self):
        source, bars = opposing_breaks()
        baseline = replay(source, bars)
        prefix = replay(source, bars[:-1])
        resumed = breaks.BreakReplay.restore(source, prefix.checkpoint())
        self.assertEqual(baseline.report()["decisions"][-1], resumed.observe(bars[-1]))
        final = resumed.report()
        self.assertEqual(baseline.report(), final)
        decision = final["decisions"][-1]
        self.assertEqual(("ABSTAINED", "OPPOSING_SIGNAL"), (decision["state"], decision["reason"]))
        self.assertCountEqual(("LONG", "SHORT"), [item["direction"] for item in decision["triggered"]])
        consumed = [item["consumed"] for item in final["action_replay"]["journal"]["groups"]]
        self.assertEqual([True, True], consumed)
        after = breaks.BreakReplay.restore(source, resumed.checkpoint())
        self.assertEqual(final, after.report())
        self.assertEqual([], entries.evaluate(after, [], as_of=bars[-1].available)["attempts"])

    def test_g23_retry_on_unpoked_spent_bounce_reports_already_consumed(self):
        expected = golden(23)["expected"]
        source, bars = bounce_fixture(end=58, approaches={
            51: (".5", "1"), 52: (".4", "1"), 58: (".4", "1"),
        })
        prefix = bounce_replay(source, bars[:52])
        resumed = breaks.BreakReplay.restore(source, prefix.checkpoint())
        for bar in bars[52:]:
            decision = resumed.observe(bar)
        self.assertEqual(expected["second_reason"], decision["reason"])
        self.assertTrue(decision["contacts"])
        self.assertEqual([], decision["triggered"])
        journal = resumed.report()["action_replay"]["journal"]
        [group] = journal["groups"]
        self.assertEqual(expected["consumed_after_restart"], group["consumed"])
        self.assertEqual(1, sum(event["command"]["op"] == "TRIGGER" for event in journal["events"]))
        [attempt] = entries.evaluate(resumed, [], as_of=bars[-1].available)["attempts"]
        self.assertEqual(("EXPIRED", "MISSING_ENTRY_BAR"), (attempt["status"], attempt["reason"]))

    def test_completed_d1_bias_filters_actual_brk3_break_after_consumption(self):
        for side, bias, state, reason in (
                ("LONG", "BULLISH", "READY", None), ("SHORT", "BEARISH", "READY", None),
                ("LONG", "BEARISH", "SKIPPED", "CONTEXT_CONFLICT"),
                ("LONG", "NEUTRAL", "SKIPPED", "CONTEXT_NEUTRAL")):
            with self.subTest(side=side, bias=bias):
                source, bars = context_break(side, bias)
                book = replay(source, bars, context.PROFILE)
                report = book.report()
                decision = report["decisions"][-1]
                self.assertEqual((state, reason, side), (decision["state"], decision["reason"], decision["direction"]))
                snapshot = decision["context"]["snapshot"]
                self.assertEqual(bias, snapshot["bias"])
                self.assertLess(snapshot["d1_bar"]["available"], decision["available_at"])
                self.assertTrue(any(g["consumed"] for g in report["action_replay"]["journal"]["groups"]))
                attempts = entries.evaluate(book, [], as_of=bars[-1].available)["attempts"]
                self.assertEqual(["PENDING"] if state == "READY" else [], [row["status"] for row in attempts])
                if state == "SKIPPED":
                    restored = breaks.BreakReplay.restore(source, book.checkpoint())
                    self.assertEqual(report, restored.report())

    def test_restart_preserves_discarded_and_poked_break_decisions(self):
        for state_name, index in (("DISCARDED", 47), ("INVALIDATED", 48)):
            with self.subTest(state=state_name):
                source, bars = bars_for(golden(35)["inputs"]["ohlc"])
                changed = (replace(bars[index], high=Decimal("104.6"), close=Decimal("104.2"))
                           if index == 47 else replace(bars[index], close=Decimal("103.89")))
                bars = [*bars[:index], changed, *bars[index + 1:]]
                before = replay(source, bars[:index])
                restored = breaks.BreakReplay.restore(source, before.checkpoint())
                decision = restored.observe(changed)
                self.assertEqual(state_name, decision["state"])
                after = breaks.BreakReplay.restore(source, restored.checkpoint())
                for bar in bars[index + 1:]:
                    after.observe(bar)
                self.assertEqual(replay(source, bars).report(), after.report())
                self.assertEqual([], entries.evaluate(after, [], as_of=bars[-1].available)["attempts"])

    def test_dly_expiry_restarts_on_both_sides_of_deadline(self):
        source, bars = dly_fixture(end=59, safety_pivot=55)
        prefix = dly_replay(source, bars[:58])
        before = breaks.BreakReplay.restore(source, prefix.checkpoint(), enable_dly=True)
        expired = before.observe(bars[58])
        self.assertEqual(("EXPIRED", "DLY_EXPIRED"), (expired["state"], expired["reason"]))
        after = breaks.BreakReplay.restore(source, before.checkpoint(), enable_dly=True)
        self.assertNotEqual("READY", after.observe(bars[59])["state"])
        self.assertEqual(dly_replay(source, bars, lines.DLY_PROFILE).report(), after.report())
        self.assertEqual([], entries.evaluate(after, [], as_of=bars[-1].available)["attempts"])
