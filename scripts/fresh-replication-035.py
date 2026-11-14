"""One frozen four-source-hour replication; no retries or performance."""
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
from forex_demo_lab.fresh_replication_035 import START,END,VERSION,capture,reserve_output,no_call

PRIOR=ROOT/'reports/fresh-flags-034-final-source.json'
LEDGER=ROOT/'reports/fresh-replication-035-ledger.json'
OUTPUT=ROOT/'data/fresh-replication-035'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='ed8df2660c2fb308174f5ccfb5d03353c79cf53a093049b004ae85c243b7adeb'
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
    assert len(bindings)==1014 and len(external)==43
    assert all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==971
        assert set(z.namelist())==set(bindings)-set(external)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==bindings[name],name
    return dict(bindings_verified=1014,archived_members_verified=971,external_bindings_verified=43,allowed_handoff_changes=changes)


def freeze():
    checked=prior_verify()
    tests=sealed(ROOT/'reports/fresh-replication-035-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==482 and tests['new_tests']==25
    previous=runpy.run_path(str(ROOT/'scripts/fresh-context-033.py'))
    old=previous['verify']()
    checks=sealed(ROOT/'reports/fresh-flags-034-checks.json')
    review=sealed(ROOT/'reports/fresh-flags-034-review.json')
    assert checks['checker_passed'] and review['passed'] and review['prior_033_diagnostic_passed'] is False
    qualification=ROOT/'reports/fresh-replication-035-qualification.json'
    write(qualification,dict(kind='pre_acquisition_qualification_review_035',
        previous_review_sha256=sha(ROOT/'reports/fresh-flags-034-review.json'),
        historical_source_clock='uncertified',upstream_completeness='unresolved',historical_executable_costs='uncertified',
        relative_feed_collection_permitted=True,qualified_dataset_publication=False,normalization_permitted=False,
        performance_testing_permitted=False,fresh_performance_eligible=False,annual_eligible=False,
        prior_033_diagnostic_passed=False,market_requests=0,orders_available=False))
    bindings={n:h for n,h in old['bindings'].items() if n.startswith('/mnt/')}
    for pattern in ('src/**/*.py','scripts/*035*.py','scripts/check-fresh-context-033.py',
                    'tests/*035*.py','docs/*035*.md','reports/fresh-replication-035-tests*',
                    'reports/fresh-replication-035-qualification*','reports/fresh-flags-034-ledger.*',
                    'reports/fresh-flags-034-audit.*','reports/fresh-flags-034-checks.*',
                    'reports/fresh-flags-034-review.*','reports/fresh-flags-034-final-source.*',
                    'data/fresh-ticks-032/*','data/fresh-context-033/*'):
        for path in ROOT.glob(pattern):bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    assert not OUTPUT.exists() and not (ROOT/'reports/fresh-replication-035-checks.json').exists()
    write(LEDGER,dict(kind='frozen_four_source_hour_replication_035',version=VERSION,date='2026-10-06',bindings=bindings,
        prior_snapshot_verification=checked,qualification_review_sha256=sha(qualification),terminal=old['terminal'],
        start_raw_ms=START,end_raw_ms=END,bounds='inclusive_ticks_four_half_open_hours',maximum_requests=3,
        maximum_ticks=100000,maximum_bars=10,maximum_evidence_bytes=32*1024*1024,
        soft_timeout_seconds=60,total_history_soft_timeout_seconds=120,witness_rows=13769,
        fixed_definitions=['all','bid_flag','ask_flag','both_flags','neither_flag',
                          'bid_value_change_with_first','ask_value_change_with_first'],
        strategy_replays=0,prior_033_diagnostic_passed=False,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),maximum_requests=3,performance_testing_permitted=False)))


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
