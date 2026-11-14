from datetime import datetime, timedelta
import unittest

from forex_demo_lab.corrected_clock import Replay, candidate_utc, corrected_events


def row(seq, label, bid=1.1):
    return {'sequence': seq, 'source_label': datetime.fromisoformat(label), 'bid': bid, 'ask': bid + .0001, 'volume': 0.0}


class CorrectionTests(unittest.TestCase):
    def replay_rows(self):
        return [row(0, '2023-10-29T19:00:00', 1.1), row(1, '2023-10-29T19:00:00', 1.11),
                row(2, '2023-10-29T19:59:59', 1.12), row(3, '2023-10-29T19:00:00', 1.1),
                row(4, '2023-10-29T19:00:00', 1.11), row(5, '2023-10-29T19:59:59', 1.12),
                row(6, '2023-10-29T20:00:00', 1.13)]

    def test_only_declared_second_copy_collapses_with_original_lineage(self):
        source = self.replay_rows()
        output = list(corrected_events(source, '202310', Replay(0, 3, 3)))
        self.assertEqual([r['source_sequence'] for r in output], [0, 1, 2, 6])
        self.assertEqual([r['sequence'] for r in output], [0, 1, 2, 3])
        self.assertEqual([r['bid'] for r in output], [1.1, 1.11, 1.12, 1.13])
        self.assertEqual(output[0]['candidate_time'], output[1]['candidate_time'])
        self.assertEqual(output[0]['candidate_time'].isoformat(), '2023-10-30T00:00:00+00:00')

    def test_no_blanket_duplicate_filter_and_no_implicit_replay_permission(self):
        source = [row(0, '2023-10-30T10:00:00'), row(1, '2023-10-30T10:00:00')]
        self.assertEqual(len(list(corrected_events(source, '202310'))), 2)
        with self.assertRaisesRegex(ValueError, 'Unlisted source reversal'):
            list(corrected_events(self.replay_rows(), '202310'))

    def test_any_changed_timestamp_bid_ask_or_volume_in_second_copy_rejected(self):
        for key, value in (('bid', 1.10001), ('ask', 1.2), ('volume', 1.0),
                           ('source_label', datetime.fromisoformat('2023-10-29T19:00:00.001'))):
            values = self.replay_rows()
            values[3][key] = value
            with self.assertRaises(ValueError):
                list(corrected_events(values, '202310', Replay(0, 3, 3)))

    def test_incomplete_replay_or_invalid_ranges_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            list(corrected_events(self.replay_rows()[:5], '202310', Replay(0, 3, 3)))
        with self.assertRaises(ValueError):
            Replay(0, 4, 3)

    def test_spring_gap_is_preserved_instead_of_compressed(self):
        values = [row(0, '2023-03-26T18:59:56.352'), row(1, '2023-03-26T20:00:00.010')]
        a, b = list(corrected_events(values, '202303'))
        self.assertAlmostEqual((b['candidate_time']-a['candidate_time']).total_seconds(), 3603.658)

    def test_european_calendar_changes_before_market_reopens(self):
        self.assertEqual(candidate_utc(datetime.fromisoformat('2023-03-26T17:00:00')).hour, 21)
        self.assertEqual(candidate_utc(datetime.fromisoformat('2023-10-29T17:00:00')).hour, 22)
        self.assertEqual(candidate_utc(datetime.fromisoformat('2023-11-03T07:30:00')).hour, 12)

    def test_nonexistent_or_ambiguous_calendar_wall_time_rejected(self):
        for label in ('2023-03-25T20:30:00', '2023-10-28T20:30:00'):
            with self.assertRaisesRegex(ValueError, 'Ambiguous or nonexistent'):
                candidate_utc(datetime.fromisoformat(label))

    def test_wrong_sequence_month_quote_and_future_year_rejected(self):
        for source in ([row(1, '2023-10-30T10:00:00')], [row(0, '2023-11-01T00:00:00')],
                       [row(0, '2023-10-30T10:00:00', float('inf'))]):
            with self.assertRaises(ValueError):
                list(corrected_events(source, '202310'))
        with self.assertRaises(ValueError):
            candidate_utc(datetime.fromisoformat('2026-11-01T00:00:00'))


if __name__ == '__main__':
    unittest.main()
