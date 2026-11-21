"""Check candle alignment and the earliest published lower-timeframe row."""

import gzip
import json
import unittest

from tools.ev_opening_resample_223 import COLUMNS, END, START, compare, download, parse, year_bounds


def row(stamp):
    return dict(zip(COLUMNS, (stamp, 1.11, 1.12, 1.10, 1.11, 1.1102, 1.1202, 1.1002, 1.1102, 10), strict=True))


def zipped(document):
    return gzip.compress(json.dumps(document).encode())


class EvOpeningResampleTests(unittest.TestCase):
    def test_earliest_m5_open_counts_even_when_a_later_pair_matches(self):
        first_pair = (1, 3)
        report = compare(
            {START: (1, 2), START + 3600: first_pair, START + 7200: (1, None), START + 10800: first_pair},
            {START + 300: first_pair, START + 600: (1, 2), START + 3600: first_pair,
             START + 7200: (1, 2), START + 14400: first_pair},
        )
        self.assertEqual({"different_opening_pair": 1, "matching_bid_and_ask": 1,
                          "missing_m5_hour": 1, "missing_open_side": 1}, report["comparison_counts"])
        self.assertEqual({"0": 2, "300": 1}, report["first_m5_label_lag_seconds"])
        self.assertEqual(1, report["m5_hours_without_h1"])

    def test_parser_accepts_documented_rows_and_columns(self):
        rows = [row(START), row(START + 3600)]
        columns = {key: [item[key] for item in rows] for key in COLUMNS}
        self.assertEqual(parse(zipped(rows), 3600), parse(zipped(columns), 3600))

    def test_parser_rejects_duplicate_misaligned_and_out_of_scope_timestamps(self):
        for rows in ([row(START), row(START)], [row(START + 300)], [row(END)]):
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, "aligned 2024"):
                parse(zipped(rows), 3600)

    def test_matching_but_crossed_quotes_stay_out_of_the_match_total(self):
        result = compare({START: (2, 1)}, {START: (2, 1)})
        self.assertEqual({"crossed_opening_pair": 1}, result["comparison_counts"])

    def test_development_parse_checks_exact_year_and_download_excludes_reserved_year(self):
        start, end = year_bounds(2022)
        self.assertEqual([start], list(parse(zipped([row(start)]), 3600, year=2022)))
        with self.assertRaisesRegex(ValueError, "aligned 2022"):
            parse(zipped([row(end)]), 3600, year=2022)
        with self.assertRaisesRegex(ValueError, "outside the reviewed scope"):
            download("H1", 1, year=2025)
