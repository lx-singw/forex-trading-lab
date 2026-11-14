"""Preserve the stopped launcher and declare the direct native compiler build."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/compiler-launch-039.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
FINAL=ROOT/'reports/compiler-launch-039-final-source.json'
NEXT='docs/NATIVE-COMPILER-040-PLAN.md'

def main():
    ledger=API['verify']();tests=sealed(ROOT/'reports/compiler-launch-039-tests.json')
    build=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/compiler-launch-039-checks.json')
    diagnostic=sealed(ROOT/'reports/compiler-launch-039-module-diagnostic.json')
    assert tests['passed'] and tests['tests_passed']==566 and tests['new_tests']==20
    assert build['stop_reason']=='native_metadata_failed' and build['fixture_invocations']==build['compiler_invoker_calls']==0
    assert checks['checker_passed'] and checks['build_sha256']==sha(API['OUTPUT'])
    assert diagnostic['return_code']==0 and diagnostic['effective_policy']=='Restricted'
    assert diagnostic['execution_policy_changed'] is diagnostic['global_environment_changed'] is False
    text=('Latest — 2026-10-06: compiler launch039 sealed; read COMPILER-LAUNCH-039-RESULTS.md. '
          '566 tests (20 new),97 frozen inputs. Metadata autoload failed before the fixture/compiler: zero invocations. '
          'Read-only diagnostic with the native Windows PowerShell module catalog succeeded and reported Restricted. '
          'No policy or global environment changes, observer compilation/runtime, market reads or orders. '
          '038 failure and 033/035 diagnostic failures preserved; clock/completeness/cost/flag blockers remain. '
          'Fresh/annual eligibility false; consumed2025/reservedNov–Dec2026/provider stops unchanged. '
          'Next NATIVE-COMPILER-040-PLAN.md declares a direct MetaEditor EXE build with a native argv fixture, '
          'without executing a PowerShell script or changing policy; not executed in039. Earlier entries are historical.\n\n')
    for name in API['HANDOFF']:
        path=ROOT/name;old=path.read_text();i=old.index('\n')+1;path.write_text(old[:i]+'\n'+text+old[i:])
    prior_check=API['prior_verify'](allow_handoff=True)
    write(ROOT/'reports/compiler-launch-039-review.json',dict(review_integrity_passed=True,
        prior_snapshot_verification=prior_check,input_bindings_verified=len(ledger['bindings']),
        software_tests_passed=566,new_tests=20,observer_compiled=False,observer_runtime_executed=False,
        compiler_invocations=0,market_requests=0,execution_policy_changed=False,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=NEXT,next_plan_executed=False))
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in API['HANDOFF']:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('scripts/*039*','tests/*039*.py','docs/*039*.md',NEXT,'src/forex_demo_lab/compiler_launch_039.py'):
        for p in ROOT.glob(pattern):groups['source_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for p in ROOT.glob('reports/compiler-launch-039-*'):
        assert 'final-source' not in p.name;groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    for suffix in ('.json','.sha256','.zip'):
        p=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][p.relative_to(ROOT).as_posix()]=sha(p)
    existing={n:h for v in groups.values() for n,h in v.items()};groups['compiler_launch_input_bindings']={}
    for n,h in ledger['bindings'].items():
        if n in existing:assert existing[n]==h,n
        else:groups['compiler_launch_input_bindings'][n]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for n,h in bindings.items():assert sha(API['bound_path'](n))==h,n
    archive=FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==internal[n]
    write(FINAL,dict(**groups,archive_external_bindings=external,archive_sha256=sha(archive),
        archive_members_verified=len(internal),external_bindings_verified=len(external),
        observer_compiled=False,observer_runtime_executed=False,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False,next_plan=NEXT,next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),members=len(internal),external=len(external),sha256=sha(FINAL))))

if __name__=='__main__':main()
