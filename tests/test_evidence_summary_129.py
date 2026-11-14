from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import evidence_summary_129 as evidence
from test_forward_capture_111 import payloads as quote_payloads, encode as quote_encode, START
from test_metadata_probe_127 import fixture_payloads as metadata_payloads, encode as metadata_encode, SECOND
from test_cost_probe_128 import fixture as cost_payloads, encode as cost_encode

ROOT = Path(__file__).resolve().parents[1]


def fixtures(root, quote_count=2, metadata=None, cost=None):
    groups = quote_encode(quote_payloads(quote_count))
    raw = {
        'quotes111': [(f'data/forward-capture-112/Run111-{START}-1-1/{name}', data) for name, data in groups],
        'metadata127': [(f'data/metadata-probe-127-native/Run127-{SECOND}-1-1/Metadata127.txt',
                         metadata_encode(metadata_payloads() if metadata is None else metadata))],
        'costs128': [(f'data/cost-probe-128-native/Run128-{SECOND}-1-1/Costs128.txt',
                     cost_encode(cost_payloads() if cost is None else cost))],
    }
    manifest = {'schema': evidence.SCHEMA, 'sources': []}
    for key in evidence.IDS:
        files = []
        for relative, data in raw[key]:
            path = root/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            files.append({'path': relative, 'sha256': hashlib.sha256(data).hexdigest()})
        manifest['sources'].append({'id': key, 'files': files})
    return manifest


class Evidence129Tests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.manifest = fixtures(self.root)

    def build(self, manifest=None):
        return evidence.build_summary(self.manifest if manifest is None else manifest, self.root)

    def test_report_reparses_all_sources_and_preserves_scopes(self):
        report = self.build()
        self.assertEqual(report['input_files'], 3)
        self.assertEqual(report['quotes']['observations'], 2)
        self.assertEqual(len(report['metadata']['latest_quote_reads']), 2)
        self.assertEqual(report['quotes']['capture_status'], 'stopped')
        self.assertEqual([s['id'] for s in report['sources']], list(evidence.IDS))
        self.assertEqual(report['sources'][0]['nominal_computer_gmt_origin_label'], '2026-10-12T12:00:00')
        self.assertEqual(report['sources'][1]['nominal_computer_gmt_origin_label'], '2026-10-14T12:00:00')

    def test_deterministic_json_markdown_and_inputs_unchanged(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        report = self.build()
        self.assertEqual(report, self.build())
        self.assertEqual(evidence.render_markdown(report), evidence.render_markdown(self.build()))
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        markdown = evidence.render_markdown(report)
        for source in report['sources']:
            for file in source['files']:
                self.assertIn(file['sha256'], markdown)
        self.assertIn('Metadata quote reads are kept separate', markdown)

    def test_market_headers_never_enable_qualification_money_or_identity(self):
        for source in self.manifest['sources']:
            for entry in source['files']:
                path = self.root/entry['path']
                raw = path.read_bytes()
                # Re-encode a valid changed declaration, not just a stale digest.
                if source['id'] == 'quotes111':
                    raw = quote_encode(quote_payloads(2, kind='market_declared'))[0][1]
                elif source['id'] == 'metadata127': raw = metadata_encode(metadata_payloads('market_declared'))
                else: raw = cost_encode(cost_payloads(kind='market_declared'))
                path.write_bytes(raw);entry['sha256'] = hashlib.sha256(raw).hexdigest()
        report = self.build()
        for key in ('producer_authenticated', 'cross_run_contract_authenticated', 'continuous_history_across_sources',
                    'source_utc_certified', 'receipt_utc_certified', 'historical_cost_terms_certified',
                    'strategy_evaluated', 'profitability_established', 'market_data_qualified',
                    'paper_evaluation_available', 'orders_available', 'real_money_execution_available'):
            self.assertIs(report[key], False)
        for key in ('source_age', 'commission_cost_USD', 'margin_requirement_USD', 'slippage_terms'):
            self.assertIsNone(report[key])
        self.assertEqual(report['model_assumptions_applied'], [])

    def test_failed_property_and_observed_zero_are_distinct(self):
        self.manifest = fixtures(self.root, metadata=metadata_payloads(failed=('point',)))
        report = self.build(); rows = {r['key']: r for r in report['metadata']['properties']}
        self.assertEqual(rows['point']['status'], 'query_failed'); self.assertIsNone(rows['point']['value'])
        self.assertIsNotNone(rows['account_leverage']['value'])
        self.assertGreater(rows['point']['error_code'], 0)

    def test_empty_failed_and_incomplete_commission_states_remain_distinct(self):
        cases = [(cost_payloads(rules=0), 'reported_empty'),
                 (cost_payloads(returned=-1, commission_error=4303), 'query_failed'),
                 (cost_payloads()[:5] + ['S\t9\t2'], 'incomplete')]
        for payloads, state in cases:
            self.manifest = fixtures(self.root, cost=payloads)
            report = self.build()
            self.assertEqual(report['costs']['commission_state'], state)
            self.assertIsNone(report['commission_cost_USD'])
            self.assertIn(state, evidence.render_markdown(report))

    def test_reported_rules_and_rebates_kept_without_conversion(self):
        report = self.build()
        self.assertEqual(report['costs']['commission_state'], 'reported_rules')
        self.assertEqual(report['costs']['commission_rules'][0]['tiers'][0]['value'], '-0.2')
        self.assertIn('-0.2', evidence.render_markdown(report))
        self.assertIsNone(report['commission_cost_USD'])

    def test_failed_margin_is_not_zero_and_reported_zero_is_not_no_margin(self):
        self.manifest = fixtures(self.root, cost=cost_payloads(failed_margin=('buy',)))
        report = self.build(); rows = {r['side']: r for r in report['costs']['margin_factors']}
        self.assertEqual(rows['buy']['status'], 'query_failed'); self.assertIsNone(rows['buy']['initial_rate'])
        self.assertEqual(rows['sell']['initial_rate'], '1.0')
        self.assertIsNone(report['margin_requirement_USD'])

    def test_stopped_or_partial_metadata_does_not_get_completed(self):
        data = metadata_payloads()[:4] + ['S\t7\t2']
        self.manifest = fixtures(self.root, metadata=data)
        report = self.build()
        self.assertEqual(report['metadata']['capture_status'], 'stopped')
        self.assertTrue(report['metadata']['pending_attempt'])
        self.assertEqual(report['metadata']['properties'], [])

    def test_no_quotes_is_missing_coverage_not_zero_spread(self):
        self.manifest = fixtures(self.root, quote_count=0)
        report = self.build()
        self.assertEqual(report['quotes']['observations'], 0)
        self.assertIsNone(report['quotes']['window'])
        self.assertIsNone(report['quotes']['spread_min_price_units'])

    def test_raw_clock_difference_is_preserved_without_age_or_shift(self):
        report = self.build()
        self.assertEqual(report['metadata']['clock_groups'][0]['server_minus_computer_gmt_seconds'], 10800)
        self.assertEqual(report['costs']['clock_groups'][0]['local_minus_computer_gmt_seconds'], 7200)
        self.assertIsNone(report['quotes']['source_age'])
        self.assertIsNone(report['source_age'])
        self.assertIn('10800', evidence.render_markdown(report))

    def test_valid_wire_change_with_old_manifest_hash_rejected(self):
        file = self.manifest['sources'][2]['files'][0]
        (self.root/file['path']).write_bytes(cost_encode(cost_payloads(rules=0)))
        with self.assertRaisesRegex(ValueError, 'hash_mismatch'): self.build()

    def test_bad_wire_cannot_be_admitted_by_updating_its_hash(self):
        file = self.manifest['sources'][2]['files'][0]
        data = (self.root/file['path']).read_bytes().replace(b'FXDL_COST128', b'FXDL_COST999')
        (self.root/file['path']).write_bytes(data);file['sha256'] = hashlib.sha256(data).hexdigest()
        with self.assertRaises(ValueError): self.build()

    def test_unexpected_manifest_fields_cannot_override_policy(self):
        for field in ('orders_available', 'market_data_qualified', 'commission_cost_USD'):
            manifest = deepcopy(self.manifest);manifest[field] = True
            with self.assertRaises(ValueError): self.build(manifest)
        manifest = deepcopy(self.manifest);manifest['sources'][0]['account_identifier'] = 'private'
        with self.assertRaises(ValueError): self.build(manifest)

    def test_roles_counts_order_and_file_duplicates_rejected(self):
        cases = []
        m = deepcopy(self.manifest);m['sources'].reverse();cases.append(m)
        m = deepcopy(self.manifest);m['sources'][0]['id'] = 'costs128';cases.append(m)
        m = deepcopy(self.manifest);m['sources'].pop();cases.append(m)
        m = deepcopy(self.manifest);m['sources'][1]['files'] *= 2;cases.append(m)
        m = deepcopy(self.manifest);m['sources'][0]['files'] *= 2;cases.append(m)
        for manifest in cases:
            with self.assertRaises(ValueError): self.build(manifest)

    def test_path_escape_arbitrary_file_and_windows_paths_rejected(self):
        for path in ('../credentials', '/etc/passwd', 'data/../secret', 'C:/private',
                     'data\\forward-capture-112\\file', 'data/cost-probe-128-native/other/Costs128.txt'):
            m = deepcopy(self.manifest);m['sources'][0]['files'][0]['path'] = path
            with self.assertRaises(ValueError): self.build(m)

    def test_leaf_and_ancestor_symlinks_rejected(self):
        entry = self.manifest['sources'][2]['files'][0];p = self.root/entry['path']
        saved = self.root/'saved';saved.write_bytes(p.read_bytes());p.unlink();p.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.build()
        p.unlink();p.write_bytes(saved.read_bytes())
        parent = p.parent;renamed = parent.with_name(parent.name+'-moved');parent.rename(renamed);parent.symlink_to(renamed, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.build()

    def test_missing_oversize_and_bad_digest_rejected(self):
        entry = self.manifest['sources'][2]['files'][0];p = self.root/entry['path']
        p.unlink()
        with self.assertRaises(ValueError): self.build()
        p.write_bytes(b'x'*65537)
        with self.assertRaisesRegex(ValueError, 'size'): self.build()
        p.write_bytes(cost_encode(cost_payloads()));entry['sha256'] = 'A'*64
        with self.assertRaises(ValueError): self.build()

    def test_run_folder_origin_cannot_be_mislabeled(self):
        entry = self.manifest['sources'][2]['files'][0];old = self.root/entry['path']
        entry['path'] = entry['path'].replace(str(SECOND), str(SECOND+1))
        new = self.root/entry['path'];new.parent.mkdir(parents=True);new.write_bytes(old.read_bytes())
        with self.assertRaisesRegex(ValueError, 'run_origin'): self.build()

    def test_json_manifest_duplicate_keys_constants_and_size_rejected(self):
        path = self.root/'manifest.json'
        for data in (b'{"schema":1,"schema":2}', b'{"x":NaN}', b'\xff', b'x'*65537):
            path.write_bytes(data)
            with self.assertRaises(ValueError): evidence.load_manifest(path)

    def test_cli_json_markdown_and_generic_errors_do_not_modify_inputs(self):
        path = self.root/'manifest.json';path.write_text(json.dumps(self.manifest))
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        for fmt in ('json', 'markdown'):
            run = subprocess.run([sys.executable, str(ROOT/'scripts/evidence-summary-129.py'), str(path),
                                  '--root', str(self.root), '--format', fmt], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0);self.assertEqual(run.stderr, '')
            self.assertIn('evidence', run.stdout.lower())
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        path.write_bytes(b'private_identifier')
        run = subprocess.run([sys.executable, str(ROOT/'scripts/evidence-summary-129.py'), str(path)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1);self.assertNotIn('private_identifier', run.stdout+run.stderr)

    def test_quote_segments_from_different_runs_rejected(self):
        self.manifest = fixtures(self.root, quote_count=121)
        entry = self.manifest['sources'][0]['files'][1];old = self.root/entry['path']
        entry['path'] = entry['path'].replace('-1-1/', '-2-1/')
        new = self.root/entry['path'];new.parent.mkdir(parents=True);new.write_bytes(old.read_bytes())
        with self.assertRaisesRegex(ValueError, 'run_order'): self.build()

    def test_empty_final_quote_segment_retains_partial_evidence(self):
        self.manifest = fixtures(self.root, quote_count=121)
        entry = self.manifest['sources'][0]['files'][1]
        (self.root/entry['path']).write_bytes(b'');entry['sha256'] = hashlib.sha256(b'').hexdigest()
        report = self.build()
        self.assertEqual(report['quotes']['observations'], 120)
        self.assertEqual(report['quotes']['capture_status'], 'incomplete')
        self.assertTrue(report['quotes']['truncated_tail'])
