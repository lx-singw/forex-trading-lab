"""Exclusive offline feasibility actions; no native authority or new reader."""
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
API=runpy.run_path(str(ROOT/'scripts/compound-089.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='source-feasibility-090';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/compound-089-final-source.json'
REVIEW=ROOT/'reports/compound-089-completion-review.json'
DESIGN=ROOT/'docs/SOURCE-FEASIBILITY-090-DESIGN.md'
POLICY=ROOT/'docs/SOURCE-FEASIBILITY-090-POLICY.md'
PLAN=ROOT/'docs/RESEARCH-091-PLAN.md'
OWN=('scripts/source-feasibility-090.py','src/forex_demo_lab/source_feasibility_090.py',
    'tests/test_source_feasibility_090.py','docs/SOURCE-FEASIBILITY-090-DESIGN.md',
    'docs/SOURCE-FEASIBILITY-090-POLICY.md','docs/RESEARCH-091-PLAN.md')
EXPECTED,NEW=1942,27
CASES=dict(reader_bounded={},old_source_change={'mutation':'source_change'},
    new_source_change={'mutation':'source_change','new_source_only':True},
    account_real={'mutation':'account_real'},account_contest={'mutation':'account_contest'},
    peer_change={'mutation':'peer_change'},default_off={'enabled':False})
ACTIVE=API['ACTIVE']


def proposal():
    sys.path[:0]=[str(ROOT/'src')]
    from forex_demo_lab.source_feasibility_090 import feasibility090, CAPS, SOURCE
    names=set(API['proposal']()['input_bindings'])|set(OWN)|{
        'src/forex_demo_lab/private_guard_065.py','src/forex_demo_lab/native_files_065.py',
        'src/forex_demo_lab/sharing_companion_065.py'}
    return dict(version='source_feasibility_090_v1',review_date='2026-10-09',
        historical_fixture_date='2026-10-08',input_bindings={n:sha(ROOT/n) for n in sorted(names)},
        feasibility=feasibility090(),native_reader_caps=dict(CAPS),
        accounting_source=SOURCE,accounting_scope='original065_numeric_predicates_only',
        new_reader_implemented=False,native_date_admission=False,native_experiment_can_proceed=False,
        runtime_authorized=False,orders_available=False)


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='00fcbb68757fe6f58302d08f9d416386c80df2828df54242939bfc008826c0d2'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'])==(2820,2607)
    assert (v['tests_passed'],v['new_tests'])==(1915,31)
    assert ARCHIVE(PRIOR,r)==2607
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    development=ROOT/f'reports/{PREFIX}-development-checks.json'
    write(development,dict(origin='tool_outputs_before_freeze',targeted_test_runs=[
        dict(tests=23,passed=True,failures=0,errors=0,elapsed_seconds=3.676),
        dict(tests=27,passed=True,failures=0,errors=0,elapsed_seconds=5.184)],
        all_old_date_and_count_gates_unchanged=True,frozen_full_suite_run=False,
        controller_development_case_audit_passed=True,development_cases=7,**ZERO,**FALSE))
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256'),
              development,development.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected);prop=proposal()
    for n,h in prop['input_bindings'].items():assert b[n]==h,n
    write(LEDGER,dict(bindings=b,proposal=prop,prior_source_sha256=sha(PRIOR),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        expected_tests=EXPECTED,new_tests=NEW,prior_active_tests=1915,
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
    from test_source_feasibility_090 import coupled090
    return coupled090(**CASES[name])


def audit_rows(rows,inventory):
    assert set(rows)==set(CASES)
    f=inventory['feasibility'];p=inventory['projection'];proofs=inventory['proofs']
    assert (f['source_reads'],f['explicit_reads'],f['identity_image_reads'],f['reader_reads'],f['hash_read_cap'])==(3116,4100,152,4252,768)
    assert not f['source_only_fits'] and not f['contract_fits'] and not f['native_experiment_can_proceed']
    assert len(proofs)==50 and sum(x['reads'] for x in proofs)==4252
    assert len({x['name'] for x in proofs})==50
    assert sum(x['reads'] for x in proofs if not x['name'].startswith('role:'))==3116
    assert p['projected_counts']['hash_reads']==4252 and set(p['exceeded'])=={'hash_reads','hash_path_stats'}
    assert p['arithmetic_projection_only'] and not p['native_cost_proven']
    from forex_demo_lab.source_feasibility_090 import CAPS
    for name,r in rows.items():
        assert not r['modeled_completed'] and not r['runtime_authorized'] and not r['orders_available']
        assert not r['native_reader_verified'] and not r['native_date_admission'] and not r['new_reader_implemented']
        for k in ('native_invocations','sdk_connections','market_reads','orders'):
            assert type(r[k]) is int and r[k]==0
        assert r['historical_fixture_date']=='2026-10-08'
        assert r['sdk_cleanup_confirmed'] and r['sdk_shutdown_attempts']==1
        assert r['summary']['cleanup_confirmed'] and r['reader_model_owned_remaining']==0
        assert r['remaining_handles']==r['remaining_allocations']==0 and not r['reader_cleanup_exceeded']
        assert r['reader_count_scope']=='065_original_numeric_predicates_with_injected_acquisitions'
        counts=r['reader_counts']
        assert all(type(counts[k]) is int and 0<=counts[k]<=CAPS[k] for k in CAPS)
        assert counts['closes']==r['reader_model_close_attempts']
        assert counts['local_frees']==r['reader_model_free_attempts']
        if name=='reader_bounded':
            assert r['reader_first_exhausted']=='hash_reads' and counts['hash_reads']==r['hash_reads']==768
            assert (r['bridge_calls'],r['summary']['valid_guard_spans'],len(r['controls']))==(7,6,1)
            assert (r['api_calls'],r['api_clock_samples'],r['sdk_queries'],r['boot_queries'])==(301,603,78,13)
            assert (r['reader_identity_hashes'],counts['process_snapshots'],counts['native_calls'])==(26,13,260)
            assert (counts['closes'],counts['local_frees'],counts['token_queries'])==(65,26,78)
        elif name=='default_off':
            assert counts['hash_reads']==counts['native_calls']==r['api_calls']==r['sdk_queries']==0
        else:
            assert r['mutation_injected'] and r['reader_first_exhausted'] is None
            assert r['summary']['valid_guard_spans']==1 and len(r['controls'])==0
    return dict(cases=7,count_budget_rejections=1,current_fact_change_rejections=5,default_off_cases=1,
        source_only_required_reads=3116,full_target_required_reads=4252,unchanged_hash_read_cap=768,
        native_experiment_can_proceed=False,new_reader_implemented=False,native_reader_verified=False)


def evidence():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');assert t['passed'] and t['tests_run']==EXPECTED
    assert t['ledger_sha256']==sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-evidence-started.json',dict(evidence_set_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from test_source_feasibility_090 import inventory090
    rows={n:model_case(n) for n in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(cases=rows,inventory=inventory090(),
        dependencies_injected=True,ledger_sha256=sha(LEDGER),
        scope='count_only_original_reader_predicates_and_arithmetic_proof_lower_bound',**ZERO,**FALSE))
    print(json.dumps(dict(recorded_cases=len(rows))))


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and (t['tests_run'],t['new_tests'],t['failures'],t['errors'],t['skipped'])==(EXPECTED,NEW,0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and e['dependencies_injected'] is True
    counts=audit_rows(e['cases'],e['inventory']);initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json')
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
    result=ROOT/'docs/SOURCE-FEASIBILITY-090-RESULTS.md'
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
        tests_passed=EXPECTED,new_tests=NEW,model_cases=7,full_sharing_episode_proven=False,
        native_experiment_can_proceed=False,new_reader_implemented=False,
        native_boot_proof_implemented=False,native_guard_wiring_complete=False,next_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,r);write(final,r)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();f=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(f);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(f,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json');counts=audit_rows(e['cases'],e['inventory'])
    assert c['checks_passed'] and c['ledger_sha256']==sha(LEDGER) and t['passed'] and t['tests_run']==EXPECTED
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert not r['next_plan_executed'] and not r['full_sharing_episode_proven'] and not r['new_reader_implemented']
    assert not r['native_experiment_can_proceed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(f),
        bindings_verified=len(b),archive_members_verified=members,frozen_inputs_verified=len(l['bindings']),
        frozen_input_coverage_complete=True,tests_passed=EXPECTED,new_tests=NEW,
        source_inputs=len(l['proposal']['input_bindings']),prior_failure_records_preserved=True,
        retained_portable_close_comparisons=11,retained_ported_reader_scenarios=6,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**counts,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests=EXPECTED,bindings=len(b),members=members,**counts)))


RESULT_TEXT="""# Source-proof feasibility090 results

The native experiment **cannot proceed under the current contract**. All41
individual sources must be freshly hashed before and after each of38 guards:
3,116 reads already exceed the unchanged768 cap. Even a disallowed single pass
requires1,558. Nine image/helper/SDK roles and75 fresh boot queries increase the
explicit target to4,100. The actual native065 identity method additionally
hashes terminal/helper images at each boundary:152 reads, bringing the target
to **4,252**. No valid archive/manifest/cache/batch representation removes the
required individual current-file observations. No cap/proof/date/window changed.

The new module accounts for costs; it is not a native reader. Original065
consume/cleanup predicates are used directly with injected file/process facts.
The full six-control historical089 target rejects on guard7 after6 valid spans
and1 control at exactly768 reads. Raw301 calls/603 clock checks,78 SDK queries,
13 boot queries. Reader accounting includes26 identity image hashes,26 process
opens/tokens,13 snapshots/26 injected entries,260 modeled native calls and78
token queries. All65 registered reader-model close attempts/26 frees are
counted; protocol fake handles/allocations end at zero, its owned cleanup and
one SDK shutdown complete. These are model cleanup attempts, not native proof.

An individually enumerated50-path projection preserves every repeated source,
role, boot and identity acquisition. Public Linux source size/depth plus explicitly
synthetic private image profiles also exceed16,384 path stats. Bytes/clocks/
process costs remain conditional; real Windows depth/image size, loaded-module
provenance, IO/provider/runner/driver/access/timeouts/cleanup remain unverified.
Three memory-filesystem comparisons execute the actual065 hash method unbound
without any DLL constructor and match byte/chunk/path/EOF/clock accounting.
SDK/raw/runner cost remains independently constrained, not folded into or hidden
by the count model. The original065 Oct7 and prototype Oct8 date gates remain
expired; no dated reader was renewed or prepared.

One frozen active084R2 regression passed1,942 tests:1,915 retained plus27 new,
zero failures/errors/skips. Developer targeted runs passed23 then27 tests;
there were no development failures. Seven frozen injected evidence cases:
one read-budget rejection, five persistent current-fact rejections (old/new
source, real/contest account and peer change), one default-off. Source changes
are freshly checked across acquisition, not served from a cached/archive proof.
Default-off performs no reader/API/SDK acquisitions. Exhaustion latches, exact
cap admission and rejection-before-extra-read, counted cleanup after exhaustion,
oversized/zero/bool profiles, chunks/ancestry, process ownership and post-call
clock exhaustion all have meaningful tests. No native full episode is claimed.

Prior089 closure2,820 bindings/2,607 archive members verified. Its positive
historical core models remain intact, alongside768-read,100ms-freshness,
0861,611ms/60,870ms deadline,087/088 API/SDK/boot and standalone SDK failures.
The earlier wire and model-build fake pins are not one verified runnable
provenance chain; these models grant no source/build coherence authority.
The090 cost module is not added to a claimed executable source graph; doing
so would increase the minimum read burden. Old reports, dates/spent markers,
all data/cost/clock/coverage/consumed2025/reserved Nov–Dec2026/provider exclusions
remain. No market rows, strategy returns, selection or candidate promotion.

Zero actual DLL/WMI/SDK/MT5/compiler/deploy/log/market/orders/receipts or grants.
Native entry rejects; orders, runtime and fresh/annual eligibility stay false.
Real-money mode/martingale remain unavailable. Source, evidence and four
handoffs sealed and reviewed. Next091 is offline historical research readiness,
declared unexecuted, to return work to qualified data and strategy validation.
No terminal/UI action is required.
"""
LATEST_TEXT=('Latest — 2026-10-09 local/UTC: offline source-proof feasibility090 sealed; '
    'read SOURCE-FEASIBILITY-090-RESULTS.md. 1,942 active tests /27 new pass; zero frozen failures/errors/skips. '
    'Seven injected cases:1 read-budget rejection /5 current-fact rejections /1 default-off. '
    'Native experiment cannot proceed under unchanged contract:41 individually fresh sources before/after '
    '38 guards require3,116 reads against768; total4,100 explicit +152 identity image hashes =4,252. '
    'No archive/cache/batch substitution, cap/proof/date/window change or new native reader. '
    'Original065 numeric predicates stop historical six-control target at768 reads on guard7 /6 spans /1 control; '
    '301 raw calls /603 raw clocks /78 SDK /13 boot queries. Reader model counts26 identity hashes, '
    '260 process calls /65 once-only closes /26 frees, no remaining modeled resources; SDK shutdown1. '
    'Actual065 hash method unbound over memory fixtures agrees with count accounting. '
    'Conditional Linux/synthetic-image full-target projection also exceeds path-stat cap; native bytes/paths/ '
    'module/SDK/provider/runner/driver/access/timing remain unverified. Count-only review, expired Oct7/Oct8 '
    'gates unchanged; native entry/eligibility/orders unavailable. Prior0892,820 bindings /2,607 archive '
    'members verified; positive models and every old failure/spent/data/cost/clock/coverage/reserved/provider '
    'gate preserved. Zero actual native/DLL/WMI/SDK/MT5/compiler/deploy/log/market/orders/receipts/grants. '
    'Next091 offline historical research readiness unexecuted; no further terminal experiment or UI action. '
    'Earlier entries historical.'+chr(10)+chr(10))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
         check=check,seal=seal,review=review)[p.parse_args().action]()
