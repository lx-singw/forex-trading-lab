import unittest

from tools.ev_delay_sensitivity_233 import EntryWindow, comparison, selection_breakpoints


class DelaySensitivityTests(unittest.TestCase):
    def test_strict_boundary_shifts_selection(self):
        window = EntryWindow(100, (110, 120, 130))
        self.assertEqual(window.select(9, wait_for_quote=False), 110)
        self.assertEqual(window.select(10, wait_for_quote=False), 120)
        self.assertEqual(window.select(0, wait_for_quote=True), 120)
        self.assertEqual(window.select(10, wait_for_quote=True), 130)
        self.assertIsNone(window.select(20, wait_for_quote=True))
        self.assertEqual(selection_breakpoints((window,)), [0, 10, 20, 30])

    def test_late_selected_open_stays_unavailable(self):
        window = EntryWindow(100, (110, 120))
        result = comparison((window,), {110}, 0)
        self.assertEqual(result["clock"], 0)
        self.assertEqual(result["clock_late"], 1)
        self.assertEqual(result["first_possible_quote_only"], 1)
        self.assertEqual(result["same_open"], 0)

    def test_equal_totals_can_hide_different_openings(self):
        windows = (EntryWindow(100, (100, 110)), EntryWindow(120, (130, 140)), EntryWindow(150, ()))
        result = comparison(windows, set(), 0)
        self.assertEqual(result["clock"], 2)
        self.assertEqual(result["first_possible_quote"], 2)
        self.assertEqual(result["same_open"], 1)
        self.assertEqual(result["different_open"], 1)
        self.assertEqual(result["neither"], 1)
