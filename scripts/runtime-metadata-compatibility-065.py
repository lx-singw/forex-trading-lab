"""One reserved Windows-only compatibility probe. No SDK or MT5 interaction."""
from datetime import datetime,timezone
import ctypes as C
import json
import os
from pathlib import Path
import runpy
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/sharing-companion-065-r2.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']


def main():
    assert os.name=='nt' and sha(Path(sys.executable))==API['PYTHON_SHA']
    ledger=API['verify']();p=sealed(ROOT/'reports/sharing-companion-065-r2-preparation-checks.json')
    assert p['checker_passed'] and p['tests_passed']==1091 and p['ledger_sha256']==sha(API['LEDGER'])
    assert p['tests_sha256']==sha(ROOT/'reports/sharing-companion-065-r2-tests.json')
    assert datetime.now(timezone.utc).date().isoformat()==ledger['declared_date']=='2026-10-07'
    plan=ROOT/'docs/METADATA-COMPATIBILITY-065-RUNTIME-PLAN.md'
    write(ROOT/'reports/sharing-companion-065-r2-runtime-started.json',dict(native_session_consumed=True,
        native_sessions=1,phase=ledger['probe_identity'],ledger_sha256=sha(API['LEDGER']),
        runtime_plan_sha256=sha(plan),preparation_checks_sha256=sha(ROOT/'reports/sharing-companion-065-r2-preparation-checks.json'),
        sdk_connections=0,mt5_invocations=0,receipt_permissions=0,orders_available=False))
    from forex_demo_lab.sharing_companion_065 import Meter065,run_compatibility
    from forex_demo_lab.native_files_065 import NativeFiles065
    backend=None;meter=None
    try:
        kernel=C.WinDLL('kernel32',use_last_error=True);boot=kernel.GetTickCount64
        boot.argtypes=[];boot.restype=C.c_uint64
        meter=Meter065(lambda:(time.time_ns()//1000000,time.monotonic_ns(),int(boot())))
        raw=os.environ.get('TEMP');assert type(raw) is str and raw
        backend=NativeFiles065(meter,Path(raw),'compatibility')
        result=run_compatibility(backend,meter)
    except Exception:
        result=dict(passed=False,reason='native_startup_failed_details_redacted',counts=dict(meter.counts) if meter else {},
            cleanup=backend.finish() if backend else None,controls=[],native_mql_verified=False,native_publication_verified=False,
            sdk_connections=0,mt5_invocations=0,receipt_permissions=0,quote_reads=0,history_reads=0,orders=0,
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
    result.update(actual_windows_backend=True,native_sessions=1,ledger_sha256=sha(API['LEDGER']),
        runtime_plan_sha256=sha(plan),preparation_checks_sha256=sha(ROOT/'reports/sharing-companion-065-r2-preparation-checks.json'),
        native_close_diagnostics=backend.closes if backend else [])
    write(ROOT/'reports/sharing-companion-065-r2-runtime.json',result)
    print(json.dumps({k:result.get(k) for k in ('passed','reason','elapsed_us','controls','cleanup')}))


if __name__=='__main__':main()
