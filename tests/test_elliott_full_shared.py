"""Common H1 lineage, causal aggregation, unchanged controls and default-off study."""
from copy import deepcopy
from dataclasses import replace
from decimal import localcontext
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.elliott_full import shared as s
from forex_demo_lab.elliott_full.contracts import Bar,D,digest
from test_daily_fills_120 import audit_ledger
from test_elliott_execution_125 import audit_account

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("shared_hourly_fixture",ROOT/"scripts/elliott-full-shared.py")
examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(examples)


class SharedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=tempfile.TemporaryDirectory();cls.root=Path(cls.home.name);cls.cache={}

    @classmethod
    def tearDownClass(cls):
        cls.home.cleanup()

    def frozen(self,value=None):
        root=Path(tempfile.mkdtemp(dir=self.root));p=root/"input.json";m=root/"freeze.json"
        s.c.daily.write_new(p,examples.fixture() if value is None else value)
        s.freeze(p,m)
        return root,p,m

    def prepared(self,side=1,outcome="gap",partition="development"):
        key=side,outcome,partition
        if key not in self.cache:
            root,p,m=self.frozen(examples.fixture(side,outcome))
            s.prepare(p,m,partition,root/"prepared");self.cache[key]=root/"prepared"
        return self.cache[key]

    def test_parent_ohlc_and_publication_are_exact_child_derivations(self):
        value=examples.fixture(warmup_days=1)
        hours=value["hours"][:24]
        for i,row in enumerate(hours):
            price=D("1.1")+D(i)/10000
            row.update(open=str(price),high=str(price+D(".0002")),low=str(price-D(".0003")),close=str(price+D(".0001")))
            row["lineage"]=s.hour_lineage(value["case"],row)
        hours[-1]["available"]+=3000
        hours[-1]["lineage"]=s.hour_lineage(value["case"],hours[-1])
        end=hours[-1]["end"]
        before,coverage=s.derive(hours,value["calendar"],end+2000)
        self.assertEqual(1,coverage["missing_hour_count"])
        self.assertFalse(any(b.timeframe=="D1" for b in before))
        after,coverage=s.derive(hours,value["calendar"],end+5000)
        day=next(b for b in after if b.timeframe=="D1")
        self.assertEqual((D("1.1"),D("1.1025"),D("1.0997"),D("1.1024")),(day.open,day.high,day.low,day.close))
        self.assertEqual(end+5000,day.available)
        self.assertEqual(0,coverage["missing_hour_count"])
        self.assertEqual(6,sum(b.timeframe=="H4" for b in after))
        self.assertFalse(any(b.timeframe=="D1" for b in before))

    def test_shared_daily_features_and_execution_quotes_are_identical(self):
        root=self.prepared()
        prepared=s.c.daily._json((root/"prepared.json").read_bytes())
        self.assertEqual({"H1":6072,"H4":1518,"D1":253},prepared["warmup"])
        bundle=s.c.daily._json((root/"ew-full-input.json").read_bytes())
        features=s.c.daily._json((root/"daily-input.json").read_bytes())
        daily=[b for b in bundle["bars"] if b["timeframe"]=="D1"]
        self.assertEqual(len(daily),len(features["bars"]))
        for new,old in zip(daily,features["bars"]):
            self.assertEqual((new["start"],new["end"],new["available"]),(old["start_msc"],old["end_msc"],old["available_msc"]))
            self.assertEqual(tuple(D(new[k]) for k in ("open","high","low","close")),tuple(D(str(old[k])) for k in ("open","high","low","close")))
        expected=[(q["source"],q["time"],D(q["bid"]),D(q["ask"])) for q in bundle["quotes"]]
        for path in ("fills-input.json","compiled-input.json"):
            original=s.c.daily._json((root/path).read_bytes())
            self.assertEqual(expected,[(e["source_msc"],e["receipt_msc"],D(str(e["bid"])),D(str(e["ask"]))) for e in original["events"]])

    def test_controls_reconcile_targets_and_gaps_in_both_directions(self):
        for side in (1,-1):
            for outcome in ("target","gap"):
                root=self.prepared(side,outcome)
                for profile in s.c.PROFILES:
                    for candidate in s.c.CANDIDATES:
                        with self.subTest(side=side,outcome=outcome,profile=profile,candidate=candidate):
                            replay=s.SharedReplay(root,candidate,profile);report=replay.run()
                            original=report["original_report"]
                            (audit_account if candidate=="EWPB_D124" else audit_ledger)(replay.engine._fixture,original)
                            self.assertEqual("10000",report["summary"]["initial_cash_usd"])
                            if candidate=="T12_D":
                                self.assertEqual(1,report["summary"]["closed_positions"])
                                self.assertEqual(outcome=="target",Fraction(report["summary"]["toy_net_usd"])>0)
                            else:
                                self.assertEqual("10000",report["summary"]["final_cash_usd"])

    def test_control_restart_held_and_finished_and_ew_prefix_restore(self):
        root=self.prepared()
        for candidate in s.CANDIDATES:
            replay=s.SharedReplay(root,candidate)
            for _ in range(10 if candidate=="EW_FULL_V1" else 1):
                replay.step()
            if candidate=="T12_D":
                self.assertIsNotNone(replay.engine.state["held"])
            cp=replay.checkpoint();restored=s.SharedReplay.restore(root,cp)
            self.assertEqual(cp,restored.checkpoint())
            if candidate!="EW_FULL_V1":
                self.assertEqual(replay.run(),restored.run())
                final=restored.checkpoint()
                self.assertEqual(final,s.SharedReplay.restore(root,final).checkpoint())

    def test_rehashed_engine_prefix_and_control_state_forgeries_reject(self):
        root=self.prepared()
        replay=s.SharedReplay(root,"EW_FULL_V1");replay.step();cp=replay.checkpoint()
        cp["payload"]["inner"]["payload"]["events"][0]["value"]["lineage"]="forged"
        cp["payload"]["inner"]["digest"]=digest(cp["payload"]["inner"]["payload"])
        cp["digest"]=digest(cp["payload"])
        with self.assertRaisesRegex(ValueError,"checkpoint_prefix"):
            s.SharedReplay.restore(root,cp)
        replay=s.SharedReplay(root,"T12_D");replay.step();cp=replay.checkpoint()
        inner=json.loads(cp["payload"]["inner"]);inner["payload"]["state"]["balance_usd"]="1000000"
        inner["sha256"]=s.c.daily._digest(inner["payload"]);cp["payload"]["inner"]=json.dumps(inner);cp["digest"]=digest(cp["payload"])
        with self.assertRaisesRegex(ValueError,"reconstructed_state"):
            s.SharedReplay.restore(root,cp)

    def test_future_hour_changes_leave_all_development_inputs_unchanged(self):
        value=examples.fixture();cut=value["partitions"][1]["end_msc"]
        for row in value["hours"]:
            if row["start"]>=cut:
                for field in ("open","high","low","close"):
                    row[field]=str(D(row[field])+D(".1"))
                row["lineage"]=s.hour_lineage(value["case"],row)
        home,p,m=self.frozen(value);root=home/"prepared";s.prepare(p,m,"development",root)
        for name in ("ew-full-input.json","fills-input.json","daily-input.json"):
            self.assertEqual(s.c.daily._json((self.prepared()/name).read_bytes()),s.c.daily._json((root/name).read_bytes()))

    def test_missing_hour_and_inadequate_warmup_are_unavailable_not_zero_returns(self):
        for missing in (True,False):
            value=examples.fixture(warmup_days=253 if missing else 1)
            if missing:
                del value["hours"][10]
            root,p,m=self.frozen(value);result=s.evaluate(p,m,root/"run")
            self.assertEqual(16,len(result["cells"]));self.assertEqual(0,result["computed_invented_cells"])
            expected="shared_missing_completed_hours" if missing else "shared_insufficient_common_warmup"
            self.assertEqual({expected},{c["reason"] for c in result["cells"]})
            self.assertTrue(all(c["summary"] is None and c["market_returns"] is None for c in result["cells"]))

    def test_endpoint_must_be_exact_fresh_last_observation(self):
        for kind in ("missing","stale","repeated","late_bar"):
            value=examples.fixture();part=value["partitions"][0]
            if kind=="missing":
                part["endpoint_source_msc"]-=1
            elif kind=="stale":
                value["quotes"][1]["source"]-=3000
                part["endpoint_source_msc"]=value["quotes"][1]["source"]
            elif kind=="repeated":
                value["quotes"].insert(2,{**value["quotes"][1],"time":value["quotes"][1]["time"]+1})
                for i,q in enumerate(value["quotes"]):q["sequence"]=i
            else:
                row=next(r for r in value["hours"] if r["end"]==part["end_msc"]-s.HOUR)
                row["available"]=part["end_msc"]-997
                row["lineage"]=s.hour_lineage(value["case"],row)
            root,p,m=self.frozen(value)
            with self.assertRaisesRegex(ValueError,"endpoint"):
                s.prepare(p,m,"development",root/"prepared")

    def test_quote_bar_contradictions_and_extra_timeframes_reject(self):
        value=examples.fixture(warmup_days=1)
        q=value["quotes"][0];row=next(r for r in value["hours"] if r["start"]<=q["source"]<r["end"])
        row["high"]=row["close"];row["lineage"]=s.hour_lineage(value["case"],row)
        with self.assertRaisesRegex(ValueError,"quote_hour_conflict"):
            s.validate(value)
        value=examples.fixture(warmup_days=1);value["hours"][0]["timeframe"]="H4"
        value["hours"][0]["lineage"]=s.hour_lineage(value["case"],value["hours"][0])
        with self.assertRaisesRegex(ValueError,"hour_contract"):
            s.validate(value)

    def test_freeze_mutations_market_schema_and_roundtrip_reject(self):
        root,p,m=self.frozen(examples.fixture(warmup_days=1))
        frozen=json.loads(m.read_text());frozen["orders_available"]=0;m.write_text(json.dumps(frozen))
        with self.assertRaisesRegex(ValueError,"freeze_binding"):
            s.prepare(p,m,"development",root/"prepared")
        self.assertFalse((root/"prepared").exists())
        value=examples.fixture(warmup_days=1);value["kind"]="qualified_market"
        with self.assertRaisesRegex(ValueError,"invented_shared"):
            s.validate(value)
        with self.assertRaisesRegex(ValueError,"float_roundtrip"):
            s._float("1.100000000000000000000000000001")
        value=examples.fixture(warmup_days=1);first=value["quotes"][0]
        value["quotes"]=[{**first,"source":first["source"]+i,"time":first["time"]+i} for i in range(257)]+value["quotes"][2:]
        for i,q in enumerate(value["quotes"]):q["sequence"]=i
        with self.assertRaisesRegex(ValueError,"partition_quote_limit"):
            s.validate(value)
        with localcontext() as context:
            context.prec=6
            s.validate(examples.fixture(warmup_days=1))

    def test_cross_partition_checkpoint_and_conflicting_duplicate_reject(self):
        root=self.prepared();replay=s.SharedReplay(root,"CASH");first=deepcopy(replay.events[0])
        replay.step(first);cp=replay.checkpoint();self.assertFalse(replay.step(first))
        bad={**first,"bid":first["bid"]-.00001}
        with self.assertRaisesRegex(ValueError,"event_binding"):
            replay.step(bad)
        self.assertEqual(cp,replay.checkpoint())
        other=self.prepared(partition="later_validation")
        with self.assertRaisesRegex(ValueError,"checkpoint_partition"):
            s.SharedReplay.restore(other,cp)

    def test_public_cli_computes_all_16_invented_cells_with_common_warmup(self):
        # One full public replay is sufficient: the constructed trend has no
        # resolved Elliott context. Its abstention is checked, not called a win.
        configured=os.environ.get("ELLIOTT_SHARED_EVIDENCE_DIR")
        home=Path(configured) if configured else self.root/"public-cli"
        home.mkdir(parents=True,exist_ok=False)
        s.c.daily.write_new(home/"declaration.json",{"kind":"invented_shared_hourly_demo","case":"short_gap",
                            "sources":s.c.source_bindings(),"market_cells_run":0,"orders_available":False})
        script=str(ROOT/"scripts/elliott-full-shared.py");p=home/"input.json";m=home/"freeze.json";run=home/"run"
        commands=(("fixture",str(p),"--side","-1","--outcome","gap"),("freeze",str(p),str(m)),("replay",str(p),str(m),str(run)))
        for args in commands:
            completed=subprocess.run([sys.executable,script,*args],cwd=ROOT,text=True,capture_output=True)
            with (home/"cli.txt").open("a") as f:f.write(completed.stdout+completed.stderr)
            self.assertEqual(0,completed.returncode,completed.stderr)
        result=json.loads((run/"comparison-status.json").read_text())
        self.assertEqual(16,result["computed_invented_cells"]);self.assertEqual(16,len(result["cells"]))
        self.assertEqual(0,result["market_cells_run"]);self.assertFalse(result["orders_available"])
        self.assertTrue(all(c["market_status"]=="UNAVAILABLE" and c["market_returns"] is None for c in result["cells"]))
        for partition in ("development","later_validation"):
            directory=run/partition
            for profile in s.c.PROFILES:
                replay=s.SharedReplay(directory,"EW_FULL_V1",profile)
                report=json.loads((directory/f"EW_FULL_V1-{profile}.json").read_text())
                self.assertEqual("0",report["summary"]["toy_net_usd"])
                self.assertFalse(report["original_report"]["ledger"]["trades"])
                self.assertFalse(any(snap["signals"] for snap in report["original_report"]["snapshots"]))
                for candidate in s.c.CANDIDATES:
                    control=s.SharedReplay(directory,candidate,profile)
                    original=json.loads((directory/f"{candidate}-{profile}.json").read_text())["original_report"]
                    (audit_account if candidate=="EWPB_D124" else audit_ledger)(control.engine._fixture,original)
        with self.assertRaises(FileExistsError):
            s.evaluate(p,m,run)


if __name__=="__main__":
    unittest.main()
