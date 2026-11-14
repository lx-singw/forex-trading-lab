from datetime import timedelta
from pathlib import Path
import runpy
import tempfile
import unittest

from forex_demo_lab.recovery import audit_chunk
from forex_demo_lab.tick_audit import capture_ticks, sha256
from test_ingestion import START
from test_tick_audit import TickTerminal, tick

CHECK = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/check-recovery-010.py'))


class RecoverySQLTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / 'capture'
        self.api = TickTerminal()
        self.api.events = [tick(30, bid=1.1, ask=1.1002), tick(30, bid=1.099, ask=1.1005),
                           tick(3599999, bid=1.101, ask=1.1011)]
        end = START + timedelta(hours=2)
        capture_ticks(self.api, START, end, self.folder)
        self.report = audit_chunk(self.folder, START.isoformat(), end.isoformat(), {})
        self.report['capture_sha256'] = sha256(self.folder / 'capture.json')

    def test_independent_sql_preserves_same_ms_quote_order_and_empty_hour(self):
        result = CHECK['check_chunk'](self.folder, self.report)
        self.assertEqual(result['ticks'], 3)
        self.assertEqual(result['observed_hours'], 1)

    def test_wrong_close_is_rejected_even_with_unchanged_counts(self):
        self.report['hours'][0]['bid_close'] = 1.1001
        with self.assertRaisesRegex(ValueError, 'quote aggregation differs'):
            CHECK['check_chunk'](self.folder, self.report)

    def test_fabricated_empty_hour_and_changed_input_are_rejected(self):
        self.report['hours'][1]['ticks'] = 1
        with self.assertRaisesRegex(ValueError, 'coverage/count differs'):
            CHECK['check_chunk'](self.folder, self.report)
        with (self.folder / 'ticks.csv.gz').open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            CHECK['check_chunk'](self.folder, self.report)


if __name__ == '__main__':
    unittest.main()
