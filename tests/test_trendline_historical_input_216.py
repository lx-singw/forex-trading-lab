"""Exercise the historical reader with a fabricated calendar, H1 bytes and a test-only pin."""

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from forex_demo_lab.elliott_sessions_146 import HOUR
from forex_demo_lab.trendline import (
    data, entries, exits, fills, historical_calendar, historical_count, historical_input, ledger, risk, signal_count, study,
)
from test_trendline_signal_count_194 import PROFILE, bar_fixture
from test_trendline_study_165 import declared, span


def midnight(year):
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()) * 1000


def row(start, end=None):
    if end is None:
        end = start + HOUR
    return {"start": start, "end": end, "available_at": end,
            "open": "1.1", "high": "1.1002", "low": "1.0998", "close": "1.1", "spread_pips": "1.2"}


def session(start, end):
    return {"kind": "session", "start": start, "end": end, "partial": end - start < 23 * HOUR,
            "h1": [*range(start, end, HOUR), end], "h4": [*range(start, end, 4 * HOUR), end]}


def closure(start, end):
    return {"kind": "closure", "start": start, "end": end, "reason": "holiday"}


def assumed_opening(hour):
    return {"kind": "bar_open_assumption", "start": hour["start"], "end": hour["end"],
            "bid": hour["open"], "spread_pips": hour["spread_pips"],
            "source_at": None, "available_at": hour["available_at"]}


def paired_opening(hour, *, source_delay=0, receipt_delay=0):
    source_at = hour["start"] + source_delay
    return {"kind": "paired_quote", "start": hour["start"], "end": hour["end"],
            "bid": "1.1000", "ask": "1.1002", "source_at": source_at, "available_at": source_at + receipt_delay}


class HistoricalInputTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.prices = self.root / "bars.json"
        self.manifest = self.root / "manifest.json"
        self.plan_path = self.root / "plan.json"
        self.calendar_path = self.root / "calendar.json"
        self.plan = declared()
        self.plan.update(case="current_unassigned", source={"alias": "source_existing_export", "route": "existing_export"})
        self.plan["partitions"]["validation"] = study.draft()["partitions"]["validation"]
        development = self.plan["partitions"]["development"]
        development["interval"] = span("2021-01-01", "2023-01-01")
        development["warmup"]["interval"] = span("2020-01-01", "2021-01-01")
        self.plan["endpoints"]["development"]["liquidation_at"] = None
        for evidence in self.plan["evidence"].values():
            evidence["intervals"] = [span("2020-01-01", "2023-01-01")]

        self.seam = midnight(2021)
        day = 24 * HOUR
        first = self.seam - 253 * day
        short_end = self.seam + 5 * HOUR + HOUR // 2
        sessions = [session(start, start + day) for start in range(first, self.seam, day)]
        sessions.append(session(self.seam, short_end))
        self.calendar = {"kind": historical_calendar.KIND, "segments": [
            closure(midnight(2020), first), *sessions, closure(short_end, midnight(2023)),
        ]}
        self.rows = [row(left, right) for item in sessions for left, right in zip(item["h1"], item["h1"][1:])]

    def bundle(self, *, opening_rows=None, **override):
        if opening_rows is None:
            opening_rows = [assumed_opening(hour) for hour in self.rows]
        prices = data.canonical({
            "hours": [{key: value for key, value in hour.items() if key != "spread_pips"} for hour in self.rows],
            "openings": opening_rows,
        })
        self.prices.write_bytes(prices)
        self.plan["input_sha256"] = hashlib.sha256(prices).hexdigest()
        calendar = data.canonical(self.calendar)
        self.calendar_path.write_bytes(calendar)
        self.plan["calendar_sha256"] = hashlib.sha256(calendar).hexdigest()
        plan = data.canonical(self.plan)
        self.plan_path.write_bytes(plan)
        manifest = {"schema": historical_input.VERSION, "kind": historical_input.MANIFEST_KIND,
                    "symbol": "EURUSD", "partition": "development", "plan_file": "plan.json",
                    "plan_file_sha256": hashlib.sha256(plan).hexdigest(), "calendar_file": "calendar.json",
                    "price_file": "bars.json", "tick_size": "0.0001",
                    "same_time_open_order": "decision_before_open", **override}
        content = data.canonical(manifest)
        self.manifest.write_bytes(content)
        return patch.object(historical_input, "REVIEWED_MANIFESTS", frozenset({hashlib.sha256(content).hexdigest()}))

    def test_unreviewed_manifest_leaves_plan_and_prices_unopened(self):
        self.bundle()
        self.plan_path.unlink()
        with patch.object(historical_input, "strict_json", side_effect=AssertionError("no parsing expected")):
            with self.assertRaisesRegex(ValueError, "no recorded qualification"):
                historical_input.load_level_b(self.manifest)

    def test_reviewed_input_yields_typed_rows_with_separate_warmup(self):
        with self.bundle():
            result = historical_input.load_level_b(self.manifest)
        receipt = result.receipt
        self.assertEqual(6072, len(result.warmup))
        self.assertEqual(6, len(result.development))
        self.assertEqual(replace(data.Hour.from_record(self.rows[-1], "bid_only"), spread_pips=None),
                         result.development[-1])
        self.assertIsNone(receipt["actual_counts"])
        self.assertEqual(self.plan["input_sha256"], receipt["input_sha256"])
        self.assertEqual(self.plan["calendar_sha256"], result.calendar.sha256)
        self.assertEqual(253, receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertEqual(2, receipt["development_at_scope_end"]["H4"]["complete_by_cutoff"])
        self.assertEqual(6, receipt["development_openings_at_scope_end"]["status_counts"]["BAR_OPEN_ASSUMPTION"])

    def test_changed_plan_and_overlapping_holdout_stop_before_price_read(self):
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            self.plan_path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "plan differs"):
                historical_input.load_level_b(self.manifest)
        self.plan["partitions"]["validation"]["interval"] = span("2022-01-01", "2024-01-01")
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.assertRaisesRegex(ValueError, "development_scope_overlaps_reserved_validation"):
                historical_input.load_level_b(self.manifest)

    def test_price_hash_is_checked_before_decoding(self):
        with self.bundle(), patch.object(historical_input, "strict_json", wraps=historical_input.strict_json) as decode:
            self.prices.write_bytes(b"malformed price contents")
            with self.assertRaisesRegex(ValueError, "before parsing"):
                historical_input.load_level_b(self.manifest)
        self.assertEqual(3, decode.call_count)

    def test_late_warmup_receipt_does_not_count_at_development_start(self):
        self.rows[6071]["available_at"] = self.seam + 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "warmup coverage"):
                historical_input.load_level_b(self.manifest)

    def test_reader_rejects_outside_rows_missing_warmup_and_path_traversal(self):
        self.rows.append(row(midnight(2023)))
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed"):
                historical_input.load_level_b(self.manifest)
        self.rows = self.rows[1:-1]
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "warmup coverage"):
                historical_input.load_level_b(self.manifest)
        with self.bundle(price_file="../other.json"):
            with self.assertRaisesRegex(ValueError, "relative reviewed filename"):
                historical_input.load_level_b(self.manifest)

    def test_calendar_hash_and_segment_gap_reject_before_price_read(self):
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            self.calendar_path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "calendar file differs"):
                historical_input.load_level_b(self.manifest)
        self.calendar["segments"][0]["end"] -= HOUR
        with self.bundle(), patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.assertRaisesRegex(ValueError, "without gaps or overlaps"):
                historical_input.load_level_b(self.manifest)

    def test_parent_edges_and_seam_are_enforced_before_price_read(self):
        short = self.calendar["segments"][-2]
        with patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            short["h4"][1] += HOUR // 2
            with self.bundle():
                with self.assertRaisesRegex(ValueError, "only terminal intraday bar may be shortened"):
                    historical_input.load_level_b(self.manifest)
            short["h4"][1] -= HOUR // 2
            self.calendar["segments"][-3]["end"] += HOUR
            with self.bundle():
                with self.assertRaisesRegex(ValueError, "session crosses"):
                    historical_input.load_level_b(self.manifest)

    def test_missing_child_marks_development_parents_incomplete(self):
        gap = self.rows.pop(-1)["start"]
        with self.bundle():
            receipt = historical_input.load_level_b(self.manifest).receipt
        coverage = receipt["development_at_scope_end"]
        self.assertEqual([gap], coverage["H1"]["missing_due_starts"])
        self.assertEqual([self.seam + 4 * HOUR], coverage["H4"]["missing_due_starts"])
        self.assertEqual([self.seam], coverage["D1"]["missing_due_starts"])

    def test_h1_observation_must_match_a_scheduled_window_exactly(self):
        final = self.rows[-1]
        final["end"] = final["available_at"] = final["start"] + HOUR
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed calendar window"):
                historical_input.load_level_b(self.manifest)
        self.rows[-1] = row(self.seam + 6 * HOUR)
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "outside reviewed calendar window"):
                historical_input.load_level_b(self.manifest)

    def test_warmup_checks_h4_and_calendar_finalization(self):
        counts = self.plan["partitions"]["development"]["warmup"]["declared_complete_bars"]
        counts["H4"] += 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "H4 warmup coverage"):
                historical_input.load_level_b(self.manifest)
        counts["H4"] -= 1
        self.plan["latency"]["finalization_delay_ms"] = 1
        with self.bundle():
            with self.assertRaisesRegex(ValueError, "D1 warmup coverage"):
                historical_input.load_level_b(self.manifest)

    def test_three_year_fabricated_weekday_calendar_fits_input_limits(self):
        start, end = midnight(2020), midnight(2023)
        day = 24 * HOUR
        self.rows = []
        segments = []
        for left in range(start, end, day):
            if datetime.fromtimestamp(left // 1000, timezone.utc).weekday() < 5:
                segments.append(session(left, left + day))
                self.rows.extend(row(hour) for hour in range(left, left + day, HOUR))
            elif segments[-1]["kind"] == "closure":
                segments[-1]["end"] += day
            else:
                segments.append({"kind": "closure", "start": left, "end": left + day, "reason": "weekend"})
        self.calendar["segments"] = segments
        with self.bundle():
            result = historical_input.load_level_b(self.manifest)
        self.assertEqual(18792, len(result.calendar.frame("H1")))
        self.assertEqual(262, result.receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertEqual(521, result.receipt["development_at_scope_end"]["D1"]["complete_by_cutoff"])

    def test_cli_current_repository_cannot_read_historical_data_through_self_approval(self):
        self.bundle()
        report = self.root / "receipt.json"
        entry = data.ROOT / "tools/signal_count.py"
        run = subprocess.run([sys.executable, str(entry), "historical-input", str(self.manifest), str(report)],
                             capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertIn("no recorded qualification before price read", run.stderr)
        self.assertFalse(report.exists())

    def test_cli_writes_coverage_receipt_for_a_test_reviewed_bundle(self):
        report = self.root / "receipt.json"
        entry = data.ROOT / "tools/signal_count.py"
        args = [str(entry), "historical-input", str(self.manifest), str(report)]
        with self.bundle(), patch.object(sys, "argv", args):
            runpy.run_path(str(entry), run_name="__main__")
        receipt, _ = data.read_json(report)
        self.assertEqual(253, receipt["warmup_at_development_start"]["D1"]["complete_by_cutoff"])
        self.assertIsNone(receipt["actual_counts"])

    def test_reviewed_count_carries_warmup_lines_into_development(self):
        value, pattern, opening = bar_fixture()
        day = 24 * HOUR
        pattern_start = self.seam - 8 * day
        delta = pattern_start - value["calendar"]["scope"]["start"]
        # 245 flat daily sessions followed by the first eight patterned days
        # give 253 daily and 390 H4 warmup windows.
        start = pattern_start - (97 * 5 + 148) * HOUR
        segments = [closure(midnight(2020), start)]
        self.rows = []
        for length in [5] * 97 + [1] * 148:
            end = start + length * HOUR
            segments.append(session(start, end))
            self.rows.extend(row(hour) for hour in range(start, end, HOUR))
            start = end
        end = pattern_start + 9 * day
        segments.extend(session(start, start + day) for start in range(pattern_start, end, day))
        segments.append(closure(end, midnight(2023)))
        self.calendar["segments"] = segments
        for item in pattern:
            self.rows.append(item | {field: item[field] + delta for field in ("start", "end", "available_at")})
        self.plan["partitions"]["development"]["warmup"]["declared_complete_bars"] = {"H1": 825, "H4": 390, "D1": 253}

        reports = {}
        original_setups = signal_count._setups

        def capture(source, bars, tick, profile):
            result = original_setups(source, bars, tick, profile)
            reports[profile] = result
            return result

        output = self.root / "count.json"
        runner = data.ROOT / "tools/signal_count.py"
        args = [str(runner), "historical-count", str(self.manifest), str(output)]
        with self.bundle(), patch.object(sys, "argv", args), patch.object(signal_count, "_setups", side_effect=capture):
            for module, function in ((exits, "_evaluate"), (ledger, "_evaluate"), (risk, "_timeline"),
                                     (fills.PriceModel, "exit_open")):
                blocked = patch.object(module, function, side_effect=AssertionError("account or outcome path called"))
                blocked.start()
                self.addCleanup(blocked.stop)
            runpy.run_path(str(runner), run_name="__main__")
            dataset = historical_input.load_level_b(self.manifest)

        report, _ = data.read_json(output)
        self.assertEqual("historical_development_opportunity_counts", report["kind"])
        self.assertEqual((self.seam, midnight(2023)), (report["scope_start"], report["scope_end"]))
        self.assertFalse(report["outcomes_computed"])
        self.assertFalse(report["orders_available"])
        self.assertEqual(len(signal_count.PROFILES) * len(signal_count.COSTS), len(report["cells"]))
        brk3 = [cell for cell in report["cells"] if cell["profile"] == PROFILE]
        for cell in brk3:
            self.assertEqual({"2021-01"}, set(cell["months"]))
            counts = cell["total"]["counts"]
            self.assertEqual((6, 2, 0, 1, 1), tuple(counts[name] for name in (
                "scheduled_h4_due", "observed_h4", "valid_action_lines_found", "break_setups",
                "entry_eligible_opportunities",
            )))
        self.assertTrue(all(cell["status"] == "INSUFFICIENT" for cell in report["feasibility"]["actual_counts"]))

        # Reuse the observed lifecycle to test a later seam and an unresolved
        # same-time open without replaying several hundred warmup H4 bars.
        source = dataset.source
        cutoff = source.calendar.end
        openings = {item.price.start: item for item in dataset.openings}
        model = fills.PriceModel(source, "base")
        setup_report = reports[PROFILE]
        unresolved = list(signal_count._bar_attempts(
            source, openings, setup_report, model, cutoff, dataset.liquidation_at, self.seam, False,
        ))
        self.assertEqual([("SKIPPED", "UNRESOLVED_OPEN_ORDER")], [attempt[1:3] for attempt in unresolved])
        later_seam = opening["start"] + delta
        self.assertEqual([], list(signal_count._bar_attempts(
            source, openings, setup_report, model, cutoff, dataset.liquidation_at, later_seam, True,
        )))
        months = signal_count._setup_months(setup_report, source.calendar, cutoff, PROFILE, later_seam)
        self.assertEqual(0, months["2021-01"]["counts"]["break_setups"])

        # The next hour remains supported. It must not replace the first.
        with self.bundle(opening_rows=[assumed_opening(item) for item in self.rows if item["start"] != later_seam]):
            without_opening = historical_input.load_level_b(self.manifest)
            self.assertEqual(dataset.development, without_opening.development)
            self.assertEqual(source.calendar.publications(dataset.development, cutoff),
                             source.calendar.publications(without_opening.development, cutoff))
            recounted = historical_count.count(self.manifest)
        suppressed = [cell for cell in recounted["cells"] if cell["profile"] == PROFILE]
        for original, cell in zip(brk3, suppressed, strict=True):
            counts = cell["total"]["counts"]
            self.assertEqual((2, 1, 1, 0), tuple(counts[name] for name in (
                "observed_h4", "break_setups", "entry_attempts", "entry_eligible_opportunities",
            )))
            self.assertEqual({"MISSING_OPENING_EVIDENCE": 1}, cell["total"]["entry_skip_reasons"])
            self.assertEqual(original["months"].keys(), cell["months"].keys())
            self.assertEqual({"evaluated": 0, "passed": 0}, cell["total"]["entry_price_filters"]["spread_to_stop_cap"])

    def test_historical_count_rejects_unreviewed_manifest_without_a_report(self):
        self.bundle()
        output = self.root / "count.json"
        runner = data.ROOT / "tools/signal_count.py"
        run = subprocess.run([sys.executable, str(runner), "historical-count", str(self.manifest), str(output)],
                             capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertIn("no recorded qualification before price read", run.stderr)
        self.assertFalse(output.exists())

    def test_parent_publication_waits_for_late_child_and_orders_daily_first(self):
        late = self.rows[-1]["end"] + 2
        self.rows[-1].update(available_at=late, high="1.1009", close="1.1006")
        with self.bundle():
            dataset = historical_input.load_level_b(self.manifest)
        calendar = dataset.calendar
        before = calendar.publications(dataset.development, late - 1)
        self.assertEqual(("H4",), tuple(bar.timeframe for bar in before))
        after = calendar.publications(dataset.development, late)
        self.assertEqual(before, after[:1])
        self.assertEqual(("D1", "H4"), tuple(bar.timeframe for bar in after[1:]))
        for bar in after[1:]:
            self.assertEqual(late, bar.available)
            self.assertEqual(("1.1009", "1.1006"), (str(bar.high), str(bar.close)))

    def test_reviewed_tick_order_and_liquidation_are_checked_before_prices(self):
        with patch.object(historical_input, "_read_hours", side_effect=AssertionError("no prices expected")):
            with self.bundle(tick_size="0"), self.assertRaisesRegex(ValueError, "positive reviewed price tick"):
                historical_input.load_level_b(self.manifest)
            with self.bundle(same_time_open_order="unknown"), self.assertRaisesRegex(ValueError, "opening order policy"):
                historical_input.load_level_b(self.manifest)
            self.plan["endpoints"]["development"]["liquidation_at"] = "2021-01-01T00:30:00Z"
            with self.bundle(), self.assertRaisesRegex(ValueError, "scheduled H1 opening"):
                historical_input.load_level_b(self.manifest)

    def test_completed_h1_receipt_applies_delay_and_scope_end(self):
        with self.bundle():
            dataset = historical_input.load_level_b(self.manifest)
        last = dataset.development[-1]
        calendar = replace(dataset.calendar, delay=2, end=last.end)
        dataset = replace(dataset, source=replace(dataset.source, calendar=calendar))
        completed = tuple(historical_count._completed_hours(dataset))
        self.assertEqual(len(dataset.warmup) + len(dataset.development) - 1, len(completed))
        self.assertEqual(dataset.development[-2].end + 2, completed[-1].available_at)
        self.assertNotEqual(last.start, completed[-1].start)

    def test_opening_coverage_reconciles_independently_of_completed_bars(self):
        hours = self.rows[-6:]
        openings = [
            paired_opening(hours[0]),
            paired_opening(hours[1], source_delay=1),
            paired_opening(hours[2], receipt_delay=1),
            assumed_opening(hours[3]) | {"available_at": midnight(2023) + 1},
            paired_opening(hours[5]),
        ]
        self.rows.pop()
        with self.bundle(opening_rows=openings):
            dataset = historical_input.load_level_b(self.manifest)
        self.assertEqual(5, dataset.receipt["development_at_scope_end"]["H1"]["complete_by_cutoff"])
        self.assertEqual({
            "scheduled": 6,
            "status_counts": {"PAIRED_AT_BOUNDARY": 2, "OPENING_SOURCE_AFTER_START": 1,
                              "OPENING_RECEIVED_AFTER_START": 1, "PENDING_OPENING_EVIDENCE": 1,
                              "MISSING_OPENING_EVIDENCE": 1},
        }, dataset.receipt["development_openings_at_scope_end"])
        self.assertEqual(2, dataset.openings[-1].price.spread_pips)
        self.assertNotIn(dataset.openings[-1].price.start, {hour.start for hour in dataset.development})

    def test_opening_evidence_rejects_invalid_price_pairs_or_schedule(self):
        hour = self.rows[-1]
        opening = paired_opening(hour)
        checks = (
            ([opening, opening], "unique opening evidence"),
            ([opening | {"end": opening["end"] + 1}], "outside reviewed H1"),
            ([opening | {"ask": "1.0999"}], "ask must be at or above bid"),
            ([opening | {"available_at": opening["start"] - 1}], "source and receipt"),
            ([assumed_opening(hour) | {"source_at": hour["start"] + 1}], "null source time"),
        )
        for rows, reason in checks:
            with self.subTest(reason=reason), self.bundle(opening_rows=rows), self.assertRaisesRegex(ValueError, reason):
                historical_input.load_level_b(self.manifest)

    def test_entry_evidence_is_only_considered_through_cutoff_and_expiry(self):
        hour = self.rows[-6]
        window = SimpleNamespace(start=hour["start"], end=hour["end"])
        expiry = window.end
        request = {"decision_at": {"time": window.start - 1}}
        model = Mock()
        model.entry.return_value = {"status": "FILLED", "reason": None}

        def resolve(record, as_of, *, delay=0):
            evidence = entries.HistoricalOpening.from_record(record, delay=delay)
            observations = {window.start: evidence}
            return entries._resolve(model, request, window, expiry, observations, as_of, True, None,
                                    historical=True)[:2]

        self.assertEqual(("PENDING", "AWAITING_OPENING_EVIDENCE"),
                         resolve(paired_opening(hour, receipt_delay=1), window.start))
        self.assertEqual(("UNAVAILABLE", "OPENING_RECEIVED_AFTER_START"),
                         resolve(paired_opening(hour, receipt_delay=1), window.start + 1))
        self.assertEqual(("UNAVAILABLE", "OPENING_SOURCE_AFTER_START"),
                         resolve(paired_opening(hour, source_delay=1), window.start + 1))
        modeled = assumed_opening(hour)
        self.assertEqual(("EXPIRED", "MISSING_OPENING_EVIDENCE"),
                         resolve(modeled, expiry, delay=1))
        self.assertEqual(("EXPIRED", "OPENING_EVIDENCE_AFTER_EXPIRY"),
                         resolve(modeled, expiry + 1, delay=1))
        model.entry.assert_not_called()
        self.assertEqual(("FILLED", None), resolve(paired_opening(hour), window.start))
        self.assertEqual(2, model.entry.call_args.args[1].spread_pips)
