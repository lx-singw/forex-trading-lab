from datetime import datetime
import unittest

from forex_demo_lab.reference import HEADER, HOUR, compare_day, hourly, ms, parse, screen, utc_label
from datetime import timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile


def source(*rows):
    return [','.join(HEADER), *rows]


def row(time='120000', prices='1.1,1.2,1.0,1.15', day='20230714'):
    return f'EURUSD,{day},{time},{prices}'


class ReferenceTests(unittest.TestCase):
    def test_winter_summer_and_november_are_format_specific(self):
        for label, offset in [('2022-01-07T12:00', 1), ('2022-07-08T12:00', 2),
                              ('2022-11-04T12:00', 1)]:
            local = datetime.fromisoformat(label)
            self.assertEqual(utc_label(local).hour, 12-offset)

    def test_transition_ambiguity_and_nonexistent_labels_rejected(self):
        for label in ('2023-03-26T02:30', '2023-10-29T02:30'):
            with self.assertRaises(ValueError): utc_label(datetime.fromisoformat(label))

    def test_source_lineage_and_other_symbols(self):
        rows = parse(source('OTHER,not-a-date,not-a-time,x,x,x,x', row()), '2023-07-14')
        self.assertEqual(rows[0]['source_row'], 3)
        self.assertEqual(rows[0]['source_time'], '120000')
        self.assertEqual(rows[0]['close'], '1.15')

    def test_midnight24_is_literal_next_day_not_shifted_bar(self):
        rows = parse(source(row('235900'), row('240000')), '2023-07-14')
        self.assertEqual(rows[1]['reference_time_msc']-rows[0]['reference_time_msc'], 60000)
        self.assertEqual(rows[1]['source_date'], '20230714')

    def test_schema_dates_order_duplicates_and_prices_rejected(self):
        cases = [['bad-header'], source(row(day='20230715')),
                 source(row(),row()), source(row('120100'),row()),
                 source(row(prices='NaN,1.2,1.0,1.1')), source(row(prices='1.3,1.2,1,1.1')),
                 source(row('120001')), source(row('250000')),
                 source('EURUSD,20230714,120000,1,1,1')]
        for lines in cases:
            with self.subTest(lines=lines), self.assertRaises(ValueError): parse(lines,'2023-07-14')

    def test_hourly_aggregate_keeps_missing_minutes_without_filling(self):
        bars = hourly(parse(source(row('120000'),row('120200','1.15,1.3,1.1,1.2')), '2023-07-14'))
        bar = next(iter(bars.values()))
        self.assertEqual(bar['minutes'],2)
        self.assertEqual((bar['open'],bar['high'],bar['low'],bar['close']),('1.1','1.3','1.0','1.2'))
        rows = parse(source(row()),'2023-07-14')
        with self.assertRaises(ValueError): hourly(rows+rows)

    def fixture(self):
        start=ms(datetime(2023,7,14,tzinfo=timezone.utc))
        ref={}; candidate={}
        for hour in range(24):
            stamp=start+hour*HOUR; price=1+hour*.001
            ref[stamp]={'open':str(price),'high':str(price),'low':str(price),'close':str(price)}
            candidate[stamp]={f'bid_{k}':price for k in ('open','high','low','close')}
        return ref,candidate

    def test_screen_uses_both_controls_and_all_pairs(self):
        ref,candidate=self.fixture()
        self.assertTrue(screen('2023-07-14',ref,candidate)['fixed_screen_pass'])
        del candidate[min(candidate)+5*HOUR]
        result=screen('2023-07-14',ref,candidate)
        self.assertEqual(result['aligned_pairs_within_2_pips'],12)
        self.assertFalse(result['fixed_screen_pass'])
        self.assertIsNone(result['median_close_distance_pips']['minus_one_hour'])

    def test_flat_price_ambiguous_clock_fails(self):
        ref,candidate=self.fixture()
        for v in ref.values(): v.update({k:'1.0' for k in ('open','high','low','close')})
        for v in candidate.values(): v.update({k:1.0 for k in v})
        self.assertFalse(screen('2023-07-14',ref,candidate)['fixed_screen_pass'])

    def test_all_24_hours_include_absence_and_distance(self):
        ref,candidate=self.fixture(); del ref[max(ref)]
        results=compare_day('2023-07-14',ref,candidate)
        self.assertEqual(len(results),24)
        self.assertIsNone(results[-1]['reference'])
        self.assertIsNone(results[-1]['absolute_ohlc_distance_pips'])
        self.assertEqual(results[0]['absolute_ohlc_distance_pips']['close'],0)

    def test_frozen_input_source_and_ledger_tampering_rejected(self):
        path=Path(__file__).resolve().parents[1]/'scripts/reference-016.py'
        spec=importlib.util.spec_from_file_location('ref016',path)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        original=Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            os.chdir(temp)
            try:
                Path('reports').mkdir(); source=Path('reports/reference-016-source.zip')
                source.write_bytes(b'fixture-source'); data=Path('fixture-input');data.write_bytes(b'fixture')
                digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
                ledger={'archive_sha256':digest(source),'file_bindings':{str(data):digest(data)}}
                cli.LEDGER.write_text(json.dumps(ledger))
                seal=Path('reports/reference-016-seal.json')
                seal.write_text(json.dumps({'ledger_sha256':digest(cli.LEDGER)}))
                cli.verify()
                for target in (data,source,cli.LEDGER):
                    before=target.read_bytes();target.write_bytes(before+b'changed')
                    with self.assertRaises((ValueError,json.JSONDecodeError)):cli.verify()
                    target.write_bytes(before)
                cli.verify()
            finally:os.chdir(original)

    def test_independent_checker_calendar_uses_same_instants_separately(self):
        path=Path(__file__).resolve().parents[1]/'scripts/check-reference-016.py'
        spec=importlib.util.spec_from_file_location('independent016',path)
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        for label in ('2022-01-07T12:00','2022-07-08T12:00','2023-03-26T01:00',
                      '2023-03-26T03:00','2023-11-03T12:00'):
            local=datetime.fromisoformat(label)
            self.assertEqual(checker.manual_utc(local),ms(utc_label(local)))
        for label in ('2023-03-26T02:00','2023-10-29T02:00'):
            with self.assertRaises(ValueError):checker.manual_utc(datetime.fromisoformat(label))


if __name__=='__main__': unittest.main()
