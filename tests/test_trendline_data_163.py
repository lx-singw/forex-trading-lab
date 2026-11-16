"""Invented Phase 2 observations; no market files, API keys or native accounts."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_sessions_146 as reference
from forex_demo_lab.elliott_full.contracts import Bar
from forex_demo_lab.trendline import data as d


def calendar(lengths=(24,), closures=(), partial=False):
    cursor = reference.START + 22 * reference.HOUR
    start = cursor
    segments = []
    for index, hours in enumerate(lengths):
        end = cursor + int(hours * reference.HOUR)
        def grid(period):
            return list(range(cursor, end, period)) + [end]
        segments.append({"kind":"session", "label":f"session_{index}",
                         "start":cursor, "end":end, "h1":grid(reference.HOUR),
                         "h4":grid(4*reference.HOUR), "partial":partial})
        cursor = end
        if index < len(closures) and closures[index]:
            end = cursor + closures[index]*reference.HOUR
            segments.append({"kind":"closure", "start":cursor, "end":end, "reason":"weekend"})
            cursor = end
    return {"kind":"invented_session_calendar_146", "scope":{"start":start,"end":cursor},
            "finalization_delay_ms":2000, "segments":segments}


def descriptor(cal=None, basis="bid_only", partition="development"):
    return {"schema":d.VERSION, "kind":"invented_trendline_source", "symbol":"EURUSD",
            "data_level":"B", "geometry_basis":basis,
            "spread_semantics":"constant_per_h1_assumption" if basis == "bid_only" else "not_available",
            "partition":partition, "input_sha256":"0"*64, "calendar":cal or calendar()}


def rows_for(value):
    rows = []
    cal = d.Declaration.from_record(value).calendar
    for i, window in enumerate(cal.frame("H1")):
        price = Decimal("1.1000") + Decimal(i)/10000
        rows.append({"start":window.start, "end":window.end, "available_at":window.end+2000,
                     "open":str(price), "high":str(price+Decimal("0.0003")),
                     "low":str(price-Decimal("0.0002")), "close":str(price+Decimal("0.0001")),
                     "spread_pips":"1.2" if value["geometry_basis"] == "bid_only" else None})
    return rows


def stream_for(value, rows=None):
    stream = d.BarStream(d.Declaration.from_record(value))
    for row in rows if rows is not None else rows_for(value):
        stream.observe(d.Hour.from_record(row, value["geometry_basis"]))
    return stream


def files(directory, value=None, rows=None):
    value = deepcopy(value or descriptor())
    rows = deepcopy(rows if rows is not None else rows_for(value))
    row_path = Path(directory)/"hours.json"
    row_path.write_text(json.dumps(rows))
    value["input_sha256"] = hashlib.sha256(row_path.read_bytes()).hexdigest()
    meta_path = Path(directory)/"source.json"
    meta_path.write_text(json.dumps(value))
    return meta_path, row_path, value


class TrendlineData163Tests(unittest.TestCase):
    def test_full_day_matches_existing_aggregation_exactly(self):
        value = descriptor()
        stream = stream_for(value)
        observer = reference.Observations(stream.source.calendar)
        for row in rows_for(value):
            observer.observe(Bar("H1", row["start"],row["end"],row["available_at"],
                                 row["open"],row["high"],row["low"],row["close"],"1"*64))
        actual = [(b.timeframe,b.start,b.end,b.available,b.open,b.high,b.low,b.close) for b in stream.bars()]
        expected = [(b.timeframe,b.start,b.end,b.available,b.open,b.high,b.low,b.close) for b in observer.bars()]
        self.assertEqual(expected, actual)
        self.assertEqual([1,6,24], [sum(b.timeframe == f for b in stream.bars()) for f in reference.FRAMES])

    def test_first_h4_ohlc_is_hand_reconciled(self):
        stream = stream_for(descriptor())
        bar = next(b for b in stream.bars() if b.timeframe == "H4")
        self.assertEqual((Decimal("1.1000"),Decimal("1.1006"),Decimal("1.0998"),Decimal("1.1004")),
                         (bar.open,bar.high,bar.low,bar.close))

    def test_declared_23_25_hour_days_and_closures_have_parity(self):
        value = descriptor(calendar((23,25),(48,)))
        stream = stream_for(value)
        days = [b for b in stream.bars() if b.timeframe == "D1"]
        self.assertEqual([23,25],[(b.end-b.start)//reference.HOUR for b in days])
        self.assertEqual(48, stream.report()["coverage"]["H1"]["complete_count"])
        self.assertEqual([], stream.report()["coverage"]["H1"]["missing_starts"])

    def test_short_session_requires_explicit_partial_policy(self):
        with self.assertRaises(ValueError):
            d.Declaration.from_record(descriptor(calendar((3.5,))))
        stream = stream_for(descriptor(calendar((3.5,),partial=True)))
        self.assertEqual(4, stream.report()["observed_hours"])

    def test_missing_child_blocks_only_its_parents(self):
        value = descriptor()
        rows = rows_for(value)
        missing = rows.pop(1)
        stream = stream_for(value,rows)
        report = stream.report()
        self.assertEqual([missing["start"]], report["coverage"]["H1"]["missing_starts"])
        self.assertEqual(5, report["coverage"]["H4"]["complete_count"])
        self.assertEqual(0, report["coverage"]["D1"]["complete_count"])

    def test_finalization_delay_blocks_unfinished_parent(self):
        value = descriptor()
        rows = rows_for(value)[:4]
        for row in rows:
            row["available_at"] = row["end"]
        stream = stream_for(value,rows)
        self.assertFalse(any(b.timeframe == "H4" for b in stream.bars()))
        stream.advance(rows[-1]["end"]+1999)
        self.assertFalse(any(b.timeframe == "H4" for b in stream.bars()))
        stream.advance(rows[-1]["end"]+2000)
        self.assertEqual(1,sum(b.timeframe == "H4" for b in stream.bars()))

    def test_late_child_publishes_at_receipt_never_backdates(self):
        value = descriptor()
        rows = rows_for(value)
        late = rows.pop(1)
        late["available_at"] = rows[-1]["available_at"]+1000
        stream = stream_for(value,rows)
        self.assertFalse(any(b.timeframe == "D1" for b in stream.bars()))
        stream.observe(d.Hour.from_record(late,"bid_only"))
        day = next(b for b in stream.bars() if b.timeframe == "D1")
        self.assertEqual(late["available_at"],day.available)

    def test_future_suffix_changes_leave_earlier_published_bars_identical(self):
        value = descriptor()
        rows = rows_for(value)
        prefix = stream_for(value, rows[:4]).bars()
        changed = deepcopy(rows)
        for row in changed[4:]:
            row.update(open="2", high="3", low="1", close="2")
        other = deepcopy(value)
        other["input_sha256"] = "f"*64
        full = stream_for(other, changed)
        earlier = tuple(b for b in full.bars() if b.available <= rows[3]["available_at"])
        self.assertEqual(prefix, earlier)

    def test_duplicate_and_out_of_order_receipt_reject_without_mutation(self):
        value = descriptor()
        rows = rows_for(value)
        stream = stream_for(value,rows[:2])
        before = stream.report()
        for row in (rows[1],rows[0]):
            with self.assertRaises(ValueError):
                stream.observe(d.Hour.from_record(row,"bid_only"))
            self.assertEqual(before,stream.report())

    def test_unscheduled_hour_and_backward_advance_reject(self):
        value = descriptor()
        row = rows_for(value)[0]
        stream = stream_for(value,[row])
        with self.assertRaises(ValueError):
            stream.advance(row["start"])
        row["start"] += 1
        with self.assertRaises(ValueError):
            stream.observe(d.Hour.from_record(row,"bid_only"))

    def test_nonfinite_float_boolean_and_unknown_price_fields_reject(self):
        original = rows_for(descriptor())[0]
        for bad in ("NaN","Infinity","-1","1e999",True,1.1,None):
            row = deepcopy(original);row["close"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                d.Hour.from_record(row,"bid_only")
        row = deepcopy(original);row["unknown"] = "not allowed"
        with self.assertRaises(ValueError):d.Hour.from_record(row,"bid_only")

    def test_invalid_ohlc_unfinished_observation_and_bad_spread_reject(self):
        original = rows_for(descriptor())[0]
        for key,bad in (("low","2"),("high","0"),("available_at",original["end"]-1),
                        ("spread_pips","-0.1"),("spread_pips",None),("start",True)):
            row = deepcopy(original);row[key] = bad
            with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):
                d.Hour.from_record(row,"bid_only")

    def test_midpoint_source_never_fabricates_executable_sides(self):
        value = descriptor(basis="mid_candles_source")
        report = stream_for(value).report()
        self.assertEqual("unavailable_mid_only",report["execution_side_data"])
        self.assertEqual("mid_candles_source",report["geometry_basis"])
        self.assertFalse(report["demo_eligible"])
        row = rows_for(value)[0];row["spread_pips"] = "1"
        with self.assertRaises(ValueError):d.Hour.from_record(row,"mid_candles_source")

    def test_blended_geometry_q_label_or_market_kind_rejected(self):
        for key,bad in (("geometry_basis","average_bid_ask_extremes"),("data_level","Q"),
                        ("kind","qualified_market"),("spread_semantics","end_of_hour_statistic"),
                        ("symbol","GBPUSD"),("partition","live")):
            value = descriptor();value[key] = bad
            with self.subTest(key=key),self.assertRaises(ValueError):d.Declaration.from_record(value)

    def test_calendar_unknown_gaps_and_market_dates_reject(self):
        value = descriptor(calendar((24,24),(48,)))
        value["calendar"]["segments"].pop(1)
        with self.assertRaises(ValueError):d.Declaration.from_record(value)
        value = descriptor();value["calendar"]["scope"]["start"] = 0
        with self.assertRaises(ValueError):d.Declaration.from_record(value)

    def test_declaration_and_report_are_defensive_copies(self):
        value = descriptor()
        declaration = d.Declaration.from_record(value)
        original_hash = declaration.sha256
        value["calendar"]["segments"].clear()
        returned = declaration.record();returned["calendar"]["segments"].clear()
        self.assertEqual(original_hash,declaration.sha256)
        stream = d.BarStream(declaration)
        before = stream.report()
        report = stream.report();report["coverage"]["H1"]["missing_starts"].append("changed")
        self.assertEqual(before,stream.report())

    def test_protocol_or_source_binding_change_blocks_report(self):
        stream = stream_for(descriptor())
        with patch.object(d,"source_bindings",return_value={}):
            with self.assertRaises(ValueError):stream.report()

    def test_file_hash_mismatch_rejects_before_typed_row_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,value = files(tmp)
            price.write_text("[]")
            with self.assertRaisesRegex(ValueError,"SHA256"):d.load_dataset(meta,price)

    def test_validation_rejected_before_hourly_file_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,value = files(tmp,descriptor(partition="validation"))
            reader = d.read_json
            opened = []
            def tracked(path,*args):
                opened.append(Path(path).name)
                return reader(path,*args)
            with patch.object(d,"read_json",side_effect=tracked):
                with self.assertRaisesRegex(ValueError,"unlock"):d.load_dataset(meta,price)
            self.assertEqual(["source.json"],opened)

    def test_explicit_unlock_binds_scope_input_and_partition(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,value = files(tmp,descriptor(partition="validation"))
            receipt = Path(tmp)/"unlock.json"
            d.write_new(receipt,d.unlock_record(d.Declaration.from_record(value)))
            source,hours = d.load_dataset(meta,price,receipt)
            self.assertEqual("validation",source.record()["partition"])
            self.assertEqual(24,len(hours))
            changed = json.loads(receipt.read_text());changed["input_sha256"] = "f"*64
            receipt.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,"unlock"):d.load_dataset(meta,price,receipt)

    def test_unlock_cannot_admit_market_kind_or_development(self):
        for value in (descriptor(),dict(descriptor(partition="validation"),kind="market")):
            with self.assertRaises(ValueError):d.unlock_record(d.Declaration.from_record(value))

    def test_loader_rejects_bad_full_prefix_and_no_partial_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            value = descriptor();rows = rows_for(value);rows[-1] = rows[0]
            meta,price,_ = files(tmp,value,rows)
            with self.assertRaises(ValueError):d.load_dataset(meta,price)

    def test_loader_accepts_explicit_invented_development_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,_ = files(tmp)
            source,hours = d.load_dataset(meta,price)
            self.assertEqual("B",source.record()["data_level"])
            self.assertEqual(24,len(hours))

    def test_duplicate_keys_nonfinite_oversize_and_symlink_files_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}'):
                path.write_text(text)
                with self.assertRaises(ValueError):d.read_json(path)
            with self.assertRaises(ValueError):d.read_json(path,1)
            link = Path(tmp)/"link.json";link.symlink_to(path)
            with self.assertRaises(ValueError):d.read_json(link)

    def test_exclusive_output_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"report.json"
            d.write_new(path,{"kind":"first"})
            with self.assertRaises(FileExistsError):d.write_new(path,{"kind":"second"})
            self.assertEqual({"kind":"first"},json.loads(path.read_text()))

    def test_draft_keeps_all_28_market_cells_unavailable(self):
        report = d.assess_plan(d.draft_plan())
        self.assertEqual(28,len(report["cells"]))
        self.assertTrue(all(c["returns"] is None and c["status"] == "UNAVAILABLE" for c in report["cells"]))
        self.assertFalse(report["demo_eligible"])

    def test_complete_metadata_cannot_self_qualify(self):
        value = d.draft_plan()
        value.update(source_alias="local_export",geometry_basis="bid_only",input_sha256="1"*64,
                     calendar_sha256="2"*64,spread_semantics="constant_per_h1_assumption")
        value["scope"] = {"warmup":{"start":"2017-01-01","end":"2018-01-01"},
                          "development":{"start":"2018-01-01","end":"2020-01-01"},
                          "validation":{"start":"2020-01-01","end":"2022-01-01"}}
        value["evidence_sha256"] = {key:"3"*64 for key in d.EVIDENCE}
        report = d.assess_plan(value)
        self.assertEqual("UNAVAILABLE",report["status"])
        self.assertIn("independent_source_calendar_cost_exposure_review_required",report["reasons"])

    def test_protected_dates_also_block_warmup_and_seen_validation(self):
        for start,end,label in (("2025-01-01","2026-01-01","consumed"),
                                ("2026-10-01","2026-11-01","quarantined"),
                                ("2026-11-01","2027-01-01","reserved")):
            value = d.draft_plan();value["scope"]["warmup"] = {"start":start,"end":end}
            self.assertIn("warmup_overlaps_"+label,d.assess_plan(value)["reasons"])
        value = d.draft_plan();value["scope"]["validation"] = {"start":"2024-01-01","end":"2025-01-01"}
        self.assertIn("validation_overlaps_seen_2024",d.assess_plan(value)["reasons"])

    def test_metadata_schema_rejects_unknown_fields_and_bad_geometry(self):
        for key,bad in (("undeclared_field","blocked"),("data_level","live"),("geometry_basis","average_extremes")):
            value = d.draft_plan();value[key] = bad
            with self.assertRaises(ValueError):d.assess_plan(value)
        value = d.draft_plan();value["geometry_basis"] = "mid_sync"
        with self.assertRaises(ValueError):d.assess_plan(value)

    def test_metadata_cannot_claim_midpoint_has_executable_spread(self):
        value = d.draft_plan()
        value.update(geometry_basis="mid_candles_source", spread_semantics="recorded_bid_ask")
        with self.assertRaisesRegex(ValueError,"spread"):d.assess_plan(value)

    def test_unlock_numeric_false_is_not_a_boolean_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,value = files(tmp,descriptor(partition="validation"))
            record = d.unlock_record(d.Declaration.from_record(value))
            record["market_data_authorized"] = 0
            receipt = Path(tmp)/"unlock.json";receipt.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,"unlock"):d.load_dataset(meta,price,receipt)

    def test_unexpected_development_unlock_and_symlink_output_parent_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,_ = files(tmp)
            with self.assertRaises(ValueError):d.load_dataset(meta,price,Path(tmp)/"unused.json")
            link = Path(tmp)/"linked";link.symlink_to(Path(tmp),target_is_directory=True)
            with self.assertRaises(ValueError):d.write_new(link/"new.json",{})

    def test_cli_inspects_prefix_and_preserves_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,price,value = files(tmp)
            out = Path(tmp)/"output"
            now = rows_for(value)[3]["available_at"]
            command = [sys.executable,"-m","forex_demo_lab.trendline","inspect-invented",
                       str(meta),str(price),str(out),"--as-of",str(now)]
            result = subprocess.run(command,capture_output=True,text=True,check=True)
            self.assertEqual(4,json.loads(result.stdout)["observed_hours"])
            report = json.loads((out/"report.json").read_text())
            self.assertEqual("B",report["data_level"])
            self.assertEqual("bid_only",report["geometry_basis"])
            self.assertFalse(report["orders_available"])
            self.assertNotEqual(0,subprocess.run(command,capture_output=True).returncode)

    def test_cli_draft_and_assessment_do_not_read_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp)/"plan.json"
            subprocess.run([sys.executable,"-m","forex_demo_lab.trendline","draft-plan",str(plan)],check=True,capture_output=True)
            result = subprocess.run([sys.executable,"-m","forex_demo_lab.trendline","assess-plan",str(plan)],check=True,capture_output=True,text=True)
            self.assertEqual(28,len(json.loads(result.stdout)["cells"]))


if __name__ == "__main__":
    unittest.main()
