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
API=runpy.run_path(str(ROOT/'scripts/acquisition-088.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='compound-089';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/acquisition-088-final-source.json'
REVIEW=ROOT/'reports/acquisition-088-completion-review.json'
DESIGN=ROOT/'docs/COMPOUND-089-DESIGN.md'
POLICY=ROOT/'docs/COMPOUND-089-POLICY.md'
PLAN=ROOT/'docs/GUARD-090-PLAN.md'
OWN=('scripts/compound-089.py','src/forex_demo_lab/compound_acquisition_089.py',
    'tests/test_compound_acquisition_089.py','docs/COMPOUND-089-DESIGN.md',
    'docs/COMPOUND-089-POLICY.md','docs/GUARD-090-PLAN.md')
EXPECTED,NEW=1915,31
MUTATIONS=('file_replace','root_replace','ancestor_replace','ancestor_reparse',
    'acl_change','peer_change','account_real','account_contest','account_change','source_change')
CASES=dict(normal={},api_1ms={'api_latency':1},api_100ms={'api_latency':100},default_off={'enabled':False},
    **{n:{'mutation':n} for n in MUTATIONS},
    new_source_change={'mutation':'source_change','new_source_only':True},
    after_open_change={'mutation':'file_replace','mutation_at_inspection':4},
    substituted_control={'control_substitution':True},security_overflow={'needed_overflow':True},
    security_interrupt={'interrupt_security':True},control_close_uncertain={'control_close_uncertain':True},
    creator_close_uncertain={'close_uncertain':True},detached_clock={'detach_clock':True},
    bounded_reader={'native_reader_hash_cap':True},sdk_repeat={})
ACTIVE=runpy.run_path(str(ROOT/'scripts/synchronization-084-r2.py'))


def proposal():
    import ast
    sys.path[:0]=[str(ROOT/'src')]
    from forex_demo_lab.compound_acquisition_089 import SOURCE,PHASE,REVIEW_DATE,PROTOTYPE_DATE
    from forex_demo_lab.build_bindings_087 import build_contract087
    names=set(API['proposal']()['input_bindings'])
    pending=[SOURCE,'src/forex_demo_lab/native_bindings_087.py','src/forex_demo_lab/__init__.py']
    visited=set()
    while pending:
        n=pending.pop()
        if n in visited:continue
        visited.add(n);names.add(n)
        for node in ast.walk(ast.parse((ROOT/n).read_text())):
            if isinstance(node,ast.ImportFrom) and node.level:
                assert node.level==1 and node.module is not None
                pending.append('src/forex_demo_lab/'+node.module.replace('.','/')+'.py')
    names.update(('scripts/boot-proof-087.ps1','docs/BINDINGS-087-DESIGN.md',
        'docs/BINDINGS-087-POLICY.md','docs/COMPOUND-089-DESIGN.md','docs/COMPOUND-089-POLICY.md'))
    return dict(version='compound_acquisition_proposal_089_v1',phase=PHASE,review_date=REVIEW_DATE,
        historical_fixture_date=PROTOTYPE_DATE,input_bindings={n:sha(ROOT/n) for n in sorted(names)},
        retained_build_contract=build_contract087(ROOT),source_proofs_per_guard=41,
        source_proof_passes_per_guard=2,security_buffer_bytes=65536,
        count_scope='injected_raw_api_sdk_boot_only',native_reader_hash_cap=768,
        native_hash_reader_verified=False,runtime_authorized=False,orders_available=False,
        new_reader_implemented=False)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='87c3f8a2096f94ca78a8d274d4c73196e505f9cee17173b912f1c49371efce5e'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2791,2580)
    assert v['tests_passed']==1884 and v['new_tests']==20
    assert ARCHIVE(PRIOR,r)==2580
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=24,passed=True,failures=0,errors=0,elapsed_seconds=8.139),
        dict(tests=27,passed=False,failures=1,errors=0,elapsed_seconds=9.094,
            cause='fixture_uncertain_close_triggered_creator_instead_of_control'),
        dict(tests=28,passed=True,failures=0,errors=0,elapsed_seconds=9.931),
        dict(tests=30,passed=True,failures=0,errors=0,elapsed_seconds=10.446),
        dict(tests=31,passed=False,failures=0,errors=1,elapsed_seconds=10.408,
            cause='fixture_used_legacy_meter_with_different_expired_date'),
        dict(tests=31,passed=True,failures=0,errors=0,elapsed_seconds=10.726)],
        fixture_corrected_before_freeze=True,all_old_date_and_count_gates_unchanged=True,
        frozen_full_suite_run=False,controller_development_case_audit_passed=True,
        development_cases=24,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected);prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1884,
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
    from test_compound_acquisition_089 import combined089,model_guard087
    return model_guard087(repeat=True) if name=='sdk_repeat' else combined089(**CASES[name])


def audit_rows(rows):
    assert set(rows)==set(CASES)
    for name,r in rows.items():
        assert r['runtime_authorized'] is False and r['orders_available'] is False
        for k in ('native_invocations','sdk_connections','market_reads','orders'):
            assert type(r[k]) is int and r[k]==0
        if name=='sdk_repeat':
            assert not r['modeled_completed'] and r['cleanup_confirmed']
            assert (r['full_bridge_calls'],r['sdk_queries'],r['boot_queries'])==(86,1024,85)
            assert r['shutdown_attempts']==1;continue
        assert r['sdk_cleanup_confirmed'] and r['sdk_shutdown_attempts']==1
        assert r['remaining_handles']==r['remaining_allocations']==0
        assert r['historical_fixture_date']=='2026-10-08' and r['review_date']=='2026-10-09'
        assert r['native_timing_proven'] is False and r['new_runtime_admission'] is False
        s=r['summary']
        assert s['cleanup_confirmed'] is (name not in ('control_close_uncertain','creator_close_uncertain'))
        if name in ('normal','api_1ms'):
            assert r['modeled_completed'] and len(r['controls'])==6 and r['frame_kinds']==[1,2,3,4]
            assert (r['api_calls'],r['api_clock_samples'],r['bridge_clock_samples'])==(1689,3379,1139)
            assert (r['bridge_calls'],r['sdk_queries'],r['boot_queries'],r['hash_reads'])==(38,456,75,4100)
            assert s['counts']['guards']==s['valid_guard_spans']==38 and s['counts']['closes']==7
            assert s['episode_elapsed_ms']==(30256 if name=='normal' else 31156)
            assert r['blocked_controls']==2 and r['control_fact_reads']==8
            assert set(r['inspection_call_counts'])=={44,46} and r['source_checks']==76
            assert r['native_reader_hash_cap'] is None
        else:
            assert not r['modeled_completed']
            if name=='default_off':assert (r['api_calls'],r['bridge_calls'],r['sdk_queries'],r['source_checks'])==(0,0,0,0)
            elif name=='bounded_reader':
                assert (r['native_reader_hash_cap'],r['bounded_reader_hash_reads'],r['hash_reads'])==(768,768,768)
                assert r['bounded_reader_scope']=='065_hash_count_only'
                assert (r['bridge_calls'],s['valid_guard_spans'],len(r['controls']))==(8,7,1)
                assert r['api_clock_samples']==605 and r['sdk_queries']==90
            elif name=='api_100ms':
                assert r['stop_reason']=='sync086_frame_rejected' and s['episode_elapsed_ms']==11500
                assert not s['release_spent'] and len(r['controls'])==2
            elif name in MUTATIONS or name=='new_source_change':
                assert r['mutation_injected'] and s['valid_guard_spans']==1 and len(r['controls'])==0
            elif name=='after_open_change':
                assert r['mutation_injected'] and s['valid_guard_spans']==4 and len(r['controls'])==0
            elif name=='substituted_control':assert s['valid_guard_spans']==3 and len(r['controls'])==0
            elif name in ('control_close_uncertain','creator_close_uncertain'):
                assert r['unconfirmed_api_closes']==1
            elif name=='detached_clock':assert s['valid_guard_spans']==1
    return dict(cases=24,modeled_full_combined_completions=2,coupled_model_rejections=20,
        standalone_sdk_rejections=1,default_off_cases=1,native_sharing_episodes_proven=0,
        native_reader_verified=False)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');assert t['passed'] and t['tests_run']==EXPECTED
    assert t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    rows={n:model_case(n) for n in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,dependencies_injected=True,
        ledger_sha256=sha(LEDGER),scope='compound_historical_raw_bridge_and_reader_count_models',**ZERO,**FALSE))
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
    result=ROOT/'docs/COMPOUND-089-RESULTS.md'
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
        tests_passed=EXPECTED,new_tests=NEW,model_cases=24,full_sharing_episode_proven=False,
        modeled_full_combined_completions=2,new_reader_implemented=False,
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


RESULT_TEXT="""# Compound acquisition 089 results

The historical raw API/full bridge prototype completes all six controls and
four frames within the original API/SDK/boot count limits. File security uses a
bounded caller-owned descriptor buffer; named-pipe security retains its existing
API. Complete ancestry is freshly checked at both ends of each composite.
Separate root/file descriptor/path/ACL proofs remain. Physical control opens
and closes retain full before/after guards, with current control-handle stamps
inside those guards. One SDK/image/source proof surrounds raw acquisition.
No cross-guard cache, fake span, raised cap or longer window.

Normal and 1ms-per-API injected episodes complete: 38 guards/38 valid spans,
1,689 API calls, 3,379 API clock samples, 1,139 bridge clock samples, 456 SDK
queries and 75 boot queries. Both complete six controls and four canonical
frames, including two independent sharing-error32 controls. Episode times are
30,256ms and 31,156ms. Seven once-only owned model closes and one SDK shutdown
complete. Actual native sharing, timing, provider, driver/access and cleanup
remain unverified; source hashing/identity/SDK/WMI latency is free in this model.

The native reader remains a blocker. The successful fake reader has no hash
cap; its 4,100 reads exceed the available legacy reader's 768-read limit.
Injecting that unchanged count predicate rejects bridge attempt eight after
seven spans/one control, at only 605 API clock checks/90 SDK queries. This tests
the hash count only, not the expired legacy meter/native implementation or its
bytes/path/process/clock budgets. The native experiment still cannot proceed
under the available reader contract. No new reader, compile or admission flag.

One frozen full 084 R2 active regression passed 1,915 tests: 1,884 retained and
31 new, zero failures/errors/skips. Developer runs before freeze were: 24 pass;
27 with one fixture failure (uncertainty hit creator, expected control counter);
28 pass; 30 pass; 31 with one fixture error (wrong expired legacy meter date);
31 pass. Fixtures were corrected without changing any old gate or cap. The
hash comparison now uses only the legacy count predicate and does not bypass
or renew its old date gate.

Twenty-four evidence cases: two complete coupled models, 20 coupled rejections,
one independent SDK rejection and one default-off. Mid-composite file/root/
ancestor/reparse/ACL/peer/current account/source changes, new-source-only change,
post-open replacement, substituted control, oversized or interrupted security
query and detached clock reject. Uncertain creator/control close never claims
cleanup success. Fake resources are removed and one SDK shutdown is attempted;
fake removal is not physical close proof. Standalone SDK still rejects at 1,024
queries. 100ms-per-API rejects 2s response freshness with release still unspent.

Prior 088 closure (2,791 bindings/2,580 members), the old 1,611ms/60,870ms deadline
failure, count failures, spent markers and all data/cost/clock/coverage/consumed-
2025/reserved-Nov–Dec/provider exclusions are preserved. The new source is an
Oct8 historical prototype reviewed Oct9, not an expired reader renewal. Native
entry rejects and current runtime is unavailable. Native boot identity, module
provenance, capped capture/timeout, fresh build and source-reader cost are open.
Finite ancestry observations do not guarantee atomicity or detect every restored
transient change. No latency or profitability claim.

Zero actual DLL/WMI/SDK/MT5/compiler/deploy/log/market/orders/receipts or grants.
No real-money execution, live toggle, martingale or UI action. All original
2s/10s/30–31s/250ms/60s/120s windows and default-off/actual-DEMO checks remain.
Eligibility and orders remain false. Source, evidence, archives and four
handoffs were sealed and reviewed; next 090 source-proof feasibility is unexecuted.
Primary API references and remaining limitations are in COMPOUND-089-DESIGN.md.
"""
LATEST_TEXT=('Latest — 2026-10-09 local/UTC: offline compound acquisition 089 sealed; '
    'read COMPOUND-089-RESULTS.md. 1,915 active tests / 31 new pass; no frozen failures/errors/skips. '
    '24 injected cases: 2 coupled completions / 20 coupled rejections / 1 SDK rejection / 1 off. '
    'Historical full raw API/bridge six-control models fit API/SDK/boot caps: 1,689 calls, '
    '3,379 API clock checks, 1,139 bridge checks, 38 guards/spans, 456 SDK queries, 75 boot queries; '
    'six controls/four frames/7 once-only model closes/SDK shutdown 1. Normal episode 30,256ms, '
    '1ms/API 31,156ms. No native success. One fresh bridge surrounds raw facts; file security '
    'bounded caller buffer, named-pipe API unchanged, complete ancestry fresh at both ends, '
    'descriptor/path/ACL/current control stamps inside uncached guards; physical open/close guard '
    'pairs retained. No limits/windows weakened. Native source reader still blocks: fake reader '
    'performs 4,100 hashes; injecting existing 768-read cap rejects attempt 8 / 7 spans / 1 control. '
    'Legacy expired date unchanged; count-only comparison is not full native validation. '
    'Replacement/account/source/ACL/peer/callback/uncertain cleanup tests reject. 100ms/API freshness '
    'failure and all prior 086–088 timing/count/spent/data/cost/clock/coverage/reserved/provider gates '
    'preserved. Prior 088: 2,791 bindings / 2,580 members verified. Oct8 historical source only; '
    'new reader/build/native boot/provenance/hash-cost/driver/timing remain unverified. '
    'Zero actual DLL/WMI/native/SDK/MT5/compiler/deploy/log/market/orders/grants. Entry/eligibility/ '
    'orders unavailable. Next 090 source-proof feasibility unexecuted; no UI action. Earlier entries historical.'+chr(10)+chr(10))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
