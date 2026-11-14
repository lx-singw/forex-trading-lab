"""Repair test selection only; preserve093 failed run/source/demo unchanged."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
A = runpy.run_path(str(ROOT / 'scripts/seal-challenger-chronology-093.py'))
B = runpy.run_path(str(ROOT / 'scripts/source-feasibility-090.py'))
sha, sealed, write, bound = (A[k] for k in ('sha', 'sealed', 'write', 'bound'))
HANDOFF, ARCHIVE, ZERO, FALSE = (A[k] for k in ('HANDOFF', 'ARCHIVE', 'ZERO', 'FALSE'))
PREFIX = 'challenger-chronology-093'
REPAIR = PREFIX + '-r1'
LEDGER = ROOT / f'reports/{REPAIR}-ledger.json'
POLICY = ROOT / 'docs/CHALLENGER-CHRONOLOGY-093-R1-POLICY.md'
FULL = ROOT / f'reports/{REPAIR}-full-tests.json'


def selection():
    suite, retired = B['ACTIVE']['active_suite']()
    assert retired == 43 and suite.countTestCases() == 1975
    assert B['ACTIVE']['active_suite'].__code__.co_filename == str(ROOT / 'scripts/synchronization-084-r2.py')
    return suite


def freeze():
    l = A['verify'](); failed = sealed(ROOT / f'reports/{PREFIX}-full-tests.json')
    assert (failed['tests_passed'], failed['tests_run'], failed['failures'], failed['errors'], failed['skips']) == (False, 2054, 2, 0, 0)
    log = ROOT / f'reports/{PREFIX}-full-tests.txt'
    assert sha(log) == failed['log_sha256']
    assert 'test_source_build_phase_episode_sequence_and_padding_changes_rejected' in log.read_text()
    assert 'test_owned_cleanup_after_date_expiry' in log.read_text()
    selection()
    b = dict(l['bindings'])
    for p in (A['LEDGER'], A['LEDGER'].with_suffix('.sha256'), POLICY,
              ROOT / 'scripts/seal-challenger-chronology-093-r1.py'):
        b[p.relative_to(ROOT).as_posix()] = sha(p)
    for p in (ROOT / 'reports').glob(PREFIX + '*'):
        for q in (p.rglob('*') if p.is_dir() else (p,)):
            if q.is_file():
                b[q.relative_to(ROOT).as_posix()] = sha(q)
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    write(LEDGER, dict(bindings=b, original_ledger_sha256=sha(A['LEDGER']), policy_sha256=sha(POLICY),
        failed_full_result_sha256=sha(ROOT / f'reports/{PREFIX}-full-tests.json'),
        active_suite='scripts/synchronization-084-r2.py', active_tests=1975,
        original_retired083=43, original_retired084=36, new_exclusions=0,
        maximum_corrected_full_regressions=1, maximum_new_scenarios=0, maximum_new_checks=0,
        bot_sources_unchanged=True, failed_run_preserved=True, **ZERO, **FALSE))
    print(json.dumps(dict(repair_frozen=True, bindings=len(b), active_tests=1975)), flush=True)


def verify():
    A['verify'](); l = sealed(LEDGER)
    for n, h in l['bindings'].items():
        assert sha(bound(n)) == h, n
    assert l['original_ledger_sha256'] == sha(A['LEDGER']) and l['policy_sha256'] == sha(POLICY)
    assert l['new_exclusions'] == 0 and l['failed_run_preserved'] and l['bot_sources_unchanged']
    return l


def full():
    verify(); suite = selection(); started = FULL.with_name(FULL.stem + '-started.json')
    write(started, dict(ledger_sha256=sha(LEDGER), active_suite='scripts/synchronization-084-r2.py',
        active_tests=1975, retired083=43, retired084=36, new_exclusions=0, **ZERO, **FALSE))
    output = io.StringIO(); begin = time.monotonic()
    with redirect_stdout(output), redirect_stderr(output):
        r = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    log = FULL.with_suffix('.txt')
    with log.open('x') as f:
        f.write(output.getvalue())
    ok = r.wasSuccessful() and r.testsRun == 1975 and not r.skipped
    value = dict(tests_passed=ok, tests_run=r.testsRun, failures=len(r.failures), errors=len(r.errors),
        skips=len(r.skipped), elapsed_seconds=time.monotonic()-begin, new_tests=33, retained_tests=1942,
        active_suite='scripts/synchronization-084-r2.py', retired083=43, retired084=36, new_exclusions=0,
        ledger_sha256=sha(LEDGER), started_sha256=sha(started), log_sha256=sha(log),
        failed_original_run_preserved=True, **ZERO, **FALSE)
    write(FULL, value)
    print(json.dumps({k: value[k] for k in ('tests_passed','tests_run','failures','errors','skips','elapsed_seconds')}), flush=True)
    if not ok:
        raise SystemExit(1)


def result_text(t, c):
    original = A['result_text'](t, c)
    sentence = 'One full regression, no failures/errors/skips.'
    assert original.count(sentence) == 1
    return original.replace(sentence,
        'The initial unrestricted discovery ran2,054 cases and failed two already-retired083/084 fixtures. '
        'The frozen093 launcher used the wrong discovery entry point; it and that failure remain unchanged. '
        'A separately frozen R1 launcher inherited the established084R2 active suite, with the same '
        '43+36 prior exclusions and no new exclusions. The corrected1,975-test active full regression '
        'passed with zero failures/errors/skips. The bot sources and recorded demonstration were not changed '
        'or rerun. Both full results, logs, spent markers and correction policy are retained.')


def seal():
    l = verify(); t = sealed(FULL); c = sealed(ROOT / f'reports/{PREFIX}-checks.json')
    assert t['tests_passed'] and (t['tests_run'],t['new_tests'],t['failures'],t['errors'],t['skips']) == (1975,33,0,0,0)
    assert t['ledger_sha256'] == sha(LEDGER) and c['checks_passed']
    assert c['summary_sha256'] == sha(A['DEST'] / 'run/summary.json')
    result = ROOT / 'docs/CHALLENGER-CHRONOLOGY-093-RESULTS.md'
    with result.open('x') as f:
        f.write(result_text(t, c))
    latest = ('Latest — chronological challenger093 software verified with invented quotes; corrected '
        '084R2 active suite1975 passes/33 new. Original broad discovery2054 had2 retired083/084 fixture '
        'failures; preserved, no new test exclusions. R1 repairs orchestration only; bot sources and '
        'single40-scenario demonstration unchanged. Independent audit20,241 invented input ticks/424 '
        'protection arms;2 locked CASH choices. Read CHALLENGER-CHRONOLOGY-093-RESULTS.md. Separate '
        'C00/C05/C06/C07/C08 runner, original009/020 and028/030 rules unchanged. Market roles/modified '
        'fixture bytes reject; synthetic gains never approve data or orders. Historical clock/session/'
        'coverage/lineage/repeatability/cost evidence unresolved.2025 consumed/excluded,Nov–Dec2026 '
        'reserved,October/provider stops intact. Native090 branch closed; no external/native/MT5/'
        'compiler/deploy/log/market/orders/receipts/grants. Market edge/eligibility/runtime/orders false. '
        'Qualified evidence and a separate plan needed for historical performance; no acquisition/replay '
        'authorized by093. No UI action. Earlier entries historical.\n\n')
    b = dict(l['bindings'])
    for n in HANDOFF:
        p = ROOT / n; s = p.read_text(); i = s.index('\n') + 1
        p.write_text(s[:i] + '\n' + latest + s[i:]); b[n] = sha(p)
    b[result.relative_to(ROOT).as_posix()] = sha(result)
    for p in (ROOT / 'reports').glob(PREFIX + '*'):
        for q in (p.rglob('*') if p.is_dir() else (p,)):
            if q.is_file(): b[q.relative_to(ROOT).as_posix()] = sha(q)
    for n, h in b.items(): assert sha(bound(n)) == h, n
    external = {n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal = set(b)-set(external); final = ROOT / f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal): z.write(ROOT/n,n)
    r = dict(source_and_evidence_bindings=b, archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')), archive_members_verified=len(internal),
        tests_passed=1975,new_tests=33,scenarios=40,choices=2,synthetic_only=True,
        active_suite='scripts/synchronization-084-r2.py',retired083=43,retired084=36,new_exclusions=0,
        original_failed_tests=2054,original_failures=2,failed_original_run_preserved=True,
        bot_sources_unchanged_after_demo=True, historical_price_rows_read=0,new_market_returns_computed=0,
        prior_failure_records_preserved=True, **ZERO, **FALSE)
    ARCHIVE(final,r);write(final,r)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))),flush=True)


def review():
    l = verify(); final = ROOT / f'reports/{PREFIX}-final-source.json'; r = sealed(final)
    b = r['source_and_evidence_bindings']
    for n,h in b.items(): assert sha(bound(n))==h,n
    assert all(b.get(n)==h for n,h in l['bindings'].items())
    members=ARCHIVE(final,r);t=sealed(FULL);c=sealed(ROOT/f'reports/{PREFIX}-checks.json')
    assert (ROOT/'docs/CHALLENGER-CHRONOLOGY-093-RESULTS.md').read_text()==result_text(t,c)
    assert t['tests_passed'] and t['tests_run']==1975 and t['new_exclusions']==0
    assert t['ledger_sha256']==sha(LEDGER) and sha(FULL.with_suffix('.txt'))==t['log_sha256']
    failed=sealed(ROOT/f'reports/{PREFIX}-full-tests.json')
    assert failed['tests_passed'] is False and failed['failures']==2 and failed['tests_run']==2054
    assert sha(ROOT/f'reports/{PREFIX}-full-tests.txt')==failed['log_sha256']
    assert c['checks_passed'] and c['summary_sha256']==sha(A['DEST']/'run/summary.json')
    for k,v in {**ZERO,**FALSE}.items(): assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(final),
        bindings_verified=len(b),archive_members_verified=members,frozen_inputs_verified=len(l['bindings']),
        frozen_input_coverage_complete=True,tests_passed=1975,new_tests=33,scenarios=40,choices=2,
        active_suite='scripts/synchronization-084-r2.py',retired083=43,retired084=36,new_exclusions=0,
        failed_original_run_preserved=True,bot_sources_unchanged_after_demo=True,synthetic_only=True,
        prior_failure_records_preserved=True,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,tests=1975)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','full','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),full=full,seal=seal,review=review)[p.parse_args().action]()
