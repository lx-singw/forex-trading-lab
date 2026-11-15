"""Candle-derived nested grammar, confirmation timing and finite-search evidence."""
from dataclasses import replace
from fractions import Fraction as F
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab.elliott_full.contracts import Bar, D, digest
from forex_demo_lab.elliott_full.patterns import Parser, CATALOGUE, OBSERVATION_ONLY, confirmed, promote
from forex_demo_lab.elliott_full.incremental import ConfirmedPivots
from forex_demo_lab.elliott_full.rulebook import diagnose
from forex_demo_lab.elliott_full.setups import Policy

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/"scripts/elliott-pattern-matrix-153.py"


def module():
    spec = importlib.util.spec_from_file_location("matrix153_examples", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class PatternMatrix153Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(os.environ.get("ELLIOTT_PATTERN_EVIDENCE_DIR", str(Path(cls.temp.name)/"matrix")))
        done = subprocess.run([sys.executable,str(SCRIPT),str(cls.output)],capture_output=True,text=True)
        if done.returncode:raise AssertionError(done.stderr)
        cls.cli_status = json.loads(done.stdout)
        cls.report = json.loads((cls.output/"matrix.json").read_text())
        cls.example = module()
        cls.records = cls.report["records"]
        cls.generated = {}
        for record in cls.records:
            case=record["case"]
            raw=json.loads((cls.output/(case["id"]+".bars.json")).read_text())
            bars=[Bar(**b) for b in raw["bars"]]
            target,parent,position,_=cls.example.candle_fixture(case)
            journal,chain=confirmed(bars,2)
            parser=Parser();nodes=parser.parse(chain)
            cls.generated[case["id"]]=(target,parent,position,bars,journal,chain,parser,nodes)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all18_families_both_directions_and_ten_extensions_are_retained(self):
        self.assertEqual(46,len(self.records))
        base=[r for r in self.records if not r['case']['extensions']]
        self.assertEqual({(f,s) for f in CATALOGUE for s in (1,-1)}, {(r['case']['family'],r['case']['side']) for r in base})
        self.assertEqual({'RECOGNIZED':46,'SEARCH_INCOMPLETE':0,'NOT_RECOGNIZED':0},self.cli_status['statuses'])
        self.assertFalse(self.report['orders_available']);self.assertIsNone(self.report['market_returns'])
        for record in self.records:
            self.assertEqual((4096,128),(record['parser']['budget'],record['parser']['cap']))
            self.assertFalse(record['parser']['incomplete'])
            self.assertEqual(1,record['exact_candidates'])
            self.assertEqual('valid_at_resolution',record['diagnostics_at_declared_location'][0]['state'])

    def test_recursive_target_prices_have_independent_candle_and_pivot_evidence(self):
        checks=[]
        for record in self.records:
            case=record['case'];target,parent,pos,bars,journal,chain,parser,nodes=self.generated[case['id']]
            self.assertEqual(digest([b.record() for b in bars]),record['input_sha256'])
            by_index={p.index:p for p in journal}
            def verify(node):
                for pivot in node.anchors:
                    self.assertIn(pivot.index,by_index)
                    point=by_index[pivot.index]
                    self.assertEqual(F(pivot.price),F(bars[pivot.index].close))
                    self.assertEqual(F(pivot.price),F(point.price))
                    self.assertEqual(bars[pivot.index+2].available,point.available)
                    self.assertEqual(bars[pivot.index].end,point.time)
                    neighbors=bars[pivot.index-2:pivot.index]+bars[pivot.index+1:pivot.index+3]
                    self.assertTrue(all(F(point.price)>F(b.high) if point.kind=='high' else F(point.price)<F(b.low) for b in neighbors))
                for child in node.children:verify(child)
            verify(target)
            exact=self.example.matching(nodes,target)
            self.assertEqual(1,len(exact));self.assertEqual(case['side'],exact[0].side)
            self.assertEqual(record['declared_signature'],self.example.signature(exact[0]))
            checks.append({'case':case['id'],'recursive_OHLC_and_strict_confirmed_pivots':True})
        self.write('candle-audits.json',{'cases':checks})

    def test_no_nested_label_before_confirmation_and_no_coarse_confirmation_borrow(self):
        checks=[]
        for record in self.records:
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            last=target.anchors[-1].index
            self.assertFalse(self.example.matching(Parser().parse(confirmed(bars[:last+2],2)[1]),target))
            exact=self.example.matching(Parser().parse(confirmed(bars[:last+3],2)[1]),target)
            self.assertEqual(1,len(exact));self.assertEqual(bars[last+2].available,exact[0].available)
            for radius in (4,8):
                early=promote(nodes,confirmed(bars[:last+radius],radius)[1])
                self.assertFalse(self.example.matching(early,target))
                at=promote(nodes,confirmed(bars[:last+radius+1],radius)[1])
                selected=self.example.matching(at,target)
                self.assertEqual(1,len(selected));self.assertEqual(bars[last+radius].available,selected[0].available)
            checks.append({'case':record['case']['id'],'fine_confirmation_delayed':True,'r4_r8_confirmation_delayed':True})
        self.write('confirmation-audits.json',{'cases':checks})

    def test_future_candles_do_not_rewrite_published_journal_or_existing_nodes(self):
        for record in self.records:
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            cut=target.anchors[-1].index+3
            prefix=bars[:cut];stream=ConfirmedPivots.bootstrap(prefix,2)
            known=list(stream.journal);existing_nodes=Parser().parse(stream.chain);known_nodes=[n.record() for n in existing_nodes]
            fork=stream.fork();changed=list(prefix)
            for bar in bars[cut:]:
                price=bar.close+D('2')*(len(changed)-cut+1)
                changed.append(replace(bar,open=price,high=price,low=price,close=price,lineage=digest(['future153',bar.lineage])))
                fork.append(changed)
            self.assertEqual(known,[p for p in fork.journal if p.available<=prefix[-1].available])
            self.assertEqual(known,stream.journal)
            Parser().parse(fork.chain)
            self.assertEqual(known_nodes,[n.record() for n in existing_nodes])
            self.assertEqual(known_nodes,[n.record() for n in Parser().parse(stream.chain)])

    def test_tied_terminal_prevents_the_claimed_confirmation(self):
        for record in self.records:
            target,parent,pos,bars,*_=self.generated[record['case']['id']]
            changed=list(bars);last=target.anchors[-1].index;bar=changed[last+1];price=changed[last].close
            changed[last+1]=replace(bar,open=price,high=price,low=price,close=price,lineage='invented153_tie')
            journal,chain=confirmed(changed,2)
            self.assertNotIn(last,{p.index for p in journal})
            self.assertFalse(self.example.matching(Parser().parse(chain),target))

    def test_rare_families_remain_observation_only_and_ambiguity_is_retained(self):
        for record in self.records:
            family=record['case']['family'];node=record['exact_records'][0]
            if family in OBSERVATION_ONLY:self.assertFalse(node['actionable'])
            if family in ('leading_33333','ending_diagonal'):
                alternatives={a['family'] for a in record['full_span_alternatives']}
                self.assertTrue({'leading_33333','ending_diagonal'}<=alternatives)
        self.assertEqual(8,sum(r['case']['family'] in OBSERVATION_ONLY for r in self.records))

    def test_bad_child_endpoints_and_incomplete_resolution_cannot_be_actionable(self):
        for record in self.records:
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            node=self.example.matching(nodes,target)[0];child=node.children[0]
            first=replace(child.anchors[0],index=child.anchors[0].index+1)
            bad=replace(node,children=(replace(child,anchors=(first,*child.anchors[1:])),*node.children[1:]))
            self.assertIn('child_endpoints',diagnose(bad,parent,pos)['failed']);self.assertFalse(bad.actionable)
            unresolved=replace(node,children=(),depth=1)
            self.assertNotEqual('valid_at_resolution',diagnose(unresolved,parent,pos)['state'])
            self.assertFalse(unresolved.actionable)

    def test_forbidden_triangle_and_diagonal_parent_locations_reject_bar_derived_nodes(self):
        for record in self.records:
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            family=record['case']['family'];node=self.example.matching(nodes,target)[0]
            if family.startswith('triangle'):
                self.assertIn('parent_location',diagnose(node,'impulse','2')['failed'])
            elif family.startswith(('leading','ending','expanding_diagonal')):
                self.assertIn('parent_location',diagnose(node,'impulse','3')['failed'])

    def test_single_and_multiple_extensions_resolve_at_depth_three_and_four_is_unsupported(self):
        for record in self.records:
            if not record['case']['extensions']:continue
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            node=self.example.matching(nodes,target)[0]
            self.assertEqual(3,node.height)
            self.assertEqual(record['case']['extensions'],[i for i,c in enumerate(node.children) if c.children])
            self.assertTrue(node.actionable)
            outer=node.children[record['case']['extensions'][0]]
            nested=self.example.resolve_impulse(outer.children[0])
            deeper=replace(outer,children=(nested,*outer.children[1:]))
            children=list(node.children);children[record['case']['extensions'][0]]=deeper
            unsupported=replace(node,children=tuple(children))
            self.assertEqual('unsupported',diagnose(unsupported,parent,pos)['state'])
            self.assertEqual(['finite_depth'],diagnose(unsupported,parent,pos)['failed']);self.assertFalse(unsupported.actionable)

    def test_budget_exhaustion_and_candidate_cap_block_policy_even_with_partial_nodes(self):
        for record in self.records:
            target,parent,pos,bars,journal,chain,parser,nodes=self.generated[record['case']['id']]
            for limited in (Parser(budget=0),Parser(cap=0)):
                partial=limited.parse(chain);self.assertTrue(limited.incomplete)
                if limited.cap==0:self.assertTrue(partial)
                policy=Policy();self.assertEqual([],policy.update([],bars,(target.side,)*2,incomplete=limited.incomplete))
                self.assertEqual('search_incomplete',policy.reason);self.assertEqual([],policy.revisions)

    def test_public_cli_is_exclusive_and_has_no_order_or_market_options(self):
        for args in ([str(self.output)],['--live'],['--source','market']):
            done=subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)
            self.assertNotEqual(0,done.returncode)
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        self.assertTrue(all(row['status']=='UNAVAILABLE' and row['returns'] is None for row in study_status()['cells']))
        self.assertFalse(DemoBoundary().submission_status()['available'])

    def write(self,name,value):
        if os.environ.get('ELLIOTT_PATTERN_EVIDENCE_DIR'):
            with (self.output/name).open('x') as file:json.dump(value,file,indent=2);file.write('\n')


if __name__ == '__main__':unittest.main()
