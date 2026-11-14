"""Invented fixtures only: transport causality and unchanged offline risk engine."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from forex_demo_lab import paired_replay_133 as replay
from forex_demo_lab.execution_audit_runtime_b import InjectedTick019B
from forex_demo_lab.model import Bar, Config
from test_paired_capture_132 import SECOND, bits, change, encode, fixture

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = int(datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc).timestamp()) * 1000


def sparse(offsets, prices=None, kind='invented_fixture'):
    prices = prices or [1.1] * len(offsets)
    rows = [f'H\tFXDL_PAIRED132_V1\t{kind}\t2026.10.19\t{SECOND}\t1000']
    sequence = 0
    for offset, bid in zip(offsets, prices, strict=True):
        for part, (tag, key) in enumerate((('C', 'before'), ('T', 'quote'), ('C', 'after'))):
            sequence += 1
            micros = 1000 + offset + part * 100
            second = SECOND + (micros - 1000) // 1_000_000
            values = [second + 10800, second + 10800, second, second + 7200, -7200, 0]
            if tag == 'T':
                source = second + 10800
                values = [source, source * 1000 + 123, bits(bid), bits(bid + .0001), bits(0), 0, 1026, bits(0)]
            rows += [f'A\t{sequence}\t{tag}\t{key}', '\t'.join(map(str,
                     [tag, sequence, key, second, second, second, micros, micros + 10, micros + 20, 1, 0, *values]))]
    return encode(rows + [f'S\t18\t{sequence}'])


def drain(cursor):
    packets = []
    while (packet := cursor.peek()) is not None:
        packets.append(packet)
        cursor.ack(packet)
    return packets


def invented_tick(packet):
    # Explicit test-only embedding. Never applies to market_declared files.
    if packet['declared_kind'] != 'invented_fixture':
        raise ValueError('invented_only')
    return dict(sequence=packet['poll'] - 1,
                time_msc=ANCHOR + (packet['replay_offset_us'] + 999) // 1000,
                bid=float(packet['quote']['bid_decimal']), ask=float(packet['quote']['ask_decimal']))


def engine(side):
    result = InjectedTick019B(Config())
    result.audit_decisions = {str((ANCHOR // 3_600_000 + 1) * 3_600_000): [side, .001]}
    return result


def manifest_for(raw, root, run_id='run001'):
    path = f'data/paired-recorder-132-native/Run132-{SECOND}-1-1000/Paired132.txt'
    target = Path(root) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return dict(schema=replay.SCHEMA + '_manifest', runs=[dict(id=run_id, path=path, sha256=replay.digest(raw))])


class PairedReplay133Tests(unittest.TestCase):
    def test_repeated_observations_keep_all_bits_and_distinct_causal_ids(self):
        rows = fixture(repeated=True)
        change(rows, 10, 15, bits(-0.0)); change(rows, 10, 17, 2**32 - 1)
        cursor = replay.Replay(encode(rows)); packets = drain(cursor)
        self.assertEqual(len({p['event_id'] for p in packets}), 3)
        self.assertEqual(packets[1]['quote']['native_bits']['last'], bits(-0.0))
        self.assertEqual(packets[1]['quote']['raw_flags'], 2**32 - 1)
        self.assertEqual(cursor.report()['same_time_changed'], 2)
        cursor = replay.Replay(encode(fixture(repeated=True))); drain(cursor)
        self.assertEqual(cursor.report()['adjacent_repeated_snapshots'], 2)

    def test_no_future_packet_or_footer_leaks_into_earlier_ids(self):
        rows = fixture(); original = drain(replay.Replay(encode(rows)))
        change(rows, 16, 13, bits(1.0999)); rows[-1] = 'S\t13\t9'
        changed = drain(replay.Replay(encode(rows)))
        self.assertEqual(original[:2], changed[:2])
        self.assertNotEqual(original[2]['event_id'], changed[2]['event_id'])
        prefix = drain(replay.Replay(encode(fixture()[:13])))
        self.assertEqual(prefix, original[:2])

    def test_clock_marker_is_after_group_and_gaps_are_never_resampled(self):
        packets = drain(replay.Replay(sparse([0, 2_000_000, 4_000_001])))
        self.assertEqual([p['replay_offset_us'] for p in packets], [220, 2_000_220, 4_000_221])
        self.assertEqual([p['quote_receipt_gap_us'] for p in packets], [None, 2_000_000, 2_000_001])
        self.assertEqual([p['sampling_gap'] for p in packets], [False, False, True])
        for packet in packets:
            self.assertEqual(packet['replay_offset_us'] + 1000, packet['after']['receipt_monotonic_us'][2])
            self.assertGreater(packet['replay_offset_us'] + 1000, packet['quote']['receipt_monotonic_us'][2])
            self.assertIsNone(packet['source_age']); self.assertNotIn('time_msc', packet)

    def test_source_reversals_keep_sequence_and_recovery_below_highwater(self):
        rows = fixture(polls=4)
        for index, offset in ((10, -1), (16, -2), (22, 0)):
            change(rows, index, 11, SECOND + 10800 + offset)
            change(rows, index, 12, (SECOND + 10800 + offset) * 1000 + 123)
        packets = drain(replay.Replay(encode(rows)))
        self.assertEqual([p['poll'] for p in packets], [1, 2, 3, 4])
        self.assertEqual([p['source_reversal'] for p in packets], [False, True, True, False])
        self.assertEqual([p['source_below_highwater'] for p in packets], [False, True, True, False])

    def test_every_wire_prefix_quarantines_incomplete_poll_and_preserves_pending(self):
        rows = fixture()
        for end in range(1, len(rows)):
            raw = encode(rows[:end])
            cursor = replay.Replay(raw); packets = drain(cursor); report = cursor.report()
            outcomes = (end - 1) // 2
            self.assertEqual(len(packets), outcomes // 3)
            self.assertEqual(report['quarantined_rows'], outcomes % 3)
            self.assertEqual(report['quarantined_quotes'], int(outcomes % 3 == 2))
            self.assertEqual(report['pending_attempt'], (end - 1) % 2 == 1)
        raw = encode(rows[:-1]) + b'C\t10'
        cursor = replay.Replay(raw); drain(cursor)
        self.assertTrue(cursor.report()['truncated_tail'])

    def test_peek_is_copy_report_waits_and_ack_rejects_mutation_and_skips(self):
        raw = encode(fixture()); cursor = replay.Replay(raw)
        with self.assertRaisesRegex(ValueError, 'not_exhausted'): cursor.report()
        first = cursor.peek(); first['quote']['bid_decimal'] = '3'
        with self.assertRaises(ValueError): cursor.ack(first)
        other = replay.Replay(raw); other.ack(other.peek()); second = other.peek()
        with self.assertRaises(ValueError): cursor.ack(second)
        self.assertTrue(cursor.ack(cursor.peek()))
        before = cursor.checkpoint(); self.assertFalse(cursor.ack(drain(replay.Replay(raw))[0]))
        self.assertEqual(before, cursor.checkpoint())
        with self.assertRaises(ValueError): cursor.ack(None)
        drain(cursor)
        with self.assertRaises(ValueError): cursor.ack(drain(replay.Replay(raw))[0])

    def test_checkpoints_every_boundary_and_uncommitted_delivery(self):
        raw = encode(fixture(polls=6, repeated=True)); expected = replay.replay_bytes(raw)
        cursor = replay.Replay(raw)
        for index in range(7):
            pending = cursor.peek(); saved = cursor.checkpoint()
            restored = replay.Replay.restore(raw, saved)
            self.assertEqual(restored.peek(), pending)
            self.assertEqual(restored.checkpoint(), saved)
            drain(restored); self.assertEqual(restored.report(), expected)
            if pending is not None: cursor.ack(pending)

    def test_checkpoint_integrity_runtime_and_run_binding_are_strict(self):
        raw = encode(fixture()); cursor = replay.Replay(raw); cursor.ack(cursor.peek())
        saved = json.loads(cursor.checkpoint())
        mutations = [dict(saved, extra=1), dict(saved, checksum='0' * 64)]
        for field, value in [('next_index', True), ('next_index', -1), ('next_index', 4),
                             ('next_index', 2), ('last_event_id', '0' * 64),
                             ('committed_prefix_sha256', '0' * 64), ('runtime', {})]:
            changed = deepcopy(saved); changed['state'][field] = value
            changed['checksum'] = replay.digest(replay.canonical(changed['state']))
            mutations.append(changed)
        for value in mutations:
            with self.assertRaises(ValueError): replay.Replay.restore(raw, replay.canonical(value))
        for bad in (b'{"state":{},"state":{}}', b'{"x":NaN}', b'[]', b'\xff', b' ' * 16_385):
            with self.assertRaises(ValueError): replay.Replay.restore(raw, bad)
        with self.assertRaises(ValueError): replay.Replay.restore(encode(fixture(polls=4)), cursor.checkpoint())
        with self.assertRaises(ValueError): replay.Replay(raw.replace(b'1026', b'1027', 1))

    def test_maximum_fixture_and_bounded_gap_details(self):
        cursor = replay.Replay(encode(fixture(polls=3600))); drain(cursor)
        self.assertEqual(cursor.report()['packets_committed'], 3600)
        cursor = replay.Replay(sparse([i * 3_000_000 for i in range(132)])); drain(cursor)
        report = cursor.report()
        self.assertEqual(report['sampling_gap_count'], 131)
        self.assertEqual(len(report['sampling_gaps']), 128)
        self.assertTrue(report['sampling_gap_details_truncated'])

    def test_manifest_is_hash_bound_separate_and_cli_matches_library(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = encode(fixture()); manifest = manifest_for(raw, temp)
            bundle = replay.replay_manifest(temp, replay.canonical(manifest))
            self.assertFalse(bundle['runs_joined']); self.assertEqual(bundle['runs'][0]['audit']['packets_committed'], 3)
            path = Path(temp) / 'manifest.json'; path.write_bytes(replay.canonical(manifest))
            for fmt in ('json', 'markdown'):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/paired-replay-133.py'),
                                         '--root', temp, '--manifest', str(path), '--format', fmt],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), bundle) if fmt == 'json' else self.assertEqual(result.stdout, replay.markdown(bundle))
            manifest['runs'][0]['sha256'] = '0' * 64; path.write_bytes(replay.canonical(manifest))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/paired-replay-133.py'),
                                     '--root', temp, '--manifest', str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2); self.assertEqual(result.stdout, '')
            self.assertNotIn(temp, result.stderr)

    def test_manifest_rejects_traversal_duplicates_origin_symlinks_and_mixed_kind(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = manifest_for(encode(fixture()), temp)
            invalid = [dict(manifest, extra=True), dict(manifest, runs=[]), dict(manifest, runs=manifest['runs'] * 2)]
            for field, value in [('path', '../Paired132.txt'), ('path', '/tmp/Paired132.txt'),
                                 ('id', True), ('sha256', 'F' * 64)]:
                changed = deepcopy(manifest); changed['runs'][0][field] = value; invalid.append(changed)
            for value in invalid:
                with self.assertRaises(ValueError): replay.replay_manifest(temp, replay.canonical(value))
            target = Path(temp) / manifest['runs'][0]['path']
            raw = sparse([0, 1_000_000], kind='market_declared')
            otherpath = manifest['runs'][0]['path'].replace('-1-1000/', '-2-1000/')
            other = Path(temp) / otherpath; other.parent.mkdir(); other.write_bytes(raw)
            changed = deepcopy(manifest); changed['runs'].append(dict(id='run002', path=otherpath, sha256=replay.digest(raw)))
            with self.assertRaisesRegex(ValueError, 'mixed_provenance'): replay.replay_manifest(temp, replay.canonical(changed))
            wrongpath = manifest['runs'][0]['path'].replace('-1000/', '-1001/')
            wrong = Path(temp) / wrongpath; wrong.parent.mkdir(); wrong.write_bytes(target.read_bytes())
            changed = deepcopy(manifest); changed['runs'][0]['path'] = wrongpath
            with self.assertRaisesRegex(ValueError, 'origin'): replay.replay_manifest(temp, replay.canonical(changed))
            saved = target.read_bytes(); target.unlink(); external = Path(temp) / 'external'; external.write_bytes(saved); target.symlink_to(external)
            with self.assertRaisesRegex(ValueError, 'symlink'): replay.replay_manifest(temp, replay.canonical(manifest))

    def test_native_label_has_no_financial_time_bridge_or_order_admission(self):
        cursor = replay.Replay(sparse([0, 1_000_000], kind='market_declared'))
        packet = cursor.peek()
        with self.assertRaisesRegex(ValueError, 'unverified'): cursor.financial_tick(packet)
        with self.assertRaisesRegex(ValueError, 'invented_only'): invented_tick(packet)
        for key, value in replay.DENIED.items(): self.assertEqual(packet[key], value)
        drain(cursor); self.assertEqual(cursor.report()['financial_engine_events'], 0)

    def test_invented_gap_stops_costs_single_position_and_daily_latch_both_sides(self):
        for side in (1, -1):
            raw = sparse([0, 3_000_000_000, 3_001_000_000, 3_002_000_000],
                         [1.1, 1.1, 1.09 if side == 1 else 1.11, 1.1])
            cursor = replay.Replay(raw); sim = engine(side); position = None; boundaries = []
            for index in range(4):
                packet = cursor.peek(); tick = invented_tick(packet); sim.step_tick(tick); cursor.ack(packet)
                if index == 1:
                    position = deepcopy(sim.position); self.assertIsNotNone(position)
                    self.assertEqual(position.lots, .22)  # floor(25 / (102 + 7), step .01)
                    self.assertAlmostEqual(position.entry, 1.10012 if side == 1 else 1.09998)
                    before = sim.checkpoint()
                    bar = Bar(datetime(2024, 1, 1, 1, tzinfo=timezone.utc), 1.1, 1.1, 1.1, 1.1, 1)
                    sim._open(bar, -side, .001); self.assertEqual(sim.checkpoint(), before)
                if index >= 2:
                    self.assertTrue(sim.paused); self.assertIsNone(sim.position)
                    self.assertEqual(len(sim.trades), 1)
                boundaries.append((cursor.checkpoint(), sim.checkpoint()))
            trade = sim.trades[0]
            expected_exit = 1.08998 if side == 1 else 1.11012
            expected_net = side * (expected_exit - position.entry) * .22 * 100000 - .22 * 7
            self.assertEqual(trade['reason'], 'stop_tick'); self.assertAlmostEqual(trade['exit'], expected_exit)
            self.assertAlmostEqual(trade['net_pnl'], expected_net); self.assertLess(expected_net, -100)
            self.assertGreater(-expected_net, Config().initial_equity * Config().risk_fraction)
            before = sim.checkpoint(); sim._open(bar, side, .001); self.assertEqual(sim.checkpoint(), before)
            self.assertEqual(cursor.report()['sampling_gap_count'], 1)
            for cursor_state, engine_state in boundaries:
                recovered = replay.Replay.restore(raw, cursor_state)
                restored = InjectedTick019B.restore(engine_state, Config())
                for packet in drain(recovered): restored.step_tick(invented_tick(packet))
                self.assertEqual(restored.checkpoint(), sim.checkpoint())
                restored._open(bar, side, .001); self.assertEqual(restored.checkpoint(), sim.checkpoint())

    def test_invented_target_overshoot_and_joint_restart_at_every_boundary(self):
        for side in (1, -1):
            raw = sparse([0, 3_000_000_000, 3_001_000_000, 3_002_000_000],
                         [1.1, 1.1, 1.11 if side == 1 else 1.09, 1.1])
            baseline = engine(side); cursor = replay.Replay(raw); boundaries = []
            for packet in drain(cursor):
                baseline.step_tick(invented_tick(packet))
                boundaries.append(baseline.checkpoint())
            baseline.finish(); expected = baseline.checkpoint()
            trade = baseline.trades[0]
            self.assertEqual(trade['reason'], 'target_tick'); self.assertAlmostEqual(trade['exit'], trade['target'])
            self.assertAlmostEqual(trade['net_pnl'], .22 * (200 - 7))
            for index, engine_state in enumerate(boundaries):
                pending = replay.Replay(raw)
                for _ in range(index + 1): pending.ack(pending.peek())
                recovered = replay.Replay.restore(raw, pending.checkpoint())
                sim = InjectedTick019B.restore(engine_state, Config())
                # Simulate crash after consumer step but before cursor ack: same tick is idempotent.
                previous = drain(replay.Replay(raw))[index]; before = sim.checkpoint()
                self.assertFalse(sim.step_tick(invented_tick(previous))); self.assertEqual(sim.checkpoint(), before)
                for packet in drain(recovered): sim.step_tick(invented_tick(packet))
                sim.finish(); self.assertEqual(sim.checkpoint(), expected)
            with self.assertRaises(ValueError): baseline.step_tick(invented_tick(previous))


if __name__ == '__main__':
    unittest.main()
