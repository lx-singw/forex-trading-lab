"""Frozen offline design/tests and evidence; no MT5/IPC/quote runtime actions."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import sys
import time
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/clock-session-044.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed'];bound_path=API['bound_path']
HANDOFF=API['HANDOFF']
PRIOR=ROOT/'reports/clock-log-audit-045-final-source.json'
LEDGER=ROOT/'reports/capture-budget-046-ledger.json'
TESTS=ROOT/'reports/capture-budget-046-regression.json'
PATTERNS=('docs/*046*.md','docs/CAPTURE-TRANSPORT-047-PLAN.md','scripts/*046.py',
    'src/forex_demo_lab/*046.py','tests/*046.py','mt5/Scripts/*046.mqh','mt5/Tests/*046.cpp')

def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='ca66bddacebf572c112b98cfa03322ebdea9b6002dcd70a320fbf00f83504e2a'
    prior=sealed(PRIOR);bindings={n:h for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings' for n,h in v.items()}
    for n,h in bindings.items():
        actual=sha(bound_path(n))
        assert actual==h or allow_handoff and n in HANDOFF,n
    assert len(bindings)==1378 and sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    internal={n:h for n,h in bindings.items() if n not in prior['archive_external_bindings']}
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1305 and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    assert prior['acquisition_budget_compliant'] is False and prior['recorded_native_quote_reads']==6
    assert not prior['original_044_runtime_completed'] and not prior['orders_available']
    return prior,bindings

def freeze():
    prior,bindings=prior_verify()
    inputs={n:h for n,h in bindings.items() if n not in HANDOFF}
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for binary in (Path(sys.executable).resolve(),Path(shutil.which('g++')).resolve()):inputs[str(binary)]=sha(binary)
    required={'scripts/capture-budget-046.py','src/forex_demo_lab/capture_budget_046.py','tests/test_capture_budget_046.py',
        'mt5/Scripts/CapturePermit046.mqh','mt5/Tests/CapturePermit046.cpp','docs/CLOCK-UI-SAFETY-046-PROTOCOL.md',
        'docs/CLOCK-UI-SAFETY-046-RESEARCH.md','docs/CAPTURE-TRANSPORT-047-PLAN.md'}
    assert required<=set(inputs) and not LEDGER.exists() and not TESTS.exists()
    write(LEDGER,dict(bindings=inputs,prior_bindings_verified=len(bindings),prior_archive_members_verified=1305,
        prior_external_bindings_verified=73,new_tests=32,expected_tests=654,shared_mql_receipt_checks=18,
        differential_receipt_cases=500,research_queries=1,research_opens=11,research_finds=3,
        native_mt5_compilations=0,native_sdk_connections=0,pipe_servers=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(frozen=True,input_bindings=len(inputs),prior_bindings_verified=len(bindings))))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound_path(n))==h,n
    return ledger

def regression():
    ledger=verify();start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==ledger['expected_tests'] and not result.skipped
    write(TESTS,dict(passed=passed,tests_run=result.testsRun,
        tests_passed=result.testsRun-len(result.errors)-len(result.failures)-len(result.skipped),
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),new_tests=32,
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),shared_mql_receipt_checks=18,
        differential_receipt_cases=500,native_mt5_compilations=0,native_sdk_connections=0,pipe_servers=0,
        new_quote_reads=0,orders_available=False))
    if not passed:raise SystemExit(1)

def finalize():
    ledger=verify();tests=sealed(TESTS)
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==654 and tests['ledger_sha256']==sha(LEDGER)
    prior,bindings=prior_verify()
    assert (ROOT/'docs/CLOCK-UI-SAFETY-046-RESULTS.md').is_file()
    text=('Latest — 2026-10-06: capture-budget046 offline design/core sealed; read CLOCK-UI-SAFETY-046-RESULTS.md. '
        '654 tests (32 new),18 exact shared MQL receipt checks/500 differential boundaries pass. '
        'Six repeated and32 concurrent requests issue at most one permission; consume before guards/journal/response, '
        'no refund on failure/lost response, exclusive reservation rejects phase restart. '
        'One-query/11-open/three-find primary-source review; named-pipe native integration unimplemented. '
        'Zero native SDK/quote/history/strategy/orders/MT5 builds/deployments/settings/pipe actions. '
        'Old045 six native captures and044 timeout/incomplete preserved; do not rerun042. '
        'Next CAPTURE-TRANSPORT-047-PLAN.md no-market transport fixtures, not executed. '
        'Clock/coverage/cost/flags/033/035 failures, consumed2025/reservedNov–Dec2026/provider stops retained; '
        'fresh/annual eligibility and orders false. Earlier entries are historical.\n\n')
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for n in HANDOFF:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+text+old[i:]);groups['source_bindings'][n]=sha(p)
    prior_verify(allow_handoff=True)
    for pattern in PATTERNS:
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/capture-budget-046-*.json','reports/capture-budget-046-*.sha256'):
        for p in ROOT.glob(pattern):groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    existing={n:h for v in groups.values() for n,h in v.items()};groups['capture_budget_046_input_bindings']={}
    for n,h in ledger['bindings'].items():
        if n in existing:assert existing[n]==h,n
        else:groups['capture_budget_046_input_bindings'][n]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(bound_path(n))==h,n
    final=ROOT/'reports/capture-budget-046-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),tests_passed=654,new_tests=32,
        native_capture_budget_verified=False,native_integration_implemented=False,old_045_native_quote_reads=6,
        old_044_runtime_completed=False,new_quote_reads=0,orders_available=False,fresh_performance_eligible=False,
        annual_eligible=False,next_plan='docs/CAPTURE-TRANSPORT-047-PLAN.md',next_plan_executed=False))
    assert sealed(final)['archive_sha256']==sha(archive)
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(final),tests_passed=654)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','test','finalize'));a=parser.parse_args()
    {'freeze':freeze,'test':regression,'finalize':finalize}[a.action]()
