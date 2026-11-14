import ast
import copy
import json
from pathlib import Path
import unittest

from forex_demo_lab.data_qualification_036 import VERSION,GATES,overlap,validate_research,validate_matrix,policy
from test_fresh_ticks_032 import row

ROOT=Path(__file__).resolve().parents[1]
DECLARED=json.loads((ROOT/'config/research-actions-036.json').read_text())
URL=DECLARED['target_pages'][0]


def research():
    return dict(version=VERSION,actions=[dict(action_index=0,kind='search',query=DECLARED['search_queries'][0],domains=DECLARED['allowed_domains'],retrieved_utc='2026-10-06T14:00:00+00:00'),
        dict(action_index=1,kind='open',url=URL,status='retrieved',retrieved_utc='2026-10-06T14:00:01+00:00'),
        dict(action_index=2,kind='find',url=URL,pattern=DECLARED['find_patterns'][0],retrieved_utc='2026-10-06T14:00:02+00:00')],
        findings=[dict(id='f1',classification='documented',summary='A synthetic attributed statement.',source_urls=[URL])],
        market_requests=0,strategy_replays=0,orders_available=False)


def matrix():
    return [dict(gate=g,status='observed_pass' if i<2 else 'observed_failure' if i==2 else 'unresolved',
        evidence_class='observed_equality' if i<2 else 'observed_contradiction' if i==2 else 'absent_provider_evidence',
        local_evidence=['bound.json'],finding_ids=['f1'],limitation='Synthetic limitation',minimal_missing_evidence='Synthetic missing evidence') for i,g in enumerate(GATES)]


class QualificationTests(unittest.TestCase):
    def test_expected_document_actions_and_counts(self):
        self.assertEqual(validate_research(research(),DECLARED),dict(search_queries=1,opens=1,finds=1,findings=1))

    def test_nonprimary_forum_http_or_private_urls_rejected(self):
        for url in ('https://evil.example/en/docs/x','https://www.mql5.com.evil.example/en/docs/x',
                    'https://www.mql5.com/en/forum/1','http://www.mql5.com/en/docs/x','https://user:secret@www.mql5.com/en/docs/x'):
            r=research();r['actions'][1]['url']=url
            with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_undeclared_query_target_and_find_rejected(self):
        for index,key,value in ((0,'query','undeclared'),(1,'url','https://www.mql5.com/en/docs/other'),(2,'pattern','undeclared')):
            r=research();r['actions'][index][key]=value
            with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_duplicate_queries_opens_finds_and_action_order_rejected(self):
        for index in (0,1,2):
            r=research();a=copy.deepcopy(r['actions'][index]);a['action_index']=3;r['actions'].append(a)
            with self.assertRaises(ValueError):validate_research(r,DECLARED)
        r=research();r['actions'][1]['action_index']=0
        with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_budget_authority_cannot_expand_and_market_actions_rejected(self):
        for key,value in (('maximum_search_queries',5),('maximum_opens',13),('maximum_finds',9),('allowed_domains',['evil.example'])):
            d=copy.deepcopy(DECLARED);d[key]=value
            with self.assertRaises(ValueError):validate_research(research(),d)
        for key,value in (('market_requests',1),('strategy_replays',1),('orders_available',True)):
            r=research();r[key]=value
            with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_unretrieved_or_unattributed_findings_and_unopened_find_rejected(self):
        for mode in ('unavailable','missing_source','missing_summary','unopened'):
            r=research()
            if mode=='unavailable':r['actions'][1]['status']='unavailable'
            elif mode=='missing_source':r['findings'][0]['source_urls']=[]
            elif mode=='missing_summary':r['findings'][0]['summary']=''
            else:r['actions'][2]['url']=DECLARED['target_pages'][1]
            with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_utc_receipts_and_distinct_finding_ids_required(self):
        r=research();r['actions'][0]['retrieved_utc']='2026-10-06T14:00:00'
        with self.assertRaises(ValueError):validate_research(r,DECLARED)
        r=research();r['findings'].append(copy.deepcopy(r['findings'][0]))
        with self.assertRaises(ValueError):validate_research(r,DECLARED)

    def test_overlap_retains_flag_revision_without_masking(self):
        old=[{**row(),'flags':1026}];new=[{**old[0],'flags':1154}]
        result=overlap(old,new)
        self.assertTrue(result['all_non_flag_fields_equal']);self.assertEqual(result['changed_field_counts'],{'flags':1})
        self.assertEqual(result['flag_xor_histogram'],{128:1});self.assertEqual(result['complete_witnesses_matched'],0)
        self.assertFalse(result['ordinal_alignment_replaces_complete_identity']);self.assertFalse(result['unknown_flag_bits_interpreted'])

    def test_nonflag_revision_is_detected_and_complete_match_fails(self):
        old=[row()];new=[{**row(),'ask':1.1002}]
        result=overlap(old,new)
        self.assertFalse(result['all_non_flag_fields_equal']);self.assertEqual(result['non_flag_mismatch_prior_indices'],[0])
        self.assertEqual(result['changed_field_counts'],{'ask':1});self.assertEqual(result['complete_witnesses_missing'],1)

    def test_duplicate_full_identity_remains_ambiguous(self):
        result=overlap([row(),row()],[row(),row()])
        self.assertEqual(result['ambiguous_complete_witnesses'],2);self.assertEqual(result['complete_witnesses_matched'],0)
        self.assertEqual(result['complete_witnesses'][0]['matching_original_row_indices'],[0,1])

    def test_overlap_order_and_half_open_boundary_remain_explicit(self):
        old=[row(),row(1791295199999)];new=[row(1791280800000),*old,row(1791295200000)]
        result=overlap(old,new)
        self.assertEqual(result['new_overlapping_rows'],2);self.assertEqual(result['complete_witnesses_matched'],2)
        self.assertEqual(result['complete_witnesses'][0]['matching_original_row_indices'],[1])
        with self.assertRaises(ValueError):overlap(old,[old[0]])

    def test_fixed_gate_order_and_bound_local_evidence(self):
        self.assertTrue(validate_matrix(matrix(),{'bound.json':'hash'},research()))
        m=matrix();m.reverse()
        with self.assertRaises(ValueError):validate_matrix(m,{'bound.json':'hash'},research())
        with self.assertRaises(ValueError):validate_matrix(matrix(),{},research())

    def test_provider_qualification_cannot_be_promoted_from_docs(self):
        for i in (2,3,4,5):
            m=matrix();m[i]['status']='observed_pass'
            with self.assertRaises(ValueError):validate_matrix(m,{'bound.json':'hash'},research())

    def test_gate_findings_and_limitations_must_be_attributed(self):
        for key,value in (('finding_ids',['unknown']),('limitation',''),('minimal_missing_evidence','')):
            m=matrix();m[0][key]=value
            with self.assertRaises(ValueError):validate_matrix(m,{'bound.json':'hash'},research())

    def test_policy_stays_proposal_only_with_immutable_originals(self):
        p=policy();self.assertTrue(p['proposal_only']);self.assertFalse(p['implemented'])
        self.assertTrue(p['preserve_every_original_revision'])
        for key in ('original_overwrite_permitted','source_blending_permitted','flag_masking_of_originals_permitted',
                    'complete_identity_gate_changes_permitted','clock_normalization_permitted','qualified_publication_permitted',
                    'performance_testing_permitted','fresh_performance_eligible','annual_eligible','orders_available'):
            self.assertFalse(p[key])

    def test_review_source_has_no_market_api_or_network_calls(self):
        tree=ast.parse((ROOT/'src/forex_demo_lab/data_qualification_036.py').read_text())
        forbidden={'initialize','copy_ticks_range','copy_rates_range','symbol_info_tick','order_send','symbol_select','shutdown','urlopen','get'}
        for n in ast.walk(tree):
            if isinstance(n,(ast.Import,ast.ImportFrom)):self.assertNotIn('MetaTrader5',ast.unparse(n))
            if isinstance(n,ast.Call):
                name=n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else ''
                self.assertNotIn(name,forbidden)
