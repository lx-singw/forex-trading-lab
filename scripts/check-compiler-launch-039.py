"""Independent seals, native path/argv, compiler log and unchanged gate checks."""
import json
from pathlib import Path,PureWindowsPath
import re
import runpy

ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/compiler-launch-039.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']


def check():
    ledger=API['verify']();build=sealed(API['OUTPUT']);tests=sealed(ROOT/'reports/compiler-launch-039-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==566 and tests['new_tests']==20
    assert build['ledger_sha256']==sha(API['LEDGER']) and build['reservation_sha256']==sha(API['RESERVATION'])
    assert set(build)=={'version','ledger_sha256','reservation_sha256','stop_reason','metadata_before','metadata_after',
        'metadata_process_before','metadata_process_after','observed_policy_unchanged','fixture_invocations','compiler_invoker_calls',
        'fixture_result','compile_result','fixture_process','compiler_process','fixture_output_bindings','compile_output_bindings',
        'observer_compiled','observer_attached','observer_runtime_executed','market_requests','native_connections',
        'external_requests','historical_downloads','strategy_replays','execution_policy_changed',
        'fresh_performance_eligible','annual_eligible','orders_available'}
    assert 0<=build['fixture_invocations']<=1 and 0<=build['compiler_invoker_calls']<=1
    for flag in ('observer_attached','observer_runtime_executed','execution_policy_changed','fresh_performance_eligible','annual_eligible','orders_available'):
        assert build[flag] is False
    for key in ('market_requests','native_connections','external_requests','historical_downloads','strategy_replays'):
        assert build[key]==0
    processes=('metadata_process_before','metadata_process_after','fixture_process','compiler_process')
    for key in processes:
        value=build[key]
        if value is None:continue
        assert set(value)=={'return_code','unauthorized_access','security_exception','access_denied','authorization_manager_failure','missing_path'}
        assert type(value['return_code']) is int and all(type(value[k]) is bool for k in value if k!='return_code')
    for key in ('metadata_before','metadata_after'):
        value=build[key]
        if value is None:continue
        assert set(value)=={'parser_errors','effective_policy','signature_status','local_app_data','editor_processes'}
        assert type(value['parser_errors']) is int and type(value['editor_processes']) is int
        assert PureWindowsPath(value['local_app_data'])/'ForexDemoLab'/'builds'==PureWindowsPath(ledger['build_root'])
    before,after=build['metadata_before'],build['metadata_after']
    assert build['observed_policy_unchanged']==(before is not None and after is not None and before['effective_policy']==after['effective_policy'])
    if build['fixture_invocations']:assert before is not None and before['parser_errors']==0 and before['editor_processes']==0
    fixture_files=build['fixture_output_bindings'];compiler_files=build['compile_output_bindings']
    root=PureWindowsPath(ledger['build_root']);stage_names=set()
    for kind,files in (('fixture',fixture_files),('compile',compiler_files)):
        names=set();parents=set()
        for name,h in files.items():
            p=API['bound_path'](name);assert sha(p)==h,name
            relative=name.split('/ForexDemoLab/builds/',1);assert len(relative)==2
            dirname,filename=relative[1].split('/');names.add(filename);parents.add(dirname)
            pattern='compiler039-'+('fixture-' if kind=='fixture' else '')+'[0-9a-f]{32}'
            assert re.fullmatch(pattern,dirname)
            assert API['external_name'](str(root/dirname/filename))==name
        assert len(parents)<=1;stage_names.update(parents)
        allowed={'ArgumentFixture039.ps1','ArgumentEcho039.py','fixture-argv.json'} if kind=='fixture' else {
            'ForexDemoClockObserver038.mq5','ClockGuard038.mqh','CompileClock039.ps1','compile.log','ForexDemoClockObserver038.ex5'}
        assert names<=allowed
    assert len(stage_names)==len({n.split('/ForexDemoLab/builds/')[1].split('/')[0] for n in (*fixture_files,*compiler_files)})
    fixtures={Path(n).name:n for n in fixture_files};outputs={Path(n).name:n for n in compiler_files}
    if 'ArgumentFixture039.ps1' in fixtures:assert fixture_files[fixtures['ArgumentFixture039.ps1']]==sha(ROOT/'scripts/argument-fixture-039.ps1')
    if 'ArgumentEcho039.py' in fixtures:assert fixture_files[fixtures['ArgumentEcho039.py']]==sha(ROOT/'scripts/argument-echo-039.py')
    witness=None
    f=build['fixture_result']
    if f is not None:
        assert set(f)=={'outcome','fixture_passed','child_exit_code','process_completed'}
        assert f['outcome'] in ('fixture_passed','fixture_failed') and type(f['fixture_passed']) is bool
        if f['fixture_passed']:
            assert f['process_completed'] is True and f['child_exit_code']==0
            assert set(fixtures)=={'ArgumentFixture039.ps1','ArgumentEcho039.py','fixture-argv.json'}
            witness=json.loads(API['bound_path'](fixtures['fixture-argv.json']).read_text(encoding='utf-8-sig'))
            parent=PureWindowsPath(str(root))/fixtures['fixture-argv.json'].split('/ForexDemoLab/builds/')[1].split('/')[0]
            assert witness==dict(arguments_equal=True,argv=['/compile:'+str(parent/'source with spaces.mq5'),'/log:'+str(parent/'log with spaces.log')])
    if build['compiler_invoker_calls']:
        assert f is not None and f['fixture_passed'] and witness is not None
        assert build['fixture_process']['return_code']==0
    for name,source in (('ForexDemoClockObserver038.mq5',API['MQL']),('ClockGuard038.mqh',API['GUARD']),('CompileClock039.ps1','scripts/compile-clock-observer-039.ps1')):
        if name in outputs:assert compiler_files[outputs[name]]==sha(ROOT/source)
    compiled=False;native_attempts=None
    c=build['compile_result']
    if c is not None:
        assert set(c)=={'outcome','compiled','native_compiler_attempts','native_compiler_started','process_completed',
            'exit_code','errors','warnings','owned_timeout_cleanup'}
        assert c['outcome'] in ('compiled','compile_failed','compiler_timeout','preflight_rejected','compiler_launch_failed')
        assert type(c['native_compiler_attempts']) is int and 0<=c['native_compiler_attempts']<=1
        native_attempts=c['native_compiler_attempts'];compiled=c['compiled']
        if compiled:
            assert c['outcome']=='compiled' and native_attempts==1 and c['native_compiler_started'] is c['process_completed'] is True
            assert c['errors']==c['warnings']==0 and build['compiler_process']['return_code']==0 and build['stop_reason'] is None
            assert set(outputs)=={'ForexDemoClockObserver038.mq5','ClockGuard038.mqh','CompileClock039.ps1','compile.log','ForexDemoClockObserver038.ex5'}
            log=API['bound_path'](outputs['compile.log']).read_text(encoding='utf-16')
            results=re.findall(r'(\d+) errors, (\d+) warnings',log);assert results and results[-1]==('0','0')
            assert API['bound_path'](outputs['ForexDemoClockObserver038.ex5']).stat().st_size>0
    assert build['observer_compiled']==compiled
    old=sealed(ROOT/'reports/clock-semantics-038-compile.json')
    assert old['compiled'] is False and old['outcome']=='compiler_driver_failure_details_redacted'
    assert old['source_sha256']==sha(ROOT/API['MQL']) and old['header_sha256']==sha(ROOT/API['GUARD'])
    for name in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/name)['diagnostic_passed'] is False
    write(ROOT/'reports/compiler-launch-039-checks.json',dict(checker_passed=True,ledger_sha256=sha(API['LEDGER']),
        build_sha256=sha(API['OUTPUT']),input_bindings_verified=len(ledger['bindings']),software_tests_passed=566,new_tests=20,
        fixture_invocations=build['fixture_invocations'],compiler_invoker_calls=build['compiler_invoker_calls'],
        native_compiler_attempts=native_attempts,fixture_argv=witness,observer_compiled=compiled,
        observed_policy_unchanged=build['observed_policy_unchanged'],external_output_bindings={**fixture_files,**compiler_files},
        original_038_failure_preserved=True,observer_source_unchanged=True,observer_attached=False,observer_runtime_executed=False,
        market_requests=0,native_connections=0,external_requests=0,historical_downloads=0,strategy_replays=0,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        source_clock_sessions_qualified=False,upstream_completeness_qualified=False,historical_executable_costs_qualified=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(checker_passed=True,observer_compiled=compiled,native_compiler_attempts=native_attempts,
                         fixture_invocations=build['fixture_invocations'],market_requests=0)))


if __name__=='__main__':check()
