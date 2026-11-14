from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import forward_quality_131 as quality
from forex_demo_lab import forward_capture_111 as forward
from forex_demo_lab import timing_probe_130 as timing
from test_forward_capture_111 import payloads as fp, encode as fe, START
from test_timing_probe_130 import fixture as tp, encode as te, change, bits, SECOND

ROOT = Path(__file__).resolve().parents[1]


def timed(polls=3, repeated=False, kind='invented_fixture', step=1000000):
    rows = tp(polls=polls, repeated=repeated, kind=kind, step=step)
    if polls != 60:
        rows[-1] = f'S\t18\t{polls*3}'
    return rows


def fixtures(root, groups=None, clock_rows=None, count=4, kind='invented_fixture'):
    groups = fe(fp(count, kind=kind)) if groups is None else fe(groups)
    clock_rows = timed(kind=kind) if clock_rows is None else clock_rows
    files = {
        'forward111': [(f'data/forward-capture-112/Run111-{START}-1-1000/{name}', data) for name, data in groups],
        'timing130': [(f'data/timing-probe-130-native/Run130-{SECOND}-1-1000/Timing130.txt', te(clock_rows))],
    }
    manifest = {'schema': quality.SCHEMA, 'sources': []}
    for key in quality.IDS:
        entries = []
        for relative, data in files[key]:
            p = root/relative; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
            entries.append({'path': relative, 'sha256': hashlib.sha256(data).hexdigest()})
        manifest['sources'].append({'id': key, 'files': entries})
    return manifest


def codes(report):
    return {r['code'] for r in report['findings']}


class ForwardQuality131Tests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.root = Path(folder.name); self.manifest = fixtures(self.root)

    def build(self, manifest=None):
        return quality.build_report(self.manifest if manifest is None else manifest, self.root)

    def test_both_formats_report_without_clock_transfer_or_join(self):
        r = self.build(); a, b = [s['quality'] for s in r['sources']]
        self.assertEqual(r['input_files'], 2)
        self.assertEqual(a['quote_outcomes_recorded'], 4); self.assertEqual(b['quote_outcomes_recorded'], 3)
        self.assertEqual(a['paired_clocks']['status'], 'not_recorded')
        self.assertIsNone(a['paired_clocks']['completed_pairs']); self.assertIsNone(a['paired_clocks']['paired_raw_arithmetic'])
        self.assertEqual(b['paired_clocks']['completed_pairs'], 3)
        self.assertEqual(b['paired_clocks']['raw_offset_observations']['time_trade_server_minus_gmt_seconds']['range']['min'], 10800)
        self.assertIn('paired_clocks_not_recorded', codes(a)); self.assertNotIn('paired_clocks_not_recorded', codes(b))
        self.assertFalse(r['source_offsets_transferred_between_runs']); self.assertFalse(r['continuous_history_across_sources'])
        self.assertNotEqual(a['origin_nominal_gmt_seconds'], b['origin_nominal_gmt_seconds'])

    def test_changing_quotes_and_repeat_spans_use_same_meaning(self):
        a = quality.inspect_forward_segments(fe(fp(4)))
        b = quality.inspect_timing_bytes(te(timed(repeated=True)))
        self.assertEqual(a['quote_statistics']['adjacent_identical_snapshots'], 3)
        self.assertEqual(a['quote_statistics']['longest_observed_repeat_span_us'], 1500000)
        self.assertEqual(b['quote_statistics']['adjacent_identical_snapshots'], 2)
        self.assertEqual(b['quote_statistics']['longest_observed_repeat_span_us'], 2000000)
        self.assertFalse(b['quote_statistics']['repeat_span_is_quote_age'])
        changing = quality.inspect_timing_bytes(te(timed()))
        self.assertEqual(changing['quote_statistics']['source_label_advances'], 2)
        self.assertEqual(changing['quote_statistics']['longest_observed_repeat_span_us'], 0)

    def test_actual_and_invented_labels_never_enable_admission(self):
        self.manifest = fixtures(self.root, kind='market_declared')
        report = self.build()
        for r in [report] + [s['quality'] for s in report['sources']]:
            for key in ('producer_authenticated', 'source_utc_certified', 'receipt_utc_certified', 'market_data_qualified',
                        'paper_evaluation_available', 'orders_available', 'real_money_execution_available',
                        'strategy_evaluated', 'profitability_established'):
                self.assertIs(r[key], False, key)
            self.assertIsNone(r['source_age'])
        for s in report['sources']:
            self.assertIn('source_age_unverified', codes(s['quality']))
            self.assertIn('execution_quality_unverified', codes(s['quality']))

    def test_adjacent_reversal_and_highwater_recovery_are_distinct(self):
        rows = timed(polls=4)
        for index, offset in ((10, -2), (16, -1)):
            source = SECOND+10800+offset
            change(rows, index, 11, source); change(rows, index, 12, source*1000+123)
        r = quality.inspect_timing_bytes(te(rows)); stats = r['quote_statistics']
        self.assertEqual(stats['source_label_adjacent_reversals'], 1)
        self.assertEqual(stats['source_labels_below_prior_highwater'], 2)
        self.assertEqual(stats['source_label_advances'], 2)
        self.assertIn('source_label_reversals_observed', codes(r))

    def test_source_reversal_is_reported_for_forward_format_too(self):
        groups = fp(3); source = (START+10800)*1000-1
        change(groups[0], 4, 8, source//1000); change(groups[0], 4, 9, source)
        r = quality.inspect_forward_segments(fe(groups))
        self.assertEqual(r['quote_statistics']['source_label_adjacent_reversals'], 1)
        self.assertEqual(r['quote_statistics']['source_labels_below_prior_highwater'], 1)

    def test_same_timestamp_native_bit_change_and_unknown_flags(self):
        rows = timed(repeated=True)
        change(rows, 10, 15, bits(-0.0)); change(rows, 10, 17, 2**32-1)
        r = quality.inspect_timing_bytes(te(rows))
        self.assertEqual(r['quote_statistics']['same_timestamp_changed_snapshots'], 2)
        self.assertEqual(r['quote_statistics']['adjacent_identical_snapshots'], 0)
        self.assertIn('same_timestamp_changed_snapshots_observed', codes(r))

    def test_receipt_gap_threshold_is_fixed_and_not_source_age(self):
        for interval, expected in ((2000000, 0), (2000001, 2)):
            r = quality.inspect_timing_bytes(te(timed(step=interval)))
            self.assertEqual(r['quote_statistics']['receipt_poll_gaps_over_two_seconds'], expected)
            self.assertEqual(r['fixed_receipt_gap_notice_threshold_us'], 2000000)
            self.assertIsNone(r['source_age'])

    def test_raw_clock_reversal_and_offset_change_are_preserved(self):
        rows = timed(); change(rows, 8, 12, SECOND+7200)
        native = timing.inspect_bytes(te(rows)); r = quality.inspect_timing_bytes(te(rows))
        self.assertEqual(r['paired_clocks']['paired_raw_arithmetic'], native['paired_raw_arithmetic'])
        self.assertIn('raw_clock_numeric_reversals_observed', codes(r))
        self.assertIn('raw_clock_offset_changes_observed', codes(r))
        self.assertFalse(r['historical_timezone_rule_established'])

    def test_unfinished_quote_preserved_without_completed_clock_pair(self):
        r = quality.inspect_timing_bytes(te(timed()[:5]+['S\t13\t2']))
        self.assertEqual(r['quote_outcomes_recorded'], 1)
        self.assertEqual(r['paired_clocks']['completed_pairs'], 0)
        self.assertEqual(r['paired_clocks']['quotes_without_completed_pair'], 1)
        self.assertEqual(r['paired_clocks']['paired_raw_arithmetic'], [])
        self.assertIn('quote_without_completed_clock_pair', codes(r))

    def test_empty_run_has_unknown_repeat_span_and_no_observed_clock_groups(self):
        reports = [quality.inspect_forward_segments(fe(fp(0))),
                   quality.inspect_timing_bytes(te(timed()[:1]+['S\t18\t0']))]
        for r in reports:
            self.assertEqual(r['quote_outcomes_recorded'], 0)
            self.assertIsNone(r['quote_statistics']['longest_observed_repeat_span_us'])
            self.assertIsNone(r['receipt_window']); self.assertIn('no_recorded_quotes', codes(r))
        self.assertEqual(reports[1]['paired_clocks']['status'], 'not_observed')

    def test_pending_attempt_and_partial_tail_have_explicit_findings(self):
        for r in (quality.inspect_timing_bytes(te(timed()[:2])),
                  quality.inspect_forward_segments(fe([fp(1)[0][:2]]))):
            self.assertTrue(r['pending_attempt']); self.assertIn('pending_attempt', codes(r))
        r = quality.inspect_timing_bytes(te(timed()[:-1])+b'S\t')
        self.assertTrue(r['truncated_tail']); self.assertIn('partial_final_frame', codes(r))

    def test_missing_invalid_native_quote_outcomes_are_not_zeros(self):
        for code, field in ((15, 'missing_quote_outcomes'), (16, 'invalid_quote_outcomes')):
            groups = fp(2); fields = groups[0][4].split('\t')
            groups[0][4] = '\t'.join(['N', *fields[1:8], str(code)])
            groups[0][-1] = f'S\t{code}\t2\t1'
            r = quality.inspect_forward_segments(fe(groups))
            self.assertEqual(r[field], 1); self.assertEqual(r['quote_outcomes_recorded'], 1)
            self.assertEqual(r['quote_statistics']['distinct_source_millis'], 1)
            self.assertIn(field, codes(r))

    def test_event_details_capped_but_all_rotation_counts_retained(self):
        r = quality.inspect_forward_segments(fe(fp(240)))
        self.assertEqual(r['quote_statistics']['adjacent_identical_snapshots'], 239)
        self.assertEqual(r['event_count'], 239); self.assertEqual(len(r['events']), 128)
        self.assertTrue(r['event_details_truncated']); self.assertEqual(r['events'][-1]['sequence'], 129)

    def test_event_prefix_does_not_use_future_observations(self):
        groups = fp(6)
        prefix = [groups[0][:7]+['S\t18\t3\t3']]
        a = quality.inspect_forward_segments(fe(prefix)); b = quality.inspect_forward_segments(fe(groups))
        self.assertEqual(a['events'], b['events'][:2])
        self.assertEqual(a['quote_statistics']['longest_observed_repeat_span_us'], 1000000)
        self.assertEqual(b['quote_statistics']['longest_observed_repeat_span_us'], 2500000)

    def test_limit_stop_remains_stopped_and_complete_format_remains_complete(self):
        rows = timed(); rows[-1] = 'S\t13\t9'
        r = quality.inspect_timing_bytes(te(rows))
        self.assertEqual(r['capture_status'], 'stopped'); self.assertIn('elapsed_limit_stop', codes(r))
        complete = quality.inspect_timing_bytes(te(timed(polls=60)))
        self.assertEqual(complete['capture_status'], 'complete'); self.assertFalse(complete['market_data_qualified'])

    def test_all_metrics_match_retained_readers_where_semantics_match(self):
        segments = fe(fp(240)); a = forward.inspect_segments(segments); r = quality.inspect_forward_segments(segments)
        self.assertEqual(r['quote_statistics']['adjacent_identical_snapshots'], a['repeated_snapshots'])
        self.assertEqual(r['quote_statistics']['source_labels_below_prior_highwater'], a['source_backwards'])
        self.assertEqual(r['quote_statistics']['same_timestamp_changed_snapshots'], a['equal_time_changed'])
        raw = te(timed(repeated=True)); b = timing.inspect_bytes(raw); r = quality.inspect_timing_bytes(raw)
        for new, old in (('source_label_adjacent_reversals', 'source_label_reversals'),
                         ('adjacent_identical_snapshots', 'adjacent_identical_snapshots'),
                         ('longest_observed_repeat_span_us', 'longest_observed_repeat_span_us')):
            self.assertEqual(r['quote_statistics'][new], b[old])

    def test_no_join_at_source_boundary(self):
        r = self.build(); a, b = [s['quality'] for s in r['sources']]
        self.assertEqual(a['quote_statistics']['adjacent_comparisons'], 3)
        self.assertEqual(b['quote_statistics']['adjacent_comparisons'], 2)
        self.assertNotIn('quote_statistics', r)
        self.assertFalse(r['cross_run_contract_authenticated'])

    def test_deterministic_report_markdown_and_read_only_inputs(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        a = self.build(); b = self.build()
        self.assertEqual(a, b); self.assertEqual(quality.render_markdown(a), quality.render_markdown(b))
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        md = quality.render_markdown(a)
        self.assertIn('not_recorded', md); self.assertIn('source_age_unverified', md)
        for source in a['sources']:
            for entry in source['files']: self.assertIn(entry['sha256'], md)

    def test_wrong_order_duplicate_extra_fields_and_source_count_reject(self):
        for mutate in ('order', 'duplicate', 'extra', 'count', 'schema'):
            m = deepcopy(self.manifest)
            if mutate == 'order': m['sources'].reverse()
            elif mutate == 'duplicate': m['sources'][0]['files'] *= 2
            elif mutate == 'extra': m['orders_available'] = True
            elif mutate == 'count': m['sources'].pop()
            else: m['schema'] = 'qualified'
            with self.assertRaises(ValueError): self.build(m)

    def test_path_traversal_absolute_backslash_and_injection_reject(self):
        for path in ('../private', '/tmp/private', 'C:\\private', 'data/../private',
                     'data/timing-probe-130-native/Run130-1-1-1/Timing130.txt\nsecret'):
            m = deepcopy(self.manifest); m['sources'][1]['files'][0]['path'] = path
            with self.assertRaises(ValueError): self.build(m)

    def test_corrupt_hash_payload_and_canonical_hash_types_reject(self):
        for digest in ('f'*64, 'F'*64, True, 123, None):
            m = deepcopy(self.manifest); m['sources'][1]['files'][0]['sha256'] = digest
            with self.assertRaises(ValueError): self.build(m)
        p = self.root/self.manifest['sources'][1]['files'][0]['path']; p.write_bytes(b'forged')
        self.manifest['sources'][1]['files'][0]['sha256'] = hashlib.sha256(b'forged').hexdigest()
        with self.assertRaises(ValueError): self.build()

    def test_mixed_run_names_origin_and_segment_order_reject(self):
        self.manifest = fixtures(self.root, count=240)
        for mutate in ('run', 'origin', 'order'):
            m = deepcopy(self.manifest)
            if mutate == 'order': m['sources'][0]['files'].reverse()
            else:
                entry = m['sources'][0]['files'][1]
                old = self.root/entry['path']
                entry['path'] = entry['path'].replace('-1-1000/', '-2-1000/' if mutate == 'run' else '-1-1001/')
                target = self.root/entry['path']; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(old.read_bytes())
            with self.assertRaises(ValueError): self.build(m)

    def test_whole_run_origin_microseconds_must_match(self):
        m = deepcopy(self.manifest); entry = m['sources'][1]['files'][0]; old = self.root/entry['path']
        entry['path'] = entry['path'].replace('-1-1000/', '-1-1001/')
        target = self.root/entry['path']; target.parent.mkdir(parents=True); target.write_bytes(old.read_bytes())
        with self.assertRaisesRegex(ValueError, 'quality_run_origin'): self.build(m)

    def test_mixed_invented_and_market_declarations_reject(self):
        self.manifest = fixtures(self.root, clock_rows=timed(kind='market_declared'))
        with self.assertRaisesRegex(ValueError, 'quality_mixed_declarations'): self.build()

    def test_symlink_file_directory_and_root_reject(self):
        entry = self.manifest['sources'][1]['files'][0]; p = self.root/entry['path']
        saved = p.read_bytes(); target = self.root/'saved'; target.write_bytes(saved); p.unlink(); p.symlink_to(target)
        with self.assertRaises(ValueError): self.build()
        p.unlink(); p.write_bytes(saved)
        folder = p.parent; moved = self.root/'moved'; folder.rename(moved); folder.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError): self.build()
        link = self.root/'rootlink'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): quality.build_report(self.manifest, link)

    def test_manifest_duplicate_keys_nonfinite_unicode_and_size_reject(self):
        p = self.root/'manifest.json'
        for data in (b'{"schema":1,"schema":2}', b'{"schema":NaN}', b'\xff', b'x'*(quality.MAX_MANIFEST+1), b''):
            p.write_bytes(data)
            with self.assertRaises(ValueError): quality.load_manifest(p)

    def test_file_and_total_byte_bounds_and_count_caps(self):
        m = deepcopy(self.manifest); m['sources'][0]['files'] *= 65
        with self.assertRaises(ValueError): self.build(m)
        with patch.object(quality, 'MAX_TOTAL', 1):
            with self.assertRaisesRegex(ValueError, 'quality_total_size'): self.build()
        entry = self.manifest['sources'][1]['files'][0]
        (self.root/entry['path']).write_bytes(b'x'*(timing.MAX_BYTES+1))
        with self.assertRaisesRegex(ValueError, 'quality_size'): self.build()

    def test_raw_inputs_required_not_alleged_inspection_json(self):
        with self.assertRaises(ValueError): quality.inspect_timing_bytes({'orders_available': True})
        with self.assertRaises(ValueError): quality.inspect_forward_segments({'observed': 1})

    def test_cli_json_markdown_and_generic_failure_without_input_secrets(self):
        p = self.root/'manifest.json'; p.write_text(json.dumps(self.manifest))
        args = [sys.executable, str(ROOT/'scripts/forward-quality-131.py'), str(p), '--root', str(self.root)]
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(json.loads(result.stdout), self.build())
        md = subprocess.run(args+['--format', 'markdown'], capture_output=True, text=True)
        self.assertEqual(md.returncode, 0); self.assertEqual(md.stdout, quality.render_markdown(self.build())+'\n')
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        p.write_text('{"schema":"private_account_identifier"}')
        bad = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1); self.assertNotIn('private_account_identifier', bad.stdout+bad.stderr)
        self.assertEqual(json.loads(bad.stdout)['reason'], 'invalid_or_unreadable_quality_inputs')

    def test_default_config_and_no_terminal_order_or_strategy_interface(self):
        config = json.loads((ROOT/'config/forward-quality-131.json').read_bytes())
        self.assertEqual(config['schema'], quality.SCHEMA)
        self.assertEqual([s['id'] for s in config['sources']], list(quality.IDS))
        self.assertEqual([len(s['files']) for s in config['sources']], [60, 1])
        source = (ROOT/'src/forex_demo_lab/forward_quality_131.py').read_text()
        for token in ('MetaTrader5', 'OrderSend', 'order_send', 'subprocess', 'WebRequest', 'backtest', 'AccountInfo'):
            self.assertNotIn(token, source)


if __name__ == '__main__':
    unittest.main()
