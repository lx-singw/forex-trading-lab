"""Seal/audit the one observed early rejection. Cannot authorize or run native code."""
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
API=runpy.run_path(str(ROOT/'scripts/native-timing-078.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='native-timing-079'
LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/native-timing-078-final-source.json'
REVIEW=ROOT/'reports/native-timing-078-completion-review.json'
AUTH=ROOT/'reports/native-timing-078-authorization.json'
START=ROOT/f'reports/{PREFIX}-invocation-started.json'
OUTCOME=ROOT/f'reports/{PREFIX}-invocation-outcome.json'
DECLARATION=ROOT/'docs/NATIVE-TIMING-079-AUDIT.md'
PLAN=ROOT/'docs/NATIVE-TIMING-080-PLAN.md'
OWN=('scripts/native-timing-079.py','src/forex_demo_lab/timing_outcome_079.py',
     'tests/test_timing_outcome_079.py','docs/NATIVE-TIMING-079-AUDIT.md',
     'docs/NATIVE-TIMING-080-PLAN.md')
EXPECTED=24
RETAINED=1492
ABSENT=dict(dispatch='reports/native-timing-078-dispatch-started.json',
    dispatch_sidecar='reports/native-timing-078-dispatch-started.sha256',
    reservation='reports/native-timing-078-sdk-reservation.json',
    reservation_sidecar='reports/native-timing-078-sdk-reservation.sha256',
    runtime='reports/native-timing-078-runtime.json',
    runtime_sidecar='reports/native-timing-078-runtime.sha256')


def expected_authorization():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.native_timing_078 import Spec078,authorization078
    from forex_demo_lab.sharing_adapter_076 import VerifiedBuild076,encoded076
    from forex_demo_lab.image_guard_068 import HelperChain068
    l=sealed(ROOT/'reports/native-timing-078-ledger.json')
    def pair(n):return str(bound(n)),l['runtime_bindings'][n]
    p=l['helper_chain']
    chain=HelperChain068(pair(p['launcher']),pair(p['config']),
        tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
    build=VerifiedBuild076(encoded076(l['build_record']))
    spec=Spec078(build,sha(PRIOR),sha(API['POLICY']),sha(API['PROFILE']),chain,
        pair(l['terminal_name']),pair(l['editor_name']),pair(l['artifact_name']),
        tuple((n,str(ROOT/n)) for n in build.record()['input_bindings']),
        tuple(pair(n) for n in l['sdk_bindings']))
    expected=authorization078(sha(PRIOR),sha(API['POLICY']),sha(API['PROFILE']),
        sha(API['LEDGER']),l['runtime_bindings']['scripts/runtime-native-timing-078.py'],
        build.sha256,spec.component_sha256)
    return expected,l['runtime_bindings'][p['launcher']]


def observed():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.timing_outcome_079 import audit_preflight079
    expected,launcher=expected_authorization()
    sealed(AUTH) # Mandatory digest, then canonical exact-schema byte validation.
    return audit_preflight079(AUTH.read_bytes(),expected,sha(AUTH),
        sealed(START),sealed(OUTCOME),sha(START),launcher,
        {k:(ROOT/n).exists() for k,n in ABSENT.items()})


def retained_checks():
    review=sealed(REVIEW);prior=sealed(PRIOR)
    assert sha(PRIOR)=='d77fd2245d558618739438af080fbafcedd2967769fb25baf9727e3fe7a70945'
    assert review['review_passed'] and review['frozen_input_coverage_complete']
    assert review['final_source_sha256']==sha(PRIOR)
    assert (review['tests_passed'],review['bindings_verified'],review['archive_members_verified'])==(1492,2449,2261)
    assert review['runtime_sources_verified']==29 and review['entry_cases_verified']==6
    assert review['next_plan_sha256']==sha(API['PLAN']) and not review['next_plan_executed']
    assert ARCHIVE(PRIOR,prior)==2261
    t=sealed(ROOT/'reports/native-timing-078-tests.json')
    c=sealed(ROOT/'reports/native-timing-078-checks.json')
    e=sealed(ROOT/'reports/native-timing-078-evidence.json')
    assert t['passed'] and t['tests_run']==RETAINED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert c['checker_passed'] and c['tests_sha256']==sha(ROOT/'reports/native-timing-078-tests.json')
    assert c['evidence_sha256']==sha(ROOT/'reports/native-timing-078-evidence.json')
    assert c['entry_cases_verified']==6 and c['modeled_completions']==1 and c['modeled_rejections']==5
    references={
        'success':(126,8,89,1,None), 'real':(28,1,3,1,'profile_samples'),
        'sdk_changed':(2,0,0,0,'preflight'), 'initialize_failed':(24,0,0,1,'sdk_attach'),
        'signature_failed':(12,0,0,0,'signature'), 'initialize_interrupted':(24,0,0,1,'sdk_attach')}
    assert set(e['cases'])==set(references)
    for name,(hashes,guards,queries,sdk,stage) in references.items():
        row=e['cases'][name];r=row['result'];counts=r['counts']
        assert row['dependencies_injected']
        assert (counts['hash_reads'],counts['guards'],counts['sdk_queries'],counts['sdk_connections'],r['stopped_stage'])==(hashes,guards,queries,sdk,stage)
        assert r['entry_completed']==(name=='success') and not r['orders_available']
    return review


def freeze():
    API['verify']() # Current unchanged inputs/import closure/installed pins, no SDK.
    review=retained_checks();r=observed();p=sealed(PRIOR)
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
                 REVIEW,REVIEW.with_suffix('.sha256'),AUTH,AUTH.with_suffix('.sha256'),
                 START,START.with_suffix('.sha256'),OUTCOME,OUTCOME.with_suffix('.sha256')):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    write(LEDGER,dict(bindings=b,preparation_sha256=sha(PRIOR),
        declaration_sha256=sha(DECLARATION),next_plan_sha256=sha(PLAN),
        prior_bindings_verified=2449,prior_archive_members_verified=2261,
        tests_retained=RETAINED,expected_new_tests=EXPECTED,
        maximum_new_test_runs=1,maximum_new_native_invocations=0,
        runtime_artifacts_required_absent=ABSENT,observed_native_entry_invocations=1,
        authority_retired_for_future_invocation=True,observed_outcome=r))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),new_audit_tests=EXPECTED,native_invocations=1,sdk_connections=0)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['preparation_sha256']==sha(PRIOR)
    assert l['declaration_sha256']==sha(DECLARATION) and l['next_plan_sha256']==sha(PLAN)
    assert l['runtime_artifacts_required_absent']==ABSENT
    assert l['observed_outcome']==observed()
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(test_run_consumed=True,
        ledger_sha256=sha(LEDGER),maximum_native_invocations=0))
    start=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_timing_outcome_079.py')
    r=unittest.TextTestRunner(verbosity=1).run(suite)
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),
        tests_retained=RETAINED,retained_suite_rerun=False,native_invocations=0))
    if not passed:raise SystemExit(1)


def check():
    l=verify();retained_checks();r=observed()
    t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==sha(LEDGER) and not t['retained_suite_rerun'] and t['native_invocations']==0
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json')
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(**r,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),new_audit_tests_passed=EXPECTED,
        tests_retained=RETAINED,retained_suite_rerun=False,
        started_record_sha256=sha(START),outcome_record_sha256=sha(OUTCOME),
        source_import_closure_retained=29,independent_injected_cases_rechecked=6))
    print(json.dumps(dict(audit_passed=True,samples_completed=0,sdk_connections=0,exact_failure_cause_known=False)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/NATIVE-TIMING-079-RESULTS.md'
    text=('# Native timing079 results\n\n'
        'One invocation of the exact frozen078 entry was consumed on2026-10-08. '
        'Current closure/date/image/input verification and canonical authorization passed. '
        'The native process exited1 with the fixed public-preflight rejection; '
        'process duration1979ms, zero timing samples. Exact public failure cause unknown.\n\n'
        'No dispatch, SDK reservation or runtime report (including sidecars) exists. '
        'Frozen entry creates dispatch before native backend/SDK import/attach. '
        'This branch made zero SDK connections/shutdowns/metadata queries/full guards. '
        'Actual demo/account guards were not reached; owned cleanup is inapplicable, '
        'not an observed cleanup success. No scripts, deployment, compiler, terminal-log '
        'content, market data, orders or receipt permissions. Original authorization '
        'and consumed invocation retained; no retry/reset/refund/reuse.\n\n'
        f'{EXPECTED} new offline audit tests passed with zero failures/errors/skips. '
        f'{RETAINED} unchanged preparation tests retained, not rerun; six injected entry '
        'cases and29-source import closure rechecked. Exact authority/schema/hashes, '
        'invocation timestamps/once count/redaction and absent artifacts independently audited. '
        '079 closure is separate from unchanged078 and all earlier failure/source archives.\n\n'
        '1979ms is process duration, not guard latency. No07616-guard timing comparison '
        'is possible;10s/30s/250ms gates remain. Native timing, sharing/publication/ACK, '
        '070 root cause and profitable edge remain unproven. Next NATIVE-TIMING-080-PLAN.md '
        'declares offline public-boundary diagnosis, then a separately bounded/tested '
        'public-files-only diagnostic if needed; unexecuted. No MT5 click or log-saving '
        'step is requested. Keep033/035 clock/cost/coverage failures, consumed2025, '
        'reserved Nov–Dec2026/provider stops/old raw markers; eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=('Latest — 2026-10-08: native timing079 early rejection audited; read NATIVE-TIMING-079-RESULTS.md. '
        'One frozen078 invocation/exit1/preflight rejection/1979ms; zero dispatch/SDK reservation/runtime, '
        'SDK/guards/queries/samples0. Actual account guards not reached; cleanup inapplicable. '
        f'{EXPECTED} new audit tests pass;{RETAINED} unchanged preparation tests retained (not rerun); '
        'six injected cases/29-source closure rechecked. Exact public cause and native timing unknown; '
        'process duration is not guard latency. No scripts/compiler/deploy/log/market/orders/grants; '
        'invocation consumed, authorization retained but retired, no retry/reuse. Separate079 closure; '
        '078/source/artifacts/old failures and data gates preserved. Next080 public-boundary diagnosis '
        'unexecuted; separate diagnostic declaration/tests/authority required. Sharing/publication/ACK/profit '
        'and070 cause unproven;10s/30s/250ms/033/035/reserved exclusions remain. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1
        path.write_text(s[:i]+'\n'+latest+s[i:]);b[n]=sha(path)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}
    final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        observed_outcome=observed(),new_audit_tests_passed=EXPECTED,tests_retained=RETAINED,
        retained_suite_rerun=False,next_plan_executed=False,authority_retired_for_future_invocation=True)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final)
    b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r)
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER) and c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert r['observed_outcome']==observed() and r['new_audit_tests_passed']==EXPECTED
    assert t['passed'] and t['tests_run']==EXPECTED and r['tests_retained']==RETAINED
    assert not r['retained_suite_rerun'] and not r['next_plan_executed']
    assert r['authority_retired_for_future_invocation'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(final),bindings_verified=len(b),archive_members_verified=members,
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),
        new_audit_tests_passed=EXPECTED,tests_retained=RETAINED,retained_suite_rerun=False,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,observed_outcome=observed()))
    print(json.dumps(dict(review_passed=True,new_audit_tests=EXPECTED,sdk_connections=0,bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,
         check=check,seal=seal,review=review)[p.parse_args().action]()
