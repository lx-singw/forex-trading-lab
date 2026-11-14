"""Freeze/test/authorize/audit one source-bound compiler; no MT5 runtime."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/sharing-integration-072.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='sharing-build-073';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/sharing-integration-072-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-SHARING-073-BUILD-PLAN.md'
POLICY=ROOT/'docs/SHARING-BUILD-073-POLICY.md';PLAN=ROOT/'docs/NATIVE-SHARING-074-PLAN.md'
CHECKS=ROOT/f'reports/{PREFIX}-preparation-checks.json';AUTH=ROOT/f'reports/{PREFIX}-authorization.json'
NATIVE=ROOT/f'reports/{PREFIX}-native.json';STARTED=ROOT/f'reports/{PREFIX}-started.json'
EXPECTED,NEW=1331,38
PATTERNS=('scripts/*073.py','src/forex_demo_lab/*073.py','tests/*073.py','docs/*073*.md','docs/*074*.md')
ZERO=dict(sdk_connections=0,mt5_runtime_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,actual_mt5_repair_verified=False,
    root_cause_proven=False,native_adapter_ready=False)


def external_name(path):
    return runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))['external_name'](path)


def freeze():
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-08'
    assert sha(PRIOR)=='29c154b5d78ca0acaa422b26884e82298d00d2186dec6a7d5155e8125ff41b50'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/sharing-integration-072-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['tests_passed']==1293 and r['bindings_verified']==2273 and r['archive_members_verified']==2103
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='d6d19ee11ed69d5857637aa9b6cacc7652d40f5ebad28d3994ac0507424aaf0f'
    assert r['next_plan_executed'] is False and r['compiled'] is False
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2103;API['verify']();API['API']['prior_evidence']()
    old=sealed(ROOT/'reports/sharing-companion-065-r2-build.json')
    assert old['compiled'] and old['compiler_exit_code']==1 and old['errors']==old['warnings']==0
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/sharing-integration-072-completion-review.json',ROOT/'reports/sharing-integration-072-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    assert all(not p.exists() for p in (AUTH,NATIVE,STARTED))
    settings=sealed(ROOT/'reports/native-compiler-042-ledger.json')
    py='/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python/Scripts/python.exe'
    paths=dict(terminal_path='/mnt/c/Program Files/MetaTrader 5/terminal64.exe',editor_path=settings['editor_path'],
        shell_path=settings['powershell_path'],python_path=py)
    pins={k.replace('_path','_sha256'):b[v] for k,v in paths.items()}
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        policy_sha256=sha(POLICY),future_plan_sha256=sha(PLAN),source_contract=API['contract'](),
        prior_bindings_verified=2273,prior_archive_members_verified=2103,tests_retained=1293,
        expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,maximum_compiler_invocations=1,
        declared_date='2026-10-08',build_phase='73000000000000000000000000000001',execution_policy='RemoteSigned',
        build_root=settings['build_root'],**paths,**pins,**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['prior_source_sha256']==sha(PRIOR) and l['prior_plan_sha256']==sha(PRIOR_PLAN)
    assert l['policy_sha256']==sha(POLICY) and l['future_plan_sha256']==sha(PLAN)
    assert l['source_contract']==API['contract']()
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),native_compiler_invocations=0,**ZERO,**FALSE))
    start=time.monotonic();r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in r.failures+r.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),native_compiler_invocations=0,**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    for k,v in {**ZERO,**FALSE,'native_compiler_invocations':0}.items():assert t[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    write(CHECKS,dict(checker_passed=True,ledger_sha256=sha(LEDGER),tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),
        tests_passed=EXPECTED,old_exit_zero_contract_retained=True,actual_exit_one_explicit=True,
        native_compiler_invocations=0,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


def authorization_value(l):
    return dict(version='sharing_build_authorization_073_v1',ledger_sha256=sha(LEDGER),policy_sha256=sha(POLICY),
        preparation_checks_sha256=sha(CHECKS),source_contract_sha256=sha(ROOT/'reports/sharing-integration-072-source-contract.json'),
        phase=l['build_phase'],date=l['declared_date'],maximum_compiler_invocations=1,maximum_runtime_invocations=0,
        maximum_sdk_connections=0,maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0,orders_available=False)


def authorize():
    l=verify();c=sealed(CHECKS);assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert datetime.now(timezone.utc).date().isoformat()==l['declared_date']
    assert all(not p.exists() for p in (AUTH,NATIVE,STARTED));write(AUTH,authorization_value(l))
    print(json.dumps(dict(compilation_authorized=True,maximum_compiler_invocations=1,runtime_authorized=False)))


def final_check():
    l=verify();r=sealed(NATIVE);s=sealed(STARTED)
    assert sealed(AUTH)==authorization_value(l)
    assert s['build_reservation_consumed'] and s['ledger_sha256']==r['ledger_sha256']==sha(LEDGER)
    assert s['authorization_sha256']==r['authorization_sha256']==sha(AUTH) and r['started_sha256']==sha(STARTED)
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.sharing_build_073 import LIMITS,metadata073,build_record073
    assert set(r['counts'])==set(LIMITS) and all(type(v) is int and 0<=v<=LIMITS[k] for k,v in r['counts'].items())
    assert type(r['completed']) is bool and r['compiled'] is r['completed']
    assert all(r[k]==v for k,v in {**ZERO,'orders_available':False,'native_mql_verified':False,
        'native_publication_verified':False,'fresh_performance_eligible':False,'annual_eligible':False}.items())
    for n,h in r['output_bindings'].items():assert sha(bound(n))==h,n
    if r['completed']:
        assert r['counts']['compiler_invocations']==1 and r['compiler_process_completed']
        assert r['compiler_exit_code']==1 and r['stop_reason'] is r['stopped_stage'] is None
        assert r['owned_compiler_absent_after'] and len(r['stage_trace'])==8 and all(e['completed'] for e in r['stage_trace'])
        before=metadata073(r['metadata_before'],l['execution_policy']);assert metadata073(r['metadata_after'],l['execution_policy'])==before
        names={n.rsplit('/',1)[-1]:n for n in r['output_bindings']}
        assert set(names)=={Path(n).name for n in l['source_contract']['input_bindings']}|{'compile.log','ForexDemoSharing072.ex5'}
        artifact=bound(names['ForexDemoSharing072.ex5']);log=bound(names['compile.log']).read_text(encoding='utf-16')
        matched=build_record073(l['source_contract'],r['compiler_exit_code'],log,
            dict(sha256=sha(artifact),size=artifact.stat().st_size,raw=None),l['editor_sha256'],l['terminal_sha256'])
        assert matched==r['build_record'] and r['clean_log_summary']==dict(errors=0,warnings=0)
    else:assert r['stop_reason'] is not None and r['stopped_stage'] is not None
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),native_sha256=sha(NATIVE),started_sha256=sha(STARTED),
        compiled=r['completed'],compiler_invocations=r['counts']['compiler_invocations'],
        compiler_exit_code=r['compiler_exit_code'],tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,compiled=r['completed'],compiler_exit_code=r['compiler_exit_code'])))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');r=sealed(NATIVE)
    assert c['checker_passed'] and c['native_sha256']==sha(NATIVE) and c['ledger_sha256']==sha(LEDGER)
    text=(f'# Source-bound build073 results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        f'Native build completed:{r["completed"]}; compiler invocations:{r["counts"]["compiler_invocations"]}; '
        f'actual exit:{r["compiler_exit_code"]}; clean summary:{r["clean_log_summary"]}; stop:{r["stop_reason"]}/stage:{r["stopped_stage"]}. '
        'One consumed build marker and isolated owned output folder retained; exact source/include/compiler/terminal '
        'and output hashes audited. No retry/reset/refund.\n\n'
        'Separate073 schema retains observed native exit1; frozen072 exit0 assumption/checker and source remain unchanged. '
        'No fabricated normalized exit. Actual signed6244 metadata, full uncached image/source checks, bounded '
        'copy/hash/log/artifact/clock/process budgets and no-editor/policy checks guard this one attempt. '
        f'Owned compiler absent afterward:{r["owned_compiler_absent_after"]}; execution policy not changed.\n\n'
        'Zero MT5 script/SDK/deployment/terminal log-content/market/orders/receipt grants. Compiled output, if validated, '
        'is retained only in the new build folder and has not run on MT5. Native sharing/publication/ACK and '
        'profit remain unestablished; old070 exact failure cause unknown. Next NATIVE-SHARING-074-PLAN.md is '
        'outcome-driven tested runtime preparation/synchronization before any later policy, not executed. '
        'Oct8 expiry requires fresh source/phase instead of editing frozen072/073. Keep033/035 failures, '
        'clock/cost/coverage/flags, consumed2025/reserved Nov–Dec2026/provider exclusions; eligibility/orders false.\n')
    with (ROOT/'docs/SHARING-BUILD-073-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-08: source-bound build073 sealed; read SHARING-BUILD-073-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass; native completed:{r["completed"]}, compiler calls:{r["counts"]["compiler_invocations"]}, '
        f'exit:{r["compiler_exit_code"]}, summary:{r["clean_log_summary"]}, stop:{r["stop_reason"]}/{r["stopped_stage"]}. '
        'Fresh072 source unchanged;073 exact actual-exit1 schema fixes frozen072 exit0 assumption without normalization. '
        'Owned build marker/folder/output hashes retained; no retry/refund. Zero MT5 scripts/SDK/deploy/terminal log/market/orders/grants. '
        'Native sharing/publication/ACK/profit unestablished;070 cause unknown. Next074 outcome-driven runtime '
        'preparation/synchronization/tests, not executed; expiredOct8 source requires fresh declaration. '
        'Old failures/spent allowances/033/035/reserved gates retained; eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    b.update(r['output_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,compiled=r['completed'],compiler_invocations=r['counts']['compiler_invocations'],
        compiler_exit_code=r['compiler_exit_code'],future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final),compiled=r['completed'])))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checker_passed'] and c['native_sha256']==sha(NATIVE)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN) and not r['future_plan_executed']
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,compiled=r['compiled'],
        compiler_invocations=r['compiler_invocations'],compiler_exit_code=r['compiler_exit_code'],
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,compiled=r['compiled'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','authorize','final-check','seal','review','verify'))
    dict(freeze=freeze,test=test,check=check,authorize=authorize,seal=seal,review=review,
        **{'final-check':final_check},verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
