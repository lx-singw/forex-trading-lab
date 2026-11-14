"""Independent original-file, argv, compiler evidence and unchanged-gate checks."""
import json
from pathlib import Path,PureWindowsPath
import re
import runpy
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-compiler-042.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']

def check():
    ledger=API['verify']();build=sealed(API['OUTPUT']);tests=sealed(ROOT/'reports/native-compiler-042-regression.json')
    assert sealed(API['STARTED'])==dict(ledger_sha256=sha(API['LEDGER']),reservation_sha256=sha(API['RESERVATION']),
        reservation_consumed=True,maximum_fixture_invocations=1,maximum_compiler_invocations=1)
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==604 and tests['new_tests']==20
    assert build['ledger_sha256']==sha(API['LEDGER']) and build['reservation_sha256']==sha(API['RESERVATION'])
    assert set(build)=={'version','ledger_sha256','reservation_sha256','metadata_before','metadata_after',
        'observed_policy_unchanged','stop_reason','fixture_invocations','fixture_passed','fixture_exit_code',
        'compiler_invocations','compiler_started','compiler_completed','compiler_exit_code','owned_timeout_cleanup',
        'errors','warnings','compiled','ex5_bytes','fixture_output_bindings','compile_output_bindings',
        'powershell_script_executions','execution_policy_changed','global_environment_changed','observer_attached',
        'observer_runtime_executed','market_requests','native_connections','external_requests','historical_downloads',
        'strategy_replays','orders_available','fresh_performance_eligible','annual_eligible'}
    for key in ('fixture_invocations','compiler_invocations'):
        assert type(build[key]) is int and 0<=build[key]<=1
    for key in ('compiler_exit_code','fixture_exit_code','errors','warnings'):
        assert build[key] is None or type(build[key]) is int
    assert type(build['ex5_bytes']) is int and build['ex5_bytes']>=0
    for key in ('fixture_passed','compiler_started','compiler_completed','owned_timeout_cleanup','compiled','observed_policy_unchanged'):
        assert type(build[key]) is bool
    for key in ('execution_policy_changed','global_environment_changed','observer_attached','observer_runtime_executed',
                'orders_available','fresh_performance_eligible','annual_eligible'):
        assert build[key] is False
    for key in ('powershell_script_executions','market_requests','native_connections','external_requests','historical_downloads','strategy_replays'):
        assert build[key]==0
    for key in ('metadata_before','metadata_after'):
        value=build[key]
        if value is None:continue
        assert set(value)=={'effective_policy','security_module_version','local_app_data','editor_processes'}
        assert value['effective_policy']=='Restricted' and value['security_module_version']=='3.0.0.0'
        assert PureWindowsPath(value['local_app_data'])/'ForexDemoLab'/'builds'==PureWindowsPath(ledger['build_root'])
        assert type(value['editor_processes']) is int and value['editor_processes']>=0
    before,after=build['metadata_before'],build['metadata_after']
    assert build['observed_policy_unchanged']==(before is not None and after is not None and before['effective_policy']==after['effective_policy'])
    files={};parents={};root=PureWindowsPath(ledger['build_root'])
    for kind,key in (('fixture','fixture_output_bindings'),('compile','compile_output_bindings')):
        names={};dirs=set()
        for n,h in build[key].items():
            assert sha(API['bound_path'](n))==h,n
            tail=n.split('/ForexDemoLab/builds/',1);assert len(tail)==2
            directory,filename=tail[1].split('/');dirs.add(directory)
            assert re.fullmatch('compiler042-'+('fixture-' if kind=='fixture' else '')+'[0-9a-f]{32}',directory)
            assert API['external_name'](str(root/directory/filename))==n
            names[filename]=n
        assert len(dirs)<=1
        allowed={'ArgumentEcho042.py'} if kind=='fixture' else {'ForexDemoClockObserver042.mq5','ClockGuard042.mqh','compile.log','ForexDemoClockObserver042.ex5'}
        assert set(names)<=allowed;files[kind]=names;parents[kind]=next(iter(dirs),None)
    if parents['compile'] is not None:assert parents['compile']!=parents['fixture']
    fixture=files['fixture'];outputs=files['compile'];witness=None
    if 'ArgumentEcho042.py' in fixture:
        assert build['fixture_output_bindings'][fixture['ArgumentEcho042.py']]==sha(ROOT/'scripts/argument-echo-040.py')
    if build['fixture_passed']:
        assert build['fixture_invocations']==1 and build['fixture_exit_code']==0 and set(fixture)=={'ArgumentEcho042.py'}
        witness=sealed(ROOT/'reports/native-compiler-042-fixture.json')
        parent=root/parents['fixture']
        expected=['/compile:'+str(parent/'source with spaces & $ ;.mq5'),'/log:'+str(parent/'log with spaces & $ ;.log')]
        assert witness==dict(argv=expected,expected=expected,fixture_passed=True,return_code=0,
            ledger_sha256=sha(API['LEDGER']),shell_used=False)
    if build['compiler_invocations']:
        assert witness is not None and before is not None and before['editor_processes']==0
        assert set(outputs)>={'ForexDemoClockObserver042.mq5','ClockGuard042.mqh'}
    for filename,source in (('ForexDemoClockObserver042.mq5',API['MQL']),('ClockGuard042.mqh',API['GUARD'])):
        if filename in outputs:assert build['compile_output_bindings'][outputs[filename]]==sha(ROOT/source)
    counts=None;ex5_bytes=0
    if 'compile.log' in outputs:
        log=API['bound_path'](outputs['compile.log']).read_text(encoding='utf-16')
        matches=re.findall(r'(\d+) errors, (\d+) warnings',log)
        if matches:counts=tuple(map(int,matches[-1]))
    if 'ForexDemoClockObserver042.ex5' in outputs:ex5_bytes=API['bound_path'](outputs['ForexDemoClockObserver042.ex5']).stat().st_size
    if build['compiler_completed']:
        assert build['compiler_started'] and build['compiler_invocations']==1 and not build['owned_timeout_cleanup']
        assert build['compiler_exit_code'] is not None
        assert (build['errors'],build['warnings'])==((None,None) if counts is None else counts)
        assert build['ex5_bytes']==ex5_bytes
    compiled=build['compiler_completed'] and counts==(0,0) and ex5_bytes>0
    assert build['compiled']==compiled
    if compiled:
        assert build['stop_reason'] is None and build['observed_policy_unchanged'] and after['editor_processes']==0
        assert set(outputs)=={'ForexDemoClockObserver042.mq5','ClockGuard042.mqh','compile.log','ForexDemoClockObserver042.ex5'}
    assert sealed(ROOT/'reports/native-compiler-040-build.json')['stop_reason']=='staging_failed'
    old=sealed(ROOT/'reports/compiler-launch-039-build.json')
    assert old['stop_reason']=='native_metadata_failed' and old['fixture_invocations']==old['compiler_invoker_calls']==0
    assert sealed(ROOT/'reports/clock-semantics-038-compile.json')['compiled'] is False
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/n)['diagnostic_passed'] is False
    write(ROOT/'reports/native-compiler-042-checks.json',dict(checker_passed=True,ledger_sha256=sha(API['LEDGER']),
        build_sha256=sha(API['OUTPUT']),input_bindings_verified=len(ledger['bindings']),software_tests_passed=604,new_tests=20,
        fixture_invocations=build['fixture_invocations'],compiler_invocations=build['compiler_invocations'],
        observer_compiled=compiled,errors=build['errors'],warnings=build['warnings'],ex5_bytes=ex5_bytes,
        observed_policy_unchanged=build['observed_policy_unchanged'],external_output_bindings={**build['fixture_output_bindings'],**build['compile_output_bindings']},
        original_038_039_040_failures_preserved=True,observer_source_unchanged=True,powershell_script_executions=0,
        execution_policy_changed=False,observer_runtime_executed=False,market_requests=0,orders_available=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,source_clock_sessions_qualified=False,
        upstream_completeness_qualified=False,historical_executable_costs_qualified=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(checker_passed=True,observer_compiled=compiled,errors=build['errors'],warnings=build['warnings'],market_requests=0)))

if __name__=='__main__':check()
