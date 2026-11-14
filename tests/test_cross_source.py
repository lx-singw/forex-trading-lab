import importlib.util
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("cross_source", Path(__file__).resolve().parents[1]/"scripts/compare-histdata.py")
cross_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross_source)


class CrossSourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        (self.folder/"capture.json").write_text("{}")
        (self.folder/"original.zip").write_bytes(b"fixture")
        # Distinct price path separates offset candidates by ten pips/hour.
        self.other = [dict(sequence=h, time_msc=h*3600000, bid=1+h*.001, ask=1.0001+h*.001)
                      for h in range(6,14)]
        self.mt5 = [dict(sequence=h-10, time_msc=h*3600000, bid=1+(h-2)*.001, ask=1.0001+(h-2)*.001)
                    for h in range(10,14)]

    def compare(self, expected):
        with patch.object(cross_source,"checked_capture",return_value=({},self.mt5,10*3600000,14*3600000)), \
                patch.object(cross_source,"archive_ticks",return_value=iter(self.other)):
            return cross_source.compare(self.folder,self.folder,expected)

    def test_expected_offset_pass_preserves_all_alternatives(self):
        result = self.compare(2)
        self.assertEqual(result["status"],"sample_corroborated")
        self.assertEqual(len(result["candidates"]),5)
        self.assertGreater(result["alternative_mean_error_margin_pips"],9)
        self.assertFalse(result["full_year_timezone_verified"])

    def test_best_alternative_does_not_silently_replace_failed_hypothesis(self):
        result = self.compare(3)
        self.assertEqual(result["status"],"sample_not_corroborated")
        self.assertEqual(result["expected_offset"],3)
        self.assertAlmostEqual(result["candidates"][2]["mean_absolute_close_pips"],0)

    def test_missing_mt5_or_comparison_hour_cannot_pass(self):
        self.other = [t for t in self.other if t["time_msc"] != 8*3600000]
        self.assertEqual(self.compare(2)["status"],"sample_not_corroborated")
        self.mt5.pop(0)
        self.assertEqual(self.compare(2)["status"],"sample_not_corroborated")

    def test_preserved_bar_comparison_checks_order_and_explicit_clock(self):
        raw = self.folder/"raw.csv"
        def write(reverse=False):
            with raw.open("w",newline="") as stream:
                writer=csv.writer(stream)
                writer.writerow(["time","open","high","low","close"])
                for t in (list(reversed(self.mt5)) if reverse else self.mt5):
                    writer.writerow([datetime.fromtimestamp(t["time_msc"]/1000,timezone.utc).isoformat(),*[t["bid"]]*4])
        write()
        with patch.object(cross_source,"archive_ticks",return_value=iter(self.other)):
            result=cross_source.compare_bars(raw,self.folder,2,datetime.fromtimestamp(36000,timezone.utc),datetime.fromtimestamp(50400,timezone.utc))
        self.assertEqual(result["status"],"sample_corroborated")
        self.assertEqual(result["comparison_kind"],"preserved_h1_bid_candles_not_fresh_ticks")
        write(reverse=True)
        with self.assertRaisesRegex(ValueError,"unordered"):
            cross_source.compare_bars(raw,self.folder,2,datetime.fromtimestamp(36000,timezone.utc),datetime.fromtimestamp(50400,timezone.utc))

    def test_stage_requires_failed_original_before_fixed_offset_amendment(self):
        spec=importlib.util.spec_from_file_location("stage",Path(__file__).resolve().parents[1]/"scripts/check-data-stage.py")
        stage=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        w=self.folder/"winter.json";s=self.folder/"summer.json";o=self.folder/"original.json"
        for p in (w,s):p.write_text(json.dumps({"status":"sample_corroborated","expected_offset":2}))
        self.assertFalse(stage.evaluate(w,s)["dataset_construction_ready"])
        o.write_text(json.dumps({"status":"blocked_clock_discrepancy"}))
        amended=stage.evaluate(w,s,o)
        self.assertTrue(amended["dataset_construction_ready"])
        self.assertFalse(amended["demo_execution_ready"])
        s.write_text(json.dumps({"status":"sample_not_corroborated","expected_offset":2}))
        self.assertFalse(stage.evaluate(w,s,o)["dataset_construction_ready"])
