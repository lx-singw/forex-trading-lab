"""Freeze an explicitly authorized057 runtime; no SDK initialization here."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))
sha,sealed,write,bound=API['sha'],API['sealed'],API['write'],API['bound']
PRIOR=ROOT/'reports/native-pipe-057-preparation-final-source.json'
LEDGER=ROOT/'reports/native-pipe-058-ledger.json'

def freeze():
    from forex_demo_lab.native_pipe_057 import date_guard,validate_runtime_authorization
    import time
    date_guard(time.time_ns()//1000000)
    assert sha(PRIOR)=='828b2d86533affdc49c6506749ba963a3cb8d186a6f05ba41f8f18938fb22651'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/native-pipe-057-preparation-completion-review.json')
    assert review['review_passed'] and review['frozen_input_coverage_complete'] and review['final_source_sha256']==sha(PRIOR)
    assert review['next_plan_sha256']==sha(ROOT/'docs/NATIVE-PIPE-058-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==1836
    for n,h in b.items():assert sha(bound(n))==h,n
    helper=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-056.py'))
    assert helper['verify_archive'](PRIOR,p)==1704
    helper['API']['original_failure']()
    assert sealed(ROOT/'reports/native-pipe-058-readiness.json')['pins_match']
    for n in API['HANDOFF']:b.pop(n)
    for suffix in ('.json','.sha256','.zip'):
        path=PRIOR.with_suffix(suffix);b[path.relative_to(ROOT).as_posix()]=sha(path)
    for pattern in ('scripts/*058.py','docs/*058*.md','reports/native-pipe-058-*.json','reports/native-pipe-058-*.sha256',
                    'reports/native-pipe-057-preparation-completion-review.*'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    auth=dict(version='native_runtime_057_v1',runtime_authorized=True,preparation_sha256=sha(PRIOR),
        plan_sha256=sha(ROOT/'docs/NATIVE-PIPE-058-PLAN.md'),phase='57000000000000000000000000000001',date='2026-10-07',
        maximum_sdk_connections=1,maximum_script_arms=3,maximum_grants=1,maximum_deployments=1,
        maximum_session_seconds=900,maximum_io_ms=2000,maximum_drain_ms=1000)
    validate_runtime_authorization(auth,sha(PRIOR),auth['plan_sha256'])
    write(LEDGER,dict(bindings=b,runtime_authorization=auth,user_authorized_proceed=True,
        baseline_log_saved_acknowledged=True,original054_runtime_completed=False,
        native_read_timeout_enforced=False,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    write(ROOT/'reports/native-pipe-057-runtime-authorization.json',auth)
    print(json.dumps(dict(frozen=True,bindings=len(b),runtime_authorized=True)))

def verify():
    ledger=sealed(LEDGER)
    for n,h in ledger['bindings'].items():assert sha(bound(n))==h,n
    assert sealed(ROOT/'reports/native-pipe-057-runtime-authorization.json')==ledger['runtime_authorization']
    return ledger

if __name__=='__main__':freeze()
