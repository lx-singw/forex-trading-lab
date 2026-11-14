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
API=runpy.run_path(str(ROOT/'scripts/sharing-build-074.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='sharing-build-075';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/sharing-build-074-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-SHARING-075-PLAN.md'
POLICY=ROOT/'docs/SHARING-BUILD-075-POLICY.md';PLAN=ROOT/'docs/NATIVE-SHARING-076-PLAN.md'
CHECKS=ROOT/f'reports/{PREFIX}-preparation-checks.json';AUTH=ROOT/f'reports/{PREFIX}-authorization.json'
NATIVE=ROOT/f'reports/{PREFIX}-native.json';STARTED=ROOT/f'reports/{PREFIX}-started.json'
EXPECTED,NEW=1360,13
PATTERNS=('scripts/*075.py','src/forex_demo_lab/*075.py','tests/*075.py','docs/*075*.md','docs/*076*.md','reports/sharing-build-075-policy-observation.json','reports/sharing-build-075-policy-observation.sha256')
ZERO=dict(sdk_connections=0,mt5_runtime_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,actual_mt5_repair_verified=False,
    root_cause_proven=False,native_adapter_ready=False)


def external_name(path):
    return runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))['external_name'](path)


def freeze():
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-08'
    assert sha(PRIOR)=='c28e6db29c396456bcc50e815ae05f444e9a0533596481080ebbc420b86b19c2'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/sharing-build-074-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['tests_passed']==1347 and r['bindings_verified']==2335 and r['archive_members_verified']==2161
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='0da925bb93fea94af177de67fcb5a14386d6df76fcc64bf7a667ef17caf7cb49'
    assert r['next_plan_executed'] is False and r['compiled'] is False
    failed=sealed(ROOT/'reports/sharing-build-074-native.json')
    assert not failed['completed'] and failed['counts']['compiler_invocations']==0
    assert (failed['stop_reason'],failed['stopped_stage'])==('metadata_rejected','metadata_before')
    observation=sealed(ROOT/'reports/sharing-build-075-policy-observation.json')
    assert observation['read_only'] and observation['returncode']==0 and not observation['stderr_present']
    assert observation['metadata']==dict(valid_signatures=True,policy='Restricted',editor_processes=0,terminal_build=6244,editor_build=6244)
    assert observation['source_metadata_function_sha256']==sha(ROOT/'scripts/runtime-sharing-build-074.py')
    assert observation['pinned_shell_sha256']==sealed(ROOT/'reports/sharing-build-074-ledger.json')['shell_sha256']
    assert observation['compiler_invocations']==observation['execution_policy_changes']==observation['sdk_connections']==0
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2161;API['verify']();API['API']['API']['API']['prior_evidence']()
    old=sealed(ROOT/'reports/sharing-companion-065-r2-build.json')
    assert old['compiled'] and old['compiler_exit_code']==1 and old['errors']==old['warnings']==0
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/sharing-build-074-completion-review.json',ROOT/'reports/sharing-build-074-completion-review.sha256'):
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
        policy_sha256=sha(POLICY),future_plan_sha256=sha(PLAN),source_contract=API['API']['API']['contract'](),
        prior_bindings_verified=2335,prior_archive_members_verified=2161,tests_retained=1347,
        expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,maximum_compiler_invocations=1,
        declared_date='2026-10-08',build_phase='75000000000000000000000000000001',execution_policy='Restricted',
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
    assert l['source_contract']==API['API']['API']['contract']()
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
    return dict(version='sharing_build_authorization_075_v1',ledger_sha256=sha(LEDGER),policy_sha256=sha(POLICY),
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
    from forex_demo_lab.sharing_build_075 import LIMITS,metadata073,build_record075
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
        matched=build_record075(l['source_contract'],r['compiler_exit_code'],log,
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
    text=(f'# Compiler-shell-bound build075 results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        f'Build completed:{r["completed"]}; compiler invocations:{r["counts"]["compiler_invocations"]}; '
        f'actual exit:{r["compiler_exit_code"]}; clean summary:{r["clean_log_summary"]}; stop:{r["stop_reason"]}/stage:{r["stopped_stage"]}. '
        'The consumed075 marker, separate compiler075 folder and source/include/compiler/terminal/output hashes are retained.\n\n'
        'Frozen073 image-link/version failure and074 metadata failure both occurred before compiler invocation and remain preserved. '
        'The exact074 metadata command returned Restricted in its pinned Windows PowerShell child, while the workspace shell reports '
        'RemoteSigned. The074 results wording about RemoteSigned describes its incorrect expectation, not verified child metadata. '
        'Separate075 binds Restricted to the actual compiler shell. It changes no execution policy and uses no bypass. '
        'Retain074 measured image profile: exactly two links only for pinned powershell.exe; all other images/source/log/artifact '
        'files require one. Full uncached hashes, identity, no-reparse, signatures, clocks and process checks remain.\n\n'
        'Actual native exit1 is retained in the075 schema alongside a clean log and nonempty artifact; frozen072 exit0 checker is unchanged. '
        f'Owned compiler absent afterward:{r["owned_compiler_absent_after"]}; final metadata:{r["metadata_after"]}. '
        'Zero MT5 script/SDK/deployment/terminal log-content/market/orders/receipt grants. '
        'A clean compile establishes a build artifact only; native sharing/publication/ACK and profitability remain unestablished.\n\n'
        'Next NATIVE-SHARING-076-PLAN.md is unexecuted outcome-driven runtime preparation/synchronization/tests before a later policy. '
        'Oct8 expiry requires fresh source/phase instead of modifying frozen072/073/074/075. Preserve033/035 failures, '
        'clock/cost/coverage/flags, consumed2025/reserved Nov-Dec2026 and provider stops. Eligibility/orders remain false.\n')
    with (ROOT/'docs/SHARING-BUILD-075-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-08: compiler-shell-bound build075 sealed; read SHARING-BUILD-075-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass; completed:{r["completed"]}, compiler calls:{r["counts"]["compiler_invocations"]}, '
        f'actual exit:{r["compiler_exit_code"]}, clean summary:{r["clean_log_summary"]}, stop:{r["stop_reason"]}/{r["stopped_stage"]}. '
        'Original073/074 failed precompiler and remain preserved.075 binds actual compiler-child policy Restricted; '
        'workspace shell RemoteSigned was the incorrect074 expectation, not corroborated native metadata. No policy change/bypass. '
        'Pinned two-link shell/private version6244 and all full-hash/identity/signature/process/date/source guards remain. '
        'Fresh072 source unchanged and actual exit1 explicit. Zero MT5 scripts/SDK/deploy/terminal log/market/orders/grants. '
        'Native sharing/publication/ACK/profit unestablished. Next076 runtime preparation/synchronization/tests unexecuted; '
        'Oct8 expiry needs fresh declaration. All old failures/spent/reserved gates retained. Earlier entries are historical.\n\n')
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
