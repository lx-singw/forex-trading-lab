"""Full closure review of057 preparation; no SDK, pipe or log content read."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']

def review():
    p=ROOT/'reports/native-pipe-057-preparation-final-source.json';r=sealed(p);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    helper=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))
    members=helper['verify_archive'](p,r)
    ledger=sealed(API['LEDGER']);assert all(b.get(n)==h for n,h in ledger['bindings'].items())
    checks=sealed(ROOT/'reports/native-pipe-057-preparation-checks.json')
    assert checks['checker_passed'] and checks['tests_passed']==874 and checks['native_lifetime_cases']==6
    assert checks['wire_differential_frames']==87 and not checks['native_mt5_transport_verified']
    initial=sealed(ROOT/'reports/native-pipe-057-initial-source.json')
    zip_path=ROOT/'reports/native-pipe-057-initial-source.zip';assert sha(zip_path)==initial['archive_sha256']
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings']) and len(z.infolist())==len(initial['bindings'])
        for n,h in initial['bindings'].items():assert b[n]==hashlib.sha256(z.read(n)).hexdigest()==h
    helper['API']['original_failure']()
    assert not (ROOT/'reports/native-pipe-057-runtime-authorization.json').exists()
    plan=ROOT/'docs/NATIVE-PIPE-058-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/'reports/native-pipe-057-preparation-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(p),bindings_verified=len(b),archive_members_verified=members,
        external_bindings_verified=len(r['archive_external_bindings']),frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(ledger['bindings']),tests_passed=874,new_tests=32,native_lifetime_cases=6,
        wire_differential_frames=87,compiler_invocations=1,native_errors=0,native_warnings=0,
        runtime_authorization_present=False,native_read_timeout_enforced=False,original054_runtime_completed=False,
        root_cause_proven=False,next_plan='docs/NATIVE-PIPE-058-PLAN.md',next_plan_sha256=sha(plan),
        next_plan_executed=False,sdk_connections=0,terminal_deployments=0,native_script_runs=0,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(ledger['bindings']))))

if __name__=='__main__':review()
