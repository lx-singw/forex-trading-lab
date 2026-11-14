import copy
import csv
import io
import unittest
from forex_demo_lab.observer_parity import fixtures
from forex_demo_lab.observer_parity_symbols import CONSTANT_ROWS, NAMES, check_symbols
from test_observer_parity import results


def native(cases, parameters):
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(['case_id', 'raw_init', 'init_name'])
    constants = dict(INIT_SUCCEEDED=0, INIT_FAILED=1, INIT_PARAMETERS_INCORRECT=parameters)
    for case in cases:
        name = NAMES[case['expected']['init']]
        writer.writerow([case['case_id'], -99 if name == 'GUARD' else constants[name], name])
    for row, name in CONSTANT_ROWS: writer.writerow([row, constants[name], name])
    return stream.getvalue()


class ObserverSymbolTests(unittest.TestCase):
    def test_symbolic_contract_does_not_hardcode_parameter_integer(self):
        cases = fixtures()
        for number in (2, 17, 32767):
            review = check_symbols(results(cases), native(cases, number), cases)
            self.assertEqual(review['comparisons'], 304)
            self.assertFalse(review['original_018_strict_review_passed'])
            self.assertFalse(review['demo_execution_ready'])

    def test_missing_extra_and_duplicate_enum_rows_rejected(self):
        cases = fixtures(); lines = native(cases, 17).splitlines()
        for text in ('\n'.join(lines[:-1]), '\n'.join(lines + lines[-1:]),
                     '\n'.join(lines[:2] + lines[1:])):
            with self.assertRaises(ValueError): check_symbols(results(cases), text, cases)

    def test_correct_name_with_wrong_native_value_rejected(self):
        cases = fixtures()
        text = native(cases, 17).replace('wrong_symbol,17,', 'wrong_symbol,2,')
        with self.assertRaises(ValueError): check_symbols(results(cases), text, cases)

    def test_nonzero_initialization_cannot_be_accepted_as_success(self):
        cases = fixtures()
        text = native(cases, 17).replace('wrong_period,17,INIT_PARAMETERS_INCORRECT',
                                        'wrong_period,17,INIT_SUCCEEDED')
        with self.assertRaises(ValueError): check_symbols(results(cases), text, cases)

    def test_enum_constant_aliases_and_changed_original_checks_rejected(self):
        cases = fixtures()
        with self.assertRaises(ValueError): check_symbols(results(cases), native(cases, 1), cases)
        changed = copy.deepcopy(cases); changed[7]['expected']['side'] = 'SELL'
        with self.assertRaises(ValueError): check_symbols(results(changed), native(cases, 17), cases)


if __name__ == '__main__': unittest.main()
