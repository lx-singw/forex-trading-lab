"""Public shared entry paths, independent rational fills and pending/held restarts."""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as F
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.elliott_full import shared as s
from forex_demo_lab.elliott_full.contracts import D
from forex_demo_lab.elliott_full.strategy import Strategy
from forex_demo_lab.elliott_full.report import render,viewer_data

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("shared_entry_fixture",ROOT/"scripts/elliott-full-shared-entry.py")
examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(examples)
CASES=(("EW3",1,"target"),("EW3",-1,"gap"),("EW5",1,"gap"),("EW5",-1,"target"))


def before_quote(replay):
    while replay.cursor<len(replay.events) and replay.events[replay.cursor]["kind"]!="quote":
        replay.step()
    return replay.engine.pending


def drain(replay):
    while replay.step():pass


def rounding(value,side):
    scaled=value/F(".00001")
    integer=scaled.numerator//scaled.denominator if side==1 else -((-scaled.numerator)//scaled.denominator)
    return integer*F(".00001")


class SharedEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=tempfile.TemporaryDirectory();cls.root=Path(cls.home.name)

    @classmethod
    def tearDownClass(cls):cls.home.cleanup()

    def prepared(self,value):
        root=Path(tempfile.mkdtemp(dir=self.root));p=root/"input.json";f=root/"freeze.json"
        s.c.daily.write_new(p,value);s.freeze(p,f);s.prepare(p,f,"development",root/"prepared")
        return root/"prepared"

    def test_unresolved_and_completed_parent_paths_still_skip(self):
        for compression,phase,expected in ((D(".8"),0,"competitive_disagreement"),(D("1"),0,"context_disagreement"),(D(".9"),1,"context_disagreement")):
            value=examples.fixture(compression=compression,phase=phase)
            bars,_=s.derive(value["hours"],value["calendar"],value["quotes"][0]["time"])
            strategy=Strategy();signals=[]
            for bar in bars:signals.extend(strategy.on_bar(bar))
            self.assertFalse(signals)
            self.assertEqual(expected,strategy.policy.reason)

    def test_future_exit_price_does_not_change_pending_entry(self):
        value=examples.fixture();first=self.prepared(value)
        q=value["quotes"][1];q["bid"]=str(D(q["bid"])+D(".04"));q["ask"]=str(D(q["ask"])+D(".04"))
        row=next(r for r in value["hours"] if r["start"]<=q["source"]<r["end"])
        row["high"]=str(max(D(row["high"]),(D(q["bid"])+D(q["ask"]))/2))
        row["lineage"]=s.hour_lineage(value["case"],row)
        second=self.prepared(value)
        a=s.SharedReplay(first,"EW_FULL_V1");b=s.SharedReplay(second,"EW_FULL_V1")
        self.assertEqual(asdict(before_quote(a)),asdict(before_quote(b)))
        self.assertEqual(a.engine.strategy.snapshots,b.engine.strategy.snapshots)

    def test_public_matrix_entry_restart_and_independent_accounting(self):
        configured=os.environ.get("ELLIOTT_ENTRY_EVIDENCE_DIR")
        home=Path(configured) if configured else self.root/"matrix"
        home.mkdir(parents=True,exist_ok=False)
        s.c.daily.write_new(home/"declaration.json",{"kind":"invented_shared_entry_acceptance","cases":[{"setup":k,"side":side,"outcome":outcome} for k,side,outcome in CASES],
                            "sources":s.c.source_bindings(),"profiles":list(s.c.PROFILES),"market_cells_run":0,"orders_available":False,
                            "fixture_compression":".9","fixture_phase":0,"selection":"software_state_coverage_not_market_returns"})
        results=[];script=str(ROOT/"scripts/elliott-full-shared-entry.py")
        for kind,side,outcome in CASES:
            case=f"{kind}-{'long' if side==1 else 'short'}-{outcome}";directory=home/case;directory.mkdir()
            p=directory/"input.json";f=directory/"freeze.json";run=directory/"run"
            for args in (("fixture",str(p),"--setup",kind,"--side",str(side),"--outcome",outcome),("freeze",str(p),str(f)),("replay",str(p),str(f),str(run))):
                done=subprocess.run([sys.executable,script,*args],cwd=ROOT,text=True,capture_output=True)
                with (directory/"cli.txt").open("a") as log:log.write(done.stdout+done.stderr)
                self.assertEqual(0,done.returncode,done.stderr)
            status=json.loads((run/"comparison-status.json").read_text())
            self.assertEqual(16,status["computed_invented_cells"])
            self.assertTrue(all(c["market_status"]=="UNAVAILABLE" and c["market_returns"] is None for c in status["cells"]))
            prepared=run/"development";bundle=json.loads((prepared/"ew-full-input.json").read_text())
            q0,q1=bundle["quotes"]
            for profile in s.c.PROFILES:
                with self.subTest(case=case,profile=profile):
                    replay=s.SharedReplay(prepared,"EW_FULL_V1",profile)
                    signal=before_quote(replay);self.assertIsNotNone(signal)
                    self.assertEqual((side,kind),(signal.side,signal.kind))
                    self.assertEqual({"D1":side,"H4":side},replay.engine.strategy.contexts)
                    self.assertLess(signal.formed,q0["source"])
                    pending=replay.checkpoint()
                    with gzip.open(directory/f"pending-{profile}.json.gz","wt",encoding="utf-8") as stream:json.dump(pending,stream)
                    restored_pending=s.SharedReplay.restore(prepared,pending)
                    replay.step();restored_pending.step()
                    position=deepcopy(replay.engine.ledger.position);self.assertIsNotNone(position)
                    self.assertEqual(position,restored_pending.engine.ledger.position)
                    checkpoint=replay.checkpoint()
                    with gzip.open(directory/f"held-{profile}.json.gz","wt",encoding="utf-8") as stream:json.dump(checkpoint,stream)
                    restored_held=s.SharedReplay.restore(prepared,checkpoint)
                    drain(replay);drain(restored_pending);drain(restored_held)
                    self.assertEqual(replay.engine.ledger.state(),restored_pending.engine.ledger.state())
                    self.assertEqual(replay.engine.ledger.state(),restored_held.engine.ledger.state())
                    self.assertEqual(replay.engine.strategy.snapshots,restored_held.engine.strategy.snapshots)
                    ledger=replay.engine.ledger
                    self.assertEqual(1,len(ledger.trades));self.assertTrue(ledger.finished)
                    self.assertIsNone(ledger.position)
                    # Independent rational calculations: production fill, price,
                    # sizing and rounding functions are not used as the oracle.
                    fee,slip,floor=(F(7),F(".00002"),F(0)) if profile=="base" else (F(10),F(".00005"),F(".00012"))
                    bid0,ask0=F(q0["bid"]),max(F(q0["ask"]),F(q0["bid"])+floor)
                    entry=ask0+slip if side==1 else bid0-slip
                    stop=rounding(F(signal.stop),side);distance=side*(entry-stop)
                    per_lot=(distance+slip)*100000+fee
                    raw=min(F(25)/per_lot,F(10000)/(entry*100000/30+fee/2),F(1))
                    lots=F((raw*100).numerator//(raw*100).denominator,100)
                    target=rounding(entry+side*2*distance,side)
                    self.assertEqual((entry,stop,target,lots),tuple(F(position[k]) for k in ("entry","stop","target","lots")))
                    bid1,ask1=F(q1["bid"]),max(F(q1["ask"]),F(q1["bid"])+floor)
                    fill=target if outcome=="target" else (bid1 if side==1 else ask1)-side*slip
                    gross=side*(fill-entry)*lots*100000;net=gross-fee*lots
                    trade=ledger.trades[0]
                    self.assertEqual((fill,gross,net,per_lot*lots),tuple(F(trade[k]) for k in ("exit","gross","net","estimated_risk")))
                    self.assertEqual(F(10000)+net,F(ledger.cash));self.assertLessEqual(per_lot*lots,25)
                    self.assertEqual("target" if outcome=="target" else "stop",trade["reason"])
                    if outcome=="gap":
                        self.assertGreater(-net,per_lot*lots);self.assertTrue(ledger.paused)
                    report=json.loads((prepared/f"EW_FULL_V1-{profile}.json").read_text())
                    self.assertEqual(ledger.state(),report["original_report"]["ledger"])
                    display={"bars":bundle["bars"],**report["original_report"],"limitations":["Invented shared H1 observations; market validation and orders unavailable","Constructed entry and exit coverage; no estimate of trading advantage"]}
                    data=viewer_data(display)
                    self.assertEqual(1,sum(row["reason"]=="entry" for row in data["snapshots"]))
                    self.assertTrue(any(row["reason"].startswith("exit:") for row in data["snapshots"]))
                    (directory/f"replay-{profile}.html").write_text(render(display),encoding="utf-8")
                    results.append({"case":case,"profile":profile,"setup":kind,"side":side,"exit":trade["reason"],
                                    "trades":1,"pending_restart":True,"held_restart":True,"fraction_reconciled":True})
                    del pending,checkpoint,restored_pending,restored_held,replay
        s.c.daily.write_new(home/"results.json",{"kind":"invented_shared_entry_acceptance","accounts":results,
                            "computed_invented_cells":64,"market_cells_run":0,"orders_available":False,"strategy_selected":False})
        self.assertEqual(8,len(results))


if __name__=="__main__":unittest.main()
