"""Phase 9 account isolation and restart checks on invented Level B and Q inputs."""
from fractions import Fraction
import unittest

from forex_demo_lab.trendline import breaks, data, fills, ledger, quote_replay, quotes, risk
from test_trendline_data_163 import stream_for
from test_trendline_entries_174 import fixture
from test_trendline_exits_181 import suffix
from test_trendline_quotes_185 import document, history, midpoint, row


class LevelBIsolationTests(unittest.TestCase):
    def test_interleaved_cost_runs_keep_their_own_reservation_cash_and_pause(self):
        value, prefix = fixture()
        continuation = suffix(value, prefix, ("104.4", "104.9", "103.2", "104.4"), ("85",) * 4)
        rows = prefix + continuation
        for hour in rows:
            for side in ("open", "high", "low", "close"):
                hour[side] = fills.text(Fraction("1.1") + (Fraction(hour[side]) - 100) / 1000)
        stream = stream_for(value, rows)
        replay = breaks.BreakReplay(stream.source, "0.0001")
        for bar in stream.bars():
            if bar.timeframe == "H4":
                replay.observe(bar)
        setups = data.canonical(replay.checkpoint())
        reserved_at, filled_at, gap_receipt = (continuation[0]["start"], continuation[0]["available_at"],
                                               continuation[1]["available_at"])

        def run(cost, cutoff):
            visible = [data.Hour.from_record(hour, "bid_only") for hour in rows if hour["available_at"] <= cutoff]
            return ledger.evaluate(replay, visible, as_of=cutoff, cost_profile=cost)

        reserved = {cost: run(cost, reserved_at) for cost in ("base", "adverse")}
        for result in reserved.values():
            self.assertEqual(("RESERVED", "RESERVATION", "10000"),
                             (result["status"], result["active"]["kind"], result["account"]["cash_usd"]))
            self.assertEqual(1, len(result["decisions"]))
            self.assertFalse(result["positions"])
        self.assertNotEqual(reserved["base"]["active"]["attempt_id"], reserved["adverse"]["active"]["attempt_id"])

        held_base = run("base", filled_at)
        held_snapshot = data.canonical(held_base)
        closed_adverse = run("adverse", gap_receipt)
        self.assertTrue(closed_adverse["account"]["entries_paused"])
        self.assertEqual(held_snapshot, data.canonical(run("base", filled_at)))
        self.assertEqual(held_snapshot, data.canonical(held_base))
        self.assertFalse(held_base["account"]["entries_paused"])
        self.assertEqual("OPEN", held_base["status"])

        closed_base = run("base", gap_receipt)
        for cost, result in (("base", closed_base), ("adverse", closed_adverse)):
            [trade] = result["trades"]
            [position] = result["positions"]
            self.assertEqual(reserved[cost]["active"]["attempt_id"], trade["attempt_id"])
            self.assertEqual(("STOP_OPEN_GAP", gap_receipt), (trade["reason"], position["release_at"]))
            self.assertTrue(result["account"]["entries_paused"])
            self.assertIsNone(result["active"])
            self.assertFalse(result["orders_available"])
        self.assertNotEqual(closed_base["trades"][0]["commission_usd"], closed_adverse["trades"][0]["commission_usd"])
        self.assertEqual(data.canonical(closed_adverse), data.canonical(run("adverse", gap_receipt)))
        self.assertEqual(setups, data.canonical(replay.checkpoint()))


class LevelQCheckpointTests(unittest.TestCase):
    settings = {"tick": "0.0001", "profile": "TRL_BRK3_E1", "cost": "base", "enable_dly": False}

    @classmethod
    def setUpClass(cls):
        value, prefix = fixture(final_sessions=(24, 24, 24))
        value["calendar"]["finalization_delay_ms"] = 1000
        trigger = prefix[-1]["end"]
        continuation = suffix(value, prefix, *[("104.4", "104.9", "103.2", "104.4")] * 8)
        observations = history(continuation)
        observations.insert(3, midpoint(trigger + 1001, "104.4"))
        cls.protection_at = continuation[-1]["end"] + 1000
        cls.protected_receipt = cls.protection_at + 800
        cls.gap_receipt = cls.protection_at + 1500
        cls.midnight = (cls.gap_receipt // risk.UTC_DAY_MS + 1) * risk.UTC_DAY_MS
        cls.reset_receipt = cls.midnight + 750
        observations.extend((
            row(cls.protection_at - 500, "1.10265", "1.10275", cls.protection_at + 1),
            row(cls.protection_at + 2, "1.103", "1.1031", cls.protected_receipt),
            row(cls.protection_at + 4, "1.085", "1.0851", cls.gap_receipt),
            row(cls.midnight + 1, "1.104", "1.1041", cls.reset_receipt),
        ))
        cls.tape = quotes.Tape(document(value, history(prefix) + observations))
        cls.protected = quote_replay.evaluate(cls.tape, as_of=cls.protected_receipt, **cls.settings)
        cls.paused = quote_replay.evaluate(cls.tape, as_of=cls.gap_receipt, **cls.settings)
        cls.before_reset = quote_replay.evaluate(cls.tape, as_of=cls.reset_receipt - 1, **cls.settings)
        cls.full = quote_replay.evaluate(cls.tape, as_of=cls.reset_receipt, **cls.settings)

    def resume(self, snapshot, cutoff):
        return quote_replay.restore(self.tape, quote_replay.checkpoint(snapshot), as_of=cutoff, **self.settings)

    def test_restart_after_e1_tightens_preserves_protection_and_prices_the_later_gap_once(self):
        [position] = self.protected["positions"]
        [change] = position["protection_events"]
        self.assertEqual(("OPEN", "STOP_TIGHTENED", self.protection_at),
                         (self.protected["status"], change["reason"], change["decision_at"]["time"]))
        self.assertGreater(Fraction(change["stop"]), Fraction(change["old_stop"]))
        self.assertEqual(change["stop"], self.protected["open_liability"]["stop"])
        final_mark = self.protected["events"][-1]
        self.assertEqual((self.protection_at + 2, self.protected_receipt),
                         (final_mark["effective_at"], final_mark["available_at"]))
        self.assertFalse(self.protected["trades"])

        continued = self.resume(self.protected, self.reset_receipt)
        self.assertEqual(data.canonical(self.full), data.canonical(continued))
        [trade] = continued["trades"]
        self.assertEqual(("STOP_QUOTE", "1.08498"), (trade["reason"], trade["exit_price"]))
        self.assertGreater(Fraction(trade["realized_loss_excess_usd"]), 0)
        self.assertEqual(self.gap_receipt, continued["positions"][0]["release_at"])
        self.assertEqual(1, sum(event["kind"] == "EXIT_FILL" for event in continued["events"]))
        self.assertEqual(self.protected["events"], [event for event in continued["events"]
                                                    if event["available_at"] <= self.protected_receipt])

    def test_restart_after_loss_keeps_pause_until_next_day_reference_receipt(self):
        self.assertTrue(self.paused["account"]["entries_paused"])
        self.assertEqual(self.paused["events"], self.before_reset["events"])
        self.assertEqual(self.paused["account"], self.before_reset["account"])
        self.assertEqual(data.canonical(self.before_reset), data.canonical(self.resume(self.paused, self.reset_receipt - 1)))
        self.assertEqual(data.canonical(self.full), data.canonical(self.resume(self.paused, self.reset_receipt)))
        [reset] = self.full["events"][len(self.paused["events"]):]
        self.assertEqual(("DAY_REFERENCE", self.midnight, self.reset_receipt),
                         (reset["kind"], reset["effective_at"], reset["available_at"]))
        self.assertEqual(self.paused["account"]["cash_usd"], reset["account"]["reference_equity_usd"])
        self.assertFalse(reset["account"]["entries_paused"])
        forged = {**self.paused, "account": {**self.paused["account"], "entries_paused": False}}
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            self.resume(forged, self.reset_receipt)
