from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import paired_capture_132 as paired
from forex_demo_lab import timing_probe_130 as old
from forex_demo_lab.forward_quality_131 import _quality

ROOT = Path(__file__).resolve().parents[1]
SECOND = int(datetime(2026, 10, 19, 12, tzinfo=timezone.utc).timestamp())


def bits(value):
    return struct.pack('>d', float(value)).hex().upper()


def encode(payloads):
    chain = paired.ZERO; lines = []
    for payload in payloads:
        chain = hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()
        lines.append(payload+'\t'+chain+'\r\n')
    return ''.join(lines).encode('ascii')


def fixture(polls=3, repeated=False, seconds=SECOND, step=1000000, terminal=None, kind='invented_fixture'):
    date = datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y.%m.%d')
    rows = [f'H\tFXDL_PAIRED132_V1\t{kind}\t{date}\t{seconds}\t1000']; seq = 0
    for poll in range(polls):
        for part, (tag, key) in enumerate(paired.CYCLE):
            seq += 1; bu = 1000+poll*step+part*100; s = seconds+(bu-1000)//1000000
            values = [s+10800, s+10800, s, s+7200, -7200, 0]
            if tag == 'T':
                source = seconds+10800+(0 if repeated else poll)
                values = [source, source*1000+123, bits(1.1), bits(1.1001), bits(0), 0, 1026, bits(0)]
            rows += [f'A\t{seq}\t{tag}\t{key}', '\t'.join(map(str, [tag, seq, key, s, s, s, bu, bu+10, bu+20, 1, 0, *values]))]
    end = 1000+(polls-1)*step+230 if polls else 1000
    rows.append(f'E\t{seq}\t{seconds+(end-1000)//1000000}\t{end}' if terminal == 'E' or polls == 3600
                else f'S\t{terminal or 18}\t{seq}')
    return rows


def change(rows, index, field, value):
    fields = rows[index].split('\t'); fields[field] = str(value); rows[index] = '\t'.join(fields)


class Paired132Tests(unittest.TestCase):
    def test_complete_invented_hour_with_all10800_groups_and_boundaries(self):
        raw = encode(fixture(polls=3600)); r = paired.inspect_bytes(raw)
        self.assertEqual((r['capture_status'], r['completed_polls'], r['queries_recorded']), ('complete', 3600, 10800))
        self.assertEqual(r['source_label_advances'], 3599); self.assertLess(len(raw), paired.MAX_BYTES)
        self.assertEqual(r['schema'], 'paired_recorder132_inspection_v1')
        q = paired.quality_report(raw)
        self.assertEqual(q['format'], 'paired132'); self.assertEqual(q['quote_outcomes_recorded'], 3600)
        self.assertEqual(q['paired_clocks']['completed_pairs'], 3600); self.assertFalse(q['orders_available'])

    def test_all_five_dates_and_allowed_midnight_crossing(self):
        for day in range(19, 24):
            second = int(datetime(2026, 10, day, 12, tzinfo=timezone.utc).timestamp())
            r = paired.inspect_bytes(encode(fixture(seconds=second)))
            self.assertEqual(r['origin_nominal_gmt_seconds'], second)
        second = int(datetime(2026, 10, 19, 23, 59, 59, tzinfo=timezone.utc).timestamp())
        self.assertEqual(paired.inspect_bytes(encode(fixture(seconds=second)))['completed_polls'], 3)

    def test_before_after_window_and_crossing_expiry_reject(self):
        for second in (SECOND-86400, SECOND+5*86400,
                       int(datetime(2026, 10, 23, 23, 59, 59, tzinfo=timezone.utc).timestamp())):
            with self.assertRaises(ValueError): paired.inspect_bytes(encode(fixture(seconds=second)))
        rows = fixture(); change(rows, 0, 3, '2026.10.20')
        with self.assertRaisesRegex(ValueError, 'paired_header_date'): paired.inspect_bytes(encode(rows))

    def test_repeated_quotes_keep_native_bits_and_unknown_flags(self):
        r = paired.inspect_bytes(encode(fixture(repeated=True)))
        self.assertEqual(r['adjacent_identical_snapshots'], 2); self.assertEqual(r['longest_observed_repeat_span_us'], 2000000)
        rows = fixture(repeated=True); change(rows, 10, 15, bits(-0.0)); change(rows, 10, 17, 2**32-1)
        r = paired.inspect_bytes(encode(rows))
        self.assertEqual(r['same_time_changed_snapshots'], 2)
        self.assertEqual(r['rows'][4]['native_bits']['last'], '8000000000000000')
        self.assertEqual(r['rows'][4]['raw_flags'], 2**32-1)

    def test_source_reversals_and_clock_domain_changes_remain_raw(self):
        rows = fixture(); change(rows, 10, 11, SECOND+10799); change(rows, 10, 12, (SECOND+10799)*1000+123)
        change(rows, 8, 12, SECOND+7200)
        r = paired.inspect_bytes(encode(rows)); q = paired.quality_report(encode(rows))
        self.assertEqual(r['source_label_reversals'], 1)
        self.assertEqual(r['raw_clock_changes']['time_trade_server']['reversals'], 1)
        self.assertEqual(q['paired_clocks']['paired_raw_arithmetic'], r['paired_raw_arithmetic'])
        self.assertFalse(q['historical_timezone_rule_established']); self.assertIsNone(q['source_age'])

    def test_every_small_prefix_stop_keeps_pending_attempt_without_values(self):
        original = fixture()
        for i in range(1, len(original)-1, 2):
            seq = (i+1)//2
            for reason in (3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 18, 19):
                r = paired.inspect_bytes(encode(original[:i+1]+[f'S\t{reason}\t{seq}']))
                self.assertTrue(r['pending_attempt']); self.assertEqual(r['queries_recorded'], seq-1)
                self.assertEqual(r['completed_polls'], (seq-1)//3)

    def test_unfinished_quote_not_a_completed_pair(self):
        raw = encode(fixture()[:5]+['S\t13\t2']); r = paired.quality_report(raw)
        self.assertEqual(r['quote_outcomes_recorded'], 1)
        self.assertEqual(r['paired_clocks']['completed_pairs'], 0)
        self.assertEqual(r['paired_clocks']['quotes_without_completed_pair'], 1)

    def test_storage_failure_tail_missing_footer_and_empty_prefix(self):
        for suffix in (b'', b'C\t', b'C\t3\r'):
            r = paired.inspect_bytes(encode(fixture()[:-1])+suffix)
            self.assertEqual(r['capture_status'], 'incomplete')
        r = paired.quality_report(encode(fixture()[:1]))
        self.assertEqual(r['paired_clocks']['status'], 'not_observed'); self.assertIsNone(r['receipt_window'])

    def test_spacing_gap_and_no_catchup(self):
        with self.assertRaisesRegex(ValueError, 'paired_poll_spacing'): paired.inspect_bytes(encode(fixture(step=999999)))
        q = paired.quality_report(encode(fixture(step=2000001)))
        self.assertEqual(q['quote_statistics']['receipt_poll_gaps_over_two_seconds'], 2)
        self.assertIsNone(q['source_age'])

    def test_elapsed_cap_drift_and_monotonic_receipts(self):
        for field, value in ((3, SECOND-1), (5, SECOND+3), (6, 999), (8, paired.MAX_US+1001)):
            rows = fixture(); change(rows, 2, field, value)
            with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))

    def test_premature_end_duplicate_attempt_and_count_limit(self):
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(fixture(terminal='E')))
        rows = fixture(); rows.insert(2, rows[1])
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))
        # First attempt must start at1 even if the declared integer is within the cap.
        rows = fixture(); change(rows, 1, 1, 10800)
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))

    def test_forged_digest_reordered_frames_failed_outcomes_reject(self):
        raw = encode(fixture())
        with self.assertRaises(ValueError): paired.inspect_bytes(raw.replace(b'before', b'befoxe', 1))
        rows = fixture(); rows[1], rows[3] = rows[3], rows[1]
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))
        for field, value in ((9, 0), (10, 4303)):
            rows = fixture(); change(rows, 4, field, value)
            with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))

    def test_bad_quotes_integers_native_bits_and_framing_reject(self):
        for field, value in ((11, 1), (12, 0), (13, bits(0)), (14, bits(.9)), (15, '7FF0000000000000'),
                             (18, bits(-1)), (17, 2**32), (1, '01'), (9, 'True')):
            rows = fixture(); change(rows, 4, field, value)
            with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))
        for data in (b'', b'\xff', b'\x7f', b'H\nX', b'X'*2049, b'X'*(paired.MAX_BYTES+1)):
            with self.assertRaises(ValueError): paired.inspect_bytes(data)

    def test_header_magic_and_old_reader_are_not_reused_as_wire_authority(self):
        raw = encode(fixture())
        with self.assertRaises(ValueError): old.inspect_bytes(raw)
        rows = fixture(); change(rows, 0, 1, 'FXDL_TIMING130_V1')
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows))
        source = (ROOT/'src/forex_demo_lab/paired_capture_132.py').read_text()
        self.assertNotIn('old.inspect_bytes', source)
        self.assertEqual(paired.quality_report(raw)['wire_schema'], 'paired_recorder132_inspection_v1')

    def test_quality_engine_preserves_policy_and_never_admits_market_headers(self):
        raw = encode(fixture(kind='market_declared')); parsed = paired.inspect_bytes(raw); report = paired.quality_report(raw)
        shared = _quality('timing130', parsed)
        self.assertEqual(report['quote_statistics'], shared['quote_statistics'])
        self.assertEqual(report['events'], shared['events']); self.assertEqual(report['event_detail_limit'], 128)
        for key in ('source_utc_certified', 'receipt_utc_certified', 'market_data_qualified', 'paper_evaluation_available',
                    'orders_available', 'real_money_execution_available', 'strategy_evaluated', 'profitability_established'):
            self.assertIs(report[key], False)
        self.assertIsNone(report['source_age'])
        self.assertIn('Declared input kind: **market_declared**', paired.quality_markdown(report))

    def test_bounded_event_details_preserve_all_counts(self):
        report = paired.quality_report(encode(fixture(polls=180, repeated=True)))
        self.assertEqual(report['event_count'], 179); self.assertEqual(len(report['events']), 128)
        self.assertTrue(report['event_details_truncated']); self.assertEqual(report['quote_statistics']['adjacent_identical_snapshots'], 179)

    def test_cli_and_library_agree_and_inputs_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'Paired132.txt'; raw = encode(fixture()); p.write_bytes(raw)
            args = [sys.executable, str(ROOT/'scripts/paired-recorder-132.py'), str(p)]
            a = subprocess.run(args, capture_output=True, text=True)
            b = subprocess.run(args+['--format', 'markdown'], capture_output=True, text=True)
            self.assertEqual(a.returncode, 0, a.stderr); self.assertEqual(b.returncode, 0, b.stderr)
            q = paired.quality_report(raw)
            self.assertEqual(json.loads(a.stdout), q); self.assertEqual(b.stdout, paired.quality_markdown(q)+'\n')
            self.assertEqual(p.read_bytes(), raw); self.assertIn('Paired forward recorder132 quality', b.stdout)
            self.assertIn('Declared input kind: **invented_fixture**', b.stdout)
            p.write_bytes(b'invalid private_account_identifier')
            bad = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1); self.assertNotIn('private_account_identifier', bad.stdout+bad.stderr)
            self.assertEqual(json.loads(bad.stdout)['reason'], 'invalid_or_unreadable_paired_export')
            p.write_bytes(raw); link = p.with_name('link'); link.symlink_to(p)
            bad = subprocess.run([*args[:-1], str(link)], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)

    def test_terminal_tail_wrong_stop_and_no_resuming(self):
        rows = fixture()
        for changed in (rows+[rows[1]], rows[:-1]+['S\t1\t9'], rows[:-1]+['S\t13\t8']):
            with self.assertRaises(ValueError): paired.inspect_bytes(encode(changed))
        with self.assertRaises(ValueError): paired.inspect_bytes(encode(rows)+b'X')

    def test_source_config_state_io_and_read_only_capabilities(self):
        spec = json.loads((ROOT/'config/paired-recorder-132.json').read_bytes())
        self.assertEqual(spec['nominal_gmt_dates'], list(paired.DATES)); self.assertEqual(spec['max_bytes'], paired.MAX_BYTES)
        self.assertEqual(spec['max_diagnostic_groups'], paired.MAX_QUERIES); self.assertEqual(spec['max_elapsed_us'], paired.MAX_US)
        source = (ROOT/'mt5/Scripts/ForexDemoPairedRecorder132.mq5').read_text()
        self.assertIn('input bool CollectEvidence = false;', source)
        self.assertLess(source.index('if(!CollectEvidence)'), source.index('int reason=Guard132(false)'))
        self.assertIn('reason!=14 && Append132', source); self.assertIn('CompletePairedQuery132(clock132)', source)
        self.assertLess(source.index('ReservePairedBytes132'), source.index('ulong size=FileSize(file132)'))
        self.assertIn('if(exists || (error!=0 && error!=5019)) return false;', source)
        self.assertIn('size!=0 || error!=0', source)
        self.assertLess(source.index('if(!After132()) return false;', source.index('bool Tick132')), source.index('return Record132("T"'))
        for token in ('OrderSend(', 'OrderCheck(', 'CopyTicks', 'CopyRates', 'SymbolSelect(', 'WebRequest(', '#import',
                      'FILE_COMMON', 'FILE_SHARE', 'ClockReason107(', '2026.10.15'):
            self.assertNotIn(token, source)
        for line in source.splitlines():
            if any(token in line for token in ('StringFormat(', 'PrintFormat(', 'Record132(')):
                self.assertNotIn('private_login132', line); self.assertNotIn('private_server132', line)


if __name__ == '__main__':
    unittest.main()
