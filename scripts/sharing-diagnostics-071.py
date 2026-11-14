"""Freeze/test/audit offline071 diagnosis. No native execution action."""
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
API=runpy.run_path(str(ROOT/'scripts/native-sharing-070.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='sharing-diagnostics-071';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/native-sharing-070-final-source.json'
RUNTIME=ROOT/'reports/native-sharing-069-runtime.json'
RESERVATION=ROOT/'reports/native-sharing-069-runtime-reservation.json'
DISPATCH=ROOT/'reports/native-sharing-069-dispatch-started.json'
PRIOR_PLAN=ROOT/'docs/NATIVE-SHARING-071-PLAN.md'
PLAN=ROOT/'docs/NATIVE-SHARING-072-PLAN.md'
EXPECTED,NEW=1241,32
PATTERNS=('scripts/*071.py','src/forex_demo_lab/*071.py','tests/*071.py','docs/*071*.md','docs/*072*.md')
ZERO=dict(sdk_connections=0,mt5_invocations=0,terminal_deployments=0,terminal_log_content_reads=0,
    native_metatrader_compiler_invocations=0,native_self_profiles=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
    native_mql_verified=False,native_publication_verified=False,actual_mt5_repair_verified=False,
    native_adapter_ready=False,root_cause_proven=False,native_experiment_repeated=False)


def prior_evidence():
    c=sealed(ROOT/'reports/native-sharing-070-checks.json');r=sealed(RUNTIME)
    assert c['audit_passed'] and c['owned_cleanup_confirmed'] and c['counts_within_declared_caps']
    for key,path in (('runtime_sha256',RUNTIME),('dispatch_sha256',DISPATCH),
                     ('reservation_sha256',RESERVATION),('authorization_sha256',API['AUTH'])):
        assert c[key]==sha(path)
    assert not RESERVATION.with_suffix('.sha256').exists()
    assert not (ROOT/'reports/native-sharing-066-runtime-reservation.sha256').exists()
    assert r['cleanup_errors']==[] and r['script_arms']==['disabled','enabled']
    sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.sharing_diagnostics_071 import inspect_prior071
    return inspect_prior071(r)


def freeze():
    assert sha(PRIOR)=='702ce7b47de61d37898959390ba0d39814d564793e9342fe87569ebcad5e1421'
    p=sealed(PRIOR);r=sealed(ROOT/'reports/native-sharing-070-completion-review.json')
    assert r['review_passed'] and r['frozen_input_coverage_complete'] and r['final_source_sha256']==sha(PRIOR)
    assert r['tests_passed']==1209 and r['bindings_verified']==2221 and r['archive_members_verified']==2055
    assert r['runtime_completed'] is False and r['stopped_stage']=='independent_controls'
    assert r['next_plan_sha256']==sha(PRIOR_PLAN)=='2be28f50ba1aede79f9eb4b16f415af6d78e7b1511755f600cf1c1523732ee42'
    assert r['next_plan_executed'] is False
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    assert ARCHIVE(PRIOR,p)==2055;API['verify']();observation=prior_evidence()
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),
            ROOT/'reports/native-sharing-070-completion-review.json',ROOT/'reports/native-sharing-070-completion-review.sha256'):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={}
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):n=path.relative_to(ROOT).as_posix();b[n]=selected[n]=sha(path)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),prior_plan_sha256=sha(PRIOR_PLAN),
        prior_bindings_verified=2221,prior_archive_members_verified=2055,tests_retained=1209,
        expected_tests=EXPECTED,new_tests=NEW,maximum_full_regressions=1,maximum_native_sessions=0,
        diagnostic_phase='71000000000000000000000000000001',maximum_diagnostic_events=192,
        maximum_launch_delay_ms=10000,future_plan_sha256=sha(PLAN),**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    write(ROOT/f'reports/{PREFIX}-observations.json',dict(**observation,ledger_sha256=sha(LEDGER),
        prior_runtime_sha256=sha(RUNTIME),prior_reservation_sha256=sha(RESERVATION),prior_dispatch_sha256=sha(DISPATCH)))
    print(json.dumps(dict(frozen=True,bindings=len(b),expected_tests=EXPECTED,new_tests=NEW)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['prior_source_sha256']==sha(PRIOR) and l['prior_plan_sha256']==sha(PRIOR_PLAN)
    assert l['future_plan_sha256']==sha(PLAN)
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
    observation=prior_evidence();saved=sealed(ROOT/f'reports/{PREFIX}-observations.json')
    for k,v in observation.items():assert saved[k]==v
    assert saved['ledger_sha256']==sha(LEDGER)
    assert saved['prior_runtime_sha256']==sha(RUNTIME) and saved['prior_reservation_sha256']==sha(RESERVATION)
    assert saved['prior_dispatch_sha256']==sha(DISPATCH)
    from forex_demo_lab.sharing_runtime_069 import LIMITS069
    from forex_demo_lab.image_guard_068 import MAX_IMAGE_BYTES
    assert LIMITS069['hash_bytes']==103079215104 and MAX_IMAGE_BYTES==136314880
    assert LIMITS069['commands']==6 and LIMITS069['script_arms']==2 and LIMITS069['schedule_waits']==2
    for n in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert not sealed(ROOT/n)['diagnostic_passed']
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),tests_passed=EXPECTED,
        observations_sha256=sha(ROOT/f'reports/{PREFIX}-observations.json'),prior_native_evidence_retained=True,
        previous_exact_failure_unknown=True,diagnostic_runner_prepared=True,future_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,tests_passed=EXPECTED,root_cause_proven=False)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['observations_sha256']==sha(ROOT/f'reports/{PREFIX}-observations.json')
    text=(f'# Sharing diagnostics071 results\n\n{EXPECTED} tests/{NEW} new pass; zero failures/errors/skips. '
        'The offline diagnostic runner separates guard, clock, launch deadline, wait, control, saved-range and cleanup '
        'failures with fixed codes and relative timings. It keeps the first failure and bounded owned cleanup. '
        'Tests reproduce different old-runner causes with the same generic reason. Guards, hashes, accounts, '
        'ten-second launch gate, five/35-second schedule and existing operation limits are unchanged.\n\n'
        'Frozen070 counters locate its failure before the first wait or independent control; the exact native '
        'substep and root cause remain unknown. No native timing delta was recorded there. Uncached guarded '
        'hash work totaled26612155900 bytes in67 guards, but this aggregate does not prove why the probe failed. '
        'Its confirmed cleanup, exact raw reservation/dispatch hashes and consumed allowances remain retained.\n\n'
        'This stage ran no MT5/SDK/compiler/deployment/terminal log-content reads/market/orders/grants or self profile. '
        'Injected success remains synthetic; no native MQL/publication/ACK or profit proof. Next '
        'NATIVE-SHARING-072-PLAN.md is fresh separately declared MQL/source/phase/build integration and tests, '
        'not a retry of069 or permission to reuse064. No native session authorized here. Preserve033/035 '
        'failures, clock/cost/coverage/flags, consumed2025, reserved Nov–Dec2026 and provider exclusions. '
        'Fresh/annual eligibility and orders false.\n')
    with (ROOT/'docs/SHARING-DIAGNOSTICS-071-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: offline sharing diagnostics071 sealed; read SHARING-DIAGNOSTICS-071-RESULTS.md. '
        f'{EXPECTED} tests/{NEW} new pass, zero failures/errors/skips. Fixed substep/failure codes and relative '
        'arm/receipt/guard/wait timings; first failure and owned cleanup retained. Old guard/deadline causes '
        'reproduced with indistinguishable old evidence;070 exact native cause remains unknown. Full guards '
        'and timing/budget gates unchanged. Zero MT5/SDK/compiler/deploy/terminal log/market/orders/grants; '
        'spent066/069 reservations and070 audit retained. Next072 fresh MQL/source/phase/build integration/tests, '
        'not executed; no064 reuse/native retry. Native sharing/publication/ACK/profit unestablished; '
        '033/035 and reserved gates retained; fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
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
        new_tests=NEW,prior_native_evidence_retained=True,diagnostic_runner_prepared=True,future_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final);l=sealed(LEDGER);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json')
    assert r['tests_passed']==EXPECTED and all(r[k]==v for k,v in {**ZERO,**FALSE}.items())
    assert b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN) and not r['future_plan_executed']
    prior_evidence()
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_input_coverage_complete=True,
        frozen_inputs_verified=len(l['bindings']),tests_passed=EXPECTED,new_tests=NEW,
        prior_native_evidence_retained=True,next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,frozen_inputs=len(l['bindings']))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','test','check','seal','review','verify'))
    dict(freeze=freeze,test=test,check=check,seal=seal,review=review,
        verify=lambda:print(len(verify()['bindings'])))[p.parse_args().action]()
