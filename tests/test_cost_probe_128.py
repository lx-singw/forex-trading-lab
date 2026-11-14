from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import cost_probe_128 as probe

ROOT = Path(__file__).resolve().parents[1]
SECOND = int(datetime(2026, 10, 14, 12, tzinfo=timezone.utc).timestamp())


def bits(value):
    return struct.pack('>d', float(value)).hex().upper()


def encode(payloads):
    chain = '0' * 64
    lines = []
    for payload in payloads:
        chain = hashlib.sha256((chain + '\t' + payload + '\n').encode('ascii')).hexdigest().upper()
        lines.append(payload + '\t' + chain + '\r\n')
    return ''.join(lines).encode('ascii')


def fixture(rules=1, tiers=2, commission_error=0, returned=None, failed_margin=(), kind='invented_fixture'):
    payloads = [f'H\tFXDL_COST128_V1\t{kind}\t2026.10.14\t{SECOND}\t1000']
    sequence = 0

    def add(tag, key, values, succeeded=True, error=0):
        nonlocal sequence
        sequence += 1
        before = 1000 + sequence * 1000
        payloads.append(f'A\t{sequence}\t{tag}\t{key}')
        payloads.append('\t'.join(map(str, [tag, sequence, key, SECOND, SECOND, SECOND,
                                           before, before + 10, before + 20, int(succeeded), error, *values])))

    clocks = [SECOND + 10800, SECOND + 10800, SECOND, SECOND + 7200, -7200, 0]
    add('C', 'clock_before', clocks)
    result = rules if returned is None else returned
    ok = result >= 0 and commission_error == 0
    add('K', 'commissions', [result], ok, commission_error)
    if ok:
        for i in range(rules):
            payloads.append(f'R\t2\t{i}\tEMPTY\t0\t2\t0\t0\t0\t{tiers}')
            for j in range(tiers):
                payloads.append('\t'.join(['T', '2', str(i), str(j), '1', '1',
                                           bits(-.2), bits(0), bits(100), bits(j), bits(j + 1), 'USD']))
    for side in ('buy', 'sell'):
        ok = side not in failed_margin
        add('M', side, [bits(1 if ok else 0), bits(1 if ok else 0)], ok, 4303 if not ok else 0)
    add('C', 'clock_after', clocks)
    payloads.append(f'E\t5\t{SECOND}\t6030')
    return payloads


def changed(payloads, tag, column, value, key=None):
    result = list(payloads)
    for i, payload in enumerate(result):
        f = payload.split('\t')
        if f[0] == tag and (key is None or f[2] == key):
            f[column] = str(value)
            result[i] = '\t'.join(f)
            return result
    raise AssertionError('missing fixture row')


class Cost128Tests(unittest.TestCase):
    def test_complete_reported_rules_with_rebate_bits_and_raw_conditions(self):
        result = probe.inspect_bytes(encode(fixture()))
        self.assertEqual(result['capture_status'], 'complete')
        self.assertEqual(result['queries_recorded'], 5)
        self.assertEqual(result['commission_state'], 'reported_rules')
        rule = result['commission_rules'][0]
        self.assertIsNone(rule['currency'])
        self.assertEqual(rule['mode_charge'], 2)
        self.assertEqual(len(rule['tiers']), 2)
        self.assertEqual(rule['tiers'][0]['value'], '-0.2')
        self.assertEqual(rule['tiers'][0]['native_bits'][0], bits(-.2))

    def test_no_cost_conversion_or_admission_even_for_market_header(self):
        result = probe.inspect_bytes(encode(fixture(kind='market_declared')))
        for flag in ('producer_authenticated', 'source_utc_certified', 'receipt_utc_certified',
                     'historical_cost_terms_certified', 'market_data_qualified', 'paper_evaluation_available',
                     'orders_available', 'real_money_execution_available'):
            self.assertIs(result[flag], False)
        for value in ('commission_cost_USD', 'margin_requirement_USD', 'slippage_terms'):
            self.assertIsNone(result[value])

    def test_successful_empty_rules_distinct_from_failed_query(self):
        empty = probe.inspect_bytes(encode(fixture(rules=0)))
        failed = probe.inspect_bytes(encode(fixture(returned=-1, commission_error=4303)))
        self.assertEqual(empty['commission_state'], 'reported_empty')
        self.assertEqual(failed['commission_state'], 'query_failed')
        self.assertEqual(empty['commission_rules'], failed['commission_rules'])
        self.assertIsNone(empty['commission_cost_USD'])

    def test_failed_positive_return_and_minus_one_without_error_remain_failed(self):
        for returned, error in ((2, 4303), (-1, 0)):
            result = probe.inspect_bytes(encode(fixture(returned=returned, commission_error=error)))
            self.assertEqual(result['commission_state'], 'query_failed')
            row = next(r for r in result['rows'] if r['type'] == 'K')
            self.assertEqual(row['native_return_count'], returned)

    def test_failed_margin_is_unknown_and_successful_zero_preserved(self):
        result = probe.inspect_bytes(encode(fixture(failed_margin=('buy',))))
        margin = next(r for r in result['rows'] if r.get('key') == 'buy')
        self.assertIsNone(margin['initial_rate'])
        self.assertIsNone(margin['maintenance_rate'])
        zero = changed(fixture(), 'M', 11, bits(0), 'buy')
        result = probe.inspect_bytes(encode(zero))
        self.assertEqual(next(r for r in result['rows'] if r.get('key') == 'buy')['initial_rate'], '0.0')
        self.assertIsNone(result['margin_requirement_USD'])

    def test_worst_accepted_rule_and_tier_counts(self):
        data = encode(fixture(rules=8, tiers=16))
        self.assertLess(len(data), 65536)
        result = probe.inspect_bytes(data)
        self.assertEqual(len(result['commission_rules']), 8)
        self.assertEqual(sum(len(r['tiers']) for r in result['commission_rules']), 128)

    def test_rules_without_tiers_are_preserved_without_fee_assumption(self):
        result = probe.inspect_bytes(encode(fixture(rules=2, tiers=0)))
        self.assertEqual([r['tiers'] for r in result['commission_rules']], [[], []])
        self.assertIsNone(result['commission_cost_USD'])

    def test_unknown_signed_conditions_are_raw(self):
        data = changed(fixture(), 'R', 5, -2147483648)
        result = probe.inspect_bytes(encode(data))
        self.assertEqual(result['commission_rules'][0]['mode_charge'], -2147483648)
        self.assertIsNone(result['commission_cost_USD'])

    def test_every_pending_native_attempt_can_stop_without_an_outcome(self):
        payloads = fixture()
        for index, payload in enumerate(payloads):
            if payload.startswith('A\t'):
                q = int(payload.split('\t')[1])
                result = probe.inspect_bytes(encode(payloads[:index + 1] + [f'S\t7\t{q}']))
                self.assertEqual(result['capture_status'], 'stopped')
                self.assertTrue(result['pending_attempt'])
                self.assertEqual(result['queries_recorded'], q - 1)

    def test_every_partial_rule_payload_stays_incomplete(self):
        payloads = fixture(rules=2)
        for index, payload in enumerate(payloads):
            if payload.startswith(('R\t', 'T\t')):
                result = probe.inspect_bytes(encode(payloads[:index] + ['S\t9\t2']))
                self.assertEqual(result['commission_state'], 'incomplete')
                self.assertEqual(result['commission_rules'], [])
                self.assertTrue(result['pending_rule_payload'])

    def test_guard_stops_before_commission_count_are_preserved(self):
        payloads = fixture()
        result = probe.inspect_bytes(encode(payloads[:4] + ['S\t21\t2']))
        self.assertTrue(result['pending_attempt'])
        self.assertEqual(result['commission_state'], 'incomplete')

    def test_missing_end_and_torn_rule_tail(self):
        result = probe.inspect_bytes(encode(fixture()[:-1]))
        self.assertEqual(result['capture_status'], 'incomplete')
        payloads = fixture(); i = next(i for i, p in enumerate(payloads) if p.startswith('T\t'))
        result = probe.inspect_bytes(encode(payloads[:i]) + b'T\t2\t0')
        self.assertTrue(result['truncated_tail'])
        self.assertEqual(result['commission_state'], 'incomplete')

    def test_checksum_and_terminal_continuation_rejected(self):
        data = bytearray(encode(fixture())); data[12] ^= 1
        with self.assertRaises(ValueError): probe.inspect_bytes(bytes(data))
        for extra in ('A\t6\tM\tbuy', 'S\t7\t5'):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(fixture() + [extra]))

    def test_query_rule_tier_order_and_sequence_rejected(self):
        for tag, column, value in (('A', 1, 2), ('R', 2, 1), ('T', 3, 1), ('T', 1, 3), ('A', 3, 'sell')):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), tag, column, value)))

    def test_count_limit_and_return_consistency_rejected(self):
        for tag, column, value in (('K', 11, 9), ('K', 11, -2), ('K', 9, 0), ('K', 10, 4303), ('R', 9, 17)):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), tag, column, value)))

    def test_nonfinite_rule_margin_and_negative_margin_rejected(self):
        for tag, column, value in (('T', 6, bits(float('inf'))), ('T', 10, bits(float('nan'))),
                                   ('M', 11, bits(-1)), ('M', 12, bits(float('inf')))):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), tag, column, value)))

    def test_failed_margin_payload_cannot_smuggle_nonzero_value(self):
        data = changed(fixture(failed_margin=('buy',)), 'M', 11, bits(1), 'buy')
        with self.assertRaises(ValueError): probe.inspect_bytes(encode(data))

    def test_currency_tokens_reject_arbitrary_strings(self):
        for value in ('usd', 'account_identifier', 'USD extra', 'US', '123', 'NA'):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), 'R', 3, value)))

    def test_short_and_extra_rehashed_fields_raise_value_error(self):
        payloads = fixture()
        for index, payload in enumerate(payloads):
            if payload.startswith(('C\t', 'K\t', 'M\t', 'R\t', 'T\t')):
                fields = payload.split('\t')
                for size in range(1, len(fields)):
                    malformed = list(payloads); malformed[index] = '\t'.join(fields[:size])
                    with self.assertRaises(ValueError): probe.inspect_bytes(encode(malformed))
                malformed = list(payloads); malformed[index] += '\textra'
                with self.assertRaises(ValueError): probe.inspect_bytes(encode(malformed))

    def test_premature_end_skipped_rule_and_missing_outcome_rejected(self):
        payloads = fixture()
        for malformed in (payloads[:5] + [f'E\t2\t{SECOND}\t3030'],
                          [p for p in payloads if not p.startswith('R\t')],
                          [p for p in payloads if not p.startswith('K\t')]):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(malformed))

    def test_clock_reversal_jump_deadline_wrong_date_rejected(self):
        for column, value in ((3, SECOND-1), (7, 1999), (5, SECOND+3), (8, 60001001)):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), 'C', column, value)))
        payloads = fixture(); payloads[0] = payloads[0].replace('2026.10.14', '2026.10.15')
        with self.assertRaises(ValueError): probe.inspect_bytes(encode(payloads))

    def test_size_encoding_framing_and_enum_width_rejected(self):
        for data in (b'', b'x'*65537, b'\xff', encode(fixture()).replace(b'\r\n', b'\n'), b'\x00'):
            with self.assertRaises(ValueError): probe.inspect_bytes(data)
        for value in (2147483648, -2147483649, '00', '-0'):
            with self.assertRaises(ValueError): probe.inspect_bytes(encode(changed(fixture(), 'R', 4, value)))

    def test_cli_reads_original_unchanged_and_reports_generic_bad_file(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'costs.txt'; p.write_bytes(encode(fixture(rules=0)))
            before = p.read_bytes()
            run = subprocess.run([sys.executable, str(ROOT/'scripts/cost-probe-128.py'), str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0); self.assertEqual(json.loads(run.stdout)['commission_state'], 'reported_empty')
            self.assertEqual(p.read_bytes(), before); self.assertEqual(run.stderr, '')
            p.write_bytes(b'arbitrary identifier')
            run = subprocess.run([sys.executable, str(ROOT/'scripts/cost-probe-128.py'), str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1); self.assertNotIn('identifier', run.stdout + run.stderr)

    def test_inspect_file_refuses_direct_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'costs.txt'; p.write_bytes(encode(fixture()))
            link = Path(folder)/'link'; link.symlink_to(p)
            with self.assertRaises(ValueError): probe.inspect_file(link)

    def test_native_scope_default_off_bounds_and_guard_before_payload(self):
        source = (ROOT/'mt5/Scripts/ForexDemoCostProbe128.mq5').read_text()
        config = json.loads((ROOT/'config/cost-probe-128.json').read_text())
        self.assertEqual(config['max_queries'], 5); self.assertFalse(config['orders_available'])
        self.assertIn('input bool CollectEvidence = false;', source)
        for forbidden in ('OrderSend', 'CTrade', 'trade.Buy', 'trade.Sell', 'WebRequest', 'SymbolSelect(', 'CopyTicks',
                          'CopyRates', 'FILE_COMMON', 'FILE_SHARE', '#import', 'ClockReason107'):
            self.assertNotIn(forbidden, source)
        after_call = source.index('if(!After128()) return false;', source.index('int count=SymbolInfoCommissions'))
        output = source.index('Record128("K","commissions"')
        self.assertLess(after_call, output)
        self.assertIn('CostRuleCountReason128(count,ArraySize(rules))', source)
        self.assertIn('if(!SerializeGuard128()) return false;', source)
