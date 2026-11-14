"""Separate offline audit/closure of the already completed081 observation."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-timing-081.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='native-timing-082';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/native-timing-081-final-source.json'
REVIEW=ROOT/'reports/native-timing-081-completion-review.json'
AUTH=ROOT/'reports/native-timing-081-authorization.json'
PUBLIC=ROOT/'reports/native-timing-081-public-outcome.json'
RUNTIME=ROOT/'reports/native-timing-081-runtime.json'
START=ROOT/f'reports/{PREFIX}-invocation-started.json'
OUTCOME=ROOT/f'reports/{PREFIX}-invocation-outcome.json'
DECLARATION=ROOT/'docs/NATIVE-TIMING-082-AUDIT.md'
PLAN=ROOT/'docs/NATIVE-TIMING-083-PLAN.md'
OWN=('scripts/native-timing-082.py','src/forex_demo_lab/timing_observation_082.py',
    'tests/test_timing_observation_082.py','docs/NATIVE-TIMING-082-AUDIT.md',
    'docs/NATIVE-TIMING-083-PLAN.md')
EXPECTED,RETAINED=32,1604
RAW=dict(invocation='reports/native-timing-081-invocation-started.json',
    dispatch='reports/native-timing-081-dispatch-started.json',
    component='reports/native-timing-081-sdk-reservation.json')
UNC=PureWindowsPath(r'\\wsl.localhost\Ubuntu\home\lx_singw\projects\forex-demo-lab')


def public_record(path):
    # Existing seals plus bounded ASCII/unique-key parsing; do not normalize bytes.
    from forex_demo_lab.clock_observer_042 import unique_pairs
    from forex_demo_lab.public_preflight_080 import verify_sidecar080
    sealed(path);raw=path.read_bytes();assert 0<len(raw)<=524288
    side=path.with_suffix('.sha256').read_bytes();assert len(side)<=66
    verify_sidecar080(side,raw)
    return json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)


def expected_metrics(l):
    # UNC parents + before/after lstat + two descriptor fstats per read.
    paths=(API['LEDGER'],ROOT/'reports/native-timing-081-checks.json',PRIOR,
        REVIEW,API['PROFILE'],AUTH)
    records=[p for path in paths for p in (path,path.with_suffix('.sha256'))]
    rs=sum(len((UNC/p.relative_to(ROOT).as_posix()).parents)+4 for p in records)
    sources=l['runtime_sources'];launcher=bound(l['helper_chain']['launcher'])
    windows_launcher=PureWindowsPath('C:/'+str(launcher).removeprefix('/mnt/c/'))
    ss=sum(len((UNC/n).parents)+4 for n in sources)+len(windows_launcher.parents)+4
    metrics=dict(public_record_reads=len(records),
        public_record_bytes=sum(p.stat().st_size for p in records),
        public_record_stats=rs,public_source_reads=len(sources)+1,
        public_source_bytes=sum((ROOT/n).stat().st_size for n in sources)+launcher.stat().st_size,
        public_source_stats=ss,steps=2+5*4+3+4+2*len(sources)+2+1)
    size=lambda n:bound(n).stat().st_size
    p=l['helper_chain'];assert len(p['images'])==1
    t,e,a=(size(l[k]) for k in ('terminal_name','editor_name','artifact_name'))
    h=sum(size(n) for n in p['images']);lc,cc,dc=(size(p[k]) for k in ('launcher','config','library'))
    sdk=sum(size(n) for n in l['sdk_bindings'])
    mql=sum(size(n) for n in l['build_record']['input_bindings'])
    guard=2*t+e+2*h+a
    sample=2*guard+sdk+lc+cc+dc+h+mql
    bootstrap=2*sdk+mql+a+4*t+e+3*h+lc+cc+dc
    return metrics,sample,bootstrap


def observed():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.timing_observation_082 import audit_observation082
    l=sealed(API['LEDGER']);spec,expected=API['spec_and_auth'](l,sha(PRIOR))
    sealed(AUTH);metrics,sample,bootstrap=expected_metrics(l)
    return audit_observation082(AUTH.read_bytes(),expected,sha(AUTH),spec.component_raw,
        {k:(ROOT/n).read_bytes() for k,n in RAW.items()},
        {k:(ROOT/n).with_suffix('.sha256').exists() for k,n in RAW.items()},
        public_record(START),public_record(OUTCOME),sha(START),
        l['runtime_bindings'][l['helper_chain']['launcher']],
        public_record(PUBLIC),public_record(RUNTIME),
        sha(ROOT/'reports/native-timing-081-checks.json'),sha(REVIEW),sha(PUBLIC),
        metrics,sample,bootstrap)


def retained_checks():
    review=sealed(REVIEW);prior=sealed(PRIOR)
    assert sha(PRIOR)=='3f40809cdbf92f2f1332c677391c8e3f87221d6fb3bee0c178c57dc28db38ab1'
    assert review['review_passed'] and review['frozen_input_coverage_complete']
    assert review['final_source_sha256']==sha(PRIOR)
    assert (review['tests_passed'],review['bindings_verified'],review['archive_members_verified'])==(1604,2530,2336)
    assert (review['runtime_sources_verified'],review['entry_cases_verified'],review['public_cases_verified'])==(31,6,4)
    assert review['next_plan_sha256']==sha(API['PLAN']) and not review['next_plan_executed']
    assert ARCHIVE(PRIOR,prior)==2336
    t=sealed(ROOT/'reports/native-timing-081-tests.json')
    c=sealed(ROOT/'reports/native-timing-081-checks.json')
    e=sealed(ROOT/'reports/native-timing-081-evidence.json')
    assert t['passed'] and t['tests_run']==RETAINED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert c['checker_passed'] and c['tests_sha256']==sha(ROOT/'reports/native-timing-081-tests.json')
    assert c['evidence_sha256']==sha(ROOT/'reports/native-timing-081-evidence.json')
    assert c['derivation']==API['derivation']()
    assert set(e['entry_cases'])==set(API['CASES']) and set(e['public_cases'])==set(API['PUBLIC_CASES'])
    assert sum(row['result']['entry_completed'] for row in e['entry_cases'].values())==1
    assert sum(row['result']['completed'] for row in e['public_cases'].values())==1
    references={
        'success':(126,8,89,1,None), 'real':(28,1,3,1,'profile_samples'),
        'sdk_changed':(2,0,0,0,'preflight'), 'initialize_failed':(24,0,0,1,'sdk_attach'),
        'signature_failed':(12,0,0,0,'signature'), 'initialize_interrupted':(24,0,0,1,'sdk_attach')}
    for name,(hashes,guards,queries,sdk,stage) in references.items():
        row=e['entry_cases'][name];r=row['result'];counts=r['counts']
        assert row['dependencies_injected'] and r['entry_completed']==(name=='success')
        assert (counts['hash_reads'],counts['guards'],counts['sdk_queries'],counts['sdk_connections'],r['stopped_stage'])==(hashes,guards,queries,sdk,stage)
        assert not r['orders_available']
    public_refs={'windows_crlf':(True,12,120,3,30,None,None,None),
        'oversized_profile':(False,10,97,0,0,'helper_profile','sidecar_bytes','file_rejected'),
        'changed_source':(False,12,120,2,21,'source','source_digest','binding_rejected'),
        'stale_authority':(False,12,120,0,0,'authorization','validate','authorization_rejected')}
    for name,expected in public_refs.items():
        row=e['public_cases'][name];r=row['result']
        assert row['dependencies_injected'] and not row['windows_metadata_measured']
        assert tuple(r[k] for k in ('completed','public_record_reads','public_record_stats',
            'public_source_reads','public_source_stats','stopped_stage','stopped_operation','stop_reason'))==expected
        assert r['sdk_connections']==r['sdk_queries']==0 and not r['owned_cleanup_applicable']
    for k,v in {**API['ZERO'],**API['FALSE']}.items():assert type(review[k]) is type(v) and review[k]==v
    return review


def freeze():
    API['verify']();retained_checks();r=observed();p=sealed(PRIOR)
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        REVIEW,REVIEW.with_suffix('.sha256'),AUTH,AUTH.with_suffix('.sha256'),
        PUBLIC,PUBLIC.with_suffix('.sha256'),RUNTIME,RUNTIME.with_suffix('.sha256'),
        START,START.with_suffix('.sha256'),OUTCOME,OUTCOME.with_suffix('.sha256'),
        *(ROOT/n for n in RAW.values())):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    write(LEDGER,dict(bindings=b,preparation_sha256=sha(PRIOR),
        declaration_sha256=sha(DECLARATION),next_plan_sha256=sha(PLAN),
        prior_bindings_verified=2530,prior_archive_members_verified=2336,
        tests_retained=RETAINED,expected_new_tests=EXPECTED,maximum_new_test_runs=1,
        maximum_new_native_invocations=0,observed_native_entry_invocations=1,
        raw_marker_paths=RAW,authority_retired_for_future_invocation=True,
        observed_outcome=r))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),new_audit_tests=EXPECTED)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['preparation_sha256']==sha(PRIOR) and l['declaration_sha256']==sha(DECLARATION)
    assert l['next_plan_sha256']==sha(PLAN) and l['raw_marker_paths']==RAW
    assert l['observed_outcome']==observed()
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(test_run_consumed=True,
        ledger_sha256=sha(LEDGER),maximum_new_native_invocations=0))
    start=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_timing_observation_082.py')
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
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(**r,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),new_audit_tests_passed=EXPECTED,
        tests_retained=RETAINED,retained_suite_rerun=False,
        started_record_sha256=sha(START),outcome_record_sha256=sha(OUTCOME),
        public_record_sha256=sha(PUBLIC),native_record_sha256=sha(RUNTIME),
        public_metrics_independently_verified=expected_metrics(sealed(API['LEDGER']))[0],
        source_import_closure_retained=31,independent_entry_cases_retained=6,
        independent_public_models_retained=4))
    print(json.dumps(dict(audit_passed=True,samples_completed=4,guards=8,sdk_connections=1)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/NATIVE-TIMING-082-RESULTS.md'
    text=('# Native metadata observation082 results\n\n'
        'The corrected081 probe completed on2026-10-08: four fixed metadata composites, '
        'eight full actual-DEMO/USD/connected/Algooff account/private identity guards, '
        'one SDK connection and shutdown, confirmed handle/allocation cleanup. '
        'Signed images, SDK/helper chain, source/build and exact raw one-use markers verified. '
        'CLI exit0; process elapsed23096ms. No orders, quotes/history, scripts, deployment, '
        'compiler, terminal-log content or receipt permissions. The081 invocation/dispatch/'
        'component are spent, authority retained but retired; no retry/reset/refund/reuse.\n\n'
        '| Sample | Guard 1 (ms) | Guard 2 (ms) | Composite (ms) |\n'
        '| --- | ---: | ---: | ---: |\n'
        '| 1 | 1138 | 1156 | 2521 |\n| 2 | 1264 | 1217 | 2689 |\n'
        '| 3 | 1220 | 1444 | 2885 |\n| 4 | 1611 | 1279 | 3174 |\n\n'
        '126 hash reads/3791254545 bytes and89 SDK metadata queries independently reconciled '
        'with26 bootstrap hashes/664015205 bytes plus four25-hash/781809835-byte composites; '
        'one metadata query plus eight11-query guards. Public preflight12 reads/659045 bytes/'
        '120 stats and32 source reads/516466 bytes/350 stats/94 steps also match original '
        'record/source sizes and Windows path arithmetic. Caps held. Public report correctly '
        'predates native work, so its account/SDK/backend/cleanup flags are false/zero. '
        'Frozen077 observation flags runtime_authorized/native_timing_verified remain false; '
        '082 separately verifies the completed metadata observation without granting launch authority.\n\n'
        'The external CLI capture omitted sample count because its PowerShell Int32 filter '
        'excluded the parsed Int64. Capture preserved unchanged; the sealed native runtime '
        'provides the four-sample count. No missing counter is invented.\n\n'
        f'{EXPECTED} new offline audit tests passed, zero failures/errors/skips; '
        f'{RETAINED} preparation tests/60 new retained without rerun. Six injected core cases, '
        'four public models,31-source closure and unchanged derivation checked against081 seals. '
        'Exact schemas/redaction, pins, raw markers without fabricated sidecars, timestamps, '
        'stage order, caps, query/hash/sample arithmetic, maxima and cleanup audited. '
        '082 source/evidence closure is separate from immutable081 preparation.\n\n'
        'Guard observations range1.138–1.611s. Using1611ms repeatedly in unchanged076 '
        'completion formula16*g+u+c+5000+6*n+o+w yields30776ms even with all other overheads '
        'zero;45776ms with retained15000ms wait overshoot;47382ms with earlier illustrative '
        'overheads. Each exceeds strict29750ms completion threshold. These are hypothetical '
        'repeat-maximum scenarios, not measured MQL critical paths or worst-case bounds. '
        'Current30s sharing feasibility is unestablished;10s/30s/250ms and full guards retained.\n\n'
        'Next NATIVE-TIMING-083-PLAN.md: offline bounded readiness/release synchronization '
        'integration with fresh source/phase/date/private handle/signal/clock/IO/polling proof '
        'and tests before separate compilation/runtime review. Unexecuted; no UI/log-saving '
        'step requested. Native sharing/publication/ACK,070 cause and profitable edge remain '
        'unproven. Keep033/035 failures/clock/cost/coverage/consumed2025/reserved Nov–Dec2026/'
        'provider stops/old grants/artifacts/raw markers; eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=(f'Latest — 2026-10-08: native metadata observation082 audited; read NATIVE-TIMING-082-RESULTS.md. '
        'One corrected081 invocation/exit0/23096ms,4 composites/8 actual-DEMO guards,SDK1/shutdown1/'
        'queries89,126 hashes/3791254545 bytes; owned cleanup confirmed. Observed guard1.138–1.611s/'
        'composite max3174ms; maxima not bounds. Repeat1611ms in076 sixteen-guard formula gives '
        '30776ms with all other overheads zero, exceeding29750ms.30s sharing feasibility unestablished; '
        '10s/30s/250ms and guards retained. Public counts/raw markers/pins/stages/timings/cleanup audited; '
        f'{EXPECTED} new tests pass;{RETAINED} preparation tests retained, no rerun. External sample-count '
        'capture omission preserved; runtime supplies4. Zero scripts/compiler/deploy/log/market/orders/receipts; '
        '081 authority/markers spent and retired, no retry/reuse. Separate082 closure; all old failures retained. '
        'Next083 offline bounded synchronization/source/phase/date/private signal/handle/clock/IO/polling '
        'integration/tests unexecuted. Sharing/publication/ACK/profit/070 cause and eligibility/orders remain '
        'unproven/false;033/035/reserved gates preserved. Earlier entries historical.\n\n')
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
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert r['observed_outcome']==observed() and r['new_audit_tests_passed']==EXPECTED
    assert t['passed'] and t['tests_run']==EXPECTED and r['tests_retained']==RETAINED
    assert not r['retained_suite_rerun'] and not r['next_plan_executed']
    assert r['authority_retired_for_future_invocation'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(final),bindings_verified=len(b),archive_members_verified=members,
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),
        new_audit_tests_passed=EXPECTED,tests_retained=RETAINED,retained_suite_rerun=False,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,observed_outcome=observed()))
    print(json.dumps(dict(review_passed=True,new_audit_tests=EXPECTED,bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,
         check=check,seal=seal,review=review)[p.parse_args().action]()
