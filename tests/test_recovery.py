import csv
from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.collection import RAW_FIELDS
from forex_demo_lab.recovery import audit_chunk, bound, chunks, combine, references, sample_passed
from forex_demo_lab.tick_audit import capture_ticks
from test_ingestion import START
from test_tick_audit import TickTerminal, tick


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.api = TickTerminal()

    def collect(self, hours=1):
        folder = self.root / 'capture'
        end = START + timedelta(hours=hours)
        capture_ticks(self.api, START, end, folder)
        return folder, START.isoformat(), end.isoformat()

    def test_sample_requires_every_hour_and_all_four_prices(self):
        folder, start, end = self.collect(2)
        ref = {bound(start): {'open': 1.1, 'high': 1.1, 'low': 1.1, 'close': 1.1}}
        report = audit_chunk(folder, start, end, ref)
        self.assertFalse(sample_passed(report, 2))
        self.assertEqual(report['hours'][1]['status'], 'empty_unclassified')
        ref[bound(start)]['high'] = 1.1001
        report = audit_chunk(folder, start, end, ref)
        self.assertEqual(report['hours'][0]['status'], 'mismatch')
        self.assertFalse(sample_passed(report, 1))

    def test_original_equal_ms_order_and_both_quote_sides(self):
        self.api.events = [tick(30, bid=1.1, ask=1.1002), tick(30, bid=1.099, ask=1.1005),
                           tick(3599999, bid=1.101, ask=1.1011)]
        folder, start, end = self.collect()
        ref = {bound(start): {'open': 1.1, 'high': 1.101, 'low': 1.099, 'close': 1.101}}
        report = audit_chunk(folder, start, end, ref)
        self.assertTrue(sample_passed(report, 1))
        self.assertEqual(report['same_millisecond_events'], 1)
        self.assertEqual(report['hours'][0]['ask_high'], 1.1011)
        self.assertEqual(report['hours'][0]['bid_open'], 1.1)
        self.assertFalse(combine([report])['performance_evaluation_ready'])

    def test_reference_only_hour_not_filled_and_tick_only_hour_recorded(self):
        folder, start, end = self.collect(2)
        ref = {bound(start) + 3600000: {'open': 1.1, 'high': 1.1, 'low': 1.1, 'close': 1.1}}
        report = audit_chunk(folder, start, end, ref)
        self.assertEqual([h['status'] for h in report['hours']],
                         ['ticks_without_reference', 'reference_without_ticks'])
        self.assertNotIn('bid_close', report['hours'][1])

    def test_wrong_resume_bounds_and_invalid_quote_rejected(self):
        folder, start, end = self.collect()
        with self.assertRaisesRegex(ValueError, 'declared window'):
            audit_chunk(folder, start, (START + timedelta(hours=2)).isoformat(), {})
        metadata = folder / 'capture.json'
        value = json.loads(metadata.read_text())
        value['account_type'] = 'real'
        metadata.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'demo mode'):
            audit_chunk(folder, start, end, {})

    def test_invalid_quotes_cannot_be_discarded(self):
        self.api.events = [tick(bid=1.2, ask=1.1)]
        folder, start, end = self.collect()
        with self.assertRaisesRegex(ValueError, 'Invalid quotes'):
            audit_chunk(folder, start, end, {})

    def test_empty_chunk_does_not_hide_gap_across_chunks(self):
        base = bound(START.isoformat())
        reports = []
        for i, count in enumerate((1, 0, 1)):
            start = START + timedelta(hours=i)
            ms = base + i * 3600000 + 100
            reports.append({'source_label_start': start.isoformat(),
                'source_label_end_exclusive': (start + timedelta(hours=1)).isoformat(),
                'first_ms': ms if count else None, 'last_ms': ms if count else None,
                'ticks': count, 'hours': [{'source_hour_label': start.isoformat(), 'ticks': count,
                                        'status': 'ticks_without_reference' if count else 'empty_unclassified'}],
                'gaps_over_one_hour': [], 'same_millisecond_events': 0})
        result = combine(reports)
        self.assertEqual(result['gaps_over_one_hour'][0]['seconds'], 7200)
        self.assertEqual(result['ticks'], 2)
        reports[1]['source_label_start'] = reports[0]['source_label_start']
        with self.assertRaisesRegex(ValueError, 'overlap or leave a hole'):
            combine(reports)

    def test_dropped_hour_rejected_not_treated_as_closed_market(self):
        folder, start, end = self.collect(2)
        report = audit_chunk(folder, start, end, {})
        report['hours'].pop()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            combine([report])

    def test_reference_invalid_or_duplicate_prices_rejected(self):
        path = self.root / 'reference.csv'
        row = [START.isoformat(), 1.1, 1.11, 1.09, 1.1, 1, 1, 0]
        for rows in ([row, row], [[START.isoformat(), 1.1, 1.09, 1.08, 1.1, 1, 1, 0]]):
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(RAW_FIELDS)
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, 'reference candle'):
                references(path)

    def test_chunks_preserve_exclusive_upper_boundary_and_reject_naive_labels(self):
        windows = chunks(START.isoformat(), (START + timedelta(hours=49)).isoformat())
        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0][1], windows[1][0])
        self.assertEqual(windows[-1][1], (START + timedelta(hours=49)).isoformat())
        with self.assertRaises(ValueError):
            chunks(START.replace(tzinfo=None).isoformat(), windows[-1][1])


if __name__ == '__main__':
    unittest.main()
