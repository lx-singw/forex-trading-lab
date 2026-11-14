from datetime import datetime, timedelta
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('corroborate009', Path(__file__).resolve().parents[1] / 'scripts/corroborate-history-009.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RelativePriceTests(unittest.TestCase):
    def fixture(self):
        start = datetime(2020, 1, 14)
        reference = {start + timedelta(hours=i): 1.1 + i * .001 for i in range(32)}
        source = {start + timedelta(hours=i): reference[start + timedelta(hours=i+7)] for i in range(8, 20)}
        return source, reference

    def test_unique_alignment_reports_all_offsets(self):
        source, reference = self.fixture()
        r = module.compare('2020-01-14', source, reference)
        self.assertTrue(r['relative_price_screen_passed'])
        self.assertEqual(r['best_offset'], 7)
        self.assertEqual(len(r['all_offsets']), 10)

    def test_missing_hour_cannot_pass_from_partial_matches(self):
        source, reference = self.fixture()
        del source[datetime(2020, 1, 14, 19)]
        self.assertFalse(module.compare('2020-01-14', source, reference)['relative_price_screen_passed'])

    def test_flat_prices_do_not_identify_a_clock_offset(self):
        source, reference = self.fixture()
        source = dict.fromkeys(source, 1.1)
        reference = dict.fromkeys(reference, 1.1)
        self.assertFalse(module.compare('2020-01-14', source, reference)['relative_price_screen_passed'])
