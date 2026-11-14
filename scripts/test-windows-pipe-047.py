"""Bounded Windows IPC fixtures, synthetic guards, no SDK or price capability."""
from concurrent.futures import ThreadPoolExecutor
import os
import json
import traceback
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
from threading import Thread,Event
import uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/capture-transport-047.py'))
from forex_demo_lab.capture_budget_047 import Policy,start_authority,PermitRejected
from forex_demo_lab.capture_wire_047 import *
from forex_demo_lab.windows_pipe_047 import WindowsPipe,PipeRejected,_PENDING
_CASES=[]

def run():
    API['verify']();API['write'](ROOT/'reports/capture-transport-047-native-r3-started.json',dict(ledger_sha256=API['sha'](API['LEDGER']),
        suite_consumed=True,maximum_native_suites=1,sdk_connections=0,quote_reads=0,orders_available=False))
    win=WindowsPipe();owner=win.identity(os.getpid());outcomes=[]
    with TemporaryDirectory(prefix='fxdl-ipc047-') as directory:
        def exchange(case,request_mode='valid',reply_mode='valid',wrong_client=False,wrong_server=False,clients=1):
            _CASES.append(dict(case=case,completed=False))
            phase=uuid.uuid4().hex;p=Policy(phase,'47'*32);name='\\\\.\\pipe\\ForexDemoFixture047-'+phase
            journal=[];consumed=Event();release=Event()
            def save(r):journal.append(r);consumed.set();return True
            authority=start_authority(Path(directory)/(phase+'.json'),p,win.clock,lambda:True,save)
            server=win.server(name,owner);status=[];client_results=[]
            expected=(owner[0]+1,*owner[1:]) if wrong_client else owner
            def serve():
                try:
                    win.io(server,'connect');win.peer(server,'client',expected)
                    raw=win.io(server,'read',size=57)
                    try:phase,digest=decode_request(raw,p)
                    except PermitRejected:
                        authority.issue('invalid','invalid');raise
                    reply=encode_response(authority.issue(phase,digest))
                    if reply_mode=='lost':
                        if not release.wait(2):raise PipeRejected('fixture_barrier_timeout')
                    if reply_mode=='short':reply=reply[:-1]
                    if reply_mode=='long':reply=reply+b'xx'
                    if reply_mode=='magic':reply=b'X'+reply[1:]
                    win.io(server,'write',data=reply);status.append('reply_written')
                except (PermitRejected,PipeRejected):status.append('rejected')
                except Exception:status.append('fixture_failure')
                finally:authority.close();win.close(server)
            thread=Thread(target=serve,daemon=True);thread.start()
            def client(_):
                handle=None
                try:
                    handle=win.client(name)
                    win.peer(handle,'server',(owner[0]+1,*owner[1:]) if wrong_server else owner)
                    raw=encode_request(p)
                    if request_mode=='short':raw=raw[:-1]
                    if request_mode=='long':raw=raw+b'xx'
                    if request_mode=='magic':raw=b'X'+raw[1:]
                    win.io(handle,'write',data=raw)
                    if reply_mode=='lost':
                        if not consumed.wait(2):raise PipeRejected('fixture_barrier_timeout')
                        win.close(handle);handle=None;release.set();return False
                    response=win.io(handle,'read',size=85)
                    utc,_,boot=win.clock();decode_response(response,p,utc,boot);return True
                except (PermitRejected,PipeRejected):return False
                finally:
                    if handle is not None:win.close(handle)
            with ThreadPoolExecutor(max_workers=clients) as pool:client_results=list(pool.map(client,range(clients)))
            thread.join(5)
            if thread.is_alive():raise PipeRejected('fixture_thread_deadline')
            if 'fixture_failure' in status:raise PipeRejected('fixture_internal_failure')
            expected_grants=1 if case in ('valid','parallel') else 0
            assert sum(client_results)==expected_grants
            assert authority.summary()['permissions_consumed']<=1 and len(journal)<=1
            try:start_authority(Path(directory)/(p.phase+'.json'),p,win.clock,lambda:True,save)
            except PermitRejected:restart_blocked=True
            else:restart_blocked=False
            assert restart_blocked
            try:authority.issue(p.phase,p.digest)
            except PermitRejected:repeat_blocked=True
            else:repeat_blocked=False
            assert repeat_blocked
            outcomes.append(dict(case=case,passed=True,valid_responses=sum(client_results),
                permission_consumed=authority.summary()['permissions_consumed'],restart_blocked=True,repeat_blocked=True))
            _CASES[-1]['completed']=True
        for case,options in (
            ('valid',{}),('parallel',dict(clients=8)),('short_request',dict(request_mode='short')),
            ('long_request',dict(request_mode='long')),('wrong_request',dict(request_mode='magic')),
            ('short_reply',dict(reply_mode='short')),('long_reply',dict(reply_mode='long')),
            ('wrong_reply',dict(reply_mode='magic')),('wrong_client',dict(wrong_client=True)),
            ('wrong_server',dict(wrong_server=True)),('lost_reply',dict(reply_mode='lost'))):exchange(case,**options)
        name='\\\\.\\pipe\\ForexDemoFixture047-'+uuid.uuid4().hex;h=win.server(name,owner)
        try:
            try:second=win.server(name,owner)
            except PipeRejected:collision=True
            else:win.close(second);collision=False
            assert collision
            try:win.io(h,'connect',timeout_ms=30)
            except PipeRejected as e:assert str(e)=='io_deadline_exceeded'
            else:raise AssertionError('missing_connect_timeout')
        finally:win.close(h)
        outcomes.append(dict(case='collision_and_connect_timeout',passed=True))
        try:win.client(name)
        except PipeRejected:missing=True
        else:missing=False
        assert missing
        outcomes.append(dict(case='missing_or_dead_server',passed=True))
        name='\\\\.\\pipe\\ForexDemoFixture047-'+uuid.uuid4().hex;h=win.server(name,owner);result=[]
        def read_timeout():
            try:
                win.io(h,'connect');win.peer(h,'client',owner);win.io(h,'read',size=57,timeout_ms=30)
            except PipeRejected as e:result.append(str(e)=='io_deadline_exceeded')
            finally:win.close(h)
        t=Thread(target=read_timeout,daemon=True);t.start();client=win.client(name)
        try:t.join(3);assert not t.is_alive() and result==[True]
        finally:win.close(client)
        outcomes.append(dict(case='read_timeout_cancellation',passed=True))
        assert not _PENDING
    API['write'](ROOT/'reports/capture-transport-047-native-r3.json',dict(passed=True,cases=outcomes,cases_passed=len(outcomes),
        ledger_sha256=API['sha'](API['LEDGER']),synthetic_guard_only=True,actual_mt5_peer_tested=False,
        both_windows_peer_identities_checked=True,explicit_logon_dacl=True,remote_clients_rejected=True,
        first_instance_only=True,cancellation_drained=True,maximum_io_ms=2000,
        sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(native_cases_passed=len(outcomes),sdk_connections=0,quote_reads=0)))

if __name__=='__main__':
    try:run()
    except Exception as e:
        p=ROOT/'reports/capture-transport-047-native-r3.json'
        if not p.exists():API['write'](p,dict(passed=False,stop_reason='native_fixture_failed_details_redacted',
            error_type=type(e).__name__,errno=getattr(e,'errno',None),winerror=getattr(e,'winerror',None),
            source_frames=[dict(file=Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(e.__traceback__)],
            case_progress=_CASES,
            sdk_connections=0,quote_reads=0,orders_available=False))
        raise SystemExit('native_fixture_failed_details_redacted')
