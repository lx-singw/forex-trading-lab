"""Freeze/test/check068 source then one separately reserved helper SELF profile."""
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
OLD=runpy.run_path(str(ROOT/'scripts/audit-native-sharing-067-r2.py'))
sha,sealed,write,bound=(OLD[k] for k in ('sha','sealed','write','bound'))
ARCHIVE,HANDOFF=OLD['ARCHIVE'],OLD['HANDOFF']
PRIOR=ROOT/'reports/native-sharing-067-r2-final-source.json'
PREFIX='image-correction-068';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
EXPECTED,NEW=1158,30
PATTERNS=('scripts/*068.py','src/forex_demo_lab/*068.py','tests/*068.py','docs/*068*.md','docs/*069*.md')
PYTHON='/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python/Scripts/python.exe'
PYTHON_SHA='b70275ad94210fce7548761143be5e177769721045e287bb6c80aac3f928c65b'
PACKAGE='/mnt/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0/'
ZERO=dict(sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    native_metatrader_compiler_invocations=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,native_adapter_ready=False,actual_mt5_repair_verified=False)


def freeze():
    p=sealed(PRIOR);assert sha(PRIOR)=='590fac8cb98c4b6b27881cb80b037add5c274613921b56b77d1c127270be6dc6'
    r=sealed(ROOT/'reports/native-sharing-067-r2-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['next_plan_sha256']==sha(ROOT/'docs/NATIVE-SHARING-068-PLAN.md')
    b=dict(p['source_and_evidence_bindings']);assert len(b)==2136
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==1978
    assert not (ROOT/'reports/native-sharing-066-runtime-reservation.sha256').exists()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        ROOT/'reports/native-sharing-067-r2-completion-review.json',ROOT/'reports/native-sharing-067-r2-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    assert sha(bound(PYTHON))==PYTHON_SHA
    config='/mnt/c/Users/Linda Singwane/.forex-demo-lab/mt5-python/pyvenv.cfg'
    chain=dict(launcher=PYTHON,config=config,images=[PACKAGE+'python.exe',PACKAGE+'python3.13.exe'],
        library=PACKAGE+'python313.dll',base_alias=r'C:\Users\Linda Singwane\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe')
    for n in (config,chain['library'],*chain['images']):b[n]=sha(bound(n))
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        prior_bindings_verified=2136,prior_archive_members_verified=1978,maximum_self_profiles=1,
        python_sha256=PYTHON_SHA,helper_chain=chain,maximum_mt5_sessions=0,
        per_file_image_cap=136314880,aggregate_guard_hash_bytes=103079215104,
        prefreeze_inventory=dict(config_reads=1,package_queries=1,package_file_inventories=1,version='3.13.14',package_version='3.13.3824.0'),
        **ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
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
    old=sealed(ROOT/'reports/native-sharing-066-runtime.json')
    assert not old['completed'] and old['counts']['hash_bytes']==0 and old['counts']['sdk_connections']==0
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED)))


def check_profile():
    l=verify();p=sealed(ROOT/'reports/helper-profile-068.json');started=sealed(ROOT/'reports/helper-profile-068-started.json')
    assert p['ledger_sha256']==started['ledger_sha256']==sha(LEDGER)
    assert p['source_checks_sha256']==sha(ROOT/f'reports/{PREFIX}-checks.json')
    assert all(p[k]==v for k,v in {**ZERO,**FALSE}.items() if k in p)
    assert p['sdk_connections']==p['mt5_invocations']==p['market_reads']==p['orders']==0
    sys.path.insert(0,str(ROOT/'src'));profile=runpy.run_path(str(ROOT/'scripts/profile-helper-068.py'))
    caps=profile['SELF_LIMITS'];counts=p['counts']
    assert set(counts)==set(caps) and all(type(v) is int and 0<=v<=caps[k] for k,v in counts.items())
    assert p['cleanup']['all_handles_closed'] and p['cleanup']['allocations_released'] and p['cleanup']['unconfirmed_handles']==0
    if p['profile_verified']:
        assert p['native_signature_checks_passed'] and p['loaded_python_library_matches_pin']
        assert p['actual_helper_image_name'] in ('python.exe','python3.13.exe')
        assert counts['hash_reads']==5 and counts['process_opens']==counts['identity_tokens']==2 and counts['closes']==4
    else:assert p['stop_reason'] and p['stopped_stage']
    write(ROOT/f'reports/{PREFIX}-profile-checks.json',dict(checker_passed=True,profile_verified=p['profile_verified'],
        profile_sha256=sha(ROOT/'reports/helper-profile-068.json'),ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,profile_verified=p['profile_verified'])))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-profile-checks.json');p=sealed(ROOT/'reports/helper-profile-068.json')
    assert c['checker_passed'] and c['profile_sha256']==sha(ROOT/'reports/helper-profile-068.json')
    text=('# Image correction068 results\n\n1158 tests/30 new pass, zero failures/errors/skips. '
        'Separate image reader raises per-file cap128→130MiB while retaining96GiB aggregate budget, exact hashes '
        'and uncached checks. Descriptor/path identity/size/mtime and late-change/expiry/stream cleanup tested. '
        'Requested byte allowances reserve before read; failed/short reads never refund. Fixed stage diagnostics '
        'and exact reservation-byte/hash decisions prepared. Original065/066/067 failures and spent reservation retained.\n\n'
        f'One bounded Windows self profile verified:{p["profile_verified"]}; stopped stage:{p["stopped_stage"]}; '
        f'stop:{p["stop_reason"]}; helper equals sys.executable:{p["helper_image_equals_sys_executable"]}. '
        'Installed package/launcher/config/library inputs source-bound; native process identities remain private. '
        'No MT5 enumeration/SDK/deployment/sandbox creation/log/quotes/history/orders/receipt actions. '
        'Profile cleanup checked; no rerun or native MT5 sharing claim.\n\n'
        'Next NATIVE-SHARING-069-PLAN.md corrected runtime integration with actual helper pin and stage diagnostics '
        'before new native reservation/policy. Actual helper/MT5 logon equality, SDK/MQL sharing/publication/ACK remain '
        'unverified. Oct7 MQL source expires later. Old market gates/033/035/clock/cost/coverage/flags/consumed2025/'
        'reserved Nov–Dec2026/provider stops remain; fresh/annual eligibility/orders false.\n')
    with (ROOT/'docs/IMAGE-CORRECTION-068-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: separate image correction068 sealed; read IMAGE-CORRECTION-068-RESULTS.md. '
        '1158 tests/30 new pass; bounded130MiB file cap,96GiB aggregate, uncached exact hashes and descriptor/path '
        'identity/size/mtime/cleanup checks. Fixed stages/exact-byte reservation checks prepared. '
        f'One self-only native helper profile verified:{p["profile_verified"]}, stage:{p["stopped_stage"]}, '
        f'same sys.executable:{p["helper_image_equals_sys_executable"]}; cleanup checked. '
        'Zero MT5/SDK/deploy/log/market/orders/grants. Original067 size/checker failures and spent066 reservation retained. '
        'Next069 corrected runtime integration/tests before new MT5 phase, not executed. Actual MQL/private peer integration/'
        'publication/ACK remain unverified. FixedOct7 source expires later; market gates/reserved exclusions retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip',
        'reports/helper-profile-068*.json','reports/helper-profile-068*.sha256'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,native_self_profiles=1,helper_profile_verified=p['profile_verified'],**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    plan=ROOT/'docs/NATIVE-SHARING-069-PLAN.md';assert b[plan.relative_to(ROOT).as_posix()]==sha(plan)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,
        helper_profile_verified=r['helper_profile_verified'],next_plan_sha256=sha(plan),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','check-profile','seal','review','verify'))
    dict(freeze=freeze,test=test,check=check,**{'check-profile':check_profile},seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
