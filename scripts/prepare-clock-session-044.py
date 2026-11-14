"""Derive a separately versioned runtime/checker/sealer; preserve043 exactly."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
worker=(ROOT/'scripts/clock-runtime-043.py').read_text().replace('scripts/clock-session-043.py','scripts/clock-session-044.py')
worker=worker.replace('reports/clock-observer-043-','reports/clock-observer-044-')
worker=worker.replace('from forex_demo_lab.clock_session_043 import require_interactive,reuse_path',
    'from forex_demo_lab.clock_session_044 import require_interactive,reuse_path,RuntimeSequence044 as RuntimeSequence')
worker=worker.replace('date_guard,runtime_guard,RuntimeSequence,records_from_log','date_guard,runtime_guard,records_from_log')
worker=worker.replace('guard_checks=0;offset=None;log=None;receipts=[]','guard_checks=0;offset=None;log=None;receipts=[];terminal_build=None')
worker=worker.replace('data_root=info.data_path;log=', "terminal_build=info.build\n        if type(terminal_build) is not int:raise ValueError('terminal_build_invalid')\n        data_root=info.data_path;log=")
worker=worker.replace('native_connections_attempted=connection_calls,sdk_quote_reads=0,','native_connections_attempted=connection_calls,running_terminal_build=terminal_build,sdk_quote_reads=0,')
checker=(ROOT/'scripts/check-clock-runtime-043.py').read_text().replace('scripts/clock-session-043.py','scripts/clock-session-044.py').replace('reports/clock-observer-043-','reports/clock-observer-044-')
runner=(ROOT/'scripts/test-clock-session-043.py').read_text().replace('scripts/clock-session-043.py','scripts/clock-session-044.py').replace('reports/clock-session-043-regression.json','reports/clock-session-044-regression.json').replace('new_tests=8','new_tests=10')
finalizer=(ROOT/'scripts/finalize-clock-session-043.py').read_text().replace('scripts/clock-session-043.py','scripts/clock-session-044.py')
finalizer=finalizer.replace('clock-session-043','clock-session-044').replace('clock-observer-043','clock-observer-044')
finalizer=finalizer.replace('CLOCK-SESSION-043-RESULTS.md','CLOCK-DEPENDENCY-044-RESULTS.md')
finalizer=finalizer.replace('==612','==622').replace('612 tests (8 new)','622 tests (10 new)').replace('software_tests_passed=612,new_tests=8','software_tests_passed=622,new_tests=10')
finalizer=finalizer.replace('clock session043 sealed','clock session044 sealed').replace('all_043_critical_sources_frozen_before_runtime','all_044_critical_sources_frozen_before_runtime')
finalizer=finalizer.replace("'scripts/*043*','tests/*043*.py','docs/*043*.md',next_plan,'src/forex_demo_lab/*043.py'", "'scripts/*044*','tests/*044*.py','docs/*044*.md',next_plan,'src/forex_demo_lab/*044.py'")
finalizer=finalizer.replace('clock_session_043_input_bindings','clock_session_044_input_bindings')
needle="    for n in API['HANDOFF']:groups['source_bindings'][n]=sha(ROOT/n)"
rebind="""    from forex_demo_lab.clock_session_044 import ROLLOVER
    for values in groups.values():
        for n,(before,after) in ROLLOVER.items():
            if n in values:assert values[n]==before;values[n]=after
"""
finalizer=finalizer.replace(needle,rebind+needle)
for name,text in {'scripts/clock-runtime-044.py':worker,'scripts/check-clock-runtime-044.py':checker,
    'scripts/test-clock-session-044.py':runner,'scripts/finalize-clock-session-044.py':finalizer}.items():
    with (ROOT/name).open('x',encoding='utf-8') as out:out.write(text)
print('New044 sources created; original043 unchanged, no compiler/deployment action')
