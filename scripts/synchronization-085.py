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
API=runpy.run_path(str(ROOT/'scripts/synchronization-084-r3.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='synchronization-085';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/synchronization-084-r3-final-source.json'
REVIEW=ROOT/'reports/synchronization-084-r3-completion-review.json'
DESIGN=ROOT/'docs/SYNCHRONIZATION-085-DESIGN.md'
POLICY=ROOT/'docs/SYNCHRONIZATION-085-POLICY.md'
PLAN=ROOT/'docs/SYNCHRONIZATION-086-PLAN.md'
OWN=('scripts/synchronization-085.py','src/forex_demo_lab/synchronization_085.py',
    'tests/test_synchronization_085.py','mt5/Scripts/Synchronization085.mqh',
    'docs/SYNCHRONIZATION-085-DESIGN.md','docs/SYNCHRONIZATION-085-POLICY.md',
    'docs/SYNCHRONIZATION-086-PLAN.md')
EXPECTED,NEW=1769,41
CASES=dict(default_off={'enabled':False},normal={},observed_guard={'guard_ms':1611},
    slow_guard={'guard_ms':2000},no_data_then_reply={'no_data':3},no_data_exhausted={'no_data':1000},
    backpressure={'write_result':{'succeeded':True,'error':0,'count':0}},stale={'stale_ms':1},
    changed_peer={'change':'peer'},replaced_path={'change':'path'},
    changed_account={'bad_guard_at':4,'bad_guard':{'same_account':False}},
    close_uncertain={'close_uncertain':True},autonomous_absent_peer={'autonomous':True},
    autonomous_slow_guard={'autonomous':True,'guard_ms':1611},
    autonomous_scheduler_late={'autonomous':True,'late_ms':1001})


def proposal():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.synchronization_085 import source_contract085
    return source_contract085(ROOT)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='0cecf20b988c1f99d1af50ae81715ec7b26a380f3ca2e41a8141f3fcd658202e'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2666,2463)
    assert v['full_tests_retained']==1720 and v['audit_tests_passed']==8 and not v['full_suite_rerun']
    assert ARCHIVE(PRIOR,r)==2463
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=37,passed=True,failures=0,errors=0,elapsed_seconds=1.369),
        dict(tests=41,passed=True,failures=0,errors=0,elapsed_seconds=1.283)],
        refinements_between_runs=True,frozen_full_suite_run=False,
        controller_development_case_audit_passed=True,development_cases=15,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1728,
        maximum_full_regressions=1,maximum_evidence_sets=1,evidence_cases=CASES,
        evidence_scope='isolated_ready_transactions_and_autonomous_close_schedules',
        prior_failure_records_preserved=True,portable_close_comparisons=11,**ZERO,**FALSE))
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
    suite,retired=API['API']['active_suite']();assert suite.countTestCases()==EXPECTED and retired==43
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
    from dataclasses import replace
    from test_synchronization_085 import bindings085,transport_case085,autonomous_case085
    cfg=dict(CASES[name]);autonomous=cfg.pop('autonomous',False);change=cfg.pop('change',None)
    if change=='peer':cfg['pipe_change']={'client':replace(bindings085().peer,created=1)}
    if change=='path':cfg['file_change']={'identity':(8,20,10)}
    return autonomous_case085(**cfg) if autonomous else transport_case085(**cfg)


def audit_rows(rows):
    assert set(rows)==set(CASES)
    successes={'normal','observed_guard','no_data_then_reply','autonomous_absent_peer'}
    for name,row in rows.items():
        assert row['modeled_completed'] is (name in successes)
        if name.startswith('autonomous_'):
            assert row['close_spent'] is True and row['close_confirmed'] is True and row['close_calls']==1
            assert row['peer_requests']==0 and row['close_depends_on_peer'] is False and row['full_guards']==2
            assert row['native_protocol_implemented'] is False and row['latency_guaranteed'] is False
            assert row['runtime_authorized'] is False
            for k in ('sdk_connections','market_reads','orders','receipt_permissions'):assert type(row[k]) is int and row[k]==0
            continue
        s=row['summary'];counts=s['counts']
        assert row['episode_scope']=='isolated_ready_transaction'
        assert row['full_guards']==counts['guards']<=96 and row['valid_guard_spans']==len(row['guard_spans'])
        assert row['valid_guard_spans']<=row['full_guards']
        if name in ('changed_peer','replaced_path','changed_account'):
            assert row['full_guards']==row['valid_guard_spans']+1
        else:assert row['full_guards']==row['valid_guard_spans']
        for k in ('sdk_connections','market_reads','orders','receipt_permissions'):
            assert type(s[k]) is int and s[k]==0
        for k in ('native_protocol_implemented','native_mql_verified','runtime_authorized','latency_guaranteed'):
            assert s[k] is False
        assert s['response_files_created']==0 and s['full_guards_uncached'] is True
        assert row['handles_remaining']==0 and row['message_writes']<=1
        assert row['read_attempts']<=16 and row['poll_waits']<=15
        assert counts['reads']==row['read_attempts'] and counts['writes']==row['message_writes']
        assert counts['waits']==row['poll_waits']
        if name=='default_off':
            assert all(v==0 for v in counts.values()) and row['backend_finish_calls']==0
            assert row['private_inspections']==0 and row['modeled_elapsed_ms']==0
        else:
            assert counts['cleanup']==row['backend_finish_calls']==1 and counts['closes']==s['physical_close_attempts']==3
            assert s['cleanup_confirmed'] is (name!='close_uncertain')
            assert s['unconfirmed_closes']==(3 if name=='close_uncertain' else 0)
        if name in successes:
            assert len(row['original_message_sha256'])==64 and row['message_age_after_guard_ms']<=2000
            assert row['full_guards']==row['valid_guard_spans']==4
    assert rows['observed_guard']['modeled_elapsed_ms']==6446
    assert rows['observed_guard']['message_age_after_guard_ms']==1612
    assert rows['no_data_then_reply']['read_attempts']==4 and rows['no_data_then_reply']['poll_waits']==3
    assert rows['no_data_exhausted']['read_attempts']==16 and rows['no_data_exhausted']['poll_waits']==15
    assert rows['backpressure']['message_writes']==1 and rows['backpressure']['read_attempts']==0
    assert rows['autonomous_absent_peer']['hold_elapsed_at_close_ms']==30000
    assert rows['autonomous_slow_guard']['hold_elapsed_at_close_ms']==31611
    assert rows['autonomous_scheduler_late']['hold_elapsed_at_close_ms']==31001
    return dict(cases=15,modeled_completions=4,modeled_rejections=10,default_off_cases=1,
        completed_isolated_message_cases=3,completed_autonomous_close_cases=1,
        complete_sharing_episodes_proven=0,native_timing_proven=False)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    rows={name:model_case(name) for name in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,dependencies_injected=True,
        ledger_sha256=sha(LEDGER),scope='isolated_message_and_close_policy',**ZERO,**FALSE))
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
        portable_close_comparisons=11,prior_failure_records_preserved=True,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(checks_passed=True,**counts)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checks_passed']
    assert c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/SYNCHRONIZATION-085-RESULTS.md'
    text=('''# Held message and autonomous-close redesign085 results

Prepared an injected held-pipe-message transport and autonomous own-clock close
policy. Response-file publication is removed; original immutable144-byte peer
messages and the physical private pipe instance stay held across full trailing
guards. Fresh raw account/private peer/ACL/root/file/descriptor/path/ancestor
facts are checked inside every full uncached composite. Default-off calls no
clock/guard/factory/close. Nonwaiting exact-message/no-data/backpressure contracts,
bounded polling, once-release/cleanup and typed ownership are implemented.

One fresh active full suite passed1769 tests:1728 prior active checks plus41 new.
No failures/errors/skips. Retired08343/08436 fixture classes are excluded by084
R2 active_suite(); R3 eight auditors are now included in a full run. Eleven
portable g++/Python close-policy comparisons passed; these are not MT5 builds.
Two earlier developer runs passed37 and41 checks, before this frozen run.

Fifteen injected evidence cases:4 modeled completions,10 rejections,1 default-off.
Only three isolated ready transactions and one autonomous close schedule complete;
no complete sharing episode/native execution is proven. The1611ms-per-composite
scenario takes6446ms/four full guards; its original message is1612ms old after the
trailing guard, within unchanged2s freshness. A2000ms guard rejects freshness.
The new composite includes additional acquisition obligations; its native cost
is unknown. Neither1611ms nor any historical observed maximum is a bound.

Empty pipe polls cap at16 reads/15 ten-ms waits, without resending. Zero-byte
successful writes/backpressure, partial/extra messages, stale frames, replaced
peer/path/account and uncertain closes reject. All model handles have one close
attempt; uncertain closes remain unconfirmed and are not retried. Started guards
and valid spans differ by one in injected proof-rejection cases; no missing
completed span is fabricated.

The close policy acts at30000ms with zero peer requests. A1611ms close guard
moves the modeled close to31611ms and invalidates it; scheduler arrival at31001ms
also attempts once but rejects. It removes the design dependency on a closed
challenge; it cannot guarantee physical scheduling or native close latency.

The pure Synchronization085.mqh header has no IO or MQL entry point. The retained
084 reader still blocks and cannot consume085. Fresh MQL reader, Windows backend,
full six-control integration, strict native record matching and source-bound
compilation remain next086 preparation. All35 source/import/include/design/policy
bindings are conservative; retained084 MQL inputs are historical, not an085
candidate build. This phase is uncompiled/undeployed, with zero native/SDK/MT5/
MetaEditor/deploy/log/market/order/receipt invocations or grants.

The original083/084 fixture failures, R2 checker exit1 and084 R3 correction remain
immutable. Prior2666 bindings/2463 members were verified. All2s/10s/30–31s/250ms/
60s/120s and uncached actual-DEMO/default-off guards remain. Native sharing/ACK,
profitable edge and070 cause remain unproven.033/035/data/cost/coverage/consumed2025/
reservedNov–Dec2026/provider exclusions and old spent markers persist;
eligibility/orders remain false. Next086 is unexecuted; no user UI action required.

API rationale and precise changed grouping are in SYNCHRONIZATION-085-DESIGN.md;
Microsoft's message/nonwaiting/flush behavior supports the contract choice,
which remains a design inference rather than measured Windows behavior.
''')
    with result.open('x') as f:f.write(text)
    latest=('Latest — 2026-10-08: offline held-message/own-clock-close redesign085 sealed; read SYNCHRONIZATION-085-RESULTS.md. '
        '1769 active tests/41 new/11 portable close comparisons pass, zero failures/errors/skips.15 injected cases:4 completions/'
        '10 rejections/1 default-off; only3 isolated ready transactions and1 autonomous schedule, no full sharing/native episode. '
        'Response files removed, original144-byte message and private pipe held across full trailing guards; fresh account/peer/'
        'ACL/root/file/path/descriptor/ancestors inside every uncached composite, explicit transaction grouping.1611ms scenario '
        'four guards/6446ms/age1612ms fits2s in isolation;2000ms guard rejects. Empty peer own-clock close30000ms;1611ms close '
        'guard causes31611ms late rejection. No maxima/bounds/preemption claims. Finite no-data polling, backpressure/no resend, '
        'once cleanup tested.35 source bindings; pure header only, no fresh MQL entry/native backend/build/integration. All '
        '2s/10s/30–31s/250ms/60s/120s limits retained.084/R2 failures/R3 correction/082 observations/spent081 preserved. '
        'Zero native/SDK/MT5/compiler/deploy/log/market/orders/grants. Next086 fresh reader/Windows adapter source preparation '
        'unexecuted; no UI action. Native sharing/ACK/profit/070 cause/eligibility/orders unproven/false; all data/reserved/provider '
        'gates retained. Earlier entries historical.\n\n')
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
        archive_members_verified=len(internal),tests_passed=EXPECTED,new_tests=NEW,model_cases=15,
        full_sharing_episode_proven=False,next_plan_executed=False,**ZERO,**FALSE)
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
        frozen_input_coverage_complete=True,tests_passed=EXPECTED,new_tests=NEW,source_inputs=35,
        portable_close_comparisons=11,prior_failure_records_preserved=True,next_plan_sha256=sha(PLAN),
        next_plan_executed=False,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests=EXPECTED,bindings=len(b),members=members,**counts)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
