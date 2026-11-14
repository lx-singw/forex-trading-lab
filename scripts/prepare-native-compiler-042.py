"""Create new compiler scaffolding from041; fix its pre-run filename coverage."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'scripts/native-compiler-041.py').read_text()
text=text.replace('native_compiler_041','native_compiler_042').replace('native-compiler-041','native-compiler-042').replace('compiler041-','compiler042-')
text=text.replace("OLD=runpy.run_path(str(ROOT/'scripts/native-compiler-040.py'))","OLD=runpy.run_path(str(ROOT/'scripts/native-compiler-041.py'))")
text=text.replace("PRIOR=ROOT/'reports/native-compiler-040-final-source.json'","PRIOR=ROOT/'reports/native-compiler-041-final-source.json'")
text=text.replace('32fd7ad55f19df68ecc1244d1d4f949a57a9fb307d4390b60dcdfb27ac89f5f5','6e2d5f7cea92d989a3fb211051e1300a55dabbf55f0a4fe26dbbad65c9dba16a')
text=text.replace('1218','1251').replace('1162','1189').replace('==56','==62').replace('external_bindings_verified=56','external_bindings_verified=62')
text=text.replace("assert prior['observer_compiled'] is prior['observer_runtime_executed'] is prior['orders_available'] is False",
    "assert prior['observer_compiled'] is True and prior['observer_runtime_executed'] is prior['orders_available'] is False")
text=text.replace('==584','==604').replace("new_tests']==6","new_tests']==20")
text=text.replace("'scripts/*040*','tests/*040*.py','docs/*040*.md'","'scripts/*042*','tests/*042*.py','docs/*042*.md'")
text=text.replace("'reports/native-compiler-040-*','scripts/finalize-native-build.py',MQL,GUARD,'mt5/Tests/ClockGuard038.cpp'",
    "'reports/native-compiler-041-*','scripts/finalize-clock-observer-042.py',MQL,GUARD,'mt5/Tests/ClockGuard042.cpp'")
text=text.replace("ROOT/'scripts/argument-echo-040.py'","ROOT/'scripts/argument-echo-042.py'")
text=text.replace('ForexDemoClockObserver038.ex5','ForexDemoClockObserver042.ex5')
marker="    for stem in ('ledger','reservation','started','build','fixture','checks','review','final-source'):"
extra="""    required={'scripts/native-compiler-042.py','scripts/check-native-compiler-042.py','scripts/clock-runtime-042.py',
        'scripts/check-clock-runtime-042.py','scripts/finalize-clock-observer-042.py','tests/test_clock_observer_042.py',
        'docs/CLOCK-OBSERVER-042-PLAN.md','docs/CLOCK-OBSERVER-042-PROTOCOL.md',MQL,GUARD,'mt5/Tests/ClockGuard042.cpp'}
    assert required<=set(bindings)
    sdk=sealed(ROOT/'reports/fresh-replication-035-ledger.json')
    for n,h in sdk['bindings'].items():
        if '/MetaTrader5/' in n:assert sha(bound_path(n))==h;bindings[n]=h
    terminal=external_name(sdk['terminal']);bindings[terminal]=sha(bound_path(terminal))
"""
text=text.replace(marker,extra+marker)
module=(ROOT/'src/forex_demo_lab/native_compiler_041.py').read_text().replace('038','042').replace('039','039').replace('041','042')
checker=(ROOT/'scripts/check-native-compiler-041.py').read_text().replace('native-compiler-041','native-compiler-042').replace('ArgumentEcho041','ArgumentEcho042').replace('compiler041-','compiler042-')
checker=checker.replace('ForexDemoClockObserver038','ForexDemoClockObserver042').replace('ClockGuard038.mqh','ClockGuard042.mqh')
checker=checker.replace('==584','==604').replace('==6','==20').replace('software_tests_passed=584,new_tests=6','software_tests_passed=604,new_tests=20')
runner=(ROOT/'scripts/test-native-compiler-041.py').read_text().replace('native-compiler-041','native-compiler-042').replace('new_tests=6','new_tests=20')
echo=(ROOT/'scripts/argument-echo-041.py').read_text()
for name,body in {'scripts/native-compiler-042.py':text,'src/forex_demo_lab/native_compiler_042.py':module,
    'scripts/check-native-compiler-042.py':checker,'scripts/test-native-compiler-042.py':runner,'scripts/argument-echo-042.py':echo}.items():
    with (ROOT/name).open('x',encoding='utf-8') as out:out.write(body)
print('New042 compiler scaffolding created, with required pre-run source coverage')
