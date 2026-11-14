"""Seal native build outcomes and external artifacts without changing frozen code."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def main(stage,next_plan):
    assert stage in ('040','041')
    prefix='native-compiler-'+stage
    API=runpy.run_path(str(ROOT/('scripts/'+prefix+'.py')))
    sha,write,sealed=API['sha'],API['write'],API['sealed']
    ledger=API['verify']();checks=sealed(ROOT/('reports/'+prefix+'-checks.json'));build=sealed(API['OUTPUT'])
    tests=sealed(ROOT/('reports/'+prefix+'-regression.json'));count,new=(578,12) if stage=='040' else (584,6)
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==count and tests['new_tests']==new
    assert checks['checker_passed'] and checks['build_sha256']==sha(API['OUTPUT']) and checks['observer_compiled']==build['compiled']
    if stage=='040':
        assert build['stop_reason']=='staging_failed' and build['fixture_invocations']==build['compiler_invocations']==0
        diagnostic=sealed(ROOT/'reports/native-compiler-040-hidden-diagnostic.json')
        assert diagnostic['root_check_passed'] and diagnostic['hidden_ancestor_attributes']==18 and not diagnostic['hidden_ancestor_is_reparse']
    results='docs/'+('NATIVE-COMPILER-040-RESULTS.md' if stage=='040' else 'NATIVE-STAGING-041-RESULTS.md')
    assert (ROOT/next_plan).is_file() and (ROOT/results).is_file()
    text=(f'Latest — 2026-10-06: native build{stage} sealed; read {Path(results).name}. '
        f'{count} tests ({new} new),{len(ledger["bindings"])} frozen inputs; '
        f'fixture invocations {build["fixture_invocations"]}, compiler invocations {build["compiler_invocations"]}, '
        f'compiled {build["compiled"]}, errors {build["errors"]}, warnings {build["warnings"]}. '
        f'Stop reason {build["stop_reason"]}; original evidence and outputs preserved, no rerun. '
        'Restricted policy observed unchanged; no PowerShell script execution/policy/global environment changes. '
        'No observer attachment/runtime, HTTP/SDK/quote/history/returns/orders. Old038/039/040 failures remain historical evidence. '
        'Clock/completeness/cost/flag blockers and033/035 failures unchanged; fresh/annual eligibility and orders false. '
        'Consumed2025/reservedNov–Dec2026/provider stops unchanged. '
        f'Next {Path(next_plan).name} declared, not executed under{stage}. Earlier entries are historical.\n\n')
    for name in API['HANDOFF']:
        path=ROOT/name;old=path.read_text();i=old.index('\n')+1;path.write_text(old[:i]+'\n'+text+old[i:])
    previous=API['prior_verify'](allow_handoff=True)
    write(ROOT/('reports/'+prefix+'-review.json'),dict(review_integrity_passed=True,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),
        documentation_bindings={n:sha(ROOT/n) for n in (results,next_plan,'scripts/finalize-native-build.py')},
        software_tests_passed=count,new_tests=new,observer_compiled=build['compiled'],observer_runtime_executed=False,
        market_requests=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        next_plan=next_plan,next_plan_executed=False))
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in API['HANDOFF']:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('scripts/*'+stage+'*','tests/*'+stage+'*.py','docs/*'+stage+'*.md',next_plan,
                    'scripts/finalize-native-build.py','src/forex_demo_lab/native_compiler_'+stage+'.py'):
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for p in ROOT.glob('reports/'+prefix+'-*'):
        assert 'final-source' not in p.name;groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    existing={n:h for v in groups.values() for n,h in v.items()};groups['native_build_'+stage+'_input_bindings']={}
    for n,h in {**ledger['bindings'],**checks['external_output_bindings']}.items():
        if n in existing:assert existing[n]==h,n
        else:groups['native_build_'+stage+'_input_bindings'][n]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(API['bound_path'](n))==h,n
    final=ROOT/('reports/'+prefix+'-final-source.json');archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==internal[n]
    write(final,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),
        observer_compiled=build['compiled'],observer_runtime_executed=False,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=next_plan,next_plan_executed=False))
    assert sealed(final)['archive_sha256']==sha(archive)
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(final),observer_compiled=build['compiled'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('next_plan');a=p.parse_args();main(a.stage,a.next_plan)
