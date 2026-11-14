"""Invented136 inputs only; no fresh feed, broker or strategy evaluation."""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import coverage_137 as coverage
from forex_demo_lab.paired_replay_133 import DENIED, canonical, digest
from test_context_recorder_136 import SECOND, change, encode, fixture

ROOT = Path(__file__).resolve().parents[1]


def inputs(root, raws=None):
    raws = [encode(fixture())] if raws is None else raws
    entries = []
    for i, raw in enumerate(raws):
        header = raw.split(b'\r\n', 1)[0].split(b'\t')
        relative = f'data/context-recorder-136-native/Run136-{int(header[4])}-{i}-{int(header[5])}/Context136.txt'
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        entries.append(dict(id=f'run{i + 1}', path=relative, sha256=digest(raw)))
    return dict(schema=coverage.SCHEMA + '_manifest', runs=entries)


class Coverage137Tests(unittest.TestCase):
    def test_geometry_exact_hour_and_partial_hour_never_qualify(self):
        for span, bound in [(coverage.HOUR_US - 1, 0), (coverage.HOUR_US, 1)]:
            c = coverage.assess_bytes(encode(fixture(polls=2, step=span)))['coverage']
            self.assertEqual(c['marker_span_us'], span)
            self.assertEqual(c['geometric_h1_upper_bound'], bound)
            self.assertEqual(c['maximum_h1_intervals_in_one_segment'], 0)
            self.assertEqual(c['qualified_aligned_h1_bars'], 0)
            self.assertEqual(c['qualified_warmup_shortfall'], 201)
            self.assertFalse(c['UTC_alignment_established'])

    def test_gap_boundary_is_strict_and_separates_segments(self):
        for step, gaps, segments in [(2_000_000, 0, 1), (2_000_001, 2, 3)]:
            c = coverage.assess_bytes(encode(fixture(step=step)))['coverage']
            self.assertEqual(c['quote_before_gaps_over2s'], gaps)
            self.assertEqual(c['segment_count'], segments)
            self.assertEqual(c['maximum_quote_before_gap_us'], step)

    def test_all_identical_and_trailing_groups_are_observations_not_age(self):
        r = coverage.assess_bytes(encode(fixture(polls=40, repeats=True)))
        c = r['coverage']
        self.assertEqual(c['paired_quote_observations'], 40)
        self.assertEqual(c['distinct_recorded_snapshots'], 1)
        self.assertEqual(c['adjacent_repeated_snapshots'], 39)
        self.assertEqual(c['longest_identical_quote_before_span_us'], 39_000_000)
        self.assertEqual(c['trailing_identical_group']['last_poll'], 40)
        self.assertFalse(c['repeat_span_is_source_age']); self.assertIsNone(r['source_age'])
        self.assertFalse(c['active_session_established'])
        self.assertFalse(c['distinct_snapshots_are_market_tick_count'])

    def test_repeat_group_spanning_gap_does_not_claim_continuous_sampling(self):
        c = coverage.assess_bytes(encode(fixture(repeats=True, step=5_000_000)))['coverage']
        self.assertEqual(c['identical_snapshot_group_count'], 1)
        self.assertTrue(c['identical_snapshot_groups'][0]['contains_sampling_gap'])
        self.assertEqual(c['segment_count'], 3)

    def test_no_pair_and_unpaired_last_quote_do_not_extend_coverage(self):
        empty = coverage.assess_bytes(encode(fixture(polls=0)))['coverage']
        self.assertIsNone(empty['marker_span_us']); self.assertEqual(empty['segment_count'], 0)
        rows = fixture()
        index = [i for i, row in enumerate(rows) if row.startswith('T\t')][-1]
        sequence = int(rows[index].split('\t')[1])
        r = coverage.assess_bytes(encode(rows[:index + 1] + [f'S\t13\t{sequence}\t2']))
        c = r['coverage']
        self.assertEqual(c['paired_quote_observations'], 2)
        self.assertEqual(c['unpaired_quote_observations'], 1)
        self.assertEqual(c['marker_span_us'], 1_000_000)
        self.assertEqual(r['quarantined_poll_rows'], 2)
        self.assertEqual(c['segments'][0]['last_poll'], 2)

    def test_pending_attempt_and_truncated_context_cannot_make_quotes(self):
        rows = fixture()
        r = coverage.assess_bytes(encode(rows[:3]))
        self.assertTrue(r['pending_attempt']); self.assertTrue(r['incomplete_context'])
        self.assertEqual(r['coverage']['paired_quote_observations'], 0)
        self.assertEqual(r['complete_context_count'], 0)

    def test_source_reversal_and_same_timestamp_changed_payload_break_geometry(self):
        for reversed_time in (True, False):
            rows = fixture()
            first = next(row.split('\t') for row in rows if row.startswith('T\t'))
            source = int(first[11]) - int(reversed_time)
            change(rows, 'T', 11, source, occurrence=1)
            change(rows, 'T', 12, source * 1000 + 123, occurrence=1)
            change(rows, 'T', 16, 1, occurrence=1)
            c = coverage.assess_bytes(encode(rows))['coverage']
            self.assertEqual(c['segment_count'], 2)
            self.assertEqual(c['source_reversals'], int(reversed_time))
            self.assertEqual(c['same_source_time_changed_payload'], int(not reversed_time))

    def test_detail_truncation_does_not_hide_maxima_or_final_groups(self):
        rows = fixture(polls=400, step=3_000_000)
        for i in range(1, 400, 2):
            source = SECOND + 10800 + i - 1
            change(rows, 'T', 11, source, occurrence=i)
            change(rows, 'T', 12, source * 1000 + 123, occurrence=i)
        # Make the final group longer than every group in the first128 details.
        outcomes = [i for i, row in enumerate(rows) if row.startswith(('C\t', 'T\t'))]
        for index in outcomes[-3:]:
            fields = rows[index].split('\t')
            for field in (3, 4, 5): fields[field] = str(int(fields[field]) + 2)
            for field in (6, 7, 8): fields[field] = str(int(fields[field]) + 2_000_000)
            rows[index] = '\t'.join(fields)
        c = coverage.assess_bytes(encode(rows))['coverage']
        self.assertEqual(c['identical_snapshot_group_count'], 200)
        self.assertEqual(len(c['identical_snapshot_groups']), coverage.DETAIL_LIMIT)
        self.assertTrue(c['identical_group_details_truncated'])
        self.assertEqual(c['trailing_identical_group']['last_poll'], 400)
        self.assertEqual(c['longest_identical_quote_before_span_us'], 5_000_000)
        self.assertEqual(c['maximum_quote_before_gap_us'], 5_000_000)
        self.assertEqual(c['segment_count'], 400)
        self.assertTrue(c['segment_details_truncated'])
        self.assertEqual(c['quote_before_gaps_over2s'], 399)

    def test_empty_failed_and_reported_commissions_do_not_become_total_costs(self):
        for kwargs, state in [({}, 'reported_empty'), ({'commission_failed': True}, 'query_failed'),
                              ({'rules': 1}, 'reported_rules')]:
            r = coverage.assess_bytes(encode(fixture(**kwargs)))
            self.assertEqual(r['commission_states'], [state])
            self.assertIsNone(r['applicable_total_costs_USD'])
            self.assertFalse(r['context_is_atomic_contract'])

    def test_separate_runs_do_not_join_or_construct_financial_engine(self):
        with tempfile.TemporaryDirectory() as temp:
            m = inputs(temp, [encode(fixture()), encode(fixture(seconds=SECOND + 86400, kind='invented_fixture'))])
            with patch('forex_demo_lab.tick_simulation.TickSimulator.__init__', side_effect=AssertionError('engine')):
                r = coverage.assess(temp, canonical(m))
            self.assertEqual(len(r['runs']), 2); self.assertFalse(r['runs_joined'])
            self.assertIsNone(r['combined_continuous_history_hours'])
            self.assertEqual(r['qualified_aligned_h1_bars'], 0)
            self.assertEqual(r['November_December2026'], 'reserved_untouched')
            self.assertFalse(r['collection_authorized']); self.assertFalse(r['profitability_established'])
            self.assertEqual(r['financial_engine_events'], 0)
            for key, value in DENIED.items(): self.assertEqual(r[key], value)

    def test_invalid_wire_fresh_hash_and_market_header_cannot_bypass_reader(self):
        with tempfile.TemporaryDirectory() as temp:
            m = inputs(temp, [encode(fixture(kind='market_declared'))])
            r = coverage.assess(temp, canonical(m))
            self.assertFalse(r['market_data_qualified']); self.assertTrue(r['retrospective_diagnostics_only'])
            rows = fixture(); change(rows, 'T', 13, '0000000000000000')
            m = inputs(temp, [encode(rows)])
            with self.assertRaises(ValueError): coverage.assess(temp, canonical(m))

    def test_strict_manifest_rejects_qualification_flags_duplicates_and_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            m = inputs(temp)
            invalid = [dict(m, market_data_qualified=True), dict(m, runs=[]), dict(m, runs=m['runs'] * 2),
                       dict(m, schema='other')]
            for field, value in [('path', '../secret'), ('path', True), ('sha256', 'f' * 64), ('id', 'name with spaces')]:
                changed = deepcopy(m); changed['runs'][0][field] = value; invalid.append(changed)
            for bad in invalid:
                with self.assertRaises(ValueError): coverage.assess(temp, canonical(bad))
            with self.assertRaises(ValueError): coverage.assess(temp, b'{"schema":1,"schema":2,"runs":[]}')

    def test_origin_mixed_provenance_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            m = inputs(temp, [encode(fixture()), encode(fixture(seconds=SECOND + 86400, kind='market_declared'))])
            with self.assertRaises(ValueError): coverage.assess(temp, canonical(m))
            m = inputs(temp); path = Path(temp) / m['runs'][0]['path']
            wrong = path.parent.with_name(f'Run136-{SECOND + 1}-0-1000'); path.parent.rename(wrong)
            m['runs'][0]['path'] = str((wrong / path.name).relative_to(temp))
            with self.assertRaises(ValueError): coverage.assess(temp, canonical(m))
            target = wrong / path.name; saved = wrong / 'saved'; target.rename(saved); target.symlink_to(saved)
            with self.assertRaises(ValueError): coverage.assess(temp, canonical(m))

    def test_cli_is_deterministic_read_only_and_failure_does_not_disclose_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            m = inputs(temp); manifest = Path(temp) / 'manifest.json'; manifest.write_bytes(canonical(m))
            source = Path(temp) / m['runs'][0]['path']; before = source.read_bytes()
            command = [sys.executable, str(ROOT / 'scripts/coverage-137.py'), '--root', temp, '--manifest', str(manifest)]
            first = subprocess.run(command, capture_output=True, check=True)
            second = subprocess.run(command, capture_output=True, check=True)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(json.loads(first.stdout), coverage.assess(temp, canonical(m)))
            self.assertEqual(source.read_bytes(), before)
            manifest.write_bytes(canonical(dict(m, private_do_not_print='private_do_not_print')))
            bad = subprocess.run(command, capture_output=True)
            self.assertEqual(bad.returncode, 2); self.assertFalse(bad.stdout)
            self.assertNotIn(b'private_do_not_print', bad.stderr)


if __name__ == '__main__':
    unittest.main()
