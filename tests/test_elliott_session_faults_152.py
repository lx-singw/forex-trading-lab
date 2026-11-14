"""Automatic EW prefixes under declared variable warmup and fixed fault branches."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
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

from forex_demo_lab import elliott_session_comparison_149 as c
from forex_demo_lab.elliott_full.contracts import digest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/"scripts/elliott-session-faults-152.py"


def module():
    spec = importlib.util.spec_from_file_location("fault152_examples", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class Fixture152Tests(unittest.TestCase):
    def test_variable_prefix_covers_same_hours_and_retains_future_schedule(self):
        example = module()
        value = example.fixture("ew3_long")
        rows = value["calendar"]["segments"]
        self.assertEqual([12,12,23,25], [(r["end"]-r["start"])//c.observations.HOUR for r in rows[:4]])
        self.assertEqual([True,True,False,False], [r["partial"] for r in rows[:4]])
        calendar = c.observations.Calendar.from_record(value["calendar"])
        self.assertEqual(rows[0]["start"]+72*c.observations.HOUR, rows[3]["end"])
        self.assertEqual(4, len([w for w in calendar.frame("D1") if w.end <= rows[3]["end"]]))
        self.assertEqual(19, len([w for w in calendar.frame("H4") if w.end <= rows[3]["end"]]))
        self.assertEqual(72, len([w for w in calendar.frame("H1") if w.end <= rows[3]["end"]]))
        calendar_sha = calendar.sha256
        for hour in value["hours"]:
            self.assertEqual(c.hour_lineage(value["case"],calendar_sha,hour), hour["lineage"])
        with self.assertRaisesRegex(ValueError, "legacy_requires"):
            c.legacy_calendar(calendar)

    def test_fixture_is_deterministic_and_rejects_unsupported_cases(self):
        example = module()
        self.assertEqual(digest(example.fixture("ew5_short")), digest(example.fixture("ew5_short")))
        for value in ("market", "ew5_long", None):
            with self.assertRaises(ValueError):example.fixture(value)

    def test_public_fixture_cli_is_exact_exclusive_and_has_no_live_option(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"input.json"
            args = [sys.executable,str(SCRIPT),"fixture",str(path),"--case","ew3_long"]
            done = subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
            self.assertEqual(module().fixture("ew3_long"),json.loads(path.read_text()))
            self.assertFalse(json.loads(done.stdout)["orders_available"])
            self.assertNotEqual(0,subprocess.run(args,capture_output=True).returncode)
            self.assertNotEqual(0,subprocess.run(args+["--live"],capture_output=True).returncode)


class AutomaticFault152Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(os.environ.get("ELLIOTT_FAULT_EVIDENCE_DIR", str(Path(cls.temp.name)/"matrix")))
        cls.root.mkdir(parents=True,exist_ok=False)
        cls.example = module()
        cls.sources = cls.example.sources()
        c.write(cls.root/"declaration.json", {"kind":"invented_fault152_matrix_before_returns",
                "cases":cls.example.CASES,"profiles":list(c.PROFILES),"faults":list(cls.example.FAULTS),
                "branches":40,"sources":cls.sources,"market_cells_run":0,"orders_available":False})
        cls.records = {}
        available = 0
        if Path('/proc/meminfo').exists():
            available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
        workers = 2 if available >= 4*1024*1024 and (os.cpu_count() or 1) >= 2 else 1
        def run_case(case,profile):
            path=cls.root/(case+'-'+profile)
            done=subprocess.run([sys.executable,str(SCRIPT),'exercise',str(path),'--case',case,'--profile',profile],capture_output=True,text=True)
            (cls.root/(case+'-'+profile+'-cli.txt')).write_text(done.stdout+done.stderr)
            if done.returncode:raise AssertionError(case+' '+profile+': '+done.stderr)
            return case,profile,json.loads((path/'cases.json').read_text())
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(run_case,case,profile) for case in cls.example.CASES for profile in c.PROFILES]
            for future in as_completed(futures):
                case,profile,record=future.result()
                cls.records[case,profile]=record
        if cls.sources != cls.example.sources():raise AssertionError("sources changed")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all40_predeclared_branches_remain_and_prefixes_are_automatic(self):
        for (case,profile),record in self.records.items():
            self.assertEqual(list(self.example.FAULTS),[r["fault"] for r in record["cases"]])
            prefix=record["prefix"];kind,side,_=self.example.CASES[case]
            self.assertEqual((kind,side),(prefix["signal"]["kind"],prefix["signal"]["side"]))
            self.assertEqual({"D1":side,"H4":side},prefix["contexts"])
            self.assertGreaterEqual(min(prefix["bars"].values()),253)
            self.assertTrue(prefix["coverage"]["ready"])
            self.assertFalse(record["orders_available"]);self.assertEqual(0,record["market_cells_run"])
            for result in record["cases"]:
                self.assertTrue(result["ledger"]["finished"])
                self.assertTrue(result["snapshot_history_unchanged"])
                self.assertIsNone(result["pending"])
                self.assertIsNone(result["ledger"]["position"])

    def test_36_filled_accounts_independently_reconcile_fills_size_costs_and_financing(self):
        checks=[]
        for (case,profile),record in self.records.items():
            signal=record["prefix"]["signal"];side=signal["side"]
            fee,slip,floor,rate=(F(7),F('.00002'),F(0),F(3) if side==1 else F('1.5')) if profile=='base' else (F(10),F('.00005'),F('.00012'),F('4.5') if side==1 else F('2.25'))
            def tick(value):
                scaled=value/F('.00001');whole=scaled.numerator//scaled.denominator if side==1 else -((-scaled.numerator)//scaled.denominator)
                return whole*F('.00001')
            for result in record['cases']:
                if result['fault']=='expired':continue
                with self.subTest(case=case,profile=profile,fault=result['fault']):
                    ledger=result['ledger'];self.assertEqual(1,len(ledger['trades']));trade=ledger['trades'][0]
                    event=next(e for e in ledger['events'] if e['kind']=='entry')
                    q0=next(q for q in result['quotes'] if q['time']==int(event['time']))
                    q1=next(q for q in result['quotes'] if q['time']==trade['time'])
                    entry=(max(F(q0['ask']),F(q0['bid'])+floor) if side==1 else F(q0['bid']))+side*slip
                    stop=tick(F(signal['stop']));distance=side*(entry-stop);target=tick(entry+side*2*distance)
                    per_lot=(distance+slip)*100000+fee
                    raw=min(F(25)/per_lot,F(10000)/(entry*100000/30+fee/2),F(1));lots=F((raw*100).numerator//(raw*100).denominator,100)
                    self.assertEqual((entry,stop,target,lots),tuple(F(event[k]) for k in ('entry','stop','target','lots')))
                    self.assertLessEqual(per_lot*lots,25)
                    if signal['ceiling'] is not None:self.assertLessEqual(side*(target-F(signal['ceiling'])),0)
                    self.assertGreater(q0['source'],signal['formed']+(250 if profile=='base' else 1000))
                    self.assertLessEqual(q0['time'],signal['formed']+60000)
                    finance=F(0)
                    for day in range(q0['time']//c.DAY+1,q1['time']//c.DAY+1):
                        weekday=datetime.fromtimestamp((day-1)*86400,timezone.utc).weekday()
                        finance+=rate*lots*(3 if weekday==2 else 0 if weekday>=5 else 1)
                    exit_price=target if trade['reason']=='target' else (F(q1['bid']) if side==1 else max(F(q1['ask']),F(q1['bid'])+floor))-side*slip
                    gross=side*(exit_price-entry)*100000*lots;net=gross-fee*lots-finance
                    self.assertEqual((exit_price,gross,net,per_lot*lots),tuple(F(trade[k]) for k in ('exit','gross','net','estimated_risk')))
                    self.assertEqual(finance,sum((F(e['debit']) for e in ledger['events'] if e['kind']=='financing'),F(0)))
                    self.assertEqual(F(10000)+net,F(ledger['cash']))
                    checks.append({'case':case,'profile':profile,'fault':result['fault'],'fraction_reconciled':True,'financing_usd':str(finance)})
        self.assertEqual(36,len(checks));c.write(self.root/'accounting.json',{'accounts':checks})

    def test_unavailable_and_wide_quotes_retry_without_early_entry(self):
        expected={'wide_retry':'entry_spread','stale_retry':'unavailable_quote','raw_closed_retry':'unavailable_quote','repeated_source_retry':'entry_spread'}
        for record in self.records.values():
            for result in record['cases']:
                if result['fault'] not in expected:continue
                self.assertEqual(expected[result['fault']],result['trace'][0]['result'])
                entry=next(e for e in result['ledger']['events'] if e['kind']=='entry')
                self.assertGreater(int(entry['time']),result['quotes'][0]['time'])
                if result['fault']=='repeated_source_retry':self.assertEqual('unavailable_quote',result['trace'][1]['result'])

    def test_automatic_expiry_cannot_reenter_or_change_cash(self):
        for record in self.records.values():
            result=next(r for r in record['cases'] if r['fault']=='expired')
            self.assertEqual([],result['ledger']['trades']);self.assertEqual('10000',result['ledger']['cash'])
            self.assertEqual('expired',result['cancellations'][-1]['reason'])
            self.assertFalse(any(e['kind']=='entry' for e in result['ledger']['events']))

    def test_gap_protection_operates_without_coverage_and_after_closure(self):
        for record in self.records.values():
            for result in record['cases']:
                if result['fault'] not in ('missing_bars_gap','closure_gap'):continue
                trade=result['ledger']['trades'][0]
                self.assertEqual('stop',trade['reason']);self.assertGreater(-F(trade['net']),F(trade['estimated_risk']))
                self.assertTrue(result['ledger']['paused']);self.assertFalse(result['final_coverage']['ready'])
                if result['fault']=='closure_gap':
                    closed=result['quote_gates'][-2]
                    self.assertTrue(closed['declared_open']);self.assertFalse(closed['effective_open'])
                    self.assertGreater(trade['time'],closed['time'])
                    self.assertTrue(any(t.get('whole_state_unchanged') for t in result['trace'] if t['kind']=='finish'))

    def test_duplicate_conflicts_and_invalid_batches_are_atomic_on_automatic_pending(self):
        for record in self.records.values():
            for result in record['cases']:
                if result['fault'] not in ('duplicate_conflict','invalid_batch'):continue
                rejected=[t for t in result['trace'] if t.get('rejected')]
                self.assertEqual(1,len(rejected));self.assertTrue(rejected[0]['whole_state_unchanged'])
                self.assertEqual(1,len(result['ledger']['trades']))
                if result['fault']=='duplicate_conflict':self.assertTrue(any(t.get('result')=='duplicate' for t in result['trace']))

    def test_fault_pending_and_closed_held_restart_in_separate_processes(self):
        checks=[]
        for case,profile,fault in (('ew5_short','adverse','wide_retry'),('ew3_long','base','closure_gap')):
            directory=self.root/(case+'-'+profile);checkpoint=directory/(fault+'.json.gz')
            with gzip.open(checkpoint,'rt') as file:saved=json.load(file)
            state=saved['payload']['state']
            if fault=='wide_retry':self.assertIsNotNone(state['pending']);self.assertIsNone(state['ledger']['position'])
            else:
                self.assertIsNotNone(state['ledger']['position']);self.assertFalse(state['quote_gates'][-1]['effective_open'])
                original=next(r for r in self.records[case,profile]['cases'] if r['fault']==fault)['entry_position']
                self.assertEqual((original['stop'],original['target']),(state['ledger']['position']['stop'],state['ledger']['position']['target']))
            self.assertEqual(self.records[case,profile]['prefix']['snapshot_sha256'],digest(state['decisions']['snapshots']))
            output=directory/(fault+'-restored.json')
            done=subprocess.run([sys.executable,str(SCRIPT),'resume',str(checkpoint),str(checkpoint.with_suffix('.continuation.json')),str(output)],capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
            actual=json.loads(output.read_text());expected=next(r for r in self.records[case,profile]['cases'] if r['fault']==fault)
            self.assertEqual(expected['whole_state_sha256'],actual['whole_state_sha256'])
            self.assertEqual(expected['ledger'],actual['ledger'])
            checks.append({'case':case,'profile':profile,'fault':fault,'separate_process':True,'whole_state_digest_equal':True,'ledger_equal':True})
        c.write(self.root/'restarts.json',{'cases':checks,'market_cells_run':0,'orders_available':False})

    def test_market_cells_and_native_submission_remain_unavailable(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(cell['status']=='UNAVAILABLE' and cell['returns'] is None for cell in study_status()['cells']))
        self.assertFalse(DemoBoundary().submission_status()['available'])
        self.assertEqual(self.sources,self.example.sources())


if __name__ == '__main__':unittest.main()
