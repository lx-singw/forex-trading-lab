"""Freeze/test/check/seal corrected069 integration; no native session here."""
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
OLD=runpy.run_path(str(ROOT/'scripts/image-correction-068.py'))
sha,sealed,write,bound=(OLD[k] for k in ('sha','sealed','write','bound'))
ARCHIVE,HANDOFF=OLD['ARCHIVE'],OLD['HANDOFF']
PRIOR=ROOT/'reports/image-correction-068-final-source.json'
PREFIX='sharing-integration-069';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PROFILE=ROOT/'reports/helper-profile-068.json';POLICY=ROOT/'docs/NATIVE-SHARING-070-POLICY.md'
EXPECTED,NEW=1192,34
PATTERNS=('scripts/*069.py','src/forex_demo_lab/*069.py','tests/*069.py','docs/*069*.md','docs/*070*.md')
ZERO=dict(sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    native_metatrader_compiler_invocations=0,native_self_profiles=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,native_adapter_ready=False,actual_mt5_repair_verified=False)


def freeze():
    p=sealed(PRIOR);assert sha(PRIOR)=='d47f9e09f89fc52cd817446e9009b1e2c569000c1bf27eba90ffd93afb80e995'
    r=sealed(ROOT/'reports/image-correction-068-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-SHARING-069-PLAN.md')
    assert r['tests_passed']==1158 and r['helper_profile_verified']
    b=dict(p['source_and_evidence_bindings']);assert len(b)==2167
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2005
    old=OLD['verify']();profile=sealed(PROFILE)
    assert profile['profile_verified'] and profile['native_signature_checks_passed'] and profile['loaded_python_library_matches_pin']
    assert profile['ledger_sha256']==sha(OLD['LEDGER']) and profile['actual_helper_image_name']=='python3.13.exe'
    assert not profile['helper_image_equals_sys_executable']
    assert not (ROOT/'reports/native-sharing-066-runtime-reservation.sha256').exists()
    assert not (ROOT/'reports/native-sharing-069-runtime-reservation.json').exists()
    assert not (ROOT/'reports/native-sharing-069-dispatch-started.json').exists()
    assert not (ROOT/'reports/native-sharing-070-authorization.json').exists()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/image-correction-068-completion-review.json',ROOT/'reports/image-correction-068-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    chain=dict(old['helper_chain']);chain['images']=[n for n in chain['images'] if n.rsplit('/',1)[-1]==profile['actual_helper_image_name']]
    assert len(chain['images'])==1 and sha(bound(chain['launcher']))==old['python_sha256']
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        prior_bindings_verified=2167,prior_archive_members_verified=2005,maximum_native_sessions=0,
        python_sha256=old['python_sha256'],helper_chain=chain,measured_helper_name=profile['actual_helper_image_name'],
        helper_profile_sha256=sha(PROFILE),future_policy_sha256=sha(POLICY),
        per_file_image_cap=136314880,aggregate_guard_hash_bytes=103079215104,
        maximum_startup_path_stats=64,maximum_stage_events=32,**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['helper_profile_sha256']==sha(PROFILE) and l['future_policy_sha256']==sha(POLICY)
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(suite_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic();result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    passed=result.wasSuccessful() and result.testsRun==EXPECTED and not result.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=result.testsRun,new_tests=NEW,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        failure_details=[dict(test=str(t),traceback=d) for t,d in result.failures+result.errors],
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert t['passed'] and t['tests_run']==EXPECTED and t['ledger_sha256']==sha(LEDGER)
    assert (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    for k,v in {**ZERO,**FALSE}.items():assert t[k]==l[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.image_guard_068 import MAX_IMAGE_BYTES
    from forex_demo_lab.sharing_runtime_069 import LIMITS069,PHASE
    assert MAX_IMAGE_BYTES==l['per_file_image_cap']==136314880
    assert LIMITS069['hash_bytes']==l['aggregate_guard_hash_bytes']==103079215104
    assert LIMITS069['startup_path_stats']==64 and PHASE=='69000000000000000000000000000001'
    assert len(l['helper_chain']['images'])==1 and l['helper_chain']['images'][0].endswith('/python3.13.exe')
    old=sealed(ROOT/'reports/native-sharing-066-runtime.json')
    assert not old['completed'] and old['counts']['hash_bytes']==old['counts']['sdk_connections']==0
    assert not (ROOT/'reports/native-sharing-066-runtime-reservation.sha256').exists()
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    for n in ('reports/native-sharing-069-runtime-reservation.json','reports/native-sharing-069-runtime.json',
              'reports/native-sharing-069-dispatch-started.json','reports/native-sharing-070-authorization.json'):
        assert not (ROOT/n).exists()
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,
        helper_profile_retained=True,measured_helper_pin_integrated=True,future_policy_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    text=(f'# Sharing integration069 results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'New phase069 integrates corrected NativeIdentity068130MiB per file/96GiB aggregate uncached hashes and '
        'measured native python3.13.exe helper alone, launcher/config/library/alias pins and native logon/session checks. '
        'Fixed32-event stage diagnostics,64 startup path stats, exclusive dispatch/reservation exact-byte SHA, '
        'early sanitized outcome and once-owned cleanup including expired/failed SDK attachment tested. '
        'Missing/malformed cleanup proof fails; real/contest accounts rejected before file preparation.\n\n'
        'This stage is preparation only: zero SDK/native MT5/compiler/deployment/terminal log/market/orders/grants. '
        'Injected completed sequences remain synthetic tests, not actual MQL/private bootstrap/sharing/publication/ACK proof. '
        'Retained068 helper self profile was not rerun. Original066 consumed reservation,067 native-size failure and '
        'sidecar checker failure remain immutable; original128MiB reader unchanged.\n\n'
        'Next NATIVE-SHARING-070-POLICY.md source-bound one native session, not authorized/executed here. '
        'Actual Oct7 UTC/unused064 sandbox mandatory or new declared MQL source/phase/build. Slow uncached guards '
        'can miss30s hold and must fail; opaque SDK calls cannot be preempted by after-return checks. '
        'Profit not established. Preserve033/035 failures, clock/cost/coverage/flags, consumed2025, reserved '
        'Nov–Dec2026/provider stops. Fresh/annual eligibility/orders remain false.\n')
    with (ROOT/'docs/SHARING-INTEGRATION-069-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: corrected sharing integration069 sealed; read SHARING-INTEGRATION-069-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass, zero failures/errors/skips. New069 runtime uses bounded130MiB image reader '
        'and measured native python3.13.exe helper/launch chain; uncached identity/session/logon guards retained. '
        'Fixed stage diagnostics, bounded path checks, exact raw reservation SHA, early outcome and owned cleanup tested. '
        'Preparation only: zero SDK/MT5/compiler/deploy/log/market/orders/grants;068 self profile retained without rerun. '
        'Old066 spent reservation/067 size and checker failures remain. Next070 controlled native session policy, '
        'not authorized/executed; Oct7 expiry/unused sandbox required. Actual MQL/private bootstrap/sharing/publication/ACK '
        'remain unverified; profit not established; market gates/reserved exclusions retained; fresh/annual eligibility/orders false. '
        'Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,helper_profile_retained=True,corrected_runtime_prepared=True,future_policy_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[POLICY.relative_to(ROOT).as_posix()]==sha(POLICY) and not r['future_policy_executed']
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,
        helper_profile_retained=True,next_policy_sha256=sha(POLICY),next_policy_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    dict(freeze=freeze,test=test,check=check,seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
