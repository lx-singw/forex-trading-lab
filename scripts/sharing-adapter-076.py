"""Offline build/adapter/timing preparation; no native dispatch action."""
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
API=runpy.run_path(str(ROOT/'scripts/sharing-build-075.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='sharing-adapter-076';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/sharing-build-075-final-source.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-SHARING-076-PLAN.md'
DESIGN=ROOT/'docs/SHARING-ADAPTER-076-DESIGN.md';PLAN=ROOT/'docs/NATIVE-SHARING-077-PLAN.md'
EXPECTED,NEW=1408,48
PATTERNS=('scripts/*076.py','src/forex_demo_lab/*076.py','tests/*076.py','docs/*076*.md','docs/*077*.md')
ZERO=dict(sdk_connections=0,mt5_runtime_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    native_metatrader_compiler_invocations=0,native_self_profiles=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,native_mql_verified=False,
    native_publication_verified=False,actual_mt5_repair_verified=False,root_cause_proven=False,
    native_adapter_ready=False,native_timing_verified=False,runtime_authorized=False)
CASES=dict(fast_conservative=[100,1000,100,1,500,15000],one_second_guards=[1000,1000,100,1,500,15000],
    late_start=[0,4750,0,0,0,15000],slow_launch=[6000,0,0,0,0,15000],
    hold_deadline=[1500,0,750,0,0,0],hold_inside=[1500,0,749,0,0,0],
    launch_deadline=[1,0,9998,0,0,0],launch_and_full_wait=[1,0,9998,0,0,15000])


def compiled_evidence():
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.sharing_adapter_076 import validate_build076
    from forex_demo_lab.sharing_integration_072 import SOURCE_INPUTS,source_contract072
    native=sealed(ROOT/'reports/sharing-build-075-native.json')
    settings=sealed(ROOT/'reports/sharing-build-075-ledger.json')
    assert native['completed'] and native['compiled'] and native['compiler_process_completed']
    assert native['counts']['compiler_invocations']==1 and native['compiler_exit_code']==1
    assert len(native['stage_trace'])==8 and all(s['completed'] for s in native['stage_trace'])
    assert native['owned_compiler_absent_after'] and not native['execution_policy_changed']
    metadata=dict(policy='Restricted',editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
    assert native['metadata_before']==native['metadata_after']==metadata
    for k in ('sdk_connections','mt5_runtime_invocations','terminal_deployments','terminal_log_content_reads',
              'market_reads','orders','receipt_permissions'):assert native[k]==0
    names={n.rsplit('/',1)[-1]:n for n in native['output_bindings']}
    assert set(names)=={Path(n).name for n in SOURCE_INPUTS}|{'compile.log','ForexDemoSharing072.ex5'}
    for n,h in native['output_bindings'].items():assert sha(bound(n))==h,n
    contract=source_contract072({n:sha(ROOT/n) for n in SOURCE_INPUTS})
    for n,h in contract['input_bindings'].items():assert native['output_bindings'][names[Path(n).name]]==h
    artifact=bound(names['ForexDemoSharing072.ex5']);log=bound(names['compile.log']).read_text(encoding='utf-16')
    value=dict(sha256=sha(artifact),size=artifact.stat().st_size,raw=None)
    build=validate_build076(native['build_record'],contract,log,value,settings['editor_sha256'],settings['terminal_sha256'])
    return build,dict(retained_compiled=True,source_phase=build.record()['phase'],source_date=build.record()['date'],
        source_contract=contract,retained_build_phase=build.record()['build_phase'],build_record_sha256=build.sha256,
        artifact_sha256=value['sha256'],artifact_bytes=value['size'],actual_compiler_exit_code=1,
        native_report_sha256=sha(ROOT/'reports/sharing-build-075-native.json'),native_runtime_authorized=False)


def freeze():
    assert sha(PRIOR)=='a528c4374c0b037b529f171cabeef72579f7807be29164747a1fc59c37d66f9a'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/sharing-build-075-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert (r['tests_passed'],r['bindings_verified'],r['archive_members_verified'])==(1360,2374,2192)
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='a82613dfa29bda78433d7a28452e3542177d134d76b8ded29b461fa66f395d6d'
    assert not r['next_plan_executed'] and r['compiled'] and r['compiler_exit_code']==1
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2192;API['verify']()
    _,build=compiled_evidence()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
        ROOT/'reports/sharing-build-075-completion-review.json',ROOT/'reports/sharing-build-075-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        design_sha256=sha(DESIGN),future_plan_sha256=sha(PLAN),retained_build=build,timing_cases=CASES,
        preparation_date=datetime.now(timezone.utc).date().isoformat(),phase='76000000000000000000000000000001',
        tests_retained=1360,expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,
        maximum_native_sessions=0,launch_gate_ms=10000,mql_hold_ms=30000,margin_ms=250,
        prior_bindings_verified=2374,prior_archive_members_verified=2192,**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['prior_source_sha256']==sha(PRIOR) and l['prior_plan_sha256']==sha(PRIOR_PLAN)
    assert l['design_sha256']==sha(DESIGN) and l['future_plan_sha256']==sha(PLAN)
    assert l['retained_build']==compiled_evidence()[1] and l['timing_cases']==CASES
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


def evidence():
    l=verify()
    from forex_demo_lab.sharing_adapter_076 import TimingBounds076
    rows={name:TimingBounds076(*values).report() for name,values in l['timing_cases'].items()}
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(ledger_sha256=sha(LEDGER),retained_build=l['retained_build'],
        cases=rows,modeled_admissions=sum(r['modeled_admission'] for r in rows.values()),
        native_timing_unknown=True,old070_root_cause_unknown=True,**ZERO,**FALSE))
    print(json.dumps(dict(cases=len(rows),modeled_admissions=sum(r['modeled_admission'] for r in rows.values()),native_timing_verified=False)))


def timeline(values):
    # Independently enumerate each before/operation/after segment. Do not call
    # TimingBounds076.report or use its aggregate16g/6n completion expression.
    g,u,c,n,o,w=values
    ready=g;latest_start=ready+u+o;received=ready+u+c+o;gate=received+g
    t=gate+g; t+=5000+w; t+=g
    guards=4;operations=0;probes=[]
    for access in ('write','delete'):
        for operation in ('metadata_before','open','metadata_after'):
            t+=g;guards+=1;start=t;t+=n;operations+=1
            if operation=='open':probes.append(dict(access=access,start_upper_ms=start,end_upper_ms=t))
            t+=g;guards+=1
    return dict(launch_gate_upper_ms=gate,latest_mql_start_ms=latest_start,
        independent_start_lower_ms=5000,independent_completion_upper_ms=t,
        launch_gate_fits=gate<=10000,start_margin_fits=latest_start+250<5000,end_margin_fits=t<29750,
        guards=guards,operations=operations,probe_upper_windows=probes)


def check():
    l=verify();t=sealed(ROOT/f'reports/{PREFIX}-tests.json');e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER)
    assert e['retained_build']==compiled_evidence()[1] and set(e['cases'])==set(CASES)
    timelines={}
    for name,values in CASES.items():
        r=e['cases'][name];independent=timeline(values);timelines[name]=independent
        assert independent['guards']==16 and independent['operations']==6
        for k in ('launch_gate_upper_ms','latest_mql_start_ms','independent_start_lower_ms',
                  'independent_completion_upper_ms','launch_gate_fits','start_margin_fits','end_margin_fits'):
            assert type(r[k]) is type(independent[k]) and r[k]==independent[k],(name,k)
        admitted=all(independent[k] for k in ('launch_gate_fits','start_margin_fits','end_margin_fits'))
        assert type(r['modeled_admission']) is bool and r['modeled_admission']==admitted
        assert r['assumed_bounds_only'] and r['requires_native_timing_evidence']
        assert not r['runtime_authorized'] and not r['native_mql_verified'] and not r['orders_available']
    assert e['modeled_admissions']==3 and e['native_timing_unknown'] and e['old070_root_cause_unknown']
    for data in (t,e,l):
        for k,v in {**ZERO,**FALSE}.items():assert type(data[k]) is type(v) and data[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h==l['bindings'][n]
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    for name in ('native-sharing-076-runtime.json','native-sharing-076-authorization.json',
                 'native-sharing-076-dispatch-started.json','native-sharing-072-runtime-reservation.json'):
        assert not (ROOT/'reports'/name).exists()
    assert not list(ROOT.glob('mt5/**/ForexDemoSharing072.ex5'))
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        tests_passed=EXPECTED,retained_build_validated=True,independent_timelines=timelines,
        timing_cases_verified=8,modeled_admissions=3,modeled_rejections=5,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,timing_cases_verified=8)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    text=(f'# Adapter076 and timing results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'The exact075 actual-exit1/clean-log/15554-byte compiled072 artifact is validated without modifying the old072 exit0 checker. '
        'Immutable build, raw reservation/dispatch bindings, exclusive once-only claim, actual072 graph, source-bound deployment and '
        'once-owned cleanup are prepared and tested with temporary injected peers.\n\n'
        'Eight fixed timing cases independently checked:3 modeled admissions/5 rejections under declared assumptions. '
        'The actual injected graph verifies16 full guards and six operations in the critical window. Launch can fit10s while '
        'checks miss the unchanged30s hold: one-second guards plus the existing15s wait overshoot produce37606ms in the declared case. '
        'Bounds include UI/command delay, aggregate overhead and whole logical operation costs. Strict250ms margins and '
        '10s/30s runtime/matcher gates remain. Observed guards/waits above assumptions invalidate results without allowance refund.\n\n'
        'Native timing/readiness, MQL sharing/publication/ACK and profitability remain unproven. Old070 exact cause is unknown; '
        'its elapsed totals do not establish an individual guard bound. Modeled admission grants no runtime permission. '
        'Zero new SDK/MT5/compiler/deployment/terminal-log content/self-profile/market/orders/receipt grants.\n\n'
        'Next NATIVE-SHARING-077-PLAN.md declares tested finite timing-profile preparation and source-bound synchronization before '
        'any later native policy. Unexecuted. If Oct8 expired, fresh source/date/phase/matcher/build required; all frozen inputs and '
        'old failures/spent raw reservations preserved.033/035, clock/cost/coverage/flags, consumed2025/reserved Nov-Dec2026 '
        'and provider stops retained; eligibility/orders false.\n')
    with (ROOT/'docs/SHARING-ADAPTER-076-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-08: offline adapter076 sealed; read SHARING-ADAPTER-076-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass; retained075 actual-exit1/clean072 artifact validated. Immutable build, exact raw '
        'dispatch/reservation, once-only claim/cleanup, actual072 graph and owned076 deployment prepared with injected peers. '
        'Eight independent timing cases:3 modeled admissions/5 rejections;16 guards/six operations verified. One-second guard '
        'case fits10s launch but reaches37606ms with existing wait overshoot, exceeding30s hold. Native bounds/readiness unknown; '
        'no assumed admission authorizes native work. Zero new SDK/MT5/compiler/deploy/terminal-log/profile/market/orders/grants. '
        'MQL sharing/publication/ACK/profit and070 cause unproven. Next077 finite timing-profile/synchronization preparation '
        'unexecuted; Oct8 expiry needs fresh source/date/phase. All old frozen failures/spent/reserved gates retained. Earlier entries historical.\n\n')
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
        new_tests=NEW,retained_build_validated=True,timing_cases_verified=8,modeled_admissions=3,
        modeled_rejections=5,future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN) and not r['future_plan_executed']
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,retained_build_validated=True,
        timing_cases_verified=8,modeled_admissions=3,modeled_rejections=5,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,tests_passed=EXPECTED)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','evidence','check','seal','review','verify'))
    dict(freeze=freeze,test=test,evidence=evidence,check=check,seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
