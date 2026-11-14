from dataclasses import replace
from pathlib import Path
import hashlib
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.native_bindings_087 import *
from forex_demo_lab.build_bindings_087 import build_contract087,build_record087,verify_build087,encoded076
from test_build_bindings_087 import LOG,PINS,ROOT
from test_synchronization_086 import Clock086

RAW=b'20261008090000.000000+000'


class Reader:
    model_only=True
    def __init__(self):self.hashes={};self.hash_calls=[];self.identities={};self.pid=123;self.identity_calls=0
    def hash_file(self,path):self.hash_calls.append(path);return self.hashes[path]
    def unique_pid(self):return self.pid
    def identity(self,pid):self.identity_calls+=1;return self.identities[pid]


class Runner:
    model_only=True
    def __init__(self,c,**cfg):self.c=c;self.cfg=cfg;self.calls=0;self.arguments=[]
    def query(self,exe,args,**kw):
        self.calls+=1;self.arguments.append((exe,args,kw))
        self.c.advance(self.cfg.get('latency',0))
        if self.cfg.get('interrupt'):raise KeyboardInterrupt()
        return dict(exit_code=self.cfg.get('exit_code',0),stdout=self.cfg.get('stdout',RAW),
            stderr=self.cfg.get('stderr',b''),owned_child_absent=self.cfg.get('absent',True))


class SDK:
    model_only=True
    ACCOUNT_TRADE_MODE_DEMO=0
    __version__=SDK_VERSION
    def __init__(self):
        self.account=NS(login=1,server='private-model',currency='USD',trade_mode=0)
        self.terminal=NS(connected=True,trade_allowed=False,build=6244,path='C:\\terminal',data_path='C:\\data')
        self.symbol=NS(visible=True,currency_base='EUR',currency_profit='USD')
        self.queries=0;self.shutdowns=0
    def account_info(self):self.queries+=1;return self.account
    def terminal_info(self):self.queries+=1;return self.terminal
    def symbol_info(self,name):self.queries+=1;assert name=='EURUSD';return self.symbol
    def shutdown(self):self.shutdowns+=1;return True


def fixture087(**cfg):
    c=Clock086();meter=Meter083(c);reader=Reader();runner=Runner(c,**cfg);sdk=SDK()
    contract=build_contract087(ROOT);artifact=dict(sha256='c'*64,size=12,raw=None)
    value=build_record087(contract,1,LOG,artifact,PINS['compiler'],PINS['terminal'])
    build=verify_build087(encoded076(value),contract,LOG,artifact,PINS['compiler'],PINS['terminal'])
    terminal=Identity065(123,456,'C:\\terminal\\terminal64.exe','b'*64,2,'S-1-5-21')
    helper=Identity065(789,100,'C:\\helper\\python.exe','d'*64,2,'S-1-5-21')
    boot=boot_stamp087(RAW,c.utc*1000)
    peer=Peer084(terminal.pid,terminal.creation,terminal.session,sid_binary087(terminal.logon),boot)
    roles={
        'terminal':(terminal.image,terminal.digest),'helper':(helper.image,helper.digest),
        'editor':('C:\\terminal\\metaeditor64.exe','a'*64),'artifact':('C:\\stage\\ForexDemoSynchronization086.ex5','c'*64),
        'sdk':('C:\\sdk\\library.pyd','e'*64),'launcher':('C:\\helper\\launcher.py','f'*64),
        'config':('C:\\helper\\config.json','1'*64),'boot_script':('C:\\stage\\boot-proof-087.ps1',hashlib.sha256((ROOT/'scripts/boot-proof-087.ps1').read_bytes()).hexdigest()),
        'boot_shell':('C:\\Windows\\powershell.exe','3'*64)}
    sources={n:(str(ROOT/n),h) for n,h in contract['source_contract']['input_bindings'].items()}
    sources.update({n:(str(ROOT/n),hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in GUARD_INPUTS})
    pins=Pins087(terminal,helper,peer,'C:\\terminal','C:\\data',roles['sdk'][0],build,roles,sources)
    reader.hashes=dict([*roles.values(),*sources.values()]);reader.identities={123:terminal,789:helper}
    owner=Session087(sdk,reader,pins,meter,lambda:pins.loaded_library)
    boot_reader=BootReader087(runner,reader,meter,roles['boot_shell'][0],roles['boot_script'][0],
        (roles['boot_shell'],roles['boot_script']))
    return owner,FullGuard087(owner,boot_reader),runner,c


def model_guard087(**cfg):
    owner,g,runner,c=fixture087(**cfg);ok=False;reason=None
    try:
        if cfg.get('real'):owner.sdk.account.trade_mode=2
        if cfg.get('changed_source'):owner.reader.hashes[next(iter(owner.pins.sources.values()))[0]]='0'*64
        if cfg.get('changed_boot'):runner.cfg['stdout']=b'20261008090100.000000+000'
        if cfg.get('repeat'):
            while True:g()
        else:ok=g()==Guard083()
    except (Exception,KeyboardInterrupt):reason='binding_rejected'
    finally:cleanup=owner.close()
    return dict(modeled_completed=ok,stop_reason=reason,full_bridge_calls=g.calls,
        sdk_queries=g.metadata.queries,boot_queries=runner.calls,hash_reads=len(owner.reader.hash_calls),
        cleanup_confirmed=cleanup,shutdown_attempts=owner.sdk.shutdowns,dependencies_injected=True,
        native_boot_provider_verified=False,native_guard_wiring_verified=False,runtime_authorized=False,orders_available=False,
        native_invocations=0,sdk_connections=0,market_reads=0,orders=0)


def model_combined087():
    from test_windows_adapter_086 import World,Table
    from forex_demo_lab.windows_adapter_086 import Api086,WindowsAdapter086
    from forex_demo_lab.synchronization_086 import Transport086
    owner,guard,runner,c=fixture087()
    class SharedWorld(World):
        def call(self,name,*args):
            value=super().call(name,*args)
            if name=='WriteFile' and self.request is not None and self.request[6]==2:
                self.c.advance(5)
            return value
    w=SharedWorld();w.c=c;w.b=replace(w.b,peer=owner.pins.peer)
    api=Api086(Table(w),Table(w),c,guard.boot,lambda:w.error,lambda v:setattr(w,'error',v))
    backend=WindowsAdapter086(api,w.b,guard,lambda ms:c.advance(ms))
    def factory(o,b):
        made=backend.factory(o,b);w.bound_b=made[2];return made
    t=Transport086(w.b,c,guard,factory);ok=False;reason=None
    try:
        t.start(True)
        for access in ('write','delete'):t.control('pre',access)
        t.wait_until(c.boot+300);deadline=c.boot+60000
        t.transaction('ready',deadline).close();t.transaction('release',deadline)
        t.transaction('holding',deadline).close();t.wait_until(t.hold_start+251)
        for access in ('write','delete'):t.control('independent',access)
        t.wait_until(t.hold_start+30251);t.transaction('closed',deadline).close()
        t.wait_until(t.hold_end+251)
        for access in ('write','delete'):t.control('post',access)
        ok=True
    except (Exception,KeyboardInterrupt) as e:
        reason=str(e) if str(e) in ('sync086_episode_clock_rejected','sync_clock_rejected') else 'binding_or_budget_rejected'
    finally:
        if t.counts['cleanup']==0:ok=t.finish() and ok
        shutdown=owner.close()
    return dict(modeled_completed=ok,stop_reason=reason,summary=t.summary(),controls=len(t.probes),
        full_bridge_calls=guard.calls,sdk_queries=guard.metadata.queries,boot_queries=runner.calls,
        api_calls=api.calls,api_clock_samples=api.meter.counts['clock_samples'],remaining_handles=len(w.handles),
        remaining_allocations=len(w.buffers),shutdown_attempts=owner.sdk.shutdowns,sdk_cleanup_confirmed=shutdown,
        diagnosed_budget='raw_api_clock_samples' if api.meter.counts['clock_samples']>4096 else None,
        raw_api_clock_sample_limit=4096,
        dependencies_injected=True,native_invocations=0,sdk_connections=0,market_reads=0,orders=0,
        runtime_authorized=False,orders_available=False)


class Native087Tests(unittest.TestCase):
    def test_boot_timestamp_strict_calendar_future_and_wildcards(self):
        c=Clock086();self.assertEqual(len(boot_stamp087(RAW,c.utc*1000)),20)
        for raw in (RAW+b'\n',RAW[:-1],RAW.replace(b'09',b'**'),b'20260230090000.000000+000',
            b'20261009090000.000000+000',RAW.replace(b'+000',b'+999')):
            with self.assertRaises(Exception):boot_stamp087(raw,c.utc*1000)
    def test_timezone_equivalence_and_microseconds_preserved(self):
        c=Clock086()
        self.assertEqual(boot_stamp087(RAW,c.utc*1000),boot_stamp087(b'20261008110000.000000+120',c.utc*1000))
        self.assertNotEqual(boot_stamp087(RAW,c.utc*1000),boot_stamp087(b'20261008090000.000001+000',c.utc*1000))
    def test_query_fresh_each_call_bounded_and_no_policy_change(self):
        o,g,r,c=fixture087();a=g.boot();b=g.boot();self.assertEqual(a,b);self.assertEqual(r.calls,2)
        exe,argv,kw=r.arguments[0];self.assertEqual(argv,[exe,'-NoProfile','-NonInteractive','-File',g.boot.script])
        self.assertEqual(kw,dict(timeout_ms=2000,stdout_cap=25,stderr_cap=0));o.close()
    def test_bad_return_stderr_child_alive_and_late_query_reject(self):
        for cfg in ({'exit_code':True},{'exit_code':1},{'stderr':b'x'},{'absent':False},{'latency':2001},{'interrupt':True}):
            self.assertFalse(model_guard087(**cfg)['modeled_completed'])
    def test_boot_path_changed_and_query_limit_reject(self):
        o,g,r,c=fixture087();g.boot.script='changed'
        with self.assertRaises(Exception):g.boot()
        self.assertEqual(r.calls,0);o.close()
        o,g,r,c=fixture087();g.boot.calls=128
        with self.assertRaises(Exception):g.boot()
        self.assertEqual(r.calls,0);o.close()
    def test_sid_conversion_raw_boundary_and_invalid_values(self):
        self.assertEqual(sid_binary087('S-1-5-21'),b'\x01\x01'+b'\0'*5+b'\x05'+bytes([21,0,0,0]))
        for s in ('S-2-5-21','S-1-5',True,'S-1-5-4294967296','S-1-281474976710656-21'):
            with self.assertRaises(Exception):sid_binary087(s)
    def test_full_bridge_checks_every_source_helper_image_and_boot(self):
        o,g,r,c=fixture087();self.assertEqual(g(),Guard083());first=list(o.reader.hash_calls)
        self.assertEqual(g(),Guard083());self.assertEqual(len(o.reader.hash_calls),2*len(first))
        self.assertEqual((g.metadata.queries,r.calls,o.reader.identity_calls),(24,2,8));o.close()
    def test_real_contest_and_bool_account_type_reject(self):
        for mode in (1,2,False):
            o,g,r,c=fixture087();o.sdk.account.trade_mode=mode
            with self.assertRaises(Exception):g()
            self.assertEqual(r.calls,0);o.close()
    def test_account_changed_after_initial_guard_and_sdk_replaced(self):
        o,g,r,c=fixture087();g();o.sdk.account.login=2
        with self.assertRaises(Exception):g()
        self.assertTrue(o.close())
        o,g,r,c=fixture087();o.sdk=SDK()
        with self.assertRaises(Exception):g()
        o.close()
    def test_metadata_terminal_build_path_algo_and_disconnection_reject(self):
        for key,value in (('build',6245),('path','different'),('trade_allowed',True),('connected',False)):
            o,g,r,c=fixture087();setattr(o.sdk.terminal,key,value)
            with self.assertRaises(Exception):g()
            o.close()
    def test_source_and_each_required_role_change_reject(self):
        for role in HASH_ROLES:
            o,g,r,c=fixture087();o.reader.hashes[o.pins.hashes[role][0]]='0'*64
            with self.assertRaises(Exception):g()
            o.close()
        self.assertFalse(model_guard087(changed_source=True)['modeled_completed'])
    def test_identity_peer_boot_and_loaded_library_change_reject(self):
        for cfg in ('peer','boot','library','pid'):
            o,g,r,c=fixture087()
            if cfg=='peer':o.reader.identities[123]=replace(o.pins.terminal,creation=1000)
            if cfg=='boot':r.cfg['stdout']=b'20261008090100.000000+000'
            if cfg=='library':o.loaded_library=lambda:'changed'
            if cfg=='pid':o.reader.pid=999
            with self.assertRaises(Exception):g()
            o.close()
    def test_missing_role_source_and_mutated_pins_reject(self):
        o,g,r,c=fixture087()
        for key in ('editor','artifact','launcher','config','sdk'):
            roles=dict(o.pins.hashes);roles.pop(key)
            with self.assertRaises(Exception):replace(o.pins,hashes=roles)
        sources=dict(o.pins.sources);sources.pop(next(iter(sources)))
        with self.assertRaises(Exception):replace(o.pins,sources=sources)
        o.pins.hashes['editor']=('changed','a'*64)
        with self.assertRaises(Exception):g()
        o.close()
    def test_repeated_guard_hits_finite_budget_without_relabeling(self):
        r=model_guard087(repeat=True);self.assertFalse(r['modeled_completed'])
        self.assertEqual(r['sdk_queries'],1024);self.assertLessEqual(r['full_bridge_calls'],96)
        self.assertEqual(r['shutdown_attempts'],1);self.assertTrue(r['cleanup_confirmed'])
    def test_owned_shutdown_once_even_after_guard_rejection(self):
        o,g,r,c=fixture087(real=True);o.sdk.account.trade_mode=2
        with self.assertRaises(Exception):g()
        self.assertTrue(o.close())
        with self.assertRaises(Exception):o.close()
        with self.assertRaises(Exception):g()
        self.assertEqual(o.sdk.shutdowns,1)
    def test_native_entry_and_actual_tables_remain_unavailable(self):
        with self.assertRaises(Exception):native_entry087()
        o,g,r,c=fixture087();r.model_only=False
        with self.assertRaises(Exception):BootReader087(r,o.reader,o.meter,g.boot.shell,g.boot.script,g.boot.bindings)
        o.close()
    def test_private_representations_and_public_results_redacted(self):
        o,g,r,c=fixture087();self.assertNotIn('private-model',repr(o.pins));o.close()
        row=model_guard087();self.assertTrue(row['modeled_completed']);self.assertFalse(row['runtime_authorized'])
        self.assertEqual((row['native_invocations'],row['sdk_connections'],row['market_reads'],row['orders']),(0,0,0,0))
    def test_combined_raw_episode_budgets_and_owned_cleanup(self):
        r=model_combined087();self.assertFalse(r['modeled_completed'],r)
        self.assertEqual((r['remaining_handles'],r['remaining_allocations'],r['shutdown_attempts']),(0,0,1))
        self.assertTrue(r['sdk_cleanup_confirmed']);self.assertFalse(r['runtime_authorized'])

if __name__=='__main__':unittest.main()
