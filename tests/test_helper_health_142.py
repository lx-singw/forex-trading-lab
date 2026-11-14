"""Invented health packets only; no Windows/API dependencies."""
import tempfile
import unittest

from forex_demo_lab.helper_health_142 import HealthDecoder
from forex_demo_lab.paired_replay_133 import canonical
from forex_demo_lab.supervision_140 import Cause, MAX_STATUS_AGE_US
from test_acquisition_138 import GOOD
import test_supervision_140 as supervision_tests

TOKEN, CHALLENGE = 'a'*32, 'b'*32


def wire(**updates):
    value = dict(schema='native_health142_status_v1',token=TOKEN,challenge=CHALLENGE,operation='POLL',
                 contained=True,running=True,sample_valid=True,sample_sequence=1,sample_tick_ms=100,
                 owner_tick_ms=120,create_ack=True,set_ack=True,ready_signal=True,mains=True,
                 helper_running_marker=True,cancel_ack=False)
    value.update(updates)
    return canonical(value)


class HelperHealth142Tests(unittest.TestCase):
    def test_native_age_and_round_trip_are_charged_without_cross_os_epoch(self):
        report=HealthDecoder(TOKEN).decode(wire(),CHALLENGE,2_000_000,2_030_000)
        self.assertEqual(report.observed_us,1_980_000)
        self.assertEqual(2_030_000-report.observed_us,50_000)

    def test_duplicated_native_sample_never_advances_freshness(self):
        d=HealthDecoder(TOKEN); first=d.decode(wire(),CHALLENGE,2_000_000,2_010_000)
        second=d.decode(wire(owner_tick_ms=620),CHALLENGE,2_500_000,2_510_000)
        self.assertEqual(first.observed_us,second.observed_us)

    def test_new_sample_can_advance_but_never_reverse_sequence_or_ticks(self):
        d=HealthDecoder(TOKEN); d.decode(wire(),CHALLENGE,2_000_000,2_010_000)
        r=d.decode(wire(sample_sequence=2,sample_tick_ms=350,owner_tick_ms=360),CHALLENGE,2_250_000,2_260_000)
        self.assertEqual(r.observed_us,2_240_000)
        for changes in [dict(sample_sequence=1),dict(sample_tick_ms=99),dict(owner_tick_ms=359)]:
            with self.assertRaises(ValueError): d.decode(wire(**changes),CHALLENGE,2_500_000,2_510_000)

    def test_same_sequence_changed_contents_is_rejected(self):
        for changes in [dict(mains=False),dict(set_ack=False,ready_signal=False),dict(sample_tick_ms=101)]:
            d=HealthDecoder(TOKEN);d.decode(wire(),CHALLENGE,2_000_000,2_010_000)
            with self.assertRaises(ValueError): d.decode(wire(**changes),CHALLENGE,2_100_000,2_110_000)

    def test_wrong_token_challenge_schema_types_unknown_fields_and_uncontained_rejected(self):
        for changes in [dict(token='c'*32),dict(challenge='c'*32),dict(schema='other'),dict(running=1),
                        dict(sample_sequence=True),dict(sample_tick_ms=-1),dict(untrusted=True),dict(contained=False),dict(cancel_ack=True)]:
            with self.assertRaises(ValueError):HealthDecoder(TOKEN).decode(wire(**changes),CHALLENGE,2_000_000,2_010_000)

    def test_slow_round_trip_invalid_ids_and_future_native_tick_rejected(self):
        for sent,received in [(True,2_000_000),(-1,1),(2,1),(0,1_000_001)]:
            with self.assertRaises(ValueError): HealthDecoder(TOKEN).decode(wire(),CHALLENGE,sent,received)
        with self.assertRaises(ValueError):HealthDecoder('invalid')
        with self.assertRaises(ValueError):HealthDecoder(TOKEN).decode(wire(sample_tick_ms=121),CHALLENGE,2_000_000,2_010_000)

    def test_no_sample_during_startup_is_not_readiness_and_sample_loss_afterward_fails(self):
        d=HealthDecoder(TOKEN)
        self.assertIsNone(d.decode(wire(sample_valid=False),CHALLENGE,2_000_000,2_010_000))
        d.decode(wire(),CHALLENGE,2_000_000,2_010_000)
        with self.assertRaises(ValueError):d.decode(wire(sample_valid=False),CHALLENGE,2_100_000,2_110_000)

    def test_readiness_without_create_set_or_running_marker_is_contradictory(self):
        for key in ('create_ack','set_ack','helper_running_marker'):
            with self.assertRaises(ValueError):HealthDecoder(TOKEN).decode(wire(**{key:False}),CHALLENGE,2_000_000,2_010_000)

    def test_exact_child_exit_is_separate_from_cleanup_acknowledgement(self):
        r=HealthDecoder(TOKEN).decode(wire(running=False,sample_valid=False),CHALLENGE,2_000_000,2_010_000)
        self.assertFalse(r.running);self.assertFalse(r.create_ack);self.assertFalse(r.ready_signal)

    def test_valid_but_old_sample_is_kept_old(self):
        r=HealthDecoder(TOKEN).decode(wire(owner_tick_ms=2120),CHALLENGE,3_000_000,3_010_000)
        self.assertGreater(3_010_000-r.observed_us,MAX_STATUS_AGE_US)

    def test_decoded_observations_drive_frozen140_and_abort_invented_pending_on_stale_power_or_exit(self):
        factory=supervision_tests.Supervision140Tests()
        for updates,expected in [(dict(owner_tick_ms=1120),Cause.STALE),(dict(sample_sequence=2,sample_tick_ms=350,owner_tick_ms=360,mains=False),Cause.POWER),(dict(running=False),Cause.EXIT)]:
            with self.subTest(expected=expected),tempfile.TemporaryDirectory() as root:
                s,_=factory.make(root);s.start(1_000_000,GOOD)
                decoder=HealthDecoder(TOKEN)
                s.helper.report=decoder.decode(wire(),CHALLENGE,2_000_000,2_010_000)
                self.assertTrue(s.observe(2_010_000,GOOD));self.assertTrue(s.record_context(2_010_001,2_010_002,GOOD,GOOD))
                self.assertTrue(s.begin_triple(2_010_003,GOOD))
                s.helper.report=decoder.decode(wire(**updates),CHALLENGE,3_000_000,3_010_000)
                self.assertFalse(s.finish_triple(3_010_000,GOOD));self.assertEqual(s.cause,expected)
                self.assertEqual(s.life.journal.committed,0);self.assertIsNone(s.life.pending)
                self.assertEqual(factory.audit(root,s)['cause'],expected.value)


if __name__=='__main__':unittest.main()
