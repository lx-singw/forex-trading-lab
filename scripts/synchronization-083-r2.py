"""Freeze/test/model/check/review only; no native authorization or execution."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/synchronization-083.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='synchronization-083-r2';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/native-timing-082-final-source.json'
REVIEW=ROOT/'reports/native-timing-082-completion-review.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-TIMING-083-PLAN.md'
DESIGN=ROOT/'docs/SYNCHRONIZATION-083-R2-DESIGN.md'
POLICY=DESIGN
PLAN=ROOT/'docs/SYNCHRONIZATION-084-R2-PLAN.md'
OWN=('scripts/synchronization-083-r2.py','tests/test_synchronization_083_r2.py',
    'docs/SYNCHRONIZATION-083-R2-DESIGN.md','docs/SYNCHRONIZATION-084-R2-PLAN.md')
EXPECTED,NEW,RETAINED=1682,46,1636
CASES={**API['CASES'],'changed_magic':{'wire_change':0}}
ORIGINAL_REPORTS=tuple(ROOT/n for n in (
    'reports/synchronization-083-ledger.json','reports/synchronization-083-ledger.sha256',
    'reports/synchronization-083-initial-source.json','reports/synchronization-083-initial-source.sha256',
    'reports/synchronization-083-initial-source.zip',
    'reports/synchronization-083-tests-started.json','reports/synchronization-083-tests-started.sha256',
    'reports/synchronization-083-tests.json','reports/synchronization-083-tests.sha256'))
ZERO=dict(native_invocations=0,sdk_connections=0,mt5_runtime_invocations=0,
    native_metatrader_compiler_invocations=0,terminal_deployments=0,
    terminal_log_content_reads=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(native_protocol_implemented=False,native_mql_verified=False,
    native_publication_verified=False,native_launch_ready=False,latency_guaranteed=False,
    runtime_authorized=False,orders_available=False,fresh_performance_eligible=False,
    annual_eligible=False,old070_cause_proven=False)


def retained_checks():
    r=API['retained_checks']()
    t=sealed(ROOT/'reports/synchronization-083-tests.json')
    assert not t['passed'] and t['tests_run']==1679
    assert (t['failures'],t['errors'],t['skipped'])==(1,0,0)
    assert len(t['failed_test_names'])==1
    assert 'test_source_build_phase_episode_sequence_and_padding_changes_rejected' in t['failed_test_names'][0]
    assert 'offset=0' in t['failed_test_names'][0]
    assert t['ledger_sha256']==sha(API['LEDGER'])
    for suffix in ('evidence-started.json','evidence.json','checks.json','final-source.json','completion-review.json'):
        assert not (ROOT/('reports/synchronization-083-'+suffix)).exists()
    return r


def active_suite():
    # Immutable retired fixture remains evidence; do not execute its faulty test.
    loader=unittest.defaultTestLoader
    all_tests=loader.discover(str(ROOT/'tests'))
    def leaves(suite):
        for item in suite:
            if isinstance(item,unittest.TestSuite):yield from leaves(item)
            else:yield item
    kept=[];retired=[]
    for test in leaves(all_tests):
        (retired if type(test).__module__=='test_synchronization_083' else kept).append(test)
    assert len(retired)==43
    return unittest.TestSuite(kept),len(retired)


def proposal():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.synchronization_083 import source_contract083,SOURCE_INPUTS
    return source_contract083({n:sha(ROOT/n) for n in SOURCE_INPUTS})


def freeze():
    API['verify']();retained_checks();p=sealed(PRIOR)
    b=dict(sealed(API['LEDGER'])['bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    for n in HANDOFF:b.pop(n,None)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),*ORIGINAL_REPORTS):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        proposal=proposal(),expected_tests=EXPECTED,new_tests=NEW,retained_tests=RETAINED,
        prior_bindings_verified=2565,prior_archive_members_verified=2369,
        maximum_full_regressions=1,evidence_cases=CASES,maximum_evidence_cases=14,
        portable_header_comparisons=34,retired_prototype_tests=43,original_failed_tests_sha256=sha(ROOT/'reports/synchronization-083-tests.json'),**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    for k,p in (('prior_source_sha256',PRIOR),('prior_plan_sha256',PRIOR_PLAN),
        ('design_sha256',DESIGN),('policy_sha256',POLICY),('next_plan_sha256',PLAN)):
        assert l[k]==sha(p)
    assert l['proposal']==proposal() and l['evidence_cases']==CASES
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic();suite,retired=active_suite();assert suite.countTestCases()==EXPECTED
    r=unittest.TextTestRunner(verbosity=1).run(suite)
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failed_test_names=[str(t) for t,d in r.failures+r.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),
        portable_header_comparisons=34,retired_prototype_tests=retired,active_suite=True,**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def model_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from forex_demo_lab.synchronization_083 import Bindings083,encoded076
    from test_synchronization_083_r2 import fixture083_r2
    config=dict(CASES[name]);enabled=config.pop('enabled',True)
    if 'bad_proof_operation' in config:config['bad_proof_operation']=tuple(config['bad_proof_operation'])
    with TemporaryDirectory() as d:
        p=proposal();source=hashlib.sha256(encoded076(p)).hexdigest()
        b=Bindings083(source,'b73158599f38b39d3802d95b2badc11a441368cdc004d2b48c75e4e06d6003e4',
            sha(ROOT/'reports/helper-profile-068.json'),sha(POLICY),
            (500123987,2,3),(700789321,4,5))
        f=fixture083_r2(Path(d)/'marker',bindings=b,**config);r=f.model.run(enabled)
        raw=f.model.path.read_bytes() if f.model.path.exists() else None
        marker=json.loads(raw) if raw else None
        assert raw is None or raw==encoded076(marker)
        return dict(result=r,dependencies_injected=True,model_peer_cleanup_calls=f.peer.cleanup_calls,
            all_model_leases_closed=all(x.closed for x in f.peer.leases),
            model_release_calls=f.peer.release_calls,model_factories=f.state.factories,
            reservation=marker,reservation_sha256=hashlib.sha256(raw).hexdigest() if raw else None)


def evidence():
    verify()
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(model_cases_consumed=True,
        ledger_sha256=sha(LEDGER),maximum_model_cases=14,**ZERO,**FALSE))
    rows={n:model_case(n) for n in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,
        ledger_sha256=sha(LEDGER),dependencies_injected=True,**ZERO,**FALSE))
    print(json.dumps(dict(model_cases=14,modeled_completions=sum(x['result']['modeled_completed'] for x in rows.values()),native_invocations=0)))


def check():
    l=verify();retained_checks()
    from forex_demo_lab.synchronization_083 import LIMITS,encoded076
    t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['new_tests']==NEW
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and set(e['cases'])==set(CASES)
    critical_max=None
    for name,row in e['cases'].items():
        r=row['result'];expected_complete=name in ('normal','observed_guard','pending')
        assert r['modeled_completed']==expected_complete and row['dependencies_injected']
        assert row['all_model_leases_closed'] and row['model_release_calls']<=1
        assert set(r['counts'])==set(LIMITS)
        for k,cap in LIMITS.items():assert type(r['counts'][k]) is int and 0<=r['counts'][k]<=cap
        for k,v in {**ZERO,**FALSE}.items():
            if k in r:assert type(r[k]) is type(v) and r[k]==v
        if name=='default_off':
            assert row['reservation'] is None and row['model_factories']==row['model_peer_cleanup_calls']==0
            assert not r['release_spent'] and r['counts']['guards']==0
            continue
        assert row['reservation_sha256']==hashlib.sha256(encoded076(row['reservation'])).hexdigest()
        marker=row['reservation']
        assert marker['source_sha256']==hashlib.sha256(encoded076(proposal())).hexdigest()
        assert marker['policy_sha256']==sha(POLICY) and marker['limits']==LIMITS
        assert marker['execution_authorized'] is False and marker['orders_available'] is False
        assert row['model_peer_cleanup_calls'] in (0,1)
        if expected_complete:
            assert row['model_peer_cleanup_calls']==1 and r['cleanup_confirmed']
            assert r['first_failure'] is None and r['outer_elapsed_ms']<120000 and r['episode_elapsed_ms']<60000
            assert r['release_spent'] and row['model_release_calls']==1
            assert len(r['probes'])==6
            assert [(p['stage'],p['access']) for p in r['probes']]==[(s,a) for s in ('pre','independent','post') for a in ('write','delete')]
            guards=[v for v in r['trace'] if v['operation'].endswith('_guard')]
            assert r['counts']['guards']==len(guards)
            for v in r['trace']:
                assert v['elapsed_ms']==v['end_boot_offset_ms']-v['start_boot_offset_ms']>=0
            operations=[v for v in r['trace'] if not v['operation'].endswith('_guard')]
            assert r['counts']['operations']==len(operations)
            critical=[v for v in guards if v['operation'].startswith('independent_')]
            assert len(critical)==12
            assert all(v['end_boot_offset_ms']<r['hold_start_offset_ms']+29750 for v in critical)
            assert 0<=r['hold_start_offset_ms']-r['release_offset_ms']<=10000
            assert 30000<=r['hold_end_offset_ms']-r['hold_start_offset_ms']<=31000
            for p in r['probes']:
                assert p['companion_blockers']==0 and p['full_guards_before_after'] and p['same_file_before_after']
                if p['stage']=='pre':assert p['error']==0 and p['end_boot_offset_ms']<r['hold_start_offset_ms']-250
                elif p['stage']=='post':assert p['error']==0 and p['start_boot_offset_ms']>r['hold_end_offset_ms']+250
                else:assert p['error']==32 and r['hold_start_offset_ms']+250<p['start_boot_offset_ms']<=p['end_boot_offset_ms']<r['hold_start_offset_ms']+29750
            if name=='observed_guard':
                assert all(v['elapsed_ms']==1611 for v in guards)
                critical_max=max(v['end_boot_offset_ms'] for v in critical)-r['hold_start_offset_ms']
                assert critical_max<29750
        else:
            assert r['first_failure'] is not None
            assert row['model_peer_cleanup_calls']==1
    for record in (t,e):
        for k,v in {**ZERO,**FALSE}.items():assert type(record[k]) is type(v) and record[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,modeled_completions=3,
        modeled_rejections=10,default_off_cases=1,portable_header_comparisons=34,
        observed_guard_scenario_critical_completion_offset_ms=critical_max,
        critical_control_guards_verified=12,proposal=proposal(),**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,model_cases=14,critical_completion_ms=critical_max)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json');slow=e['cases']['observed_guard']['result']
    result=ROOT/'docs/SYNCHRONIZATION-083-R2-RESULTS.md'
    text=(f'# Offline synchronization083 R2 results\n\n{EXPECTED} tests/{NEW} new passed; zero failures/errors/skips. '
        '34 portable C++/pure-MQL header comparisons agree.14 fixed injected cases:3 completions,10 rejections,1 default-off. '
        'No SDK/native/MT5/compiler/deployment/terminal-log/market/orders/receipt grants. Models do not establish Windows '
        'security or native timing. New pure header/protocol source is uncompiled and has no runnable MQL reader.\n\n'
        'Fresh challenge-bound ready/release/holding/closed signals keep both full guards and exact144-byte boundaries, '
        'phase/source/build-reference/episode/sequence/clock bindings,2s freshness,10s start/30s hold/250ms margins. '
        'Preparation/pre controls precede the hold; the fixed5-second blind wait is explicitly replaced by a guarded '
        'fresh holding witness. All12 full guards around six independent metadata/open operations remain. '
        'Pre/post stamp/open/close/metadata guards and final guard retained. Guarded bounded hold-close wait uses '
        'the same before/after structure as071. Native challenge/ACL/transport and actual MQL implementation remain future work.\n\n'
        f'With the observed1611ms guard value used only as a scenario input, independent work including its trailing guards '
        f'finishes{c["observed_guard_scenario_critical_completion_offset_ms"]}ms after hold start, below strict29750ms. '
        f'The handshake episode completes in{slow["episode_elapsed_ms"]}ms (60s cap); whole model{slow["outer_elapsed_ms"]}ms '
        '(120s cap includes preparation and post controls). Those are simulated durations, not worst-case bounds or '
        'native admission. Slow2001ms guards reject on2s signal freshness. Stale/source/private identity/account changes, '
        'blocked-call return, wait overshoot, cleanup failure and interruption reject; leases/owner still receive cleanup.\n\n'
        'Pre-freeze zero-cost model exposed equality at strict pre/hold-start margins; explicit bounded margin waits '
        'were added before freezing. No frozen evidence was repaired. Exclusive reservation, spent release, no same-path '
        'restart, owner-before-factory cleanup and default-off paths tested. Private identifiers/episode are hashed in '
        'markers and absent from reports. Counts/guard spans/error32 and all pre/inside/post windows independently reconciled.\n\n'
        '082 native four-sample/eight-guard metadata success, spent081 authority/markers and every earlier failure remain '
        'unchanged.075 artifact is historical reference only; it cannot consume this protocol. Next '
        'SYNCHRONIZATION-084-R2-PLAN.md prepares fresh runnable MQL source and concrete private transport interfaces/decoder/'
        'matcher/tests before separate compilation/runtime phases. Unexecuted; no UI action requested. Native sharing/'
        'publication/ACK,070 cause and profitable edge remain unproven.033/035/data clock/cost/coverage/consumed2025/'
        'reserved Nov–Dec2026/provider exclusions preserved; eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=(f'Latest — 2026-10-08: offline synchronization083 R2 sealed; read SYNCHRONIZATION-083-R2-RESULTS.md. Original1679-test run had1 fixture failure (offset0 ignored), preserved; R2 corrects fixture only,43 retired tests replaced by46 active checks. Future full checks use active_suite(). '
        f'{EXPECTED} tests/{NEW} new/34 portable header comparisons pass;14 injected cases:3 completions/10 rejections/1 default-off. '
        'Fresh144-byte challenge ready/release/holding/closed model binds source/build-reference/episode/sequence/private '
        'identity and held boundary; full guards retained. Blind5s wait explicitly replaced;12 independent-control guards '
        f'remain. Observed1611ms scenario finishes critical work{c["observed_guard_scenario_critical_completion_offset_ms"]}ms '
        'after hold start, below29750ms; simulated, not bounds/native admission.2s freshness/10s start/30s hold/250ms margins '
        'retained;60s handshake/declared120s whole-model cap, bounded IO/poll/waits and owned cleanup tested. Slow/stale/'
        'replacement/account/overrun/cleanup/interruption reject. No native/SDK/MT5/compiler/deploy/log/market/orders/grants. '
        'Pure header/protocol uncompiled; actual Windows/MQL transport not implemented.082 success/old failures/spent081/'
        '075 reference preserved. Next084 fresh MQL source/private transport/decoder/matcher preparation/tests unexecuted. '
        'Sharing/publication/ACK/profit/070 cause unproven;033/035/reserved gates and eligibility/orders false. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+latest+s[i:]);b[n]=sha(path)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,portable_header_comparisons=34,active_suite=True,retired_prototype_tests=43,
        future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and r['tests_passed']==EXPECTED
    assert not r['future_plan_executed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(final),bindings_verified=len(b),archive_members_verified=members,
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),
        tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,portable_header_comparisons=34,active_suite=True,retired_prototype_tests=43,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,original_failed_tests_sha256=sha(ROOT/'reports/synchronization-083-tests.json'),**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests_passed=EXPECTED,bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,
        evidence=evidence,check=check,seal=seal,review=review)[p.parse_args().action]()
