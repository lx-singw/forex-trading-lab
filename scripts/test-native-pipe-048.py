"""One reserved bounded Windows suite. No SDK, MT5 or market functions."""
import os
from pathlib import Path
import runpy
import sys
from threading import Thread, Event
import time
import uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
from forex_demo_lab.native_pipe_048 import ManualWindowsPipe048
from forex_demo_lab.windows_pipe_047 import PipeRejected, _PENDING

def run():
    API['verify']();API['write'](ROOT/'reports/native-pipe-048-native-tests-started.json',dict(suite_consumed=True,
        ledger_sha256=API['sha'](API['LEDGER']),sdk_connections=0,quote_reads=0,orders_available=False))
    passed=False;cases=[];reason=None
    try:
        win=ManualWindowsPipe048();owner=win.identity(os.getpid())
        for case in ('delayed_connect','connect_timeout','connect_cancel'):
            name='\\\\.\\pipe\\ForexDemoFixture047-'+uuid.uuid4().hex;h=win.server(name,owner)
            stop=Event();outcome=[];started=time.monotonic();connected_call=Event()
            original_connect=win.connect
            def observed_connect(*args):
                result=original_connect(*args);connected_call.set();return result
            win.connect=observed_connect
            def serve():
                try:win.connect_until(h,started+(5 if case=='delayed_connect' else .1 if case=='connect_timeout' else 5),stop);outcome.append('connected')
                except PipeRejected as e:outcome.append(str(e))
                finally:win.close(h)
            t=Thread(target=serve);t.start();client=None
            try:
                if case=='delayed_connect':time.sleep(2.1);client=win.client(name)
                if case=='connect_cancel':
                    assert connected_call.wait(1);stop.set()
                t.join(6);assert not t.is_alive()
                if case=='delayed_connect':assert outcome==['connected'] and time.monotonic()-started>2
                elif case=='connect_cancel':assert outcome in (['manual_connect_cancelled_or_expired'],['manual_connect_deadline_rejected'])
                else:assert outcome==['manual_connect_cancelled_or_expired']
            finally:
                if client is not None:win.close(client)
                win.connect=original_connect
            assert not _PENDING;cases.append(dict(case=case,passed=True))
        try:win.connect_until(0,time.monotonic()-1,Event())
        except PipeRejected:pass
        else:raise AssertionError()
        cases.append(dict(case='expired_before_connect',passed=True))
        for kind in ('read','write'):
            try:win.io(0,kind,timeout_ms=2001)
            except PipeRejected as e:assert str(e)=='io_deadline_rejected'
            else:raise AssertionError()
        cases.append(dict(case='io_still_two_seconds',passed=True))
        passed=True
    except Exception:reason='native_lifetime_fixture_failed_details_redacted'
    API['write'](ROOT/'reports/native-pipe-048-native-tests.json',dict(passed=passed,cases=cases,
        stop_reason=reason,ledger_sha256=API['sha'](API['LEDGER']),cancellation_drained=not bool(_PENDING),
        actual_mt5_peer_tested=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(dict(passed=passed,cases=len(cases)))
    if not passed:raise SystemExit(1)

if __name__=='__main__':run()
