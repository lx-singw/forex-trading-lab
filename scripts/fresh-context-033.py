"""One frozen complete source-hour audit; no retries or performance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/fresh-data-031.py'))
sha,write,sealed,load=API['sha'],API['write'],API['sealed'],API['load']
from forex_demo_lab.fresh_context_033 import START,END,VERSION,capture,reserve_output,no_call

PRIOR=ROOT/'reports/fresh-ticks-032-final-source.json'
LEDGER=ROOT/'reports/fresh-context-033-ledger.json'
OUTPUT=ROOT/'data/fresh-context-033'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='e694fa38e27b3cd29efd87f70782c121bdd4fa2f5022bcb91e5fec7bf8c27e7b'
    previous=sealed(PRIOR)
    bindings,changes={},{}
    for group,values in previous.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for name,expected in values.items():
            assert name not in bindings
            current=sha(ROOT/name)
            if current!=expected:
                assert allow_handoff and group=='source_bindings' and name in API['API']['HANDOFF'],name
                changes[name]=dict(previous_sha256=expected,current_sha256=current)
            bindings[name]=expected
    external=previous['archive_external_bindings']
    assert len(bindings)==963 and len(external)==41
    assert all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==922
        assert set(z.namelist())==set(bindings)-set(external)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==bindings[name],name
    return dict(bindings_verified=963,archived_members_verified=922,external_bindings_verified=41,allowed_handoff_changes=changes)


def freeze():
    checked=prior_verify()
    tests=sealed(ROOT/'reports/fresh-context-033-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==441
    previous=runpy.run_path(str(ROOT/'scripts/fresh-ticks-032.py'))
    old=previous['verify']()
    checks=sealed(ROOT/'reports/fresh-ticks-032-checks.json')
    assert checks['diagnostic_passed'] and checks['rows_checked']==196
    bindings={n:h for n,h in old['bindings'].items() if n.startswith('/mnt/')}
    for pattern in ('src/**/*.py','scripts/*033*.py','tests/*033*.py','docs/*033*.md',
                    'reports/fresh-context-033-tests*','reports/fresh-ticks-032-ledger.*',
                    'reports/fresh-ticks-032-checks.*','reports/fresh-ticks-032-final-source.*',
                    'data/fresh-ticks-032/*'):
        for path in ROOT.glob(pattern):bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    assert not OUTPUT.exists()
    assert not (ROOT/'reports/fresh-context-033-checks.json').exists()
    write(LEDGER,dict(kind='frozen_source_hour_context_033',version=VERSION,date='2026-10-06',bindings=bindings,
        prior_snapshot_verification=checked,terminal=old['terminal'],start_raw_ms=START,end_raw_ms=END,
        bounds='inclusive_ticks_half_open_hour',maximum_requests=3,maximum_ticks=100000,maximum_bars=10,
        maximum_evidence_bytes=32*1024*1024,soft_timeout_seconds=60,total_history_soft_timeout_seconds=120,
        witness_rows=196,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),maximum_requests=3)))


def verify():
    ledger=sealed(LEDGER)
    for name,expected in ledger['bindings'].items():
        assert sha(API['bound_path'](name))==expected,name
    return ledger


def not_requested(reason):
    return no_call(reason)


def run():
    ledger=verify()
    reserve_output(OUTPUT)  # Before initialization or any native API operation.
    mt5=None
    try:
        if os.name!='nt':
            outcome=not_requested('windows_runtime_required')
        else:
            status=subprocess.run(['powershell.exe','-NoProfile','-Command',
                'ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })'],
                capture_output=True,text=True,check=True,timeout=15)
            paths=json.loads(status.stdout)
            wanted=os.path.normcase(str(Path(ledger['terminal']).resolve()))
            if wanted not in [os.path.normcase(p) for p in paths if p]:
                outcome=not_requested('terminal_not_running')
            else:
                from forex_demo_lab.fresh_data_031 import receipt
                receipt(time.time_ns()//1000000)
                import MetaTrader5 as mt5
                if not mt5.initialize(str(Path(ledger['terminal'])),timeout=15000):
                    outcome=not_requested('read_only_connection_failed_details_redacted')
                else:
                    outcome=capture(mt5,OUTPUT,lambda:(time.time_ns()//1000000,time.monotonic_ns()),prepared=True)
    except Exception:
        # The collector preserves its own failure. Never replace it or retry.
        if (OUTPUT/'capture.json').exists():raise
        outcome=not_requested('preflight_failure_details_redacted')
    finally:
        if mt5 is not None:mt5.shutdown()
    if not (OUTPUT/'capture.json').exists():
        with (OUTPUT/'capture.json').open('x') as f:
            json.dump(outcome,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    with (OUTPUT/'capture.sha256').open('x') as f:f.write(sha(OUTPUT/'capture.json')+'\n')
    print(json.dumps({k:outcome[k] for k in ('status','stop_reason','requests','history_elapsed_ns','orders_available')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','verify','run'))
    {'freeze':freeze,'verify':verify,'run':run}[parser.parse_args().action]()
