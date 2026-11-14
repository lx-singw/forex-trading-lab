"""Active parent contexts, partial alternatives, completion and permanent breaches."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from forex_demo_lab.elliott_full.contracts import D
from forex_demo_lab.elliott_full.interpretations import context_state
from forex_demo_lab.elliott_full.strategy import Strategy
from test_elliott_full_policy import counts,history,append,mirrored,HOUR


def moved(node,shift=0,offset=D(0),prefix="moved"):
    return replace(node,anchors=tuple(replace(p,id=prefix+p.id,index=p.index+shift,time=p.time+shift*HOUR,
                    available=p.available+shift*HOUR,price=p.price+offset) for p in node.anchors),
                   children=tuple(moved(c,shift,offset,prefix) for c in node.children))


class ContextLifecycleTests(unittest.TestCase):
    def test_context_cache_keeps_clock_gate_and_fork_isolation(self):
        c=counts();h=history(c);s=Strategy()
        for frame in ("D1","H4"):
            s.bars[frame]=[replace(b,timeframe=frame) for b in h]
            s.counts[frame]={"interpretations":[c],"nodes":list(c.legs),"incomplete":False}
        with patch("forex_demo_lab.elliott_full.strategy.context_state",wraps=context_state) as compute:
            s._contexts(h[-1].end);self.assertEqual(2,compute.call_count)
            s._contexts(h[-1].end+HOUR);self.assertEqual(2,compute.call_count)
            s._contexts(h[-1].end+4*HOUR)
            self.assertIsNone(s.contexts["H4"]);self.assertEqual(2,compute.call_count)
            fork=s.fork();fork.counts["D1"]=dict(s.counts["D1"])
            fork._contexts(h[-1].end+HOUR);self.assertEqual(3,compute.call_count)
            self.assertIs(s.context_cache["D1"][0],s.counts["D1"])
            self.assertIsNot(s.context_cache["D1"][0],fork.context_cache["D1"][0])

    def test_new_parent_analysis_invalidates_cached_context_permanently(self):
        c=counts();h=history(c);s=Strategy()
        for frame in ("D1","H4"):
            s.bars[frame]=[replace(b,timeframe=frame) for b in h]
            s.counts[frame]={"interpretations":[c],"nodes":list(c.legs),"incomplete":False}
        s._contexts(h[-1].end);self.assertEqual(1,s.contexts["D1"])
        for breach in (True,False):
            previous=s.bars["D1"][-1]
            s.bars["D1"].append(replace(previous,start=previous.end,end=previous.end+HOUR,available=previous.end+HOUR,
                               low=c.terminal.price-D(".0001") if breach else previous.close-D(".00001")))
            s.counts["D1"]=dict(s.counts["D1"])
            s._contexts(s.bars["D1"][-1].available)
            self.assertIsNone(s.contexts["D1"])

    def test_resolved_wave_four_retires_its_matching_wave_two_prefix(self):
        later=counts("EW5");earlier=replace(later,kind="EW3",legs=later.legs[:2]);h=history(later)
        barriers=[later.legs[2]]
        self.assertIsNone(context_state([earlier],h[-1],barriers=barriers,history=h)["side"])
        incomplete=replace(later,legs=(*later.legs[:3],replace(later.legs[3],depth=1,children=())))
        self.assertIsNone(context_state([earlier,incomplete],h[-1],barriers=barriers,history=h)["side"])
        result=context_state([earlier,later],h[-1],barriers=barriers,history=h)
        self.assertEqual(1,result["side"]);self.assertEqual([later.id],result["counts"])

    def test_newer_partial_count_does_not_precede_economic_rank(self):
        c=counts();h=history(c)
        other=replace(c,legs=tuple(moved(n,1) for n in c.legs))
        other=replace(other,legs=(replace(other.legs[0],children=(),depth=1),other.legs[1]))
        result=context_state([c,other],h[-1])
        self.assertEqual(1,result["side"]);self.assertEqual([c.id],result["counts"])

    def test_invalid_opposed_count_is_removed_before_competition(self):
        c=counts();h=history(c)
        self.assertEqual(1,context_state([c,mirrored(c)],h[-1])["side"])

    def test_historical_breach_cannot_revive_after_rebound(self):
        for c in (counts(),mirrored(counts())):
            h=history(c)
            append(h,c.terminal.price-c.side*D(".0001"))
            append(h,(c.trigger+c.terminal.price)/2)
            self.assertIsNone(context_state([c],h[-1],history=h)["side"])

    def test_gap_inside_required_history_prevents_context(self):
        c=counts();h=history(c)
        for i in range(50,len(h)):
            h[i]=replace(h[i],start=h[i].start+HOUR,end=h[i].end+HOUR,available=h[i].available+HOUR)
        self.assertIsNone(context_state([c],h[-1],history=h)["side"])

    def test_small_later_pattern_is_not_parent_completion(self):
        c=counts();h=history(c)
        node=replace(moved(c.legs[0],90),children=(),depth=1)
        bar=replace(h[-1],start=node.anchors[-1].time+HOUR,end=node.anchors[-1].time+2*HOUR,available=node.available+HOUR)
        self.assertEqual(1,context_state([c],bar,barriers=[node])["side"])

    def test_anchored_resolved_completed_leg_prevents_context_but_future_does_not(self):
        c=counts();h=history(c)
        node=moved(c.legs[0],c.terminal.index-c.legs[0].anchors[0].index,c.terminal.price-c.origin)
        future=context_state([c],h[-1],barriers=[node])
        self.assertEqual(1,future["side"])
        bar=replace(h[-1],start=node.anchors[-1].time+HOUR,end=node.anchors[-1].time+2*HOUR,available=node.available+HOUR)
        result=context_state([c],bar,barriers=[node])
        self.assertIsNone(result["side"]);self.assertEqual("new_terminal_unresolved",result["stage"])

    def test_unrelated_deep_node_does_not_close_an_active_parent(self):
        c=counts();node=moved(c.legs[0],200,D(".1"))
        bar=replace(history(c)[-1],start=node.anchors[-1].time+HOUR,end=node.anchors[-1].time+2*HOUR,available=node.available+HOUR)
        self.assertEqual(1,context_state([c],bar,barriers=[node])["side"])


if __name__=="__main__":unittest.main()
