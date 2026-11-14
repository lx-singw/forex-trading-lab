"""Scope-limited differential checks against actual frozen arithmetic methods."""
import unittest
from forex_demo_lab.elliott_full.crosscheck import audit,sizing_case,accounting_case


class DifferentialTests(unittest.TestCase):
    def test_declared_sizing_and_accounting_matrix(self):
        result=audit()
        self.assertEqual(48,len(result["sizing"]))
        self.assertEqual(24,len(result["accounting"]))
        self.assertTrue(all(r["matched"] for r in result["sizing"]+result["accounting"]))
        self.assertEqual(4,len(result["timing_differences"]))
        self.assertTrue(all(r["status"]=="known_timing_difference" for r in result["timing_differences"]))
        self.assertFalse(result["orders_available"])

    def test_daily_headroom_rejection_agrees(self):
        result=sizing_case(1,"base",".00100","10000","10099")
        self.assertFalse(result["admitted"])
        self.assertEqual("daily_headroom",result["new_reason"])

    def test_invalid_reference_case_rejected(self):
        with self.assertRaises(ValueError): accounting_case(1,"base","unknown")


if __name__=="__main__":
    unittest.main()
