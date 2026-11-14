import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('history009', Path(__file__).resolve().parents[1] / 'scripts/history-009.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RawHistoryTests(unittest.TestCase):
    def fixture(self, folder, rows, name='DAT_ASCII_EURUSD_T_202001.csv'):
        with zipfile.ZipFile(folder / 'original.zip', 'w') as z:
            z.writestr(name, rows)
        metadata = {'source': 'HistData', 'page': 'https://www.histdata.com/download-free-forex-historical-data/?/ascii/tick-data-quotes/eurusd/2020/1',
                    'sha256': module.sha256(folder / 'original.zip'), 'bytes': (folder / 'original.zip').stat().st_size}
        (folder / 'download.json').write_text(json.dumps(metadata))

    def test_raw_clock_is_not_converted_and_same_ms_quotes_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            self.fixture(p, '20200102 120000000,1.1,1.1001,0\n20200102 120000000,1.1001,1.1002,0\n20200102 120000000,1.1001,1.1002,0\n')
            r = module.scan(p, '202001')
            self.assertEqual(r['first_source_label'], '2020-01-02T12:00:00')
            self.assertEqual(r['ticks'], 3)
            self.assertEqual(r['same_millisecond_transitions'], 2)
            self.assertEqual(r['exact_duplicate_transitions'], 1)
            self.assertFalse(r['performance_evaluation_ready'])

    def test_gaps_remain_unreviewed_and_no_hours_are_fabricated(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            self.fixture(p, '20200102 120000000,1.1,1.1001,0\n20200102 140000001,1.2,1.2002,0\n')
            r = module.scan(p, '202001')
            self.assertEqual(r['observed_source_hours'], 2)
            self.assertEqual(r['gaps_over_one_hour'][0]['classification'], 'unreviewed')
            self.assertAlmostEqual(r['gaps_over_one_hour'][0]['seconds'], 7200.001)

    def test_malformed_prices_dates_and_reordered_rows_rejected(self):
        bad = ['20200102 120000000,nan,1.2,0\n', '20200102 120000000,1.2,1.1,0\n',
               '20200202 120000000,1.1,1.2,0\n', '20200102 250000000,1.1,1.2,0\n',
               '20200102 120000000,1.1,1.2,-1\n', '20200102 120000000,1.1,1.2\n',
               '20200102 120000000,1.1,1.2,0\n20200102 110000000,1.1,1.2,0\n']
        for rows in bad:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as temp:
                p = Path(temp); self.fixture(p, rows)
                with self.assertRaises(ValueError): module.scan(p, '202001')

    def test_tampered_archive_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); self.fixture(p, '20200102 120000000,1.1,1.2,0\n')
            with (p / 'original.zip').open('ab') as f: f.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'identity'): module.scan(p, '202001')

    def test_wrong_archive_month_and_undeclared_year_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); self.fixture(p, '', name='DAT_ASCII_EURUSD_T_202002.csv')
            with self.assertRaisesRegex(ValueError, 'Wrong'): module.scan(p, '202001')
            with self.assertRaisesRegex(ValueError, 'outside'): module.binding(p, '202501')

    def test_empty_archive_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); self.fixture(p, '')
            with self.assertRaisesRegex(ValueError, 'Empty'): module.scan(p, '202001')
