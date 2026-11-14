from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import timing_probe_130 as probe

ROOT = Path(__file__).resolve().parents[1]
SECOND = int(datetime(2026, 10, 15, 12, tzinfo=timezone.utc).timestamp())


def bits(value):
    return struct.pack('>d', float(value)).hex().upper()


def encode(payloads):
    chain = probe.ZERO; rows = []
    for payload in payloads:
        chain = hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()
        rows.append(payload+'\t'+chain+'\r\n')
    return ''.join(rows).encode('ascii')


def fixture(polls=60, repeated=False, kind='invented_fixture', step=1000000):
    rows = [f'H\tFXDL_TIMING130_V1\t{kind}\t{probe.DATE}\t{SECOND}\t1000']; seq = 0
    for poll in range(polls):
        for part, (tag, key) in enumerate(probe.CYCLE):
            seq += 1; bu = 1000+poll*step+part*100; s = SECOND+(bu-1000)//1000000
            if tag == 'C':
                values = [s+10800, s+10800, s, s+7200, -7200, 0]
            else:
                source = SECOND+10800+(0 if repeated else poll)
                values = [source, source*1000+123, bits(1.1), bits(1.1001), bits(0), 0, 1026, bits(0)]
            rows += [f'A\t{seq}\t{tag}\t{key}', '\t'.join(map(str, [tag, seq, key, s, s, s, bu, bu+10, bu+20, 1, 0, *values]))]
    end = 1000+(polls-1)*step+230 if polls else 1000
    rows.append(f'E\t{seq}\t{SECOND+(end-1000)//1000000}\t{end}')
    return rows


def change(rows, index, field, value):
    fields = rows[index].split('\t'); fields[field] = str(value); rows[index] = '\t'.join(fields)


class Timing130Tests(unittest.TestCase):
    def test_complete_healthy_updates_and_separate_observations(self):
        r = probe.inspect_bytes(encode(fixture()))
        self.assertEqual((r['capture_status'], r['completed_polls'], r['quotes_recorded'], r['queries_recorded']), ('complete', 60, 60, 180))
        self.assertEqual(r['source_label_advances'], 59)
        self.assertEqual(r['adjacent_identical_snapshots'], 0)
        self.assertEqual(r['longest_observed_repeat_span_us'], 0)
        self.assertEqual(r['paired_raw_arithmetic'][0]['raw_source_minus_time_current_ms'], [123, 123])
        self.assertEqual(r['paired_raw_arithmetic'][0]['raw_server_minus_gmt_seconds'], [10800, 10800])

    def test_repeated_quotes_while_clocks_advance_are_observations_not_age(self):
        r = probe.inspect_bytes(encode(fixture(repeated=True)))
        self.assertEqual(r['adjacent_identical_snapshots'], 59)
        self.assertEqual(r['longest_observed_repeat_span_us'], 59000000)
        self.assertEqual(r['source_label_advances'], 0)
        self.assertEqual(r['raw_clock_changes']['time_current']['advances'], 59)
        self.assertIsNone(r['source_age']); self.assertFalse(r['repeat_span_is_quote_age'])
        self.assertEqual(r['paired_raw_arithmetic'][-1]['raw_source_minus_time_current_ms'], [-58877, -58877])

    def test_source_reversal_preserved_and_flagged(self):
        p = fixture(); change(p, 10, 11, SECOND+10799); change(p, 10, 12, (SECOND+10799)*1000+123)
        r = probe.inspect_bytes(encode(p))
        self.assertEqual(r['source_label_reversals'], 1); self.assertEqual(r['quotes_recorded'], 60)

    def test_server_clock_domain_change_and_reversal_preserved(self):
        p = fixture(); change(p, 8, 12, SECOND+7200)
        r = probe.inspect_bytes(encode(p))
        self.assertEqual(r['raw_clock_changes']['time_trade_server']['reversals'], 1)
        self.assertEqual(r['paired_raw_arithmetic'][1]['raw_server_minus_gmt_seconds'][0], 7199)
        self.assertFalse(r['historical_timezone_rule_established'])

    def test_same_timestamp_changed_price_or_unknown_flags_not_identical(self):
        p = fixture(repeated=True); change(p, 10, 13, bits(1.10001)); change(p, 16, 17, 2**32-1)
        r = probe.inspect_bytes(encode(p))
        self.assertEqual(r['rows'][7]['raw_flags'], 2**32-1)
        self.assertEqual(r['same_time_changed_snapshots'], 3)
        self.assertEqual(r['adjacent_identical_snapshots'], 56)

    def test_native_bits_and_unknown_flags_retained(self):
        p = fixture(); change(p, 4, 15, bits(-0.0))
        r = probe.inspect_bytes(encode(p)); q = r['rows'][1]
        self.assertEqual(q['native_bits']['last'], '8000000000000000'); self.assertEqual(q['raw_flags'], 1026)

    def test_all_admission_and_authentication_flags_false(self):
        r = probe.inspect_bytes(encode(fixture(kind='market_declared')))
        for key in ('source_utc_certified', 'receipt_utc_certified', 'tick_delivery_complete', 'executable_freshness_certified',
                    'market_data_qualified', 'paper_evaluation_available', 'orders_available', 'real_money_execution_available', 'producer_authenticated'):
            self.assertIs(r[key], False, key)
        self.assertTrue(all(not p['arithmetic_is_quote_age'] for p in r['paired_raw_arithmetic']))

    def test_every_pending_attempt_stop_preserves_only_recorded_values(self):
        original = fixture()
        for i in range(1, len(original)-1, 2):
            seq = (i+1)//2
            r = probe.inspect_bytes(encode(original[:i+1]+[f'S\t9\t{seq}']))
            self.assertTrue(r['pending_attempt']); self.assertEqual(r['queries_recorded'], seq-1)
            self.assertEqual(r['completed_polls'], (seq-1)//3)
            self.assertEqual(r['capture_status'], 'stopped')

    def test_unfinished_poll_quote_is_not_a_completed_pair(self):
        r = probe.inspect_bytes(encode(fixture()[:5]+['S\t13\t2']))
        self.assertEqual(r['quotes_recorded'], 1); self.assertEqual(r['completed_polls'], 0)
        self.assertIsNone(r['longest_observed_repeat_span_us'])

    def test_incomplete_tail_and_missing_end(self):
        for suffix in (b'', b'E\t', b'E\t180\r'):
            r = probe.inspect_bytes(encode(fixture()[:-1])+suffix)
            self.assertEqual(r['capture_status'], 'incomplete'); self.assertEqual(r['completed_polls'], 60)
        r = probe.inspect_bytes(encode(fixture()[:1])); self.assertEqual(r['quotes_recorded'], 0)

    def test_short_stopped_run_and_deadline_after_return(self):
        p = fixture(polls=2)[:-1]+['S\t13\t6']; r = probe.inspect_bytes(encode(p))
        self.assertEqual(r['completed_polls'], 2); self.assertEqual(r['stop_code'], 13)

    def test_minimum_spacing_and_no_catchup(self):
        with self.assertRaisesRegex(ValueError, 'timing_poll_spacing'):
            probe.inspect_bytes(encode(fixture(step=999999)))
        r = probe.inspect_bytes(encode(fixture(polls=3, step=2000000)[:-1]+['S\t18\t9']))
        self.assertEqual(r['completed_polls'], 3)

    def test_date_expiry_and_date_mismatch(self):
        for text in ('2026.10.14', '2026.10.16'):
            p = fixture(); p[0] = p[0].replace(probe.DATE, text)
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))
        p = fixture(); change(p, 0, 4, SECOND-86400)
        with self.assertRaisesRegex(ValueError, 'timing_date'): probe.inspect_bytes(encode(p))

    def test_receipt_reversal_jump_and_elapsed_cap(self):
        for field, value in ((3, SECOND-1), (5, SECOND+3), (6, 999), (8, 60001001)):
            p = fixture(); change(p, 2, field, value)
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))

    def test_crossed_nonpositive_nonfinite_and_invalid_source_reject(self):
        for field, value in ((13, bits(0)), (14, bits(.9)), (13, '7FF0000000000000'), (15, bits(-1)), (18, bits(-1)), (11, 1), (12, 0), (17, 2**32)):
            p = fixture(); change(p, 4, field, value)
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))

    def test_failed_or_error_outcome_reject(self):
        for field, value in ((9, 0), (10, 4303)):
            p = fixture(); change(p, 4, field, value)
            with self.assertRaisesRegex(ValueError, 'timing_query_failed'): probe.inspect_bytes(encode(p))

    def test_checksum_and_digest_case(self):
        raw = encode(fixture())
        for bad in (raw.replace(b'before', b'befoxe', 1), raw[:raw.index(b'\r\n')].lower()+raw[raw.index(b'\r\n'):]):
            with self.assertRaises(ValueError): probe.inspect_bytes(bad)

    def test_reordered_duplicate_missing_and_wrong_sequence(self):
        for operation in ('reorder', 'duplicate', 'missing', 'sequence'):
            p = fixture()
            if operation == 'reorder': p[1], p[3] = p[3], p[1]
            elif operation == 'duplicate': p.insert(3, p[2])
            elif operation == 'missing': p.pop(2)
            else: change(p, 1, 1, 2)
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))

    def test_frame_size_encoding_controls_and_types(self):
        for raw in (b'', b'\xff', b'H\x7f', b'X'*(probe.MAX_BYTES+1), b'X'*2049, 'text', b'X\nY'):
            with self.assertRaises(ValueError): probe.inspect_bytes(raw)

    def test_extra_fields_and_noncanonical_integers(self):
        for field, value in ((1, '01'), (6, '-1'), (9, 'True'), (11, '-0')):
            p = fixture(); change(p, 2, field, value)
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))
        p = fixture(); p[2] += '\tprivate_identifier'
        with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))

    def test_premature_end_terminal_tail_unknown_and_bad_stop(self):
        original = fixture()
        for p in (fixture(polls=2), original+['S\t13\t180'], original[:-1]+['S\t1\t180'], original[:-1]+['S\t13\t179'], original[:1]+['Z']):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(p))
        with self.assertRaises(ValueError): probe.inspect_bytes(encode(original)+b'X')

    def test_query_cap_not_renewed_by_extra_polls(self):
        with self.assertRaises(ValueError): probe.inspect_bytes(encode(fixture(polls=61)))

    def test_file_cli_readonly_generic_failure_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'Timing130.txt'; raw = encode(fixture()); p.write_bytes(raw)
            args = [sys.executable, str(ROOT/'scripts/timing-probe-130.py'), str(p)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(p.read_bytes(), raw)
            self.assertEqual(json.loads(result.stdout), probe.inspect_bytes(raw))
            link = p.with_name('link'); link.symlink_to(p)
            with self.assertRaises(ValueError): probe.inspect_file(link)
            p.write_bytes(b'invalid'); result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['reason'], 'invalid_or_unreadable_timing_export')

    def test_actual_guard_schedule_default_off_and_collision_source(self):
        source = (ROOT/'mt5/Scripts/ForexDemoTimingProbe130.mq5').read_text()
        spec = json.loads((ROOT/'config/timing-probe-130.json').read_bytes())
        self.assertEqual(spec['query_cycle'], [list(p) for p in probe.CYCLE]); self.assertEqual(spec['max_bytes'], probe.MAX_BYTES)
        self.assertIn('input bool CollectEvidence = false;', source); self.assertIn('if(!CollectEvidence) {Status130(1);return;}', source)
        self.assertIn('MarkPollStart130(clock130,bu130)', source); self.assertIn('Sleep(50)', source)
        self.assertIn('if(exists || (error!=0 && error!=5019)) return false;', source)
        self.assertIn('size!=0 || error!=0', source); self.assertIn('FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI', source)
        for token in ('OrderSend(', 'OrderCheck(', 'SymbolSelect(', 'WebRequest(', 'CopyTicks', 'CopyRates', '#import', 'FILE_COMMON', 'ClockReason107(', 'AccountInfoDouble('):
            self.assertNotIn(token, source)
        # Neither private identity field occurs in any export or log formatter.
        for line in source.splitlines():
            if any(t in line for t in ('StringFormat(', 'PrintFormat(', 'Record130(')):
                self.assertNotIn('private_login130', line); self.assertNotIn('private_server130', line)


if __name__ == '__main__':
    unittest.main()
