from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.research_data import build,mt5_month_ticks,shifted_histdata,compare_hourly
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.tick_dataset import read_ticks


class ResearchDataTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.ms=int(datetime(2024,1,1,2,tzinfo=timezone.utc).timestamp()*1000)
        self.ticks=[dict(sequence=0,time_msc=self.ms,bid=1.1,ask=1.1001),
                    dict(sequence=1,time_msc=self.ms+1,bid=1.1002,ask=1.1003)]

    def test_clock_scenario_changes_only_timestamps_and_preserves_source(self):
        original=self.root/"original"
        build(iter(self.ticks),original,{"kind":"normalized_histdata_ticks"})
        digest=sha256(original/"ticks.csv.gz")
        shifted=list(shifted_histdata(original,-3600000))
        self.assertEqual(shifted[0],{**self.ticks[0],"time_msc":self.ms-3600000})
        self.assertEqual(sha256(original/"ticks.csv.gz"),digest)
        with self.assertRaises(ValueError):list(shifted_histdata(original,1))

    def test_mt5_chunks_renumber_without_overlap_or_missing_window(self):
        windows=[];returns=[]
        for i in range(2):
            folder=self.root/f"chunk-{i}";folder.mkdir();(folder/"capture.json").write_text("{}")
            windows.append({"folder":folder.name,"capture_sha256":sha256(folder/"capture.json"),"ticks":1})
            returns.append(({},[{**self.ticks[0],"time_msc":self.ms+i*3600000}],self.ms+i*3600000,self.ms+(i+1)*3600000))
        manifest={"kind":"bounded_mt5_month_capture","month":"202401","source_label_offset_hours":2,"ticks":2,
                  "source_label_start":"2024-01-01T02:00:00+00:00","source_label_end_exclusive":"2024-01-01T04:00:00+00:00","windows":windows}
        (self.root/"month.json").write_text(json.dumps(manifest))
        with patch("forex_demo_lab.research_data.checked_capture",side_effect=returns):
            actual=list(mt5_month_ticks(self.root))
        self.assertEqual([t["sequence"] for t in actual],[0,1])
        self.assertEqual(actual[0]["time_msc"],self.ms-7200000)
        bad=list(returns);bad[1]=(bad[1][0],bad[1][1],bad[1][2]+3600000,bad[1][3]+3600000)
        with patch("forex_demo_lab.research_data.checked_capture",side_effect=bad),self.assertRaises(ValueError):
            list(mt5_month_ticks(self.root))

    def test_mt5_normalization_supported_and_bad_quotes_never_publish(self):
        result=build(iter(self.ticks),self.root/"good",{"kind":"normalized_mt5_ticks"})
        self.assertEqual(list(read_ticks(self.root/"good")),self.ticks)
        self.assertFalse(result["provider_certified_clock"])
        bad=[{**self.ticks[0],"ask":1.0}]
        with self.assertRaises(ValueError):build(iter(bad),self.root/"bad",{"kind":"normalized_mt5_ticks"})
        self.assertFalse((self.root/"bad/provenance.json").exists())

    def test_hourly_comparison_reports_missing_and_large_discrepancies(self):
        a=self.root/"a.csv";b=self.root/"b.csv"
        a.write_text("hour,bid_close\n1,1.1000\n2,1.1010\n")
        b.write_text("hour,bid_close\n1,1.1000\n2,1.1020\n3,1.1000\n")
        result=compare_hourly(a,b)
        self.assertEqual(result["missing_reference_hours"],[3])
        self.assertAlmostEqual(result["maximum_close_difference_pips"],10)
        self.assertEqual(result["within_one_pip_fraction"],.5)
        bounded=compare_hourly(a,b,1,3)
        self.assertEqual(bounded["missing_reference_hours"],[])
        self.assertEqual(bounded["reference_hours_outside_requested_scope"],[3])
