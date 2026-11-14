"""Finite-profile geometry/child/location examples, independent of return outcomes."""
import unittest
from dataclasses import replace
from forex_demo_lab.elliott_full.contracts import D
from forex_demo_lab.elliott_full.patterns import Pivot,Node,CATALOGUE,grammar,Parser
from forex_demo_lab.elliott_full.rulebook import diagnose,RULEBOOK

CASES={
    "impulse":([10,12,11,15,13,16],"MCMCM","impulse","1"),
    "truncated_impulse":([10,12,11,16,13,15],"MCMCM","impulse","5"),
    "leading_53535":([10,14,12,15,"13.4","15.6"],"MCMCM","impulse","1"),
    "leading_33333":([10,14,12,15,"13.4","15.6"],"CCCCC","zigzag","A"),
    "ending_diagonal":([10,14,12,15,"13.4","15.6"],"CCCCC","impulse","5"),
    "expanding_diagonal":([10,13,11,16,12,20],"CCCCC","zigzag","C"),
    "zigzag":([10,12,11,13],"MCM","impulse","2"),
    "flat_regular":([10,12,"10.1","12.2"],"CCM","impulse","2"),
    "flat_expanded":([10,12,9,13],"CCM","impulse","4"),
    "flat_running":([10,12,9,11],"CCM","impulse","4"),
    "triangle_contracting":([10,15,11,14,12,13],"CCCCC","impulse","4"),
    "triangle_barrier":([10,15,11,14,11,13],"CCCCC","zigzag","B"),
    "triangle_running":([10,15,9,14,10,12],"CCCCC","impulse","4"),
    "triangle_expanding":([10,13,11,15,9,17],"CCCCC","zigzag","B"),
    "double_zigzag":([10,13,12,16],"CCC","impulse","2"),
    "triple_zigzag":([10,13,12,16,15,19],"CCCCC","impulse","4"),
    "double_three":([10,13,12,16],"FCF","impulse","2"),
    "triple_three":([10,13,12,16,15,19],"FCFCF","impulse","4"),
}


def pivots(values,indices=None):
    values=list(map(D,values))
    indices=indices or [30*i for i in range(len(values))]
    side=1 if values[1]>values[0] else -1
    return tuple(Pivot(f"p-{i}-{v}",i,i*1000,(i+1)*1000,v,"low" if (j%2==0)==(side==1) else "high",2)
                 for j,(i,v) in enumerate(zip(indices,values)))


def example(family,mirror=False):
    values,form,parent,position=CASES[family]
    values=[D(40)-D(v) for v in values] if mirror else values
    anchors=pivots(values)
    children=[]
    for a,b,kind in zip(anchors,anchors[1:],form):
        fractions=list(map(D,("0",".25",".15",".75",".5","1") if kind=="M" else
                            ("0",".9",".045","1") if kind=="F" else ("0",".5",".25","1")))
        points=[a.price+(b.price-a.price)*f for f in fractions]
        indices=[a.index+(b.index-a.index)*i//(len(points)-1) for i in range(len(points))]
        children.append(Node("impulse" if kind=="M" else "flat_regular" if kind=="F" else "zigzag",pivots(points,indices)))
    return Node(family,anchors,tuple(children),2),parent,position


class RulebookTests(unittest.TestCase):
    def test_pivot_cap_reports_unavailable_without_missing_diagnostics(self):
        p=Parser();nodes=p.parse(pivots([10+i%2 for i in range(257)]))
        self.assertFalse(nodes)
        self.assertTrue(p.incomplete)
        self.assertEqual(["pivot_cap"],p.rejections[0]["failed"])

    def test_all_declared_families_have_positive_and_mirrored_examples(self):
        self.assertEqual(set(CATALOGUE),set(CASES))
        for family in CASES:
            for mirror in (False,True):
                with self.subTest(family=family,mirror=mirror):
                    node,parent,position=example(family,mirror)
                    report=diagnose(node,parent,position)
                    self.assertEqual([],report["failed"])
                    self.assertEqual("valid_at_resolution",report["state"])

    def test_all_families_reject_nonmatching_child_endpoints(self):
        for family in CASES:
            with self.subTest(family=family):
                n,p,pos=example(family)
                child=n.children[0]
                child=replace(child,anchors=(replace(child.anchors[0],price=child.anchors[0].price+D(".01")),*child.anchors[1:]))
                report=diagnose(replace(n,children=(child,*n.children[1:])),p,pos)
                self.assertIn("child_endpoints",report["failed"])

    def test_flat_requires_335_not_333(self):
        n,_,_=example("flat_regular")
        self.assertTrue(grammar(n.family,n.children))
        bad=replace(n.children[-1],family="zigzag")
        self.assertFalse(grammar(n.family,(*n.children[:-1],bad)))

    def test_triangle_cannot_be_whole_wave_two(self):
        for family in (f for f in CASES if f.startswith("triangle")):
            n,_,_=example(family)
            self.assertIn("parent_location",diagnose(n,"impulse","2")["failed"])
            self.assertNotIn("parent_location",diagnose(n,"double_three","Y")["failed"])

    def test_diagonals_have_distinct_locations(self):
        for family in ("leading_53535","leading_33333","ending_diagonal","expanding_diagonal"):
            n,_,_=example(family)
            self.assertIn("parent_location",diagnose(n,"impulse","3")["failed"])

    def test_triangle_not_first_connector_of_triple(self):
        n,_,_=example("triangle_contracting")
        self.assertIn("parent_location",diagnose(n,"triple_three","X")["failed"])
        self.assertNotIn("parent_location",diagnose(n,"triple_three","X2")["failed"])

    def test_unknown_location_and_geometry_only_are_explicit(self):
        n,_,_=example("ending_diagonal")
        self.assertEqual("unknown_location",diagnose(n)["state"])
        self.assertEqual("insufficient_resolution",diagnose(replace(example("impulse")[0],children=(),depth=1))["state"])

    def test_depth_claim_without_evidence_rejected(self):
        n,_,_=example("impulse")
        self.assertIn("resolution",diagnose(replace(n,children=()))["failed"])

    def test_unknown_family(self):
        n,_,_=example("impulse")
        self.assertEqual("unsupported",diagnose(replace(n,family="unrecognised"))["state"])

    def test_observation_only_does_not_become_actionable(self):
        for family in RULEBOOK["observation_only"]:
            self.assertFalse(example(family)[0].actionable)

    def test_nonconverging_diagonal_rejected(self):
        n,p,pos=example("ending_diagonal")
        # Unequal source durations turn otherwise plausible price ratios into a
        # widening envelope. Count geometry must use source bar indices.
        a=list(n.anchors)
        a[4]=replace(a[4],index=149,time=149000,available=150000)
        a[5]=replace(a[5],index=150,time=150000,available=151000)
        self.assertIn("boundary_lines",diagnose(replace(n,anchors=tuple(a)),p,pos)["failed"])


if __name__=="__main__":
    unittest.main()
