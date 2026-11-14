import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from forex_demo_lab.histdata import archive_ticks, hourly
from forex_demo_lab.tick_dataset import normalize, read_ticks


class HistDataTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def archive(self, content, month="202407", name=None):
        with zipfile.ZipFile(self.root/"original.zip", "w") as z:
            z.writestr(name or f"DAT_ASCII_EURUSD_T_{month}.csv", content)
        digest = hashlib.sha256((self.root/"original.zip").read_bytes()).hexdigest()
        (self.root/"download.json").write_text(json.dumps({"source":"HistData", "sha256":digest}))

    def test_fixed_est_summer_and_winter_milliseconds(self):
        for month in ("202401", "202407"):
            self.archive(f"{month}02 120000123,1.1,1.1002,0\n", month)
            values = list(archive_ticks(self.root))
            from datetime import datetime, timezone
            actual = datetime.fromtimestamp(values[0]["time_msc"]/1000,timezone.utc)
            self.assertEqual(actual.hour,17)
            self.assertEqual(actual.microsecond,123000)

    def test_same_millisecond_events_preserve_order_and_no_missing_bar_fill(self):
        self.archive("20240702 120000000,1.1,1.1002,0\n20240702 120000000,1.099,1.1,0\n20240702 140000000,1.101,1.102,0\n")
        ticks = list(archive_ticks(self.root))
        bars = list(hourly(ticks))
        self.assertEqual(len(bars),2)
        self.assertEqual(bars[0]["bid_open"],1.1)
        self.assertEqual(bars[0]["bid_close"],1.099)
        self.assertEqual(bars[1]["hour"]-bars[0]["hour"],2)
        self.assertAlmostEqual(bars[0]["spread_pips"],2)

    def test_invalid_quotes_rows_months_and_order_rejected(self):
        for content in (
            "20240702 120000000,1.2,1.1,0\n", "20240702 120000000,nan,1.1,0\n",
            "20240702 120000000,1.1,1.2,-1\n", "20240802 120000000,1.1,1.2,0\n",
            "20240702 120000000,1.1,1.2\n", "20240702 126000000,1.1,1.2,0\n",
            "20240702 120001000,1.1,1.2,0\n20240702 120000000,1.1,1.2,0\n"):
            with self.subTest(content=content):
                self.archive(content)
                with self.assertRaises(ValueError):
                    list(archive_ticks(self.root))

    def test_hash_change_and_wrong_instrument_rejected(self):
        self.archive("20240702 120000000,1.1,1.2,0\n")
        with (self.root/"original.zip").open("ab") as stream:
            stream.write(b"tamper")
        with self.assertRaisesRegex(ValueError,"hash/source"):
            list(archive_ticks(self.root))
        self.archive("20240702 120000000,1.1,1.2,0\n",name="DAT_ASCII_GBPUSD_T_202407.csv")
        with self.assertRaises(ValueError):
            list(archive_ticks(self.root))

    def test_filtered_hourly_still_validates_later_bad_rows(self):
        self.archive("20240702 120000000,1.1,1.2,0\n20240703 120000000,1.2,1.1,0\n")
        with self.assertRaises(ValueError):
            list(hourly(archive_ticks(self.root), upper=0))

    def test_normalization_requires_source_bound_stage_and_preserves_gaps(self):
        self.archive("20240702 120000000,1.1,1.2,0\n20240702 140000000,1.11,1.21,0\n")
        gate=self.root/"gate.json";output=self.root/"normalized"
        gate.write_text(json.dumps({"dataset_construction_ready":False,"checks":[]}))
        with self.assertRaises(ValueError):normalize(self.root,output,gate)
        self.assertFalse(output.exists())
        digest=hashlib.sha256((self.root/"original.zip").read_bytes()).hexdigest()
        gate.write_text(json.dumps({"dataset_construction_ready":True,"checks":[{"histdata_archive_sha256":digest}]}))
        result=normalize(self.root,output,gate)
        self.assertEqual(result["observed_hours"],2)
        self.assertEqual(result["gaps_over_one_hour"][0]["seconds"],7200)
        self.assertEqual(len(list(read_ticks(output))),2)
        with self.assertRaises(FileExistsError):normalize(self.root,output,gate)
        with (output/"ticks.csv.gz").open("ab") as stream:stream.write(b"modified")
        with self.assertRaisesRegex(ValueError,"integrity"):list(read_ticks(output))

    def test_bad_source_never_publishes_normalized_provenance(self):
        self.archive("20240702 120000000,1.1,1.2,0\n20240702 140000000,1.3,1.2,0\n")
        digest=hashlib.sha256((self.root/"original.zip").read_bytes()).hexdigest()
        gate=self.root/"gate.json";output=self.root/"normalized"
        gate.write_text(json.dumps({"dataset_construction_ready":True,"checks":[{"histdata_archive_sha256":digest}]}))
        with self.assertRaises(ValueError):normalize(self.root,output,gate)
        self.assertFalse((output/"provenance.json").exists())
