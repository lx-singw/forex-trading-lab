from datetime import datetime,timezone
import unittest

from forex_demo_lab.reference import HEADER,parse as original_parse,ms
from forex_demo_lab.reference_boundary import parse


def source(*rows): return [','.join(HEADER),*rows]
def row(date,time): return f'EURUSD,{date},{time},1.1,1.2,1.0,1.15'


class BoundaryTests(unittest.TestCase):
    def test_next_midnight_preserves_original_labels_and_rows(self):
        lines=source(row('20230326','235900'),row('20230327','000000'))
        with self.assertRaises(ValueError):original_parse(lines,'2023-03-26')
        rows=parse(lines,'2023-03-26')
        self.assertEqual(rows[-1]['source_date'],'20230327')
        self.assertEqual(rows[-1]['source_time'],'000000')
        self.assertEqual(rows[-1]['source_row'],3)
        self.assertEqual(rows[-1]['reference_time_msc'],ms(datetime(2023,3,26,22,tzinfo=timezone.utc)))
        self.assertEqual(rows[-1]['reference_time_msc']-rows[0]['reference_time_msc'],60000)

    def test_other_dates_and_later_next_day_minutes_rejected(self):
        for date,time in [('20230325','000000'),('20230328','000000'),('20230327','000100')]:
            with self.subTest(date=date,time=time),self.assertRaises(ValueError):
                parse(source(row(date,time)),'2023-03-26')

    def test_duplicate_midnight_and_reversed_date_boundary_rejected(self):
        midnight=row('20230327','000000')
        for lines in (source(midnight,midnight),source(row('20230326','240000'),midnight),
                      source(midnight,row('20230326','235900'))):
            with self.assertRaises(ValueError):parse(lines,'2023-03-26')

    def test_ordinary_rows_are_unchanged(self):
        lines=source(row('20230714','120000'))
        self.assertEqual(parse(lines,'2023-07-14'),original_parse(lines,'2023-07-14'))


if __name__=='__main__':unittest.main()
