"""Check close clipping, coverage, and the fixed first scheduled opening."""

import unittest

from tools.ev_publication_timing_226 import BEFORE, HOUR, TIED, compare


class EvPublicationTimingTests(unittest.TestCase):
    def test_close_clipping_adds_time_without_moving_the_open(self):
        result = compare((0, 10 * HOUR, 11 * HOUR), set())
        self.assertEqual({3: 1}, result["h4_close_advance_hours_when_clipped"])
        self.assertEqual(0, result["first_scheduled_open_changed"])
        models = result["models"]
        for model, lead in (("utc_bucket_end", 6), ("ordinary_session_end", 9)):
            with self.subTest(model=model):
                self.assertEqual({lead: 1}, models[model]["h4_close_to_first_open_hours_when_strictly_early"])
                cases = models[model]["timing_cases"]
                self.assertEqual(1, cases[1]["status_counts"][BEFORE])
                self.assertEqual(1, cases[2]["status_counts"][TIED])
                self.assertEqual(0, cases[3]["ceiling_if_decision_precedes_tied_open"])

    def test_missing_parent_and_open_block_once_without_advancing_to_later_hour(self):
        result = compare((0, 10 * HOUR, 11 * HOUR), {0, 10 * HOUR})
        self.assertEqual(2, result["h4_buckets_missing_one_or_more_scheduled_children"])
        for model in result["models"].values():
            case = model["timing_cases"][0]
            self.assertEqual(1, case["status_counts"][BEFORE])
            self.assertEqual({"missing_h4_child and missing_first_h1": 1},
                             case["timely_or_tied_slots_blocked_by_coverage"])
            self.assertEqual(0, case["coverage_adjusted_ceiling_without_same_time_order"])
