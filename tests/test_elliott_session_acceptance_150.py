"""Fixed automatic EW3/EW5 long/short session comparisons; invented inputs only."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from fractions import Fraction as F
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import elliott_session_comparison_149 as s
from test_daily_fills_120 import audit_ledger
from test_elliott_execution_125 import audit_account

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/elliott-session-comparison-149.py"
CASES=(("EW3",1,"target"),("EW3",-1,"gap"),("EW5",1,"gap"),("EW5",-1,"target"))
BASELINE={"trend":"d57210449bd0c9d8e15e38448e6c03810ac862036037848ed7d52e4073d9543f",
          "wave":"69eb799be385a70eca5dfe6b348114235902522482a6f97dc1324b5c33245b35",
          "shifted":"a09468954577379fa53ddfc609d65b38b8dbd09031b4c961c01e01db955a87d8"}


def examples():
    spec=importlib.util.spec_from_file_location("acceptance150_example",SCRIPT)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def case_name(kind,side,outcome):return kind.lower()+"_"+("long" if side==1 else "short")+"_"+outcome


def round_tick(value,side):
    scaled=value/F(".00001")
    count=scaled.numerator//scaled.denominator if side==1 else -((-scaled.numerator)//scaled.denominator)
    return count*F(".00001")


class Fixture150Tests(unittest.TestCase):
    def test_existing_default_fixtures_match_recorded149_inputs(self):
        for case,expected in BASELINE.items():self.assertEqual(expected,s.digest(examples().fixture(case)))

    def test_parameters_reject_unsupported_families_sides_and_outcomes(self):
        for params in ({"setup":"ABC"},{"side":0},{"side":True},{"outcome":"selected_winner"}):
            with self.subTest(params=params),self.assertRaises(ValueError):examples().fixture("wave",**params)
        with self.assertRaises(ValueError):examples().fixture("trend",setup="EW5")

    def test_target_and_gap_future_quotes_preserve_ew5_short_decision_prefix(self):
        a=examples().fixture("wave",setup="EW5",side=-1,outcome="target")
        b=examples().fixture("wave",setup="EW5",side=-1,outcome="gap")
        ea=s.scope(a,"development")[5];eb=s.scope(b,"development")[5]
        self.assertEqual(ea[:-2],eb[:-2]);self.assertNotEqual(ea[-2:],eb[-2:])
        self.assertEqual("quote",ea[-2]["kind"]);self.assertEqual("finish",ea[-1]["kind"])

    def test_public_fixture_flags_create_exact_requested_invention(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"input.json"
            args=[sys.executable,str(SCRIPT),"fixture",str(output),"--case","wave","--setup","EW5","--side","-1","--outcome","target"]
            done=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
            self.assertEqual(examples().fixture("wave",setup="EW5",side=-1,outcome="target"),json.loads(output.read_text()))
            self.assertNotEqual(0,subprocess.run(args+["--live"],capture_output=True).returncode)


class Acceptance150Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=tempfile.TemporaryDirectory()
        cls.root=Path(os.environ.get("ELLIOTT_ACCEPTANCE_EVIDENCE_DIR",str(Path(cls.home.name)/"acceptance")))
        cls.root.mkdir(parents=True,exist_ok=False)
        files=(SCRIPT,ROOT/"scripts/elliott-full-shared-entry.py",ROOT/"tests/test_elliott_full_policy.py",Path(__file__))
        cls.generators={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        declaration={"kind":"invented_session_acceptance150_pre_return_declaration",
                     "cases":[{"setup":kind,"side":side,"outcome":outcome} for kind,side,outcome in CASES],
                     "profiles":list(s.PROFILES),"partitions":list(s.PARTITIONS),"planned_comparison_cells":64,
                     "primary_ew_accounts":8,"sources":s.source_bindings(),"generators":cls.generators,
                     "selection":"fixed_software_state_coverage_before_returns","market_cells_run":0,"orders_available":False}
        s.write(cls.root/"declaration.json",declaration)
        available=0
        if Path("/proc/meminfo").exists():
            available=int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:")))
        workers=2 if available>=4*1024*1024 and (os.cpu_count() or 1)>=2 else 1
        cls.case_roots={}
        def run_case(case):
            kind,side,outcome=case;name=case_name(*case);root=cls.root/name;root.mkdir()
            input,manifest,output=root/"input.json",root/"freeze.json",root/"run"
            commands=(("fixture",str(input),"--case","wave","--setup",kind,"--side",str(side),"--outcome",outcome),
                      ("freeze",str(input),str(manifest)),("replay",str(input),str(manifest),str(output)))
            for args in commands:
                done=subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)
                with (root/"cli.txt").open("a") as log:log.write(done.stdout+done.stderr)
                if done.returncode:raise AssertionError(name+": "+done.stderr)
            status=json.loads((output/"comparison-status.json").read_text())
            if len(status["cells"])!=16 or status["computed_invented_cells"]!=16:
                raise AssertionError(name+": comparison unavailable "+json.dumps(status["cells"]))
            return name,root
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs=[pool.submit(run_case,case) for case in CASES]
            for job in as_completed(jobs):
                name,root=job.result();cls.case_roots[name]=root
                with (cls.root/"progress.jsonl").open("a") as log:log.write(json.dumps({"case":name,"computed_paper_cells":16})+"\n")
        for path,expected in cls.generators.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise AssertionError("generator changed during acceptance")

    @classmethod
    def tearDownClass(cls):cls.home.cleanup()

    def test_all64_cells_are_retained_independent_and_market_unavailable(self):
        cells=[]
        for case,root in sorted(self.case_roots.items()):
            status=json.loads((root/"run/comparison-status.json").read_text())
            self.assertFalse(status["strategy_selected"]);self.assertFalse(status["capital_summed_as_portfolio"])
            self.assertEqual(16,len(status["report_sha256"]))
            for cell in status["cells"]:
                self.assertEqual("computed",cell["invented_status"])
                self.assertEqual("10000",cell["summary"]["initial_cash_usd"])
                self.assertEqual("UNAVAILABLE",cell["market_status"]);self.assertIsNone(cell["market_returns"])
                cells.append({"case":case,**{k:cell[k] for k in ("candidate","profile","partition","invented_status","market_status","market_returns")}})
        self.assertEqual(64,len(cells));s.write(self.root/"cells.json",{"kind":"invented_acceptance150_cells","cells":cells,"market_cells_run":0,"orders_available":False})

    def test_eight_primary_ew_accounts_reconcile_with_independent_rational_fills(self):
        results=[]
        for kind,side,outcome in CASES:
            root=self.case_roots[case_name(kind,side,outcome)];value=json.loads((root/"input.json").read_text());q0,q1=value["quotes"][:2]
            for profile in s.PROFILES:
                report=json.loads((root/"run/development"/("EW_FULL_V1-"+profile+".json")).read_text())
                state=report["original_report"];ledger=state["ledger"]
                self.assertTrue(ledger["finished"]);self.assertIsNone(ledger["position"])
                self.assertEqual(1,len(ledger["trades"]));self.assertEqual(1,report["summary"]["closed_positions"])
                entry=next(e for e in ledger["events"] if e["kind"]=="entry")
                formations=[(snapshot,signal) for snapshot in state["decisions"]["snapshots"] for signal in snapshot["signals"] if signal["key"]==entry["key"]]
                self.assertEqual(1,len(formations));snapshot,signal=formations[0]
                self.assertEqual((kind,side),(signal["kind"],signal["side"]))
                self.assertEqual({"D1":side,"H4":side},snapshot["context"])
                self.assertTrue(snapshot["session_coverage"]["ready"])
                fee,slip,floor,latency=(F(7),F(".00002"),F(0),250) if profile=="base" else (F(10),F(".00005"),F(".00012"),1000)
                self.assertGreater(q0["source"],signal["formed"]+latency);self.assertLessEqual(q0["time"],signal["expires"])
                bid0=F(q0["bid"]);ask0=max(F(q0["ask"]),bid0+floor)
                price=(ask0 if side==1 else bid0)+side*slip
                stop=round_tick(F(signal["stop"]),side);distance=side*(price-stop)
                target=round_tick(price+side*2*distance,side)
                per_lot=(distance+slip)*100000+fee
                raw=min(F(25)/per_lot,F(10000)/(price*100000/30+fee/2),F(1))
                lots=F((raw*100).numerator//(raw*100).denominator,100)
                self.assertEqual((price,stop,target,lots),tuple(F(entry[k]) for k in ("entry","stop","target","lots")))
                self.assertLessEqual(per_lot*lots,25)
                if signal["ceiling"] is not None:self.assertLessEqual(side*(target-F(signal["ceiling"])),0)
                bid1=F(q1["bid"]);ask1=max(F(q1["ask"]),bid1+floor)
                fill=target if outcome=="target" else (bid1 if side==1 else ask1)-side*slip
                gross=side*(fill-price)*lots*100000;net=gross-fee*lots;trade=ledger["trades"][0]
                self.assertEqual((fill,gross,net,per_lot*lots),tuple(F(trade[k]) for k in ("exit","gross","net","estimated_risk")))
                self.assertEqual(F(10000)+net,F(ledger["cash"]));self.assertEqual("target" if outcome=="target" else "stop",trade["reason"])
                self.assertEqual(q0["time"]//s.DAY,q1["time"]//s.DAY)
                if outcome=="gap":self.assertGreater(-net,per_lot*lots);self.assertTrue(ledger["paused"])
                results.append({"case":case_name(kind,side,outcome),"setup":kind,"side":side,"profile":profile,
                                "trades":1,"exit":trade["reason"],"fraction_reconciled":True,
                                "gap_loss_beyond_estimate":outcome=="gap","market_cells_run":0,"orders_available":False})
        s.write(self.root/"primary-accounts.json",{"kind":"invented_session_primary_acceptance150","accounts":results,"market_cells_run":0,"orders_available":False})

    def test_all48_control_accounts_reconcile_without_rule_changes(self):
        records=[]
        for case,root in sorted(self.case_roots.items()):
            for partition in s.PARTITIONS:
                for profile in s.PROFILES:
                    for candidate in s.CANDIDATES[1:]:
                        prepared=root/"run"/partition
                        report=json.loads((prepared/(candidate+"-"+profile+".json")).read_text())
                        replay=s.ComparisonReplay(prepared,candidate,profile)
                        original=report["original_report"]["original_report"]
                        (audit_account if candidate=="EWPB_D124" else audit_ledger)(replay.engine.engine._fixture,original)
                        records.append({"case":case,"partition":partition,"profile":profile,"candidate":candidate,"independent_audit":True})
        self.assertEqual(48,len(records));s.write(self.root/"control-audits.json",{"kind":"invented_control_acceptance150","accounts":records})

    def test_each_later_partition_has_fresh_capital_and_no_incoming_position(self):
        for root in self.case_roots.values():
            for profile in s.PROFILES:
                report=json.loads((root/"run/later_validation"/("EW_FULL_V1-"+profile+".json")).read_text())
                ledger=report["original_report"]["ledger"]
                self.assertEqual(F(10000)+sum((F(t["net"]) for t in ledger["trades"]),F(0)),F(ledger["cash"]))
                self.assertEqual("10000",report["summary"]["initial_cash_usd"]);self.assertIsNone(ledger["position"])

    def test_ew5_pending_and_held_restart_in_separate_processes(self):
        witnesses=(("ew5_short_target","adverse","pending"),("ew5_long_gap","base","held"));results=[]
        code="""import gzip,json,sys
from pathlib import Path
from forex_demo_lab import elliott_session_comparison_149 as s
with gzip.open(sys.argv[2],'rt') as f:checkpoint=json.load(f)
replay=s.ComparisonReplay.restore(Path(sys.argv[1]),checkpoint)
s.write(sys.argv[3],replay.run())
"""
        for case,profile,stage in witnesses:
            root=self.case_roots[case];prepared=root/"run/development";replay=s.ComparisonReplay(prepared,"EW_FULL_V1",profile)
            while replay.events[replay.cursor]["kind"]!="quote":replay.step()
            self.assertIsNotNone(replay.engine.pending)
            if stage=="held":replay.step();self.assertIsNotNone(replay.engine.ledger.position)
            checkpoint=root/(stage+"-"+profile+".json.gz")
            with gzip.open(checkpoint,"wt") as output:json.dump(replay.checkpoint(),output)
            continuous=replay.run();target=root/(stage+"-"+profile+"-restored.json")
            done=subprocess.run([sys.executable,"-c",code,str(prepared),str(checkpoint),str(target)],capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
            self.assertEqual(continuous,json.loads(target.read_text()))
            saved=json.loads((prepared/("EW_FULL_V1-"+profile+".json")).read_text())
            self.assertEqual(saved["original_report"]["ledger"],continuous["original_report"]["ledger"])
            results.append({"case":case,"profile":profile,"stage":stage,"separate_process":True,"whole_state_equal":True})
        s.write(self.root/"restarts.json",{"kind":"invented_session_restart_acceptance150","cases":results,"market_cells_run":0,"orders_available":False})

    def test_market_and_native_submission_stay_unavailable(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(cell["status"]=="UNAVAILABLE" and cell["returns"] is None for cell in study_status()["cells"]))
        self.assertFalse(DemoBoundary().submission_status()["available"])


if __name__=="__main__":unittest.main()
