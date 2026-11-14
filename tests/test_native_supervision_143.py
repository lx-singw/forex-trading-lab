"""Scripted channel only. Tests never launch a Windows process."""
import tempfile
import subprocess
import sys
from pathlib import Path
import unittest

from forex_demo_lab.acquisition_lifecycle_138 import Lifecycle,Policy
from forex_demo_lab.native_supervision_143 import NativePort,NativeSupervisor,local_windows_path,now_us
from forex_demo_lab.paired_replay_133 import canonical,DENIED
from forex_demo_lab.segment_journal_138 import Journal,DiskStore
from forex_demo_lab.supervision_140 import Ledger,Cause,inspect_ledger
from test_acquisition_138 import GOOD,blobs
import test_helper_health_142 as health_tests


class Channel:
    def __init__(self,mode='good'):
        self.mode=mode;self.owner_exit_observed=False;self.operations=[];self.token=None;self.sequence=0
    def start(self,token,duration_ms):
        self.token=token;self.operations.append('START')
        return canonical(dict(schema='native_health142_start_v1',token=token,contained=self.mode!='uncontained',resumed=True,helper_pid=42))
    def request(self,operation,challenge):
        self.operations.append(operation)
        if operation=='EXIT':
            return canonical(dict(schema='native_health142_exit_v1',token=self.token,challenge=challenge,exit_observed=True,
                                  cancel_ack=True,job_closed=True,clear_ack=True,close_ack=True,forced=False))
        self.sequence+=1;tick=now_us()//1000
        updates=dict(token=self.token,challenge=challenge,operation=operation,sample_sequence=self.sequence,
                     sample_tick_ms=tick,owner_tick_ms=tick,cancel_ack=operation=='CANCEL')
        if operation=='POLL':
            if self.mode=='malformed':return b'{}'
            if self.mode=='stale':updates['sample_tick_ms']=tick-2000
            if self.mode=='power':updates['mains']=False
            if self.mode=='exit':updates['running']=False
        elif self.mode=='cancel_denied':updates['cancel_ack']=False
        return health_tests.wire(**updates)
    def close(self):self.owner_exit_observed=True


def make(root,channel,enabled=True,budget=10_000_000):
    job='a'*32;life=Lifecycle(Journal(job,lambda name:DiskStore(root,name)),Policy(enabled=True,max_elapsed_us=budget))
    return NativeSupervisor(life,NativePort(channel),Ledger(root,job),enabled=enabled)


class NativeSupervision143Tests(unittest.TestCase):
    def test_default_off_does_not_launch_or_write(self):
        with tempfile.TemporaryDirectory() as root:
            channel=Channel();s=make(root,channel,False)
            self.assertFalse(s.start(now_us(),GOOD));self.assertEqual(channel.operations,[])
            self.assertEqual(s.helper.calls['start'],0)
            for k,v in DENIED.items():self.assertEqual(s.snapshot()[k],v)

    def test_invalid_guard_blocks_native_start(self):
        from dataclasses import replace
        from forex_demo_lab.acquisition_lifecycle_138 import AccountMode
        for mode in (AccountMode.REAL,AccountMode.CONTEST):
            with tempfile.TemporaryDirectory() as root:
                c=Channel();s=make(root,c)
                self.assertFalse(s.start(now_us(),replace(GOOD,actual_mode=mode)))
                self.assertEqual(c.operations,[]);self.assertEqual(s.cause,Cause.GUARD)

    def test_uncontained_start_ack_is_rejected_and_channel_closed(self):
        p=NativePort(Channel('uncontained'))
        self.assertFalse(p.start('a'*32,10_000));self.assertTrue(p.channel.owner_exit_observed)

    def test_bad_health_packet_causes_shutdown_without_a_healthy_cache(self):
        p=NativePort(Channel('malformed'))
        self.assertFalse(p.start('a'*32,10_000));self.assertTrue(p.channel.owner_exit_observed)
        with self.assertRaises(OSError):p.poll(now_us())

    def test_clean_native_port_drives_invented_lifecycle_and_binds_both_journals(self):
        with tempfile.TemporaryDirectory() as root:
            s=make(root,Channel())
            try:
                self.assertTrue(s.start(now_us(),GOOD));self.assertTrue(s.observe(now_us(),GOOD))
                mark=now_us();self.assertTrue(s.record_context(mark,mark,GOOD,GOOD))
                self.assertTrue(s.begin_triple(now_us(),GOOD));self.assertTrue(s.finish_triple(now_us(),GOOD))
                s.stop(now_us(),GOOD)
                self.assertTrue(s.snapshot()['cleanup_complete']);self.assertEqual(s.life.journal.committed,1)
                r=inspect_ledger(s.ledger.path.read_bytes(),blobs(root))
                self.assertTrue(r['lifecycle_acknowledged_prefix_bound']);self.assertFalse(r['native_supervision_certified'])
                self.assertTrue(s.snapshot()['acquisition_events_invented_only'])
            finally:s.helper.cancel()

    def test_stale_power_and_exact_exit_samples_stop_before_any_invented_commit(self):
        for mode,cause in [('stale',Cause.STALE),('power',Cause.POWER),('exit',Cause.EXIT)]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as root:
                s=make(root,Channel(mode))
                try:
                    self.assertTrue(s.start(now_us(),GOOD));self.assertFalse(s.observe(now_us(),GOOD))
                    self.assertEqual(s.cause,cause);self.assertEqual(s.life.journal.committed,0)
                finally:s.helper.cancel()

    def test_failed_cancel_does_not_fabricate_exit_or_cleanup_receipt(self):
        p=NativePort(Channel('cancel_denied'));self.assertTrue(p.start('a'*32,10_000))
        self.assertFalse(p.cancel());self.assertFalse(p.confirm_exit());self.assertTrue(p.channel.owner_exit_observed)

    def test_prototype_duration_and_path_limits(self):
        for duration in (0,-1,30_001,True):
            c=Channel();p=NativePort(c);self.assertFalse(p.start('a'*32,duration));self.assertEqual(c.operations,[])
        for path in ('\\\\server\\share\\ForexDemoHealthOwner142.exe','C:\\x\\..\\ForexDemoHealthOwner142.exe','C:\\wrong.exe'):
            with self.assertRaises(ValueError):local_windows_path(path,'ForexDemoHealthOwner142.exe')

    def test_no_future_cache_packet_is_selected(self):
        p=NativePort(Channel());self.assertTrue(p.start('a'*32,10_000))
        try:
            with self.assertRaises(OSError):p.poll(0)
        finally:p.cancel()

    def test_state_initialization_matches_frozen140_and_rejects_reused_lifecycle(self):
        with tempfile.TemporaryDirectory() as root:
            s=make(root,Channel());self.assertEqual(s.state,'off');self.assertFalse(s.start_attempted)
            self.assertTrue(s.start(now_us(),GOOD))
            try:
                with self.assertRaises(ValueError):NativeSupervisor(s.life,s.helper,s.ledger,enabled=True)
            finally:s.stop(now_us(),GOOD)

    def test_native_exercise_cli_is_off_without_explicit_flag(self):
        import json
        script=Path(__file__).resolve().parents[1]/'scripts/native-supervision-143.py'
        r=subprocess.run([sys.executable,str(script)],capture_output=True,timeout=5,check=True)
        value=json.loads(r.stdout);self.assertFalse(value['enabled'])
        self.assertFalse(value['orders_available']);self.assertFalse(value['market_data_qualified'])


if __name__=='__main__':unittest.main()
