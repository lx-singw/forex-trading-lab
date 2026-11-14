"""Immutable offline056 freeze/test/check/seal/review; no native runtime calls."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-055.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
HANDOFF=API['API']['HANDOFF']
PRIOR=ROOT/'reports/native-log-055-final-source.json'
PREFIX='transport-diagnostics-056'
LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PATTERNS=('scripts/*056.py','src/forex_demo_lab/*056.py','tests/*056.py',
          'docs/*056*.md','mt5/Scripts/*056*','mt5/Tests/*056*')
EXPECTED=842
ZERO=dict(sdk_connections=0,market_reads=0,orders=0,native_fixture_invocations=0,
          native_metatrader_compiler_invocations=0,terminal_deployments=0,terminal_log_content_reads=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
           actual_mt5_repair_verified=False,root_cause_proven=False)

def verify_archive(path, record, expected_members=None):
    b=record['source_and_evidence_bindings']
    assert sha(path.with_suffix('.zip'))==record['archive_sha256']
    internal=set(b)-set(record['archive_external_bindings'])
    with zipfile.ZipFile(path.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal) and set(z.namelist())==internal
        if expected_members is not None:assert len(internal)==expected_members
        for n in internal:assert hashlib.sha256(z.read(n)).hexdigest()==b[n],n
    return len(internal)

def prior_verify():
    assert sha(PRIOR)=='d017e87e457f557291a67c67dd1d229df4ab978bcabad63c3253a5f07ec77705'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/native-log-055-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TRANSPORT-056-PLAN.md')
    assert p['original054_runtime_completed'] is False and p['native_reason_codes']==[23]
    b=dict(p['source_and_evidence_bindings']);assert len(b)==1757
    for n,h in b.items():assert sha(bound(n))==h,n
    verify_archive(PRIOR,p,1637)
    API['original_failure']()
    return b

def freeze():
    b=prior_verify()
    for n in HANDOFF:b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        p=PRIOR.with_suffix(suffix);b[p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256'):
        p=ROOT/f'reports/native-log-055-completion-review{suffix}';b[p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in (*PATTERNS,'scripts/*055.py','docs/*055*.md'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=42,pure_header_cases=42,
        prior_bindings_verified=1757,prior_archive_members_verified=1637,
        maximum_full_regressions=1,original054_runtime_completed=False,
        read_count_repair_approved=False,ack_native_implemented=False,**ZERO,**FALSE))
    # Snapshot new source before any tests; failed runs cannot lose their source.
    selected={n:h for n,h in b.items() if any(ROOT.joinpath(n).match(x) for x in PATTERNS) and not n.startswith('/')}
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED)))

def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    return l

def test():
    sys.path.insert(0,str(ROOT/'src'))
    verify();write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(ledger_sha256=sha(LEDGER),suite_consumed=True,**ZERO,**FALSE))
    start=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    r=unittest.TextTestRunner(verbosity=1).run(suite)
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=42,pure_header_cases=42,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),elapsed_seconds=time.monotonic()-start,
        ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed:raise SystemExit(1)

def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['ledger_sha256']==sha(LEDGER) and t['passed']
    assert (t['tests_run'],t['new_tests'],t['pure_header_cases'],t['failures'],t['errors'],t['skipped'])==(842,42,42,0,0,0)
    for k,v in {**ZERO,**FALSE}.items():assert t[k]==l[k]==v
    assert l['read_count_repair_approved'] is False and l['ack_native_implemented'] is False
    API['original_failure']()
    audit=sealed(ROOT/'reports/native-log-055-audit.json')
    assert audit['records'][0]['reply_bytes']==0 and audit['records'][0]['decode_reason']==1
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/n)['diagnostic_passed'] is False
    s=sealed(ROOT/f'reports/{PREFIX}-initial-source.json')
    path=ROOT/f'reports/{PREFIX}-initial-source.zip';assert sha(path)==s['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(s['bindings']) and len(z.infolist())==len(s['bindings'])
        for n,h in s['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),
        ledger_sha256=sha(LEDGER),tests_passed=EXPECTED,new_tests=42,pure_header_cases=42,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,actual_mt5_repair_verified=False)))

RESULTS='''# Offline transport diagnostics056 results — 2026-10-07

842 tests passed: the existing800 plus42 new tests. One frozen full regression,
zero failures/errors/skips.42 actual pure MQL category/duration cases match
Python through a temporary Linux C++ shim. This is not an MT5 compilation or
test of its blocking FileReadArray wrapper.

The new Windows adapter records fixed operation/error categories and duration,
distinguishes immediate from pending failures, preserves two-second waits and
one-second cancellation drain, retains uncertain IO memory/handle, and redacts
private exceptions. Existing047 security/identity hashing remains inherited.
Injected tests cover immediate/pending write/read errors, failed wait, cancelled
or raced completion, undrained/incomplete/unknown completion, short writes,
count/deadline bounds and cleanup/privacy. No frozen old backend was changed.

84/85-byte single-read models reject returned short/extra/error frames. An84-byte
read can miss an unread suffix, so changing the count is not approved as a fix.
The experimental native wrapper records the read error before cleanup and
measures duration; it does not enforce a timeout while a native call blocks.
The bounded consumption ACK is modeled and tested for exact frame/phase/policy,
guard, receipt and deadline checks. Native ACK IO/sender and long-connect
integration are unimplemented and are not deployment-ready.

Original054/051 stay failed with one consumed permission each;054 native reply
bytes0/code1 and immediate helper write rejection remain. Actual error/root
cause cannot be reconstructed by offline tests. No SDK/native MT5/compiler/
deployment/log-reread/price/history/order or strategy calls in056.

Next prepare a fresh diagnostic phase using original85-byte native read plus
new error/timing measurements, keeping all guards and original protocol bounds.
Do not adopt84-byte read or native ACK without further protocol proof. Read
NATIVE-TRANSPORT-057-PLAN.md before any future preparation. All earlier market
gates,033/035 failures, consumed2025/reservedNov–Dec2026/provider stops remain;
fresh/annual eligibility and orders false. No profitability claim follows
from transport unit tests. See NATIVE-TRANSPORT-056-DESIGN.md for limitations
and official API references.
'''

def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    with (ROOT/'docs/NATIVE-TRANSPORT-056-RESULTS.md').open('x') as f:f.write(RESULTS)
    handoff=('Latest — 2026-10-07: offline diagnostics056 sealed; read NATIVE-TRANSPORT-056-RESULTS.md. '
        '842 tests/42 new/42 pure MQL differential cases pass. Safe Windows error categories and pending '
        'retention tested; native read wrapper uncompiled, read-count84 fix not approved (unread suffix '
        'ambiguity), ACK modeled only. Original054/051 failures and permissions retained; root cause '
        'unknown. Zero SDK/MT5/compiler/deployment/log-reread/market/order calls. Next057 preparation '
        'original85 read plus measured error/timing; not executed. All market gates/reserved data '
        'remain; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        p=ROOT/n;text=p.read_text();i=text.index('\n')+1;p.write_text(text[:i]+'\n'+handoff+text[i:]);b[n]=sha(p)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip','docs/NATIVE-TRANSPORT-057-PLAN.md'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}
    final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        external_bindings_verified=len(external),tests_passed=EXPECTED,new_tests=42,pure_header_cases=42,
        original054_runtime_completed=False,original051_runtime_completed=False,
        read_count_repair_approved=False,ack_native_implemented=False,**ZERO,**FALSE)
    verify_archive(final,record)
    write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))

def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=verify_archive(final,r)
    l=sealed(LEDGER)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==842 and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    API['original_failure']()
    plan=ROOT/'docs/NATIVE-TRANSPORT-057-PLAN.md'
    assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,external_bindings_verified=len(r['archive_external_bindings']),
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),
        tests_passed=842,new_tests=42,pure_header_cases=42,next_plan='docs/NATIVE-TRANSPORT-057-PLAN.md',
        next_plan_sha256=sha(plan),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,verify=lambda:print(len(verify()['bindings'])))
    actions[p.parse_args().action]()
