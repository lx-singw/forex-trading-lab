import csv
import io
import runpy
import tempfile
import unittest
import zipfile
from pathlib import Path

from forex_demo_lab.exness_diagnostics_b import audit_month

ROOT = Path(__file__).resolve().parents[1]


class ExnessSupplementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'original.zip'

    def row(self, stamp='2023-03-01 00:00:03.282Z', bid='1.0576699999999999', ask='1.05774'):
        return ['exness', 'EURUSD', stamp, bid, ask]

    def audit(self, rows):
        stream = io.StringIO(newline='')
        csv.writer(stream).writerows([['Exness', 'Symbol', 'Timestamp', 'Bid', 'Ask'], *rows])
        with zipfile.ZipFile(self.path, 'w') as archive:
            archive.writestr('original.csv', stream.getvalue())
        return audit_month(self.path, '2023-03')

    def test_exact_derivation_preserves_both_versions(self):
        self.assertTrue(runpy.run_path(str(ROOT / 'scripts/derive-exness-024b.py'))['verify']())

    def test_observed_format_keeps_precision_and_original_endpoint(self):
        result = self.audit([self.row()])
        self.assertTrue(result['diagnostic_pass'])
        self.assertEqual(result['first'], self.row()[2])
        self.assertEqual(result['hour_counts']['2023-03-01T00:00:00Z'], 1)
        self.assertFalse(result['annual_eligible'])

    def test_alternative_tags_and_timestamp_variants_still_fail(self):
        uppercase = self.row()
        uppercase[0] = 'Exness'
        result = self.audit([uppercase, self.row('2023-03-01T00:00:03.282Z'),
                             self.row('2023-03-01 00:00:03.282+00:00'),
                             self.row('2023-03-01 00:00:03.28Z')])
        self.assertEqual(result['errors'], {'provider_or_symbol': 1, 'timestamp': 3})

    def test_price_checks_use_full_precision_and_reject_nonfinite(self):
        result = self.audit([self.row(bid='1.0000000000000001', ask='1.0'),
                             self.row(bid='NaN'), self.row(ask='Infinity')])
        self.assertEqual(result['errors'], {'price': 3})

    def test_month_edges_and_calendar_remain_strict(self):
        result = self.audit([self.row('2023-04-01 00:00:00.000Z'),
                             self.row('2023-03-32 00:00:00.000Z')])
        self.assertEqual(result['errors'], {'month_boundary': 1, 'timestamp': 1})

    def test_ties_gaps_and_backwards_with_independent_original_accounting(self):
        result = self.audit([self.row(), self.row(),
                             self.row('2023-03-01 02:00:00.000Z'), self.row()])
        self.assertEqual(result['exact_duplicate_records'], 1)
        self.assertEqual(result['tied_timestamps'], 1)
        self.assertEqual(result['backward_timestamps'], 1)
        self.assertEqual(len(result['long_gaps']), 1)
        account = runpy.run_path(str(ROOT / 'scripts/check-exness-024b.py'))['account']
        independent, rows = account(self.path, '2023-03')
        self.assertEqual(rows, 4)
        for key, value in independent.items():
            self.assertEqual(value, result[key], key)


if __name__ == '__main__':
    unittest.main()
