from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import elliott_comparison_126 as comparison
from forex_demo_lab.comparison_fixture_126 import CASES, fixture
from forex_demo_lab.elliott_execution_fixture_125 import fixture as ew_fixture
from forex_demo_lab.daily_runs_fixture_122 import fixture as daily_fixture
from test_daily_runs_122 import audit_statistics
from test_daily_fills_120 import audit_ledger
from test_elliott_execution_125 import audit_account

ROOT = Path(__file__).resolve().parents[1]
F = lambda v: Fraction(str(v))


class Comparison126Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache_temp = tempfile.TemporaryDirectory()
        cls.cache_root = Path(cls.cache_temp.name)
        cls.cache = {}

    @classmethod
    def tearDownClass(cls):
        cls.cache_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def bundle(self, value=None, root=None):
        root = root or self.root
        path, manifest = root / "input.json", root / "frozen.json"
        comparison.daily.write_new(path, value if value is not None else fixture())
        comparison.freeze_fixture(path, manifest)
        return path, manifest

    def case(self, name="ew_long_target"):
        if name not in self.cache:
            directory = self.cache_root / name
            directory.mkdir()
            path, manifest = self.bundle(fixture(name), directory)
            output = directory / "run"
            report = comparison.evaluate_fixture(path, manifest, output)
            self.cache[name] = path, manifest, output, report
        return self.cache[name]

    def copied(self, name="ew_long_target"):
        path, manifest, output, report = self.case(name)
        new = self.root / "copy"
        shutil.copytree(output, new)
        return path, manifest, new, deepcopy(report)

    def hashes(self, root):
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file()}

    def test_five_unique_models_and_26_unmodified_streams(self):
        self.assertEqual(comparison.MODELS, ("EWPB_D124", "T12_D", "MR20_D", "MIX50_D", "CASH"))
        self.assertEqual(len(CASES), 26)
        for name in CASES:
            actual = fixture(name)
            original = ew_fixture(name[3:]) if name.startswith('ew_') else daily_fixture(name[6:])
            self.assertEqual(actual['stream'], original['stream'])
            self.assertEqual(actual['partitions'], original['partitions'])
            comparison.validate_fixture(actual)

    def test_same_original_quotes_and_publication_ids_both_families(self):
        for name in ('ew_long_target', 'daily_targets', 'ew_delayed_publication'):
            path, manifest, root, report = self.case(name)
            raw = json.loads(path.read_bytes())
            for part in report['partitions']:
                d = root / part['partition']['name']
                a = json.loads((d/'compiled-input.json').read_bytes())
                b = json.loads((d/'legacy-input.json').read_bytes())
                self.assertEqual(len(a['events']), len(b['events']))
                for ew, legacy in zip(a['events'], b['events']):
                    raw_quote = raw['stream']['messages'][ew['message_sequence']]
                    for k in ('source_msc','receipt_msc','bid','ask'):
                        self.assertEqual(ew[k], legacy[k])
                        self.assertEqual(ew[k], raw_quote[k])
                    self.assertEqual(ew['feature']['session_id'], legacy['target_session_id'])
                    self.assertEqual(ew['feature']['available_msc'], legacy['feature_decision_msc'])

    def test_independent_financial_and_statistics_oracles(self):
        for name in ('ew_long_target','ew_short_target','ew_long_gap','ew_financing_pause','daily_targets'):
            _, _, root, report = self.case(name)
            for part in report['partitions']:
                d = root / part['partition']['name']
                for cell in part['cells']:
                    if cell['statistics'] is None:
                        continue
                    stem = 'compiled' if cell['candidate']=='EWPB_D124' else 'legacy'
                    compiled = json.loads((d/(stem+'-input.json')).read_bytes())
                    r = cell['account_report']
                    (audit_account if stem=='compiled' else audit_ledger)(compiled, r)
                    audit_statistics(compiled, r, part['partition'], cell['statistics'])

    def test_elliott_account_outcomes_equal_unchanged125_pipeline(self):
        _, _, _, report = self.case()
        raw, manifest = self.root/'ew.json', self.root/'ew-frozen.json'
        comparison.daily.write_new(raw, ew_fixture('long_target'))
        comparison.ew.freeze_fixture(raw, manifest)
        old = comparison.ew.evaluate_fixture(raw, manifest, self.root/'ew-run')
        for previous, current in zip(old['partitions'], report['partitions']):
            for cell in current['cells']:
                if cell['candidate']=='EWPB_D124':
                    expected = next(r for r in previous['results'] if r['candidate']==cell['candidate'] and r['profile']==cell['profile'])
                    self.assertEqual(expected['summary'], cell['account_report']['summary'])

    def test_fresh_capital_in_both_adapters_for_later_period(self):
        _, _, root, report = self.case()
        for part in report['partitions']:
            d = root/part['partition']['name']
            for stem, cls, candidate in (('compiled',comparison.ew.Account,'EWPB_D124'),('legacy',comparison.fills.Replay,'T12_D')):
                account = cls(d/(stem+'-input.json'),d/(stem+'-frozen.json'),'base',candidate)
                state = account.state
                self.assertEqual(state['balance_usd'],'10000')
                self.assertIsNone(state['held']);self.assertIsNone(state['reservation'])
                self.assertFalse(state['paused']);self.assertEqual(state['consumed_sessions'],[])
                compiled = json.loads((d/(stem+'-input.json')).read_bytes())
                self.assertEqual(compiled['initial_account']['available_msc'],part['partition']['start_msc'])
                self.assertTrue(all(q['source_msc']>=part['partition']['start_msc'] for q in compiled['events']))

    def test_common_missing_history_or_endpoint_never_cash_return(self):
        for name in ('ew_missing_history','daily_missing_endpoint','ew_stale_endpoint'):
            _, _, _, report = self.case(name)
            failed = [p for p in report['partitions'] if p['common_reason']]
            self.assertTrue(failed)
            for part in failed:
                self.assertEqual(part['computed_accounts'],0)
                self.assertEqual(part['unavailable_accounts'],10)
                self.assertEqual(len(part['cells']),10)
                self.assertTrue(all(c['statistics'] is None and c['account_report'] is None and c['reason']==part['common_reason'] for c in part['cells']))

    def test_empty_received_prefix_unavailable_and_read_only_verifiable(self):
        value=fixture();start=value['stream']['calendar']['sessions'][0]['start_msc']
        value['partitions'][0].update(start_msc=start,end_msc=start+1000,endpoint_source_msc=start+500)
        path,manifest=self.bundle(value);root=self.root/'empty-run'
        report=comparison.evaluate_fixture(path,manifest,root)
        first=report['partitions'][0]
        self.assertEqual(first['common_reason'],'no_observed_prefix')
        self.assertEqual(first['computed_accounts'],0)
        self.assertTrue(all(c['statistics'] is None and c['account_report'] is None for c in first['cells']))
        self.assertEqual(report['partitions'][1]['computed_accounts'],10)
        before=self.hashes(root)
        self.assertEqual(comparison.verify_fixture(path,manifest,root),report)
        self.assertEqual(before,self.hashes(root))

    def test_nonpositive_exit_only_invalidates_affected_account(self):
        _, _, _, report = self.case('ew_nonpositive_exit')
        part = report['partitions'][0]
        self.assertIsNone(part['common_reason'])
        self.assertGreater(part['computed_accounts'],0)
        for cell in part['cells']:
            if cell['candidate']=='EWPB_D124':
                self.assertEqual(cell['reason'],'nonpositive_exit_price')
                self.assertIsNone(cell['statistics']);self.assertIsNone(cell['account_report'])
            if cell['candidate']=='CASH':
                self.assertEqual(cell['statistics']['toy_net_usd'],'0')

    def test_no_trade_ratios_null_and_single_cash_control(self):
        _, _, _, report = self.case('ew_no_signal')
        self.assertEqual(report['computed_accounts'],20)
        for part in report['partitions']:
            self.assertEqual(sum(c['candidate']=='CASH' for c in part['cells']),2)
            for cell in part['cells']:
                s=cell['statistics']
                self.assertEqual((s['trades'],s['toy_net_usd'],s['exposure_msc']), (0,'0',0))
                for k in ('toy_win_fraction','net_expectancy_usd','payoff_ratio','profit_factor'):
                    self.assertIsNone(s[k])

    def test_cost_memos_and_loss_excess_preserved(self):
        _, _, _, report = self.case('ew_long_gap')
        found = False
        for part in report['partitions']:
            for c in part['cells']:
                s=c['statistics']
                self.assertEqual(F(s['toy_net_usd']),F(s['gross_usd'])-F(s['commissions_usd'])+F(s['financing_usd']))
                self.assertFalse(s['memos_are_extra_debits'])
                if c['candidate']=='EWPB_D124' and part['partition']['name']=='development':
                    found=True
                    self.assertGreater(F(s['largest_loss_usd']),25)
                    self.assertGreater(F(s['loss_beyond_entry_estimate'][0]['excess_usd']),0)
        self.assertTrue(found)

    def test_sparse_window_anchor_and_boundary_mark(self):
        _, _, _, report=self.case('ew_financing_pause')
        for part in report['partitions']:
            for c in part['cells']:
                s=c['statistics']
                for k in ('monthly','quarterly'):
                    self.assertEqual(s[k][-1]['closing_equity_usd'],s['final_cash_usd'])
                    self.assertTrue(all(r['kind']=='observed_window_not_certified_calendar_close' for r in s[k]))
                    self.assertEqual(sum(F(r['ledger_cash_change_usd']) for r in s[k]),F(s['toy_net_usd']))
                    for a,b in zip(s[k],s[k][1:]):
                        if a['closing_equity_usd'] is None:
                            self.assertIsNone(b['observed_window_return'])
                            self.assertIsNone(b['opening_equity_usd'])

    def test_later_changes_cannot_alter_development_statistics(self):
        raw=fixture(); changed=deepcopy(raw);cutoff=raw['partitions'][0]['end_msc']
        for q in changed['stream']['messages']:
            if q['kind']=='quote' and q['receipt_msc']>=cutoff:
                q.update(bid=.9,ask=.9001)
        original_root=self.root/'a';original_root.mkdir()
        changed_root=self.root/'b';changed_root.mkdir()
        pa,ma=self.bundle(raw,original_root);pb,mb=self.bundle(changed,changed_root)
        a=comparison.evaluate_fixture(pa,ma,original_root/'run')['partitions'][0]
        b=comparison.evaluate_fixture(pb,mb,changed_root/'run')['partitions'][0]
        self.assertEqual(a['shared_quotes_sha256'],b['shared_quotes_sha256'])
        for x,y in zip(a['cells'],b['cells']):
            for c in (x,y):
                c['statistics'].pop('fill_fixture_sha256');c['statistics'].pop('fill_manifest_sha256')
            self.assertEqual(x['statistics'],y['statistics'])

    def test_read_only_verify_repeatedly_preserves_all_bytes(self):
        path,manifest,root,report=self.case()
        before=self.hashes(root)
        for _ in range(2):self.assertEqual(comparison.verify_fixture(path,manifest,root),report)
        self.assertEqual(before,self.hashes(root))

    def test_rehashed_statistics_forgery_still_rejected(self):
        path,manifest,root,report=self.copied()
        d=root/'development'
        comparisons=json.loads((d/'comparisons.json').read_bytes())
        comparisons['cells'][0]['statistics']['toy_net_usd']='999'
        (d/'comparisons.json').write_text(json.dumps(comparisons))
        part=report['partitions'][0]
        part['cells']=comparisons['cells']
        part['artifacts']['comparisons.json']=comparison.ew._hash(d/'comparisons.json')
        (d/'partition-report.json').write_text(json.dumps(part))
        (root/'run-report.json').write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'comparison_artifact_changed'):
            comparison.verify_fixture(path,manifest,root)

    def test_rehashed_compiled_quotes_cannot_replace_original_stream(self):
        path,manifest,root,_=self.copied()
        d=root/'development'
        for stem,key in (('compiled','compiled_sha256'),('legacy','fixture_sha256')):
            p=d/(stem+'-input.json');value=json.loads(p.read_bytes())
            value['events'][0]['ask']+=.00001;p.write_text(json.dumps(value))
            m=d/(stem+'-frozen.json');value=json.loads(m.read_bytes())
            value[key]=comparison.ew._hash(p);m.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'comparison_artifact_changed'):
            comparison.verify_fixture(path,manifest,root)

    def test_human_report_or_owner_changes_reject(self):
        for filename,reason in (('REPORT.md','comparison_readable_report_changed'),('run-binding.json','comparison_artifact_changed')):
            directory=self.root/filename.replace('.','_');directory.mkdir()
            path,manifest,old,_=self.case('ew_no_signal');root=directory/'copy';shutil.copytree(old,root)
            p=root/filename
            p.write_text('changed' if filename=='REPORT.md' else '{}')
            with self.assertRaisesRegex(ValueError,reason):comparison.verify_fixture(path,manifest,root)

    def test_real_contest_boolean_modes_and_input_flags_reject(self):
        for mode in (1,2,False):
            value=fixture();value['stream']['initial_account']['trade_mode']=mode
            with self.assertRaisesRegex(ValueError,'synthetic_demo_account_required'):comparison.validate_fixture(value)
        for key in ('qualified','untouched','signals','positions'):
            value=fixture();value[key]=True
            with self.assertRaisesRegex(ValueError,'comparison_fields'):comparison.validate_fixture(value)
        value=fixture();value['partitions'][1]['start_msc']=value['partitions'][0]['start_msc']
        with self.assertRaisesRegex(ValueError,'partition_overlap'):comparison.validate_fixture(value)

    def test_freeze_cost_source_flag_and_time_changes_reject(self):
        for index,change in enumerate((lambda m:m['profiles']['base']['config'].update(commission_per_lot_round_turn=0),
                                       lambda m:m.update(sources={}),lambda m:m.update(orders_available=0),
                                       lambda m:m.update(frozen_at_utc='2001-01-01T00:00:00'))):
            root=self.root/str(index);root.mkdir();path,manifest=self.bundle(root=root)
            value=json.loads(manifest.read_bytes());change(value);manifest.write_text(json.dumps(value))
            with self.assertRaises(ValueError):comparison.evaluate_fixture(path,manifest,root/'run')
            self.assertFalse((root/'run').exists())

    def test_account_prefix_restore_and_final_idempotence_both_adapters(self):
        _,_,root,report=self.case()
        part=report['partitions'][0];directory=root/'development'
        for stem,cls,candidate in (('compiled',comparison.ew.Account,'EWPB_D124'),('legacy',comparison.fills.Replay,'MIX50_D')):
            path,manifest=directory/(stem+'-input.json'),directory/(stem+'-frozen.json')
            instance=cls(path,manifest,'base',candidate)
            events=json.loads(path.read_bytes())['events']
            for event in events[:3]:instance.step(event)
            restored=cls.restore(path,manifest,instance.checkpoint(),'base',candidate)
            self.assertEqual(restored.state,instance.state)
            result=restored.run();before=restored.state
            self.assertFalse(restored.step(events[-1]));self.assertFalse(restored.finish())
            self.assertEqual(restored.run(),result);self.assertEqual(restored.state,before)
            expected=next(c['account_report'] for c in part['cells'] if c['candidate']==candidate and c['profile']=='base')
            self.assertEqual(result,expected)

    def test_cli_evaluate_verify_collision_and_partial_root_preserved(self):
        path,manifest=self.bundle(fixture('ew_no_signal'))
        script=str(ROOT/'scripts/elliott-comparison-126.py');root=self.root/'cli'
        for command in ('evaluate','verify'):
            result=subprocess.run([sys.executable,script,command,str(path),str(manifest),str(root)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            self.assertEqual(json.loads(result.stdout)['computed_accounts'],20)
        before=self.hashes(root)
        result=subprocess.run([sys.executable,script,'evaluate',str(path),str(manifest),str(root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['reason'],'artifact_exists')
        self.assertEqual(self.hashes(root),before)
        partial=self.root/'partial';partial.mkdir();(partial/'owned.txt').write_text('retain')
        with self.assertRaises(FileExistsError):comparison.evaluate_fixture(path,manifest,partial)
        self.assertEqual((partial/'owned.txt').read_text(),'retain')


if __name__ == '__main__':
    unittest.main()
