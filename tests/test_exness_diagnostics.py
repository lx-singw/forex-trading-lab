import csv
import io
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from forex_demo_lab.exness_diagnostics import HEADER, audit_month, timestamp_ms


class ExnessDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'quotes.zip'

    def write(self, rows, header=HEADER, name='quotes.csv'):
        content = io.StringIO(newline='')
        csv.writer(content).writerows([header, *rows])
        with zipfile.ZipFile(self.path, 'w') as archive:
            archive.writestr(name, content.getvalue())

    def row(self, stamp='2023-03-01T00:00:00.000Z', bid='1.1', ask='1.2'):
        return ['Exness', 'EURUSD', stamp, bid, ask]

    def audit(self, **kwargs):
        return audit_month(self.path, '2023-03', **kwargs)

    def test_tied_order_and_nonadjacent_exact_duplicate_within_group(self):
        self.write([self.row(), self.row(bid='1.15'), self.row(),
                    self.row('2023-03-31T23:59:59.999Z')])
        result = self.audit()
        self.assertTrue(result['diagnostic_pass'])
        self.assertEqual((result['rows'], result['tied_timestamps'],
                          result['exact_duplicate_records']), (4, 2, 1))
        self.assertEqual((result['observed_hours'], result['empty_hours']), (2, 742))
        self.assertFalse(result['annual_eligible'])

    def test_boundary_month_and_leap_calendar(self):
        self.write([self.row('2023-02-28T23:59:59.999Z'),
                    self.row('2023-04-01T00:00:00.000Z'),
                    self.row('2023-03-32T00:00:00.000Z')])
        result = self.audit()
        self.assertEqual(result['errors'], {'month_boundary': 2, 'timestamp': 1})
        self.assertFalse(result['diagnostic_pass'])
        self.assertEqual(timestamp_ms('2024-02-29T00:00:00.123Z') % 1000, 123)
        with self.assertRaises(ValueError):
            timestamp_ms('2023-02-29T00:00:00.000Z')

    def test_timestamp_requires_utc_and_exact_milliseconds(self):
        self.write([self.row(value) for value in (
            '2023-03-01T00:00:00Z', '2023-03-01T00:00:00.000+00:00',
            '2023-03-01 00:00:00.000Z', '2023-03-01T00:00:00.0000Z')])
        self.assertEqual(self.audit()['errors'], {'timestamp': 4})

    def test_nonfinite_nonpositive_crossed_and_malformed_prices(self):
        pairs = [('NaN', '1.2'), ('1.1', 'Infinity'), ('-1', '1'),
                 ('0', '1'), ('1.2', '1.1'), ('bad', '1.2'), ('1', 'sNaN')]
        self.write([self.row(bid=bid, ask=ask) for bid, ask in pairs])
        result = self.audit()
        self.assertEqual(result['errors'], {'price': len(pairs)})
        self.assertEqual(result['valid_rows'], 0)

    def test_schema_failure_does_not_interpret_rows(self):
        self.write([self.row()], header=['Symbol', 'Bid', 'Ask'])
        result = self.audit()
        self.assertEqual(result['rows'], 0)
        self.assertEqual(result['errors'], {'header': 1})
        self.assertEqual(result['error_examples']['header'][0]['csv_record'], 1)

    def test_symbol_provider_and_field_count(self):
        rows = [self.row(), self.row(), self.row() + ['extra']]
        rows[0][0] = 'Other'
        rows[1][1] = 'EURUSDm'
        self.write(rows)
        self.assertEqual(self.audit()['errors'], {'provider_or_symbol': 2, 'field_count': 1})

    def test_backwards_is_preserved_not_sorted(self):
        self.write([self.row('2023-03-01T02:00:00.000Z'), self.row()])
        result = self.audit()
        self.assertEqual(result['backward_timestamps'], 1)
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['first'], '2023-03-01T02:00:00.000Z')
        self.assertEqual(result['last'], '2023-03-01T00:00:00.000Z')
        self.assertFalse(result['diagnostic_pass'])

    def test_gap_threshold_is_strict_and_month_edges_are_counted(self):
        self.write([self.row(), self.row('2023-03-01T01:00:00.000Z'),
                    self.row('2023-03-01T02:00:00.001Z')])
        result = self.audit()
        self.assertEqual(len(result['long_gaps']), 1)
        self.assertEqual(result['long_gaps'][0]['milliseconds'], 3600001)
        self.assertEqual(result['empty_hours'], 741)

    def test_paths_and_non_csv_are_rejected(self):
        for name in ('../quotes.csv', 'nested/quotes.csv', 'C:\\quotes.csv', 'quotes.txt'):
            with self.subTest(name=name):
                self.write([self.row()], name=name)
                self.assertIn('archive_or_stream_failure', self.audit()['errors'])

    def test_member_and_uncompressed_caps(self):
        self.write([self.row()])
        self.assertIn('archive_or_stream_failure', self.audit(max_uncompressed=8)['errors'])
        with zipfile.ZipFile(self.path, 'w') as archive:
            for index in range(65):
                archive.writestr(f'quotes{index}.csv', 'x')
        self.assertIn('archive_or_stream_failure', self.audit()['errors'])

    def test_corrupt_crc_and_truncated_zip_fail_before_rows(self):
        self.write([self.row()])
        content = bytearray(self.path.read_bytes())
        name_length, extra_length = struct.unpack_from('<HH', content, 26)
        content[30 + name_length + extra_length + 2] ^= 1
        self.path.write_bytes(content)
        result = self.audit()
        self.assertEqual(result['rows'], 0)
        self.assertIn('archive_or_stream_failure', result['errors'])
        self.path.write_bytes(content[:20])
        self.assertFalse(self.audit()['diagnostic_pass'])

    def test_empty_directory_allowed_but_no_empty_dataset_pass(self):
        self.write([])
        with zipfile.ZipFile(self.path, 'a') as archive:
            archive.writestr('safe/', '')
        self.assertFalse(self.audit()['diagnostic_pass'])

    def test_offending_record_samples_bounded_without_losing_counts(self):
        self.write([self.row(bid='0')] * 25)
        result = self.audit()
        self.assertEqual(result['errors']['price'], 25)
        self.assertEqual(len(result['error_examples']['price']), 20)
        self.assertEqual(result['rows'], 25)


if __name__ == '__main__':
    unittest.main()
