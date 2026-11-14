"""Immutable offline063 publication freeze/test/check/seal/review. Never starts MT5 or SDK."""
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
OLD = runpy.run_path(str(ROOT/'scripts/windows-sharing-062.py'))
sha, sealed, write, bound = (OLD[k] for k in ('sha','sealed','write','bound'))
HANDOFF = OLD['HANDOFF']
ARCHIVE = runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))['verify_archive']
PRIOR = ROOT/'reports/windows-sharing-062-final-source.json'
PREFIX = 'publication-063'
LEDGER = ROOT/f'reports/{PREFIX}-ledger.json'
PATTERNS = ('scripts/*063.py','src/forex_demo_lab/*063.py','tests/*063.py',
            'docs/*063*.md','docs/*064*.md')
EXPECTED, NEW, PURE = 1017, 42, 0
ZERO = dict(sdk_connections=0,market_reads=0,orders=0,native_fixture_invocations=0,
            native_metatrader_compiler_invocations=0,terminal_deployments=0,terminal_log_content_reads=0)
FALSE = dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
             actual_mt5_repair_verified=False,root_cause_proven=False,native_adapter_ready=False,native_publication_verified=False,native_mql_verified=False)


def original_failure():
    runtime = sealed(ROOT/'reports/native-pipe-057-runtime.json')
    assert not runtime['completed'] and runtime['permissions_consumed']==1
    assert runtime['sdk_shutdown_called'] and runtime['transport']['closed'] and runtime['cancellation_drained']
    assert runtime['diagnostic_trace'][0]['windows_operations'][-1]['events'][1]['category']=='pipe_closing'
    row = sealed(ROOT/'reports/native-log-059-audit.json')['records'][0]
    assert (row['reply_bytes'],row['decode_reason'],row['read_error_category'],row['read_elapsed_us'])==(0,1,6,11164)
    return row


def prior_verify():
    assert sha(PRIOR)=='7d41083ba899a52ef5845231d61c01f0e635219c22e26e6d6a3cc83c1b51981b'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/windows-sharing-062-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete']
    assert r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-063-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==1988
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1846
    native=sealed(ROOT/'reports/windows-sharing-062-runtime.json')
    checks=sealed(ROOT/'reports/windows-sharing-062-checks.json')
    assert native['passed'] and native['cleanup']['all_handles_closed']
    assert native['read_counts']==[84,84]
    assert (native['handle_open_attempts'],native['write_attempts'],native['read_attempts'])==(8,1,2)
    assert checks['checker_passed'] and checks['runtime_sha256']==sha(ROOT/'reports/windows-sharing-062-runtime.json')
    assert r['native_sessions']==1 and r['native_probe_passed']
    original_failure()
    return b


def freeze():
    b=prior_verify()
    for n in HANDOFF:b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        path=PRIOR.with_suffix(suffix);b[path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256'):
        path=ROOT/f'reports/windows-sharing-062-completion-review{suffix}'
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        maximum_full_regressions=1,prior_bindings_verified=1988,prior_archive_members_verified=1846,
        original_runtime_completed=False,prior_native_probe_passed=True,**ZERO,**FALSE))
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
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


RESULTS = (ROOT/'docs/PUBLICATION-063-RESULTS-TEMPLATE.md').read_text()


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    with (ROOT/'docs/PUBLICATION-063-RESULTS.md').open('x') as f: f.write(RESULTS)
    handoff=('Latest — 2026-10-07: offline publication063 sealed; read PUBLICATION-063-RESULTS.md. '
        '1017 tests/42 new pass. Exact047 response and40-byte response-digest ACK use '
        'exclusive create/write/close/same-file read seals retained through ACK/cleanup. '
        'Crash/replacement/stale/restart/expiry/cleanup/privacy failures tested; no allowance refund. '
        'Zero SDK/native/compiler/deploy/log/market/orders; injected proof only. '
        '062 native sharing success and058 failure/consumed permission/059 error/060 failed fixture retained. '
        'MQL sharing/publication/ACK/preemption unverified. Next064 synthetic MQL sharing preparation '
        'with independent hold evidence, not executed. All market gates/reserved exclusions retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
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
        tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,original_runtime_completed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items(): assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);l=sealed(LEDGER)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    original_failure()
    plan=ROOT/'docs/NATIVE-SHARING-064-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        next_plan='docs/NATIVE-SHARING-064-PLAN.md',next_plan_sha256=sha(plan),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,verify=lambda:print(len(verify()['bindings'])))
    actions[parser.parse_args().action]()
