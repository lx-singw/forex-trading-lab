"""Frozen065 companion preparation, compatibility and one compile; no MT5 runtime. Never starts MT5 or SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OLD = runpy.run_path(str(ROOT/'scripts/mql-sharing-064.py'))
sha, sealed, write, bound = (OLD[k] for k in ('sha','sealed','write','bound'))
HANDOFF = OLD['HANDOFF']
ARCHIVE = runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))['verify_archive']
PRIOR = ROOT/'reports/mql-sharing-064-final-source.json'
PREFIX = 'sharing-companion-065'
LEDGER = ROOT/f'reports/{PREFIX}-ledger.json'
PATTERNS = ('scripts/*065.py','src/forex_demo_lab/*065.py','tests/*065.py','docs/*065*.md','docs/*066*.md')
EXPECTED, NEW, PURE = 1091, 36, 0
PYTHON_PATH = '/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python/Scripts/python.exe'
PYTHON_SHA = 'b70275ad94210fce7548761143be5e177769721045e287bb6c80aac3f928c65b'
ZERO = dict(sdk_connections=0,market_reads=0,orders=0,native_fixture_invocations=0,
            native_metatrader_compiler_invocations=0,terminal_deployments=0,terminal_log_content_reads=0)
FALSE = dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
             actual_mt5_repair_verified=False,root_cause_proven=False,native_adapter_ready=False,native_publication_verified=False,native_mql_verified=False,native_reader_compiled=False)


def original_failure():
    runtime = sealed(ROOT/'reports/native-pipe-057-runtime.json')
    assert not runtime['completed'] and runtime['permissions_consumed']==1
    assert runtime['sdk_shutdown_called'] and runtime['transport']['closed'] and runtime['cancellation_drained']
    assert runtime['diagnostic_trace'][0]['windows_operations'][-1]['events'][1]['category']=='pipe_closing'
    row = sealed(ROOT/'reports/native-log-059-audit.json')['records'][0]
    assert (row['reply_bytes'],row['decode_reason'],row['read_error_category'],row['read_elapsed_us'])==(0,1,6,11164)
    return row


def prior_verify():
    assert sha(PRIOR)=='5fd7ffcfdd9efce23c599931dd8e719a966ba992684af89f8cfaf8feabf36c7a'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/mql-sharing-064-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-SHARING-065-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==2037
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1891
    assert r['tests_passed']==1055 and r['frozen_inputs_verified']==2021
    original_failure();return b


def freeze():
    from datetime import datetime,timezone
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    b=prior_verify()
    assert sha(bound(PYTHON_PATH))==PYTHON_SHA;b[PYTHON_PATH]=PYTHON_SHA
    for n in HANDOFF:b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        path=PRIOR.with_suffix(suffix);b[path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256'):
        path=ROOT/f'reports/mql-sharing-064-completion-review{suffix}'
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        maximum_full_regressions=1,prior_bindings_verified=2037,prior_archive_members_verified=1891,
        original_runtime_completed=False,prior_native_probe_passed=True,maximum_native_compiler_invocations=1,maximum_compatibility_sessions=1,declared_date='2026-10-07',probe_identity='65000000000000000000000000000001',**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED)))


def verify():
    l = sealed(LEDGER)
    for n,h in l['bindings'].items(): assert sha(bound(n))==h,n
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(ledger_sha256=sha(LEDGER),suite_consumed=True,**ZERO,**FALSE))
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==EXPECTED and not result.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=result.testsRun,new_tests=NEW,
        pure_header_cases=PURE,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        failure_details=[dict(test=str(t),traceback=detail) for t,detail in result.failures+result.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed: raise SystemExit(1)


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    for k,v in {**ZERO,**FALSE}.items(): assert t[k]==l[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json')
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'; assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items(): assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    original_failure()
    first=sealed(ROOT/'reports/transport-lifecycle-060-tests.json')
    assert not first['passed'] and first['failures']==1 and first['errors']==0
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    write(ROOT/f'reports/{PREFIX}-preparation-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


def check_runtime():
    l=verify();r=sealed(ROOT/f'reports/{PREFIX}-runtime.json')
    started=sealed(ROOT/f'reports/{PREFIX}-runtime-started.json')
    assert r['ledger_sha256']==started['ledger_sha256']==sha(LEDGER)
    assert r['preparation_checks_sha256']==started['preparation_checks_sha256']==sha(ROOT/f'reports/{PREFIX}-preparation-checks.json')
    assert r['runtime_plan_sha256']==sha(ROOT/'docs/METADATA-COMPATIBILITY-065-RUNTIME-PLAN.md')
    assert r['native_sessions']==1 and started['phase']==l['probe_identity']
    sys.path.insert(0,str(ROOT/'src'));from forex_demo_lab.sharing_companion_065 import LIMITS
    assert set(r['counts'])==set(LIMITS)
    assert all(type(v) is int and 0<=v<=LIMITS[k] for k,v in r['counts'].items())
    assert all(r[k]==0 for k in ('sdk_connections','mt5_invocations','receipt_permissions','quote_reads','history_reads','orders'))
    assert not r['native_mql_verified'] and not r['native_publication_verified'] and not r['orders_available']
    assert r['passed'] and r['cleanup']['all_handles_closed'] and r['cleanup']['allocations_released']
    assert r['counts']['opens']==12 and r['counts']['writes']==r['counts']['reads']==r['counts']['directories']==1
    assert len(r['native_close_diagnostics'])==10 and all(x['closed'] for x in r['native_close_diagnostics'])
    assert [p['error'] for p in r['controls']]==[0,0,32,32,0,0]
    assert [p['blocking_companion_handles'] for p in r['controls']]==[0,0,1,1,0,0]
    assert r['actual_windows_backend'] is True
    write(ROOT/f'reports/{PREFIX}-metadata-checks.json',dict(checker_passed=True,compatibility_passed=r['passed'],
        ledger_sha256=sha(LEDGER),runtime_sha256=sha(ROOT/f'reports/{PREFIX}-runtime.json'),**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,compatibility_passed=r['passed'])))


def build():
    import os,subprocess,uuid
    from datetime import datetime,timezone
    verify();assert os.name=='nt' and sha(Path(sys.executable))==PYTHON_SHA
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    checks=sealed(ROOT/f'reports/{PREFIX}-metadata-checks.json');assert checks['checker_passed'] and checks['compatibility_passed']
    assert checks['runtime_sha256']==sha(ROOT/f'reports/{PREFIX}-runtime.json')
    write(ROOT/f'reports/{PREFIX}-build-started.json',dict(ledger_sha256=sha(LEDGER),maximum_compiler_invocations=1,
        metadata_checks_sha256=sha(ROOT/f'reports/{PREFIX}-metadata-checks.json'),reservation_consumed=True))
    native=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
    from forex_demo_lab.native_compiler_042 import native_command,compile_evidence
    settings=sealed(ROOT/'reports/native-compiler-042-ledger.json');shell=bound(settings['powershell_path']);editor=bound(settings['editor_path'])
    count=0;reason=None;directory=None;compiled=False;errors=warnings=None;outputs={};exit_code=None;before=after=None
    try:
        before=native['metadata'](shell);assert before['editor_processes']==0
        root=Path(settings['build_root'])
        for p in (root,*root.parents):assert not p.is_symlink() and not getattr(p.stat(),'st_file_attributes',0)&0x400
        directory=root/('compiler065-'+uuid.uuid4().hex);directory.mkdir(exist_ok=False)
        for name in ('ForexDemoSharing064.mq5','SharingHold064.mqh','ClockGuard042.mqh','CaptureReadiness060.mqh'):
            source=ROOT/'mt5/Scripts'/name;dest=directory/name
            with source.open('rb') as src,dest.open('xb') as dst:
                for data in iter(lambda:src.read(1048576),b''):dst.write(data)
                dst.flush();os.fsync(dst.fileno())
            assert sha(dest)==sha(source)
        verify();assert native['metadata'](shell)['editor_processes']==0
        count=1
        result=native['hidden_process'](native_command(editor,directory/'ForexDemoSharing064.mq5',directory/'compile.log'),editor,60)
        exit_code=result.returncode;log=(directory/'compile.log').read_text(encoding='utf-16')
        artifact=directory/'ForexDemoSharing064.ex5'
        e=compile_evidence(True,log,artifact.stat().st_size if artifact.exists() else 0)
        compiled,errors,warnings=e['compiled'],e['errors'],e['warnings']
        if not compiled:reason='native_compilation_failed'
    except subprocess.TimeoutExpired:reason='owned_compiler_timeout_no_retry'
    except Exception:reason='native_build_failed_details_redacted'
    try:after=native['metadata'](shell)
    except Exception:after=None
    if directory is not None:
        for path in directory.iterdir():
            if path.is_file():outputs[native['external_name'](str(path))]=sha(path)
    write(ROOT/f'reports/{PREFIX}-build.json',dict(ledger_sha256=sha(LEDGER),compiler_invocations=count,
        compiler_exit_code=exit_code,compiled=compiled,errors=errors,warnings=warnings,stop_reason=reason,
        output_bindings=outputs,effective_policy_before=before['effective_policy'] if before else None,
        effective_policy_after=after['effective_policy'] if after else None,execution_policy_changed=False,
        fixture_attached=False,fixture_runtime_executed=False,sdk_connections=0,quote_reads=0,orders_available=False))
    print(json.dumps(dict(compiled=compiled,errors=errors,warnings=warnings,compiler_invocations=count,stop_reason=reason)))


def final_check():
    l=verify();p=sealed(ROOT/f'reports/{PREFIX}-preparation-checks.json');m=sealed(ROOT/f'reports/{PREFIX}-metadata-checks.json')
    b=sealed(ROOT/f'reports/{PREFIX}-build.json')
    assert p['checker_passed'] and m['checker_passed'] and m['compatibility_passed']
    assert b['ledger_sha256']==sha(LEDGER) and b['compiler_invocations']==1 and b['compiled'] and b['errors']==b['warnings']==0
    assert b['effective_policy_before']==b['effective_policy_after']=='Restricted' and not b['execution_policy_changed']
    for n,h in b['output_bindings'].items():assert sha(bound(n))==h,n
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),runtime_sha256=sha(ROOT/f'reports/{PREFIX}-runtime.json'),
        build_sha256=sha(ROOT/f'reports/{PREFIX}-build.json'),tests_passed=EXPECTED,native_compiler_invocations=1,
        compatibility_passed=True,reader_compiled=True,**{k:v for k,v in {**ZERO,**FALSE}.items() if k not in ('native_metatrader_compiler_invocations','native_reader_compiled')}))
    print(json.dumps(dict(checker_passed=True,reader_compiled=True)))


def result_text():
    r=sealed(ROOT/f'reports/{PREFIX}-runtime.json');b=sealed(ROOT/f'reports/{PREFIX}-build.json')
    return ('# Sharing companion065 results\n\n1091 tests/36 new pass, zero failures/errors/skips. '
        'Separate native metadata-only share7 compatibility probe passed. One synthetic84-byte write/read, '
        f'{r["counts"]["opens"]} opens, {r["counts"]["closes"]} closes; all handles/allocations closed/released. '
        'Pre/post write/delete controls succeeded; controls returned actual Win32 error32 while an explicit '
        'helper Win32 reader stood in for MQL. That helper blocker is recorded, so this cannot count as MQL evidence.\n\n'
        f'Unchanged064 MQL source compiled:{b["compiled"]}, errors:{b["errors"]}, warnings:{b["warnings"]}, '
        f'compiler calls:{b["compiler_invocations"]}. Outputs/hash bindings preserved in build report; no deployment/runtime. '
        'Full uncached private guard, process/token/hash/SDK query caps and one-use launch/saved-range source tested '
        'with injected metadata only. Actual SDK/process/logon integration, interactive bootstrap and MQL sharing '
        'remain unverified. Guard cost and blocking calls can exceed deadlines; no preemption claim.\n\n'
        'Zero SDK/MT5 scripts/deploy/log/market/history/strategy/orders/receipt grants in065. Old062 success and '
        '058 failure/spent allowance/059 record/060 failed fixture preserved. Next NATIVE-SHARING-066-PLAN.md '
        'interactive orchestration tests and new runtime declaration before deployment, not executed. '
        'Oct7 reader expires later; fresh date requires new source/phase. Market clock/cost/coverage/flag/033/035 '
        'failures, consumed2025, reserved Nov–Dec2026/provider stops remain; fresh/annual eligibility/orders false.\n')

def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    with (ROOT/'docs/SHARING-COMPANION-065-RESULTS.md').open('x') as f:f.write(result_text())
    handoff=('Latest — 2026-10-07: companion065 preparation sealed; read SHARING-COMPANION-065-RESULTS.md. '
        '1091 tests/36 new pass; one native metadata-share compatibility passed,12 opens/10 closes/one84-byte write/read. '
        'Explicit Win32 stand-in reader blocks write/delete with32; pre/post controls succeed. '
        'One clean native064 MQL compile,0 errors/warnings; no deployment or script runtime. '
        'Private uncached process/account/image guards and caps tested with injected metadata; actual SDK/native MQL '
        'integration/publication/ACK/preemption unverified. Zero SDK/market/orders/receipt grants. '
        'Old successes/failures/spent permissions retained. Next066 interactive orchestration/runtime preparation '
        'before deployment, not executed. FixedOct7 reader expires later. Market gates/reserved exclusions retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern): b[path.relative_to(ROOT).as_posix()]=sha(path)
    build=sealed(ROOT/f'reports/{PREFIX}-build.json');b.update(build['output_bindings'])
    for n,h in b.items(): assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}
    final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal): z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,original_runtime_completed=False,native_sessions=1,metadata_compatibility_passed=True,**{**ZERO,**FALSE,'native_metatrader_compiler_invocations':1,'native_reader_compiled':True})
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items(): assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);l=sealed(LEDGER)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE,'native_metatrader_compiler_invocations':1,'native_reader_compiled':True}.items())
    original_failure()
    plan=ROOT/'docs/NATIVE-SHARING-066-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        next_plan='docs/NATIVE-SHARING-066-PLAN.md',next_plan_sha256=sha(plan),next_plan_executed=False,native_sessions=1,metadata_compatibility_passed=True,**{**ZERO,**FALSE,'native_metatrader_compiler_invocations':1,'native_reader_compiled':True}))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','test','check','seal','review','verify','check-runtime','build','final-check'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,build=build,**{'check-runtime':check_runtime,'final-check':final_check},verify=lambda:print(len(verify()['bindings'])))
    actions[parser.parse_args().action]()
