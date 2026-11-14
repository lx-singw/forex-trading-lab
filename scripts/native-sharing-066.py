"""Offline immutable066 runner preparation. Never instantiates native APIs/SDK."""
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
OLD=runpy.run_path(str(ROOT/'scripts/sharing-companion-065-r2.py'))
sha,sealed,write,bound=(OLD[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=OLD['HANDOFF'],OLD['ARCHIVE']
PRIOR=ROOT/'reports/sharing-companion-065-r2-final-source.json'
PREFIX='native-sharing-066';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
EXPECTED,NEW=1128,37
PATTERNS=('scripts/*066.py','src/forex_demo_lab/*066.py','tests/*066.py','docs/*066*.md','docs/*067*.md')
ZERO=dict(sdk_connections=0,market_reads=0,orders=0,native_fixture_invocations=0,
    native_metatrader_compiler_invocations=0,terminal_deployments=0,terminal_log_content_reads=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,native_adapter_ready=False,
    actual_mt5_repair_verified=False,root_cause_proven=False,native_runtime_executed=False)


def prior_verify():
    assert sha(PRIOR)=='2fe7380177b6ef887a666e32106eae1d47bb7e0fbba335bc9e4a10d31b10db0b'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/sharing-companion-065-r2-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['tests_passed']==1091 and r['metadata_compatibility_passed'] and r['native_reader_compiled']
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-SHARING-066-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==2092
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1937
    t=sealed(ROOT/'reports/sharing-companion-065-tests.json')
    assert not t['passed'] and t['failures']==1 and t['errors']==0
    OLD['original_failure']();return b


def freeze():
    b=prior_verify()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/sharing-companion-065-r2-completion-review.json',
            ROOT/'reports/sharing-companion-065-r2-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        prior_bindings_verified=2092,prior_archive_members_verified=1937,maximum_native_sessions=0,
        python_sha256=OLD['PYTHON_SHA'],planned_runtime_phase='66000000000000000000000000000001',
        compiled_reader_retained=True,**ZERO,**FALSE))
    zpath=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(zpath),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(ledger_sha256=sha(LEDGER),suite_consumed=True,**ZERO,**FALSE))
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==EXPECTED and not result.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=result.testsRun,new_tests=NEW,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in result.failures+result.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    for k,v in {**ZERO,**FALSE}.items():assert t[k]==l[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    assert not (ROOT/'reports/native-sharing-066-runtime-reservation.json').exists()
    assert not (ROOT/'reports/native-sharing-067-authorization.json').exists()
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    text=('# Native sharing066 preparation results\n\n1128 tests/37 new pass, zero failures/errors/skips. '
        'Guarded interactive runner source prepared: new exclusive066 reservation, one SDK attempt, two exact '
        'launches, helper/terminal uncached private checks, exclusive own deployment, finite5s/35s controls '
        'and one bounded fresh saved-log audit. Bad timing/identity/log/budget/repeats/cleanup stop. '
        'Full guards may miss the30s MQL hold; no relaxed checks/retry or preemption guarantee.\n\n'
        'Injected tests only. Zero native/SDK/deployment/compiler/log/market/strategy/orders/receipts in066. '
        '065 native metadata compatibility and clean064 compile retained, including original065 clock fixture failure. '
        'Actual SDK/process/token/logon/interactive scheduling/MQL sharing remain unverified. Native entry point '
        'requires sealed preparation plus separate067 authorization bound to source and policy; not issued/run.\n\n'
        'Next NATIVE-SHARING-067-POLICY.md: one existing-demo/USD/Algooff current-Oct7 synthetic session, '
        'two manual launches and one fresh saved log range. Later date needs new source/phase/build. '
        'Old failures/spent permissions/market clock/cost/coverage/flags/033/035/consumed2025/reserved Nov–Dec2026 '
        'and provider stops unchanged. Native publication/ACK/adapter readiness and fresh/annual eligibility/orders false.\n')
    with (ROOT/'docs/NATIVE-SHARING-066-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: interactive sharing066 preparation sealed; read NATIVE-SHARING-066-RESULTS.md. '
        '1128 tests/37 new pass. New one-use reservation, uncached helper/terminal guards, exclusive deployment, '
        'finite5s/35s independent controls and one fresh bounded saved log implemented/tested with injected peers. '
        'Slow full guards may miss30s MQL hold; no guard weakening/retry/preemption. Zero native/SDK/deploy/compiler/log/market/orders. '
        '065 compatibility/clean064 compile and all earlier failures/spent permissions retained. Actual native private bootstrap/MQL '
        'integration/publication/ACK remain unverified. Next067 bounded guided runtime policy, not authorized/executed; '
        'fixedOct7 source expires later. Market gates/reserved exclusions retained; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,compiled_reader_retained=True,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);l=sealed(LEDGER)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    OLD['original_failure']();policy=ROOT/'docs/NATIVE-SHARING-067-POLICY.md'
    assert b[policy.relative_to(ROOT).as_posix()]==sha(policy)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,
        next_policy='docs/NATIVE-SHARING-067-POLICY.md',next_policy_sha256=sha(policy),next_policy_executed=False,
        compiled_reader_retained=True,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','verify','seal','review'))
    actions=dict(freeze=freeze,test=test,check=check,seal=seal,review=review,verify=lambda:print(len(verify()['bindings'])))
    actions[p.parse_args().action]()
