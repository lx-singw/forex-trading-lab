"""Offline fresh072 source/integration freeze, regression and closure audit."""
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
API=runpy.run_path(str(ROOT/'scripts/sharing-diagnostics-071.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='sharing-integration-072';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/sharing-diagnostics-071-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-SHARING-072-PLAN.md'
PLAN=ROOT/'docs/NATIVE-SHARING-073-BUILD-PLAN.md'
CONTRACT=ROOT/f'reports/{PREFIX}-source-contract.json'
EXPECTED,NEW=1293,52
PATTERNS=('scripts/*072.py','src/forex_demo_lab/*072.py','tests/*072.py',
    'mt5/Scripts/*072.*','mt5/Tests/*072.*','docs/*072*.md','docs/*073*.md')
ZERO=dict(sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    native_metatrader_compiler_invocations=0,native_self_profiles=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,actual_mt5_repair_verified=False,
    native_adapter_ready=False,root_cause_proven=False,native_experiment_repeated=False,compiled=False)


def contract():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.sharing_integration_072 import SOURCE_INPUTS,source_contract072
    return source_contract072({n:sha(ROOT/n) for n in SOURCE_INPUTS})


def freeze():
    assert sha(PRIOR)=='ea1de04cb38750419305665d6b281d305ca73a135260e4ad9d1be9b00cf94e9c'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/sharing-diagnostics-071-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['tests_passed']==1241 and r['bindings_verified']==2245 and r['archive_members_verified']==2077
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='00966b9fe08c1fa5e4343644cac6a8609911fb305a06521dbad203ef0609ee59'
    assert r['next_plan_executed'] is False and r['root_cause_proven'] is False
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2077;API['verify']();API['prior_evidence']()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/sharing-diagnostics-071-completion-review.json',ROOT/'reports/sharing-diagnostics-071-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    declared=contract()
    for n,h in declared['input_bindings'].items():assert b[n]==h
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        prior_bindings_verified=2245,prior_archive_members_verified=2077,tests_retained=1241,
        expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,maximum_native_sessions=0,
        phase=declared['phase'],declared_date=declared['date'],source_contract=declared,
        future_plan_sha256=sha(PLAN),maximum_diagnostic_events=192,maximum_launch_delay_ms=10000,
        per_file_image_cap=136314880,aggregate_guard_hash_bytes=103079215104,**ZERO,**FALSE))
    write(CONTRACT,dict(**declared,ledger_sha256=sha(LEDGER)))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW,compiled=False)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['prior_source_sha256']==sha(PRIOR) and l['prior_plan_sha256']==sha(PRIOR_PLAN)
    assert l['source_contract']==contract() and l['future_plan_sha256']==sha(PLAN)
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic();r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in r.failures+r.errors],
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
    saved=sealed(CONTRACT);assert saved==dict(**contract(),ledger_sha256=sha(LEDGER))
    from forex_demo_lab.sharing_runtime_069 import LIMITS069
    from forex_demo_lab.image_guard_068 import MAX_IMAGE_BYTES
    assert LIMITS069['hash_bytes']==l['aggregate_guard_hash_bytes']==103079215104
    assert MAX_IMAGE_BYTES==l['per_file_image_cap']==136314880
    assert (LIMITS069['commands'],LIMITS069['script_arms'],LIMITS069['schedule_waits'],LIMITS069['log_bytes'])==(6,2,2,65536)
    observations=API['prior_evidence']();assert observations['root_cause_proven'] is False
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    for n in ('reports/native-sharing-072-runtime.json','reports/native-sharing-072-runtime-reservation.json',
              'reports/native-sharing-072-dispatch-started.json','reports/native-sharing-072-authorization.json'):
        assert not (ROOT/n).exists()
    assert not list(ROOT.glob('mt5/**/ForexDemoSharing072.ex5'))
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,
        source_contract_sha256=sha(CONTRACT),prior_native_evidence_retained=True,
        fresh_source_integrated=True,pure_header_comparisons=114,future_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,pure_comparisons=114,compiled=False)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER) and c['source_contract_sha256']==sha(CONTRACT)
    text=(f'# Fresh sharing integration072 results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        '114 pure C++/MQL-header/Python hold and synthetic-byte comparisons agree. Fresh072 script, hold header, '
        'phase/sandbox, Oct8 sampler, log parser/matcher, exclusive reservation and071 diagnostic integration '
        'are prepared. Actual-type real/contest rejection, uncached guards, fresh backend binding, clock '
        'budgets/expiry, restart/duplicates, independent controls and cleanup failure tested with injected peers.\n\n'
        'A separate Oct8 sampler was required: the old047 sampler is fixed to Oct7. Its source and all earlier '
        'frozen inputs remain unchanged. Fresh sampler preserves shape/nonnegative integer/date checks, '
        '900s/session/sample/skew limits. Script remains default-off/read-only/no market/order APIs. '
        'New source contract binds script plus three includes and exact future clean6244 EX5 build schema.\n\n'
        'Timing gates remain unchanged. Injected5000ms post-arm plus6000ms probe guard rejects before waits; '
        'these durations do not establish native timing or explain070 failure. Its exact cause remains unknown. '
        'Old native evidence, consumed raw reservations without invented sidecars and dispatches retained.\n\n'
        'Zero native MT5/compiler/SDK/deployment/terminal log-content/self-profile/market/orders/grants. '
        'The source is uncompiled and undeployed; no072 native session authorized. Pure header/injected '
        'success is not MQL compilation/runtime/publication/ACK or profit proof. Next NATIVE-SHARING-073-BUILD-PLAN.md '
        'requires source-bound compile preparation/tests and separate actual build verification; after Oct8 '
        'expiry declare fresh source/phase rather than edit072. Retain033/035 failures, clock/cost/coverage/flags, '
        'consumed2025, reserved Nov–Dec2026 and provider exclusions; fresh/annual eligibility/orders false.\n')
    with (ROOT/'docs/SHARING-INTEGRATION-072-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-08: fresh offline sharing integration072 sealed; read SHARING-INTEGRATION-072-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new/114 pure header comparisons pass, zero failures/errors/skips. Fresh072 MQL '
        'source/phase/sandbox/Oct8 sampler/parser/matcher/reservation integrated with071 diagnostics; actual '
        'DEMO/uncached guards and timing/budget/cleanup limits retained. Old Oct7 sampler unchanged. Injected '
        '5000ms post-arm plus6000ms probe guard fails unchanged10s gate; native timing/root cause unknown. '
        'Zero native MT5/compiler/SDK/deploy/terminal log/self-profile/market/orders/grants; uncompiled/undeployed. '
        'Old failures/spent allowances retained. Next073 source-bound compilation preparation/tests/build '
        'verification, not executed; expired072 requires fresh declaration. Native sharing/publication/ACK/profit '
        'unestablished;033/035/reserved gates retained; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
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
        new_tests=NEW,pure_header_comparisons=114,prior_native_evidence_retained=True,
        fresh_source_integrated=True,source_contract_sha256=sha(CONTRACT),future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final),compiled=False)))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and r['source_contract_sha256']==sha(CONTRACT)
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN) and not r['future_plan_executed']
    API['prior_evidence']()
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,pure_header_comparisons=114,
        prior_native_evidence_retained=True,source_contract_sha256=sha(CONTRACT),
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    dict(freeze=freeze,test=test,check=check,seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
