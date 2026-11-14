"""Invented fixtures only; no terminal, feed, market evaluation or orders."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import forward_eligibility_134 as eligibility
from forex_demo_lab.paired_replay_133 import canonical, digest, DENIED
from test_paired_capture_132 import encode as pair_encode, fixture as pair_fixture, SECOND as PAIR_SECOND
from test_paired_replay_133 import sparse
from test_metadata_probe_127 import encode as metadata_encode, fixture_payloads, SECOND as CONTEXT_SECOND
from test_cost_probe_128 import encode as cost_encode, fixture as cost_fixture

ROOT = Path(__file__).resolve().parents[1]


def inputs(root, quote=None, metadata=None, costs=None, kind='invented_fixture', runs=1):
    root = Path(root)
    quote = pair_encode(pair_fixture(kind=kind)) if quote is None else quote
    metadata = metadata_encode(fixture_payloads(kind=kind)) if metadata is None else metadata
    costs = cost_encode(cost_fixture(rules=0, kind=kind)) if costs is None else costs
    entries = []
    for index in range(1, runs + 1):
        path = f'data/paired-recorder-132-native/Run132-{PAIR_SECOND}-{index}-1000/Paired132.txt'
        target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(quote)
        entries.append(dict(id=f'run{index:03d}', path=path, sha256=digest(quote)))
    quote_manifest = root / 'config/paired-replay-133.json'; quote_manifest.parent.mkdir(exist_ok=True)
    quote_manifest.write_bytes(canonical(dict(schema='paired_replay133_v1_manifest', runs=entries)))
    context = []
    for key, code, name, raw in [('metadata127', 127, 'Metadata127.txt', metadata), ('costs128', 128, 'Costs128.txt', costs)]:
        folder = 'metadata-probe-127-native' if code == 127 else 'cost-probe-128-native'
        path = f'data/{folder}/Run{code}-{CONTEXT_SECOND}-1-1000/{name}'
        target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        context.append(dict(id=key, path=path, sha256=digest(raw)))
    return dict(schema=eligibility.SCHEMA + '_manifest', quote_manifest=dict(
                path='config/paired-replay-133.json', sha256=digest(quote_manifest.read_bytes())), context=context)


def assess(root, manifest):
    return eligibility.assess(root, canonical(manifest))


class ForwardEligibility134Tests(unittest.TestCase):
    def test_span_boundaries_are_geometry_and_never_qualified_bars(self):
        hour = eligibility.HOUR_US
        for span, expected in ((0, 0), (hour - 1, 0), (hour, 1), (2 * hour - 1, 1), (201 * hour, 201)):
            result = eligibility.span_bounds(220, span + 220)
            self.assertEqual(result['recorded_marker_span_us'], span)
            self.assertEqual(result['maximum_fully_contained_one_hour_intervals'], expected)
            self.assertEqual(result['qualified_aligned_h1_bars'], 0)
            self.assertFalse(result['UTC_alignment_established'])
        for first, last in ((True, 1), (0, False), (-1, 2), (2, 1), (0, 2**64), (0.0, 1)):
            with self.assertRaises(ValueError): eligibility.span_bounds(first, last)

    def test_pilot_counts_partitions_and_no_statistical_or_collection_claim(self):
        plan = eligibility.pilot_plan()
        self.assertEqual((plan['warmup_observed_closed_h1_bars'], plan['development_observed_closed_h1_bars'],
                          plan['untouched_validation_observed_closed_h1_bars'], plan['total_observed_closed_h1_bars']), (201, 480, 480, 1161))
        self.assertFalse(plan['sample_size_sufficiency_established']); self.assertFalse(plan['collection_authorized'])
        self.assertTrue(plan['validation_frozen_before_development_results']); self.assertFalse(plan['development_uses_validation_prices'])
        self.assertFalse(plan['interpolated_hours_count']); self.assertFalse(plan['final_partial_hours_count'])
        self.assertIsNone(plan['collection_dates']); self.assertEqual(plan['November_December2026'], 'reserved_untouched')
        plan['candidates'].clear(); self.assertEqual(len(eligibility.pilot_plan()['candidates']), 4)

    def test_separate_runs_preserve_gaps_and_raw_offsets_without_warmup_join(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp, quote=sparse([0, 5_000_000, 6_000_000]), runs=2)
            report = assess(temp, manifest)
            self.assertEqual(report['native_input_files'], 4); self.assertIsNone(report['combined_continuous_history_hours'])
            self.assertEqual(report['qualified_aligned_h1_bars'], 0)
            for run in report['runs']:
                self.assertEqual(run['coverage']['recorded_marker_span_us'], 6_000_000)
                self.assertEqual(run['replay']['sampling_gap_count'], 1)
                self.assertEqual(run['replay']['sampling_gaps'][0]['quote_receipt_gap_us'], 5_000_000)
                self.assertEqual(run['raw_server_minus_computer_gmt_seconds_min'], 10800)
                self.assertEqual(run['raw_server_minus_computer_gmt_seconds_max'], 10800)
                self.assertFalse(run['raw_offset_applied']); self.assertIsNone(run['source_age_ms_bounds'])
                self.assertEqual(run['qualified_warmup_bars_shortfall'], 201)

    def test_unfinished_pair_and_empty_prefix_do_not_manufacture_coverage(self):
        for rows, unpaired in ((pair_fixture()[:1], 0), (pair_fixture()[:5] + ['S\t13\t2'], 1)):
            with tempfile.TemporaryDirectory() as temp:
                report = assess(temp, inputs(temp, quote=pair_encode(rows)))
                run = report['runs'][0]
                self.assertEqual(run['replay']['packets_committed'], 0)
                self.assertEqual(run['replay']['quarantined_quotes'], unpaired)
                self.assertIsNone(run['coverage']['recorded_marker_span_us'])
                self.assertEqual(run['coverage']['maximum_fully_contained_one_hour_intervals'], 0)
                self.assertFalse(report['paper_evaluation_available'])

    def test_repeated_snapshot_duration_does_not_establish_age(self):
        with tempfile.TemporaryDirectory() as temp:
            report = assess(temp, inputs(temp, quote=pair_encode(pair_fixture(repeated=True))))
            run = report['runs'][0]
            self.assertEqual(run['replay']['adjacent_repeated_snapshots'], 2)
            self.assertEqual(run['longest_observed_repeat_span_us'], 2_000_000)
            self.assertFalse(run['repeat_span_is_quote_age']); self.assertIsNone(report['source_age'])

    def test_empty_failed_reported_rules_and_incomplete_costs_stay_distinct(self):
        cases = [(cost_fixture(rules=0), 'reported_empty'),
                 (cost_fixture(returned=-1, commission_error=4303), 'query_failed'),
                 (cost_fixture(rules=1), 'reported_rules'), (cost_fixture()[:1], 'incomplete')]
        for rows, state in cases:
            with tempfile.TemporaryDirectory() as temp:
                report = assess(temp, inputs(temp, costs=cost_encode(rows)))
                cost = report['context'][1]
                self.assertEqual(cost['commission_state'], state)
                self.assertIsNone(cost['commission_cost_USD']); self.assertIsNone(cost['margin_requirement_USD'])
                self.assertFalse(cost['reported_empty_means_zero_total_cost'])
                self.assertEqual(next(r['status'] for r in report['requirements'] if r['key'] == 'costs_and_contract'), 'incomplete')
                if state == 'reported_rules': self.assertEqual(cost['commission_rules'][0]['tiers'][0]['value'], '-0.2')

    def test_failed_metadata_zero_margin_and_weekly_template_are_not_contract(self):
        rows = fixture_payloads(failed=('account_leverage', 'point'), sessions=0)
        with tempfile.TemporaryDirectory() as temp:
            report = assess(temp, inputs(temp, metadata=metadata_encode(rows), costs=cost_encode(cost_fixture(failed_margin=('buy',)))))
            meta, cost = report['context']
            by = {r['key']: r for r in meta['properties']}
            self.assertIsNone(by['account_leverage']['value']); self.assertIsNone(by['point']['value'])
            self.assertFalse(meta['weekly_template_is_verified_calendar']); self.assertFalse(meta['dollar_swap_or_margin_inferred'])
            self.assertIsNone(cost['margin_factors'][0]['initial_rate'])
            self.assertFalse(report['cross_run_contract_established']); self.assertFalse(report['model_assumptions_applied_to_native_data'])
            self.assertEqual(report['frozen_model_assumptions']['leverage'], 30)

    def test_reported_leverage_does_not_overwrite_frozen_model_or_scenarios(self):
        rows = fixture_payloads()
        for index, row in enumerate(rows):
            fields = row.split('\t')
            if fields[0] == 'I' and fields[2] == 'account_leverage':
                fields[11] = '10'; rows[index] = '\t'.join(fields)
        with tempfile.TemporaryDirectory() as temp:
            report = assess(temp, inputs(temp, metadata=metadata_encode(rows)))
            leverage = next(r['value'] for r in report['context'][0]['properties'] if r['key'] == 'account_leverage')
            self.assertEqual(leverage, 10); self.assertEqual(report['frozen_model_assumptions']['leverage'], 30)
            self.assertEqual(report['frozen_cost_scenarios']['base']['config']['commission_per_lot_round_turn'], 7)
            self.assertEqual(report['frozen_cost_scenarios']['adverse']['config']['commission_per_lot_round_turn'], 10)
            self.assertFalse(report['financial_model_changed'])

    def test_market_headers_cannot_admit_data_or_construct_financial_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp, kind='market_declared')
            with patch('forex_demo_lab.tick_simulation.TickSimulator.__init__', side_effect=AssertionError('engine constructed')):
                report = assess(temp, manifest)
            self.assertEqual(report['declared_kind'], 'market_declared')
            for key, expected in DENIED.items(): self.assertEqual(report[key], expected)
            self.assertFalse(report['implementation_grants_admission']); self.assertFalse(report['profitability_established'])
            self.assertFalse(report['collection_authorized']); self.assertEqual(report['financial_engine_events'], 0)
            self.assertEqual(report['pilot_plan']['October2026'], 'quarantined')
            self.assertEqual(report['assessment'], 'not_ready_for_fixed_h1_evaluation')

    def test_manifest_rejects_unknown_fields_including_asserted_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp)
            invalid = [dict(manifest, market_data_qualified=True), dict(manifest, schema='other'),
                       dict(manifest, context=[]), dict(manifest, context=manifest['context'][::-1])]
            for field, value in [('path', '../config/paired-replay-133.json'), ('path', True), ('sha256', 'F' * 64)]:
                changed = deepcopy(manifest); changed['quote_manifest'][field] = value; invalid.append(changed)
            for value in invalid:
                with self.assertRaises(ValueError): assess(temp, value)
            for raw in (b'{"schema":1,"schema":1}', b'[]', b'{"x":NaN}', b'\xff', b'x' * 65_537):
                with self.assertRaises(ValueError): eligibility.assess(temp, raw)

    def test_context_paths_fields_hashes_order_and_header_origin_are_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp)
            for field, value in [('path', '../Metadata127.txt'), ('path', '/tmp/Metadata127.txt'),
                                 ('sha256', '0' * 64), ('id', 'costs128')]:
                changed = deepcopy(manifest); changed['context'][0][field] = value
                with self.assertRaises(ValueError): assess(temp, changed)
            changed = deepcopy(manifest); changed['context'][0]['producer_authenticated'] = True
            with self.assertRaises(ValueError): assess(temp, changed)
            changed = deepcopy(manifest)
            newpath = changed['context'][0]['path'].replace('-1000/', '-1001/')
            newfile = Path(temp) / newpath; newfile.parent.mkdir(); newfile.write_bytes((Path(temp) / changed['context'][0]['path']).read_bytes())
            changed['context'][0]['path'] = newpath
            with self.assertRaisesRegex(ValueError, 'context_origin'): assess(temp, changed)

    def test_changed_wire_with_new_hash_still_rejects_and_mixed_kind_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp); target = Path(temp) / manifest['context'][1]['path']
            raw = target.read_bytes().replace(b'commissions', b'commissionx', 1)
            target.write_bytes(raw); manifest['context'][1]['sha256'] = digest(raw)
            with self.assertRaises(ValueError): assess(temp, manifest)
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp, costs=cost_encode(cost_fixture(kind='market_declared')))
            with self.assertRaisesRegex(ValueError, 'mixed_provenance'): assess(temp, manifest)

    def test_symlink_and_oversize_input_reject_before_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp); target = Path(temp) / manifest['context'][0]['path']
            original = target.read_bytes(); target.unlink(); other = Path(temp) / 'other'; other.write_bytes(original); target.symlink_to(other)
            with self.assertRaisesRegex(ValueError, 'symlink'): assess(temp, manifest)
            target.unlink(); target.write_bytes(b'x' * (eligibility.metadata.MAX_BYTES + 1))
            with self.assertRaises(ValueError): assess(temp, manifest)
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp); parent = Path(temp) / 'config'; parent.rename(Path(temp) / 'config-original'); parent.symlink_to(Path(temp) / 'config-original', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'): assess(temp, manifest)

    def test_deterministic_CLI_library_and_read_only_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = inputs(temp); raw = canonical(manifest)
            path = Path(temp) / 'manifest.json'; path.write_bytes(raw)
            before = {str(p.relative_to(temp)): digest(p.read_bytes()) for p in Path(temp).rglob('*') if p.is_file()}
            report = eligibility.assess(temp, raw); self.assertEqual(eligibility.assess(temp, raw), report)
            for fmt in ('json', 'markdown'):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/forward-eligibility-134.py'),
                                         '--root', temp, '--manifest', str(path), '--format', fmt],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                if fmt == 'json': self.assertEqual(json.loads(result.stdout), report)
                else: self.assertEqual(result.stdout, eligibility.markdown(report))
            after = {str(p.relative_to(temp)): digest(p.read_bytes()) for p in Path(temp).rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            manifest['quote_manifest']['sha256'] = '0' * 64; path.write_bytes(canonical(manifest))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/forward-eligibility-134.py'),
                                     '--root', temp, '--manifest', str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2); self.assertEqual(result.stdout, ''); self.assertNotIn(temp, result.stderr)


if __name__ == '__main__':
    unittest.main()
