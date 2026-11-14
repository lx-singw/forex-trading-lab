"""Synthetic-only chronological challenger runner. No network or broker client."""
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

from . import walk_forward_metrics as base
from .challenger_selection_093 import CANDIDATES, COSTS, FOLDS, select_fold, selection_rows
from .execution_metrics import METRIC_VERSION
from .exit_experiment_030 import Experiment030Simulator
from .model import Config
from .strategy_experiment_028 import Experiment028Simulator
from .tick_audit import sha256

ROOT, YEARS, HOUR = base.ROOT, base.YEARS, base.HOUR
VERSION = 'synthetic_challenger_chronology_093_v1'
FIXTURE_VERSION = 'invented_sparse_quarters_093_v1'
SPEC = ROOT / 'config/challenger-chronology-093.json'
CONTRACT = ROOT / 'reports/challenger-chronology-093-contract.json'
APPROVALS = dict(performance_evaluation_ready=False, historical_positive_edge_screen_passed=False,
    market_profitability_established=False, demo_execution_ready=False, orders_available=False,
    annual_eligible=False, runtime_authorized=False)
load, bound, period = base.load, base.bound, base.period


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def specification():
    if sha256(CONTRACT) != CONTRACT.with_suffix('.sha256').read_text().strip():
        raise ValueError('093 contract changed')
    contract = load(CONTRACT)
    if contract['prior_final_source_sha256'] != '1b7a797f7347ff42a05c32bbe07ed8a85b7729c10e429506390844f461353fc1':
        raise ValueError('Prior closure differs')
    for name, digest in contract['bindings'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError('Immutable specification or dependency changed: ' + name)
    spec = load(SPEC)
    if (spec['version'] != VERSION or spec['synthetic_only'] is not True
            or tuple(spec['candidates']) != CANDIDATES or tuple(spec['costs']) != COSTS
            or tuple(spec['years']) != YEARS or spec['folds'] != {k: list(v) for k, v in FOLDS.items()}
            or spec['maximum_scenarios'] != 40 or spec['maximum_choices'] != 2):
        raise ValueError('093 fixed specification differs')
    return spec


def require_synthetic(value, kind):
    if value.get('kind') != kind or value.get('synthetic') is not True:
        raise ValueError('093 accepts invented synthetic fixtures only; market input forbidden')


def quotes(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError('Unsupported synthetic year')
    sequence = 0
    for quarter, month in enumerate((1, 4, 7, 10)):
        start = int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp()) * 1000
        for h in range(256):
            for minute in (0, 30, 59):
                bid = round(1.1 + .003 * math.sin(h / 12 + quarter / 3 + minute / 60) + .00003 * h, 5)
                yield dict(sequence=sequence, time_msc=start + h * HOUR + minute * 60000,
                           bid=bid, ask=round(bid + .0001, 5))
                sequence += 1


def fixture_bytes(year):
    buffer = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, mtime=0) as zipped:
        with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['sequence', 'time_msc', 'bid', 'ask'])
            writer.writeheader()
            writer.writerows(quotes(year))
    return buffer.getvalue()


def provenance(year):
    rows = list(quotes(year))
    return dict(kind='chronological_research_ticks', symbol='EURUSD', year=year, synthetic=True,
        fixture_version=FIXTURE_VERSION, ticks=len(rows), first_ms=rows[0]['time_msc'],
        last_ms=rows[-1]['time_msc'], data_sha256=hashlib.sha256(fixture_bytes(year)).hexdigest(),
        source='fixed093 invented sparse quarters; no market source')


def fixture_inventory(year):
    rows = list(quotes(year))
    hours = sorted({r['time_msc'] // HOUR * HOUR for r in rows})
    gaps = [dict(after_ms=a['time_msc'], before_ms=b['time_msc'],
                 seconds=(b['time_msc'] - a['time_msc']) / 1000)
            for a, b in zip(rows, rows[1:]) if b['time_msc'] - a['time_msc'] > HOUR]
    return dict(ticks=len(rows), first_ms=rows[0]['time_msc'], last_ms=rows[-1]['time_msc'],
        observed_hours=len(hours), first_evaluation_ms=hours[201],
        last_201_hours_start_ms=hours[-201], gaps_over_one_hour=gaps)


def synthetic_fixture(destination):
    specification()
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    entries = {}
    for y in YEARS:
        path = destination / f'{y}-ticks.csv.gz'
        with path.open('xb') as f:
            f.write(fixture_bytes(y))
        save(destination / f'{y}-provenance.json', provenance(y))
        entries[str(y)] = dict(data=path.name, provenance=f'{y}-provenance.json')
    save(destination / 'review.json', dict(kind='synthetic_chronological_fixture', synthetic=True,
        performance_evaluation_ready=False, years={str(y): {} for y in YEARS}))
    save(destination / 'bundle.json', dict(kind='chronological_ticks_input', synthetic=True,
        fixture_version=FIXTURE_VERSION, years=entries, review='review.json'))
    return destination / 'bundle.json'


def windows(inventories):
    result = {}
    for label, start, end in [('A-training', 2020, 2022), ('A-test', 2022, 2023),
                               ('B-training', 2021, 2023), ('B-test', 2023, 2024)]:
        result[label] = dict(start_year=start, end_year=end,
            evaluation_start_ms=inventories['2020']['first_evaluation_ms'] if start == 2020 else bound(start),
            warmup_start_ms=bound(2020) if start == 2020 else inventories[str(start - 1)]['last_201_hours_start_ms'])
    return result


def source_files():
    paths = set((ROOT / 'src').rglob('*.py')) | set((ROOT / 'tests').glob('test_challenger*093.py'))
    paths.update(ROOT / n for n in ('scripts/challenger-chronology-093.py',
        'scripts/check-challenger-chronology-093.py', 'scripts/seal-challenger-chronology-093.py',
        'scripts/check-exit-experiment-030.py', 'scripts/exit-experiment-030.py',
        'scripts/check-walk-forward-014.py', 'config/tick-pilot-003.json',
        'config/tick-pilot-003-adverse.json', 'docs/CHALLENGER-CHRONOLOGY-093-PLAN.md',
        'docs/CHALLENGER-CHRONOLOGY-093-POLICY.md'))
    paths.update((SPEC, CONTRACT, CONTRACT.with_suffix('.sha256')))
    return sorted(paths)


def freeze(bundle_path, destination):
    bundle_path, destination = Path(bundle_path).resolve(), Path(destination)
    bundle = load(bundle_path)
    require_synthetic(bundle, 'chronological_ticks_input')  # Before data iteration/output.
    if (set(bundle['years']) != {str(y) for y in YEARS}
            or bundle.get('fixture_version') != FIXTURE_VERSION):
        raise ValueError('Require exactly fixed093 invented2020–2023 inputs')
    if destination.exists():
        raise FileExistsError('Experiment destination exists')
    specification()
    resolve = lambda p: str((bundle_path.parent / p).resolve())
    entries = {str(y): {k: resolve(bundle['years'][str(y)][k]) for k in ('data', 'provenance')} for y in YEARS}
    review_path = Path(resolve(bundle['review']))
    base.review_gate(load(review_path), synthetic=True)
    bindings = {str(bundle_path): sha256(bundle_path), str(review_path): sha256(review_path)}
    # Role labels alone cannot reclassify provider bytes as invented data.
    for y in YEARS:
        entry = entries[str(y)]
        if load(entry['provenance']) != provenance(y) or sha256(Path(entry['data'])) != provenance(y)['data_sha256']:
            raise ValueError('Fixture is not reproducible invented093 bytes/provenance')
        bindings.update({p: sha256(Path(p)) for p in entry.values()})
    inventories = {str(y): base.inventory(entries[str(y)], y, True) for y in YEARS}
    if inventories != {str(y): fixture_inventory(y) for y in YEARS}:
        raise ValueError('Invented fixture inventory differs')
    configs = {k: asdict(Config(**load(ROOT / f'config/tick-pilot-003{"-adverse" if k == "adverse" else ""}.json'))) for k in COSTS}
    files = source_files()
    sources = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(destination / 'source.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT).as_posix())
    ledger = dict(kind='frozen_challenger_093', synthetic=True, version=VERSION,
        metric_contract=METRIC_VERSION, input_bindings=bindings, source_bindings=sources,
        archive_sha256=sha256(destination / 'source.zip'), contract_sha256=sha256(CONTRACT),
        configs=configs, candidates=list(CANDIDATES), costs=list(COSTS), maximum_scenarios=40,
        entries=entries, inventory=inventories, windows=windows(inventories), **APPROVALS)
    save(destination / 'ledger.json', ledger)
    save(destination / 'seal.json', dict(ledger_sha256=sha256(destination / 'ledger.json')))
    return ledger


def verify(destination):
    destination = Path(destination)
    ledger = load(destination / 'ledger.json')
    require_synthetic(ledger, 'frozen_challenger_093')
    specification()
    if (sha256(destination / 'ledger.json') != load(destination / 'seal.json')['ledger_sha256']
            or ledger['version'] != VERSION or ledger['metric_contract'] != METRIC_VERSION
            or ledger['contract_sha256'] != sha256(CONTRACT)
            or ledger['candidates'] != list(CANDIDATES) or ledger['costs'] != list(COSTS)
            or ledger['maximum_scenarios'] != 40):
        raise ValueError('Frozen093 ledger/version/budget differs')
    for k, v in APPROVALS.items():
        if ledger.get(k) is not v:
            raise ValueError('Synthetic ledger cannot grant eligibility or execution')
    for group in ('input_bindings', 'source_bindings'):
        for p, digest in ledger[group].items():
            if sha256(Path(p) if group == 'input_bindings' else ROOT / p) != digest:
                raise ValueError('Frozen input or source changed')
    if set(ledger['source_bindings']) != {p.relative_to(ROOT).as_posix() for p in source_files()}:
        raise ValueError('Source inventory differs')
    expected = {str(y): fixture_inventory(y) for y in YEARS}
    if ledger['inventory'] != expected or ledger['windows'] != windows(expected) or set(ledger['entries']) != set(expected):
        raise ValueError('Fixed invented bounds/inventory changed')
    for y in YEARS:
        entry = ledger['entries'][str(y)]
        if any(p not in ledger['input_bindings'] for p in entry.values()):
            raise ValueError('Unbound annual input')
        if load(entry['provenance']) != provenance(y) or sha256(Path(entry['data'])) != provenance(y)['data_sha256']:
            raise ValueError('Invented093 provenance changed')
    expected_configs = {k: asdict(Config(**load(ROOT / f'config/tick-pilot-003{"-adverse" if k == "adverse" else ""}.json'))) for k in COSTS}
    if ledger['configs'] != expected_configs:
        raise ValueError('Fixed costs changed')
    if sha256(destination / 'source.zip') != ledger['archive_sha256']:
        raise ValueError('Frozen source archive changed')
    with zipfile.ZipFile(destination / 'source.zip') as z:
        if set(z.namelist()) != set(ledger['source_bindings']) or len(z.infolist()) != len(ledger['source_bindings']):
            raise ValueError('Source archive inventory changed')
        for n, digest in ledger['source_bindings'].items():
            if hashlib.sha256(z.read(n)).hexdigest() != digest:
                raise ValueError('Archived source differs')
    return ledger


def simulator(config, candidate, evaluation):
    if candidate not in CANDIDATES:
        raise ValueError('Unknown093 candidate')
    cls = Experiment030Simulator if candidate in ('C07', 'C08') else Experiment028Simulator
    return cls(config, candidate, evaluation)


def replay_input_gate(ledger):
    require_synthetic(ledger, 'frozen_challenger_093')
    specification()
    for k, v in APPROVALS.items():
        if ledger.get(k) is not v:
            raise ValueError('Invented replay cannot grant eligibility or execution')
    expected_configs = {k: asdict(Config(**load(ROOT / f'config/tick-pilot-003{"-adverse" if k == "adverse" else ""}.json'))) for k in COSTS}
    if ledger.get('configs') != expected_configs:
        raise ValueError('Fixed replay costs changed')
    if set(ledger.get('entries', {})) != {str(y) for y in YEARS}:
        raise ValueError('Fixed replay years changed')
    for y in YEARS:
        entry = ledger['entries'][str(y)]
        if load(entry['provenance']) != provenance(y) or sha256(Path(entry['data'])) != provenance(y)['data_sha256']:
            raise ValueError('Replay requires reproducible invented093 inputs')


def replay_window(ledger, window):
    replay_input_gate(ledger)  # Direct API calls have the same input boundary as the CLI.
    if window not in list(windows({str(y): fixture_inventory(y) for y in YEARS}).values()):
        raise ValueError('Unsupported window')
    evaluation, end = window['evaluation_start_ms'], window['end_year']
    accounts = {(c, k): simulator(Config(**ledger['configs'][k]), c, evaluation) for c in CANDIDATES for k in COSTS}
    marks, closing = {key: {} for key in accounts}, {key: {} for key in accounts}
    observed, warmup, previous, evaluated = {}, set(), None, False
    for tick in base.window_ticks(ledger, window):
        ms = tick['time_msc']
        if not window['warmup_start_ms'] <= ms < bound(end):
            raise ValueError('Window includes future or out-of-scope quote')
        key_period = period(ms) if ms >= evaluation else None
        if ms < evaluation:
            warmup.add(ms // HOUR)
        else:
            if not evaluated and len(warmup) != 201:
                raise ValueError('Require exactly201 observed warmup hours')
            evaluated = True
            observed[key_period] = observed.get(key_period, 0) + 1
        for key, sim in accounts.items():
            if previous is not None and previous != key_period:
                closing[key][previous] = base.account_mark(sim)
            sim.step_tick(tick)
            if ms >= evaluation:
                marks[key][key_period] = sim.last_equity
        previous = key_period
    if not evaluated:
        raise ValueError('Window lacks evaluation quotes')
    rows = []
    for (c, k), sim in accounts.items():
        aggregate, metrics = base.reconcile(sim, marks[(c, k)], window['start_year'], end, evaluation)
        closing[(c, k)][period(sim.last_tick['time_msc'])] = base.account_mark(sim)
        protection = sim.protection_lineage if c in ('C07', 'C08') else [dict(trade_index=i,
            initial_stop=t['stop'], initial_risk=abs(t['entry'] - t['stop']) * t['lots'] * sim.config.contract_size,
            initial_distance=abs(t['entry'] - t['stop']), arm=None) for i, t in enumerate(sim.trades)]
        rows.append(dict(candidate=c, cost=k, version=VERSION, metric_contract=METRIC_VERSION,
            synthetic=True, training_start=datetime.fromtimestamp(bound(window['start_year']) / 1000, timezone.utc).isoformat(),
            training_end_exclusive=datetime.fromtimestamp(bound(end) / 1000, timezone.utc).isoformat(),
            **aggregate, metrics=metrics, trades=sim.trades, peak_tick_equity=sim.peak_tick_equity,
            period_closing_marks=closing[(c, k)], observed_ticks_by_quarter=observed,
            warmup_hours=len(warmup), evaluation_start_ms=evaluation, reconciled=True,
            fill_lineage=sim.fill_lineage, protection_lineage=protection,
            flat_account_decisions=sim.decision_log,
            equity=[p for p in sim.curve if int(datetime.fromisoformat(p['time']).timestamp() * 1000) >= evaluation],
            **APPROVALS))
    return rows


def screen(metrics):
    return metrics['net_return'] > 0 and metrics['closed_trades'] >= 20 and metrics['max_tick_drawdown'] <= .10


def run(destination):
    destination = Path(destination)
    ledger = verify(destination)
    output = destination / 'run'
    output.mkdir(exist_ok=False)  # A partial/consumed run cannot be overwritten.
    ledger_hash = sha256(destination / 'ledger.json')
    save(output / 'started.json', dict(ledger_sha256=ledger_hash, maximum_scenarios=40, synthetic=True, **APPROVALS))
    scenarios, choices, selected_tests = {}, {}, []
    for fold, (_, test_year) in FOLDS.items():
        training = replay_window(ledger, ledger['windows'][fold + '-training'])
        bindings = {}
        for row in training:
            name = f'{fold}-training-{row["candidate"]}-{row["cost"]}.json'
            save(output / name, dict(ledger_sha256=ledger_hash, **row))
            scenarios[name] = bindings[name] = sha256(output / name)
        choice = select_fold(selection_rows(training), fold)
        choice.update(training_report_bindings=bindings, ledger_sha256=ledger_hash,
                      version=VERSION, metric_contract=METRIC_VERSION, **APPROVALS)
        name = fold + '-selection.json'
        save(output / name, choice)  # Training lock exists before test consumption.
        choices[name] = sha256(output / name)
        tests = replay_window(ledger, ledger['windows'][fold + '-test'])
        if sha256(output / name) != choices[name]:
            raise ValueError('Locked choice changed during test')
        for row in tests:
            report_name = f'{fold}-test-{row["candidate"]}-{row["cost"]}.json'
            save(output / report_name, dict(ledger_sha256=ledger_hash, selection_sha256=choices[name], **row))
            scenarios[report_name] = sha256(output / report_name)
        for k in COSTS:
            metrics = next(r['metrics'] for r in tests if r['candidate'] == choice['selected'] and r['cost'] == k) \
                if choice['selected'] != 'CASH' else dict(net_return=0, net_pnl=0, closed_trades=0, max_tick_drawdown=0)
            selected_tests.append(dict(fold=fold, test_year=test_year, candidate=choice['selected'], cost=k,
                metrics=metrics, positive_edge_screen_passed=screen(metrics), synthetic=True))
    if len(scenarios) != 40 or len(choices) != 2:
        raise ValueError('Fixed scenario/choice budget differs')
    verify(destination)
    for name, digest in {**scenarios, **choices}.items():
        if sha256(output / name) != digest:
            raise ValueError('Scenario or choice changed before completion')
    summary = dict(kind='completed_challenger_093', version=VERSION, metric_contract=METRIC_VERSION,
        synthetic=True, status='invented_fixture_diagnostics_only', ledger_sha256=ledger_hash,
        scenario_bindings=scenarios, selection_bindings=choices, selected_tests=selected_tests,
        capital_restarts_not_concatenated=True, **APPROVALS)
    save(output / 'summary.json', summary)
    return summary
