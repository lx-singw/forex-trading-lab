"""Pre-return plan integrity and eligibility diagnostics, with no market data."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import elliott_study_145 as s

ROOT=Path(__file__).resolve().parents[1]


def interval(start,end):return {"start":start,"end":end}


def declared():
    """Entirely invented metadata assertions, deliberately not qualified facts."""
    p=s.draft();p['case']='invented_complete_claims'
    p['source']={'alias':'source_invented','route':'existing_historical'}
    for name,start,end,warm in (('development','2014-01-01','2016-01-01','2013-01-01'),
                                ('validation','2016-01-01','2018-01-01','2015-01-01')):
        p['partitions'][name]={'interval':interval(start,end),'warmup':{'interval':interval(warm,start),
                                   'declared_complete_bars':{f:253 for f in s.FRAMES}}}
    p['history']['complete']=True
    for gate in s.GATES:
        p['evidence'][gate]={'sha256':'a'*64,'intervals':[interval('2013-01-01','2018-01-01')],'timeframes':list(s.FRAMES)}
    p['costs']['status']='broker_evidence_declared'
    return p


def codes(result,scope=None):
    return {i['code'] for i in result['issues'] if scope is None or i['scope']==scope}


class Study145Tests(unittest.TestCase):
    def test_existing_strategy_admission_stays_closed(self):
        from forex_demo_lab.elliott_full.admission import study_status,DemoBoundary
        before=study_status();s.assess(declared())
        self.assertEqual(before,study_status());self.assertEqual(16,len(before['cells']))
        self.assertTrue(all(c['status']=='UNAVAILABLE' and c['returns'] is None for c in before['cells']))
        self.assertIs(DemoBoundary().submission_status()['available'],False)

    def setUp(self):
        self.home=tempfile.TemporaryDirectory();self.root=Path(self.home.name)

    def tearDown(self):self.home.cleanup()

    def frozen(self,plan=None):
        p=self.root/'plan.json';m=self.root/'freeze.json'
        s.write(p,s.draft() if plan is None else plan);s.freeze(p,m)
        return p,m

    def test_current_draft_assigns_no_dates_or_source(self):
        p=s.draft();r=s.assess(p)
        self.assertIsNone(p['source']['alias']);self.assertIsNone(p['source']['route'])
        self.assertTrue(all(row['interval']==interval(None,None) for row in p['partitions'].values()))
        self.assertIn('source_unassigned',codes(r));self.assertIn('historical_costs_unknown',codes(r))
        self.assertIn('prior_trial_history_incomplete',codes(r))
        self.assertTrue(all('evidence_missing_'+g in codes(r) for g in s.GATES))

    def test_every_cell_retained_with_null_returns_in_both_tracks(self):
        for track in s.TRACKS:
            p=s.draft();p['track']=track;r=s.assess(p)
            combinations={(c['candidate'],c['profile'],c['partition']) for c in r['cells']}
            self.assertEqual(16,len(combinations));self.assertEqual(16,r['planned_cells'])
            self.assertTrue(all(c['status']=='UNAVAILABLE' and c['returns'] is None for c in r['cells']))
            for flag in ('market_data_read','returns_computed','native_queries','orders_available'):
                self.assertIs(r[flag],False)

    def test_complete_claims_and_hashes_cannot_self_qualify(self):
        r=s.assess(declared())
        self.assertFalse(any(i['state'] in ('MISSING','BLOCKED') for i in r['issues']))
        self.assertTrue(all('evidence_not_independently_qualified_'+g in codes(r) for g in s.GATES))
        self.assertIn('independent_qualification_required',codes(r))
        self.assertIn('qualified_market_runner_unavailable',codes(r))
        self.assertEqual('UNAVAILABLE',r['status']);self.assertEqual(0,r['market_cells_run'])

    def test_24_calendar_months_not_730_elapsed_days(self):
        p=declared();p['partitions']['development']['interval']=interval('2019-01-01','2020-12-31')
        p['partitions']['development']['warmup']['interval']=interval('2018-01-01','2019-01-01')
        self.assertIn('fewer_than_24_calendar_months',codes(s.assess(p),'development'))
        self.assertEqual(date(2022,2,28),s.add_months(date(2020,2,29),24))
        self.assertFalse('fewer_than_24_calendar_months' in codes(s.assess(declared()),'development'))

    def test_partition_overlap_and_reversal_block(self):
        p=declared();p['partitions']['validation']['interval']=interval('2015-01-01','2017-01-01')
        p['partitions']['validation']['warmup']['interval']=interval('2014-01-01','2015-01-01')
        self.assertIn('partitions_not_chronological_disjoint',codes(s.assess(p)))
        p['partitions']['validation']['interval']=interval('2017-01-01','2015-01-01')
        with self.assertRaisesRegex(ValueError,'half_open'):s.assess(p)

    def test_warmup_must_end_at_partition_and_counts_are_not_days(self):
        for frame in s.FRAMES:
            p=declared();p['partitions']['development']['warmup']['declared_complete_bars'][frame]=252
            self.assertIn('insufficient_declared_warmup_'+frame,codes(s.assess(p),'development'))
        p=declared();p['partitions']['development']['warmup']['interval']['end']='2013-12-31'
        self.assertIn('warmup_not_contiguous_with_partition',codes(s.assess(p)))
        p['partitions']['development']['warmup']['interval']['end']='2014-01-02'
        self.assertIn('warmup_not_contiguous_with_partition',codes(s.assess(p)))

    def test_consumed_quarantined_reserved_ranges_block(self):
        for start,end,code in (('2025-01-01','2026-01-01','date_consumed'),
                               ('2026-10-01','2026-11-01','date_quarantined'),
                               ('2026-11-01','2027-01-01','date_reserved_untouched')):
            p=declared();p['partitions']['validation']['interval']=interval(start,end)
            self.assertIn(code,codes(s.assess(p),'validation'))
            p['partitions']['validation']['warmup']['interval']=interval(start,end)
            p['partitions']['validation']['interval']=interval('2028-01-01','2030-01-01')
            self.assertIn(code,codes(s.assess(p),'validation'))

    def test_half_open_policy_boundaries_do_not_touch_next_interval(self):
        self.assertFalse(s.overlap((date(2023,1,1),date(2025,1,1)),(date(2025,1,1),date(2026,1,1))))
        p=declared();p['partitions']['development']['interval']=interval('2023-01-01','2025-01-01')
        p['partitions']['development']['warmup']['interval']=interval('2022-01-01','2023-01-01')
        self.assertNotIn('date_consumed',codes(s.assess(p),'development'))
        self.assertNotIn('date_seen_development_only',codes(s.assess(p),'development'))

    def test_seen_2024_blocks_funded_validation_but_not_price_warmup(self):
        p=declared();p['partitions']['validation']['interval']=interval('2024-01-01','2026-01-01')
        self.assertIn('date_seen_development_only',codes(s.assess(p),'validation'))
        p['partitions']['validation']['interval']=interval('2027-01-01','2029-01-01')
        p['partitions']['validation']['warmup']['interval']=interval('2024-01-01','2025-01-01')
        r=s.assess(p)
        self.assertNotIn('date_seen_development_only',codes(r,'validation'))
        self.assertIn('warmup_not_contiguous_with_partition',codes(r,'validation'))

    def test_prior_price_return_rule_and_friend_exposures_block_validation(self):
        for kind in ('prices','returns','rule_adjustment','friend_example'):
            p=declared();p['history']['exposures']=[{'interval':interval('2017-06-01','2017-07-01'),'kind':kind,
                                                  'track':'other','joint_study_sha256':None}]
            self.assertIn('validation_previously_exposed',codes(s.assess(p),'validation'))

    def test_development_exposure_does_not_contaminate_unseen_validation(self):
        p=declared();p['history']['exposures']=[{'interval':interval('2014-01-01','2016-01-01'),'kind':'returns',
                                              'track':'other','joint_study_sha256':None}]
        self.assertNotIn('validation_previously_exposed',codes(s.assess(p)))

    def test_joint_freeze_claim_requires_review_and_does_not_admit(self):
        p=declared();p['joint_study_sha256']='b'*64
        p['history']['exposures']=[{'interval':interval('2016-01-01','2018-01-01'),'kind':'returns',
                                   'track':'hypothetical_cost_sensitivity','joint_study_sha256':'b'*64}]
        r=s.assess(p);self.assertIn('joint_pre_return_freeze_requires_review',codes(r))
        self.assertNotIn('validation_previously_exposed',codes(r));self.assertEqual('UNAVAILABLE',r['status'])
        p['history']['exposures'][0]['kind']='rule_adjustment'
        self.assertIn('validation_previously_exposed',codes(s.assess(p)))

    def test_joint_mismatch_or_same_track_is_already_exposed(self):
        for track,sha in (('qualified','b'*64),('hypothetical_cost_sensitivity','c'*64)):
            p=declared();p['joint_study_sha256']='b'*64
            p['history']['exposures']=[{'interval':interval('2016-01-01','2018-01-01'),'kind':'prices','track':track,'joint_study_sha256':sha}]
            self.assertIn('validation_previously_exposed',codes(s.assess(p)))

    def test_hypothetical_costs_never_pass_qualified_or_demo_gate(self):
        p=declared();p['costs']['status']='hypothetical_117'
        self.assertIn('hypothetical_costs_cannot_pass_qualified_track',codes(s.assess(p)))
        p['track']='hypothetical_cost_sensitivity';r=s.assess(p)
        self.assertIn('sensitivity_cannot_satisfy_broker_or_demo_gate',codes(r))
        self.assertEqual('UNAVAILABLE',r['status'])

    def test_unknown_costs_and_empty_evidence_are_not_zero_costs(self):
        p=declared();p['costs']['status']='unknown';p['evidence']['commission_swap']['sha256']=None
        r=s.assess(p)
        self.assertIn('historical_costs_unknown',codes(r));self.assertIn('evidence_missing_commission_swap',codes(r))
        p['costs']['contradictions']=True
        self.assertIn('cost_contradiction_requires_new_declared_profile',codes(s.assess(p)))

    def test_budget_counts_prior_declarations_including_unavailable_attempts(self):
        for track in s.TRACKS:
            p=declared();p['track']=track;p['prior_cells'][track]=16
            self.assertIn('initial_track_budget_exhausted',codes(s.assess(p)))
        p=declared();p['prior_cells']['hypothetical_cost_sensitivity']=16
        self.assertNotIn('initial_track_budget_exhausted',codes(s.assess(p)))

    def test_source_routes_and_captures_are_not_reopened(self):
        for route,expected in (('closed_native090','closed_route_not_renewed'),('sdk_attach_only','closed_route_not_renewed'),
                               ('native_capture','no_bounded_native_capture_assigned')):
            p=declared();p['source']['route']=route
            self.assertIn(expected,codes(s.assess(p)))

    def test_evidence_scope_unions_cover_edges_without_filling_gaps(self):
        target=(date(2014,1,1),date(2016,1,1))
        self.assertTrue(s.covered(target,[(date(2013,1,1),date(2015,1,1)),(date(2015,1,1),date(2018,1,1))]))
        self.assertFalse(s.covered(target,[(date(2013,1,1),date(2015,1,1)),(date(2015,1,2),date(2018,1,1))]))
        p=declared();p['evidence']['coverage_lineage']['intervals']=[interval('2014-01-01','2018-01-01')]
        self.assertIn('evidence_scope_gap_coverage_lineage',codes(s.assess(p),'development'))
        p['evidence']['coverage_lineage']['timeframes']=['D1']
        self.assertIn('evidence_frames_incomplete_coverage_lineage',codes(s.assess(p)))

    def test_schema_rejects_prices_credentials_paths_and_policy_overrides(self):
        for field,value in (('prices',[]),('returns',{}),('password','not-a-secret'),('account_id',123),
                            ('price_path','never-open-this'),('policy_overrides',{})):
            p=s.draft();p[field]=value
            with self.assertRaisesRegex(ValueError,'metadata_plan_fields'):s.validate(p)
        p=s.draft();p['evidence']['source_use']['path']='never-open-this'
        with self.assertRaisesRegex(ValueError,'evidence_fields'):s.validate(p)

    def test_strict_counts_frames_dates_and_hashes(self):
        mutations=(lambda p:p['prior_cells'].update(qualified=True),
                   lambda p:p['partitions']['development']['warmup']['declared_complete_bars'].update(D1=253.0),
                   lambda p:p['evidence']['source_use'].update(timeframes=['H1','H1']),
                   lambda p:p['evidence']['source_use'].update(sha256='bad'),
                   lambda p:p['partitions']['validation'].update(interval=interval('20240230','2026-01-01')),
                   lambda p:p['partitions']['development'].update(interval=interval(None,'2016-01-01')),
                   lambda p:p['costs'].update(profile_declaration_sha256='0'*64))
        for change in mutations:
            p=s.draft();change(p)
            with self.assertRaises(ValueError):s.validate(p)

    def test_json_duplicates_nonfinite_size_and_symlinks_reject(self):
        path=self.root/'bad.json'
        for data in ('{"a":1,"a":2}','{"a":NaN}','x'*(s.LIMIT+1)):
            path.write_text(data)
            with self.assertRaises(ValueError):s.read(path)
        target=self.root/'target.json';s.write(target,s.draft());link=self.root/'link.json';link.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'metadata_input_file'):s.read(link)

    def test_freeze_exact_bytes_and_exclusive_outputs(self):
        p,m=self.frozen();report=s.run(p,m,self.root/'result')
        self.assertEqual('UNAVAILABLE',report['status'])
        with self.assertRaises(FileExistsError):s.freeze(p,m)
        with self.assertRaises(FileExistsError):s.run(p,m,self.root/'result')
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'metadata_freeze_binding'):s.run(p,m,self.root/'changed')
        self.assertFalse((self.root/'changed').exists())

    def test_manifest_privilege_and_policy_mutations_reject(self):
        p,m=self.frozen();original=json.loads(m.read_text())
        for field,value in (('orders_available',True),('returns_available',0),('market_data_access_available',True),
                            ('policy',{}),('sources',{})):
            bad=deepcopy(original);bad[field]=value;m.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'metadata_freeze_binding'):s.run(p,m,self.root/'denied')
            self.assertFalse((self.root/'denied').exists())

    def test_source_change_during_preflight_rejects_before_output(self):
        p,m=self.frozen();before=s.bindings();after=deepcopy(before);after['preflight']['changed']='0'*64
        with patch.object(s,'bindings',side_effect=[before,after]):
            with self.assertRaisesRegex(ValueError,'preflight_sources_changed'):s.run(p,m,self.root/'denied')
        self.assertFalse((self.root/'denied').exists())

    def test_no_manifest_evidence_paths_or_price_files_are_read(self):
        p,m=self.frozen(declared());observed=[];reader=s.read
        def track(path):observed.append(Path(path));return reader(path)
        with patch.object(s,'read',side_effect=track):s.run(p,m,self.root/'result')
        self.assertEqual([p,m],observed)

    def test_changed_frozen_cost_profile_is_not_silently_accepted(self):
        frozen=s.strategy_bindings();frozen['frozen_controls']['config/research-candidates-117.json']='0'*64
        with patch.object(s,'strategy_bindings',return_value=frozen):
            with self.assertRaisesRegex(ValueError,'fixed_profile_reference_changed'):s.bindings()

    def test_public_cli_drafts_freezes_and_reports_only_metadata(self):
        script=str(ROOT/'scripts/elliott-study-145.py');p=self.root/'plan.json';m=self.root/'freeze.json';out=self.root/'out'
        for args in (('draft',str(p)),('freeze',str(p),str(m)),('preflight',str(p),str(m),str(out))):
            done=subprocess.run([sys.executable,script,*args],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(0,done.returncode,done.stderr)
        result=json.loads((out/'preflight.json').read_text())
        self.assertEqual(16,len(result['cells']));self.assertFalse(result['market_data_read'])
        self.assertIn('source_unassigned',(out/'requirements.md').read_text())


if __name__=='__main__':unittest.main()
