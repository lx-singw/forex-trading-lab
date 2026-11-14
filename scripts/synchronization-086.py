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
API=runpy.run_path(str(ROOT/'scripts/synchronization-085.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='synchronization-086';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/synchronization-085-final-source.json'
REVIEW=ROOT/'reports/synchronization-085-completion-review.json'
DESIGN=ROOT/'docs/SYNCHRONIZATION-086-DESIGN.md'
POLICY=ROOT/'docs/SYNCHRONIZATION-086-POLICY.md'
PLAN=ROOT/'docs/SYNCHRONIZATION-087-PLAN.md'
OWN=('scripts/synchronization-086.py','src/forex_demo_lab/synchronization_086.py',
    'src/forex_demo_lab/windows_adapter_086.py','tests/test_synchronization_086.py',
    'tests/test_windows_adapter_086.py','tests/fixtures/reader_086.cpp',
    'mt5/Scripts/ForexDemoSynchronization086.mq5','mt5/Scripts/WindowsPipe086.mqh',
    'docs/SYNCHRONIZATION-086-DESIGN.md','docs/SYNCHRONIZATION-086-POLICY.md',
    'docs/SYNCHRONIZATION-087-PLAN.md')
EXPECTED,NEW=1830,61
CASES=dict(full_normal={},full_small_guard={'guard_ms':50},full_observed_guard={'guard_ms':1611},
    full_wrong_error={'control_error':5},full_account_change={'bad_guard_at':21},
    full_close_uncertain={'close_uncertain':True},full_default_off={'enabled':False},
    adapter_ready={'adapter':True},adapter_absent={'adapter':True,'absent':True},
    adapter_close_uncertain={'adapter':True,'close_uncertain':True})
ACTIVE=runpy.run_path(str(ROOT/'scripts/synchronization-084-r2.py'))


def proposal():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.synchronization_086 import source_contract086
    return source_contract086(ROOT)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='a4c4aefb22743ee6d73f7fe05d250fab0f14bfb1710977db0b81eaa962bb2549'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2696,2491)
    assert v['tests_passed']==1769 and v['new_tests']==41
    assert ARCHIVE(PRIOR,r)==2491
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=60,passed=True,failures=0,errors=0,elapsed_seconds=1.474,
            syntax_warnings=1,warning='invalid_escape_sequence_in_new_control_path'),
        dict(tests=61,passed=True,failures=0,errors=0,elapsed_seconds=2.320,syntax_warnings=0),
        dict(tests=61,passed=True,failures=0,errors=0,elapsed_seconds=2.320,syntax_warnings=0)],
        refinements_between_runs=True,warning_fixed_before_freeze=True,frozen_full_suite_run=False,
        exploratory_models_before_freeze=True,episode_check_added_before_and_after_control_calls=True,
        earlier_unfrozen_observed_episode_elapsed_ms=62481,
        final_development_observed_episode_elapsed_ms=60870,
        controller_development_case_audit_passed=True,development_cases=10,
        controller_initial_compile_failed=True,controller_initial_compile_error='unterminated_result_string_literal',
        controller_initial_compile_exit_code=1,controller_literal_fixed_before_freeze=True,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1769,
        maximum_full_regressions=1,maximum_evidence_sets=1,evidence_cases=CASES,
        evidence_scope='six_control_injected_episodes_and_raw_callable_adapter_acquisition',
        prior_failure_records_preserved=True,portable_close_comparisons=11,ported_reader_scenarios=6,**ZERO,**FALSE))
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
    from test_synchronization_086 import run086_case
    from test_windows_adapter_086 import adapter_ready086
    cfg=dict(CASES[name]);adapter=cfg.pop('adapter',False)
    if not adapter:return run086_case(**cfg)
    w,a,p,t,ok=adapter_ready086(**cfg)
    # Only counts and transport redactions; never export pointers/paths/PIDs/SIDs.
    return dict(modeled_completed=ok,summary=t.summary(),scope='raw_callable_table_ready_acquisition',
        injected_api_calls=a.calls,api_close_attempts=a.close_attempts,
        api_unconfirmed_closes=a.unconfirmed,api_unconfirmed_frees=a.frees_unconfirmed,
        allocation_attempts=a.allocation_attempts,remaining_handles=len(w.handles),
        remaining_allocations=len(w.buffers),connect_attempts=w.connects,
        modeled_elapsed_ms=w.c.elapsed,injected_exports_exercised=len(set(w.call_names)),
        model_only_tables=True,native_boot_proof_implemented=False,native_guard_wiring_complete=False)


def audit_rows(rows):
    assert set(rows)==set(CASES)
    successes={'full_normal','full_small_guard','adapter_ready'}
    expected_full={
        'full_normal':(70,70,34,3,4,32,7,6,30561),
        'full_small_guard':(70,70,34,3,4,32,7,6,33111),
        'full_observed_guard':(61,61,30,3,4,2,6,5,99534),
        'full_wrong_error':(36,36,17,2,3,2,5,2,559),
        'full_account_change':(21,20,10,0,0,0,5,1,0),
        'full_close_uncertain':(9,9,4,0,0,0,4,0,0),
        'full_default_off':(0,0,0,0,0,0,0,0,0)}
    for name,row in rows.items():
        assert type(row['modeled_completed']) is bool and row['modeled_completed'] is (name in successes)
        s=row['summary'];c=s['counts']
        for k in ('sdk_connections','market_reads','orders','receipt_permissions'):
            assert type(s[k]) is int and s[k]==0
        for k in ('native_protocol_implemented','native_mql_verified','runtime_authorized','latency_guaranteed'):
            assert s[k] is False
        assert s['response_files_created']==0 and s['full_guards_uncached'] is True
        assert row['remaining_handles']==0 and s['physical_close_attempts']==c['closes']
        assert all(type(v) is int and v>=0 for v in c.values()) and c['guards']<=96 and c['closes']<=8
        if name.startswith('full_'):
            assert row['scope']=='full_six_control_injected_episode'
            assert (row['full_guards'],row['valid_guard_spans'],c['transactions'],c['reads'],c['writes'],
                c['waits'],c['closes'],len(row['controls']),row['modeled_elapsed_ms'])==expected_full[name]
            assert row['full_guards']==c['guards'] and row['valid_guard_spans']==s['valid_guard_spans']
            assert [p['error'] for p in row['controls']]==[0,0,32,32,0,0][:len(row['controls'])]
            assert all(p['same_file_before_after'] is True and p['companion_blockers']==0 for p in row['controls'])
            if name=='full_default_off':
                assert all(v==0 for v in c.values()) and row['backend_finish_calls']==0
                assert s['cleanup_confirmed'] is None and row['first_failure'] is None
            else:
                assert c['cleanup']==row['backend_finish_calls']==1
                assert s['cleanup_confirmed'] is (name!='full_close_uncertain')
                assert s['unconfirmed_closes']==(4 if name=='full_close_uncertain' else 0)
            if name in successes:
                assert row['frame_kinds']==[1,2,3,4] and row['first_failure'] is None
                assert row['model_match']['modeled_match'] is True
                for k in ('native_mql_verified','native_sharing_verified','runtime_authorized','orders_available'):
                    assert row['model_match'][k] is False
            if name=='full_observed_guard':
                assert row['first_failure']=='episode_deadline' and s['episode_elapsed_ms']==60870
                assert row['frame_kinds']==[1,2,3,4] and row['model_match'] is None
        else:
            assert row['scope']=='raw_callable_table_ready_acquisition' and row['model_only_tables'] is True
            assert row['remaining_allocations']==row['api_unconfirmed_frees']==0
            assert row['native_boot_proof_implemented'] is False and row['native_guard_wiring_complete'] is False
            observed=(row['injected_api_calls'],row['api_close_attempts'],row['allocation_attempts'],
                row['connect_attempts'],row['modeled_elapsed_ms'],row['injected_exports_exercised'])
            expected={'adapter_ready':(230,51,19,3,100,23),'adapter_absent':(72,4,2,64,3200,9),
                'adapter_close_uncertain':(5,1,2,0,0,7)}[name]
            assert observed==expected
            assert s['cleanup_confirmed'] is (name!='adapter_close_uncertain')
            assert row['api_unconfirmed_closes']==(1 if name=='adapter_close_uncertain' else 0)
    return dict(cases=10,modeled_completions=3,modeled_rejections=6,default_off_cases=1,
        modeled_full_six_control_completions=2,modeled_raw_adapter_ready_completions=1,
        native_sharing_episodes_proven=0,native_timing_proven=False)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    rows={name:model_case(name) for name in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,dependencies_injected=True,
        ledger_sha256=sha(LEDGER),scope='injected_full_controls_and_raw_adapter',**ZERO,**FALSE))
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
        portable_close_comparisons=11,ported_reader_scenarios=6,prior_failure_records_preserved=True,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(checks_passed=True,**counts)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checks_passed']
    assert c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/SYNCHRONIZATION-086-RESULTS.md'
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
        archive_members_verified=len(internal),tests_passed=EXPECTED,new_tests=NEW,model_cases=10,
        full_sharing_episode_proven=False,modeled_full_six_control_completions=2,native_boot_proof_implemented=False,
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
        frozen_input_coverage_complete=True,tests_passed=EXPECTED,new_tests=NEW,source_inputs=37,
        portable_close_comparisons=11,ported_reader_scenarios=6,prior_failure_records_preserved=True,next_plan_sha256=sha(PLAN),
        next_plan_executed=False,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests=EXPECTED,bindings=len(b),members=members,**counts)))


RESULT_TEXT="""# Fresh MT5 reader and Windows adapter source086 results

Prepared a fresh default-off MQL reader, Win64 DLL declarations and concrete
ctypes acquisition adapter source. All verification is offline or uses injected
callable tables; no actual DLL, SDK, MT5, MetaEditor, deployment or terminal log
was used. The native entry rejects unconditionally and real function tables
reject before binding. No market data, orders, receipts or permissions were used.

The reader uses message/nonwaiting mode, exact144-byte messages, bounded empty
polling and no response files, pipe flushes or seeks. Zero-byte successful writes
reject without resend. Its own-clock close precedes pipe reads and acts without
a peer challenge; success reporting still requires the fresh closed challenge.
Default-off performs no account/clock/file/pipe calls. Imports may load kernel32
early in a future loaded script; this phase does not load it or change settings.

The adapter source acquires raw private ACL/SID, current pipe/client modes,
process creation/session/logon, descriptor/path/ancestor identities and exact
ownership. Newly CREATE_NEW root/file/ancestor identities are measured after
creation and bound before the trailing bootstrap guard. No unrelated files are
overwritten or deleted. Temporary resources are owned before subsequent errors;
uncertain closes/free attempts remain unconfirmed and are never retried.
A fresh native boot proof and complete native SDK/image/source/helper guard
wiring remain mandatory open bindings. The injected boot callback is not a
native implementation; there is no cached or guessed boot-proof fallback.

One frozen full active suite passed1830 tests:1769 retained plus61 new, with
zero failures/errors/skips. Three earlier developer runs passed60/61/61 checks.
The first emitted one invalid-escape SyntaxWarning, fixed before freeze; the
later two emitted none. The new controller initially had one unterminated
result-string SyntaxError, corrected before freeze; its subsequent compile and
developer case audit passed. Eleven portable close-policy comparisons and six C++
ports of the actual reader control flow passed. The port confirms own-clock
close with no further peer request, backpressure rejection, actual real-account
rejection, once uncertain close and default-off calls. These are Linux g++
checks, not MQL compilation or Windows DLL ABI verification.

Ten injected evidence cases give3 modeled completions,6 rejections,1 default-off.
Normal and50ms-per-guard full six-control episodes complete with70 full guards,
original canonical ready/release/holding/closed frames, matching redacted records,
write/delete error sequence0/0/32/32/0/0 and once-confirmed cleanup. Their total
modeled durations are30561ms and33111ms. A raw callable-table adapter ready
transaction exercises all23 declared exports,230 injected calls and51 once
close attempts; it completes with no remaining model handles or allocations.

The full1611ms-per-guard scenario FAILS the unchanged60s episode deadline,
with60870ms episode elapsed (99534ms whole modeled duration),61 full/valid guards,
four canonical frames and only five completed controls. The last post/delete
control stops before further physical work at the expired deadline. Cleanup
completes once. This rejects even though the isolated ready transaction in085
passed. The guard duration is an illustrative historical observation, not a
worst-case bound; actual new-composite costs are unknown. No guard/window was
weakened or extended to make the episode pass.

Independent access-denied/error5, changed account and uncertain closes reject.
Missing adapter peer caps at64 connect attempts; initial nonwaiting TRUE means
availability, and later error535 establishes modeled connection. Uncertain
creator close is attempted once and leaves cleanup unconfirmed despite zero
remaining fake handles. Fake handle removal is not proof of native close.

All37 imported-source/header/design/policy bindings and fresh fixture/controller
inputs were frozen before the one full suite/evidence set. Prior0852696 bindings/
2491 archived members were verified; earlier failed083/084/R2 records and R3
correction remain immutable. Source/evidence hashes, archive members and model
counts were checked again at completion. Actual MQL compilation, DLL ABI,
Windows sharing/ACK and native timing remain unproven. Next087 prepares an exact
source-bound build and resolves native boot/guard bindings; it is unexecuted and
grants no native runtime authority. No user UI action is required now.

All2s/10s/30–31s/250ms/60s/120s windows, actual-DEMO/default-off guards and finite
budgets persist. Profit and070 cause remain unproven.033/035/data/cost/clock/
coverage/consumed2025/reservedNov–Dec2026/provider exclusions and old spent
markers remain; performance/annual eligibility and order availability are false.
API references and the precise changed source are in SYNCHRONIZATION-086-DESIGN.md.
"""
LATEST_TEXT=("Latest — 2026-10-08: offline fresh MQL reader/Windows acquisition source086 sealed; "
    "read SYNCHRONIZATION-086-RESULTS.md.1830 active tests/61 new,11 portable close comparisons and6 ported reader "
    "scenarios pass; zero failures/errors/skips.10 injected cases:3 modeled completions/6 rejections/1 off. "
    "Two full six-control episodes and one raw callable-table ready transaction complete; no native sharing/ACK proof. "
    "Full1611ms scenario rejects60s episode at60870ms (whole99534ms),61 valid/full guards and only5 controls; "
    "cleanup once. Normal70 guards/30561ms,50ms guard33111ms. No maxima/bounds/windows weakened. Fresh direct "
    "message/nonwaiting kernel32 reader, own-clock close/no-peer, strict records, raw ctypes ABI/ACL/SID/peer/path/"
    "descriptor/ancestor acquisition, measured CREATE_NEW identities and6 control integration prepared.37 source "
    "bindings; uncompiled/undeployed; native_entry rejects and actual tables unavailable. Native boot proof and full "
    "guard wiring are open mandatory bindings; imported DLLs may load early in a future script. Zero native/SDK/MT5/"
    "compiler/deploy/log/market/orders/receipt grants. All2s/10s/30–31s/250ms/60s/120s/default-off/actual-DEMO gates "
    "retained. Prior0852696 bindings/2491 members verified; all failed records/spent markers/data/reserved/provider "
    "gates retained. Profit/070 cause/native timing unproven; eligibility/orders false. Next087 source-bound build "
    "and native binding review unexecuted; no UI action required. Earlier entries historical.\n\n")


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
