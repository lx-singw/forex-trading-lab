import copy
import csv
import io
import unittest

from forex_demo_lab.model import Bar, Config, signal
from forex_demo_lab.observer_parity import (CLOSED, FIELDS, check_runtime, fixtures,
                                          mql_inputs, observer_body, validate_fixtures)


def results(cases):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, FIELDS)
    writer.writeheader()
    for case in cases:
        writer.writerow(dict(case_id=case['case_id'], kind=case['kind'], **case['expected']))
    return stream.getvalue()


class ObserverParityTests(unittest.TestCase):
    def test_all_expected_fields_checked_and_flags_remain_false(self):
        cases = fixtures()
        review = check_runtime(results(cases), cases)
        self.assertEqual(review['comparisons'], len(cases)*8)
        self.assertFalse(review['demo_execution_ready'])
        self.assertFalse(review['actual_broker_account_switch_verified'])

    def test_missing_extra_duplicate_reordered_cases_rejected(self):
        cases = fixtures()
        for changed in (cases[:-1], cases + cases[:1], cases[:1] + cases, cases[::-1]):
            with self.subTest(length=len(changed)), self.assertRaises(ValueError):
                check_runtime(results(changed), cases)

    def test_each_wrong_runtime_field_is_rejected(self):
        cases = fixtures()
        changes = dict(init=1, observations=2, side='SELL', stop=.5, removed=1,
                       account_reads=1, last_closed=0, copy_contract=0)
        for key, value in changes.items():
            changed = copy.deepcopy(cases)
            changed[7]['expected'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_runtime(results(changed), cases)

    def test_nonfinite_stop_and_malformed_schema_rejected(self):
        cases = fixtures()
        for value in ('nan', 'inf', '-inf'):
            changed = copy.deepcopy(cases); changed[7]['expected']['stop'] = value
            with self.assertRaises(ValueError): check_runtime(results(changed), cases)
        with self.assertRaises(ValueError): check_runtime('wrong\n', cases)

    def test_body_bytes_preserved_and_ambiguous_marker_rejected(self):
        prefix = b'#property strict\r\n'
        body = b'datetime last_closed = 0;\r\nvoid OnTick() {}\r\n'
        self.assertEqual(observer_body(prefix+body), body)
        for data in (prefix, body+body):
            with self.assertRaises(ValueError): observer_body(data)

    def test_frozen_inputs_deterministic_and_exclude_expected_outcomes(self):
        self.assertEqual(fixtures(), fixtures())
        cases = fixtures(); generated = mql_inputs(cases)
        changed = copy.deepcopy(cases); changed[7]['expected']['stop'] = 999
        self.assertEqual(generated, mql_inputs(changed))
        self.assertNotIn(b'expected', generated)

    def test_wrong_dates_duplicate_names_and_short_history_rejected(self):
        cases = fixtures()
        for mutation in ('date', 'short', 'duplicate'):
            changed = copy.deepcopy(cases)
            if mutation == 'date': changed[0]['bars'][0]['time'] = '2025-01-02T00:00:00+00:00'
            elif mutation == 'short': changed[0]['bars'].pop()
            else: changed[1]['case_id'] = changed[0]['case_id']
            with self.assertRaises(ValueError): validate_fixtures(changed)

    def test_zero_atr_fixture_crosses_but_observer_must_suppress(self):
        case = next(c for c in fixtures() if c['case_id'] == 'zero_atr_cross')
        side, distance = signal([Bar.from_dict(b) for b in case['bars']], Config())
        self.assertEqual((side, distance), (1, 0))
        self.assertEqual(case['expected']['observations'], 0)

    def test_restart_gap_and_final_account_rechecks_are_distinct(self):
        cases = {c['case_id']:c for c in fixtures()}
        self.assertEqual(cases['restart_no_replay']['expected']['last_closed'], CLOSED)
        self.assertEqual(cases['tick_switch_real']['expected']['removed'], 1)
        self.assertEqual(cases['final_switch_real']['expected']['removed'], 0)
        self.assertEqual(cases['final_switch_real']['expected']['account_reads'], 3)


if __name__ == '__main__': unittest.main()
