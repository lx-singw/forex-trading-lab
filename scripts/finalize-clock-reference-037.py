"""Post-result handoff/review/snapshot; does not alter frozen diagnostic behavior."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/clock-reference-037.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['HANDOFF']
REVIEW=ROOT/'reports/clock-reference-037-review.json'
FINAL=ROOT/'reports/clock-reference-037-final-source.json'
NEXT='docs/CLOCK-SEMANTICS-038-PLAN.md'


def evidence():
    ledger=API['verify']();tests=sealed(ROOT/'reports/clock-reference-037-tests.json')
    capture=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/clock-reference-037-checks.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==522 and tests['new_tests']==24
    assert checks['checker_passed'] and checks['capture_sha256']==sha(API['OUTPUT'])
    assert checks['ledger_sha256']==capture['ledger_sha256']==sha(API['LEDGER'])
    assert checks['reservation_sha256']==capture['reservation_sha256']==sha(API['RESERVATION'])
    assert checks['http_requests']==len(capture['requests'])==3 and len(checks['usable_references'])==2
    assert checks['actual_quote_reads']==capture['actual_quote_reads']==1
    assert checks['native_connections_attempted']==capture['native_connections_attempted']==1
    assert checks['observed_request_budgets_passed'] and not checks['clock_errors']
    assert capture['quote_guards_passed'] and capture['stop_reason'] is None
    assert capture['comparison']==checks['comparison'] and checks['comparison']['outcome']=='disagreement'
    assert checks['comparison']['raw_minus_reference_ms']==[10795831,10799831]
    for report in (capture,checks):
        assert report['fresh_performance_eligible'] is report['annual_eligible'] is report['orders_available'] is False
        assert report['historical_reads']==report['strategy_replays']==0
    return ledger,capture,checks


def handoff():
    evidence()
    text=('Latest — 2026-10-06: clock-reference diagnostic037 complete. Read CLOCK-REFERENCE-037-RESULTS.md. '
        '522 tests (24 new),88 frozen inputs; prior1,077 bindings/1,032 ZIP members/45 external inputs verified. '
        'Three verified-TLS HEAD requests, two usable public Date references agree with local receipts within '
        'coarse seconds; time.gov response rejected by strict header validation, no retry. Windows Time service '
        'present/not running, no settings changed. One guarded existing-demo EURUSD quote, actualDEMO/USD/Algo off/'
        'connected/private stable identity; raw label ahead of local by10,797.930s and coarse cross-host references '
        'by10,795.831..10,799.831s. Current-clock disagreement persists; no timezone/cause/UTC certification or '
        'three-hour correction. Independent arithmetic/budget/privacy/gate checks pass; zero history/returns/orders. '
        'All raw labels and prior033/035 failures preserved; clock/completeness/cost and flag128/1024 remain unresolved. '
        'Fresh/annual eligibility false; consumed2025/reservedNov–Dec2026/provider stops unchanged. Next '
        'CLOCK-SEMANTICS-038-PLAN.md declares offline native seconds/milliseconds audit, official clock semantics '
        'and separate read-only observer preparation/compilation only, not executed. No observer attachment/runtime '
        'or qualification promotion. Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True)))


def review():
    prior=API['prior_verify'](allow_handoff=True);ledger,capture,checks=evidence()
    documents=('docs/CLOCK-REFERENCE-037-RESULTS.md',NEXT,'scripts/finalize-clock-reference-037.py')
    for name in HANDOFF:assert 'CLOCK-REFERENCE-037-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/NEXT).read_text()
    write(REVIEW,dict(kind='post_clock_reference_review_037',review_integrity_passed=True,
        prior_snapshot_verification=prior,input_bindings_verified=len(ledger['bindings']),
        capture_sha256=sha(API['OUTPUT']),checks_sha256=sha(ROOT/'reports/clock-reference-037-checks.json'),
        documentation_bindings={n:sha(ROOT/n) for n in documents},software_tests_passed=522,new_tests=24,
        http_requests=3,usable_hosts=2,native_connections_attempted=1,actual_quote_reads=1,
        comparison=checks['comparison'],source_clock_sessions_qualified=False,local_clock_certified=False,
        upstream_completeness_qualified=False,historical_executable_costs_qualified=False,raw_labels_normalized=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,historical_reads=0,strategy_replays=0,
        next_plan=NEXT,next_plan_executed=False))
    print(json.dumps(dict(review_integrity_passed=True,comparison=checks['comparison']['outcome'],performance_eligible=False)))


def snapshot():
    reviewed=sealed(REVIEW);assert reviewed['review_integrity_passed']
    API['prior_verify'](allow_handoff=True);ledger,capture,checks=evidence()
    for name,h in reviewed['documentation_bindings'].items():assert sha(ROOT/name)==h,name
    assert sha(API['OUTPUT'])==reviewed['capture_sha256']
    assert sha(ROOT/'reports/clock-reference-037-checks.json')==reviewed['checks_sha256']
    prior=sealed(API['PRIOR'])
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*037*.md',NEXT,'scripts/*037*.py','src/forex_demo_lab/clock_reference_037.py','tests/*037*.py'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/clock-reference-037-*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    already={n:h for v in groups.values() for n,h in v.items()};groups['clock_reference_input_bindings']={}
    for name,h in ledger['bindings'].items():
        if name in already:assert already[name]==h,name
        else:groups['clock_reference_input_bindings'][name]=h
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
    write(FINAL,dict(kind='post_clock_reference_snapshot_037',**groups,archive_external_bindings=external,
        archive_members_verified=len(internal),external_bindings_verified=len(external),archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),
        previous_snapshot_sha256=sha(API['PRIOR']),completed_utc=datetime.now(timezone.utc).isoformat(),
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        software_tests_passed=522,new_tests=24,http_requests=3,usable_hosts=2,native_connections_attempted=1,actual_quote_reads=1,
        comparison=checks['comparison'],source_clock_sessions_qualified=False,local_clock_certified=False,
        upstream_completeness_qualified=False,historical_executable_costs_qualified=False,raw_labels_normalized=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,historical_reads=0,strategy_replays=0,
        next_plan=NEXT,next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
