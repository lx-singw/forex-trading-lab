"""Preserve042 sources, compilation and sanitized bounded native runtime evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/clock-session-044.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']

def main(next_plan,completion=False):
    ledger=API['verify']();build=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/native-compiler-042-checks.json')
    tests=sealed(ROOT/'reports/clock-session-044-regression.json');assert tests['passed'] and tests['tests_passed']==622
    assert checks['checker_passed'] and checks['build_sha256']==sha(API['OUTPUT'])
    runtime_path=ROOT/'reports/clock-observer-044-runtime.json';runtime=sealed(runtime_path) if runtime_path.exists() else None
    runtime_checks=sealed(ROOT/'reports/clock-observer-044-runtime-checks.json') if runtime is not None else None
    if runtime is not None:assert runtime_checks['checker_passed'] and runtime_checks['runtime_sha256']==sha(runtime_path)
    completed=runtime is not None and runtime['completed'];reads=runtime['quote_reads'] if runtime is not None else 0
    result='docs/CLOCK-DEPENDENCY-044-RESULTS.md';assert (ROOT/result).is_file() and (ROOT/next_plan).is_file()
    text=(f'Latest — 2026-10-06: clock session044 sealed; read CLOCK-DEPENDENCY-044-RESULTS.md. '
        f'622 tests (10 new),{len(ledger["bindings"])} pre-run frozen inputs; reused042 exact shared header73 checks. '
        f'Native compiled {build["compiled"]}, errors {build["errors"]}, warnings {build["warnings"]}; '
        f'bounded native runtime completed {completed}, observed quote reads {reads}. '
        'Original sanitized records/compiled/deployed artifacts hash-bound; old038/039/040 failures and041 freeze-list omission preserved. '
        'No HTTP/history/strategy/order calls; capture off by default, actual-demo/USD/Algo-off guards, no live mode. '
        'Current relative clock evidence does not certify historical UTC or authorize correction; clock/coverage/cost/flags and033/035 '
        'failures remain, fresh/annual eligibility and orders false. Consumed2025/reservedNov–Dec2026/provider stops unchanged. '
        f'Next {Path(next_plan).name} declared, not executed under042. Earlier entries are historical.\n\n')
    for name in API['HANDOFF']:
        p=ROOT/name;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+text+old[i:])
    previous=API['prior_verify'](allow_handoff=True)
    write(ROOT/('reports/clock-session-044-'+('completion' if completion else 'preparation')+'-review.json'),dict(review_integrity_passed=True,
        previous_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),software_tests_passed=622,new_tests=10,
        observer_compiled=build['compiled'],runtime_completed=completed,observed_quote_reads=reads,
        prior_041_pre_run_coverage_gap_preserved=True,all_044_critical_sources_frozen_before_runtime=True,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False,next_plan=next_plan,next_plan_executed=False))
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    from forex_demo_lab.clock_session_044 import ROLLOVER
    for values in groups.values():
        for n,(before,after) in ROLLOVER.items():
            if n in values:assert values[n]==before;values[n]=after
    for n in API['HANDOFF']:groups['source_bindings'][n]=sha(ROOT/n)
    for pattern in ('scripts/*044*','tests/*044*.py','docs/*044*.md',next_plan,'src/forex_demo_lab/*044.py',
                    'mt5/Scripts/*042*','mt5/Tests/ClockGuard042.cpp'):
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for pattern in ('reports/clock-session-044-*','reports/clock-observer-044-*'):
        for p in ROOT.glob(pattern):
            groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    existing={n:h for v in groups.values() for n,h in v.items()};groups['clock_session_044_input_bindings']={}
    inputs={**ledger['bindings'],**checks['external_output_bindings']}
    if runtime_checks is not None:inputs.update(runtime_checks['deployment_bindings'])
    for n,h in inputs.items():
        if n in existing:assert existing[n]==h,n
        else:groups['clock_session_044_input_bindings'][n]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(API['bound_path'](n))==h,n
    final=ROOT/('reports/clock-session-044-'+('completion' if completion else 'preparation')+'-final-source.json');archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal) and set(z.namelist())==set(internal)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==internal[n]
    write(final,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),
        observer_compiled=build['compiled'],observer_runtime_executed=bool(runtime and runtime['records']),
        native_runtime_completed=completed,observed_quote_reads=reads,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=next_plan,next_plan_executed=False))
    assert sealed(final)['archive_sha256']==sha(archive)
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(final),runtime_completed=completed)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('next_plan');p.add_argument('--completion',action='store_true');a=p.parse_args();main(a.next_plan,a.completion)
