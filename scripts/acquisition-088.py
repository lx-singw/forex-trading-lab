"""Exclusive offline review actions; no native authority or executable reader."""
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
API=runpy.run_path(str(ROOT/'scripts/bindings-087.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='acquisition-088';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/bindings-087-final-source.json'
REVIEW=ROOT/'reports/bindings-087-completion-review.json'
DESIGN=ROOT/'docs/ACQUISITION-088-DESIGN.md'
POLICY=ROOT/'docs/ACQUISITION-088-POLICY.md'
PLAN=ROOT/'docs/ACQUISITION-089-PLAN.md'
OWN=('scripts/acquisition-088.py','src/forex_demo_lab/acquisition_review_088.py',
    'tests/test_acquisition_review_088.py','docs/ACQUISITION-088-DESIGN.md',
    'docs/ACQUISITION-088-POLICY.md','docs/ACQUISITION-089-PLAN.md')
EXPECTED,NEW=1884,20
MUTATIONS=('file_replace','root_replace','ancestor_replace','ancestor_reparse',
    'acl_change','peer_change','account_real','account_contest','account_change','source_change')
CASES=('budget_floor','reader_requirements','schedule_reference','combined_reference',
    'default_off','sdk_repeat')+MUTATIONS
ACTIVE=runpy.run_path(str(ROOT/'scripts/synchronization-084-r2.py'))


def proposal():
    sys.path[:0]=[str(ROOT/'src')]
    from forex_demo_lab.acquisition_review_088 import budget_review088,reader_requirements088
    p=reader_requirements088(ROOT)
    b={**p['prior_reader_inputs'],**p['requirements_inputs']}
    return dict(version='acquisition_review_proposal_088_v1',input_bindings=b,
        budget_review=budget_review088(),reader_requirements=p,
        runtime_authorized=False,orders_available=False,new_reader_implemented=False)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='3e23a791727b8232071e6f77832dbcadc104cd0a3770b4a35facc6585262df83'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2762,2553)
    assert v['tests_passed']==1864 and v['new_tests']==34
    assert ARCHIVE(PRIOR,r)==2553
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=20,passed=False,failures=0,errors=13,elapsed_seconds=6.555,
            cause='fixture_subclass_rejected_by_exact_Api086_type_requirement'),
        dict(tests=20,passed=True,failures=0,errors=0,elapsed_seconds=6.464)],
        fixture_corrected_before_freeze=True,production_type_requirement_unchanged=True,
        frozen_full_suite_run=False,controller_development_case_audit_passed=True,
        development_cases=16,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected);prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1864,
        maximum_full_regressions=1,maximum_evidence_sets=1,evidence_cases=list(CASES),
        historical_fixture_date='2026-10-08',review_date='2026-10-09',
        prior_failure_records_preserved=True,retained_portable_close_comparisons=11,
        retained_ported_reader_scenarios=6,**ZERO,**FALSE))
    archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(archive),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    for k,p in (('prior_source_sha256',PRIOR),('design_sha256',DESIGN),('policy_sha256',POLICY),('next_plan_sha256',PLAN)):
        assert l[k]==sha(p)
    assert l['proposal']==proposal() and l['evidence_cases']==list(CASES)
    return l


def test():
    verify();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(full_suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    suite,retired=ACTIVE['active_suite']();assert suite.countTestCases()==EXPECTED and retired==43
    started=time.monotonic();r=unittest.TextTestRunner(verbosity=1).run(suite)
    ok=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=ok,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failed_test_names=[str(t) for t,d in r.failures+r.errors],elapsed_seconds=time.monotonic()-started,
        active_suite=True,active_suite_inherited='synchronization-084-r2.py',
        retired_original083_tests=43,retired_original084_tests=36,
        ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not ok:raise SystemExit(1)


def model_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from forex_demo_lab.acquisition_review_088 import budget_review088,reader_requirements088
    from test_acquisition_review_088 import combined088,schedule088,model_guard087
    if name=='budget_floor':return budget_review088()
    if name=='reader_requirements':return reader_requirements088(ROOT)
    if name=='schedule_reference':return schedule088()
    if name=='sdk_repeat':return model_guard087(repeat=True)
    return combined088(mutation=name if name in MUTATIONS else None,enabled=name!='default_off')


def audit_rows(rows):
    assert set(rows)==set(CASES)
    p=rows['budget_floor']
    assert (p['total_guards'],p['raw_inspections'],p['api_calls_floor'],p['clock_samples_floor'])==(70,69,2346,4693)
    assert (p['clock_samples_limit'],p['maximum_fully_bracketed_api_calls'])==(4096,2047)
    assert (p['bridge_calls'],p['sdk_queries'],p['boot_queries'])==(139,1668,208)
    assert p['ancestor_deduplication_sufficient'] is False and p['native_timing_proven'] is False
    req=rows['reader_requirements'];assert req==proposal()['reader_requirements']
    assert req['date']=='2026-10-09' and not req['new_reader_implemented'] and not req['new_reader_compiled']
    s=rows['schedule_reference']
    assert s['modeled_completed'] and s['controls']==6 and s['total_guards']==s['valid_guard_spans']==70
    assert s['frame_kinds']==[1,2,3,4] and not s['full_combined_success']
    r=rows['sdk_repeat'];assert not r['modeled_completed']
    assert (r['full_bridge_calls'],r['sdk_queries'],r['boot_queries'])==(86,1024,85)
    assert r['cleanup_confirmed'] and r['shutdown_attempts']==1
    for name in ('combined_reference','default_off')+MUTATIONS:
        r=rows[name];assert not r['modeled_completed'] and r['sdk_cleanup_confirmed']
        assert (r['remaining_handles'],r['remaining_allocations'],r['sdk_shutdown_attempts'])==(0,0,1)
        assert r['summary']['cleanup_confirmed'] is True and r['new_runtime_admission'] is False
        assert r['historical_model_date']=='2026-10-08'
        for k in ('native_invocations','sdk_connections','market_reads','orders'):assert type(r[k]) is int and r[k]==0
        if name=='combined_reference':
            assert (r['api_calls'],r['api_clock_samples'],r['controls'])==(2048,4097,2)
            assert (r['bridge_calls'],r['sdk_queries'],r['boot_queries'])==(61,732,91)
            assert (r['summary']['counts']['guards'],r['summary']['valid_guard_spans'])==(31,30)
            assert set(r['completed_inspection_call_counts'])=={64} and r['blocked_controls']==0
            assert r['stop_reason']=='sync_clock_rejected' and not r['mutation_injected']
        elif name=='default_off':
            assert r['default_off'] and (r['api_calls'],r['bridge_calls'],r['controls'])==(0,0,0)
        else:
            assert r['mutation_injected'] and r['mutation_count']==1 and r['controls']==0
            assert r['summary']['valid_guard_spans']==1
            assert r['api_clock_samples']<4096 and r['stop_reason']!='sync_clock_rejected'
    for r in rows.values():assert r['runtime_authorized'] is False and r['orders_available'] is False
    return dict(cases=16,analysis_records=2,typed_schedule_completions=1,
        coupled_model_rejections=11,standalone_sdk_rejections=1,default_off_cases=1,
        modeled_full_combined_completions=0,native_sharing_episodes_proven=0)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');assert t['passed'] and t['tests_run']==EXPECTED
    assert t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    rows={n:model_case(n) for n in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,dependencies_injected=True,
        ledger_sha256=sha(LEDGER),scope='offline_count_review_and_historical_coupled_models',**ZERO,**FALSE))
    print(json.dumps(dict(recorded_cases=len(rows))))


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and (t['tests_run'],t['new_tests'],t['failures'],t['errors'],t['skipped'])==(EXPECTED,NEW,0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and e['dependencies_injected'] is True
    counts=audit_rows(e['cases']);initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json')
    archive=ROOT/f'reports/{PREFIX}-initial-source.zip';assert sha(archive)==initial['archive_sha256']
    assert initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checks_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,new_tests=NEW,source_inputs=len(l['proposal']['input_bindings']),
        prior_failure_records_preserved=True,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(checks_passed=True,**counts)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checks_passed'] and c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/ACQUISITION-088-RESULTS.md'
    with result.open('x') as f:f.write(RESULT_TEXT)
    b=dict(l['bindings'])
    for n in HANDOFF:
        p=ROOT/n;s=p.read_text();i=s.index('\n')+1;p.write_text(s[:i]+'\n'+LATEST_TEXT+s[i:]);b[n]=sha(p)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    r=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        tests_passed=EXPECTED,new_tests=NEW,model_cases=16,full_sharing_episode_proven=False,
        modeled_full_combined_completions=0,new_reader_implemented=False,
        native_boot_proof_implemented=False,native_guard_wiring_complete=False,next_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,r);write(final,r)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();f=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(f);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(f,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json');counts=audit_rows(e['cases'])
    assert c['checks_passed'] and c['ledger_sha256']==sha(LEDGER) and t['passed'] and t['tests_run']==EXPECTED
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert not r['next_plan_executed'] and not r['full_sharing_episode_proven'] and not r['new_reader_implemented']
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(f),
        bindings_verified=len(b),archive_members_verified=members,frozen_inputs_verified=len(l['bindings']),
        frozen_input_coverage_complete=True,tests_passed=EXPECTED,new_tests=NEW,
        source_inputs=len(l['proposal']['input_bindings']),prior_failure_records_preserved=True,
        retained_portable_close_comparisons=11,retained_ported_reader_scenarios=6,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests=EXPECTED,bindings=len(b),members=members,**counts)))


RESULT_TEXT="""# Acquisition budget review 088 results

The existing raw API/guard layout cannot complete its six-control schedule
within the unchanged budgets through ancestor deduplication alone. The typed
schedule needs70 guards/69 raw inspections. Even giving all ancestor work zero
cost, required descriptor/path/ACL/pipe/peer acquisitions need at least2,346 API
calls and4,693 clock checks; the4,096 cap permits2,047 fully bracketed calls.
Factory, control and wire IO costs are excluded from this optimistic floor.
This bound applies to the current layout, not every possible API architecture.

The same layout needs139 bridge calls against96,1,668 SDK queries against1,024
and208 boot queries against128. These are schedule-derived requirements, not
claims that rejected calls executed beyond their caps. No optimized adapter
is implemented and no limit, check or window is relaxed.

One frozen full active regression passed1,884 tests (1,864 retained/20 new),
zero failures/errors/skips. The initial20-test developer run had13 fixture
errors because the production constructor correctly rejected an Api086 subclass.
The fixture was corrected to use exact Api086; a later20-test run passed. Frozen
production sources/type checks were unchanged.

Sixteen evidence records: two analyses, one typed schedule completion, eleven
coupled rejections, one independent SDK rejection and one default-off. The
historical Oct8 full raw/full-bridge six-control target still stops after two
pre controls:2,048 API calls/check4,097,31 guards started/30 valid spans,
61 bridge calls/732 SDK queries/91 boot queries. Complete inspections measure64
raw calls each. It never reaches independent hold controls. Full combined
completion remains zero; no valid span is invented after a rejected proof.

Improved model descriptors retain object identities while new path opens see
replacements. Mid-composite file/root/ancestor replacement, ancestor reparse,
ACL and raw-peer changes reject; real/contest/changed demo account and source
changes between bridge checks reject too. Once-only model cleanup leaves no
fake handles or allocations and attempts one owned SDK shutdown. This does not
prove native sharing, physical cleanup or timing. Repeated standalone guards
still reject attempt86 at1,024 SDK queries.

Fresh Oct9 phase/reader requirements bind37 old inputs/six old compile files
and the unchanged2s/10s/30–31s/250ms/60s/120s windows. They explicitly cannot admit
runtime on any date; no new reader is implemented or compiled and the old Oct8
gate remains expired. A runnable dated reader is deferred pending a feasible
architecture. The0861,611ms /60,870ms episode deadline failure is retained.

Compiler launcher ownership, capped capture, timeout kill/wait, WMI provider/
module provenance and restart/resume/fast-startup/clock behavior remain
unverified. The current runner's returned model facts do not implement those
obligations. WMI last-restart time is not asserted to be a unique kernel GUID.

Prior087's2,762 bindings/2,553 members and every failure/spent/data/cost/clock/
coverage/consumed-2025/reserved-Nov–Dec/provider exclusion were preserved.
Zero actual DLL/WMI/SDK/MT5/compiler/deploy/log/market/orders/receipts or grants.
Native entry, performance eligibility and orders remain unavailable. No profit
or latency guarantee, real-money path, martingale or UI action. Four handoffs,
evidence, source and archives were sealed and reviewed. Next089 architecture
feasibility review is unexecuted; see ACQUISITION-089-PLAN.md.
"""
LATEST_TEXT=('Latest — 2026-10-09 local/UTC: offline acquisition review088 sealed; '
    'read ACQUISITION-088-RESULTS.md.1884 active tests/20 new pass; zero frozen failures/errors/skips. '
    'Ancestry-only optimization insufficient:70 schedule guards/69 raw inspections require at least '
    '2346 API calls/4693 clock checks even with free ancestry vs4096 cap/2047 complete calls; existing '
    'layout also needs139/96 bridge calls,1668/1024 SDK queries,208/128 boot queries. '
    '16 records:2 analyses/1 typed schedule completion/11 coupled rejections/1 SDK rejection/1 off; '
    'zero full combined success. Historical Oct8 raw+full bridge still2048 calls/4097 checks/2 controls, '
    '31 guards/30 spans. Replacement-aware descriptor fixture rejects mid-composite file/root/ancestor/ '
    'reparse/ACL/peer and current account/source changes; model cleanup confirmed. '
    'Fresh Oct9 reader requirements are non-admitting; no new runnable/compiled reader or optimized '
    'adapter. Frozen Oct8 gate unchanged/expired. Prior0872762 bindings/2553 members and all old '
    'failures/spent/data/cost/clock/coverage/consumed/reserved/provider gates retained;0861611ms timing '
    'failure persists. Compiler/boot runner/module/capture/timeout/provider/native timing unverified. '
    'Zero actual DLL/WMI/native/SDK/MT5/compiler/deploy/log/market/orders/grants. Native entry/eligibility/ '
    'orders false; no UI action. Next089 architectural feasibility unexecuted. Earlier entries historical.'+chr(10)+chr(10))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
