"""Frozen062 synthetic Windows sharing preparation and closure. No MT5 or SDK."""
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
OLD = runpy.run_path(str(ROOT/'scripts/readiness-adapter-061.py'))
sha, sealed, write, bound = (OLD[k] for k in ('sha','sealed','write','bound'))
HANDOFF = OLD['HANDOFF']
ARCHIVE = runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))['verify_archive']
PRIOR = ROOT/'reports/readiness-adapter-061-final-source.json'
PREFIX = 'windows-sharing-062'
LEDGER = ROOT/f'reports/{PREFIX}-ledger.json'
PATTERNS = ('scripts/*062.py','src/forex_demo_lab/*062.py','tests/*062.py','docs/*062*.md','docs/*063*.md')
EXPECTED, NEW, PURE = 975, 30, 0
PYTHON_PATH = '/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python/Scripts/python.exe'
PYTHON_SHA = 'b70275ad94210fce7548761143be5e177769721045e287bb6c80aac3f928c65b'
ZERO = dict(sdk_connections=0,market_reads=0,orders=0,native_fixture_invocations=0,
            native_metatrader_compiler_invocations=0,terminal_deployments=0,terminal_log_content_reads=0)
FALSE = dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
             actual_mt5_repair_verified=False,root_cause_proven=False,native_adapter_ready=False)


def original_failure():
    runtime = sealed(ROOT/'reports/native-pipe-057-runtime.json')
    assert not runtime['completed'] and runtime['permissions_consumed']==1
    assert runtime['sdk_shutdown_called'] and runtime['transport']['closed'] and runtime['cancellation_drained']
    assert runtime['diagnostic_trace'][0]['windows_operations'][-1]['events'][1]['category']=='pipe_closing'
    row = sealed(ROOT/'reports/native-log-059-audit.json')['records'][0]
    assert (row['reply_bytes'],row['decode_reason'],row['read_error_category'],row['read_elapsed_us'])==(0,1,6,11164)
    return row


def prior_verify():
    assert sha(PRIOR)=='a5886db4ad4a1e8650b1fd57ec2f64941b64bb2acd7e857edc1c825ce075d34b'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/readiness-adapter-061-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-062-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==1958
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1818
    original_failure()
    return b


def freeze():
    from datetime import datetime,timezone
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    b=prior_verify()
    for n in HANDOFF:b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        path=PRIOR.with_suffix(suffix);b[path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256'):
        path=ROOT/f'reports/readiness-adapter-061-completion-review{suffix}'
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    assert sha(bound(PYTHON_PATH))==PYTHON_SHA;b[PYTHON_PATH]=PYTHON_SHA
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        maximum_full_regressions=1,prior_bindings_verified=1958,prior_archive_members_verified=1818,
        declared_date='2026-10-07',probe_identity='62000000000000000000000000000001',
        maximum_native_sessions=1,maximum_handle_open_attempts=16,maximum_write_calls=1,
        maximum_read_calls=2,maximum_directories=1,maximum_files=2,maximum_measured_session_ms=60000,
        maximum_write_bytes=84,maximum_requested_read_bytes=85,maximum_receipt_permissions=0,
        original_runtime_completed=False,**ZERO,**FALSE))
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
    l=verify();p=sealed(ROOT/f'reports/{PREFIX}-preparation-checks.json')
    assert p['checker_passed'] and p['tests_passed']==975
    r=sealed(ROOT/f'reports/{PREFIX}-runtime.json')
    started=sealed(ROOT/f'reports/{PREFIX}-runtime-started.json')
    assert r['ledger_sha256']==started['ledger_sha256']==sha(LEDGER)
    assert r['preparation_checks_sha256']==started['preparation_checks_sha256']==sha(ROOT/f'reports/{PREFIX}-preparation-checks.json')
    assert r['runtime_plan_sha256']==sha(ROOT/'docs/WINDOWS-SHARING-062-RUNTIME-PLAN.md')
    assert r['native_sessions']==1 and r['phase']==l['probe_identity'] and r['declared_date']==l['declared_date']
    assert r['handle_open_attempts']<=16 and r['write_attempts']<=1 and r['read_attempts']<=2 and r['directory_attempts']<=1
    assert all(r[k]==0 for k in ('sdk_connections','mt5_invocations','receipt_permissions','quote_reads','history_reads','orders'))
    assert not r['native_mql_verified'] and not r['orders_available'] and not r['blocking_preemption_verified']
    if r['passed']:
        from forex_demo_lab.sharing_probe_062 import DATA
        assert (r['handle_open_attempts'],r['write_attempts'],r['read_attempts'],r['directory_attempts'])==(8,1,2,1)
        assert r['read_counts']==[84,84] and r['synthetic_sha256']==hashlib.sha256(DATA).hexdigest()
        assert [x['category'] for x in r['observations']]==['none','none','sharing_violation','none','none','sharing_violation','sharing_violation']
        assert r['same_file_verified'] and r['security_path_verified'] and not r['measured_overrun'] and r['elapsed_us']<60000000
        assert r['cleanup']['all_handles_closed'] and r['cleanup']['unconfirmed_handles']==0 and r['cleanup']['allocations_released']
        assert len(r['native_close_diagnostics'])==5 and all(x['closed'] for x in r['native_close_diagnostics'])
    original_failure()
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),runtime_sha256=sha(ROOT/f'reports/{PREFIX}-runtime.json'),
        tests_passed=EXPECTED,native_probe_passed=r['passed'],native_sessions=1,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,native_probe_passed=r['passed'])))


def result_text(r):
    return (f'# Local Windows sharing062 results — 2026-10-07\n\n'
        f'975 tests passed:945 previous plus30 new, zero failures/errors/skips. '
        f'One frozen regression. Native synthetic probe passed:{r["passed"]}; '
        f'stop:{r["stop_reason"]}; elapsed_us:{r["elapsed_us"]}.\n\n'
        f'One session, {r["handle_open_attempts"]} handle-open attempts, '
        f'{r["write_attempts"]}84-byte write attempts, {r["read_attempts"]} reads requesting85 bytes; '
        f'read counts:{r["read_counts"]}. Current-user owner/protected DACL, normalized '
        f'local handle paths/no-reparse and same-file identity/size/pointer checked:{r["security_path_verified"]}. '
        f'Cleanup:{r["cleanup"]}. Five closed handles expected on success, no event or pending IO. '
        'Dedicated synthetic directory/file retained; no delete/rename/recursive cleanup.\n\n'
        'On success, existing writer excluded the read-only seal; after closing the writer, '
        'two readers shared the file and new writer/DELETE-access opens were rejected with '
        'actual sharing_violation. Two native85-byte reads returned exactly84 matching bytes. '
        'These are local Win32 observations only; failures, if any, remain failed.\n\n'
        'No SDK/MT5/compiler/deployment/scripts/log-content reads, receipts/permissions, '
        'quotes/history/strategy or orders. Original058 failure/one spent allowance, '
        '059 other-error/zero-byte record and060 failed fixture preserved. '
        'No MQL sharing/publication/ACK or transport repair proof; blocking calls cannot '
        'be interrupted by these checks. Same-logon owner trust and handle-lifetime limits remain.\n\n'
        'Next063 offline regular-file publication/ACK design and native MQL feasibility '
        'before any fresh MT5 preparation. Read WINDOWS-SHARING-062-DESIGN.md and '
        'NATIVE-TRANSPORT-063-PLAN.md. Old market gates/033/035 failures, consumed2025, '
        'reservedNov–Dec2026/provider stops remain; fresh/annual eligibility and orders false. '
        'No profit evidence follows from file-sharing tests.\n')


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    r=sealed(ROOT/f'reports/{PREFIX}-runtime.json')
    assert c['runtime_sha256']==sha(ROOT/f'reports/{PREFIX}-runtime.json')
    with (ROOT/'docs/WINDOWS-SHARING-062-RESULTS.md').open('x') as f:f.write(result_text(r))
    handoff=(f'Latest — 2026-10-07: local Windows sharing062 sealed; read WINDOWS-SHARING-062-RESULTS.md. '
        f'975 tests/30 new pass; one native synthetic probe passed:{r["passed"]}, '
        f'{r["handle_open_attempts"]} opens/{r["write_attempts"]} writes/{r["read_attempts"]} reads, '
        f'counts:{r["read_counts"]}, cleanup:{r["cleanup"]["all_handles_closed"] if r["cleanup"] else False}. '
        'No SDK/MT5/receipt permissions/market/orders. Native Win32 evidence only; MQL sharing, '
        'publication/ACK, blocking preemption and transport repair unverified. Old058 failure/spent '
        'permission/059 record/060 failed fixture preserved. Next063 offline publication/ACK and '
        'MQL feasibility, not executed. All market gates/reserved exclusions retained; fresh/annual '
        'eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern): b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items(): assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}
    final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal): z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,original_runtime_completed=False,native_sessions=1,native_probe_passed=r['passed'],**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items(): assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);l=sealed(LEDGER)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    original_failure()
    plan=ROOT/'docs/NATIVE-TRANSPORT-063-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        native_sessions=1,native_probe_passed=r['native_probe_passed'],next_plan='docs/NATIVE-TRANSPORT-063-PLAN.md',next_plan_sha256=sha(plan),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','test','check','seal','review','verify','check-runtime'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,**{'check-runtime':check_runtime},verify=lambda:print(len(verify()['bindings'])))
    actions[parser.parse_args().action]()
