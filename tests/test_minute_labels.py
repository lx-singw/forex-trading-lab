import unittest
from forex_demo_lab.minute_labels import MINUTE,aggregate,compare


def tick(row,stamp,bid='1.1',ask='1.2'):
    return {'source_row':row,'time_msc':stamp,'bid':bid,'ask':ask}


class MinuteLabelTests(unittest.TestCase):
    def test_exact_boundaries_same_ms_and_bid_ask_preserved(self):
        bars=aggregate([tick(0,59999),tick(1,60000),tick(2,60000,'1.15','1.25')])
        self.assertEqual(bars[0]['quotes'],1)
        self.assertEqual(bars[60000]['quotes'],2)
        self.assertEqual(bars[60000]['bid_close'],'1.15')
        self.assertEqual(bars[60000]['ask_high'],'1.25')
        self.assertEqual(bars[60000]['last_source_row'],2)

    def test_gap_never_filled_or_carried(self):
        bars=aggregate([tick(0,0),tick(5,180000)])
        self.assertEqual(set(bars),{0,180000})
        result=compare([60000],{60000:dict(open='1.1',high='1.2',low='1',close='1.1')},bars)
        self.assertEqual(result['common_triplets'],0)
        self.assertIsNone(result['labels'][0]['interpretations']['literal_start']['tick_minute'])
        self.assertFalse(result['relative_end_label_screen_pass'])

    def test_reversals_rows_and_invalid_quotes_rejected(self):
        cases=[[tick(0,60000),tick(1,0)],[tick(0,0),tick(0,0)],
               [tick(1,0),tick(0,0)],[tick(0,0,'NaN')],[tick(0,0,'1.3','1.2')],
               [tick(0,0,'0')],[tick(0,0,'1','Infinity')]]
        for ticks in cases:
            with self.subTest(ticks=ticks),self.assertRaises(ValueError):aggregate(ticks)

    def fixture(self,count=250):
        bars=aggregate([tick(i,i*MINUTE,str(1+i*.001),str(1.1+i*.001)) for i in range(count+2)])
        labels=[i*MINUTE for i in range(1,count+1)]
        reference={stamp:{key:bars[stamp-MINUTE]['bid_'+key] for key in ('open','high','low','close')}
                   for stamp in labels}
        return labels,reference,bars

    def test_end_hypothesis_exact_intervals_and_declared_screen(self):
        labels,reference,bars=self.fixture()
        result=compare(labels,reference,bars)
        self.assertTrue(result['relative_end_label_screen_pass'])
        self.assertEqual(result['common_triplets'],250)
        self.assertEqual(result['common_close_median_pips']['end_label'],0)
        self.assertEqual(result['labels'][0]['interpretations']['end_label']['interval_end_exclusive_ms'],60000)

    def test_common_labels_used_for_all_hypotheses_and_missing_visible(self):
        labels,reference,bars=self.fixture();del bars[100*MINUTE]
        result=compare(labels,reference,bars)
        self.assertEqual(result['common_triplets'],247)
        self.assertEqual(result['paired_labels_by_hypothesis']['end_label'],249)
        self.assertEqual(len(result['labels']),250)

    def test_insufficient_evidence_and_flat_clock_ambiguity_fail(self):
        labels,reference,bars=self.fixture(239)
        self.assertFalse(compare(labels,reference,bars)['relative_end_label_screen_pass'])
        labels,reference,bars=self.fixture()
        for ref in reference.values():ref.update({key:'1.1' for key in ref})
        for bar in bars.values():bar.update({key:'1.1' for key in bar if key.startswith('bid_')})
        self.assertFalse(compare(labels,reference,bars)['relative_end_label_screen_pass'])

    def test_bad_reference_and_label_grid_rejected(self):
        labels,reference,bars=self.fixture()
        for grid in ([0,0],[MINUTE,0],[1]):
            with self.assertRaises(ValueError):compare(grid,reference,bars)
        reference[labels[0]]['low']='99'
        with self.assertRaises(ValueError):compare(labels,reference,bars)


if __name__=='__main__':unittest.main()
