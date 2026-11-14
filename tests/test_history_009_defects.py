import importlib.util
from pathlib import Path
import tempfile
import unittest

import test_history_009 as fixtures

spec = importlib.util.spec_from_file_location('history009defects', Path(__file__).resolve().parents[1] / 'scripts/audit-history-009-defects.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DefectReviewTests(unittest.TestCase):
    def test_rollback_is_reported_without_discarding_later_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            fixtures.RawHistoryTests().fixture(p, '20200102 195956508,1.1,1.1001,0\n20200102 190000147,1.1,1.1001,0\n20200102 190001147,1.1,1.1001,0\n')
            r = module.defects(p, '202001')
            self.assertEqual(r['rows_examined'], 3)
            self.assertEqual(r['defect_counts'], {'backward_source_timestamp': 1})
            self.assertAlmostEqual(r['examples'][0]['backward_seconds'], 3596.361)
            self.assertFalse(r['structural_checks_passed'])
            self.assertFalse(r['performance_evaluation_ready'])

    def test_multiple_defects_remain_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            fixtures.RawHistoryTests().fixture(p, '20200102 120000000,nan,1.1,0\n20200102 250000000,1.1,1.1001,0\nbad\n')
            r = module.defects(p, '202001')
            self.assertEqual(r['defect_counts'], {'invalid_quote_or_volume': 1, 'invalid_timestamp': 1, 'invalid_schema': 1})
