"""Freeze/check one new069 native attempt; raw reservation has no sidecar."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/sharing-integration-069.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='native-sharing-070';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/sharing-integration-069-final-source.json'
PROFILE=ROOT/'reports/helper-profile-068.json';POLICY=ROOT/'docs/NATIVE-SHARING-070-POLICY.md'
AUTH=ROOT/f'reports/{PREFIX}-authorization.json'
RUNTIME=ROOT/'reports/native-sharing-069-runtime.json'
RESERVATION=ROOT/'reports/native-sharing-069-runtime-reservation.json'
DISPATCH=ROOT/'reports/native-sharing-069-dispatch-started.json'
PLAN=ROOT/'docs/NATIVE-SHARING-071-PLAN.md'
EXPECTED,NEW=1209,17
PATTERNS=('scripts/*070.py','src/forex_demo_lab/*070.py','tests/*070.py','docs/*070*.md','docs/*071*.md')
ZERO=dict(sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,actual_mt5_repair_verified=False)


def freeze():
    assert datetime.now(timezone.utc).date().isoformat()=='2026-10-07'
    assert sha(PRIOR)=='ae4a0277e1aca79bf76de3a4a7bc5d6a15295b9d343131432c71df91c0c4cb3d'
    p=sealed(PRIOR);review=sealed(ROOT/'reports/sharing-integration-069-completion-review.json')
    assert review['review_passed'] and review['final_source_sha256']==sha(PRIOR)
    assert review['frozen_input_coverage_complete'] and review['tests_passed']==1192
    assert review['bindings_verified']==2190 and review['archive_members_verified']==2026
    assert review['next_policy_sha256']==sha(POLICY) and not review['next_policy_executed']
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2026;API['verify']()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/sharing-integration-069-completion-review.json',ROOT/'reports/sharing-integration-069-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    assert all(not p.exists() for p in (AUTH,RUNTIME,RESERVATION,DISPATCH))
    write(LEDGER,dict(bindings=b,preparation_sha256=sha(PRIOR),policy_sha256=sha(POLICY),helper_profile_sha256=sha(PROFILE),
        prior_bindings_verified=2190,prior_archive_members_verified=2026,tests_retained=1192,
        expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        runtime_phase='69000000000000000000000000000001',declared_date='2026-10-07',maximum_native_sessions=1,
        maximum_sdk_connections=1,maximum_manual_launches=2,maximum_saved_log_reads=1,
        maximum_saved_log_bytes=65536,maximum_session_seconds=900,maximum_market_reads=0,
        maximum_orders=0,maximum_receipt_permissions=0,experts_baseline_saved_via_open_ui=True,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['preparation_sha256']==sha(PRIOR) and l['policy_sha256']==sha(POLICY) and l['helper_profile_sha256']==sha(PROFILE)
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic();r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,new_tests=NEW,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in r.failures+r.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def source_check():
    verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==sha(LEDGER)
    for k,v in {**ZERO,**FALSE}.items():assert t[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-source-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(source_checks_passed=True,tests_passed=EXPECTED)))


def authorize():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-source-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert datetime.now(timezone.utc).date().isoformat()==l['declared_date']
    assert all(not p.exists() for p in (AUTH,RUNTIME,RESERVATION,DISPATCH))
    value=dict(version='sharing_native_070_v1',preparation_sha256=sha(PRIOR),policy_sha256=sha(POLICY),
        helper_profile_sha256=sha(PROFILE),phase=l['runtime_phase'],date=l['declared_date'],
        maximum_sdk_connections=1,maximum_launches=2,maximum_log_reads=1,maximum_log_bytes=65536,
        maximum_market_reads=0,maximum_orders=0,maximum_receipt_permissions=0)
    sys.path.insert(0,str(ROOT/'src'));runpy.run_path(str(ROOT/'scripts/runtime-native-sharing-069.py'))['authorization'](value,sha(PRIOR),sha(POLICY),sha(PROFILE))
    write(AUTH,value)
    print(json.dumps(dict(authorized=True,maximum_native_sessions=1,orders_available=False)))


def check():
    l=verify();r=sealed(RUNTIME);dispatch=sealed(DISPATCH)
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.sharing_audit_070 import same,audit
    expected=dict(dispatch_consumed=True,phase=l['runtime_phase'],preparation_sha256=sha(PRIOR),policy_sha256=sha(POLICY),
        authorization_sha256=sha(AUTH),maximum_native_sessions=1,orders_available=False)
    assert same(dispatch,expected)
    runpy.run_path(str(ROOT/'scripts/runtime-native-sharing-069.py'))['authorization'](sealed(AUTH),sha(PRIOR),sha(POLICY),sha(PROFILE))
    build=sealed(ROOT/'reports/sharing-companion-065-r2-build.json')
    artifact=next(n for n in build['output_bindings'] if n.endswith('/ForexDemoSharing064.ex5'))
    b=dict(source=sha(ROOT/'mt5/Scripts/ForexDemoSharing064.mq5'),ex5=sha(bound(artifact)),
        terminal=l['bindings']['/mnt/c/Program Files/MetaTrader 5/terminal64.exe'],
        editor=l['bindings']['/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe'],
        preparation=sha(PRIOR),policy=sha(POLICY),helper_profile=sha(PROFILE))
    raw=RESERVATION.read_bytes() if RESERVATION.exists() else None
    result=audit(r,b,raw)
    assert not RESERVATION.with_suffix('.sha256').exists()
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(**result,ledger_sha256=sha(LEDGER),
        authorization_sha256=sha(AUTH),dispatch_sha256=sha(DISPATCH),runtime_sha256=sha(RUNTIME),
        reservation_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,tests_passed=EXPECTED))
    print(json.dumps(dict(checker_passed=True,runtime_completed=r['completed'],stopped_stage=r['stopped_stage'],stop_reason=r['stop_reason'])))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');r=sealed(RUNTIME)
    assert c['audit_passed'] and c['runtime_sha256']==sha(RUNTIME) and c['ledger_sha256']==sha(LEDGER)
    counts=r['counts'] or {}
    text=('# Native sharing070 results\n\n'
        f'Completed:{r["completed"]}; stopped stage:{r["stopped_stage"]}; reason:{r["stop_reason"]}. '
        'One exclusive069 dispatch consumed; exact raw reservation/hash audited if created, no assumed sidecar. '
        f'SDK attempts:{counts.get("sdk_connections",0)}; arms:{len(r["script_arms"])}; '
        f'bootstrap:{r["native_private_bootstrap_passed"]}; deployment:{r["deployment_completed"]}; '
        f'signatures:{r["native_signature_checks_passed"]}; log reads:{counts.get("log_reads",0)}; '
        f'SDK shutdown:{r["sdk_shutdown_called"]}; cleanup errors:{r["cleanup_errors"]}. '
        'No quotes/history/orders/receipt permissions. No reconnect/retry/reset/refund.\n\n'
        f'{EXPECTED} tests/{NEW} new audit tests passed before native work; zero failures/errors/skips. '
        '1192 prior preparation tests retained; frozen069/068 source/profile and old067 failure preserved. '
        'This outcome establishes only its measured evidence; native MQL/publication/ACK/root-cause '
        'claims remain false. Profit not established. Next offline outcome-driven NATIVE-SHARING-071-PLAN.md, '
        'not executed. Oct7-only064 cannot be extended for a later date. Keep033/035 gates, historical '
        'clock/cost/coverage/flags/consumed2025/reserved Nov–Dec2026/provider stops; eligibility/orders false.\n')
    with (ROOT/'docs/NATIVE-SHARING-070-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: native sharing070 outcome sealed; read NATIVE-SHARING-070-RESULTS.md. '
        f'Completed:{r["completed"]}, stopped stage:{r["stopped_stage"]}, reason:{r["stop_reason"]}; '
        f'one consumed069 dispatch, SDK:{counts.get("sdk_connections",0)}/arms:{len(r["script_arms"])}; '
        f'bootstrap:{r["native_private_bootstrap_passed"]}/deployment:{r["deployment_completed"]}; '
        f'cleanup errors:{r["cleanup_errors"]}. Exact raw reservation audit, no assumed sidecar. '
        f'{EXPECTED} tests/{NEW} new audit tests passed before native work. Zero quotes/history/orders/grants; '
        'old spent failures and068 helper profile retained. No reconnect/reset/refund/retry. '
        'Next071 offline outcome-driven diagnosis/plan; not executed. Native MQL/publication/ACK/root cause '
        'remain unverified; profit not established. FixedOct7 expiry and market/reserved gates remain; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip',
            'reports/native-sharing-069-runtime*.json','reports/native-sharing-069-runtime*.sha256',
            'reports/native-sharing-069-dispatch*.json','reports/native-sharing-069-dispatch*.sha256'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        runtime_completed=r['completed'],stopped_stage=r['stopped_stage'],tests_passed=EXPECTED,new_tests=NEW,
        native_dispatches=1,sdk_connections=counts.get('sdk_connections',0),script_arms=len(r['script_arms']),**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['audit_passed'] and c['runtime_sha256']==sha(RUNTIME)
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in FALSE.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,runtime_completed=r['runtime_completed'],
        stopped_stage=r['stopped_stage'],next_plan_sha256=sha(PLAN),next_plan_executed=False,**FALSE))
    print(json.dumps(dict(review_passed=True,runtime_completed=r['runtime_completed'],bindings=len(b),members=members)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','source-check','authorize','verify','check','seal','review'))
    dict(freeze=freeze,test=test,**{'source-check':source_check},authorize=authorize,
        verify=lambda:print(len(verify()['bindings'])),check=check,seal=seal,review=review)[p.parse_args().action]()
