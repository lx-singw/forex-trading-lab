from dataclasses import asdict
import csv
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.model import Config
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.tick_workflow import freeze,evaluate


class TickWorkflowTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.data=self.root/"data";self.data.mkdir()
        with gzip.open(self.data/"ticks.csv.gz","wt",newline="") as stream:
            writer=csv.writer(stream);writer.writerow(["sequence","time_msc","bid","ask"])
            writer.writerow([0,1704067200000,1.1,1.1001]);writer.writerow([1,1704070800000,1.1,1.1001])
        p={"kind":"normalized_histdata_ticks","symbol":"EURUSD","role":"development",
           "data_sha256":sha256(self.data/"ticks.csv.gz"),"ticks":2,"first_ms":1704067200000,"last_ms":1704070800000}
        (self.data/"provenance.json").write_text(json.dumps(p))
        self.quality=self.root/"quality.json";self.config=self.root/"config.json";self.manifest=self.root/"manifest.json"
        self.config.write_text(json.dumps(asdict(Config(leverage=10))))
        self.review={"performance_evaluation_ready":True,"datasets":[{"provenance_sha256":sha256(self.data/"provenance.json"),"status":"ready_for_development_research"}]}
        self.quality.write_text(json.dumps(self.review))

    def test_blocked_review_or_different_dataset_cannot_freeze(self):
        self.review["performance_evaluation_ready"]=False
        self.quality.write_text(json.dumps(self.review))
        with self.assertRaisesRegex(ValueError,"blocks performance"):freeze(self.data,self.config,self.quality,self.manifest)
        self.assertFalse(self.manifest.exists())
        self.review["performance_evaluation_ready"]=True
        self.review["datasets"][0]["provenance_sha256"]="wrong"
        self.quality.write_text(json.dumps(self.review))
        with self.assertRaises(ValueError):freeze(self.data,self.config,self.quality,self.manifest)

    def test_freeze_and_run_fixture_reconciles_and_never_overwrites(self):
        freeze(self.data,self.config,self.quality,self.manifest)
        output=self.root/"result.json"
        r=evaluate(self.data,self.manifest,self.quality,output)
        self.assertEqual(r["metrics"]["ticks_processed"],2)
        self.assertEqual(r["metrics"]["net_pnl"],0)
        with self.assertRaises(FileExistsError):evaluate(self.data,self.manifest,self.quality,output)

    def test_changed_review_or_source_invalidates_frozen_experiment(self):
        freeze(self.data,self.config,self.quality,self.manifest)
        original=self.quality.read_text();self.quality.write_text(original+" ")
        with self.assertRaisesRegex(ValueError,"changed"):evaluate(self.data,self.manifest,self.quality,self.root/"out")
        self.quality.write_text(original)
        with (self.data/"ticks.csv.gz").open("ab") as stream:stream.write(b"changed")
        with self.assertRaisesRegex(ValueError,"changed"):evaluate(self.data,self.manifest,self.quality,self.root/"out")
