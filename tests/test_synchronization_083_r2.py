"""Fresh fixture revision; original083 failed test source/report stay frozen."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import test_synchronization_083 as prior

from forex_demo_lab.synchronization_083 import integer,decode_signal083,ProbeRejected


def fixture083_r2(path,bindings=None,**cfg):
    f=prior.fixture083(path,bindings=bindings,**cfg)
    if 'wire_change' not in cfg:return f
    offset=integer(cfg['wire_change'],0,143)
    original=f.peer.exchange
    def exchange(*args):
        saved=f.peer.cfg.pop('wire_change')
        try:lease=original(*args)
        finally:f.peer.cfg['wire_change']=saved
        if lease.value.status=='boundary':
            raw=bytearray(lease.value.raw);raw[offset]^=1
            lease.value=replace(lease.value,raw=bytes(raw))
        return lease
    f.peer.exchange=exchange
    return f


class Sync083R2Tests(prior.Sync083Tests):
    def f(self,**cfg):return fixture083_r2(self.root/'marker',**cfg)
    def test_source_build_phase_episode_sequence_and_padding_changes_rejected(self):
        for offset in (0,8,24,56,88,104,108,109):
            with self.subTest(offset=offset),TemporaryDirectory() as d:
                f=fixture083_r2(Path(d)/'marker',wire_change=offset)
                self.assertFalse(f.model.run(True)['modeled_completed'])
                self.assertEqual(f.peer.cleanup_calls,1)
    def test_zero_magic_offset_is_really_changed_and_decoder_rejects(self):
        f=self.f(wire_change=0);deadline=f.clock.boot+60000
        lease=f.peer.exchange('ready',1,f.bindings,f.model.episode,deadline)
        try:
            raw=lease.snapshot().raw;self.assertNotEqual(raw[:8],b'FXDL083S')
            self.assertEqual(raw[0],ord('F')^1)
            with self.assertRaises(ProbeRejected):
                decode_signal083(raw,'ready',1,f.bindings,f.model.episode,f.clock.boot,deadline,0)
        finally:lease.close();f.peer.cleanup_model()
    def test_missing_tamper_key_keeps_valid_frame_unchanged(self):
        f=self.f();deadline=f.clock.boot+60000
        lease=f.peer.exchange('ready',1,f.bindings,f.model.episode,deadline)
        try:
            raw=lease.snapshot().raw;self.assertEqual(raw[:8],b'FXDL083S')
            self.assertEqual(decode_signal083(raw,'ready',1,f.bindings,f.model.episode,
                f.clock.boot,deadline,0)['deadline'],deadline)
        finally:lease.close();f.peer.cleanup_model()
    def test_tamper_offset_boolean_negative_and_outside_frame_rejected(self):
        for offset in (False,-1,144):
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.f(wire_change=offset)
