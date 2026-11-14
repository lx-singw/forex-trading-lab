import csv
from datetime import timedelta
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.collection import RAW_FIELDS
from forex_demo_lab.tick_audit import capture_ticks, first_exit, load_ticks, summarize
from test_ingestion import FakeTerminal, START


def tick(ms=0, bid=1.1, ask=1.1001, sequence=0):
    return dict(sequence=sequence, time_msc=int(START.timestamp()*1000)+ms,
                time=int(START.timestamp())+ms//1000, bid=bid, ask=ask, flags=6)


class TickTerminal(FakeTerminal):
    COPY_TICKS_ALL = -1

    def __init__(self):
        super().__init__()
        self.events = [tick(0), tick(500, bid=1.0999), tick(500, bid=1.1000), tick(3599999)]
        self.error = 1

    def last_error(self):
        return self.error, "PRIVATE ERROR MESSAGE NEVER EXPORTED"

    def copy_ticks_range(self, symbol, start, end, flags):
        self.calls += 1
        assert symbol == "EURUSD" and flags == self.COPY_TICKS_ALL
        if self.events is None:
            return None
        return [e for e in self.events if start.timestamp()*1000 <= e["time_msc"] <= end.timestamp()*1000]


class TickCaptureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.folder = self.root/"ticks"
        self.api = TickTerminal()

    def capture(self, hours=1):
        return capture_ticks(self.api, START, START+timedelta(hours=hours), self.folder)

    def test_keeps_millisecond_order_and_last_fractional_second(self):
        self.capture()
        metadata, values = load_ticks(self.folder)
        self.assertEqual(metadata["ticks"], 4)
        self.assertEqual([v["sequence"] for v in values], list(range(4)))
        self.assertEqual(values[1]["time_msc"], values[2]["time_msc"])
        self.assertEqual(values[-1]["time_msc"], tick(3599999)["time_msc"])

    def test_chunk_boundary_tick_kept_once_and_end_excluded(self):
        self.api.events = [tick(0), tick(6*3600000), tick(7*3600000)]
        self.capture(7)
        metadata, values = load_ticks(self.folder)
        self.assertEqual(len(values), 2)
        self.assertEqual([w["excluded_upper_boundary_ticks"] for w in metadata["windows"]], [1, 1])

    def test_real_contest_and_disconnected_rejected_before_fetch(self):
        for mode in (1, 2, -1):
            self.api.mode = mode
            with self.assertRaises(ValueError):
                self.capture()
            self.assertEqual(self.api.calls, 0)
        self.api.mode = 0
        self.api.connected = False
        with self.assertRaises(ValueError):
            self.capture()
        self.assertFalse(self.folder.exists())

    def test_account_switch_after_read_never_publishes_capture(self):
        self.api.switch_after = 5
        with self.assertRaises(ValueError):
            self.capture()
        self.assertFalse((self.folder/"capture.json").exists())
        self.assertFalse((self.folder/"ticks.csv.gz").exists())

    def test_empty_is_not_complete_history_and_api_error_is_distinct(self):
        self.api.events = []
        result = self.capture()
        self.assertEqual(result["windows"][0]["status"], "empty")
        self.assertFalse(result["complete_market_history_verified"])
        self.folder = self.root/"error"
        self.api.events = None
        self.api.error = -4
        result = self.capture()
        self.assertEqual(result["windows"][0]["status"], "api_error")
        self.assertFalse(result["requests_without_api_errors"])
        self.assertNotIn("PRIVATE ERROR", json.dumps(result))

    def test_reversed_tick_order_prevents_publishing(self):
        self.api.events.reverse()
        with self.assertRaises(ValueError):
            self.capture()
        self.assertFalse((self.folder/"capture.json").exists())

    def test_seconds_millisecond_mismatch_and_nonfinite_quotes_rejected(self):
        self.api.events[0]["time"] += 1
        with self.assertRaises(ValueError):
            self.capture()
        self.folder = self.root/"badquote"
        self.api.events = [tick(bid=float("nan"))]
        with self.assertRaises(ValueError):
            self.capture()

    def test_hash_corruption_and_overwrite_rejected(self):
        self.capture()
        with self.assertRaises(FileExistsError):
            self.capture()
        with (self.folder/"ticks.csv.gz").open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaises(ValueError):
            load_ticks(self.folder)

    def test_bounded_request_rejects_unbounded_download(self):
        with self.assertRaises(ValueError):
            self.capture(49)
        self.assertEqual(self.api.calls, 0)

    def test_raw_bar_comparison_detects_gap_ticks_spreads_and_invalid_quotes(self):
        self.api.events += [tick(3600000), tick(3600001, bid=0, ask=0)]
        self.capture(2)
        bars = self.root/"bars.csv"
        with bars.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=RAW_FIELDS)
            writer.writeheader()
            writer.writerow(dict(time=START.isoformat(), open=1.1, high=1.1, low=1.0999,
                                 close=1.1, tick_volume=4, spread_points=1, real_volume=0))
        result = summarize(self.folder, bars)
        self.assertEqual(result["hours"][0]["status"], "ohlc_match")
        self.assertEqual(result["hours"][1]["status"], "ticks_without_reference_bar")
        self.assertEqual(result["invalid_quotes"], 1)
        self.assertEqual(result["same_millisecond_events"], 1)
        self.assertAlmostEqual(result["spread_pips"]["maximum"], 2)


class TickExitTests(unittest.TestCase):
    def test_target_before_stop_follows_tick_order_not_ohlc_stop_first(self):
        result = first_exit([tick(0, 1.102, 1.1021), tick(1, 1.098, 1.0981, 1)], 1, 1.099, 1.102, .2)
        self.assertEqual(result["reason"], "target")
        self.assertEqual(result["sequence"], 0)
        self.assertEqual(result["modeled_exit"], 1.102)

    def test_long_stop_uses_bid_and_gap_quote_plus_slippage(self):
        result = first_exit([tick(0, 1.098, 1.0982)], 1, 1.099, 1.102, .2)
        self.assertEqual(result["reason"], "stop")
        self.assertAlmostEqual(result["modeled_exit"], 1.09798)

    def test_short_stop_uses_ask_even_when_bid_has_not_crossed(self):
        result = first_exit([tick(0, 1.1008, 1.1012)], -1, 1.101, 1.098, .2)
        self.assertEqual(result["reason"], "stop")
        self.assertAlmostEqual(result["modeled_exit"], 1.10122)

    def test_short_target_does_not_trigger_on_bid_alone(self):
        self.assertIsNone(first_exit([tick(0, 1.0979, 1.0981)], -1, 1.101, 1.098, .2))

    def test_same_millisecond_event_order_is_preserved(self):
        result = first_exit([tick(0, 1.098, 1.0981), tick(0, 1.102, 1.1021, 1)], 1, 1.099, 1.102, .2)
        self.assertEqual(result["reason"], "stop")

    def test_zero_quote_and_bad_position_fail_closed(self):
        with self.assertRaises(ValueError):
            first_exit([tick(0, 0, 0)], 1, 1.099, 1.102, .2)
        with self.assertRaises(ValueError):
            first_exit([], 1, 1.102, 1.099, .2)


class GapProbeTests(unittest.TestCase):
    def test_successful_api_response_with_wrong_year_is_not_valid_data(self):
        path = Path(__file__).resolve().parents[1]/"scripts/probe-history-gap.py"
        spec = importlib.util.spec_from_file_location("probe_gap", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = dict(time_label="2026-06-25T03:53:00+00:00", open=1.1, high=1.101,
                   low=1.099, close=1.1, spread_points=0, tick_volume=1)
        problems = module.validate_response([row], START, START+timedelta(hours=1), 60)
        self.assertEqual(problems, [{"row": 0, "problem": "outside_requested_range"}])

    def test_duplicate_and_bad_prices_are_flagged(self):
        path = Path(__file__).resolve().parents[1]/"scripts/probe-history-gap.py"
        spec = importlib.util.spec_from_file_location("probe_gap", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = dict(time_label=START.isoformat(), open=1.1, high=1.0, low=1.099,
                   close=1.1, spread_points=0, tick_volume=1)
        problems = module.validate_response([row, row], START, START+timedelta(hours=1), 3600)
        self.assertEqual([p["problem"] for p in problems],
                         ["invalid_price_or_counts", "duplicate_or_unordered", "invalid_price_or_counts"])


if __name__ == "__main__":
    unittest.main()
