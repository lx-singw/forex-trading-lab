"""Offline freeze/test/evidence/closure only. No native run or authorization."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import time
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/sharing-adapter-076.py'))
sha, sealed, write, bound = (API[k] for k in ('sha','sealed','write','bound'))
HANDOFF, ARCHIVE = API['HANDOFF'], API['ARCHIVE']
PREFIX = 'timing-profile-077'
LEDGER = ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR = ROOT/'reports/sharing-adapter-076-final-source.json'
PRIOR_PLAN = ROOT/'docs/NATIVE-SHARING-077-PLAN.md'
DESIGN = ROOT/'docs/TIMING-PROFILE-077-DESIGN.md'
POLICY = ROOT/'docs/TIMING-PROFILE-077-POLICY-DRAFT.md'
PLAN = ROOT/'docs/NATIVE-TIMING-078-PLAN.md'
EXPECTED, NEW = 1453, 45
PATTERNS = ('scripts/*077.py','src/forex_demo_lab/*077.py','tests/*077.py',
    'docs/TIMING-PROFILE-077*.md','docs/NATIVE-TIMING-078-PLAN.md')
ZERO = dict(sdk_connections=0,mt5_runtime_invocations=0,terminal_deployments=0,
    terminal_log_content_reads=0,native_metatrader_compiler_invocations=0,
    native_self_profiles=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE = {**API['FALSE'], 'native_protocol_implemented':False, 'latency_guaranteed':False,
    'native_launch_ready':False}
PROFILE_CASES = dict(zero=0,small=100,slow=1000,expires=10000)
# Offsets are absolute boot offsets from the fresh modeled episode origin.
SYNC_CASES = dict(
    normal=dict(times=[0,1,10,510,610]),
    slow_guards=dict(times=[0,1,10,510,610],guard_ms=1001),
    stale_ready=dict(times=[2001,2002,2010,2510,2610],stale_index=0,stale_ms=2001),
    wrong_phase=dict(times=[0,1,10,510,610],change_index=0,change='phase'),
    replaced_identity=dict(times=[0,1,10,510,610],change_index=3,change='identity'),
    duplicate_release=dict(times=[0,1,2],kinds=['ready','release','release']),
    restart=dict(times=[],restart=True),
    launch_deadline=dict(times=[0,1,10001,10501,10601]),
    launch_outside=dict(times=[0,1,10002,10502,10602]),
    start_margin=dict(times=[0,1,10,260,610]),
    start_inside=dict(times=[0,1,10,261,610]),
    end_margin=dict(times=[0,1,10,510,29760]),
    end_inside=dict(times=[0,1,10,510,29759]),
    deadline=dict(times=[0,19750,19751,20251,20351]))


def freeze():
    assert sha(PRIOR) == 'fdc220659fa3219ac5ceb0462dcacf818a7aa467ad07ee4285423279b58c2dd0'
    p = sealed(PRIOR); r = sealed(ROOT/'reports/sharing-adapter-076-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256'] == sha(PRIOR)
    assert (r['tests_passed'],r['bindings_verified'],r['archive_members_verified']) == (1408,2398,2214)
    assert r['next_plan_sha256'] == sha(PRIOR_PLAN) == '0a36ebe5b599d7855a616d2abf9d1a4f0102d01ca2470dcc91a07e95a54fdc72'
    assert not r['next_plan_executed'] and r['timing_cases_verified'] == 8
    b = dict(p['source_and_evidence_bindings'])
    for n,h in b.items(): assert sha(bound(n)) == h,n
    assert ARCHIVE(PRIOR,p) == 2214
    API['verify'](); retained = API['compiled_evidence']()[1]
    for n in HANDOFF: b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        ROOT/'reports/sharing-adapter-076-completion-review.json',
        ROOT/'reports/sharing-adapter-076-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()] = sha(path)
    selected = {}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            n=path.relative_to(ROOT).as_posix(); b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),draft_policy_sha256=sha(POLICY),future_plan_sha256=sha(PLAN),
        retained_build=retained,profile_cases=PROFILE_CASES,handshake_cases=SYNC_CASES,
        preparation_date=datetime.now(timezone.utc).date().isoformat(),
        phase='77000000000000000000000000000001',tests_retained=1408,expected_tests=EXPECTED,
        new_tests=NEW,maximum_full_regressions=1,maximum_native_sessions=0,
        prior_bindings_verified=2398,prior_archive_members_verified=2214,**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected): z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',
        dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items(): assert sha(bound(n))==h,n
    for key,path in (('prior_source_sha256',PRIOR),('prior_plan_sha256',PRIOR_PLAN),
        ('design_sha256',DESIGN),('draft_policy_sha256',POLICY),('future_plan_sha256',PLAN)):
        assert l[key]==sha(path)
    assert l['retained_build']==API['compiled_evidence']()[1]
    assert l['profile_cases']==PROFILE_CASES and l['handshake_cases']==SYNC_CASES
    return l


def test():
    verify(); sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',
        dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic()
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in r.failures+r.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed: raise SystemExit(1)


def modeled_handshake(case):
    from forex_demo_lab.timing_profile_077 import Handshake077,HandshakeMeter077,Signal077,SYNC_PHASE
    from test_timing_profile_077 import Clock077,build077
    from forex_demo_lab.sharing_probe_062 import ProbeRejected
    with TemporaryDirectory() as d:
        clock=Clock077(); meter=HandshakeMeter077(clock)
        def guard():
            meter.consume('guards'); clock.advance(case.get('guard_ms',0)); return True
        path=Path(d)/'episode'; h=Handshake077(path,build077(),(1,2,3),meter,guard)
        restart_refused=False
        if case.get('restart'):
            try: Handshake077(path,build077(),(1,2,3),HandshakeMeter077(clock),guard)
            except ProbeRejected: restart_refused=True
        else:
            kinds=case.get('kinds',['ready','release','holding','write','delete'])
            for i,offset in enumerate(case['times']):
                clock.advance(h.origin+offset-clock.boot)
                stamp=clock.boot-(case.get('stale_ms',0) if case.get('stale_index')==i else 0)
                phase=SYNC_PHASE; identity=h.identity
                if case.get('change_index')==i:
                    if case['change']=='phase': phase='0'*32
                    else: identity=(1,2,4)
                signal=Signal077(kinds[i],phase,h.build.sha256,identity,h.origin,h.deadline,stamp,stamp)
                try: h.accept(signal)
                except ProbeRejected: break
        return dict(report=h.report(),guards=meter.counts['guards'],restart_refused=restart_refused,
            episode_marker_preserved=path.exists())


def evidence():
    l=verify(); sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from test_timing_profile_077 import fixture077,guard077
    from forex_demo_lab.timing_profile_077 import profile_once077
    profiles={}
    for name,cost in PROFILE_CASES.items():
        with TemporaryDirectory() as d:
            f=fixture077(Path(d),cost=cost)
            out=profile_once077(f.owner,guard077(f))
            profiles[name]=dict(observation=out,injected_initializations=f.calls.count('initialize'),
                injected_shutdowns=f.calls.count('shutdown'),dependencies_injected=True)
    handshakes={name:modeled_handshake(case) for name,case in SYNC_CASES.items()}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(ledger_sha256=sha(LEDGER),
        retained_build=l['retained_build'],profiles=profiles,handshakes=handshakes,
        observations_injected=True,native_timing_unknown=True,old070_root_cause_unknown=True,
        **ZERO,**FALSE))
    print(json.dumps(dict(profile_cases=len(profiles),handshake_cases=len(handshakes),native_sessions=0)))


def reference_handshake(case):
    # Independently enumerate guard placement and absolute signal windows. This
    # does not call Handshake077 or any of its methods/helpers.
    expected=['ready','release','holding','write','delete']; events=[]
    guards=0; release=hold=None; g=case.get('guard_ms',0)
    if case.get('restart'): return dict(completed=False,events=[],guards=0,restart_refused=True)
    for i,t in enumerate(case['times']):
        kind=case.get('kinds',expected)[i]
        stamp=t-(case.get('stale_ms',0) if case.get('stale_index')==i else 0)
        if i>=5 or kind!=expected[i] or case.get('change_index')==i or t>=60000: break
        guards+=1; after=t+g
        if after>=60000 or after-stamp>2000: break
        if kind=='holding':
            if not release<=stamp<=release+10000: break
            hold=stamp
        if kind in ('write','delete'):
            if not hold+250<stamp<hold+29750: break
        if kind=='release': release=after
        guards+=1; end=after+g
        if (end>=60000 or end-stamp>2000 or kind=='release' and end+40250>=60000 or
            kind in ('write','delete') and end>=hold+29750): break
        events.append(kind)
    return dict(completed=events==expected,events=events,guards=guards,restart_refused=False)


def check():
    l=verify(); t=sealed(ROOT/f'reports/{PREFIX}-tests.json'); e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER)
    assert e['retained_build']==API['compiled_evidence']()[1]
    assert set(e['profiles'])==set(PROFILE_CASES) and set(e['handshakes'])==set(SYNC_CASES)
    references={}
    for name,cost in PROFILE_CASES.items():
        value=e['profiles'][name]; r=value['observation']
        # Four process-image hashes occur during the injected attach. A core
        # guard hashes helper/terminal twice then editor/artifact; a composite
        # adds launcher/config/library/image and four source/header hashes.
        elapsed=0
        for _ in range(4): elapsed+=cost
        wanted=[]
        for _ in range(4):
            a=elapsed
            for _ in range(6): elapsed+=cost
            first=elapsed-a; chain_start=elapsed
            for _ in range(8): elapsed+=cost
            b=elapsed
            for _ in range(6): elapsed+=cost
            if elapsed>=600000: break
            wanted.append(dict(core_guard_ms=[first,elapsed-b],composite_sample_ms=elapsed-a,
                hash_reads=20,hash_bytes=20*1048576,sdk_queries=22))
        assert r['samples']==wanted and r['samples_completed']==len(wanted)
        assert type(r['completed']) is bool and r['completed']==(len(wanted)==4)
        assert r['observed_core_guard_max_ms']==6*cost
        assert r['observed_composite_max_ms']==20*cost
        assert r['cleanup']['sdk_shutdown_called'] and value['injected_shutdowns']==value['injected_initializations']==1
        assert value['dependencies_injected'] and r['counts']['sdk_connections']==r['counts']['sdk_shutdowns']==1
        assert r['observations_only'] and not r['latency_guaranteed'] and not r['native_launch_ready']
        assert not r['runtime_authorized'] and not r['native_timing_verified'] and not r['orders_available']
        assert r['preparation_contract_sha256'] and r['build_record_sha256']
        from forex_demo_lab.timing_profile_077 import LIMITS077
        assert all(type(v) is int and 0<=v<=LIMITS077[k] for k,v in r['counts'].items())
        for k in ('script_arms','deployment_directories','deployment_writes','log_reads','log_bytes','reads','writes'):
            assert r['counts'][k]==0
        references[name]=dict(completed_samples=len(wanted),core_ms=6*cost,composite_ms=20*cost)
    sync_refs={}
    for name,case in SYNC_CASES.items():
        ref=reference_handshake(case); value=e['handshakes'][name]; r=value['report']; sync_refs[name]=ref
        assert type(r['modeled_completed']) is bool and r['modeled_completed']==ref['completed'],name
        assert r['events']==ref['events'] and value['guards']==ref['guards'],name
        assert value['restart_refused']==ref['restart_refused'] and value['episode_marker_preserved']
        assert not r['native_protocol_implemented'] and not r['native_launch_ready'] and not r['runtime_authorized']
        assert (r['launch_gate_ms'],r['hold_ms'],r['margin_ms'])==(10000,30000,250)
    assert sum(r['completed'] for r in sync_refs.values())==4
    for data in (l,t,e):
        for k,v in {**ZERO,**FALSE}.items(): assert type(data[k]) is type(v) and data[k]==v
    assert e['observations_injected'] and e['native_timing_unknown'] and e['old070_root_cause_unknown']
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json'); path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items(): assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    for n in ('native-timing-077-runtime.json','native-timing-077-authorization.json',
        'native-timing-077-dispatch-started.json','native-timing-077-reservation.json'):
        assert not (ROOT/'reports'/n).exists()
    assert not list(ROOT.glob('mt5/**/ForexDemoSharing072.ex5'))
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,retained_build_validated=True,profile_references=references,
        handshake_references=sync_refs,profile_cases_verified=4,handshake_cases_verified=14,
        modeled_completions=4,modeled_rejections=10,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,profile_cases=4,handshake_cases=14)))


def seal():
    l=verify(); c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    text=(f'# Timing profile077 preparation results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'The metadata-only injected runner, exact preparation policy, exclusive reservation, SDK/backend ownership and '
        'once-owned cleanup are prepared. Four composite samples include eight actual account/process/full-hash guards; '
        'all helper/source inputs are rehashed. Small clock/query/byte caps and zero fixture/deployment/log budgets are tested.\n\n'
        'Four profile cases independently enumerated: three complete all samples, one expires after two. '
        'Core versus composite timings are separate observations. One-second simulated hash costs yield6000ms core '
        'guards and20000ms composite samples. These are injected costs, not native measurements or worst-case bounds. '
        'Expiration preserves partial samples and attempts owned cleanup without retry.\n\n'
        'Fourteen finite readiness/release transcripts independently checked:4 modeled completions/10 rejections. '
        'Fresh phase/build/same private identity/absolute deadline binding, stale signals, restart, duplicate release, '
        'guard overhead and unchanged10s/30s strict250ms hold margins are checked. Release failure stays spent. '
        'The handshake has no native transport, MQL decoder/hold handle or matcher; source072 cannot use it.\n\n'
        'Zero new native SDK/MT5/compiler/deployment/log-content/self-profile/market/order/receipt operations. '
        'Exact075 actual-exit1 build retained;072/075/076 and all old failures/raw reservations preserved. '
        'Observed maxima never grant launch authority. Native sharing/publication/ACK/profitability and070 cause remain '
        'unproven; eligibility/orders false.033/035 failures, clock/cost/coverage flags, consumed2025, reserved Nov-Dec2026 '
        'and provider stops retained. Next NATIVE-TIMING-078-PLAN.md prepares a separately frozen/tested metadata-only '
        'native entry/policy before a later finite profile. Unexecuted; Oct8 expiry requires fresh metadata sampler/phase.\n')
    with (ROOT/'docs/TIMING-PROFILE-077-RESULTS.md').open('x') as f: f.write(text)
    handoff=(f'Latest — 2026-10-08: offline timing-profile077 sealed; read TIMING-PROFILE-077-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass. Four fixed composite profile samples/eight full guards, exact no-authority '
        'policy, uncached helper/source/build bindings, exclusive reservation and once-owned SDK/backend cleanup prepared. '
        'Four independent injected timing cases:3 complete/1 expires after2 samples;14 readiness/release transcripts: '
        '4 modeled completions/10 rejections. Native timing is unknown; maxima grant no launch authority. The handshake '
        'is a finite state model with no MQL/native transport;10s/30s/250ms gates preserved. Retained075 actual-exit1 '
        'artifact and076 timing unchanged. Zero new native SDK/MT5/compiler/deploy/log/profile/market/orders/grants. '
        'Sharing/publication/ACK/profit and070 cause unproven. Next078 metadata-only entry/policy preparation unexecuted; '
        'Oct8 expiry needs fresh profile date/phase/sampler, later MQL needs fresh source/matcher/build. All old failures/ '
        'raw spent markers/data gates retained. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n; s=path.read_text(); i=s.index('\n')+1
        path.write_text(s[:i]+'\n'+handoff+s[i:]); b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern): b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items(): assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}; final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal): z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,retained_build_validated=True,profile_cases_verified=4,handshake_cases_verified=14,
        modeled_completions=4,modeled_rejections=10,future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record); write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json'; r=sealed(final); l=sealed(LEDGER); b=r['source_and_evidence_bindings']
    for n,h in b.items(): assert sha(bound(n))==h,n
    members=ARCHIVE(final,r); assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json'); assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN) and not r['future_plan_executed']
    assert l['retained_build']==API['compiled_evidence']()[1]
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,retained_build_validated=True,
        profile_cases_verified=4,handshake_cases_verified=14,modeled_completions=4,modeled_rejections=10,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,tests_passed=EXPECTED)))


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('freeze','test','evidence','check','seal','review','verify'))
    dict(freeze=freeze,test=test,evidence=evidence,check=check,seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
