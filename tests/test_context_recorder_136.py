from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import context_recorder_136 as recorder
from forex_demo_lab import paired_capture_132
from forex_demo_lab.fresh_input_135 import Replay, expected_policy
from forex_demo_lab.paired_replay_133 import canonical, DENIED

ROOT = Path(__file__).resolve().parents[1]
SECOND = int(datetime(2026, 10, 26, 12, tzinfo=timezone.utc).timestamp())


def bits(value): return struct.pack('>d', float(value)).hex().upper()


def encode(rows):
    chain = recorder.ZERO; lines = []
    for row in rows:
        chain = hashlib.sha256((chain + '\t' + row + '\n').encode('ascii')).hexdigest().upper()
        lines.append(row + '\t' + chain + '\r\n')
    return ''.join(lines).encode('ascii')


def fixture(polls=3, seconds=SECOND, kind='invented_fixture', rules=0, tiers=2, all_sessions=False,
            failed=(), commission_failed=False, repeats=False, step=1_000_000):
    date = datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y.%m.%d')
    rows = [f'H\tFXDL_CONTEXT136_V1\t{kind}\t{date}\t{seconds}\t1000']
    sequence = 0; cursor = 1000; last_start = None; context_index = 0
    def outcome(tag, key, values, ok=True, error=0):
        nonlocal sequence, cursor
        sequence += 1
        micros = [cursor, cursor + 10, cursor + 20]
        stamps = [seconds + (u - 1000) // 1_000_000 for u in micros]
        rows.extend([f'A\t{sequence}\t{tag}\t{key}', '\t'.join(map(str,
                    [tag, sequence, key, *stamps, *micros, int(ok), error, *values]))])
        cursor += 100
    def clocks(key):
        stamp = seconds + (cursor - 1000) // 1_000_000
        outcome('C', key, [stamp + 10800, stamp + 10800, stamp, stamp + 7200, -7200, 0])
    for poll in range(polls):
        if poll % 3600 == 0:
            context_index += 1; rows.append(f'B\t{context_index}\t{poll}'); clocks('context_before')
            for tag, key in recorder.PROPERTIES:
                ok = key not in failed
                value = (str(10 + context_index) if tag == 'I' else bits(-.7 if key.startswith('swap_') else .01) if tag == 'D' else 'EUR') if ok else ('0' if tag == 'I' else bits(0) if tag == 'D' else 'NA')
                outcome(tag, key, [value], ok, 0 if ok else 4303)
            for day in range(7):
                for index in range(9 if all_sessions else 1):
                    outcome('W', f'{day}:{index}', [0, 86400 if all_sessions else 0], all_sessions, 0 if all_sessions else 4307)
            outcome('K', 'commissions', [-1 if commission_failed else rules], not commission_failed, 4303 if commission_failed else 0)
            if not commission_failed:
                for rule in range(rules):
                    rows.append(f'R\t{sequence}\t{rule}\tEMPTY\t0\t2\t0\t0\t0\t{tiers}')
                    for tier in range(tiers):
                        rows.append('\t'.join(map(str, ['L', sequence, rule, tier, 1, 1,
                                    bits(-.2), bits(0), bits(100), bits(tier), bits(tier + 1), 'USD'])))
            for side in ('buy', 'sell'):
                ok = side not in failed
                outcome('M', side, [bits(1 if ok else 0), bits(0)], ok, 0 if ok else 4303)
            clocks('context_after'); rows.append(f'Z\t{context_index}\t{sequence}')
        cursor = max(cursor, last_start + step) if last_start is not None else cursor
        last_start = cursor; clocks('before')
        source = seconds + 10800 + (0 if repeats else poll)
        outcome('T', 'quote', [source, source * 1000 + 123, bits(1.1), bits(1.1001), bits(0), 0, 1026, bits(0)])
        clocks('after')
    if polls == recorder.MAX_POLLS:
        rows.append(f'E\t{sequence}\t{polls}\t{seconds + (cursor - 1000) // 1_000_000}\t{cursor}')
    else: rows.append(f'S\t18\t{sequence}\t{polls}')
    return rows


def change(rows, tag, field, value, key=None, occurrence=0):
    found = 0
    for index, row in enumerate(rows):
        fields = row.split('\t')
        if fields[0] == tag and (key is None or len(fields) > 2 and fields[2] == key):
            if found == occurrence:
                fields[field] = str(value); rows[index] = '\t'.join(fields); return
            found += 1
    raise AssertionError('fixture row absent')


class ContextRecorder136Tests(unittest.TestCase):
    def test_full_count_four_contexts_and_changing_metadata_match_schedule(self):
        raw = encode(fixture(polls=14400, all_sessions=True))
        parsed = recorder.inspect_bytes(raw)
        self.assertEqual((parsed['capture_status'], parsed['completed_polls'], parsed['queries_attempted']), ('complete', 14400, 43604))
        self.assertEqual([c['polls_before'] for c in parsed['contexts']], [0, 3600, 7200, 10800])
        self.assertTrue(all(c['complete'] and c['weekly_template_truncated'] for c in parsed['contexts']))
        self.assertEqual([next(r['value'] for r in c['rows'] if r['key'] == 'account_leverage') for c in parsed['contexts']], [11, 12, 13, 14])
        self.assertLess(len(raw), recorder.MAX_BYTES)

    def test_short_prefix_with_complete_context_and_raw_fields(self):
        parsed = recorder.inspect_bytes(encode(fixture(rules=1)))
        self.assertEqual(parsed['completed_polls'], 3); self.assertEqual(parsed['queries_attempted'], 54)
        context = parsed['contexts'][0]
        self.assertEqual(context['commission_state'], 'reported_rules')
        self.assertEqual(context['commission_rules'][0]['tiers'][0]['value'], '-0.2')
        self.assertIsNone(context['commission_rules'][0]['currency'])
        quote = next(r for r in parsed['rows'] if r['type'] == 'T')
        self.assertEqual(quote['native_bits']['bid'], bits(1.1)); self.assertEqual(quote['raw_flags'], 1026)

    def test_all_dates_midnight_and_expired_window(self):
        for day in range(26, 31):
            stamp = int(datetime(2026, 10, day, 12, tzinfo=timezone.utc).timestamp())
            self.assertEqual(recorder.inspect_bytes(encode(fixture(seconds=stamp)))['completed_polls'], 3)
        for day in (24, 25, 31):
            stamp = int(datetime(2026, 10, day, 12, tzinfo=timezone.utc).timestamp())
            with self.assertRaises(ValueError): recorder.inspect_bytes(encode(fixture(seconds=stamp)))
        allowed = int(datetime(2026, 10, 26, 23, 59, 59, tzinfo=timezone.utc).timestamp())
        self.assertEqual(recorder.inspect_bytes(encode(fixture(seconds=allowed)))['completed_polls'], 3)
        expired = int(datetime(2026, 10, 30, 23, 59, 59, tzinfo=timezone.utc).timestamp())
        with self.assertRaises(ValueError): recorder.inspect_bytes(encode(fixture(seconds=expired)))

    def test_every_small_prefix_preserves_pending_context_or_pair(self):
        rows = fixture(polls=1, rules=1)
        for end in range(1, len(rows)):
            parsed = recorder.inspect_bytes(encode(rows[:end]))
            self.assertEqual(parsed['capture_status'], 'incomplete')
            self.assertLessEqual(parsed['completed_polls'], 1)
            if rows[end - 1].startswith('A\t'): self.assertTrue(parsed['pending_attempt'])
            if rows[end - 1].startswith('R\t'):
                self.assertTrue(parsed['pending_rule_payload']); self.assertIsNotNone(parsed['contexts'][0]['partial_commission_rule'])
        # Closed valid stop after a quote but before its after-clock: one quarantined pair fragment.
        index = next(i for i, row in enumerate(rows) if row.startswith('T\t'))
        sequence = int(rows[index].split('\t')[1])
        parsed = recorder.inspect_bytes(encode(rows[:index + 1] + [f'S\t13\t{sequence}\t0']))
        self.assertEqual(parsed['quarantined_poll_rows'], 2); self.assertEqual(parsed['completed_polls'], 0)

    def test_failed_unknown_empty_and_pending_costs_remain_distinct(self):
        for failed, expected in ((False, 'reported_empty'), (True, 'query_failed')):
            parsed = recorder.quality_report(encode(fixture(commission_failed=failed, failed=('point', 'buy'))))
            context = parsed['contexts'][0]
            self.assertEqual(context['commission_state'], expected)
            self.assertIsNone(next(r['value'] for r in context['rows'] if r['key'] == 'point'))
            self.assertIsNone(next(r['initial_rate'] for r in context['rows'] if r['type'] == 'M' and r['key'] == 'buy'))
            self.assertIsNone(context['applicable_USD_commission']); self.assertIsNone(context['applicable_USD_margin'])
        rows = fixture(rules=2); index = next(i for i, row in enumerate(rows) if row.startswith('R\t'))
        parsed = recorder.inspect_bytes(encode(rows[:index + 1]))
        self.assertTrue(parsed['pending_rule_payload']); self.assertEqual(parsed['contexts'][0]['commission_state'], 'incomplete')

    def test_maximum_rule_tier_counts_and_empty_rule_tiers(self):
        for rules, tiers in ((8, 16), (8, 0)):
            context = recorder.inspect_bytes(encode(fixture(rules=rules, tiers=tiers)))['contexts'][0]
            self.assertEqual(context['commission_state'], 'reported_rules')
            self.assertEqual(sum(len(r['tiers']) for r in context['commission_rules']), rules * tiers)
        rows = fixture(); change(rows, 'K', 11, 9)
        with self.assertRaises(ValueError): recorder.inspect_bytes(encode(rows))
        rows = fixture(rules=1); change(rows, 'R', 9, 17)
        with self.assertRaises(ValueError): recorder.inspect_bytes(encode(rows))

    def test_context_boundaries_refresh_and_cost_payload_cannot_be_skipped(self):
        rows = fixture()
        invalid = [rows[:1] + rows[2:], [r for r in rows if not r.startswith('Z\t')]]
        modified = list(rows); change(modified, 'B', 2, 3600); invalid.append(modified)
        modified = list(rows); change(modified, 'Z', 1, 2); invalid.append(modified)
        with_rules = fixture(rules=1); invalid.append([r for r in with_rules if not r.startswith(('R\t', 'L\t'))])
        for bad in invalid:
            with self.assertRaises(ValueError): recorder.inspect_bytes(encode(bad))

    def test_native_float_bits_source_reversals_and_sampling_gaps_are_not_repaired(self):
        rows = fixture(step=3_000_000)
        first = next(r for r in rows if r.startswith('T\t')).split('\t')
        source = int(first[11]) - 1
        change(rows, 'T', 11, source, occurrence=1); change(rows, 'T', 12, source * 1000 + 123, occurrence=1)
        change(rows, 'T', 15, bits(-0.0), occurrence=1); change(rows, 'T', 17, 2**32 - 1, occurrence=1)
        parsed = recorder.inspect_bytes(encode(rows)); quality = recorder.quality_report(encode(rows))
        quote = [r for r in parsed['rows'] if r['type'] == 'T'][1]
        self.assertEqual(quote['native_bits']['last'], bits(-0.0)); self.assertEqual(quote['raw_flags'], 2**32 - 1)
        self.assertEqual(quality['source_reversals'], 1); self.assertEqual(quality['quote_receipt_gaps_over2s'], 2)
        self.assertIsNone(quality['source_offset_bounds']); self.assertIsNone(quality['source_age'])

    def test_repeated_snapshots_are_retained_and_event_details_bounded(self):
        quality = recorder.quality_report(encode(fixture(polls=180, repeats=True)))
        self.assertEqual(quality['quote_observations'], 180); self.assertEqual(quality['adjacent_repeats'], 179)
        self.assertEqual(quality['event_count'], 179); self.assertEqual(len(quality['events']), 128)
        self.assertTrue(quality['event_details_truncated']); self.assertFalse(quality['repeat_span_is_age'])

    def test_bad_wire_with_recomputed_digest_still_rejects(self):
        changes = [('C', 9, 0), ('I', 11, 'bad'), ('T', 13, bits(float('nan'))),
                   ('T', 14, bits(.1)), ('T', 12, 0), ('M', 11, bits(-1)), ('V', 11, 'unsafe'), ('A', 1, 2)]
        for tag, field, value in changes:
            rows = fixture(); change(rows, tag, field, value)
            with self.assertRaises(ValueError): recorder.inspect_bytes(encode(rows))
        rows = fixture(failed=('point',)); change(rows, 'D', 11, bits(1), key='point')
        with self.assertRaises(ValueError): recorder.inspect_bytes(encode(rows))

    def test_frames_short_rule_fields_ascii_controls_size_and_checksum_reject(self):
        for raw in (b'', b'\xff', b'x' * (recorder.MAX_BYTES + 1), b'H\tbad\r\n'):
            with self.assertRaises(ValueError): recorder.inspect_bytes(raw)
        rows = fixture(rules=1); index = next(i for i, r in enumerate(rows) if r.startswith('R\t'))
        for tag in ('R', 'L'):
            modified = list(rows); modified[index] = tag
            with self.assertRaises(ValueError): recorder.inspect_bytes(encode(modified))
        raw = encode(fixture())
        for bad in (raw.replace(b'1026', b'1027', 1), raw + b'x', raw.replace(b'\r\n', b'\n', 1)):
            with self.assertRaises(ValueError): recorder.inspect_bytes(bad)

    def test_ended_stop_count_premature_end_and_storage_tail(self):
        rows = fixture()
        for bad in (rows + [rows[1]], rows[:-1] + ['S\t13\t0\t0'], rows[:-1] + [f'E\t54\t3\t{SECOND+2}\t2006000']):
            with self.assertRaises(ValueError): recorder.inspect_bytes(encode(bad))
        parsed = recorder.inspect_bytes(encode(rows[:-1]) + b'C\t')
        self.assertEqual(parsed['capture_status'], 'incomplete'); self.assertTrue(parsed['truncated_tail'])

    def test_market_header_never_enables135_or_financial_admission(self):
        raw = encode(fixture(kind='market_declared')); quality = recorder.quality_report(raw)
        for key, value in DENIED.items(): self.assertEqual(quality[key], value)
        self.assertFalse(quality['native_to135_conversion_available']); self.assertEqual(quality['financial_engine_events'], 0)
        with self.assertRaises(ValueError): Replay(raw, canonical(expected_policy()))
        with self.assertRaises(ValueError): paired_capture_132.inspect_bytes(raw)

    def test_native_source_scope_matches_spec_and_guards_surround_reads(self):
        source = (ROOT / 'mt5/Scripts/ForexDemoContextRecorder136.mq5').read_text()
        spec = json.loads((ROOT / 'config/context-recorder-136.json').read_bytes())
        self.assertEqual(spec['nominal_computer_gmt_dates'], list(recorder.DATES))
        self.assertEqual(spec['max_queries'], recorder.MAX_QUERIES); self.assertEqual(spec['max_bytes'], recorder.MAX_BYTES)
        self.assertIn('input bool CollectEvidence = false;', source)
        self.assertLess(source.index('if(!CollectEvidence)'), source.index('int reason=Guard136(false)'))
        self.assertIn('NextQuery136(clock136,tag,key)', source); self.assertIn('CheckCollectorClock136(clock136', source)
        self.assertIn('reason!=14 && Append136', source)
        self.assertLess(source.index('ReserveCollectorBytes136'), source.index('ulong size=FileSize(file136)'))
        self.assertIn('size!=0 || error!=0', source); self.assertIn('if(exists || (error!=0 && error!=5019)) return false;', source)
        for name in ('Integer136', 'Double136', 'Currency136', 'Tick136', 'Clocks136', 'Margin136', 'Commissions136'):
            start = source.index('bool ' + name + '('); end = source.index('\n}', start)
            body = source[start:end]
            self.assertIn('Begin136(', body); self.assertIn('if(!After136()) return false;', body)
            self.assertLess(body.index('if(!After136()) return false;'), body.index('Record136('))
        for forbidden in ('OrderSend(', 'OrderCheck(', 'CopyTicks', 'CopyRates', 'SymbolSelect(', 'WebRequest(', '#import',
                          'FILE_COMMON', 'FILE_SHARE', 'ClockReason107(', 'CheckCostClock128(', 'CheckContextRun136('):
            self.assertNotIn(forbidden, source)
        for line in source.splitlines():
            if any(token in line for token in ('StringFormat(', 'PrintFormat(', 'Record136(')):
                self.assertNotIn('private_login136', line); self.assertNotIn('private_server136', line)

    def test_read_only_cli_matches_library_and_sanitizes_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'Context136.txt'; raw = encode(fixture()); path.write_bytes(raw)
            report = recorder.quality_report(raw)
            for fmt in ('json', 'markdown'):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/context-recorder-136.py'), str(path), '--format', fmt], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                if fmt == 'json': self.assertEqual(json.loads(result.stdout), report)
                else: self.assertEqual(result.stdout, recorder.markdown(report))
                self.assertEqual(path.read_bytes(), raw)
            path.write_bytes(b'bad account_identifier_placeholder')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/context-recorder-136.py'), str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1); self.assertNotIn('account_identifier_placeholder', result.stdout + result.stderr)
            path.unlink(); path.symlink_to(Path(temp) / 'missing')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/context-recorder-136.py'), str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1)


if __name__ == '__main__': unittest.main()
