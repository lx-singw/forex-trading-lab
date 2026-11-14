"""Separate pure audit; retained tests/models are never rerun."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/synchronization-084-r2.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='synchronization-084-r3';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
DESIGN=ROOT/'docs/SYNCHRONIZATION-084-R3-DESIGN.md'
PLAN=ROOT/'docs/SYNCHRONIZATION-085-R3-PLAN.md'
FAILURE=ROOT/f'reports/{PREFIX}-prior-check-failure.json'
OWN=('scripts/synchronization-084-r3.py','src/forex_demo_lab/synchronization_audit_084_r3.py',
    'tests/test_synchronization_audit_084_r3.py','docs/SYNCHRONIZATION-084-R3-DESIGN.md',
    'docs/SYNCHRONIZATION-085-R3-PLAN.md')
PRIOR_REPORTS=tuple(ROOT/('reports/synchronization-084-r2-'+n) for n in (
    'ledger.json','ledger.sha256','initial-source.json','initial-source.sha256','initial-source.zip',
    'tests-started.json','tests-started.sha256','tests.json','tests.sha256',
    'evidence-started.json','evidence-started.sha256','evidence.json','evidence.sha256'))


def retained():
    API['verify']();API['retained_checks']()
    t=sealed(ROOT/'reports/synchronization-084-r2-tests.json')
    e=sealed(ROOT/'reports/synchronization-084-r2-evidence.json')
    assert t['passed'] and t['tests_run']==1720 and t['new_tests']==38 and t['active_suite']
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(API['LEDGER'])
    assert len(e['cases'])==14 and sum(x['modeled_completed'] for x in e['cases'].values())==2
    for suffix in ('checks.json','final-source.json','completion-review.json'):
        assert not (ROOT/('reports/synchronization-084-r2-'+suffix)).exists()
    return t,e


def freeze():
    retained();b=dict(sealed(API['LEDGER'])['bindings'])
    for n in HANDOFF:b.pop(n,None)
    capture=dict(origin='tool_exit1_capture',prior_action='synchronization-084-r2 check',
        observed_exit_code=1,assertion="row['full_guards']==len(row['guard_spans'])<=256",
        script_sha256=sha(ROOT/'scripts/synchronization-084-r2.py'),
        evidence_sha256=sha(ROOT/'reports/synchronization-084-r2-evidence.json'),
        case='observed_guard',started_guards=75,valid_guard_spans=74,elapsed_ms=120827,
        successful_checker_record_created=False,reconstructed_success=False,**ZERO,**FALSE)
    write(FAILURE,capture)
    for p in (*PRIOR_REPORTS,FAILURE,FAILURE.with_suffix('.sha256')):b[p.relative_to(ROOT).as_posix()]=sha(p)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    write(LEDGER,dict(bindings=b,design_sha256=sha(DESIGN),next_plan_sha256=sha(PLAN),
        prior_ledger_sha256=sha(API['LEDGER']),prior_failure_capture_sha256=sha(FAILURE),
        retained_tests_sha256=sha(ROOT/'reports/synchronization-084-r2-tests.json'),
        retained_evidence_sha256=sha(ROOT/'reports/synchronization-084-r2-evidence.json'),
        expected_audit_tests=8,full_tests_retained=1720,maximum_targeted_test_runs=1,maximum_audits=1,
        retained_model_cases=14,full_suite_rerun=False,models_rerun=False,**ZERO,**FALSE))
    archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(archive),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),audit_tests=8,full_tests_retained=1720)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['design_sha256']==sha(DESIGN) and l['next_plan_sha256']==sha(PLAN)
    assert l['prior_ledger_sha256']==sha(API['LEDGER']) and l['prior_failure_capture_sha256']==sha(FAILURE)
    assert l['retained_tests_sha256']==sha(ROOT/'reports/synchronization-084-r2-tests.json')
    assert l['retained_evidence_sha256']==sha(ROOT/'reports/synchronization-084-r2-evidence.json')
    return l


def test():
    verify();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(audit_suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_synchronization_audit_084_r3')
    assert suite.countTestCases()==8;start=time.monotonic()
    r=unittest.TextTestRunner(verbosity=1).run(suite);ok=r.wasSuccessful() and r.testsRun==8 and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=ok,tests_run=r.testsRun,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failed_test_names=[str(t) for t,d in r.failures+r.errors],elapsed_seconds=time.monotonic()-start,
        ledger_sha256=sha(LEDGER),full_tests_retained=1720,full_suite_rerun=False,models_rerun=False,**ZERO,**FALSE))
    if not ok:raise SystemExit(1)


def audit():
    l=verify();retained();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==8 and t['ledger_sha256']==sha(LEDGER)
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.synchronization_audit_084_r3 import audit084_r3
    write(ROOT/f'reports/{PREFIX}-audit-started.json',dict(audit_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    e=sealed(ROOT/'reports/synchronization-084-r2-evidence.json');rows=audit084_r3(e)
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');archive=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(archive)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    import hashlib
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(audit_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),retained_tests_sha256=l['retained_tests_sha256'],
        retained_evidence_sha256=l['retained_evidence_sha256'],prior_failure_capture_sha256=sha(FAILURE),
        case_audits=rows,model_cases_retained=14,modeled_completions_retained=2,modeled_rejections_retained=11,
        default_off_cases_retained=1,audit_tests_passed=8,full_tests_retained=1720,
        concrete_scenario_first_recorded_stop='whole_clock_limit',native_exact_cause_proven=False,
        source_inputs_retained=31,portable_codec_decisions_retained=18,portable_encoder_comparisons_retained=1,
        portable_window_comparisons_retained=34,full_suite_rerun=False,models_rerun=False,**ZERO,**FALSE))
    print(json.dumps(dict(audit_passed=True,audit_tests=8,retained_full_tests=1720,retained_models=14)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/SYNCHRONIZATION-084-R3-RESULTS.md'
    text=('# Synchronization084 R3 source/interface closure\n\n'
        'Fresh default-off MQL reader/144-byte codec and typed private companion/decoder/matcher/build schema are prepared. '
        '31 complete source/import/include inputs are bound. Source remains uncompiled/undeployed; there is no native backend '
        'or SDK/native/MT5/compiler/deploy/log/market/orders/receipt authority. Windows ACLs, pipe message boundaries and MQL '
        'blocking/scheduling remain unverified.\n\n'
        '1720 passing active regression tests/38 corrected checks are retained, not rerun. Eight new targeted auditor tests '
        'passed. The14 retained injected cases have2 completions,11 rejections and1 default-off.18 portable frame decisions/'
        'one exact encoder comparison and34 window comparisons remain. No1728-test full run has occurred. Future full suites '
        'inherit synchronization-084-r2.py active_suite(). Original083 and084 fixture failures/retired sources remain evidence; '
        'R2 corrected084 expiry expectation only, preserving production clock rejection.\n\n'
        'The concrete zero-cost and50ms guard models each use230 full guards; the50ms model completes in38610ms. With1611ms '
        'applied to every guard as a scenario,75 guards start but only74 have valid recorded spans. The last guard crosses '
        'the120000ms whole limit at120827ms, before release. Cleanup attempts close all model handles, with zero uncertain '
        'closes, but overall timed cleanup validity stays false after expiry. No missing completed span is invented. '
        'Native latencies remain unknown and no observed maximum is a bound.\n\n'
        'R2 checker assumed started guards always equal valid spans; it exited1 at that assertion and produced no successful '
        'checker/seal/review record. That failure and its explicitly labelled tool-exit capture are retained. R3 audits the '
        'existing data only and accepts precisely one incomplete guard in this failed scenario; ordinary cases still require '
        'exact equality. Earlier084/R2 wording attributed the first stop to freshness. The recorded first stop is the whole '
        'clock; serial publication is also incompatible with2s freshness in that scenario. These results supersede that '
        'causal wording without editing frozen documents or extending limits.\n\n'
        'ActualDEMO/default-off/uncached full guards, original peer timestamps, private owner/DACL/ACE/ancestor/link/path/'
        'file/pipe identity facts, CREATE_NEW slots, held READ/share-READ response boundaries and independent write/delete '
        'error32 with no helper synthetic seal are implemented through injected interfaces. Replacements, stale or wrong '
        'frames, account changes, timing overruns and uncertain close reject. Native facts are not proved by model values. '
        'Detailed private hold/frame validation remains the frozen decoder/matcher generation result; this audit reconciles '
        'public counters, spans, frame fingerprints, controls and cleanup.\n\n'
        'All2s freshness/10s start/30–31s close/250ms/60s episode/120s whole limits remain unchanged. Named-pipe reads/flushes '
        'may block; timely close requires the closed challenge and no maximum physical hold is guaranteed. Next085 R3 '
        'explicitly reviews/redesigns response-boundary and blocking behavior before separately prepared native backend/build/'
        'runtime work. Unexecuted; no MT5 UI action requested.\n\n'
        '082 metadata success, spent081/raw markers,075 historical artifact and every earlier failure stay intact. '
        'Native sharing/publication/ACK,070 cause and profitable edge remain unproven.033/035/data clock/cost/coverage/'
        'consumed2025/reserved Nov–Dec2026/provider exclusions remain; eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=('Latest — 2026-10-08: synchronization084 R3 source/interface closure sealed; read SYNCHRONIZATION-084-R3-RESULTS.md. '
        '1720 passing active regression tests retained;8 new auditor checks pass, no full/model rerun.14 retained cases:2 complete/'
        '11 reject/1 default-off;18 portable codec decisions/one encoder/34 windows retained. Fresh default-off MQL reader/codec/'
        'typed private companion/decoder/matcher/31-input build schema uncompiled/undeployed/no native backend. Concrete1611ms '
        'scenario starts75 guards/records74 valid spans;120827ms crosses120s whole limit before release. Timed cleanup invalid '
        'but all model close attempts complete/uncertain0. R2 checker exit1 guard-span equality assumption retained; R3 audits '
        'without inventing a span. This corrects earlier freshness-first causal wording;2s freshness also infeasible there. '
        '230 full guards in successful models;50ms case38610ms, no bounds. All2s/10s/30–31s/250ms/60s/120s limits retained. '
        'Blocking pipe/timely close remains unproven. Original0841718 fixture failure/R2 replacements/original083 failure/'
        '082 success/spent081/075 artifact preserved. Future full suites use084 R2 active_suite();1728 full run not performed. '
        'Zero native/SDK/MT5/compiler/deploy/log/market/orders/grants. Next085 R3 redesign/preparation unexecuted; sharing/'
        'publication/ACK/profit/070 cause/eligibility/orders unproven/false; all data/reserved/provider gates preserved. Earlier entries historical.\n\n')
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
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        full_tests_retained=1720,audit_tests_passed=8,model_cases_retained=14,
        active_suite_inherited='synchronization-084-r2.py',full_suite_rerun=False,models_rerun=False,
        future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['audit_passed'] and c['ledger_sha256']==sha(LEDGER) and t['passed'] and t['tests_run']==8
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['retained_tests_sha256']==l['retained_tests_sha256'] and c['retained_evidence_sha256']==l['retained_evidence_sha256']
    assert not r['future_plan_executed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),full_tests_retained=1720,audit_tests_passed=8,model_cases_retained=14,
        prior_checker_exit1_preserved=True,original_fixture_failure_preserved=True,
        full_suite_rerun=False,models_rerun=False,next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,full_tests_retained=1720,audit_tests=8,bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','audit','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,audit=audit,seal=seal,review=review)[p.parse_args().action]()
