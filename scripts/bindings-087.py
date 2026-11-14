"""Offline redesign controller. Exclusive frozen actions; no native authority."""
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
API=runpy.run_path(str(ROOT/'scripts/synchronization-086.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='bindings-087';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/synchronization-086-final-source.json'
REVIEW=ROOT/'reports/synchronization-086-completion-review.json'
DESIGN=ROOT/'docs/BINDINGS-087-DESIGN.md'
POLICY=ROOT/'docs/BINDINGS-087-POLICY.md'
PLAN=ROOT/'docs/BINDINGS-088-PLAN.md'
OWN=('scripts/bindings-087.py','src/forex_demo_lab/build_bindings_087.py',
    'src/forex_demo_lab/native_bindings_087.py','scripts/boot-proof-087.ps1',
    'tests/test_build_bindings_087.py','tests/test_native_bindings_087.py',
    'docs/BINDINGS-087-DESIGN.md','docs/BINDINGS-087-POLICY.md','docs/BINDINGS-088-PLAN.md')
EXPECTED,NEW=1864,34
CASES=dict(build_normal={},build_default_off={'enabled':False},build_wrong_exit={'exit_code':0},
    build_warning={'log':'Result: 0 errors, 1 warnings, x'+chr(10)},
    build_source_change={'tamper_source':True},build_image_change={'changed_image':True},
    build_editor_remaining={'editor_left':True},build_interrupted={'interrupt':True},build_timeout={'timeout':True},
    guard_normal={},guard_real={'real':True},guard_source_change={'changed_source':True},
    guard_boot_change={'changed_boot':True},guard_late_query={'latency':2001},guard_repeat_budget={'repeat':True},
    combined_raw_episode={})
ACTIVE=runpy.run_path(str(ROOT/'scripts/synchronization-084-r2.py'))


def proposal():
    import ast
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.build_bindings_087 import build_contract087
    from forex_demo_lab.synchronization_086 import MQL_INPUTS
    names=set(MQL_INPUTS);pending=['src/forex_demo_lab/build_bindings_087.py',
        'src/forex_demo_lab/native_bindings_087.py','src/forex_demo_lab/__init__.py']
    while pending:
        n=pending.pop()
        if n in names:continue
        names.add(n)
        for node in ast.walk(ast.parse((ROOT/n).read_text())):
            if isinstance(node,ast.ImportFrom) and node.level:
                assert node.level==1 and node.module is not None
                pending.append('src/forex_demo_lab/'+node.module.replace('.','/')+'.py')
    names.update(build_contract087(ROOT)['source_contract']['input_bindings'])
    names.update(('scripts/boot-proof-087.ps1','docs/BINDINGS-087-DESIGN.md','docs/BINDINGS-087-POLICY.md',
        'docs/SYNCHRONIZATION-086-DESIGN.md','docs/SYNCHRONIZATION-086-POLICY.md'))
    return dict(version='binding_preparation_087_v1',input_bindings={n:sha(ROOT/n) for n in sorted(names)},
        build_contract=build_contract087(ROOT),guard_source_inputs=40,required_hash_roles=9,
        boot_corroborator_kind='local_wmi_last_restart_time_087',unique_kernel_boot_id_proven=False,
        actual_boot_provider_verified=False,native_guard_wiring_complete=False,
        candidate_mql_compiled=False,native_runtime_authorized=False,orders_available=False)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='3af78b9ed29d97e28d808bad79e9efab8eb5dba77293fa10e78980132d0fc469'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2730,2523)
    assert v['tests_passed']==1830 and v['new_tests']==61
    assert ARCHIVE(PRIOR,r)==2523
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=33,passed=False,failures=1,errors=0,elapsed_seconds=26.399,
            failing_test='test_full_bridge_checks_every_source_helper_image_and_boot',
            expected_metadata_queries=32,observed_metadata_queries=24),
        dict(tests=34,passed=True,failures=0,errors=0,elapsed_seconds=35.173),
        dict(tests=34,passed=True,failures=0,errors=0,elapsed_seconds=27.767)],
        refinements_between_runs=True,fixture_corrected_before_freeze=True,frozen_full_suite_run=False,
        exploratory_models_before_freeze=True,controller_development_case_audit_passed=True,
        development_cases=16,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1830,
        maximum_full_regressions=1,maximum_evidence_sets=1,evidence_cases=CASES,
        evidence_scope='model_build_and_guard_binding_plus_combined_raw_episode',
        prior_failure_records_preserved=True,retained_portable_close_comparisons=11,retained_ported_reader_scenarios=6,**ZERO,**FALSE))
    archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(archive),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),source_inputs=len(prop['input_bindings']),expected_tests=EXPECTED)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    for k,p in (('prior_source_sha256',PRIOR),('design_sha256',DESIGN),('policy_sha256',POLICY),('next_plan_sha256',PLAN)):
        assert l[k]==sha(p)
    assert l['proposal']==proposal() and l['evidence_cases']==CASES
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
        retired_original083_tests=43,retired_original084_tests=36,portable_close_comparisons=11,
        ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not ok:raise SystemExit(1)


def model_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from test_build_bindings_087 import model_build087
    from test_native_bindings_087 import model_guard087,model_combined087
    if name=='combined_raw_episode':return model_combined087()
    return model_build087(**CASES[name]) if name.startswith('build_') else model_guard087(**CASES[name])


def audit_rows(rows):
    assert set(rows)==set(CASES)
    success={'build_normal','guard_normal'}
    for name,row in rows.items():
        assert type(row['modeled_completed']) is bool and row['modeled_completed'] is (name in success)
        if name.startswith('build_'):
            assert type(row['compiler_invocations']) is int and row['compiler_invocations']<=1
            assert row['backend_compile_calls']==row['compiler_invocations']
            if name=='build_default_off':
                assert row['default_off'] is True and row['compiler_invocations']==row['backend_metadata_calls']==0
                assert row['attempt_persisted'] is False and row['stage_trace']==[]
                continue
            assert row['dependencies_injected'] is True and row['native_compiler_invocations']==0
            assert row['runtime_authorized'] is False and row['orders_available'] is False
            assert row['attempt_persisted'] is True and row['metadata_after_attempted'] is True
            assert row['backend_metadata_calls']==(1 if name=='build_image_change' else 3)
            assert row['compiler_invocations']==(0 if name=='build_image_change' else 1)
            if name=='build_normal':
                assert row['counts']['copies']==6 and row['build_record']['compiler_exit_code']==1
                assert row['build_record']['errors']==row['build_record']['warnings']==0
                assert row['build_record']['runtime_authorized'] is False and row['build_record']['orders_available'] is False
                assert len(row['build_record']['input_bindings'])==37 and len(row['build_record']['compile_inputs'])==6
            else:assert row['stop_reason'] is not None
        else:
            for k in ('native_invocations','sdk_connections','market_reads','orders'):
                assert type(row[k]) is int and row[k]==0
            assert row['runtime_authorized'] is False and row['orders_available'] is False
            assert row['shutdown_attempts']==1
            if name=='combined_raw_episode':
                assert row['sdk_cleanup_confirmed'] is True
                assert row['remaining_handles']==row['remaining_allocations']==0
                assert row['api_calls']==2048 and row['api_clock_samples']==4097
                assert row['diagnosed_budget']=='raw_api_clock_samples' and row['raw_api_clock_sample_limit']==4096
                assert row['controls']==2 and row['full_bridge_calls']==61 and row['sdk_queries']==732 and row['boot_queries']==91
                s=row['summary'];assert s['counts']['guards']==31 and s['valid_guard_spans']==30
                assert s['counts']['closes']==5 and s['cleanup_confirmed'] is True and s['episode_elapsed_ms']==5
            else:
                assert row['cleanup_confirmed'] is True and row['native_boot_provider_verified'] is False
                assert row['native_guard_wiring_verified'] is False
                expected={'guard_normal':(1,12,1,53),'guard_real':(1,2,0,0),
                    'guard_source_change':(1,6,1,14),'guard_boot_change':(1,6,1,4),
                    'guard_late_query':(1,6,1,2),'guard_repeat_budget':(86,1024,85,4505)}[name]
                assert (row['full_bridge_calls'],row['sdk_queries'],row['boot_queries'],row['hash_reads'])==expected
    return dict(cases=16,modeled_completions=2,modeled_rejections=13,default_off_cases=1,
        modeled_build_completions=1,modeled_guard_completions=1,modeled_full_combined_completions=0,
        native_sharing_episodes_proven=0,native_timing_proven=False)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    rows={name:model_case(name) for name in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,dependencies_injected=True,
        ledger_sha256=sha(LEDGER),scope='injected_build_guard_and_combined_raw_episode',**ZERO,**FALSE))
    print(json.dumps(dict(recorded_cases=len(rows),modeled_completions=sum(r['modeled_completed'] for r in rows.values()))))


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and (t['tests_run'],t['new_tests'],t['failures'],t['errors'],t['skipped'])==(EXPECTED,NEW,0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and e['dependencies_injected'] is True
    counts=audit_rows(e['cases'])
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(archive)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checks_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,new_tests=NEW,source_inputs=len(l['proposal']['input_bindings']),
        retained_portable_close_comparisons=11,retained_ported_reader_scenarios=6,prior_failure_records_preserved=True,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(checks_passed=True,**counts)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checks_passed']
    assert c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/BINDINGS-087-RESULTS.md'
    text=RESULT_TEXT
    with result.open('x') as f:f.write(text)
    latest=LATEST_TEXT
    b=dict(l['bindings'])
    for n in HANDOFF:
        p=ROOT/n;s=p.read_text();i=s.index('\n')+1;p.write_text(s[:i]+'\n'+latest+s[i:]);b[n]=sha(p)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    r=dict(source_and_evidence_bindings=b,archive_external_bindings=external,archive_sha256=sha(final.with_suffix('.zip')),
        archive_members_verified=len(internal),tests_passed=EXPECTED,new_tests=NEW,model_cases=16,
        full_sharing_episode_proven=False,modeled_full_combined_completions=0,native_boot_proof_implemented=False,
        native_guard_wiring_complete=False,next_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,r);write(final,r)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();f=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(f);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(f,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json');counts=audit_rows(e['cases'])
    assert c['checks_passed'] and c['ledger_sha256']==sha(LEDGER) and t['passed'] and t['tests_run']==EXPECTED
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert not r['next_plan_executed'] and not r['full_sharing_episode_proven']
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(f),
        bindings_verified=len(b),archive_members_verified=members,frozen_inputs_verified=len(l['bindings']),
        frozen_input_coverage_complete=True,tests_passed=EXPECTED,new_tests=NEW,source_inputs=len(l['proposal']['input_bindings']),
        retained_portable_close_comparisons=11,retained_ported_reader_scenarios=6,prior_failure_records_preserved=True,next_plan_sha256=sha(PLAN),
        next_plan_executed=False,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests=EXPECTED,bindings=len(b),members=members,**counts)))


RESULT_TEXT="""# Build preparation and native binding review 087 results

Prepared an exact compiler schema and a model-only one-use stage for the
immutable 086 reader. It binds all 37 candidate inputs and copies six MQL
source/header files. It requires actual compiler exit 1, one zero-error/zero-
warning summary, independently pinned images, build 6244 and a bounded new
artifact. Changed source/images, warnings, wrong exit, extra output, surviving
editor, restart, timeout and interruption reject. Final metadata is attempted;
owned stage directories and unrelated files are never overwritten or deleted.

Prepared a fixed local WMI query and strict parser for reported OS last-restart
time. Explicit offsets convert to UTC without guessing from uptime. Every
model query checks pinned shell/script hashes before and after, returned timing,
bounded output and absent owned child. This is corroboration, not a unique
kernel boot GUID. No actual query was run; provider restart/resume/fast-startup/
clock behavior, bounded native capture and helper/module provenance remain
unverified. A modeled query cannot establish native boot proof.

The guard bridge checks actual account type DEMO, USD, same account, connected,
Algo off, EURUSD metadata, bound SDK/loaded library/owner, fresh terminal/helper
identities, nine image/helper/artifact/config roles and 40 source inputs.
Metadata and identity are checked at both ends; source/image proofs are uncached
between calls. Owned SDK shutdown is attempted once after rejection. Native entry
and actual tables remain unavailable. No market/history/quote/order path is added.

One frozen full active regression passed 1,864 tests: 1,830 retained plus 34 new,
with no failures/errors/skips. Before freeze, the first 33-test developer run had
one fixture failure: two guard calls made 24 metadata queries, while the test
expected 32. The expectation was corrected; two later 34-test runs passed. No
runtime guard was relaxed. Prior 086's 2,730 bindings/2,523 members and all old
failures/spent markers were verified and preserved.

Sixteen injected evidence cases: two isolated completions (normal modeled build
and normal guard), one default-off and 13 rejections. No complete combined raw
adapter/guard/transport episode succeeds. Its first failure is structural:
2,048 raw callable API calls reach clock-check attempt 4,097 against the existing
4,096-check cap. Only two controls are complete; 31 outer guards start and 30
valid spans finish. The episode has elapsed only 5 ms, so this is the COUNT
budget, not the 60-second deadline. Cleanup makes five once-only model close
attempts and one SDK shutdown, leaving no fake handles or allocations.

Source hashing and native latency are free in this combined model. Actual native
work would add obligations; the result does not establish a physical timing
bound or native cleanup. The separate repeated bridge reaches its 1,024 SDK-query
cap on attempt 86 after 85 successful guards. Neither failure was made to pass
by raising a cap, skipping a guard, caching a proof or widening a time window.
The 1,611 ms full-episode deadline failure from 086 remains independently valid.

Actual MT5 compilation, DLL ABI, WMI/provider/runner semantics, native boot/guard/
sharing/ACK/timing and profitability are unverified. Zero actual WMI/DLL/SDK/
MT5/MetaEditor/deploy/terminal-log/market/order/receipt invocations or grants.
The frozen reader's Oct 8 UTC gate remains; a later expired-date admission needs
fresh phase/date/source. Next 088 reviews redundant raw acquisition and both
count budgets while preserving every required fresh proof. Build/model success
is not native authority. No user UI action is required now.

All runtime 2s/10s/30–31s/250ms/60s/120s limits and prior data/cost/clock/coverage/
consumed-2025/reserved-Nov–Dec/provider exclusions remain. Real/contest rejection,
default off, no live toggle/martingale and eligibility/order exclusions persist.
Source/evidence/archives were checked and reviewed again at closure. Primary API
references and limitations are in BINDINGS-087-DESIGN.md.
"""
LATEST_TEXT=('Latest — local 2026-10-09 / declared UTC 2026-10-08: offline build/native binding review087 sealed; '
    'read BINDINGS-087-RESULTS.md.1864 active tests/34 new pass; zero frozen failures/errors/skips. '
    '16 injected cases:2 isolated completions/13 rejections/1 off; no combined episode success. '
    'Exact37-input/six-MQL source build schema and exclusive model compiler stage, fixed fresh local WMI '
    'last-restart-time corroborator/parser, uncached actual-DEMO/SDK/image/helper/artifact/40-source guard '
    'bridge prepared. WMI timestamp is not a unique kernel boot GUID; no actual provider/runner/build verified. '
    'Combined raw API reaches4097 clock-check attempts against4096 cap after2048 calls,31 outer guards/30 '
    'valid spans/only2 controls/5ms episode. Cleanup5 model closes/SDK shutdown1 confirmed. Repeated guard '
    'hits1024 SDK-query cap on attempt86. Caps/guards/windows unchanged;0861611ms deadline failure retained. '
    'Prior0862730 bindings/2523 members and all failed records/spent/data/reserved/provider gates preserved. '
    'Zero actual WMI/DLL/native/SDK/MT5/compiler/deploy/log/market/orders/grants; native entry unavailable. '
    'Native boot/guard/build/sharing/ACK/timing/profit unproven; eligibility/orders false. Next088 acquisition '
    'budget/proof review unexecuted; no UI action. Expired Oct8 UTC runtime needs fresh source/date/phase. '
    'Earlier entries historical.'+chr(10)+chr(10))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
