"""Offline freeze/test/injected-evidence/check/seal/review only."""
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
API=runpy.run_path(str(ROOT/'scripts/synchronization-083-r2.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
ZERO,FALSE=API['ZERO'],API['FALSE']
PREFIX='synchronization-084';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/synchronization-083-r2-final-source.json'
REVIEW=ROOT/'reports/synchronization-083-r2-completion-review.json'
PRIOR_PLAN=ROOT/'docs/SYNCHRONIZATION-084-R2-PLAN.md'
DESIGN=ROOT/'docs/SYNCHRONIZATION-084-DESIGN.md'
POLICY=ROOT/'docs/SYNCHRONIZATION-084-POLICY.md'
PLAN=ROOT/'docs/SYNCHRONIZATION-085-PLAN.md'
OWN=('scripts/synchronization-084.py','src/forex_demo_lab/synchronization_084.py',
    'tests/test_synchronization_084.py','mt5/Scripts/ForexDemoSynchronization084.mq5',
    'mt5/Scripts/SynchronizationWire084.mqh','docs/SYNCHRONIZATION-084-DESIGN.md',
    'docs/SYNCHRONIZATION-084-POLICY.md','docs/SYNCHRONIZATION-085-PLAN.md')
EXPECTED,NEW,RETAINED=1718,36,1682
CASES=dict(normal={},small_guard={'guard_ms':50},observed_guard={'guard_ms':1611},
    stale={'stale_ms':1},changed_magic={'tamper':0},changed_identity={'replace_signal':True},
    pipe_acl={'pipe_acl':True},wrong_error={'control_error':5},launch_late={'launch_ms':10001},
    blocked_return={'blocked_ms':30000},cleanup_failure={'close_fail':True},
    interrupted={'factory_interrupt':True},changed_account={'bad_guard_at':21,'bad_guard':{'same_account':False}},
    default_off={'enabled':False})


def proposal():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.synchronization_084 import source_contract084
    return source_contract084(ROOT)


def retained_checks():
    API['verify']();API['retained_checks']()
    r,p=sealed(REVIEW),sealed(PRIOR)
    assert sha(PRIOR)=='68f04f9fbdfe8f3d4a5bca60adc765cb9d65f4def8346024e2f751b34b421f3d'
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert (r['bindings_verified'],r['archive_members_verified'],r['tests_passed'],r['new_tests'])==(2606,2407,1682,46)
    assert r['active_suite'] and r['retired_prototype_tests']==43 and r['model_cases_verified']==14
    assert r['portable_header_comparisons']==34 and r['next_plan_sha256']==sha(PRIOR_PLAN)
    assert not r['next_plan_executed'] and ARCHIVE(PRIOR,p)==2407
    for n,h in p['source_and_evidence_bindings'].items():
        if n not in HANDOFF: assert sha(bound(n))==h,n
    return r


def freeze():
    retained_checks();p=sealed(PRIOR);b=dict(p['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256')):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        proposal=prop,expected_tests=EXPECTED,new_tests=NEW,retained_tests=RETAINED,
        prior_bindings_verified=2606,prior_archive_members_verified=2407,maximum_full_regressions=1,
        evidence_cases=CASES,maximum_evidence_cases=14,portable_codec_decisions=18,
        portable_encoder_comparisons=1,retained_window_comparisons=34,
        development_tests_passed_before_final_refinements=34,**ZERO,**FALSE))
    archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(archive),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),source_inputs=len(prop['input_bindings']),expected_tests=EXPECTED)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    for k,p in (('prior_source_sha256',PRIOR),('prior_plan_sha256',PRIOR_PLAN),
        ('design_sha256',DESIGN),('policy_sha256',POLICY),('next_plan_sha256',PLAN)):assert l[k]==sha(p)
    assert l['proposal']==proposal() and l['evidence_cases']==CASES
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic();suite,retired=API['active_suite']();assert suite.countTestCases()==EXPECTED
    r=unittest.TextTestRunner(verbosity=1).run(suite)
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failed_test_names=[str(t) for t,d in r.failures+r.errors],elapsed_seconds=time.monotonic()-start,
        ledger_sha256=sha(LEDGER),active_suite=True,retired_prototype_tests=retired,
        portable_codec_decisions=18,portable_encoder_comparisons=1,retained_window_comparisons=34,**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def model_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from test_synchronization_084 import run084_case
    c,b,clock,state,ok,match,failure=run084_case(**CASES[name])
    guards=[t for t in c.trace if t[0]=='guard']
    from dataclasses import asdict
    return dict(modeled_completed=ok,match=match,first_failure=failure,summary=c.summary(),
        factories=state['factories'],full_guards=state['guards'],guard_spans=[dict(start=a-100000,end=z-100000) for _,a,z in guards],
        backend_model_handles_remaining=len(b.handles),model_finish_calls=b.finish_calls,
        model_close_attempts=len(b.closed),model_release_calls=b.releases,
        all_lease_closes_attempted=all(l.closed for l in c.leases),guard_cap=256,
        source_artifact_episode_bound=True,private_identifiers_exported=False,
        probes=[asdict(p) for p in c.probes],publication_count=len(b.publications),
        frames=[dict(kind=kind,sequence=s.sequence,issued_offset_ms=s.issued-100000,
            request_completed_offset_ms=request-100000,validated_offset_ms=after-100000,
            original_frame_sha256=hashlib.sha256(s.raw).hexdigest()) for kind,s,request,after in c.frames],
        elapsed_ms=clock.boot-100000,dependencies_injected=True,**ZERO,**FALSE)


def evidence():
    verify();write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(model_cases_consumed=True,
        ledger_sha256=sha(LEDGER),maximum_model_cases=14,**ZERO,**FALSE))
    rows={n:model_case(n) for n in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    print(json.dumps(dict(model_cases=14,modeled_completions=sum(x['modeled_completed'] for x in rows.values()))))


def check():
    l=verify();retained_checks()
    t,e=(sealed(ROOT/f'reports/{PREFIX}-{n}.json') for n in ('tests','evidence'))
    assert t['passed'] and t['tests_run']==EXPECTED and t['new_tests']==NEW
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0) and t['active_suite'] and t['retired_prototype_tests']==43
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and set(e['cases'])==set(CASES)
    for name,row in e['cases'].items():
        complete=name in ('normal','small_guard');s=row['summary']
        assert row['modeled_completed']==complete and row['dependencies_injected']
        assert row['backend_model_handles_remaining']==0 and row['model_release_calls']<=1
        assert row['full_guards']==len(row['guard_spans'])<=256
        for k,cap in l['proposal']['caps'].items():assert type(s['counts'][k]) is int and 0<=s['counts'][k]<=cap
        for k,v in {**ZERO,**FALSE}.items():assert type(row[k]) is type(v) and row[k]==v
        if name=='default_off':
            assert row['factories']==row['full_guards']==row['model_finish_calls']==row['publication_count']==0
            assert not s['release_spent'] and s['cleanup_confirmed'] is None and row['first_failure'] is None
            continue
        assert row['model_finish_calls']==1 and s['counts']['cleanup']==1
        if complete:
            assert row['match']['modeled_match'] and row['first_failure'] is None and s['cleanup_confirmed']
            assert row['elapsed_ms']<120000 and row['model_release_calls']==1 and row['publication_count']==3
            assert row['all_lease_closes_attempted'] and len(row['frames'])==4
            assert [p['error'] for p in row['probes']]==[0,0,32,32,0,0]
            assert all(p['companion_blockers']==0 for p in row['probes'])
            assert all(f['request_completed_offset_ms']<=f['issued_offset_ms']<=f['validated_offset_ms']<=f['issued_offset_ms']+2000 for f in row['frames'])
        else: assert row['first_failure'] is not None
        if name=='observed_guard':
            assert not s['release_spent'] and row['model_release_calls']==0
            assert all(g['end']-g['start']==1611 for g in row['guard_spans'])
        if name=='cleanup_failure':assert not s['cleanup_confirmed'] and s['unconfirmed_handles']>0
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(archive)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,modeled_completions=2,modeled_rejections=11,
        default_off_cases=1,portable_codec_decisions=18,portable_encoder_comparisons=1,
        retained_window_comparisons=34,concrete_observed_guard_scenario_rejected=True,
        complete_source_inputs_verified=len(l['proposal']['input_bindings']),**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,model_cases=14)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    result=ROOT/'docs/SYNCHRONIZATION-084-RESULTS.md'
    text=(f'# Synchronization084 source and interfaces results\n\n{EXPECTED} active tests/{NEW} new passed with zero failures/errors/skips. '
        '18 portable frame decisions and one exact144-byte encoder comparison agree;34 previous window comparisons remain. '
        '14 injected cases:2 completions,11 rejections,1 default-off. The full suite inherits083 R2 active_suite(); '
        'the original1679-test fixture failure and43 retired tests remain unchanged, with46 corrected tests active.\n\n'
        'Fresh default-off MQL reader/codec, typed private companion/backend interface, exact peer-byte decoder, strict '
        'parser/matcher and complete source/import/include/build-schema bindings are prepared. Source is uncompiled/undeployed; '
        'there is no native backend or runtime authority. No SDK/native/MT5/MetaEditor/deploy/terminal-log/market/orders/receipt grant. '
        'The34-test development check before final refinements also passed; final frozen evidence is the full suite above.\n\n'
        'Responses bind source contract, future candidate artifact, episode and fresh request sequence. Original peer timestamps '
        'must follow completed request production; publication never rewrites them. Raw ACL/owner/ACE/path/link/ancestor/root/file '
        'facts, CREATE_NEW immutable slots, READ/share-READ held response boundaries, same synthetic identity, zero helper '
        'synthetic blockers and independent write/delete error32 are checked through injected interfaces. Cleanup ownership '
        'exists before factory entry; interruption, replacement, stale frames, account change, launch/IO overrun and uncertain '
        'close reject, with no retries or allowance refunds. These facts are models, not actual Windows security evidence.\n\n'
        f'The zero-cost model uses{e["cases"]["normal"]["full_guards"]} full guards; the50ms scenario completes in'
        f'{e["cases"]["small_guard"]["elapsed_ms"]}ms. Applying082\'s observed1611ms to every guard rejects before release: '
        'additional concrete file publication guards exhaust the unchanged2s response freshness window. The earlier083 abstract '
        '24515ms critical result does not carry over. The finite guard cap is explicitly256;2s freshness/10s start/30–31s close/'
        '250ms margins/60s episode/120s whole limits remain unchanged. Observations and scenarios are not native bounds.\n\n'
        'MQL named-pipe reads/flushes may block, and timely close depends on receiving the closed challenge. Clock checks after '
        'return do not preempt those calls or guarantee a maximum physical hold. Candidate compilation requires a separate '
        'reviewed exact-exit1/clean-summary source-bound policy. Next085 explicitly redesigns/reviews the response boundary and '
        'blocking behavior before native admission; it remains unexecuted. No MT5 UI action is requested.\n\n'
        '082 metadata success, spent081 authority/raw markers,075 historical artifact and every older failure remain preserved. '
        'Native sharing/publication/ACK,070 cause and profitable edge remain unproven.033/035/data clocks/cost/coverage/'
        'consumed2025/reserved Nov–Dec2026/provider exclusions remain; eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=(f'Latest — 2026-10-08: synchronization084 source/private interfaces sealed; read SYNCHRONIZATION-084-RESULTS.md. '
        f'{EXPECTED} active tests/{NEW} new pass;18 portable codec decisions/one exact encoder comparison plus34 retained windows. '
        '14 injected cases:2 complete/11 reject/1 default-off. Fresh default-off MQL reader/codec, typed owner/ACL/ACE/ancestor/'
        'file/pipe/spec/held-boundary interfaces, original-peer-timestamp decoder and strict six-probe/four-frame matcher prepared. '
        'Complete import/include graph and actual-exit1 candidate build schema bound; uncompiled/undeployed/no native backend. '
        'Concrete1611ms guard scenario rejects stale publication before release;083 abstract timing success does not carry over. '
        'Explicit256 guard cap, unchanged2s/10s/30–31s/250ms/60s/120s time limits. Blocking pipe reads/flushes/timely close remain '
        'unproven; no native timing bounds. Zero new SDK/native/MT5/compiler/deploy/log/market/orders/grants. Original083 fixture '
        'failure/R2 active_suite/082 success/spent081/075 artifact retained. Next085 explicit response-boundary/blocking redesign '
        'and build preparation unexecuted. Sharing/publication/ACK/profit/070 cause and eligibility/orders unproven/false; all '
        '033/035/data/reserved/provider gates preserved. Earlier entries historical.\n\n')
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
        tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,active_suite=True,
        retired_prototype_tests=43,complete_source_inputs_verified=len(l['proposal']['input_bindings']),
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
    assert t['passed'] and t['tests_run']==r['tests_passed']==EXPECTED
    assert not r['future_plan_executed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,model_cases_verified=14,
        active_suite=True,retired_prototype_tests=43,complete_source_inputs_verified=len(l['proposal']['input_bindings']),
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests_passed=EXPECTED,bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,
        evidence=evidence,check=check,seal=seal,review=review)[p.parse_args().action]()
