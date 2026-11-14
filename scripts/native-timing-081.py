"""Freeze/test/review fresh081 preparation. Native authorization is later082."""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PureWindowsPath
import runpy
import sys
from tempfile import TemporaryDirectory
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/public-preflight-080.py'))
PINS=runpy.run_path(str(ROOT/'scripts/native-timing-078.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='native-timing-081';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/public-preflight-080-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-TIMING-081-PLAN.md'
DESIGN=ROOT/'docs/NATIVE-TIMING-081-DESIGN.md';POLICY=ROOT/'docs/NATIVE-TIMING-081-POLICY.md'
PLAN=ROOT/'docs/NATIVE-TIMING-082-PLAN.md';PROFILE=ROOT/'reports/helper-profile-068.json'
EXPECTED,NEW=1604,60
OWN=('src/forex_demo_lab/native_timing_081.py','src/forex_demo_lab/public_trace_081.py',
    'scripts/runtime-native-timing-081.py','scripts/native-timing-081.py',
    'tests/test_native_timing_081.py','tests/test_public_entry_081.py',
    'docs/NATIVE-TIMING-081-DESIGN.md','docs/NATIVE-TIMING-081-POLICY.md','docs/NATIVE-TIMING-082-PLAN.md')
ZERO,FALSE=API['ZERO'],API['FALSE']
CASES=('success','real','sdk_changed','initialize_failed','signature_failed','initialize_interrupted')
PUBLIC_CASES=('windows_crlf','oversized_profile','changed_source','stale_authority')
FUTURE_NAMES=('authorization.json','authorization.sha256','invocation-started.json','invocation-started.sha256',
    'public-outcome.json','public-outcome.sha256','dispatch-started.json','dispatch-started.sha256',
    'sdk-reservation.json','sdk-reservation.sha256','runtime.json','runtime.sha256')


def derivation():
    old=(ROOT/'src/forex_demo_lab/native_timing_078.py').read_text()
    expected=old.replace('078','081').replace('78000000000000000000000000000001','81000000000000000000000000000001')
    expected=expected.replace('profile_contract077,LIMITS077,DATE,SAMPLES)\n',
        'profile_contract077,LIMITS077,DATE,SAMPLES)\nfrom .public_trace_081 import PUBLIC_LIMITS081,invocation_bytes081\n')
    expected=expected.replace('component_contract_sha256=component,maximum_native_sessions=1,\n',
        'component_contract_sha256=component,maximum_native_sessions=1,\n'
        '        maximum_native_entry_invocations=1,public_limits=dict(PUBLIC_LIMITS081),\n'
        '        invocation_contract_sha256=hashlib.sha256(invocation_bytes081()).hexdigest(),\n')
    assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((ROOT/'src/forex_demo_lab/native_timing_081.py').read_text()))
    old_tree=ast.parse((ROOT/'scripts/runtime-native-timing-078.py').read_text())
    new_tree=ast.parse((ROOT/'scripts/runtime-native-timing-081.py').read_text())
    for name in ('bound078','loaded_library078','signature078'):
        a=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        b=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef) and n.name==name.replace('078','081'))
        normalized=ast.parse(ast.unparse(a).replace('078','081')).body[0]
        assert ast.dump(normalized)==ast.dump(b)
    return dict(core_derivation_verified=True,unchanged_native_helpers=3,
        only_core_changes=['fresh081_names_and_phase','public_limits_authority_binding','invocation_contract_authority_binding'])


def runtime_inputs():
    old=PINS['runtime_inputs']();entry=runpy.run_path(str(ROOT/'scripts/runtime-native-timing-081.py'))
    sources=entry['dependency_files081'](ROOT)
    old_sources=set(old['runtime_sources'])
    bindings={n:h for n,h in old['runtime_bindings'].items() if n not in old_sources}
    bindings.update({n:sha(ROOT/n) for n in sources})
    return {**old,'runtime_sources':list(sources),'runtime_bindings':bindings}


def spec_and_auth(ledger,preparation):
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.native_timing_081 import Spec081,authorization081
    from forex_demo_lab.image_guard_068 import HelperChain068
    from forex_demo_lab.sharing_adapter_076 import VerifiedBuild076,encoded076
    def pair(n):return str(bound(n)),ledger['runtime_bindings'][n]
    p=ledger['helper_chain'];chain=HelperChain068(pair(p['launcher']),pair(p['config']),
        tuple(pair(n) for n in p['images']),pair(p['library']),p['base_alias'])
    build=VerifiedBuild076(encoded076(ledger['build_record']))
    spec=Spec081(build,preparation,sha(POLICY),sha(PROFILE),chain,pair(ledger['terminal_name']),
        pair(ledger['editor_name']),pair(ledger['artifact_name']),
        tuple((n,str(ROOT/n)) for n in build.record()['input_bindings']),tuple(pair(n) for n in ledger['sdk_bindings']))
    value=authorization081(preparation,sha(POLICY),sha(PROFILE),sha(LEDGER),
        ledger['runtime_bindings']['scripts/runtime-native-timing-081.py'],build.sha256,spec.component_sha256)
    return spec,value


def freeze():
    API['verify']();p=sealed(PRIOR);r=sealed(ROOT/'reports/public-preflight-080-completion-review.json')
    assert sha(PRIOR)=='9b94c0adbf59e6fd4859efeec7b8390f9a7cc03ede91902d941c213d803a25ee'
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert (r['bindings_verified'],r['archive_members_verified'],r['new_tests_passed'])==(2502,2310,28)
    assert r['modeled_cases_verified']==3 and r['unchanged_integrity_methods_verified']==4
    assert r['deterministic_sidecar_blocker_proven'] and not r['original079_first_failure_proven']
    assert not r['next_plan_executed'] and r['next_plan_sha256']==sha(PRIOR_PLAN)
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2310
    runtime=runtime_inputs();d=derivation()
    assert len(runtime['runtime_sources'])==31
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        ROOT/'reports/public-preflight-080-completion-review.json',ROOT/'reports/public-preflight-080-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    for n,h in runtime['runtime_bindings'].items():assert b[n]==h,n
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),policy_sha256=sha(POLICY),future_plan_sha256=sha(PLAN),
        phase='81000000000000000000000000000001',declared_date='2026-10-08',
        preparation_date=datetime.now(timezone.utc).date().isoformat(),expected_tests=EXPECTED,new_tests=NEW,
        retained_tests=1544,maximum_full_regressions=1,maximum_preparation_native_sessions=0,
        conditional_future_sessions=1,entry_cases=list(CASES),public_cases=list(PUBLIC_CASES),
        prior_bindings_verified=2502,prior_archive_members_verified=2310,derivation=d,**runtime,**ZERO,**FALSE))
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
    for k,v in runtime_inputs().items():assert l[k]==v,k
    assert l['derivation']==derivation() and l['entry_cases']==list(CASES) and l['public_cases']==list(PUBLIC_CASES)
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
    from test_native_timing_081 import fixture081,run081
    with TemporaryDirectory() as d:
        f=fixture081(Path(d))
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
        r=run081(f)
        return dict(result=r,dependencies_injected=True,activity=list(f.calls),
            owned_backend_closes=f.state.base.closed if f.state.base else 0,
            raw_dispatch_sha256=sha(Path(d)/'dispatch'),raw_component_sha256=sha(Path(d)/'reservation'),
            raw_authorization_sha256=f.ash)


def public_case(name):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
    from unittest.mock import patch
    from forex_demo_lab import public_trace_081 as trace_module,public_preflight_080 as reader_module
    from forex_demo_lab.public_trace_081 import PublicTrace081,reserve_invocation081,invocation_bytes081
    from forex_demo_lab.native_timing_081 import reserve_dispatch081
    from forex_demo_lab.public_model_080 import WINDOWS_ROOT080,DATE_CLOCK080,model_paths080
    from test_public_entry_081 import sealed_fixture081,entry
    with TemporaryDirectory() as d:
        root=Path(d);f=sealed_fixture081(root);inv=reserve_invocation081(root/'model-invocation')
        if name=='oversized_profile':(root/'reports/helper-profile-068.sha256').write_bytes(b'x'*67)
        elif name=='changed_source':(root/f.sources[1]).write_bytes(b'altered')
        elif name=='stale_authority':
            f.auth['policy_sha256']='0'*64
            from forex_demo_lab.sharing_adapter_076 import encoded076
            raw=encoded076(f.auth);f.put('reports/native-timing-081-authorization.json',raw)
            f.put('reports/native-timing-081-authorization.sha256',hashlib.sha256(raw).hexdigest().encode()+b'\r\n')
        records=[]
        for label,n in (('ledger','reports/native-timing-081-ledger.json'),('checks','reports/native-timing-081-checks.json'),
            ('final','reports/native-timing-081-final-source.json'),('review','reports/native-timing-081-completion-review.json'),
            ('helper_profile','reports/helper-profile-068.json'),('authorization','reports/native-timing-081-authorization.json')):
            records.append(dict(label=label,content_bytes=(root/n).stat().st_size,
                sidecar_bytes=(root/n).with_suffix('.sha256').stat().st_size))
        mapping={str(WINDOWS_ROOT080/p.relative_to(root).as_posix()):p for p in root.rglob('*') if p.is_file()}
        model=model_paths080(mapping,root);trace=PublicTrace081(reader_module.PublicInputs080(lambda:DATE_CLOCK080))
        trace.step('platform','validate');trace.step('invocation','reserve');dispatch=None
        try:
            with (patch.object(entry,'ROOT',WINDOWS_ROOT080),patch.object(entry,'Path',PureWindowsPath),
                patch.object(trace_module,'Path',PureWindowsPath),patch.object(reader_module,'Path',model)):
                inputs=entry.prepare081(trace,str(WINDOWS_ROOT080/'launcher'))
            trace.step('dispatch','reserve');dispatch=reserve_dispatch081(root/'model-dispatch',inputs['auth'],inputs['auth_sha'])
            trace.dispatch_reserved=True;trace.public.check();result=trace.outcome(True)
        except (Exception,KeyboardInterrupt) as e:result=trace.outcome(False,e)
        return dict(result=result,dependencies_injected=True,windows_metadata_measured=False,
            original_record_byte_counts=records,source_byte_counts=[(root/n).stat().st_size for n in sorted(f.sources)],
            launcher_bytes=(root/'launcher').stat().st_size,raw_invocation_sha256=hashlib.sha256(inv).hexdigest(),
            expected_invocation_sha256=hashlib.sha256(invocation_bytes081()).hexdigest(),
            raw_dispatch_sha256=sha(root/'model-dispatch') if dispatch else None)


def evidence():
    l=verify()
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(ledger_sha256=sha(LEDGER),
        entry_cases={n:entry_case(n) for n in CASES},public_cases={n:public_case(n) for n in PUBLIC_CASES},
        retained_build=l['retained_build'],derivation=derivation(),dependencies_injected=True,**ZERO,**FALSE))
    print(json.dumps(dict(entry_cases=6,public_cases=4,native_invocations=0)))


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and e['retained_build']==l['retained_build']
    references=dict(success=(126,8,89,1,None),real=(28,1,3,1,'profile_samples'),
        sdk_changed=(2,0,0,0,'preflight'),initialize_failed=(24,0,0,1,'sdk_attach'),
        signature_failed=(12,0,0,0,'signature'),initialize_interrupted=(24,0,0,1,'sdk_attach'))
    assert set(e['entry_cases'])==set(references) and set(e['public_cases'])==set(PUBLIC_CASES)
    for n,(hashes,guards,queries,sdk,stage) in references.items():
        row=e['entry_cases'][n];r=row['result'];c=r['counts']
        assert (c['hash_reads'],c['guards'],c['sdk_queries'],c['sdk_connections'],r['stopped_stage'])==(hashes,guards,queries,sdk,stage)
        assert c['sdk_shutdowns']==sdk and r['entry_completed']==(n=='success')
        assert r['phase']=='81000000000000000000000000000001' and row['dependencies_injected']
        assert not r['cleanup']['errors'] and row['owned_backend_closes']==1
        assert r['observation']['samples_completed']==4 if n=='success' else not r['entry_completed']
        if n=='success':
            assert len(r['observation']['samples'])==4
            assert all(x['hash_reads']==25 and x['sdk_queries']==22 and x['core_guard_ms']==[0,0] for x in r['observation']['samples'])
    public_expected=dict(windows_crlf=(True,None,None,None,12,3,120,30),
        oversized_profile=(False,'helper_profile','sidecar_bytes','file_rejected',10,0,97,0),
        changed_source=(False,'source','source_digest','binding_rejected',12,2,120,21),
        stale_authority=(False,'authorization','validate','authorization_rejected',12,0,120,0))
    for n,(complete,stage,operation,reason,reads,source_reads,stats,source_stats) in public_expected.items():
        row=e['public_cases'][n];r=row['result'];rec=row['original_record_byte_counts']
        assert (r['completed'],r['stopped_stage'],r['stopped_operation'],r['stop_reason'])==(complete,stage,operation,reason)
        assert (r['public_record_reads'],r['public_source_reads'],r['public_record_stats'],r['public_source_stats'])==(reads,source_reads,stats,source_stats)
        expected_bytes=sum(x['content_bytes']+x['sidecar_bytes'] for x in rec)
        if n=='oversized_profile':expected_bytes=sum(x['content_bytes']+x['sidecar_bytes'] for x in rec[:4])+rec[4]['content_bytes']
        assert r['public_record_bytes']==expected_bytes
        expected_source_bytes=sum(row['source_byte_counts'][:source_reads])
        if source_reads==3:expected_source_bytes+=row['launcher_bytes']
        assert r['public_source_bytes']==expected_source_bytes
        assert row['raw_invocation_sha256']==row['expected_invocation_sha256'] and row['dependencies_injected']
        assert not row['windows_metadata_measured'] and r['sdk_connections']==r['sdk_queries']==0
        assert r['dispatch_reserved']==complete and bool(row['raw_dispatch_sha256'])==complete
        assert r['steps']<=128 and reads<=16 and stats<=128 and source_reads<=64 and source_stats<=1024
        assert not r['account_type_verified'] and not r['owned_cleanup_applicable'] and not r['orders_available']
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    for row in (t,e):
        for k,v in {**ZERO,**FALSE}.items():assert type(row[k]) is type(v) and row[k]==v
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,new_tests=NEW,entry_cases_verified=6,public_cases_verified=4,
        modeled_entry_completions=1,modeled_public_completions=1,derivation=derivation(),
        runtime_sources_verified=len(l['runtime_sources']),**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,entry_cases=6,public_cases=4,native_invocations=0)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    result=ROOT/'docs/NATIVE-TIMING-081-RESULTS.md'
    text=(f'# Fresh metadata entry081 preparation results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'The fresh phase81/dateOct8 entry integrates080 exact LF/CRLF checksum handling, including canonical authority sidecars. '
        'All public/native caps and file/account/private-identity guards retained. An exclusive invocation is spent before '
        'public reads; fixed stage/operation/index/reason reports retain early failure without private paths/identity/raw exceptions. '
        'Fresh exact authority binds public limits and invocation contract; old078 authority is rejected.\n\n'
        'Six injected core cases:1 completion/5 rejections; four full public Windows/UNC models:1 completion/3 rejections '
        '(profile sidecar size, changed source, stale authority). Independent counts/bytes/stat arithmetic/raw-marker digests '
        'and once-owned cleanup checked. Core AST derivation preserves078 flow with declared fresh names/phase/authority fields; '
        'three native helpers unchanged.31 frozen source dependencies.077 component stays no-authority with fresh081 '
        'preparation/policy bindings and new marker path; four samples/eight actual guards remain.\n\n'
        'Zero new native/helper/SDK/MT5/compiler/deploy/terminal-log/market/orders/receipts/grants. No native invocation/dispatch/'
        'reservation/public/runtime created during preparation. Models do not establish actual Windows metadata, current '
        'sys.executable/account or native timing. Native calls cannot be preempted by clocks; maxima would be observations '
        'only. Original profile checksum/078 retired grant/079 unknown first failure/080 correction/075 actual-exit1 artifact '
        'and old raw markers unchanged. Sharing/publication/ACK/profit and070 cause remain unproven; eligibility/orders false.\n\n'
        'Next NATIVE-TIMING-082-PLAN.md reviews closure/current pins then separately authorizes/invokes at most one exact '
        'metadata-only entry if still UTC Oct8. Unexecuted; no UI/script/log-saving step. If date/pins changed, fresh sampler/'
        'date/phase/contract is required, not a frozen-source edit or078 retry. Preserve07610s/30s/250ms and033/035/data/clock/'
        'cost/coverage/flags/consumed2025/reserved Nov–Dec2026/provider stops.\n')
    with result.open('x') as f:f.write(text)
    latest=(f'Latest — 2026-10-08: fresh metadata entry081 sealed; read NATIVE-TIMING-081-RESULTS.md. {EXPECTED} tests/{NEW} new '
        'pass;6 core models:1 completion/5 rejections;4 public models:1 completion/3 rejections. Exact LF/CRLF cap66 including '
        'authority, fixed early public substeps/redaction, pre-read one-use invocation, fresh phase81/authority/dispatch and '
        '077 component with new bindings prepared.31 frozen imports; core AST/3 unchanged helpers checked. Four samples/eight '
        'guards/native caps/actual account/private identity/once cleanup retained. Zero new native/helper/SDK/MT5/compiler/deploy/'
        'log/market/orders/grants; no native artifacts created. Windows metadata/sys.executable/account/native timing still '
        'unmeasured; sharing/publication/ACK/profit/070 cause unproven. Old sidecar/source/078 retired grant/079 first-failure '
        'unknown/075 exit1 artifact/raw markers retained. Next082 one exact read-only metadata observation if Oct8/current pins '
        'fit, separate authority required; unexecuted/no UI. Expiry requires fresh sampler/date/phase; no078 retry/reuse. All '
        'timing/data/reserved gates preserved; eligibility/orders false. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();i=s.index('\n')+1;path.write_text(s[:i]+'\n'+latest+s[i:]);b[n]=sha(path)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),tests_passed=EXPECTED,
        new_tests=NEW,entry_cases_verified=6,public_cases_verified=4,runtime_sources_verified=len(l['runtime_sources']),
        future_plan_executed=False,retained_build_validated=True,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert r['tests_passed']==EXPECTED and not r['future_plan_executed'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,entry_cases_verified=6,
        public_cases_verified=4,runtime_sources_verified=len(l['runtime_sources']),next_plan_sha256=sha(PLAN),
        next_plan_executed=False,retained_build_validated=True,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,tests_passed=EXPECTED,bindings=len(b),members=members)))


def authorize():
    # Later082 only: not part of this081 preparation sequence.
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final)
    review=sealed(ROOT/f'reports/{PREFIX}-completion-review.json')
    assert review['review_passed'] and review['final_source_sha256']==sha(final) and review['frozen_input_coverage_complete']
    assert review['tests_passed']==EXPECTED and not review['next_plan_executed']
    assert datetime.now(timezone.utc).date().isoformat()==l['declared_date']
    assert not any((ROOT/f'reports/{PREFIX}-{n}').exists() for n in FUTURE_NAMES)
    for n,h in r['source_and_evidence_bindings'].items():assert sha(bound(n))==h,n
    assert ARCHIVE(final,r)==review['archive_members_verified']
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.native_timing_081 import validate_authorization081
    from forex_demo_lab.sharing_adapter_076 import encoded076
    spec,value=spec_and_auth(l,sha(final));raw=encoded076(value);digest=hashlib.sha256(raw).hexdigest()
    validate_authorization081(raw,value,digest);path=ROOT/f'reports/{PREFIX}-authorization.json'
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    with path.with_suffix('.sha256').open('xb') as f:f.write((digest+'\n').encode('ascii'));f.flush();os.fsync(f.fileno())
    print(json.dumps(dict(authorized=True,maximum_native_entry_invocations=1,maximum_sdk_connections=1,orders_available=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review','authorize'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,evidence=evidence,
        check=check,seal=seal,review=review,authorize=authorize)[p.parse_args().action]()
