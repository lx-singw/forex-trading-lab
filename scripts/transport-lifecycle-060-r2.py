"""Immutable offline060 freeze/test/check/seal/review. Never starts MT5 or SDK."""
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
OLD = runpy.run_path(str(ROOT/'scripts/native-log-059.py'))
sha, sealed, write, bound = (OLD[k] for k in ('sha','sealed','write','bound'))
HANDOFF = OLD['API']['HANDOFF']
ARCHIVE = runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))['verify_archive']
PRIOR = ROOT/'reports/native-log-059-final-source.json'
PREFIX = 'transport-lifecycle-060-r2'
LEDGER = ROOT/f'reports/{PREFIX}-ledger.json'
PATTERNS = ('scripts/*060-r*.py','scripts/*060.py','src/forex_demo_lab/*060.py','tests/*060.py',
            'docs/*060*.md','mt5/Scripts/*060*','mt5/Tests/*060*','docs/*061*.md')
EXPECTED, NEW, PURE = 909, 35, 32
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
    assert sha(PRIOR)=='914f15aba7a635aabdd3e481a455421223cc42dce43ee8308b37e38d63c4b0b0'
    p = sealed(PRIOR); review = sealed(ROOT/'reports/native-log-059-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete']
    assert review['final_source_sha256']==sha(PRIOR)
    assert review['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-060-PLAN.md')
    b = dict(p['source_and_evidence_bindings']); assert len(b)==1899
    for n,h in b.items(): assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1764
    original_failure()
    return b


def freeze():
    b = prior_verify()
    for n in HANDOFF: b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        path = PRIOR.with_suffix(suffix); b[path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256'):
        path = ROOT/f'reports/native-log-059-completion-review{suffix}'
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    first = sealed(ROOT/'reports/transport-lifecycle-060-tests.json')
    assert not first['passed'] and (first['tests_run'],first['failures'],first['errors'])==(909,1,0)
    initial = sealed(ROOT/'reports/transport-lifecycle-060-initial-source.json')
    first_zip = ROOT/'reports/transport-lifecycle-060-initial-source.zip'
    assert sha(first_zip)==initial['archive_sha256']
    with zipfile.ZipFile(first_zip) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items(): assert hashlib.sha256(z.read(n)).hexdigest()==h
    for pattern in ('reports/transport-lifecycle-060-*.json','reports/transport-lifecycle-060-*.sha256','reports/transport-lifecycle-060-initial-source.zip'):
        for path in ROOT.glob(pattern): b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected = {}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n = path.relative_to(ROOT).as_posix(); b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
                     maximum_full_regressions=1,prior_bindings_verified=1899,
                     prior_archive_members_verified=1764,original_runtime_completed=False,**ZERO,**FALSE))
    path = ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected): z.write(ROOT/n,n)
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


RESULTS = '''# Offline readiness/lifecycle060 results — 2026-10-07

Revision2:909 tests passed, existing874 plus35 new, no failures/errors/skips in
one frozen full regression. Revision1 source archive and909-test result with
one failed clock-reversal fixture are preserved. That fixture moved a zero
monotonic clock into an invalid negative value, so the model correctly returned
the redacted validation failure rather than the expected reversal category.
The fixture now reverses a valid positive clock; lifecycle code is unchanged.
32 new pure MQL category cases agree with Python through a Linux
C++ shim. Prior87 wire frames,42 category/timing comparisons and6 Windows
lifetime cases remain regression evidence. No MT5 compiler or runtime was used.

The injected candidate waits through2.8–3.2s guard delays while keeping its handle
open, then validates the unchanged047 exact receipt and acknowledges consumption
within its remaining2s lifetime. Zero/partial/extra replies, absent message
boundary proof, read/write failures, lost ACK, cleanup failure/pending retention,
repeated request/restart, clock reversal/discontinuity,900s session expiry and
post-operation/guard/cleanup receipt expiry are tested. A finite poll budget
also rejects frozen-clock spinning. Real one-use047 temporary reservations and
guard latency are exercised; failed delivery never refunds a permission.

MetaQuotes' FileSize readiness example supports this investigation, but it does
not prove why057 read0. Its error remains category6(other), exact code unknown.
All27 documented file errors now have distinct closed categories for future
diagnostics. Uncompiled native availability/byte-value probes establish no read
count, timeout, message boundary or ACK proof. An84-byte return or availability
snapshot cannot establish absence of an unread/later suffix. The injected
boundary/pending capabilities have no verified MQL implementation. Blocking
native calls cannot be interrupted by these Python/MQL deadline checks.

Original058 remains failed, one permission spent, repeat unarmed, SDK/pipe closed;
059 late record does not repair it. No SDK/native pipe/terminal/compiler/deploy/
log-content reread/quotes/history/strategy/orders in060. Read the060 design and
061 plan before continuing offline adapter feasibility; no fresh native phase
is declared and no deployment is available. Old market gates/033/035 failures,
consumed2025/reservedNov–Dec2026/provider stops remain; fresh/annual eligibility
and automated orders false. These transport tests provide no profit evidence.
'''


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    with (ROOT/'docs/NATIVE-TRANSPORT-060-RESULTS.md').open('x') as f: f.write(RESULTS)
    handoff=('Latest — 2026-10-07: offline readiness/lifecycle060 sealed; read NATIVE-TRANSPORT-060-RESULTS.md. '
        'Revision2:909 tests/35 new/32 new pure categories pass; first failed clock fixture/source preserved. '
        'Injected readiness keeps handle open through3s guard '
        'delay, exact047 receipt/boundary plus bounded remaining-deadline ACK modeled. Native pending/boundary '
        'adapter and blocking timeout unproven; uncompiled probes only. Original058 failure/one permission '
        'and059 native0 bytes/other error/11164us retained. Zero SDK/native/compiler/deploy/log-reread/market/orders. '
        'Next061 offline adapter feasibility, not executed. Old market gates/reserved exclusions retained; '
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
    plan=ROOT/'docs/NATIVE-TRANSPORT-061-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,pure_header_cases=PURE,
        next_plan='docs/NATIVE-TRANSPORT-061-PLAN.md',next_plan_sha256=sha(plan),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,verify=lambda:print(len(verify()['bindings'])))
    actions[parser.parse_args().action]()
