"""Exclusive synthetic experiment, test records and source/evidence closure."""
import argparse
import ast
import io
import json
from pathlib import Path
import runpy
import sys
import time
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab import challenger_chronology_093 as wf
API = runpy.run_path(str(ROOT / 'scripts/archived-evidence-092.py'))
sha, sealed, write, bound = (API[k] for k in ('sha', 'sealed', 'write', 'bound'))
HANDOFF, ARCHIVE, ZERO, FALSE = (API[k] for k in ('HANDOFF', 'ARCHIVE', 'ZERO', 'FALSE'))
PREFIX = 'challenger-chronology-093'
LEDGER = ROOT / f'reports/{PREFIX}-ledger.json'
DEST = ROOT / f'reports/{PREFIX}-synthetic'
DATA = ROOT / f'data/{PREFIX}-synthetic'
PRIOR = ROOT / 'reports/archived-evidence-092-final-source.json'
REVIEW = ROOT / 'reports/archived-evidence-092-completion-review.json'


def verify():
    l = sealed(LEDGER)
    for n, h in l['bindings'].items():
        assert sha(bound(n)) == h, n
    wf.verify(DEST)
    return l


def tests(pattern, label):
    report = ROOT / f'reports/{PREFIX}-{label}.json'
    start = report.with_name(report.stem + '-started.json')
    write(start, dict(pattern=pattern, source_bindings={p.relative_to(ROOT).as_posix(): sha(p) for p in wf.source_files()},
                      synthetic_only=True, **ZERO, **FALSE))
    output = io.StringIO(); begin = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern)
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    log = report.with_suffix('.txt')
    with log.open('x') as f:
        f.write(output.getvalue())
    value = dict(tests_passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped),
        elapsed_seconds=time.monotonic() - begin, started_sha256=sha(start), log_sha256=sha(log),
        **ZERO, **FALSE)
    write(report, value)
    print(json.dumps({k: value[k] for k in ('tests_passed', 'tests_run', 'failures', 'errors', 'skips', 'elapsed_seconds')}), flush=True)
    if not value['tests_passed']:
        raise SystemExit(1)
    return value


def development():
    i = 1
    while (ROOT / f'reports/{PREFIX}-development-{i:03}-started.json').exists():
        i += 1
    tests('test_challenger_chronology_093.py', f'development-{i:03}')


def freeze():
    API['verify'](); r, v = sealed(PRIOR), sealed(REVIEW)
    assert sha(PRIOR) == '1b7a797f7347ff42a05c32bbe07ed8a85b7729c10e429506390844f461353fc1'
    assert v['review_passed'] and v['final_source_sha256'] == sha(PRIOR)
    assert (v['bindings_verified'], v['archive_members_verified']) == (2884, 2667)
    assert ARCHIVE(PRIOR, r) == 2667
    b = dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:
        b.pop(n, None)
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    for p in (PRIOR, PRIOR.with_suffix('.sha256'), PRIOR.with_suffix('.zip'), REVIEW, REVIEW.with_suffix('.sha256'), *wf.source_files()):
        n = p.relative_to(ROOT).as_posix()
        if n in b:
            assert b[n] == sha(p), n
        b[n] = sha(p)
    development_reports = sorted((ROOT / 'reports').glob(f'{PREFIX}-development-*.json'))
    outcomes = [sealed(p) for p in development_reports if not p.stem.endswith('-started')]
    assert outcomes and outcomes[-1]['tests_passed']
    tree = ast.parse((ROOT / 'tests/test_challenger_chronology_093.py').read_text())
    new_tests = sum(isinstance(n, ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(tree))
    assert 0 < new_tests <= 80 and outcomes[-1]['tests_run'] == new_tests
    for p in (ROOT / 'reports').glob(f'{PREFIX}-development-*'):
        if p.is_file():
            b[p.relative_to(ROOT).as_posix()] = sha(p)
    lock = ROOT / f'reports/{PREFIX}-source-lock.json'
    write(lock, dict(bindings=b, new_tests=new_tests, maximum_scenarios=40, synthetic_only=True, **ZERO, **FALSE))
    # Source lock precedes creation of any persistent invented quote fixture.
    bundle = wf.synthetic_fixture(DATA)
    wf.freeze(bundle, DEST)
    for p in (lock, lock.with_suffix('.sha256'), *DATA.rglob('*'), *DEST.rglob('*')):
        if p.is_file():
            b[p.relative_to(ROOT).as_posix()] = sha(p)
    write(LEDGER, dict(bindings=b, new_tests=new_tests, original_tests=1942, maximum_runs=1,
        maximum_independent_checks=1, maximum_full_regressions=1, synthetic_only=True, **ZERO, **FALSE))
    print(json.dumps(dict(frozen=True, bindings=len(b), new_tests=new_tests)), flush=True)


def demo():
    verify()
    r = wf.run(DEST)
    print(json.dumps(dict(scenarios=len(r['scenario_bindings']), choices=len(r['selection_bindings']), synthetic=True)), flush=True)


def check():
    verify()
    started = ROOT / f'reports/{PREFIX}-check-started.json'
    write(started, dict(summary_sha256=sha(DEST / 'run/summary.json'), maximum_checks=1, **ZERO, **FALSE))
    checker = runpy.run_path(str(ROOT / 'scripts/check-challenger-chronology-093.py'))
    r = checker['check'](DEST)
    r['started_sha256'] = sha(started)
    write(ROOT / f'reports/{PREFIX}-checks.json', r)
    print(json.dumps(dict(checks_passed=True, scenarios=r['scenarios'], choices=r['choices'],
        arms=sum(x['arms_checked'] for x in r['window_checks'].values()))), flush=True)


def full():
    verify(); tests('test_*.py', 'full-tests')


def result_text(t, c):
    summary = wf.load(DEST / 'run/summary.json')
    choices = {f: wf.load(DEST / 'run' / (f + '-selection.json'))['selected'] for f in wf.FOLDS}
    return ('# Chronological challenger093 — software verified with invented data\n\n'
        'A separate synthetic-only runner now evaluates C00/C05/C06/C07/C08 across the declared '
        'training/test folds and both cost scenarios. Strategy028/030 rules, numeric009 selection '
        'screens and the original009/020 implementation remain unchanged. There is no market input '
        'or order path. Role labels alone are insufficient: accepted fixture bytes/provenance must '
        'match the deterministic093 generator.\n\n'
        f"Verified {t['tests_run']} passing tests, including the new093 tests and the retained1,942. "
        'One full regression, no failures/errors/skips. Meaningful new checks cover chronology, '
        'training-only choices and ties/CASH, warmup/window isolation, choice/source/input tampering, '
        'C00 parity with020, stop protection, financing/gaps, duplicates and restart/loss pauses.\n\n'
        'The single persisted invented demonstration contains40 scenarios and2 locked choices; '
        f"choices A={choices['A']}, B={choices['B']}. These choices describe invented quotes only, "
        'not a profitable market strategy. All scenarios, including losses/rejections, are retained. '
        'Each window starts with separate $10,000 capital; windows are not concatenated returns.\n\n'
        'Independent030 account arithmetic reconstructs bid/ask fills, exact fees, swap, risk/margin, '
        'first-eligible protection, tick equity, period/year marks and liquidation without running '
        'a strategy. Independent014 trade/period arithmetic also checks every scenario. '
        f"Checked {sum(x['ticks_checked'] for x in c['window_checks'].values())} invented input ticks "
        f"and {sum(x['arms_checked'] for x in c['window_checks'].values())} protection arms. "
        'A stop can still lose beyond its level after a gap; protection can lose after financing.\n\n'
        'Source, fixture, run, choice, independent check and test records are hash-bound, archived '
        'and reviewed. Development outcomes are preserved separately, including any repaired failures. '
        'Verified092 predecessor:2,884 bindings/2,667 archive members. Four leading handoffs updated '
        'with earlier history retained.\n\n'
        'Historical clocks, sessions/coverage, upstream lineage, repeatability and executable costs '
        'remain unqualified. No historical price decoding or new market returns, no2024 replay, '
        'consumed2025 remains excluded,Nov–Dec2026 stays reserved and October/provider stops stay. '
        'No external/native/SDK/DLL/WMI/MT5/compiler/deploy/log/market/orders/receipts/grants. Native090 '
        'branch stays closed. All market profitability/edge/eligibility/runtime/order flags remain false.\n\n'
        'The software is ready for invented chronological checks. Historical performance needs '
        'dated source-clock/coverage/lineage/cost evidence and a separate qualified-input plan; '
        'no market-capable runner, acquisition or replay is authorized by this result.\n')


def seal():
    l = verify(); t = sealed(ROOT / f'reports/{PREFIX}-full-tests.json'); c = sealed(ROOT / f'reports/{PREFIX}-checks.json')
    assert t['tests_passed'] and t['failures'] == t['errors'] == t['skips'] == 0
    assert t['tests_run'] == l['original_tests'] + l['new_tests']
    assert c['checks_passed'] and c['summary_sha256'] == sha(DEST / 'run/summary.json')
    result = ROOT / 'docs/CHALLENGER-CHRONOLOGY-093-RESULTS.md'
    with result.open('x') as f:
        f.write(result_text(t, c))
    latest = (f'Latest — synthetic chronological challenger093 software verified; {t["tests_run"]} passing tests '
        f'/{l["new_tests"]} new. Separate C00/C05/C06/C07/C08 runner, unchanged028/030 rules and009 screens, '
        'original009/020 untouched.40 invented scenarios/2 locked training choices, independent fill/cost/swap/'
        'protection/equity/period checks; market inputs reject, invented bytes must be reproducible. '
        'Read CHALLENGER-CHRONOLOGY-093-RESULTS.md. Synthetic diagnostics are not market returns or validation. '
        'Clock/session/coverage/lineage/repeatability/historical costs unresolved;2025 consumed/excluded, '
        'Nov–Dec2026 reserved, October/provider stops unchanged. Native090 branch closed; no external/native/'
        'MT5/deploy/log/market/orders/receipts/grants. Market edge/eligibility/runtime/orders false. Historical '
        'performance requires qualified evidence and a separately frozen plan; no acquisition or replay '
        'authorized here. No UI action. Earlier entries historical.\n\n')
    b = dict(l['bindings'])
    for n in HANDOFF:
        p = ROOT / n; s = p.read_text(); i = s.index('\n') + 1
        p.write_text(s[:i] + '\n' + latest + s[i:]); b[n] = sha(p)
    b[result.relative_to(ROOT).as_posix()] = sha(result)
    for p in (ROOT / 'reports').glob(PREFIX + '*'):
        paths = p.rglob('*') if p.is_dir() else (p,)
        for q in paths:
            if q.is_file():
                b[q.relative_to(ROOT).as_posix()] = sha(q)
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    external = {n: h for n, h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal = set(b) - set(external); final = ROOT / f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'), 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):
            z.write(ROOT / n, n)
    r = dict(source_and_evidence_bindings=b, archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')), archive_members_verified=len(internal),
        tests_passed=t['tests_run'], new_tests=l['new_tests'], scenarios=40, choices=2,
        synthetic_only=True, historical_price_rows_read=0, new_market_returns_computed=0,
        prior_failure_records_preserved=True, **ZERO, **FALSE)
    ARCHIVE(final, r); write(final, r)
    print(json.dumps(dict(sealed=True, bindings=len(b), members=len(internal), sha256=sha(final))), flush=True)


def review():
    l = verify(); final = ROOT / f'reports/{PREFIX}-final-source.json'; r = sealed(final)
    b = r['source_and_evidence_bindings']
    for n, h in b.items():
        assert sha(bound(n)) == h, n
    assert all(b.get(n) == h for n, h in l['bindings'].items())
    members = ARCHIVE(final, r)
    t = sealed(ROOT / f'reports/{PREFIX}-full-tests.json'); c = sealed(ROOT / f'reports/{PREFIX}-checks.json')
    assert (ROOT / 'docs/CHALLENGER-CHRONOLOGY-093-RESULTS.md').read_text() == result_text(t, c)
    assert r['tests_passed'] == 1942 + l['new_tests'] and c['checks_passed']
    for k, v in {**ZERO, **FALSE}.items():
        assert type(r[k]) is type(v) and r[k] == v
    write(ROOT / f'reports/{PREFIX}-completion-review.json', dict(review_passed=True,
        final_source_sha256=sha(final), bindings_verified=len(b), archive_members_verified=members,
        frozen_inputs_verified=len(l['bindings']), frozen_input_coverage_complete=True,
        tests_passed=r['tests_passed'], new_tests=l['new_tests'], scenarios=40, choices=2,
        synthetic_only=True, prior_failure_records_preserved=True, **ZERO, **FALSE))
    print(json.dumps(dict(review_passed=True, bindings=len(b), members=members, tests=r['tests_passed'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=('development', 'freeze', 'verify', 'demo', 'check', 'full', 'seal', 'review'))
    dict(development=development, freeze=freeze, verify=lambda: print(len(verify()['bindings'])),
         demo=demo, check=check, full=full, seal=seal, review=review)[p.parse_args().action]()
