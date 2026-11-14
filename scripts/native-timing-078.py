"""Offline entry preparation/closure; authorization is a later separate action."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/timing-profile-077.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='native-timing-078';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/timing-profile-077-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-TIMING-078-PLAN.md'
DESIGN=ROOT/'docs/NATIVE-TIMING-078-DESIGN.md';POLICY=ROOT/'docs/NATIVE-TIMING-078-POLICY.md'
PLAN=ROOT/'docs/NATIVE-TIMING-079-PLAN.md';PROFILE=ROOT/'reports/helper-profile-068.json'
EXPECTED,NEW=1492,39
PATTERNS=('scripts/*078.py','src/forex_demo_lab/*078.py','tests/*078.py','docs/*078-DESIGN.md',
    'docs/*078-POLICY.md','docs/*079-PLAN.md')
ZERO,FALSE=API['ZERO'],API['FALSE']
CASES=('success','real','sdk_changed','initialize_failed','signature_failed','initialize_interrupted')
FUTURE_NAMES=('authorization.json','authorization.sha256','dispatch-started.json','sdk-reservation.json','runtime.json','runtime.sha256')


def runtime_inputs():
    sys.path.insert(0,str(ROOT/'src'))
    entry=runpy.run_path(str(ROOT/'scripts/runtime-native-timing-078.py'))
    sources=entry['dependency_files078'](ROOT)
    build,retained=API['API']['compiled_evidence']()
    old=sealed(ROOT/'reports/sharing-integration-069-ledger.json')
    profile=sealed(PROFILE)
    assert profile['profile_verified'] and profile['native_signature_checks_passed']
    assert profile['actual_helper_image_name']==old['measured_helper_name']=='python3.13.exe'
    names=sealed(ROOT/'reports/sharing-build-075-native.json')['output_bindings']
    artifact=next(n for n in names if n.endswith('/ForexDemoSharing072.ex5'))
    terminal='/mnt/c/Program Files/MetaTrader 5/terminal64.exe'
    editor='/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe'
    shell='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    sdkroot=old['helper_chain']['launcher'].rsplit('/Scripts/',1)[0]+'/Lib/site-packages/MetaTrader5/'
    sdk=(sdkroot+'__init__.py',sdkroot+'_core.cp313-win_amd64.pyd',shell,
        shell.rsplit('/',1)[0]+'/Modules/Microsoft.PowerShell.Security/Microsoft.PowerShell.Security.psd1',
        shell.rsplit('/',1)[0]+'/Modules/Microsoft.PowerShell.Management/Microsoft.PowerShell.Management.psd1')
    p=old['helper_chain'];external=(terminal,editor,artifact,p['launcher'],p['config'],p['library'],*p['images'],*sdk)
    bindings={n:sha(bound(n)) for n in (*sources,*build.record()['input_bindings'],*external)}
    for n in external:
        expected=names[n] if n==artifact else old['bindings'][n]
        assert bindings[n]==expected,n
    assert bindings[terminal]==build.record()['terminal_sha256'] and bindings[editor]==build.record()['compiler_sha256']
    return dict(runtime_sources=list(sources),runtime_bindings=bindings,helper_chain=p,
        helper_profile_sha256=sha(PROFILE),build_record=build.record(),retained_build=retained,
        terminal_name=terminal,editor_name=editor,artifact_name=artifact,shell_name=shell,sdk_bindings=list(sdk))


def freeze():
    assert sha(PRIOR)=='625bb06f2d8b650dc0dd692609c3c2f7614aaed9de1655f5c72aa9c29b83590d'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/timing-profile-077-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert (r['tests_passed'],r['bindings_verified'],r['archive_members_verified'])==(1453,2423,2237)
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='32c6be4c6aeb770a50bf5cd5c0d4e62922a5ee267409082478b4cb043fd14a5d'
    assert not r['next_plan_executed'] and r['profile_cases_verified']==4 and r['handshake_cases_verified']==14
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2237;API['verify']()
    runtime=runtime_inputs()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        ROOT/'reports/timing-profile-077-completion-review.json',ROOT/'reports/timing-profile-077-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    for n,h in runtime['runtime_bindings'].items():assert b[n]==h,n
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),future_plan_sha256=sha(PLAN),
        phase='78000000000000000000000000000001',declared_date='2026-10-08',
        preparation_date=datetime.now(timezone.utc).date().isoformat(),entry_cases=list(CASES),
        tests_retained=1453,expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        maximum_preparation_native_sessions=0,conditional_future_sessions=1,
        prior_bindings_verified=2423,prior_archive_members_verified=2237,**runtime,**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),runtime_sources=len(runtime['runtime_sources']),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    for key,path in (('prior_source_sha256',PRIOR),('prior_plan_sha256',PRIOR_PLAN),('design_sha256',DESIGN),
        ('policy_sha256',POLICY),('future_plan_sha256',PLAN)):assert l[key]==sha(path)
    runtime=runtime_inputs()
    for k,v in runtime.items():assert l[k]==v,k
    assert l['entry_cases']==list(CASES)
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


def entry_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from dataclasses import replace
    from test_native_timing_078 import fixture078,run078
    with TemporaryDirectory() as d:
        f=fixture078(Path(d))
        if name=='real':f.sdk.account.trade_mode=2;f.sdk.account.server='Demo'
        elif name=='sdk_changed':
            old=f.hooks.reader
            def reader(base):r=old(base);r.values['sdkcore']='0'*64;return r
            f.hooks=replace(f.hooks,reader=reader)
        elif name=='initialize_failed':f.sdk.initialize=lambda *a,**k:f.calls.append('initialize') or False
        elif name=='signature_failed':f.state.trust=False
        elif name=='initialize_interrupted':
            def initialize(*a,**k):f.calls.append('initialize');raise KeyboardInterrupt('private')
            f.sdk.initialize=initialize
        result=run078(f)
        return dict(result=result,dependencies_injected=True,activity=list(f.calls),
            owned_backend_closes=f.state.base.closed if f.state.base else 0,
            raw_dispatch_sha256=sha(Path(d)/'dispatch'),
            raw_component_sha256=sha(Path(d)/'reservation'),
            raw_authorization_sha256=f.ash)


def evidence():
    l=verify();rows={name:entry_case(name) for name in CASES}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(ledger_sha256=sha(LEDGER),retained_build=l['retained_build'],
        cases=rows,dependencies_injected=True,native_timing_unknown=True,old070_root_cause_unknown=True,**ZERO,**FALSE))
    print(json.dumps(dict(entry_cases=len(rows),modeled_completions=sum(v['result']['entry_completed'] for v in rows.values()),native_sessions=0)))


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and set(e['cases'])==set(CASES)
    assert e['retained_build']==l['retained_build'] and e['dependencies_injected'] and e['native_timing_unknown']
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.timing_profile_077 import LIMITS077
    # Independently enumerate bootstrap segments and phase activity. Never call
    # run_entry078/bootstrap/profile_once077 or infer native bounds from averages.
    references=dict(
        success=dict(activity=['backend','signature','import','initialize','shutdown'],stage=None,hashes=126,guards=8,queries=89,sdk=1),
        real=dict(activity=['backend','signature','import','initialize','shutdown'],stage='profile_samples',hashes=28,guards=1,queries=3,sdk=1),
        sdk_changed=dict(activity=['backend'],stage='preflight',hashes=2,guards=0,queries=0,sdk=0),
        initialize_failed=dict(activity=['backend','signature','import','initialize','shutdown'],stage='sdk_attach',hashes=24,guards=0,queries=0,sdk=1),
        signature_failed=dict(activity=['backend','signature'],stage='signature',hashes=12,guards=0,queries=0,sdk=0),
        initialize_interrupted=dict(activity=['backend','signature','import','initialize','shutdown'],stage='sdk_attach',hashes=24,guards=0,queries=0,sdk=1))
    # Successful bootstrap:10 SDK/source/artifact hashes,2 terminal/editor,
    #5 SDK after signature,2 process images,3 helper-chain inputs and4 attach
    #process images =26. Each sample adds12 guard hashes +5 SDK +4 helper +4 sources.
    bootstrap_segments=[5,4,1,2,5,2,3,4]
    assert sum(bootstrap_segments)==26 and sum([12,5,4,4])==25
    for name,ref in references.items():
        value=e['cases'][name];r=value['result'];counts=r['counts']
        assert value['dependencies_injected'] and value['activity']==ref['activity'] and value['owned_backend_closes']==1
        assert type(r['entry_completed']) is bool and r['entry_completed']==(name=='success')
        assert r['stopped_stage']==ref['stage'] and r['signature_checks_passed']==(name not in ('sdk_changed','signature_failed'))
        for key,expected in (('hash_reads',ref['hashes']),('guards',ref['guards']),('sdk_queries',ref['queries']),
            ('sdk_connections',ref['sdk']),('sdk_shutdowns',ref['sdk'])):
            assert type(counts[key]) is int and counts[key]==expected,(name,key,counts[key],expected)
        assert all(type(v) is int and 0<=v<=LIMITS077[k] for k,v in counts.items())
        assert counts['hash_bytes']==ref['hashes']*1048576
        assert r['cleanup']['sdk_shutdown_called']==bool(ref['sdk']) and not r['cleanup']['errors']
        assert value['raw_component_sha256']==r['reservation_sha256']==r['component_contract_sha256']
        assert value['raw_authorization_sha256']==r['authorization_sha256']
        if name=='success':
            rows=r['observation']['samples'];assert len(rows)==4
            assert all(v==dict(core_guard_ms=[0,0],composite_sample_ms=0,hash_reads=25,hash_bytes=25*1048576,sdk_queries=22) for v in rows)
        if name=='real':assert r['observation']['samples_completed']==0
        for k in ('script_arms','deployment_directories','deployment_writes','directories','writes','reads','log_reads','log_bytes'):
            assert counts[k]==0
        for k in ('latency_guaranteed','native_launch_ready','native_mql_verified','native_publication_verified','orders_available'):
            assert r[k] is False
        for k in ('script_launches','terminal_deployments','terminal_log_content_reads','market_reads','orders','receipt_permissions'):
            assert type(r[k]) is int and r[k]==0
    for data in (l,t,e):
        for k,v in {**ZERO,**FALSE}.items():assert type(data[k]) is type(v) and data[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    assert not list(ROOT.glob('mt5/**/ForexDemoSharing072.ex5'))
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,entry_cases_verified=6,modeled_completions=1,modeled_rejections=5,
        runtime_sources_verified=len(l['runtime_sources']),independent_activity=references,
        bootstrap_hash_segments=bootstrap_segments,retained_build_validated=True,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,entry_cases_verified=6)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    text=(f'# Windows timing entry078 preparation results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'The Windows metadata-only entry point and conditional policy are frozen/tested. Exact fresh078 authority and '
        'once-only outer dispatch bind the retained077 component schema with new preparation/policy hashes. Installed '
        'SDK/shell files are rehashed before import, after signature checking and in every sample. Same owned SDK/backend '
        'and successful attachment are mandatory; cleanup runs on failure/interruption without retry.\n\n'
        'Six fixed injected entry cases independently checked:1 modeled completion/5 rejections. Tests cover actual '
        'real/contest accounts, installed-input change, failed/interrupted initialization, signature rejection, budgets, '
        'stale/repeated grants, partial markers and cleanup failures. The bounded public loader verifies29 local Python '
        'dependencies plus its launcher; native caps remain the exact077 four-sample/eight-guard limits. Native calls '
        'cannot be preempted by clock checks.\n\n'
        'Zero new native SDK/MT5/compiler/deployment/log-content/profile/market/orders/receipt operations. No authorization '
        'or native dispatch/reservation/runtime created in078 preparation. Native timing/sharing/publication/ACK/profit '
        'and070 cause remain unproven; all observations injected, eligibility/orders false. Original075 actual-exit1 '
        'artifact,076 timing,077 bytes and old raw markers preserved. Next079 verifies078 review then records separate '
        'authorization and runs at most one existing-terminal metadata profile if Oct8 and all current pins still fit; '
        'otherwise fresh metadata preparation required. Unexecuted.033/035, clock/cost/coverage/flags, consumed2025, '
        'reserved Nov-Dec2026 and provider stops retained.\n')
    with (ROOT/'docs/NATIVE-TIMING-078-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-08: offline Windows timing entry078 sealed; read NATIVE-TIMING-078-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass;6 independent injected entry cases:1 completion/5 rejections. Fresh078 exact '
        'authority/dispatch, unchanged077 component types with new bindings,29 frozen source dependencies, bounded public '
        'loader, installed SDK/shell rehashes and once-owned cleanup prepared. Four samples/eight full guards and077 '
        'native caps retained. No native authorization/dispatch/SDK/MT5/compiler/deploy/log/profile/market/orders/grants '
        'created or run. Native timing/sharing/publication/ACK/profit and070 cause unproven. Next079 review then separately '
        'authorize/run one metadata-only existing-terminal profile if Oct8/pins valid; unexecuted. Old075-exit1 artifact, '
        '076/077 source, raw spent markers and all data gates preserved. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(path)
    for pattern in (*PATTERNS,'docs/NATIVE-TIMING-078-RESULTS.md',f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,entry_cases_verified=6,modeled_completions=1,modeled_rejections=5,
        runtime_sources_verified=len(l['runtime_sources']),future_plan_executed=False,retained_build_validated=True,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert not r['future_plan_executed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,
        entry_cases_verified=6,modeled_completions=1,modeled_rejections=5,runtime_sources_verified=len(l['runtime_sources']),
        next_plan_sha256=sha(PLAN),next_plan_executed=False,retained_build_validated=True,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,tests_passed=EXPECTED)))


def authorize():
    # Future079 only. This action is never part of the078 preparation sequence.
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final)
    review=sealed(ROOT/f'reports/{PREFIX}-completion-review.json')
    assert review['review_passed'] and review['final_source_sha256']==sha(final) and review['frozen_input_coverage_complete']
    assert review['tests_passed']==EXPECTED and not review['next_plan_executed']
    assert datetime.now(timezone.utc).date().isoformat()==l['declared_date']
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    for n,h in r['source_and_evidence_bindings'].items():assert sha(bound(n))==h,n
    assert ARCHIVE(final,r)==review['archive_members_verified']
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.native_timing_078 import Spec078,authorization078,validate_authorization078
    from forex_demo_lab.sharing_adapter_076 import VerifiedBuild076,encoded076
    from forex_demo_lab.image_guard_068 import HelperChain068
    def pair(n):return str(bound(n)),l['runtime_bindings'][n]
    p=l['helper_chain'];chain=HelperChain068(pair(p['launcher']),pair(p['config']),tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
    build=VerifiedBuild076(encoded076(l['build_record']))
    spec=Spec078(build,sha(final),sha(POLICY),sha(PROFILE),chain,pair(l['terminal_name']),pair(l['editor_name']),
        pair(l['artifact_name']),tuple((n,str(ROOT/n)) for n in build.record()['input_bindings']),tuple(pair(n) for n in l['sdk_bindings']))
    value=authorization078(sha(final),sha(POLICY),sha(PROFILE),sha(LEDGER),
        l['runtime_bindings']['scripts/runtime-native-timing-078.py'],build.sha256,spec.component_sha256)
    raw=encoded076(value);digest=hashlib.sha256(raw).hexdigest();validate_authorization078(raw,value,digest)
    path=ROOT/f'reports/{PREFIX}-authorization.json'
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    with path.with_suffix('.sha256').open('xb') as f:f.write((digest+'\n').encode('ascii'));f.flush();os.fsync(f.fileno())
    print(json.dumps(dict(authorized=True,maximum_native_sessions=1,maximum_script_launches=0,orders_available=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','evidence','check','seal','review','verify','authorize'))
    dict(freeze=freeze,test=test,evidence=evidence,check=check,seal=seal,review=review,authorize=authorize,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
