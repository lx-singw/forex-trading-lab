"""Invented interval-contract checks; no native source or financial engine."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import fresh_input_135 as contract
from forex_demo_lab.paired_replay_133 import canonical, digest, DENIED

ROOT = Path(__file__).resolve().parents[1]
POLICY = canonical(contract.expected_policy())


def example(name='bounded_assumptions'):
    return deepcopy(contract.invented_cases()[name])


def execute(fixture):
    return contract.Replay(canonical(fixture), POLICY).run()


def quote_result(fixture):
    return [v for v in execute(fixture)['verdicts'] if v['type'] == 'quote'][-1]


def renumber(fixture):
    for index, event in enumerate(fixture['events'], 1): event['sequence'] = index
    return fixture


class FreshInput135Tests(unittest.TestCase):
    def test_positive_bounds_are_exact_but_all_financial_admission_stays_off(self):
        fixture = example(); q = quote_result(fixture); utc = fixture['events'][0]['receipt_utc_us'][0]
        self.assertEqual(q['availability_utc_us'], [utc + 1_000_000, utc + 1_001_000])
        self.assertEqual(q['source_utc_us'], [utc + 900_000] * 2)
        self.assertEqual(q['estimated_age_bounds_us'], [100_000, 101_000])
        self.assertEqual(q['receipt_h1_index'], utc // contract.HOUR)
        self.assertTrue(q['hypothetical_input_usable']); self.assertEqual(q['reasons'], [])
        self.assertEqual(q['receipt_basis'], 'declared_assumption')
        self.assertFalse(q['full_strategy_entry_permission'])
        for key, value in DENIED.items(): self.assertEqual(q[key], value)

    def test_outward_drift_and_offset_uncertainty_use_integer_intervals(self):
        fixture = example(); clock, quote = fixture['events'][0], fixture['events'][-1]
        utc = clock['receipt_utc_us'][0]; offset = clock['source_to_utc_us'][0]
        clock.update(receipt_utc_us=[utc - 10, utc + 20], receipt_drift_ppm=1,
                     source_to_utc_us=[offset - 50, offset + 100])
        quote.update(observed_us=1, acquired_us=0, source_msc=(utc - offset) // 1000, post_marker_delay_us=[0, 1])
        q = quote_result(fixture)
        self.assertEqual(q['availability_utc_us'], [utc - 10, utc + 23])
        self.assertEqual(q['source_utc_us'], [utc - 50, utc + 100])
        self.assertEqual(q['estimated_age_bounds_us'], [-110, 73])
        self.assertEqual(q['age_state'], 'possibly_future'); self.assertFalse(q['hypothetical_input_usable'])

    def test_exact_age_limits_and_uncertain_stale_future_classification(self):
        for age, expected in ((0, 'within_declared_bounds'), (2_000_000, 'within_declared_bounds'),
                              (2_001_000, 'definitely_stale'), (-1000, 'definitely_future')):
            fixture = example(); clock, quote = fixture['events'][0], fixture['events'][-1]
            utc = clock['receipt_utc_us'][0]; offset = clock['source_to_utc_us'][0]
            quote.update(source_msc=(utc + quote['observed_us'] - age - offset) // 1000, post_marker_delay_us=[0, 0])
            q = quote_result(fixture)
            self.assertEqual(q['estimated_age_bounds_us'], [age, age]); self.assertEqual(q['age_state'], expected)
        self.assertEqual(quote_result(example('uncertain_age_limit'))['age_state'], 'possibly_stale')
        fixture = example(); utc = fixture['events'][0]['receipt_utc_us'][0]
        fixture['events'][0]['receipt_utc_us'] = [utc - 100_001, utc]
        self.assertEqual(quote_result(fixture)['age_state'], 'possibly_future')

    def test_unknown_receipt_source_and_post_marker_delay_never_become_zero_age(self):
        fixtures = [example('unknown_receipt_clock'), example('unknown_post_marker_delay')]
        fixture = example(); fixture['events'][0].update(source_basis='unknown', source_to_utc_us=None, source_label_range_msc=None)
        fixtures.append(fixture)
        for fixture in fixtures:
            q = quote_result(fixture)
            self.assertIsNone(q['estimated_age_bounds_us']); self.assertEqual(q['age_state'], 'unknown')
            self.assertFalse(q['hypothetical_input_usable']); self.assertTrue(q['risk_observation_retained'])

    def test_calibration_terms_and_calendar_expire_at_delivery_horizon(self):
        for context in (0, 1, 2):
            fixture = example(); fixture['events'][context]['valid_for_us'] = 1_000_000
            self.assertFalse(quote_result(fixture)['hypothetical_input_usable'])  # delay upper extends beyond validity
            fixture['events'][-1]['post_marker_delay_us'] = [0, 0]
            self.assertTrue(quote_result(fixture)['hypothetical_input_usable'])   # exact endpoint is inclusive
        self.assertIn('clock_missing_or_expired', quote_result(example('expired_calibration'))['reasons'])
        self.assertIn('terms_missing_or_expired', quote_result(example('expired_terms'))['reasons'])

    def test_source_mapping_scope_does_not_extend_or_transfer(self):
        fixture = example(); source = fixture['events'][-1]['source_msc']
        fixture['events'][0]['source_label_range_msc'] = [source + 1, source + 100]
        q = quote_result(fixture)
        self.assertIn('source_mapping_out_of_scope', q['reasons']); self.assertIsNone(q['estimated_age_bounds_us'])

    def test_invented_measurement_label_cannot_certify_market_evidence(self):
        fixture = example()
        for event in fixture['events']:
            for field in list(event):
                if field.endswith('basis'): event[field] = 'invented_measurement'
        q = quote_result(fixture)
        self.assertTrue(q['hypothetical_input_usable'])
        self.assertEqual(q['receipt_basis'], 'invented_measurement')
        self.assertFalse(q['producer_authenticated']); self.assertFalse(q['source_utc_certified'])
        self.assertEqual(q['evidence_scope'], 'invented_contract_software_check')

    def test_sessions_are_half_open_and_unknown_is_distinct_from_known_closed(self):
        fixture = example(); utc = fixture['events'][0]['receipt_utc_us'][0]
        fixture['events'][2]['sessions_utc_us'] = [[utc, utc + 1_001_000]]
        self.assertEqual(quote_result(fixture)['calendar_state'], 'ambiguous_boundary')
        fixture['events'][2]['sessions_utc_us'][0][1] += 1
        self.assertEqual(quote_result(fixture)['calendar_state'], 'open_under_declared_bounds')
        fixture['events'][2]['sessions_utc_us'] = [[utc - 1, utc + 1_000_000]]
        fixture['events'][-1]['post_marker_delay_us'] = [0, 0]
        self.assertEqual(quote_result(fixture)['calendar_state'], 'closed_under_declared_bounds')
        fixture['events'][2].update(basis='unknown', sessions_utc_us=None)
        self.assertEqual(quote_result(fixture)['calendar_state'], 'unknown')
        self.assertEqual(quote_result(example('declared_closed_session'))['calendar_state'], 'closed_under_declared_bounds')

    def test_hour_boundary_uncertainty_cannot_assign_an_h1_bucket(self):
        fixture = example(); q = fixture['events'][-1]
        utc = fixture['events'][0]['receipt_utc_us'][0]
        at = (utc // contract.HOUR + 1) * contract.HOUR - utc - 500
        offset = fixture['events'][0]['source_to_utc_us'][0]
        q.update(observed_us=at, acquired_us=at - 10, source_msc=(utc + at - 100_000 - offset) // 1000)
        verdict = quote_result(fixture)
        self.assertIn('receipt_hour_ambiguous', verdict['reasons']); self.assertIsNone(verdict['receipt_h1_index'])
        self.assertTrue(verdict['requires_history_review']); self.assertFalse(verdict['hypothetical_input_usable'])

    def test_gap_price_move_stays_visible_to_risk_and_recovery_does_not_grant_entry(self):
        fixture = example('polling_gap')
        fixture['events'][4]['bid_bits'] = '3FF170A3D70A3D71'  # invented1.09 bid after the gap
        report = execute(fixture); quotes = [v for v in report['verdicts'] if v['type'] == 'quote']
        self.assertEqual([v['hypothetical_input_usable'] for v in quotes], [True, False, True])
        self.assertEqual(quotes[1]['quote_marker_gap_us'], 5_000_000)
        self.assertEqual(quotes[1]['original_quote'], fixture['events'][4])
        self.assertTrue(quotes[1]['requires_history_review'])
        self.assertEqual(report['risk_observations_retained'], 3)
        self.assertTrue(all(not v['full_strategy_entry_permission'] for v in quotes))

    def test_repeats_reversals_changed_payload_and_highwater_are_preserved(self):
        fixture = example('polling_gap'); first, second, third = fixture['events'][3:]
        second.update(observed_us=2_000_000, acquired_us=1_999_990, source_msc=first['source_msc'])
        third.update(observed_us=3_000_000, acquired_us=2_999_990, source_msc=first['source_msc'])
        quotes = [v for v in execute(fixture)['verdicts'] if v['type'] == 'quote']
        self.assertEqual([v['repeated_snapshot'] for v in quotes], [False, True, True])
        self.assertEqual(quotes[-1]['age_state'], 'definitely_stale')
        self.assertTrue(quote_result(example('source_reversal'))['source_reversal'])
        self.assertTrue(quote_result(example('same_source_changed_payload'))['same_source_changed_payload'])
        self.assertTrue(quote_result(example('source_reversal'))['source_below_highwater'])

    def test_clock_updates_signal_disjoint_or_unverifiable_bounds_without_rewriting_prior(self):
        fixture = example('clock_discontinuity'); report = execute(fixture)
        self.assertEqual(report['verdicts'][4]['continuity'], 'disjoint_bounds')
        self.assertIn('clock_mapping_disjoint_bounds', report['verdicts'][-1]['history_review_reasons'])
        fixture['events'][0].update(source_basis='unknown', source_to_utc_us=None, source_label_range_msc=None)
        report = execute(fixture)
        self.assertEqual(report['verdicts'][4]['continuity'], 'disjoint_bounds')  # missing source scope cannot hide a known receipt jump
        fixture = example('clock_discontinuity'); utc = fixture['events'][0]['receipt_utc_us'][0]
        fixture['events'][4]['receipt_utc_us'] = [utc + 2_000_000] * 2
        self.assertEqual(execute(fixture)['verdicts'][4]['continuity'], 'bounds_overlap')

    def test_late_context_and_future_suffix_cannot_change_past_verdicts_or_ids(self):
        fixture = example('polling_gap'); terms = fixture['events'].pop(1)
        terms['observed_us'] = 2_000_000
        fixture['events'].insert(3, terms); renumber(fixture)
        first = execute(fixture)
        self.assertIn('terms_missing_or_expired', first['verdicts'][2]['reasons'])
        changed = deepcopy(fixture); changed['events'][3].update(cost_basis='unknown', cost_profile=None)
        second = execute(changed)
        self.assertEqual(first['verdicts'][:3], second['verdicts'][:3])
        changed['events'][-1]['bid_bits'] = '3FF170A3D70A3D71'
        third = execute(changed)
        self.assertEqual(second['verdicts'][:-1], third['verdicts'][:-1])

    def test_bad_event_is_atomic_and_monotonic_reset_requires_a_new_run(self):
        fixture = example(); fixture['events'][2]['sessions_utc_us'] *= 2
        cursor = contract.Replay(canonical(fixture), POLICY)
        cursor.ack(cursor.peek()); cursor.ack(cursor.peek()); before = cursor.checkpoint()
        with self.assertRaises(ValueError): cursor.ack(cursor.peek())
        self.assertEqual(cursor.checkpoint(), before)
        fixture = example('polling_gap'); fixture['events'][4].update(observed_us=999_999, acquired_us=999_998)
        cursor = contract.Replay(canonical(fixture), POLICY)
        for _ in range(4): cursor.ack(cursor.peek())
        before = cursor.checkpoint()
        with self.assertRaisesRegex(ValueError, 'reset_requires_new_run'): cursor.ack(cursor.peek())
        self.assertEqual(cursor.checkpoint(), before)

    def test_peek_copy_ack_order_and_immediate_duplicate_are_idempotent(self):
        cursor = contract.Replay(canonical(example()), POLICY)
        with self.assertRaisesRegex(ValueError, 'not_exhausted'): cursor.report()
        first = cursor.peek(); changed = deepcopy(first); changed['receipt_utc_us'][0] += 1
        with self.assertRaises(ValueError): cursor.ack(changed)
        result = cursor.ack(first); saved = cursor.checkpoint()
        result['continuity'] = 'changed'; duplicate = cursor.ack(first)
        self.assertEqual(duplicate['continuity'], 'initial'); self.assertEqual(cursor.checkpoint(), saved)
        cursor.ack(cursor.peek())
        with self.assertRaises(ValueError): cursor.ack(first)
        cursor.run(); self.assertEqual(cursor.run(), cursor.report())

    def test_every_restart_boundary_rebuilds_context_pending_review_and_results(self):
        for name in ('polling_gap', 'clock_discontinuity', 'unknown_costs'):
            raw = canonical(example(name)); original = contract.Replay(raw, POLICY); expected = contract.Replay(raw, POLICY).run()
            for _ in range(len(example(name)['events']) + 1):
                pending = original.peek(); saved = original.checkpoint()
                restored = contract.Replay.restore(raw, POLICY, saved)
                self.assertEqual(restored.peek(), pending); self.assertEqual(restored.checkpoint(), saved)
                self.assertEqual(restored.run(), expected)
                if pending is not None: original.ack(pending)

    def test_checkpoint_cannot_import_forged_derived_state_or_different_input(self):
        raw = canonical(example()); cursor = contract.Replay(raw, POLICY); cursor.ack(cursor.peek())
        saved = json.loads(cursor.checkpoint())
        mutations = []
        for key, value in [('committed_events', True), ('committed_events', 2), ('causal_prefix_sha256', '0' * 64),
                           ('runtime', {}), ('balance', 10001)]:
            altered = deepcopy(saved); altered['state'][key] = value
            altered['checksum'] = digest(canonical(altered['state'])); mutations.append(canonical(altered))
        mutations += [b'[]', b'{"state":{},"state":{}}', b'x' * 16_385]
        for bad in mutations:
            with self.assertRaises(ValueError): contract.Replay.restore(raw, POLICY, bad)
        other = example(); other['run'] = 2
        with self.assertRaises(ValueError): contract.Replay.restore(canonical(other), POLICY, cursor.checkpoint())

    def test_unknown_values_require_null_and_unreviewed_profiles_reject(self):
        changes = [(0, 'receipt_basis', 'unknown'), (0, 'source_basis', 'unknown'),
                   (1, 'cost_profile', 'zero_cost'), (2, 'basis', 'unknown'), (3, 'delay_basis', 'unknown')]
        for index, field, value in changes:
            fixture = example(); fixture['events'][index][field] = value
            with self.assertRaises(ValueError): execute(fixture)
        fixture = example(); fixture['events'][1].update(contract_basis='unknown', contract_profile=None)
        self.assertIn('contract_or_cost_unknown', quote_result(fixture)['reasons'])

    def test_native_market_headers_policy_overrides_and_schema_faults_reject(self):
        fixture = example()
        for field, value in [('kind', 'market_declared'), ('symbol', 'GBPUSD'), ('run', True), ('events', [])]:
            bad = deepcopy(fixture); bad[field] = value
            with self.assertRaises(ValueError): contract.Replay(canonical(bad), POLICY)
        bad = deepcopy(fixture); bad['orders_available'] = True
        with self.assertRaises(ValueError): contract.Replay(canonical(bad), POLICY)
        for raw in (b'H\tFXDL_PAIRED132_V1\t', b'{"kind":1,"kind":1}', b'{"x":NaN}', b'\xff'):
            with self.assertRaises(ValueError): contract.Replay(raw, POLICY)
        policy = contract.expected_policy(); policy['max_age_us'] += 1
        with self.assertRaisesRegex(ValueError, 'frozen_contract_policy'): contract.Replay(canonical(fixture), canonical(policy))

    def test_invalid_bits_crossed_prices_boolean_times_and_extra_fields_reject(self):
        changes = [('bid_bits', '7FF8000000000000'), ('bid_bits', '0000000000000000'),
                   ('bid_bits', '3FF3333333333333'), ('ask_bits', 'bad'), ('observed_us', True),
                   ('raw_flags', 2**32), ('post_marker_delay_us', [1, 0]), ('sequence', 6)]
        for field, value in changes:
            fixture = example(); fixture['events'][-1][field] = value
            with self.assertRaises(ValueError): execute(fixture)
        fixture = example(); fixture['events'][-1]['account'] = 'unaccepted'
        with self.assertRaises(ValueError): execute(fixture)

    def test_matrix_never_constructs_a_financial_engine_and_retains_all_quotes(self):
        with patch('forex_demo_lab.tick_simulation.TickSimulator.__init__', side_effect=AssertionError('financial engine')):
            for fixture in contract.invented_cases().values():
                report = execute(fixture)
                self.assertEqual(report['risk_observations_retained'], report['quote_observations'])
                self.assertEqual(report['financial_engine_events'], 0); self.assertFalse(report['strategy_evaluated'])
                self.assertTrue(report['measurements_are_synthetic']); self.assertFalse(report['native_capture_conversion_available'])
                for key, value in DENIED.items(): self.assertEqual(report[key], value)

    def test_markdown_case_order_survives_canonical_JSON_roundtrip(self):
        reports = {name: execute(fixture) for name, fixture in contract.invented_cases().items()}
        reloaded = json.loads(json.dumps(reports, sort_keys=True))
        self.assertEqual(contract.markdown(reports), contract.markdown(reloaded))

    def test_cli_and_library_are_deterministic_read_only_and_native_input_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.json'; raw = canonical(example()); path.write_bytes(raw)
            expected = {'input': contract.Replay(raw, (ROOT / 'config/fresh-input-135.json').read_bytes()).run()}
            for fmt in ('json', 'markdown'):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/fresh-input-135.py'), '--input', str(path), '--format', fmt],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                if fmt == 'json': self.assertEqual(json.loads(result.stdout), expected)
                else: self.assertEqual(result.stdout, contract.markdown(expected))
                self.assertEqual(path.read_bytes(), raw)
            bad = example(); bad['kind'] = 'market_declared'; path.write_bytes(canonical(bad))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/fresh-input-135.py'), '--input', str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2); self.assertEqual(result.stdout, ''); self.assertNotIn(temp, result.stderr)


if __name__ == '__main__':
    unittest.main()
