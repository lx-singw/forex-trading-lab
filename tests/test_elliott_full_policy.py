"""Declared invented counts test policy independently of pivot discovery.

These are component/integration tests, not market or full-bar-discovery evidence.
"""
import copy
import unittest
from decimal import localcontext
from dataclasses import replace
from forex_demo_lab.elliott_full.contracts import Bar, D, Quote
from forex_demo_lab.elliott_full.patterns import Pivot, Node, geometry, grammar, Parser, promote
from forex_demo_lab.elliott_full.interpretations import Interpretation, interpretations, context_state, competitive_counts
from forex_demo_lab.elliott_full.setups import Policy
from forex_demo_lab.elliott_full.execution import Ledger

HOUR=3600000


def resolved(family,values,indices,prefix="x",radius=4):
    prefix=f"{prefix}-r{radius}"
    values=[D("1.1")+(D(v)-D("1.1"))/10 for v in values]
    side=1 if D(values[1])>D(values[0]) else -1
    anchors=tuple(Pivot(f"{prefix}-{i}",i,(i+1)*HOUR,(i+radius+1)*HOUR,D(p),
                        "low" if (j%2==0)==(side==1) else "high",radius) for j,(i,p) in enumerate(zip(indices,values)))
    forms=["impulse","zigzag","impulse","zigzag","impulse"] if family=="impulse" else ["impulse","zigzag","impulse"]
    children=[]
    for a,b,child in zip(anchors,anchors[1:],forms):
        fractions=tuple(map(D,("0",".25",".15",".75",".5","1") if child=="impulse" else ("0",".5",".25","1")))
        pivots=[]
        for k,f in enumerate(fractions):
            index=a.index+(b.index-a.index)*k//(len(fractions)-1)
            pivots.append(a if k==0 else b if k==len(fractions)-1 else
                          Pivot(f"{prefix}-{a.index}-{k}",index,(index+1)*HOUR,(index+radius+1)*HOUR,a.price+(b.price-a.price)*f,"high" if k%2 else "low",radius))
        assert child in geometry([p.price for p in pivots])
        children.append(Node(child,tuple(pivots)))
    node=Node(family,anchors,tuple(children),2)
    assert family in geometry([p.price for p in anchors]) and grammar(family,children)
    return node


def counts(kind="EW3",radius=4):
    first=resolved("impulse",["1.100","1.112","1.106","1.130","1.118","1.142"],[10,20,30,40,50,60],"first",radius)
    second=resolved("zigzag",["1.142","1.130","1.137","1.121"],[60,70,80,90],"second",radius)
    # Canonical endpoint identity is shared, as it is in parser output.
    second=replace(second,anchors=(first.anchors[-1],*second.anchors[1:]))
    if kind=="EW3":
        return Interpretation((first,second),kind)
    third=resolved("impulse",["1.121","1.140","1.130","1.180","1.155","1.210"],[90,100,110,120,130,140],"third",radius)
    third=replace(third,anchors=(second.anchors[-1],*third.anchors[1:]))
    fourth=resolved("zigzag",["1.210","1.185","1.200","1.170"],[140,150,160,170],"fourth",radius)
    fourth=replace(fourth,anchors=(third.anchors[-1],*fourth.anchors[1:]))
    return Interpretation((first,second,third,fourth),kind)


def history(count,extra=8):
    end=count.terminal.index+extra
    close=(count.trigger+count.terminal.price)/2
    points={}
    def visit(node):
        points.update({p.index:p.price for p in node.anchors})
        for child in node.children:
            visit(child)
    for leg in count.legs:
        visit(leg)
    indices=sorted(points)
    result=[]
    for i in range(end+1):
        if i<indices[0]:
            value=points[indices[0]]
        elif i>indices[-1]:
            value=close
        else:
            a=max(j for j in indices if j<=i)
            b=min(j for j in indices if j>=i)
            value=points[a] if a==b else points[a]+(points[b]-points[a])*(i-a)/(b-a)
        result.append(Bar("H1",i*HOUR,(i+1)*HOUR,(i+1)*HOUR,value,value+D(".00001"),value-D(".00001"),value,f"bar-{i}"))
    return result


def append(history,close,low=None,high=None):
    i=len(history);close=D(close)
    bar=Bar("H1",i*HOUR,(i+1)*HOUR,(i+1)*HOUR,close,close+D(".00001") if high is None else D(high),
            close-D(".00001") if low is None else D(low),close,f"bar-{i}")
    history.append(bar)
    return bar


def mirrored(count):
    def mirror(n):
        anchors=tuple(replace(p,id="mirror-"+p.id,price=D("2.2")-p.price,kind="low" if p.kind=="high" else "high") for p in n.anchors)
        return replace(n,anchors=anchors,children=tuple(mirror(c) for c in n.children))
    return replace(count,legs=tuple(mirror(n) for n in count.legs))


def source_pivots(count):
    points={}
    def visit(n):
        points.update({p.index:replace(p,id=f"source-{p.index}") for p in n.anchors})
        for child in n.children:
            visit(child)
    for leg in count.legs:
        visit(leg)
    return [points[i] for i in sorted(points)]


class CountTests(unittest.TestCase):
    def test_opposed_competitive_context_abstains(self):
        c=counts();h=history(c)
        self.assertIsNone(context_state([c,mirrored(c)],h[-1])["side"])

    def test_channel_and_alternation_are_display_preferences(self):
        c=counts("EW5");h=history(c)
        changed=replace(c,legs=(c.legs[0],replace(c.legs[1],family="flat_regular"),*c.legs[2:]))
        self.assertEqual(c.economic_rank(),changed.economic_rank())
        self.assertNotEqual(c.rank(bars=h),changed.rank(bars=h))
    def test_real_parser_to_resolved_count(self):
        c=counts();parser=Parser();nodes=parser.parse(source_pivots(c))
        found,overflow=interpretations(nodes)
        self.assertFalse(parser.incomplete or overflow)
        self.assertTrue(any(x.resolved and x.kind=="EW3" and x.terminal.index==c.terminal.index for x in found))

    def test_coarse_confirmation_is_not_backdated(self):
        c=counts();points=source_pivots(c);parser=Parser();nodes=parser.parse(points)
        coarse=[replace(p,id="coarse-"+p.id,radius=8,available=p.available+4*HOUR) for leg in c.legs for p in leg.anchors]
        coarse=list({p.index:p for p in coarse}.values())
        found=promote(nodes,coarse)
        self.assertTrue(any(n.depth>=2 for n in found))
        for n in found:
            self.assertGreaterEqual(n.available,max(p.available for p in n.anchors))

    def test_appended_counts_leave_previous_snapshots_unchanged(self):
        c=counts();saved=c.record();node=replace(c.legs[-1],family="flat_running")
        competitive_counts([c,replace(c,legs=(*c.legs[:-1],node))])
        self.assertEqual(saved,c.record())
    def test_derive_both_setups(self):
        for kind in ("EW3","EW5"):
            c=counts(kind)
            found,overflow=interpretations(list(c.legs))
            self.assertFalse(overflow)
            self.assertIn(c.id,[x.id for x in found if x.kind==kind])

    def test_no_future_fifth_in_count(self):
        c=counts("EW5")
        self.assertEqual(4,len(c.legs))
        self.assertIsNone(c.ceiling)

    def test_context_pending_and_active(self):
        c=counts(); h=history(c)
        self.assertEqual("correction_confirmed",context_state([c],h[-1])["stage"])
        append(h,c.trigger+D(".001"))
        self.assertEqual("active_motive",context_state([c],h[-1])["stage"])

    def test_context_invalidated(self):
        c=counts();h=history(c)
        append(h,c.terminal.price-D(".001"))
        self.assertIsNone(context_state([c],h[-1])["side"])

    def test_unknown_parent_is_not_a_context(self):
        c=counts();h=history(c)
        derived,_=interpretations([c.legs[-1]])
        self.assertIsNone(context_state(derived,h[-1])["side"])

    def test_context_incomplete_search(self):
        c=counts();h=history(c)
        self.assertIsNone(context_state([c],h[-1],incomplete=True)["side"])

    def test_depth_one_abstains(self):
        c=counts();c=replace(c,legs=(replace(c.legs[0],children=(),depth=1),c.legs[1]))
        self.assertIsNone(context_state([c],history(c)[-1])["side"])

    def test_display_order_total_and_deterministic(self):
        a,b=counts(),counts(radius=8)
        self.assertEqual([c.id for c in competitive_counts([a,b])],[c.id for c in competitive_counts([b,a])])

    def test_budget_fails_closed(self):
        c=counts();_,overflow=interpretations(list(c.legs),budget=0)
        self.assertTrue(overflow)


class PolicyTests(unittest.TestCase):
    def test_consensus_expiry_uses_earliest_member(self):
        c=counts();h=history(c);p=Policy()
        p.update([c,counts(radius=8)],h,(1,1))
        earliest=next(i for i,b in enumerate(h) if b.available>=c.available)
        group=next(iter(p.groups.values()))
        self.assertEqual(earliest+10,group["expiry_index"])
    def test_precision_does_not_depend_on_caller(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,c.trigger+D(".0002"));signal=p.update([c],h,(1,1))[0]
        t=signal.formed+2000;quote=Quote(t,t,1,c.trigger+D(".0002"),c.trigger+D(".0003"))
        expected=Ledger();expected.on_quote(quote,signal)
        with localcontext() as context:
            context.prec=6
            actual=Ledger();actual.on_quote(quote,signal)
        self.assertEqual(expected.state(),actual.state())

    def test_saved_policy_is_not_mutable_live_state(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1));saved=p.record()
        saved["groups"].clear();saved["active"].clear()
        self.assertTrue(p.groups and p.active)

    def test_earlier_count_revisions_do_not_change(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        first=copy.deepcopy(p.revisions[0]);append(h,h[-1].close)
        p.update([c,counts(radius=8)],h,(1,1))
        self.assertEqual(first,p.revisions[0])
    def test_unavailable_count_cannot_form(self):
        c=counts();h=history(c,extra=1);p=Policy()
        self.assertEqual([],p.update([c],h,(1,1)))
        self.assertEqual("unavailable_count",p.reason)

    def test_rare_only_alternative_blocks(self):
        c=counts();c=replace(c,legs=(replace(c.legs[0],family="leading_33333"),c.legs[1]))
        p=Policy();self.assertEqual([],p.update([c],history(c),(1,1)))
        self.assertEqual("competitive_disagreement",p.reason)

    def test_changed_membership_cannot_trade_on_same_bar(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,c.trigger+D(".0001"))
        self.assertEqual([],p.update([c,counts(radius=8)],h,(1,1)))
        self.assertFalse(p.emitted)
        self.assertEqual("missed_before_confirmation",p.reason)

    def test_lost_coverage_cancels_opportunity(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        b=append(h,h[-1].close)
        h[-1]=replace(b,start=b.start+HOUR,end=b.end+HOUR,available=b.available+HOUR)
        self.assertEqual([],p.update([c],h,(1,1)))
        self.assertEqual("coverage_break",p.reason)

    def test_levels_are_frozen_without_recount(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        original=copy.deepcopy(p.active)
        append(h,h[-1].close,high=c.trigger)
        p.update([c],h,(1,1))
        self.assertEqual(original,p.active)
    def test_short_policy_to_fill(self):
        for kind in ("EW3","EW5"):
            c=mirrored(counts(kind));h=history(c);p=Policy();p.update([c],h,(-1,-1))
            append(h,c.trigger-D(".0002"))
            signal=p.update([c],h,(-1,-1))[0]
            l=Ledger();t=signal.formed+2000
            self.assertEqual("entered",l.on_quote(Quote(t,t,1,c.trigger-D(".0003"),c.trigger-D(".0002")),signal))

    def test_raw_structural_boundary_checked_at_fill(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,c.trigger+D(".0002"));signal=p.update([c],h,(1,1))[0]
        t=signal.formed+2000;l=Ledger()
        # Price above buffered stop but below original structural invalidation.
        price=(signal.stop+signal.invalidation)/2
        self.assertEqual("invalidated",l.on_quote(Quote(t,t,1,price,price+D(".0001")),signal))

    def test_duplicates_do_not_reform(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,h[-1].close);p.update([c,c],h,(1,1))
        self.assertEqual(1,len(p.revisions))

    def test_expiry_at_tenth_bar_and_not_eleventh(self):
        for delta,expected in ((10,1),(11,0)):
            c=counts();h=history(c,extra=4);p=Policy();p.update([c],h,(1,1))
            for _ in range(delta-1):
                append(h,h[-1].close);p.update([c],h,(1,1))
            append(h,c.trigger+D(".0002"))
            self.assertEqual(expected,len(p.update([c],h,(1,1))))

    def test_late_warmup_does_not_renew_old_pattern(self):
        c=counts();h=history(c,extra=30);p=Policy()
        self.assertEqual([],p.update([c],h,(1,1)))
        self.assertEqual("consumed_or_expired",p.reason)
    def test_ew3_and_ew5_to_ledger(self):
        for kind in ("EW3","EW5"):
            c=counts(kind);h=history(c);p=Policy()
            self.assertEqual([],p.update([c],h,(1,1)))
            append(h,c.trigger+D(".0002"))
            signals=p.update([c],h,(1,1))
            self.assertEqual(1,len(signals))
            signal=signals[0];l=Ledger()
            quote=Quote(signal.formed+2000,signal.formed+2000,1,c.trigger+D(".0002"),c.trigger+D(".0003"))
            self.assertEqual("entered",l.on_quote(quote,signal))
            self.assertEqual(kind,signal.kind)
            checkpoint=l.checkpoint()
            restored=Ledger.restore(checkpoint)
            self.assertEqual(l.state(),restored.state())
            # Stop gap really uses observed executable quote, not original stop.
            stop=l.position["stop"]-D(".01")
            l.on_quote(Quote(quote.time+1000,quote.time+1000,2,stop,stop+D(".0001")))
            self.assertIsNone(l.position)
            self.assertLess(D(l.trades[-1]["net"]),-D(l.trades[-1]["estimated_risk"]))

    def test_recount_does_not_refresh_expiry(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        expiry=next(iter(p.groups.values()))["expiry_index"]
        append(h,h[-1].close)
        alternate=counts(radius=8)
        p.update([c,alternate],h,(1,1))
        self.assertEqual(expiry,next(iter(p.groups.values()))["expiry_index"])
        self.assertEqual(2,len(p.revisions))

    def test_context_loss_cancels(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,h[-1].close)
        self.assertEqual([],p.update([c],h,(1,None)))
        self.assertFalse(p.active)

    def test_invalid_during_context_loss_cannot_revive(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        boundary=D(next(iter(p.active.values()))["boundary"])
        append(h,h[-1].close,low=boundary-D(".001"))
        p.update([c],h,(1,None))
        append(h,h[-1].close)
        self.assertEqual([],p.update([c],h,(1,1)))
        self.assertFalse(p.active)

    def test_breakout_and_invalidation_same_bar(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        boundary=D(next(iter(p.active.values()))["boundary"])
        append(h,c.trigger+D(".001"),low=boundary)
        self.assertEqual([],p.update([c],h,(1,1)))
        self.assertTrue(next(iter(p.groups.values()))["consumed"])

    def test_missed_earlier_cross_not_chased(self):
        c=counts();h=history(c);h[c.terminal.index+2]=replace(h[c.terminal.index+2],close=c.trigger+D(".001"),high=c.trigger+D(".002"))
        p=Policy();self.assertEqual([],p.update([c],h,(1,1)))
        self.assertEqual("missed_before_confirmation",p.reason)

    def test_alias_one_attempt(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,c.trigger+D(".001"));self.assertEqual(1,len(p.update([c],h,(1,1))))
        append(h,(c.trigger+c.terminal.price)/2)
        self.assertEqual([],p.update([counts(radius=8)],h,(1,1)))
        self.assertEqual(1,len(p.emitted))

    def test_unfinished_search_cancels(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        append(h,c.trigger+D(".001"))
        self.assertEqual([],p.update([c],h,(1,1),incomplete=True))
        self.assertFalse(p.active)

    def test_formation_cannot_trigger(self):
        c=counts();h=history(c);h[-1]=replace(h[-1],close=c.trigger+D(".001"),high=c.trigger+D(".002"))
        p=Policy();self.assertEqual([],p.update([c],h,(1,1)))

    def test_expiry(self):
        c=counts();h=history(c);p=Policy();p.update([c],h,(1,1))
        for _ in range(11):
            append(h,h[-1].close);p.update([c],h,(1,1))
        append(h,c.trigger+D(".001"))
        self.assertEqual([],p.update([c],h,(1,1)))


if __name__=="__main__":
    unittest.main()
