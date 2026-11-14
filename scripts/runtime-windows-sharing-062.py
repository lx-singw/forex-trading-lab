"""One reserved local synthetic Win32 probe, never an MT5 runtime."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/windows-sharing-062.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']


def main():
    assert os.name=='nt' and sha(Path(sys.executable))==API['PYTHON_SHA']
    l=API['verify']();p=sealed(ROOT/'reports/windows-sharing-062-preparation-checks.json')
    assert p['checker_passed'] and p['tests_passed']==975 and p['ledger_sha256']==sha(API['LEDGER'])
    assert p['tests_sha256']==sha(ROOT/'reports/windows-sharing-062-tests.json')
    assert datetime.now(timezone.utc).date().isoformat()==l['declared_date']=='2026-10-07'
    plan=ROOT/'docs/WINDOWS-SHARING-062-RUNTIME-PLAN.md'
    write(ROOT/'reports/windows-sharing-062-runtime-started.json',dict(native_session_consumed=True,
        native_sessions=1,ledger_sha256=sha(API['LEDGER']),runtime_plan_sha256=sha(plan),
        preparation_checks_sha256=sha(ROOT/'reports/windows-sharing-062-preparation-checks.json'),
        phase=l['probe_identity'],declared_date=l['declared_date'],receipt_permissions=0,
        sdk_connections=0,quote_reads=0,orders_available=False))
    from forex_demo_lab.sharing_probe_062 import Meter, NativeFiles062, run_probe, DATA
    backend=None
    try:
        meter=Meter(lambda:(time.time_ns()//1000000,time.monotonic_ns()))
        backend=NativeFiles062(meter)
        result=run_probe(backend,meter)
    except Exception:
        # Constructor has no token/file opens; preserve the consumed session.
        result=dict(version='sharing_probe_062_v1',phase=l['probe_identity'],declared_date=l['declared_date'],
            passed=False,stop_reason='native_startup_failed_details_redacted',observations=[],read_counts=[],
            same_file_verified=False,security_path_verified=False,synthetic_sha256=API['hashlib'].sha256(DATA).hexdigest(),
            sdk_connections=0,mt5_invocations=0,receipt_permissions=0,quote_reads=0,history_reads=0,orders=0,
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False,native_mql_verified=False,
            blocking_preemption_verified=False,handle_open_attempts=0,write_attempts=0,read_attempts=0,
            directory_attempts=0,elapsed_us=0,measured_overrun=False,cleanup=dict(all_handles_closed=True,
                unconfirmed_handles=0,allocations_released=True,synthetic_directory_retained=False))
    result.update(native_sessions=1,ledger_sha256=sha(API['LEDGER']),runtime_plan_sha256=sha(plan),
                  preparation_checks_sha256=sha(ROOT/'reports/windows-sharing-062-preparation-checks.json'),
                  native_close_diagnostics=backend.closes if backend is not None else [],event_handles_created=0)
    write(ROOT/'reports/windows-sharing-062-runtime.json',result)
    print(json.dumps({k:result[k] for k in ('passed','stop_reason','handle_open_attempts',
        'write_attempts','read_attempts','read_counts','elapsed_us','cleanup')}))


if __name__=='__main__':main()
