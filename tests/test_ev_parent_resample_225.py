"""Exercise exact dual-side resampling and partial-bucket accounting."""

import unittest

from tools.ev_parent_resample_225 import HOUR, START, compare

FIRST = (3, 6, 2, 4, 5, 8, 4, 6)
LAST = (4, 5, 1, 2, 6, 9, 3, 4)
AGGREGATE = (3, 6, 1, 2, 5, 9, 3, 4)


class EvParentResampleTests(unittest.TestCase):
    def test_an_exact_match_can_have_an_interior_gap_and_a_late_first_child(self):
        base = START
        hourly = {base + HOUR: FIRST, base + 3 * HOUR: LAST}
        scheduled = {base + n * HOUR for n in (1, 2, 3)}
        report = compare(hourly, {base: AGGREGATE}, scheduled, 4 * HOUR)

        self.assertEqual({"matching_ohlc": 1, "short_ordinary_session_buckets": 1,
                          "published_buckets_missing_ordinary_h1": 1}, report["published_bucket_counts"])
        self.assertEqual({1: 1}, report["hours_from_bucket_label_to_first_child"])
        self.assertEqual({0: 1}, report["hours_from_last_child_end_to_bucket_end"])

    def test_missing_buckets_nulls_and_field_differences_stay_visible(self):
        first, second, third, fourth = (START + n * 4 * HOUR for n in range(4))
        report = compare(
            {first: FIRST, second: LAST, third: (None, *FIRST[1:])},
            {first: (*FIRST[:-1], 5), third: FIRST, fourth: FIRST},
            {first, second, third}, 4 * HOUR,
        )
        self.assertEqual({"ac": 1}, report["different_fields"])
        self.assertEqual(1, report["published_bucket_counts"]["missing_price_fields"])
        self.assertEqual(1, report["published_bucket_counts"]["no_published_h1_children"])
        self.assertEqual(1, report["buckets_with_h1_children_but_no_published_parent"])
        self.assertEqual(1, report["published_buckets_without_ordinary_h1"])
