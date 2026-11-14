"""Independent geometry, risk, chronology and restart checks for new research path."""
import copy
import json
import tempfile
import gzip
import unittest
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from forex_demo_lab.elliott_full.contracts import Bar, Quote, D, digest, validate_bundle
from forex_demo_lab.elliott_full.patterns import geometry, confirmed, Parser, Pivot, Node, grammar
from forex_demo_lab.elliott_full.execution import Ledger, Setup
from forex_demo_lab.elliott_full.strategy import Strategy
from forex_demo_lab.elliott_full.replay import evaluate, write_report
from forex_demo_lab.elliott_full.bars import aggregate
from forex_demo_lab.elliott_full.counts import rank
from forex_demo_lab.elliott_full.admission import DemoBoundary, study_status
from forex_demo_lab.elliott_full.engine import Engine


def q(time=1000, bid="1.10000", ask="1.10010", seq=1, source=None, opened=True):
    return Quote(time,time if source is None else source,seq,D(bid),D(ask),opened)


def setup(key="a", side=1):
    return Setup(key,side,"EW3",0,60000,D("1.1000"),D("1.0990") if side==1 else D("1.1010"))


def bars(values, frame="H1"):
    return [Bar(frame,i*3600000,(i+1)*3600000,(i+1)*3600000,D(str(v)),D(str(v))+D(".1"),D(str(v))-D(".1"),D(str(v)),str(i)) for i,v in enumerate(values)]


class GeometryTests(unittest.TestCase):
    def test_impulse(self):
        self.assertIn("impulse",geometry([10,12,11,15,13,16]))

    def test_wave2_origin(self):
        self.assertNotIn("impulse",geometry([10,12,9,15,13,16]))

    def test_overlap(self):
        self.assertNotIn("impulse",geometry([10,12,11,15,12,16]))

    def test_shortest_third(self):
        self.assertNotIn("impulse",geometry([10,14,12,15,"14.5",20]))

    def test_truncation(self):
        self.assertIn("truncated_impulse",geometry([10,12,11,16,13,15]))

    def test_mirrored_impulse(self):
        self.assertIn("impulse",geometry([20,18,19,15,17,14]))

    def test_zigzag(self):
        self.assertIn("zigzag",geometry([10,12,11,13]))

    def test_flats(self):
        for values, name in [([10,12,"10.1","12.2"],"flat_regular"),([10,12,9,13],"flat_expanded"),([10,12,9,11],"flat_running")]:
            self.assertIn(name,geometry(values))

    def test_triangle(self):
        self.assertIn("triangle_contracting",geometry([10,15,11,14,12,13]))

    def test_bad_geometry(self):
        self.assertEqual([],geometry([1,2,2,3]))

    def test_grammar(self):
        # Geometry alone cannot prove an impulse's third is an impulse.
        p = Pivot("a",0,0,1,D(1),"low",2)
        ns = [Node(f,(p,)) for f in ["impulse","zigzag","leading_53535","zigzag","impulse"]]
        self.assertFalse(grammar("impulse",ns))


class CausalTests(unittest.TestCase):
    def test_full_engine_prefix_restart(self):
        engine=Engine()
        for bar in bars([1,2,4,2,1,2,3]):
            event={"kind":"bar","value":bar.record()}
            engine.step(event)
            restored=Engine.restore(json.loads(json.dumps(engine.checkpoint())))
            self.assertEqual(engine.state(),restored.state())
        checkpoint=engine.checkpoint()
        checkpoint["payload"]["state"]["contexts"]["D1"]=1
        checkpoint["digest"]=digest(checkpoint["payload"])
        with self.assertRaises(ValueError): Engine.restore(checkpoint)

    def test_engine_atomic_and_duplicate(self):
        engine=Engine(); event={"kind":"quote","value":q().record()}
        engine.step(event); before=engine.checkpoint()
        self.assertEqual("duplicate",engine.step(event))
        self.assertEqual(before,engine.checkpoint())
        with self.assertRaises(ValueError): engine.step({"kind":"quote","value":q(500,seq=2).record()})
        self.assertEqual(before,engine.checkpoint())

    def test_nested_parse(self):
        values=[10,12,11,17,14,20,17,19,15,17,16,22,19,25]
        ps=[Pivot(str(i),i,i,i+1,D(v),"low" if i%2==0 else "high",2) for i,v in enumerate(values)]
        parser=Parser(budget=50000)
        ns=parser.parse(ps)
        found=[n for n in ns if n.family=="zigzag" and n.depth==2 and n.anchors[0]==ps[0] and n.anchors[-1]==ps[-1]]
        self.assertTrue(found)
        self.assertTrue(found[0].actionable)
        self.assertEqual(found,sorted(found,key=rank))

    def test_confirmation_delay(self):
        history=bars([1,2,4,2,1])
        self.assertEqual([],confirmed(history[:-1],2)[0])
        journal,_=confirmed(history,2)
        self.assertEqual(1,len(journal))
        self.assertEqual(history[-1].available,journal[0].available)
        self.assertEqual(history[2].end,journal[0].time)

    def test_ties(self):
        self.assertEqual([],confirmed(bars([1,2,4,4,1]),2)[0])

    def test_suffix(self):
        history=bars([1,2,4,2,1,2,3,2,1])
        a=confirmed(history[:5],2)[0]
        b=confirmed(history,2)[0]
        self.assertEqual(a,[p for p in b if p.available<=history[4].available])

    def test_budget(self):
        ps=[Pivot(str(i),i,i,i+1,D(str(10+i%2)),"low" if i%2==0 else "high",2) for i in range(20)]
        parser=Parser(budget=0)
        parser.parse(ps)
        self.assertTrue(parser.incomplete)

    def test_insufficient_resolution(self):
        ps=[Pivot(str(i),i,i,i+1,D(str(v)),"low" if i%2==0 else "high",2) for i,v in enumerate([10,12,11,15,13,16])]
        ns=Parser().parse(ps)
        self.assertTrue(ns)
        self.assertFalse(any(n.actionable for n in ns))

    def test_warmup(self):
        s=Strategy()
        for b in bars([1,2,4,2,1,2,3]):
            self.assertEqual([],s.on_bar(b))
        self.assertEqual("warmup",s.snapshots[-1]["reason"])

    def test_bar_duplicate(self):
        s=Strategy(); b=bars([1])[0]
        s.on_bar(b); before=copy.deepcopy(s.snapshots)
        self.assertEqual([],s.on_bar(b))
        self.assertEqual(before,s.snapshots)
        with self.assertRaises(ValueError): s.on_bar(replace(b,close=D("1.01")))


class LedgerTests(unittest.TestCase):
    def test_risk_fraction_independent(self):
        l=Ledger()
        self.assertEqual("entered",l.on_quote(q(),setup()))
        p=l.position
        expected=(Fraction(str(p["entry"]-p["stop"]+l.slip))*100000+7)*Fraction(str(p["lots"]))
        self.assertEqual(expected,Fraction(str(p["risk"])))
        self.assertLessEqual(expected,Fraction(25))

    def test_gap_exceeds_estimate(self):
        l=Ledger(); l.on_quote(q(),setup())
        risk=l.position["risk"]
        l.on_quote(q(2000,"1.08","1.0801",2))
        self.assertIsNone(l.position)
        self.assertGreater(-D(l.trades[-1]["net"]),risk)
        self.assertTrue(l.paused)

    def test_short(self):
        l=Ledger(); self.assertEqual("entered",l.on_quote(q(),setup(side=-1)))
        l.on_quote(q(2000,"1.12","1.1201",2))
        self.assertLess(D(l.trades[-1]["net"]),0)

    def test_minimum_lot(self):
        l=Ledger(); l.cash=l.mark=l.anchor=D(20)
        self.assertEqual("minimum_volume",l.on_quote(q(),setup()))

    def test_one_position(self):
        l=Ledger(); l.on_quote(q(),setup())
        self.assertEqual("position_limit",l.on_quote(q(2000,seq=2),setup("b")))

    def test_no_reentry_on_exit(self):
        l=Ledger(); l.on_quote(q(),setup())
        self.assertEqual("position_limit",l.on_quote(q(2000,"1.08","1.0801",2),setup("b")))
        self.assertIsNone(l.position)

    def test_loss_pause_latched(self):
        l=Ledger(); l.on_quote(q(),setup()); l.on_quote(q(2000,"1.08","1.0801",2))
        self.assertEqual("daily_pause",l.on_quote(q(3000,seq=3),setup("b")))

    def test_duplicate(self):
        l=Ledger(); l.on_quote(q(),setup()); before=l.state()
        self.assertEqual("duplicate",l.on_quote(q(),setup()))
        self.assertEqual(before,l.state())
        with self.assertRaises(ValueError): l.on_quote(q(bid="1.09"),setup())
        self.assertEqual(before,l.state())

    def test_wide_exit_not_filtered(self):
        l=Ledger(); l.on_quote(q(),setup())
        l.on_quote(q(2000,"1.08","1.09",2))
        self.assertIsNone(l.position)

    def test_stale_no_exit(self):
        l=Ledger(); l.on_quote(q(),setup())
        self.assertEqual("unavailable_quote",l.on_quote(q(10000,"1.08","1.0801",2,source=1000)))
        self.assertIsNotNone(l.position)

    def test_restart_all_prefixes(self):
        l=Ledger()
        for quote,signal in [(q(),setup()),(q(2000,seq=2),None),(q(3000,"1.08","1.0801",3),None)]:
            l.on_quote(quote,signal)
            r=Ledger.restore(json.loads(json.dumps(l.checkpoint())))
            self.assertEqual(l.state(),r.state())

    def test_rehashed_forgery_rejected(self):
        l=Ledger(); l.on_quote(q(),setup()); cp=l.checkpoint()
        cp["payload"]["state"]["cash"]="999999"
        cp["digest"]=digest(cp["payload"])
        with self.assertRaises(ValueError): Ledger.restore(cp)

    def test_latency_and_spread(self):
        l=Ledger()
        self.assertEqual("signal_timing",l.on_quote(q(100),setup()))
        self.assertEqual("entry_spread",l.on_quote(q(2000,"1.1","1.101",2),setup()))
        self.assertFalse(l.used)

    def test_invalid_exit_atomic(self):
        l=Ledger(); l.on_quote(q(),setup()); before=l.checkpoint()
        with self.assertRaises(ValueError): l.on_quote(q(2000,".000001",".000002",2))
        self.assertEqual(before,l.checkpoint())

    def test_target_no_favorable_overshoot(self):
        l=Ledger(); l.on_quote(q(),setup()); target=l.position["target"]
        l.on_quote(q(2000,"1.2","1.2001",2))
        self.assertEqual(target,D(l.trades[-1]["exit"]))

    def test_financing_and_missing_day_reference(self):
        l=Ledger(); l.on_quote(q(),setup())
        l.on_quote(q(86401000,seq=2))
        self.assertTrue(l.paused)
        self.assertGreater(l.position["financing"],0)


class ContractReportTests(unittest.TestCase):
    def test_no_market_cells_fabricated(self):
        report=study_status()
        self.assertEqual(16,len(report["cells"]))
        self.assertTrue(all(c["returns"] is None for c in report["cells"]))

    def test_demo_boundary(self):
        for mode in (1,2,True,"DemoServer",None):
            boundary=DemoBoundary()
            with self.assertRaises(ValueError): boundary.check_actual_mode(mode,True)
            self.assertTrue(boundary.halted)
        boundary=DemoBoundary()
        boundary.check_actual_mode(0,True)
        self.assertFalse(boundary.submission_status()["available"])
        boundary.record_ambiguous_outcome()
        with self.assertRaises(ValueError): boundary.request_retry()
        self.assertTrue(boundary.pending)

    def test_sampled_aggregation_and_gap(self):
        quotes=[q(t,seq=i) for i,t in enumerate(range(0,3600000,2000))]
        bar=aggregate(quotes,"H1",0,3600000)
        self.assertEqual(D("1.10005"),bar.close)
        with self.assertRaises(ValueError): aggregate(quotes[:500]+quotes[502:],"H1",0,3600000)
        with self.assertRaises(ValueError): aggregate(quotes,"H1",0,3599999)

    def test_pipeline_suffix_invariance(self):
        a=self.bundle()
        a["bars"]=[b.record() for b in bars([1,2,4,2,1])]
        b=copy.deepcopy(a)
        b["bars"]=[x.record() for x in bars([1,2,4,2,1,2,3,2,1])]
        ra,rb=evaluate(a),evaluate(b)
        self.assertEqual(ra["snapshots"],rb["snapshots"][:len(ra["snapshots"])])

    def bundle(self):
        return {"kind":"invented_ew_full_v1","symbol":"EURUSD","bars":[],"quotes":[q().record()]}

    def test_actual_input_rejected(self):
        b=self.bundle();b["kind"]="market"
        with self.assertRaises(ValueError): validate_bundle(b)

    def test_bool_and_nonfinite(self):
        for value in (True,"NaN","Infinity"):
            with self.assertRaises(ValueError): D(value)

    def test_availability(self):
        with self.assertRaises(ValueError): replace(bars([1])[0],available=0)

    def test_report_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"run"
            result=write_report(self.bundle(),target)
            self.assertEqual("UNAVAILABLE",result["market_validation"])
            self.assertFalse(result["orders_available"])
            with gzip.open(target/"checkpoint.json.gz","rt",encoding="utf-8") as stream:
                checkpoint=json.load(stream)
            self.assertEqual(result["checkpoint"]["digest"],checkpoint["digest"])
            self.assertEqual(result["ledger"],Engine.restore(checkpoint).ledger.state())
            with self.assertRaises(FileExistsError): write_report(self.bundle(),target)
            self.assertIn("available<=s.time",(target/"replay.html").read_text())


if __name__ == "__main__":
    unittest.main()
