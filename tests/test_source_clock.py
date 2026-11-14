from datetime import datetime, timedelta
import unittest

from forex_demo_lab.source_clock import Boundary, SequenceClock, activity_passes


def event(seq, stamp, bid=1.1):
    return {'sequence': seq, 'source_label': datetime.fromisoformat(stamp), 'bid': bid, 'ask': bid + .0001}


class SourceClockTests(unittest.TestCase):
    def setUp(self):
        self.fall = Boundary('202310', datetime.fromisoformat('2023-10-29T19:59:55.716'),
                             datetime.fromisoformat('2023-10-29T19:00:00.094'), 4, 5)

    def test_repeated_hour_preserves_two_distinct_episodes_and_same_ms_order(self):
        clock = SequenceClock(self.fall)
        values = [event(0, '2023-10-29T19:00:00.094', 1.1),
                  event(1, '2023-10-29T19:59:55.716', 1.11),
                  event(2, '2023-10-29T19:00:00.094', 1.12),
                  event(3, '2023-10-29T19:00:00.094', 1.13)]
        output = [clock.map(v) for v in values]
        clock.finish()
        self.assertEqual(output[0]['candidate_time'].hour, 23)
        self.assertEqual(output[2]['candidate_time'].hour, 0)
        self.assertEqual([o['bid'] for o in output], [v['bid'] for v in values])
        self.assertEqual(output[2]['candidate_time'], output[3]['candidate_time'])
        self.assertEqual(clock.transition_sequence, 2)

    def test_spring_jump_is_adjacent_after_candidate_conversion(self):
        boundary = Boundary('202303', datetime.fromisoformat('2023-03-26T18:59:56.352'),
                            datetime.fromisoformat('2023-03-26T20:00:00.010'), 5, 4)
        clock = SequenceClock(boundary)
        a = clock.map(event(0, boundary.before_last.isoformat()))
        b = clock.map(event(1, boundary.after_first.isoformat()))
        clock.finish()
        self.assertAlmostEqual((b['candidate_time'] - a['candidate_time']).total_seconds(), 3.658)

    def test_other_backward_timestamp_and_wrong_boundary_do_not_advance_state(self):
        clock = SequenceClock(self.fall)
        clock.map(event(0, self.fall.before_last.isoformat()))
        before = clock.checkpoint()
        with self.assertRaisesRegex(ValueError, 'Unlisted backward'):
            clock.map(event(1, '2023-10-29T19:00:00.095'))
        self.assertEqual(before, clock.checkpoint())
        clock.map(event(1, self.fall.after_first.isoformat()))

    def test_restart_on_either_side_and_with_same_ms_matches_uninterrupted(self):
        values = [event(0, self.fall.before_last.isoformat()), event(1, self.fall.after_first.isoformat()),
                  event(2, self.fall.after_first.isoformat(), 1.2), event(3, '2023-10-29T19:01:00')]
        complete = SequenceClock(self.fall)
        expected = [complete.map(v) for v in values]
        for stop in (0, 1, 2, 3):
            clock = SequenceClock(self.fall)
            actual = [clock.map(v) for v in values[:stop]]
            clock = SequenceClock.restore(self.fall, clock.checkpoint())
            actual.extend(clock.map(v) for v in values[stop:])
            clock.finish()
            self.assertEqual(expected, actual)

    def test_missing_transition_cannot_be_finished(self):
        clock = SequenceClock(self.fall)
        clock.map(event(0, '2023-10-30T10:00:00'))
        with self.assertRaisesRegex(ValueError, 'not observed'):
            clock.finish()

    def test_wrong_sequence_month_invalid_quote_and_aware_source_rejected(self):
        for value in (event(1, self.fall.before_last.isoformat()), event(0, '2023-11-01T00:00:00'),
                      event(0, self.fall.before_last.isoformat(), float('nan')),
                      event(0, self.fall.before_last.isoformat() + '+00:00')):
            with self.assertRaises(ValueError):
                SequenceClock(self.fall).map(value)
        value = event(0, self.fall.before_last.isoformat())
        value['ask'] = value['bid'] - .0001
        with self.assertRaises(ValueError):
            SequenceClock(self.fall).map(value)

    def test_tampered_checkpoint_and_different_mapping_rejected(self):
        clock = SequenceClock(self.fall)
        clock.map(event(0, self.fall.before_last.isoformat()))
        base = clock.checkpoint()
        for change in ({'previous_source': None}, {'sequence': 0}, {'changed': True},
                       {'previous_candidate': '2023-10-29T00:00:00+00:00'}, {'transition_sequence': 1}):
            with self.assertRaises(ValueError):
                SequenceClock.restore(self.fall, {**base, **change})

    def test_source_boundary_itself_must_be_explicit_and_scoped(self):
        with self.assertRaises(ValueError):
            Boundary('202311', self.fall.before_last, self.fall.after_first, 4, 5)
        with self.assertRaises(ValueError):
            Boundary('202310', self.fall.before_last, self.fall.after_first, 4, 4)

    def test_activity_requires_both_positive_controls_and_all_thresholds(self):
        control = {'ticks': 10, 'range_pips': 1}
        e = {'ticks': 20, 'range_pips': 3}
        self.assertTrue(activity_passes(e, [control, control]))
        for controls in ([control], [control, None], [control, {'ticks': 0, 'range_pips': 1}],
                         [control, {'ticks': 10, 'range_pips': 0}]):
            self.assertFalse(activity_passes(e, controls))
        self.assertFalse(activity_passes({'ticks': 19, 'range_pips': 4}, [control, control]))
        self.assertFalse(activity_passes({'ticks': 30, 'range_pips': 2.9}, [control, control]))


if __name__ == '__main__':
    unittest.main()
