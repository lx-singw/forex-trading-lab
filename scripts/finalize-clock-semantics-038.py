"""Seal offline audit, failed build evidence and declared next build repair."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/clock-semantics-038.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed'];HANDOFF=API['HANDOFF']
REVIEW=ROOT/'reports/clock-semantics-038-review.json'
FINAL=ROOT/'reports/clock-semantics-038-final-source.json'
NEXT='docs/COMPILER-LAUNCH-039-PLAN.md'


def evidence():
    ledger=API['verify']();tests=sealed(ROOT/'reports/clock-semantics-038-tests.json')
    audit=sealed(API['OUTPUT']);research=sealed(API['RESEARCH']);compile=sealed(API['COMPILE'])
    checks=sealed(ROOT/'reports/clock-semantics-038-checks.json')
    launch=sealed(ROOT/'reports/clock-semantics-038-launch-diagnostic.json')
    metadata=sealed(ROOT/'reports/clock-semantics-038-source-metadata.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==546 and tests['new_tests']==24
    assert tests['shared_guard_checks']==checks['shared_guard_checks']==73 and checks['checker_passed']
    assert checks['ledger_sha256']==audit['ledger_sha256']==compile['ledger_sha256']==sha(API['LEDGER'])
    assert checks['audit_sha256']==sha(API['OUTPUT']) and checks['research_sha256']==audit['research_sha256']==sha(API['RESEARCH'])
    assert checks['compile_sha256']==sha(API['COMPILE'])
    assert checks['native_csv_fields_verified']==audit['native_csv_fields_verified']==709584
    assert checks['saved_tick_rows']==audit['saved_tick_rows']==88698 and checks['clock_fields_decoded']==177396
    for result in audit['native_fields']:
        assert result['all_seconds_equal_floor_milliseconds'] and not result['floor_relation_mismatches']
        assert not result['seconds_reversals'] and not result['milliseconds_reversals']
    assert audit['action_counts']==checks['action_counts']==dict(search=0,open=8,find=6,findings=7)
    assert len(research['actions'])==14
    assert compile['compiled'] is checks['observer_compiled'] is False
    assert compile['outcome']=='compiler_driver_failure_details_redacted' and compile['compilation_attempts']==1
    assert compile['output_bindings']=={}
    assert launch['return_code']==1 and launch['powershell_unauthorized_access'] and not launch['stdout_fixed_marker']
    assert launch['probe_sha256']==sha(ROOT/'scripts/clock-launch-probe-038.ps1')
    assert metadata['source_sha256']==sha(ROOT/'scripts/compile-clock-observer-038.ps1')
    assert metadata['parser_errors']==0 and metadata['execution_policy']=='RemoteSigned'
    assert metadata['signature_status']=='NotSigned' and metadata['source_is_unc']
    assert metadata['failed_nested_metadata_query_recorded']
    for report in (launch,metadata):assert report['compiler_invocations']==report['market_requests']==0 and report['settings_changed'] is False
    for report in (audit,checks):
        assert report['fresh_performance_eligible'] is report['annual_eligible'] is report['orders_available'] is False
        assert report['market_requests']==report['native_connections']==report['historical_downloads']==report['strategy_replays']==0
        assert report['observer_runtime_executed'] is False
    return ledger,audit,research,compile,checks,launch,metadata


def handoff():
    evidence()
    text=('Latest — 2026-10-06: native clock semantics audit038 complete. Read CLOCK-SEMANTICS-038-RESULTS.md. '
        '546 tests (24 new)/73 exact shared guard decisions,99 frozen inputs; prior1,101 bindings/1,055 ZIP members/'
        '46 external inputs verified. Every saved033/035 tick seconds field equals floor(milliseconds/1000): '
        '88,698 preserved response rows,177,396 clock fields/709,584 native-CSV fields, no contrary rows/reversals. '
        'All120 saved031 receipts plus037 quote rechecked; roughly three-hour lead remains a hypothesis, no correction. '
        'Eight official opens/six finds/seven findings: TimeCurrent last server quote; TimeTradeServer client-calculated; '
        'GMT/local computer-derived; tester equalities cannot certify native clocks. Zero SDK connections/new quotes/'
        'history/returns/orders/settings changes. Read-only one-shot MQL script prepared, capture off, actualDEMO/USD/'
        'Algo off/identity/instrument guards. One reserved compile-driver invocation failed, no verified EX5/native '
        'compilation/runtime; failure preserved. Harmless UNC launch returned UnauthorizedAccess; parser valid/'
        'RemoteSigned/unsigned metadata, no policy bypass. Independent arithmetic/research/build-outcome/gate checks '
        'pass; all old failures, raw labels and clock/completeness/cost/flag blockers retained. Fresh/annual eligibility '
        'false; consumed2025/reservedNov–Dec2026/provider stops unchanged. Next COMPILER-LAUNCH-039-PLAN.md declares '
        'new tested locally staged compiler launch, policy preserved, one attempt, no observer attachment/runtime '
        'or retargeting; not executed. Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True)))


def review():
    prior=API['prior_verify'](allow_handoff=True);ledger,audit,research,compile,checks,launch,metadata=evidence()
    documents=('docs/CLOCK-SEMANTICS-038-RESULTS.md',NEXT,'scripts/finalize-clock-semantics-038.py','scripts/clock-launch-probe-038.ps1')
    for name in HANDOFF:assert 'CLOCK-SEMANTICS-038-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/NEXT).read_text()
    write(REVIEW,dict(kind='post_native_clock_semantics_review_038',review_integrity_passed=True,
        prior_snapshot_verification=prior,input_bindings_verified=len(ledger['bindings']),
        evidence_bindings={str(p.relative_to(ROOT)):sha(p) for p in (
            API['OUTPUT'],API['RESEARCH'],API['COMPILE'],ROOT/'reports/clock-semantics-038-checks.json',
            ROOT/'reports/clock-semantics-038-launch-diagnostic.json',ROOT/'reports/clock-semantics-038-source-metadata.json')},
        documentation_bindings={n:sha(ROOT/n) for n in documents},software_tests_passed=546,new_tests=24,shared_guard_checks=73,
        native_csv_fields_verified=709584,saved_tick_rows=88698,clock_fields_decoded=177396,action_counts=checks['action_counts'],
        observer_compiled=False,observer_runtime_executed=False,original_failed_compilation_outcome_preserved=True,
        market_requests=0,native_connections=0,historical_downloads=0,strategy_replays=0,orders_available=False,
        raw_labels_normalized=False,source_clock_sessions_qualified=False,upstream_completeness_qualified=False,
        historical_executable_costs_qualified=False,prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=NEXT,next_plan_executed=False))
    print(json.dumps(dict(review_integrity_passed=True,observer_compiled=False,market_requests=0)))


def snapshot():
    reviewed=sealed(REVIEW);assert reviewed['review_integrity_passed'];API['prior_verify'](allow_handoff=True);ledger,*_=evidence()
    for name,h in {**reviewed['evidence_bindings'],**reviewed['documentation_bindings']}.items():assert sha(ROOT/name)==h,name
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*038*.md',NEXT,'scripts/*038*','src/forex_demo_lab/clock_semantics_038.py','tests/*038*.py',
                    'mt5/Scripts/*038*','mt5/Tests/ClockGuard038.cpp','config/research-actions-038.json'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/clock-semantics-038-*'):
        assert 'final-source' not in path.name;groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    already={n:h for v in groups.values() for n,h in v.items()};groups['clock_semantics_input_bindings']={}
    for name,h in ledger['bindings'].items():
        if name in already:assert already[name]==h,name
        else:groups['clock_semantics_input_bindings'][name]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for name,h in bindings.items():assert sha(API['bound_path'](name))==h,name
    archive=FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal) and set(z.namelist())==set(internal)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==internal[name],name
    write(FINAL,dict(kind='post_native_clock_semantics_snapshot_038',**groups,archive_external_bindings=external,
        archive_members_verified=len(internal),external_bindings_verified=len(external),archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),
        previous_snapshot_sha256=sha(API['PRIOR']),completed_utc=datetime.now(timezone.utc).isoformat(),
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/runtime/compilers externally hash-bound and required',
        software_tests_passed=546,new_tests=24,shared_guard_checks=73,native_csv_fields_verified=709584,
        saved_tick_rows=88698,clock_fields_decoded=177396,action_counts=reviewed['action_counts'],
        observer_compiled=False,observer_runtime_executed=False,original_failed_compilation_outcome_preserved=True,
        market_requests=0,native_connections=0,historical_downloads=0,strategy_replays=0,orders_available=False,
        raw_labels_normalized=False,source_clock_sessions_qualified=False,upstream_completeness_qualified=False,
        historical_executable_costs_qualified=False,prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=NEXT,next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
