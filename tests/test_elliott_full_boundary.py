"""Declared endpoint liquidation: costs, no future prices, restart and atomicity."""
import copy
from fractions import Fraction
import unittest
from forex_demo_lab.elliott_full.contracts import D,Quote,validate_bundle,digest
from forex_demo_lab.elliott_full.execution import Ledger,Setup
from forex_demo_lab.elliott_full.engine import Engine
from forex_demo_lab.elliott_full.replay import evaluate


def quote(t=1000,seq=1,bid="1.10000",ask="1.10010",source=None):
    return Quote(t,t if source is None else source,seq,D(bid),D(ask))


def signal(side=1):
    return Setup("boundary-test",side,"EW3",0,60000,D("1.10000"),D("1.09900") if side==1 else D("1.10100"))


class BoundaryTests(unittest.TestCase):
    def test_side_and_profile_cash_independently_reconcile(self):
        for side in (1,-1):
            for profile in ("base","adverse"):
                with self.subTest(side=side,profile=profile):
                    l=Ledger(profile);first=quote(2000)
                    self.assertEqual("entered",l.on_quote(first,signal(side)))
                    endpoint=quote(3000,2,"1.10020","1.10030")
                    l.on_quote(endpoint);position=copy.deepcopy(l.position)
                    expected_price=(max(endpoint.ask,endpoint.bid+D(".00012")) if profile=="adverse" else endpoint.ask) if side==-1 else endpoint.bid
                    fill=Fraction(expected_price)-side*Fraction(l.slip)
                    gross=side*(fill-Fraction(position["entry"]))*100000*Fraction(position["lots"])
                    net=gross-Fraction(l.fee)*Fraction(position["lots"])
                    l.finish(endpoint)
                    self.assertEqual(net,Fraction(l.trades[0]["net"]))
                    self.assertEqual(Fraction(10000)+net,Fraction(l.cash))
                    self.assertEqual("boundary",l.trades[0]["reason"])
                    self.assertTrue(l.finished)
                    self.assertIsNone(l.position)

    def test_missing_endpoint_rejected_even_flat(self):
        with self.assertRaises(ValueError): Ledger().finish(quote())

    def test_stale_tail_cannot_use_earlier_quote(self):
        l=Ledger();l.on_quote(quote(),signal());tail=quote(10000,2,source=1000)
        l.on_quote(tail);before=l.checkpoint()
        with self.assertRaises(ValueError): l.finish(tail)
        with self.assertRaises(ValueError): l.finish(quote())
        self.assertEqual(before,l.checkpoint())

    def test_repeated_source_tail_not_executable(self):
        l=Ledger();l.on_quote(quote(),signal());tail=quote(2000,2,source=1000)
        l.on_quote(tail)
        with self.assertRaises(ValueError): l.finish(tail)

    def test_closed_session_tail_unavailable(self):
        l=Ledger();l.on_quote(quote(),signal());tail=Quote(2000,2000,2,D("1.1"),D("1.1001"),False)
        l.on_quote(tail)
        with self.assertRaises(ValueError): l.finish(tail)

    def test_finish_idempotent_and_checkpoint_restores(self):
        l=Ledger();end=quote();l.on_quote(end,signal());l.finish(end);before=l.checkpoint()
        self.assertEqual("duplicate_finish",l.finish(end))
        self.assertEqual(before,l.checkpoint())
        self.assertEqual(l.state(),Ledger.restore(before).state())
        with self.assertRaises(ValueError): l.on_quote(quote(2000,2))

    def test_rehashed_finish_forgery_rejected(self):
        l=Ledger();end=quote();l.on_quote(end,signal());l.finish(end)
        checkpoint=l.checkpoint();checkpoint["payload"]["finish_quote"]["bid"]="1.12"
        checkpoint["digest"]=digest(checkpoint["payload"])
        with self.assertRaises(ValueError): Ledger.restore(checkpoint)

    def test_nonpositive_boundary_fill_rejects_atomically(self):
        l=Ledger();end=quote(bid=".000011",ask=".000021")
        s=Setup("tiny-price",1,"EW3",0,60000,D(".00002"),D(".00001"))
        self.assertEqual("entered",l.on_quote(end,s));before=l.checkpoint()
        with self.assertRaises(ValueError): l.finish(end)
        self.assertEqual(before,l.checkpoint())

    def test_wide_entry_filter_does_not_block_boundary_exit(self):
        l=Ledger();l.on_quote(quote(),signal());end=quote(2000,2,"1.1002","1.12")
        l.on_quote(end);l.finish(end)
        self.assertEqual("boundary",l.trades[0]["reason"])

    def test_financing_not_charged_again_at_finish(self):
        l=Ledger();l.on_quote(quote(),signal());end=quote(86401000,2)
        l.on_quote(end);charges=[e for e in l.events if e["kind"]=="financing"]
        l.finish(end)
        self.assertEqual(charges,[e for e in l.events if e["kind"]=="financing"])
        self.assertEqual(D(10000)+D(l.trades[0]["net"]),l.cash)

    def test_stop_precedes_boundary_without_second_exit(self):
        l=Ledger();l.on_quote(quote(),signal());end=quote(2000,2,"1.08","1.0801")
        l.on_quote(end);l.finish(end)
        self.assertEqual(1,len(l.trades))
        self.assertEqual("stop",l.trades[0]["reason"])

    def bundle(self):
        return {"kind":"invented_ew_full_v1","symbol":"EURUSD","bars":[],"quotes":[quote().record()],
                "boundary":{"end_time":2000,"quote_sequence":1,"quote_source":1000,"quote_time":1000}}

    def test_public_declared_boundary_and_engine_restart(self):
        result=evaluate(self.bundle())
        self.assertTrue(result["ledger"]["finished"])
        engine=Engine.restore(result["checkpoint"])
        self.assertTrue(engine.ledger.finished)
        with self.assertRaises(ValueError): engine.step({"kind":"quote","value":quote(3000,2).record()})

    def test_boundary_rejects_later_or_mismatched_quote(self):
        for field,value in (("end_time",1000),("quote_sequence",2),("quote_source",999),("quote_time",999)):
            bundle=self.bundle();bundle["boundary"][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): validate_bundle(bundle)

    def test_boundary_cannot_borrow_later_bar(self):
        bundle=self.bundle();bundle["bars"]=[{"timeframe":"H1","start":0,"end":3600000,"available":3600000,
                                             "open":"1.1","high":"1.1","low":"1.1","close":"1.1","lineage":"future"}]
        with self.assertRaises(ValueError): validate_bundle(bundle)


if __name__=="__main__":
    unittest.main()
