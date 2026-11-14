import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

from forex_demo_lab.cli import evaluate, freeze, read_bars
from forex_demo_lab.collection import RAW_FIELDS, SPEC_FIELDS, capture, clock_observation, require_demo
from forex_demo_lab.ingestion import NATIVE_FIELDS, local_to_utc, normalize

START = datetime(2024, 1, 1, tzinfo=timezone.utc)


class FakeTerminal:
    ACCOUNT_TRADE_MODE_DEMO = 0
    TIMEFRAME_H1 = 16385
    __version__ = "test"

    def __init__(self, mode=0, connected=True):
        self.mode = mode
        self.connected = connected
        self.calls = 0
        self.account_calls = 0
        self.switch_after = None
        values = {k: 0 for k in SPEC_FIELDS}
        values.update(point=.00001, digits=5, currency_base="EUR", currency_profit="USD", visible=True)
        self.symbol = SimpleNamespace(**values)

    def account_info(self):
        self.account_calls += 1
        mode = 2 if self.switch_after and self.account_calls >= self.switch_after else self.mode
        return SimpleNamespace(trade_mode=mode, currency="USD", leverage=100)

    def terminal_info(self):
        return SimpleNamespace(connected=self.connected, trade_allowed=False)

    def symbol_info(self, symbol):
        assert symbol == "EURUSD"
        return self.symbol

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(time=int(datetime.now(timezone.utc).timestamp()))

    def copy_rates_range(self, symbol, timeframe, start, end):
        self.calls += 1
        assert symbol == "EURUSD" and timeframe == self.TIMEFRAME_H1
        assert start.tzinfo is not None and end.tzinfo is not None
        return [{"time": int((start + timedelta(hours=h)).timestamp()), "open": 1.1, "high": 1.101,
                 "low": 1.099, "close": 1.1005, "tick_volume": 50, "spread": 7, "real_volume": 0}
                for h in range(int((end-start).total_seconds()/3600)+1)]


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_rejects_actual_real_contest_unknown_and_boolean_modes(self):
        for mode in (1, 2, -1, 3, None, False, "0"):
            api = FakeTerminal(mode)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                capture(api, START, START+timedelta(hours=2), self.root/"out")
            self.assertEqual(api.calls, 0)
            self.assertFalse((self.root/"out").exists())

    def test_disconnected_missing_account_and_missing_terminal_rejected(self):
        api = FakeTerminal(connected=False)
        with self.assertRaises(ValueError):
            require_demo(api)
        api.connected = True
        api.account_info = lambda: None
        with self.assertRaises(ValueError):
            require_demo(api)
        api = FakeTerminal()
        api.terminal_info = lambda: None
        with self.assertRaises(ValueError):
            require_demo(api)

    def test_account_switch_during_read_rejects_output(self):
        api = FakeTerminal()
        api.switch_after = 5  # init, two clock guards, pre-read, post-read
        with self.assertRaises(ValueError):
            capture(api, START, START+timedelta(hours=2), self.root/"out")
        self.assertEqual(api.calls, 1)
        self.assertFalse((self.root/"out").exists())

    def test_clock_witness_detects_ahead_labels_without_claiming_historical_rules(self):
        api = FakeTerminal()
        api.symbol_info_tick = lambda _: SimpleNamespace(time=int(datetime.now(timezone.utc).timestamp())+10800)
        observation = clock_observation(api)
        self.assertEqual(observation["status"], "ahead_of_utc")
        self.assertFalse(observation["historical_timezone_verified"])

    def test_capture_exact_range_and_no_account_identity(self):
        api = FakeTerminal()
        original = api.account_info
        def sensitive_account():
            value = original()
            value.login = "SHOULD_NEVER_APPEAR"
            value.name = "SHOULD_NEVER_APPEAR"
            value.server = "SHOULD_NEVER_APPEAR"
            return value
        api.account_info = sensitive_account
        result = capture(api, START, START+timedelta(days=29), self.root/"out")
        self.assertEqual(api.calls, 2)
        self.assertEqual(result["rows"], 29*24)
        self.assertEqual(result["last_bar"], (START+timedelta(days=29, hours=-1)).isoformat())
        self.assertNotIn("SHOULD_NEVER_APPEAR", (self.root/"out/capture.json").read_text())
        self.assertEqual(result["current_snapshot"]["account_type"], "demo")
        self.assertFalse(result["current_snapshot"]["terminal_algo_trading"])
        self.assertEqual(hashlib.sha256((self.root/"out/rates.csv").read_bytes()).hexdigest(), result["raw_sha256"])

    def test_empty_or_out_of_range_history_never_published(self):
        for returned in (None, [], [{"time": int((START-timedelta(hours=1)).timestamp())}]):
            api = FakeTerminal()
            api.copy_rates_range = lambda *args: returned
            with self.assertRaises(ValueError):
                capture(api, START, START+timedelta(hours=2), self.root/"out")
            self.assertFalse((self.root/"out").exists())

    def test_foreign_currency_and_invisible_symbol_rejected(self):
        api = FakeTerminal()
        api.symbol.visible = False
        with self.assertRaises(ValueError):
            capture(api, START, START+timedelta(hours=2), self.root/"out")
        api = FakeTerminal()
        api.account_info = lambda: SimpleNamespace(trade_mode=0, currency="EUR")
        with self.assertRaises(ValueError):
            capture(api, START, START+timedelta(hours=2), self.root/"out")


class IngestionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.raw = self.root/"input.csv"
        self.output = self.root/"normalized"
        self.rows = [[(START+timedelta(hours=h)).isoformat(), 1.1, 1.101, 1.099, 1.1005, 100, 7, 0]
                     for h in range(4)]
        self.write_rows()

    def write_rows(self):
        with self.raw.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(RAW_FIELDS)
            writer.writerows(self.rows)

    def normalize(self, **kwargs):
        values = dict(raw=self.raw, output=self.output, source="Test fixture",
                      as_of=START+timedelta(hours=5), spread_pips=1.2,
                      spread_notes="Fixed assumption, not measured", point_size=.00001,
                      api_timezone="Etc/UTC", timezone_notes="Synthetic fixture generated in UTC")
        values.update(kwargs)
        return normalize(**values)

    def test_api_normalization_and_spread_is_assumed_not_bar_minimum(self):
        meta = self.normalize()
        bars = read_bars(self.output/"bars.csv")
        self.assertEqual(len(bars), 4)
        self.assertTrue(all(bar.spread_pips == 1.2 for bar in bars))
        self.assertAlmostEqual(meta["raw_bar_spread_pips"]["min"], .7)
        self.assertFalse(meta["spread_policy"]["historical_execution_spread_verified"])
        self.assertEqual(meta["coverage"]["missing_hours"], 0)

    def test_incomplete_last_candle_removed_and_recorded(self):
        meta = self.normalize(as_of=START+timedelta(hours=3, minutes=30))
        self.assertEqual(meta["coverage"]["rows"], 3)
        self.assertEqual(meta["dropped_incomplete_rows"], 1)

    def test_future_candle_is_error_not_silently_removed(self):
        with self.assertRaises(ValueError):
            self.normalize(as_of=START+timedelta(hours=2))
        self.assertFalse(self.output.exists())

    def test_duplicate_reordered_invalid_price_and_negative_volume(self):
        original = self.rows
        for rows in ([original[0], original[0]], list(reversed(original)),
                     [[original[0][0], 1.1, 1, 1.099, 1.1, 100, 7, 0]],
                     [[original[0][0], 1.1, 1.101, 1.099, 1.1, -1, 7, 0]]):
            self.rows = rows
            self.write_rows()
            with self.assertRaises(ValueError):
                self.normalize()
            self.assertFalse(self.output.exists())

    def test_gap_audit_never_fills_missing_bars(self):
        self.rows = [self.rows[0], self.rows[3]]
        self.write_rows()
        meta = self.normalize()
        self.assertEqual(meta["coverage"]["rows"], 2)
        self.assertEqual(meta["coverage"]["missing_hours"], 2)
        self.assertEqual(len(read_bars(self.output/"bars.csv")), 2)

    def test_native_utf16_tab_export_converts_verified_timezone(self):
        content = "\t".join(NATIVE_FIELDS)+"\n2024.01.01\t02:00:00\t1.1\t1.101\t1.099\t1.1005\t100\t0\t7\n"
        self.raw.write_text(content, encoding="utf-16")
        with self.assertRaises(ValueError):
            self.normalize()
        self.normalize(source_timezone="Africa/Johannesburg", api_timezone=None)
        self.assertEqual(read_bars(self.output/"bars.csv")[0].time, START)

    def test_dst_ambiguity_and_nonexistent_local_time_rejected(self):
        zone = ZoneInfo("Europe/Berlin")
        for value in (datetime(2024, 3, 31, 2), datetime(2024, 10, 27, 2)):
            with self.assertRaises(ValueError):
                local_to_utc(value, zone)
        self.assertEqual(local_to_utc(datetime(2024, 1, 1, 1), zone), START)

    def test_no_double_timezone_shift_for_api_rows(self):
        with self.assertRaises(ValueError):
            self.normalize(source_timezone="Etc/UTC")

    def test_api_labels_require_explicit_interpretation_and_documented_notes(self):
        for changes in ({"api_timezone": None}, {"timezone_notes": ""}):
            with self.assertRaises(ValueError):
                self.normalize(**changes)

    def test_historical_seasonal_mapping_instead_of_fixed_current_offset(self):
        self.rows = [["2024-01-02T00:00:00+00:00", 1.1, 1.101, 1.099, 1.1005, 10, 7, 0],
                     ["2024-07-02T00:00:00+00:00", 1.1, 1.101, 1.099, 1.1005, 10, 7, 0]]
        self.write_rows()
        self.normalize(as_of=datetime(2025, 1, 1, tzinfo=timezone.utc), api_timezone="Europe/Helsinki")
        bars = read_bars(self.output/"bars.csv")
        self.assertEqual(bars[0].time.isoformat(), "2024-01-01T22:00:00+00:00")
        self.assertEqual(bars[1].time.isoformat(), "2024-07-01T21:00:00+00:00")

    def test_captured_ahead_clock_blocks_false_utc_interpretation(self):
        api = FakeTerminal()
        api.symbol_info_tick = lambda _: SimpleNamespace(time=int(datetime.now(timezone.utc).timestamp())+10800)
        meta = capture(api, START, START+timedelta(hours=4), self.root/"capture")
        with self.assertRaisesRegex(ValueError, "contradicts UTC"):
            self.normalize(raw=self.root/"capture/rates.csv", capture_path=self.root/"capture/capture.json",
                           as_of=datetime.fromisoformat(meta["captured_utc"]))

    def test_bad_header_empty_data_or_nonfinite_spread_rejected(self):
        with self.assertRaises(ValueError):
            self.normalize(spread_pips=float("nan"))
        for content in ("", "bad,header\n", ",".join(RAW_FIELDS)+"\n"):
            self.raw.write_text(content)
            with self.assertRaises(ValueError):
                self.normalize()

    def test_errors_do_not_echo_bad_row_values(self):
        self.rows[0][1] = "PRIVATE_VALUE"
        self.write_rows()
        with self.assertRaises(ValueError) as caught:
            self.normalize()
        self.assertNotIn("PRIVATE_VALUE", str(caught.exception))

    def test_refuses_overwrite(self):
        self.normalize()
        with self.assertRaises(FileExistsError):
            self.normalize()

    def test_capture_provenance_checks_hash_point_size_and_asof(self):
        meta = capture(FakeTerminal(), START, START+timedelta(hours=4), self.root/"capture")
        raw = self.root/"capture/rates.csv"
        capture_path = self.root/"capture/capture.json"
        as_of = datetime.fromisoformat(meta["captured_utc"])
        for change in ({"point_size": .0001}, {"as_of": START+timedelta(hours=5)}):
            args = dict(raw=raw, capture_path=capture_path, as_of=as_of)
            args.update(change)
            with self.assertRaises(ValueError):
                self.normalize(**args)
        self.normalize(raw=raw, capture_path=capture_path, as_of=as_of)
        with raw.open("a") as stream:
            stream.write("\n")
        with self.assertRaises(ValueError):
            self.normalize(raw=raw, output=self.root/"second", capture_path=capture_path, as_of=as_of)

    def test_market_experiment_requires_matching_provenance(self):
        meta = capture(FakeTerminal(), START, START+timedelta(hours=120), self.root/"capture")
        self.normalize(raw=self.root/"capture/rates.csv", capture_path=self.root/"capture/capture.json",
                       as_of=datetime.fromisoformat(meta["captured_utc"]))
        config = self.root/"config.json"
        config.write_text("{}")
        bars = self.output/"bars.csv"
        provenance = self.output/"provenance.json"
        manifest = self.root/"experiment.json"
        args = (bars, config, "2024-01-04T00:00:00Z", manifest, "fixture", "assumed costs", False)
        with self.assertRaises(ValueError):
            freeze(*args)
        freeze(*args, provenance_path=provenance)
        result = evaluate(bars, manifest, "holdout", self.root/"result.json")
        self.assertEqual(result["status"], "unvalidated_ohlc_research")
        self.assertEqual(result["rows"], 48)
        self.assertIsNotNone(result["experiment"]["provenance"])
        meta = json.loads(provenance.read_text())
        meta["data_sha256"] = "mismatch"
        provenance.write_text(json.dumps(meta))
        with self.assertRaises(ValueError):
            freeze(bars, config, "2024-01-04T00:00:00Z", self.root/"bad.json", "fixture", "costs", False, provenance)


if __name__ == "__main__":
    unittest.main()
