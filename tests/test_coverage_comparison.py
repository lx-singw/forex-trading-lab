import unittest

from forex_demo_lab.coverage_comparison import HOUR, aggregate, distances, questions


class CoverageComparisonTests(unittest.TestCase):
    def event(self, stamp, record=2, bid='1.1', ask='1.2'):
        return dict(event_ms=stamp, record=record, kind='ticks', path='original.zip',
                    member='ticks.csv', raw_label=str(stamp), bid=bid, ask=ask)

    def test_half_open_window_and_minute_endpoint(self):
        result = aggregate([self.event(-1), self.event(0,3), self.event(59999,4),
                            self.event(60000,5), self.event(HOUR,6)], 0, HOUR, minute_bins=True)
        self.assertEqual(result['selected_records'], 3)
        self.assertEqual([bar['records'] for bar in result['minutes'][:3]], [2,1,0])
        self.assertEqual(result['hours'][0]['first_original']['record'], 3)

    def test_tied_quotes_preserve_distinct_rows_and_close_order(self):
        result = aggregate([self.event(0), self.event(0,3,bid='1.15'), self.event(0,4)], 0, HOUR)
        self.assertEqual(result['tied_transitions'], 2)
        self.assertEqual(result['hours'][0]['bid_high'], '1.15')
        self.assertEqual(result['hours'][0]['bid_close'], '1.1')
        self.assertEqual(result['selected_records'], 3)

    def test_backward_time_or_original_record_is_rejected(self):
        for events in ([self.event(2), self.event(1,3)], [self.event(0), self.event(1)]):
            with self.assertRaises(ValueError):
                aggregate(events,0,HOUR)

    def test_unavailable_and_empty_captures_remain_distinct(self):
        result = aggregate([],0,3*HOUR,captured=(HOUR,2*HOUR))
        self.assertEqual([h['status'] for h in result['hours']], ['unavailable','empty','unavailable'])
        self.assertEqual([h['records'] for h in result['hours']], [None,0,None])
        with self.assertRaises(ValueError):
            aggregate([self.event(0)],0,3*HOUR,captured=(HOUR,2*HOUR))

    def test_tail_cutoff_and_upper_bound_are_strict(self):
        result = aggregate([self.event(10), self.event(11,3), self.event(HOUR,4)],
                           0,2*HOUR,tail_cutoff=10)
        self.assertEqual(result['tail_records'],1)

    def test_full_precision_prices_and_missing_counterparts(self):
        a=aggregate([self.event(0,bid='1.0000000000000001',ask='1.01')],0,HOUR)
        b=aggregate([self.event(0,bid='1.0',ask='1.01')],0,HOUR)
        delta=distances({'a':a,'b':b})[0]['absolute_ohlc_distance_pips']
        self.assertEqual(delta['close'],'1E-12')
        missing=aggregate([],0,HOUR)
        self.assertIsNone(distances({'a':a,'missing':missing})[0]['absolute_ohlc_distance_pips'])
        for bid,ask in [('NaN','1.1'),('1.1','Infinity'),('1.2','1.1')]:
            with self.assertRaises(ValueError):
                aggregate([self.event(0,bid=bid,ask=ask)],0,HOUR)

    def test_reference_prices_stay_separate_and_duplicate_labels_fail(self):
        event=dict(event_ms=0,record=2,kind='reference',path='reference.zip',member='bars.txt',
                   raw_label='original',open='1.1',high='1.2',low='1.0',close='1.15')
        result=aggregate([event],0,HOUR,kind='reference')
        self.assertIsNone(result['hours'][0]['ask_close'])
        self.assertIsNone(result['hours'][0]['bid_close'])
        self.assertEqual(result['hours'][0]['reference_close'],'1.15')
        with self.assertRaises(ValueError):
            aggregate([event,{**event,'record':3}],0,HOUR,kind='reference')

    def test_presence_questions_allow_negative_or_unavailable_evidence(self):
        absent=aggregate([],0,HOUR,tail_cutoff=10)
        unknown=aggregate([],0,HOUR,captured=(HOUR,2*HOUR))
        evidence=questions(unknown,absent,0,0)
        self.assertIsNone(evidence['march_utc23']['answer'])
        self.assertFalse(evidence['july_tail']['answer'])
        self.assertFalse(evidence['july_utc20']['answer'])


if __name__ == '__main__':
    unittest.main()
