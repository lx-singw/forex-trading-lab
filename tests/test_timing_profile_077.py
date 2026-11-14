from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.timing_profile_077 import *
from forex_demo_lab.private_guard_065 import Identity065
from forex_demo_lab.sharing_runtime_069 import Trace069
from forex_demo_lab.sharing_runtime_066 import attach_existing
from forex_demo_lab.sharing_adapter_076 import validate_build076
from forex_demo_lab.sharing_integration_072 import source_contract072
from forex_demo_lab.sharing_build_075 import build_record075
from test_fresh_data_031 import API as AccountAPI

PROOF = dict(all_handles_closed=True, allocations_released=True, unconfirmed_handles=0)


class Clock077:
    def __init__(self):
        self.utc = int(datetime(2026,10,8,12,tzinfo=timezone.utc).timestamp())*1000
        self.mono = 0; self.boot = 100000
    def __call__(self): return self.utc, self.mono, self.boot
    def advance(self, ms):
        self.utc += ms; self.mono += ms*1000000; self.boot += ms


class Base077:
    def __init__(self, meter): self.meter = meter; self.closed = 0; self.bad = False
    def finish(self):
        self.closed += 1
        return {**PROOF, 'unconfirmed_handles': int(self.bad)}


class Reader077:
    def __init__(self, meter, clock, base, cost=0):
        self.meter, self.clock, self.f, self.cost = meter, clock, base, cost
        self.peer = Identity065(7,11,r'c:\program files\metatrader 5\terminal64.exe','d'*64,1,'private-logon')
        self.helper = Identity065(9,12,'package/python3.13.exe','4'*64,1,'private-logon')
        self.hashes = []
        self.values = {self.peer.image:'d'*64, self.helper.image:'4'*64,
            'editor':'c'*64, 'artifact':'b'*64, 'launcher':'1'*64,
            'config':'2'*64, 'library':'3'*64, **dict.fromkeys(('source0','source1','source2','source3'),'a'*64)}
        self.on_hash = None
    def unique_pid(self):
        self.meter.consume('process_snapshots'); return self.peer.pid
    def identity(self, pid):
        self.meter.consume('process_opens'); self.meter.consume('identity_tokens')
        value = self.helper if pid == self.helper.pid else self.peer
        self.hash_file(value.image); return value
    def hash_file(self, path):
        self.meter.consume('hash_reads'); self.meter.consume('hash_bytes',1048576)
        self.hashes.append(str(path)); self.clock.advance(self.cost)
        if self.on_hash: self.on_hash(str(path))
        self.meter.check(); return self.values[str(path)]


def build077():
    contract = source_contract072(dict.fromkeys(SOURCE_INPUTS,'a'*64))
    artifact = dict(sha256='b'*64,size=100,raw=None)
    log = 'Result: 0 errors, 0 warnings, synthetic elapsed\n'
    record = build_record075(contract,1,log,artifact,'c'*64,'d'*64)
    return validate_build076(record,contract,log,artifact,'c'*64,'d'*64)


def fixture077(root, cost=0, attach=True):
    clock = Clock077(); meter = Meter077(clock); build = build077()
    chain = HelperChain068(('launcher','1'*64),('config','2'*64),
        (('package/python3.13.exe','4'*64),),('library','3'*64),'private-alias')
    session = Reservation077(root/'profile-marker',build,'e'*64,'f'*64,'5'*64,chain,meter)
    owner = Resources069(session,meter,Trace069()); owner.base = Base077(meter)
    reader = Reader077(meter,clock,owner.base,cost)
    private = PrivateReader066(reader,reader.helper)
    sdk = AccountAPI(); calls = []
    sdk.__version__ = '5.0.6231'
    sdk.initialize = lambda *a,**k: calls.append('initialize') or True
    sdk.shutdown = lambda: calls.append('shutdown')
    def forbidden(*a,**k): raise AssertionError('forbidden market/order call')
    sdk.symbol_info_tick = sdk.copy_ticks_range = sdk.copy_rates_range = sdk.order_send = forbidden
    sdk.terminal.path = r'C:\Program Files\MetaTrader 5'; sdk.terminal.data_path = r'C:\private-demo'
    sdk.terminal.build = 6244; owner.sdk = sdk
    if attach:
        owner.trace.run('sdk_attach',attach_existing,sdk,session,private,reader.peer,meter)
        session.confirm_attach(owner)
    core = FullGuard065(sdk,private,reader.peer,sdk.terminal.data_path,6244,
        ('editor','c'*64),('artifact','b'*64),meter)
    return NS(root=root,clock=clock,meter=meter,build=build,chain=chain,session=session,
        owner=owner,reader=reader,private=private,sdk=sdk,calls=calls,core=core)


def guard077(f):
    return ProfileGuard077(f.owner,f.core,f.build,'e'*64,'f'*64,'5'*64,f.chain,
        'launcher','private-alias',lambda:'library',dict(zip(SOURCE_INPUTS,('source0','source1','source2','source3'))))


class FixtureTests077(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)
    def f(self, **kw): return fixture077(self.root, **kw)
    def sync(self, guard=None):
        clock = Clock077(); meter = HandshakeMeter077(clock)
        h = Handshake077(self.root/'sync-marker',build077(),(1,2,3),meter,guard or (lambda:True))
        return clock,meter,h
    def signal(self,h,kind,**kw):
        now = h.meter.check()[2]
        return Signal077(**{**dict(kind=kind,phase=SYNC_PHASE,build_sha256=h.build.sha256,
            identity=h.identity,origin_boot_ms=h.origin,deadline_boot_ms=h.deadline,
            start_boot_ms=now,end_boot_ms=now),**kw})
    def held(self):
        c,m,h = self.sync()
        h.accept(self.signal(h,'ready')); h.accept(self.signal(h,'release'))
        c.advance(1); h.accept(self.signal(h,'holding'))
        return c,m,h


class MeterTests077(FixtureTests077):
    def test_wrong_date_is_rejected(self):
        c=Clock077(); c.utc-=86400000
        with self.assertRaises(ProbeRejected): Meter077(c)
    def test_clock_shape_and_boolean_rejected(self):
        for bad in ((True,0,0),(1,2),[1,2,3],(1,-1,3)):
            with self.assertRaises(ProbeRejected): Meter077(lambda:bad)
    def test_clock_reversal_latches(self):
        c=Clock077(); m=Meter077(c); c.boot-=1
        with self.assertRaises(ProbeRejected): m.check()
        c.boot+=1
        with self.assertRaises(ProbeRejected): m.check()
    def test_skew_and_session_deadline_rejected(self):
        for mode in ('skew','expiry'):
            c=Clock077(); m=Meter077(c)
            if mode=='skew': c.utc+=1001
            else: c.advance(SESSION_MS)
            with self.assertRaises(ProbeRejected): m.check()
    def test_zero_grant_and_byte_caps_reject_without_refund(self):
        for key,amount in (('reads',1),('script_arms',1),('deployment_writes',1),
            ('log_reads',1),('hash_bytes',LIMITS077['hash_bytes']+1),('sdk_queries',129)):
            m=Meter077(Clock077())
            with self.assertRaises(ProbeRejected): m.consume(key,amount)
            self.assertTrue(m.stopped); self.assertEqual(m.counts[key],0)
    def test_sample_and_clock_count_caps(self):
        m=Meter077(Clock077()); m.consume('profile_samples',4)
        with self.assertRaises(ProbeRejected): m.consume('profile_samples')
        m=Meter077(Clock077()); m.counts['clock_samples']=100000
        with self.assertRaises(ProbeRejected): m.check()
    def test_owned_cleanup_remains_attemptable_after_exhaustion(self):
        m=Meter077(Clock077()); m.stopped=True
        m.cleanup('sdk_shutdowns'); self.assertEqual(m.counts['sdk_shutdowns'],1)
        m.cleanup('sdk_shutdowns'); self.assertTrue(m.cleanup_exceeded)


class PolicyTests077(FixtureTests077):
    def test_contract_has_exact_small_budgets_and_no_native_authority(self):
        f=self.f(); r=profile_contract077(f.build,'e'*64,'f'*64,'5'*64,f.chain)
        self.assertEqual(r['limits']['guards'],8); self.assertEqual(r['fixed_samples'],4)
        self.assertFalse(r['execution_authorized']); self.assertFalse(r['latency_guaranteed'])
        self.assertEqual(r['maximum_script_launches'],0); self.assertEqual(r['maximum_orders'],0)
    def test_policy_unknown_missing_boolean_and_authority_fields_rejected(self):
        f=self.f(); expected=json.loads(f.session.raw)
        for r in ({**expected,'extra':0},{k:v for k,v in expected.items() if k!='limits'},
            {**expected,'fixed_samples':True},{**expected,'execution_authorized':True},
            {**expected,'maximum_sdk_connections':True}):
            raw=encoded076(r)
            with self.assertRaises(ProbeRejected): validate_policy077(raw,expected,hashlib.sha256(raw).hexdigest())
    def test_policy_raw_digest_duplicate_keys_and_noncanonical_bytes_rejected(self):
        f=self.f(); expected=json.loads(f.session.raw)
        for raw in (f.session.raw+b' ',f.session.raw.replace(b'"fixed_samples":4',b'"fixed_samples":4,"fixed_samples":4'),b'x'*8193):
            with self.assertRaisesRegex(ProbeRejected,'^profile_policy_rejected$'):
                validate_policy077(raw,expected,hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ProbeRejected): validate_policy077(f.session.raw,expected,'0'*64)
    def test_reservation_is_exclusive_and_has_no_assumed_sidecar(self):
        f=self.f(); self.assertEqual((self.root/'profile-marker').read_bytes(),f.session.raw)
        self.assertFalse((self.root/'profile-marker.sha256').exists())
        with self.assertRaises(ProbeRejected):
            Reservation077(self.root/'profile-marker',f.build,'e'*64,'f'*64,'5'*64,f.chain,Meter077(Clock077()))
    def test_sdk_attempt_is_spent_before_budget_failure(self):
        f=self.f(attach=False); f.meter.counts['sdk_connections']=1
        with self.assertRaises(ProbeRejected): f.session.sdk_attempt()
        self.assertTrue(f.session.spent)
        r=close_owned069(f.owner); self.assertTrue(r['sdk_shutdown_called'])
        self.assertEqual(f.calls,['shutdown'])
    def test_failed_attach_still_shuts_down_once(self):
        f=self.f(attach=False); f.sdk.initialize=lambda *a,**k:False
        with self.assertRaises(ProbeRejected): attach_existing(f.sdk,f.session,f.private,f.reader.peer,f.meter)
        self.assertTrue(close_owned069(f.owner)['sdk_shutdown_called'])
        self.assertFalse(close_owned069(f.owner)['sdk_shutdown_called']); self.assertEqual(f.calls,['shutdown'])


class ProfileTests077(FixtureTests077):
    def test_unconfirmed_or_failed_attach_cannot_profile(self):
        f=self.f(attach=False); f.session.sdk_attempt()
        with self.assertRaises(ProbeRejected): guard077(f)
        with self.assertRaises(ProbeRejected): f.session.confirm_attach(f.owner)
        self.assertTrue(close_owned069(f.owner)['sdk_shutdown_called'])
    def test_attachment_confirmation_requires_single_completed_owned_stage(self):
        f=self.f(attach=False); f.session.sdk_attempt()
        f.owner.trace.enter('sdk_attach')
        with self.assertRaises(ProbeRejected): f.session.confirm_attach(f.owner)
        self.assertFalse(f.session.attached); close_owned069(f.owner)
    def test_duplicate_attachment_confirmation_spends_session(self):
        f=self.f()
        with self.assertRaises(ProbeRejected): f.session.confirm_attach(f.owner)
        self.assertTrue(f.session.stopped); close_owned069(f.owner)
    def test_changed_sdk_version_invalidates_owner_graph(self):
        f=self.f(); g=guard077(f); f.sdk.__version__='changed'
        self.assertFalse(profile_once077(f.owner,g)['completed'])
        self.assertEqual(f.calls,['initialize','shutdown'])
    def test_four_composite_samples_eight_full_guards_and_exact_costs(self):
        f=self.f(cost=10); r=profile_once077(f.owner,guard077(f))
        self.assertTrue(r['completed']); self.assertEqual(r['samples_completed'],4)
        self.assertEqual(r['observed_core_guard_max_ms'],60)
        self.assertEqual(r['observed_composite_max_ms'],200)
        self.assertEqual(r['counts']['guards'],8); self.assertEqual(r['counts']['sdk_queries'],88)
        for row in r['samples']: self.assertEqual(row['hash_reads'],20)
        self.assertEqual(f.calls,['initialize','shutdown']); self.assertEqual(f.owner.base.closed,1)
        self.assertFalse(r['native_launch_ready']); self.assertFalse(r['latency_guaranteed'])
    def test_helper_inputs_and_all_sources_rehashed_in_every_sample(self):
        f=self.f(); r=profile_once077(f.owner,guard077(f)); self.assertTrue(r['completed'])
        for name in ('launcher','config','library','source0','source1','source2','source3'):
            self.assertEqual(f.reader.hashes.count(name),4)
        self.assertEqual(f.reader.hashes.count('editor'),8); self.assertEqual(f.reader.hashes.count('artifact'),8)
    def test_real_and_contest_modes_reject_demo_looking_server(self):
        for mode in (1,2):
            with TemporaryDirectory() as d:
                f=fixture077(Path(d)); f.sdk.account.trade_mode=mode; f.sdk.account.server='Demo'
                r=profile_once077(f.owner,guard077(f)); self.assertFalse(r['completed'])
                self.assertEqual(f.calls,['initialize','shutdown'])
    def test_algo_on_disconnected_and_nonusd_rejected(self):
        for obj,key,value in (('terminal','trade_allowed',True),('terminal','connected',False),('account','currency','EUR')):
            with TemporaryDirectory() as d:
                f=fixture077(Path(d)); setattr(getattr(f.sdk,obj),key,value)
                self.assertFalse(profile_once077(f.owner,guard077(f))['completed'])
    def test_account_changes_during_helper_rehash_rejected(self):
        f=self.f(); f.reader.on_hash=lambda path:setattr(f.sdk.account,'server','changed') if path=='config' else None
        r=profile_once077(f.owner,guard077(f)); self.assertFalse(r['completed']); self.assertEqual(r['samples_completed'],0)
    def test_changed_helper_library_source_editor_and_artifact_stop(self):
        for name in ('package/python3.13.exe','library','source2','editor','artifact'):
            with TemporaryDirectory() as d:
                f=fixture077(Path(d)); f.reader.values[name]='0'*64
                self.assertFalse(profile_once077(f.owner,guard077(f))['completed'])
    def test_process_replacement_rejected_without_restart(self):
        f=self.f(); g=guard077(f); f.reader.peer=replace(f.reader.peer,creation=99)
        self.assertFalse(profile_once077(f.owner,g)['completed'])
    def test_foreign_sdk_cannot_take_owned_shutdown(self):
        f=self.f(); g=guard077(f); f.core.api._api=AccountAPI()
        self.assertFalse(profile_once077(f.owner,g)['completed'])
        self.assertEqual(f.calls,['initialize','shutdown'])
    def test_foreign_base_or_binding_graph_rejected_and_caller_closes_owner(self):
        f=self.f(); f.private.base.f=Base077(f.meter)
        with self.assertRaises(ProbeRejected): guard077(f)
        self.assertTrue(close_owned069(f.owner)['sdk_shutdown_called']); self.assertEqual(f.owner.base.closed,1)
    def test_partial_samples_survive_expiry_and_cleanup_still_runs(self):
        f=self.f(cost=10000); r=profile_once077(f.owner,guard077(f))
        self.assertFalse(r['completed']); self.assertEqual(r['samples_completed'],2)
        self.assertTrue(r['cleanup']['sdk_shutdown_called']); self.assertEqual(f.owner.base.closed,1)
    def test_interruption_runs_owned_cleanup_without_private_exception(self):
        f=self.f(); f.reader.on_hash=lambda p:(_ for _ in ()).throw(KeyboardInterrupt('private'))
        r=profile_once077(f.owner,guard077(f)); self.assertFalse(r['completed'])
        self.assertEqual(f.calls,['initialize','shutdown']); self.assertNotIn('private',json.dumps(r))
    def test_cleanup_failure_invalidates_complete_measurements(self):
        f=self.f(); f.owner.base.bad=True
        r=profile_once077(f.owner,guard077(f)); self.assertEqual(r['samples_completed'],4); self.assertFalse(r['completed'])
    def test_repeat_cannot_reinitialize_or_resample_or_shutdown_twice(self):
        f=self.f(); g=guard077(f); self.assertTrue(profile_once077(f.owner,g)['completed'])
        self.assertFalse(profile_once077(f.owner,g)['completed']); self.assertEqual(f.calls,['initialize','shutdown'])
        with self.assertRaises(ProbeRejected): f.session.sdk_attempt()
    def test_reports_have_no_private_paths_logons_or_account_identifiers(self):
        f=self.f(); raw=json.dumps(profile_once077(f.owner,guard077(f)))
        for secret in (str(f.sdk.account.login),f.sdk.account.server,'private-logon',r'C:\private-demo','package/python3.13.exe'):
            self.assertNotIn(secret,raw)
    def test_positive_submillisecond_duration_rounds_up(self):
        self.assertEqual(duration_ms077((0,0,0),(0,1,0)),1)


class HandshakeTests077(FixtureTests077):
    def test_readiness_release_hold_then_both_controls_complete_model_only(self):
        c,m,h=self.held(); c.advance(251); h.accept(self.signal(h,'write'))
        c.advance(1); h.accept(self.signal(h,'delete')); r=h.report()
        self.assertTrue(r['modeled_completed']); self.assertFalse(r['native_protocol_implemented'])
        self.assertEqual(r['events'],['ready','release','holding','write','delete'])
    def test_restart_cannot_recreate_same_reserved_episode(self):
        c,m,h=self.sync()
        with self.assertRaises(ProbeRejected): Handshake077(self.root/'sync-marker',h.build,h.identity,HandshakeMeter077(c),lambda:True)
    def test_release_before_readiness_and_duplicate_release_stop(self):
        for first in (True,False):
            with TemporaryDirectory() as d:
                c=Clock077(); h=Handshake077(Path(d)/'marker',build077(),(1,2,3),HandshakeMeter077(c),lambda:True)
                if not first: h.accept(self.signal(h,'ready')); h.accept(self.signal(h,'release'))
                with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'release'))
                self.assertTrue(h.stopped)
    def test_stale_ready_signal_and_guard_delay_rejected(self):
        c,m,h=self.sync(); signal=self.signal(h,'ready'); c.advance(2001)
        with self.assertRaises(ProbeRejected): h.accept(signal)
    def test_guard_cost_is_included_after_signal_not_cached(self):
        c=Clock077(); m=HandshakeMeter077(c)
        def guard(): m.consume('guards'); c.advance(1001); return True
        h=Handshake077(self.root/'sync-marker',build077(),(1,2,3),m,guard)
        with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'ready'))
        self.assertEqual(m.counts['guards'],2)
    def test_phase_build_identity_origin_deadline_and_bool_changes_rejected(self):
        changes=({'phase':PHASE},{'build_sha256':'0'*64},{'identity':(1,2,4)},
            {'origin_boot_ms':True},{'deadline_boot_ms':1},{'identity':(True,2,3)})
        for change in changes:
            with TemporaryDirectory() as d:
                c=Clock077(); h=Handshake077(Path(d)/'marker',build077(),(1,2,3),HandshakeMeter077(c),lambda:True)
                with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'ready',**change))
    def test_ten_second_start_gate_inclusive_then_rejects_outside(self):
        for delay,accepted in ((10000,True),(10001,False)):
            with TemporaryDirectory() as d:
                c=Clock077(); h=Handshake077(Path(d)/'marker',build077(),(1,2,3),HandshakeMeter077(c),lambda:True)
                h.accept(self.signal(h,'ready')); h.accept(self.signal(h,'release')); c.advance(delay)
                if accepted: self.assertTrue(h.accept(self.signal(h,'holding')))
                else:
                    with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'holding'))
    def test_strict_start_and_end_hold_margins(self):
        for delta in (250,29750):
            with TemporaryDirectory() as d:
                c=Clock077(); h=Handshake077(Path(d)/'marker',build077(),(1,2,3),HandshakeMeter077(c),lambda:True)
                h.accept(self.signal(h,'ready')); h.accept(self.signal(h,'release')); h.accept(self.signal(h,'holding'))
                c.advance(delta)
                with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'write'))
    def test_release_requires_time_for_full_ten_plus_thirty_seconds(self):
        c,m,h=self.sync(); h.accept(self.signal(h,'ready')); c.advance(19750)
        with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'release'))
        self.assertIsNotNone(h.release_boot); self.assertTrue(h.stopped)
    def test_probe_guard_overrunning_end_margin_invalidates(self):
        c,m,h=self.held(); c.advance(29749)
        h.guard=lambda:c.advance(1) or True
        with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'write'))
    def test_signal_from_future_or_reordered_controls_rejected(self):
        c,m,h=self.held()
        with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'write',start_boot_ms=c.boot+1,end_boot_ms=c.boot+1))
    def test_interruption_spends_episode_and_no_rearm(self):
        c,m,h=self.sync(); h.guard=lambda:(_ for _ in ()).throw(KeyboardInterrupt('private'))
        with self.assertRaisesRegex(ProbeRejected,'^handshake_signal_rejected$'): h.accept(self.signal(h,'ready'))
        h.guard=lambda:True
        with self.assertRaises(ProbeRejected): h.accept(self.signal(h,'ready'))
    def test_reboot_or_clock_skew_stops(self):
        c,m,h=self.sync(); signal=self.signal(h,'ready'); c.boot=0
        with self.assertRaises(ProbeRejected): h.accept(signal)


if __name__ == '__main__': unittest.main()
