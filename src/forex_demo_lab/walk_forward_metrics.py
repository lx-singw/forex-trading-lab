# Migration 020: original 014 body with declared import/metadata/freeze sites only.
"""Frozen 009 chronological replay, with separate synthetic and reviewed inputs."""
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import zipfile

from .cli import write_json
from .model import Config
from .execution_metrics import ExecutableEquityResearchTickSimulator as ResearchTickSimulator, METRIC_VERSION
from .selection import COSTS, FOLDS, select_fold
from .strategies import CANDIDATES
from .tick_audit import sha256

HOUR = 3_600_000
YEARS = tuple(range(2020, 2024))
ROOT = Path(__file__).resolve().parents[2]
FIXED = ('docs/HISTORY-009-PLAN.md', 'docs/WALK-FORWARD-014-PLAN.md',
         'config/research-candidates-008.json', 'config/tick-pilot-003.json',
         'config/tick-pilot-003-adverse.json')


FIXED = FIXED + ('docs/WALK-FORWARD-020-PLAN.md',)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def bound(year):
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()) * 1000


def period(ms):
    t = datetime.fromtimestamp(ms / 1000, timezone.utc)
    return f'{t.year}-Q{(t.month-1)//3+1}'


def review_gate(review, synthetic=False):
    kind = 'synthetic_chronological_fixture' if synthetic else 'chronological_data_review'
    if (review.get('kind') != kind or review.get('synthetic') is not synthetic
            or review.get('performance_evaluation_ready') is not (not synthetic)
            or set(review.get('years', {})) != {str(y) for y in YEARS}):
        raise ValueError('Annual data review does not approve this input role and all four years')
    if synthetic:
        return
    evidence = review.get('evidence_bindings', {})
    if not evidence:
        raise ValueError('Market review requires bound evidence and source lineage')
    for path, digest in evidence.items():
        if sha256(Path(path)) != digest:
            raise ValueError('Review evidence changed')
    for y in YEARS:
        row = review['years'][str(y)]
        if (any(row.get(k) is not True for k in ('performance_evaluation_ready',
                'clock_verified', 'independent_corroboration_passed', 'source_lineage_reviewed'))
                or type(row.get('unresolved_open_session_gaps')) is not int
                or row['unresolved_open_session_gaps'] != 0
                or sorted(row.get('source_months', [])) != [f'{y}{m:02}' for m in range(1, 13)]):
            raise ValueError(f'Year {y} lacks clock, lineage, corroboration or coverage approval')


def annual_ticks(entry, year, synthetic):
    """Hash before consuming; validate the complete stream, including its final row."""
    meta = load(entry['provenance'])
    digest = sha256(Path(entry['data']))
    if (meta.get('kind') != 'chronological_research_ticks' or meta.get('symbol') != 'EURUSD'
            or type(meta.get('year')) is not int or meta['year'] != year
            or meta.get('synthetic') is not synthetic or meta.get('data_sha256') != digest
            or type(meta.get('ticks')) is not int or meta['ticks'] < 1):
        raise ValueError('Annual tick provenance or bytes mismatch')
    count, previous, first = 0, None, None
    with gzip.open(entry['data'], 'rt', encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['sequence', 'time_msc', 'bid', 'ask']:
            raise ValueError('Invalid annual tick header')
        for row in reader:
            tick = {'sequence': int(row['sequence']), 'time_msc': int(row['time_msc']),
                    'bid': float(row['bid']), 'ask': float(row['ask'])}
            ms = tick['time_msc']
            if (tick['sequence'] != count or not bound(year) <= ms < bound(year+1)
                    or previous is not None and ms < previous
                    or not all(math.isfinite(tick[k]) for k in ('bid', 'ask'))
                    or not 0 < tick['bid'] <= tick['ask']):
                raise ValueError('Invalid annual sequence, time or quote')
            first = ms if first is None else first
            previous, count = ms, count+1
            yield tick
    if count != meta['ticks'] or first != meta.get('first_ms') or previous != meta.get('last_ms'):
        raise ValueError('Annual tick coverage differs from provenance')


def inventory(entry, year, synthetic):
    hours, months, gaps = [], set(), []
    count, first, last = 0, None, None
    for tick in annual_ticks(entry, year, synthetic):
        ms = tick['time_msc']
        hour = ms // HOUR * HOUR
        if not hours or hours[-1] != hour:
            hours.append(hour)
        months.add(datetime.fromtimestamp(ms/1000, timezone.utc).month)
        if last is not None and ms-last > HOUR:
            gaps.append({'after_ms': last, 'before_ms': ms, 'seconds': (ms-last)/1000})
        first = ms if first is None else first
        last, count = ms, count+1
    if len(hours) <= 201 or not synthetic and months != set(range(1, 13)):
        raise ValueError('Annual coverage lacks warmup or all twelve months')
    return {'ticks': count, 'first_ms': first, 'last_ms': last,
            'observed_hours': len(hours), 'first_evaluation_ms': hours[201],
            'last_201_hours_start_ms': hours[-201], 'gaps_over_one_hour': gaps}


def source_files():
    return sorted(set(ROOT.joinpath('src').rglob('*.py'))
                  | {ROOT/'scripts/walk-forward-014.py',ROOT/'scripts/check-walk-forward-014.py',
                     ROOT/'scripts/walk-forward-020.py',ROOT/'scripts/check-walk-forward-020.py',
                     ROOT/'scripts/migrate-walk-forward-020.py'}
                  | set(ROOT.joinpath('tests').glob('test_walk_forward*.py'))
                  | {ROOT/p for p in FIXED})


def freeze(bundle_path, destination):
    """No return computation; validate inputs before creating the frozen directory."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Experiment destination exists')
    bundle_path = Path(bundle_path).resolve()
    bundle = load(bundle_path)
    synthetic = bundle.get('synthetic')
    if (type(synthetic) is not bool or bundle.get('kind') != 'chronological_ticks_input'
            or set(bundle.get('years', {})) != {str(y) for y in YEARS}):
        raise ValueError('Require exactly the declared 2020–2023 annual inputs')
    # Relative input paths resolve against the bundle, never the caller cwd.
    resolve = lambda p: str((bundle_path.parent/Path(p)).resolve())
    entries = {y: {k: resolve(bundle['years'][str(y)][k]) for k in ('data', 'provenance')}
               for y in YEARS}
    review_path = Path(resolve(bundle['review']))
    review = load(review_path)
    review_gate(review, synthetic)
    inventories, bindings = {}, {str(bundle_path): sha256(bundle_path), str(review_path): sha256(review_path)}
    for y, entry in entries.items():
        if not synthetic and (review['years'][str(y)].get('data_sha256') != sha256(Path(entry['data']))
                or review['years'][str(y)].get('provenance_sha256') != sha256(Path(entry['provenance']))):
            raise ValueError('Year-specific review does not bind this dataset')
        inventories[str(y)] = inventory(entry, y, synthetic)
        bindings.update({p: sha256(Path(p)) for p in entry.values()})
    bindings.update(review.get('evidence_bindings', {}))
    configs = {c: asdict(Config(**load(ROOT/f'config/tick-pilot-003{"-adverse" if c == "adverse" else ""}.json')))
               for c in COSTS}
    # Compare with the original candidate batch, rather than accepting revised costs.
    original = load(ROOT/'reports/comparison-008-ledger.json')
    original_zip = ROOT/'reports/comparison-008-source.zip'
    if sha256(original_zip) != original['archive_sha256']:
        raise ValueError('Original candidate source archive changed')
    with zipfile.ZipFile(original_zip) as archived:
        for name in ('model','simulation','research_simulation','strategies','tick_simulation'):
            path = f'src/forex_demo_lab/{name}.py'
            if archived.read(path) != (ROOT/path).read_bytes():
                raise ValueError('Frozen strategy or shared simulation implementation changed')
    if sha256(ROOT/FIXED[2]) != original['spec_sha256']:
        raise ValueError('Frozen candidate specification changed')
    prior = load(ROOT/'reports/correction-013-final-source-02.json')
    for path in ('src/forex_demo_lab/selection.py','docs/HISTORY-009-PLAN.md'):
        if sha256(ROOT/path) != prior['source_bindings'][path]:
            raise ValueError('Frozen selection rules or 009 protocol changed')
    for cost in COSTS:
        expected = [s['config'] for s in original['scenarios'] if s['cost'] == cost]
        if not expected or any(v != configs[cost] for v in expected):
            raise ValueError('Frozen 008 costs/risk configuration changed')
    if tuple(c['id'] for c in load(ROOT/FIXED[2])['candidates']) != CANDIDATES:
        raise ValueError('Frozen candidate set changed')
    bindings[str(ROOT/'reports/comparison-008-ledger.json')] = sha256(ROOT/'reports/comparison-008-ledger.json')
    for p in (original_zip,ROOT/'reports/correction-013-final-source-02.json'):
        bindings[str(p)] = sha256(p)
    windows = {}
    for label, start, end in [('A-training',2020,2022), ('A-test',2022,2023),
                              ('B-training',2021,2023), ('B-test',2023,2024)]:
        windows[label] = {'start_year': start, 'end_year': end,
            'evaluation_start_ms': inventories['2020']['first_evaluation_ms'] if start == 2020 else bound(start),
            'warmup_start_ms': bound(2020) if start == 2020 else inventories[str(start-1)]['last_201_hours_start_ms']}
    files = source_files()
    code = {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}
    destination.mkdir(parents=True, exist_ok=False)
    archive = destination/'source.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for p in files:
            zipped.write(p, p.relative_to(ROOT).as_posix())
    result = {'kind': 'frozen_chronological_replay_020', 'synthetic': synthetic,
        'frozen_utc': datetime.now(timezone.utc).isoformat(), 'input_bindings': bindings,
        'source_bindings': code, 'archive_sha256': sha256(archive), 'configs': configs,
        'entries': {str(y): e for y,e in entries.items()}, 'inventory': inventories, 'windows': windows,
        'performance_evaluation_ready': not synthetic, 'demo_execution_ready': False,
        'market_profitability_established': False, 'maximum_scenarios': 40,
        'runner_version': '020', 'metric_contract': METRIC_VERSION}
    write_json(destination/'ledger.json', result)
    write_json(destination/'seal.json', {'ledger_sha256': sha256(destination/'ledger.json')})
    return result


def verify(destination):
    destination = Path(destination)
    if sha256(destination/'ledger.json') != load(destination/'seal.json')['ledger_sha256']:
        raise ValueError('Frozen ledger changed')
    ledger = load(destination/'ledger.json')
    if ledger.get('kind') != 'frozen_chronological_replay_020':
        raise ValueError('Invalid replay ledger; 020 requires a new freeze')
    if ledger.get('runner_version') != '020' or ledger.get('metric_contract') != METRIC_VERSION:
        raise ValueError('Runner or execution metric version mismatch')
    if sha256(destination/'source.zip') != ledger['archive_sha256']:
        raise ValueError('Frozen archive changed')
    for p, expected in ledger['input_bindings'].items():
        if sha256(Path(p)) != expected:
            raise ValueError('Frozen input or evidence changed')
    for p, expected in ledger['source_bindings'].items():
        if sha256(ROOT/p) != expected:
            raise ValueError('Frozen code or protocol changed')
    return ledger


def window_ticks(ledger, window):
    start, end = window['start_year'], window['end_year']
    first_year = start-1 if start > 2020 else start
    sequence = 0
    for y in range(first_year, end):
        for tick in annual_ticks(ledger['entries'][str(y)], y, ledger['synthetic']):
            if tick['time_msc'] < window['warmup_start_ms']:
                continue
            yield {**tick, 'sequence': sequence}
            sequence += 1


def reconcile(sim, quarters, start, end, evaluation_start):
    sim.finish()
    final_period = period(sim.last_tick['time_msc'])
    quarters[final_period] = sim.last_equity  # Final liquidation costs included.
    previous = sim.config.initial_equity
    changes, annual = {}, {}
    for year in range(start, end):
        opening = previous
        for q in range(1, 5):
            key = f'{year}-Q{q}'
            closing = quarters.get(key, previous)
            changes[key] = closing-previous
            previous = closing
        annual[str(year)] = {'starting_equity': opening, 'net_pnl': previous-opening,
                            'closed_trades': sum(datetime.fromisoformat(t['closed']).year == year for t in sim.trades)}
    metrics = sim.metrics()
    for trade in sim.trades:
        if (int(datetime.fromisoformat(trade['opened']).timestamp()*1000) < evaluation_start
                or not math.isclose(trade['gross_pnl']-trade['commission']+trade['swap'], trade['net_pnl'], abs_tol=1e-8)):
            raise ValueError('Warmup trade or inconsistent trade charges')
    wins = sum(t['net_pnl'] for t in sim.trades if t['net_pnl'] > 0)
    losses = sum(t['net_pnl'] for t in sim.trades if t['net_pnl'] < 0)
    if (not math.isclose(sum(changes.values()), metrics['net_pnl'], abs_tol=1e-8)
            or not math.isclose(wins+losses, metrics['net_pnl'], abs_tol=1e-8)
            or not math.isclose(previous, sim.config.initial_equity+metrics['net_pnl'], abs_tol=1e-8)
            or len(sim.trades) != metrics['closed_trades']):
        raise ValueError('Period/trade/final equity reconciliation failed')
    return {'years': annual, 'quarters': changes, 'closed_trades': len(sim.trades),
            'net_winning_trade_sum': wins, 'net_losing_trade_sum': losses,
            'max_tick_drawdown': metrics['max_tick_drawdown']}, metrics


def replay_window(ledger, window):
    start, end = window['start_year'], window['end_year']
    evaluation = window['evaluation_start_ms']
    accounts = {(c,k): ResearchTickSimulator(Config(**ledger['configs'][k]), c, evaluation)
                for c in CANDIDATES for k in COSTS}
    marks = {key: {} for key in accounts}
    closing_marks = {key: {} for key in accounts}
    observed = {}
    warmup_hours = set()
    evaluation_seen = False
    previous_period = None
    for tick in window_ticks(ledger, window):
        ms = tick['time_msc']
        if not window['warmup_start_ms'] <= ms < bound(end):
            raise ValueError('Window includes future or out-of-scope data')
        key_period = period(ms) if ms >= evaluation else None
        if ms < evaluation:
            warmup_hours.add(ms//HOUR)
        else:
            if not evaluation_seen and len(warmup_hours) != 201:
                raise ValueError('Window requires exactly 201 observed warmup hours')
            evaluation_seen = True
            observed[key_period] = observed.get(key_period,0)+1
        for key, sim in accounts.items():
            if previous_period is not None and previous_period != key_period:
                closing_marks[key][previous_period] = account_mark(sim)
            sim.step_tick(tick)
            if ms >= evaluation:
                marks[key][key_period] = sim.last_equity
        previous_period = key_period
    if not evaluation_seen:
        raise ValueError('Window has no evaluation quotes')
    results = []
    for (candidate,cost), sim in accounts.items():
        aggregates, metrics = reconcile(sim, marks[(candidate,cost)], start, end, evaluation)
        closing_marks[(candidate,cost)][period(sim.last_tick['time_msc'])] = account_mark(sim)
        results.append({'candidate': candidate, 'cost': cost,
            'runner_version': '020', 'metric_contract': METRIC_VERSION,
            'peak_tick_equity': sim.peak_tick_equity,
            'training_start': datetime.fromtimestamp(bound(start)/1000,timezone.utc).isoformat(),
            'training_end_exclusive': datetime.fromtimestamp(bound(end)/1000,timezone.utc).isoformat(),
            **aggregates, 'metrics': metrics, 'trades': sim.trades,
            'period_closing_marks': closing_marks[(candidate,cost)],
            'observed_ticks_by_quarter': observed, 'warmup_hours': len(warmup_hours),
            'evaluation_start_ms': evaluation, 'reconciled': True})
    return results


def account_mark(sim):
    return {'time_msc': sim.last_tick['time_msc'], 'bid': sim.last_tick['bid'],
            'ask': sim.last_tick['ask'], 'balance': sim.balance, 'equity': sim.last_equity,
            'position': vars(sim.position).copy() if sim.position is not None else None}


def selection_rows(reports):
    fields = ('candidate','cost','training_start','training_end_exclusive','years','quarters',
              'closed_trades','net_winning_trade_sum','net_losing_trade_sum','max_tick_drawdown')
    return [{k: row[k] for k in fields} for row in reports]


def run(destination):
    destination = Path(destination)
    ledger = verify(destination)
    output = destination/'run'
    output.mkdir(exist_ok=False)  # A partial run may not be silently repeated.
    ledger_hash = sha256(destination/'ledger.json')
    scenarios, choices, selected_tests = {}, {}, []
    for fold, (_, test_year) in FOLDS.items():
        training = replay_window(ledger, ledger['windows'][f'{fold}-training'])
        bindings = {}
        for row in training:
            name = f'{fold}-training-{row["candidate"]}-{row["cost"]}.json'
            write_json(output/name, {'ledger_sha256': ledger_hash, 'synthetic': ledger['synthetic'], **row})
            bindings[name] = sha256(output/name)
            scenarios[name] = bindings[name]
        choice = select_fold(selection_rows(training), fold)
        choice.update(training_report_bindings=bindings, ledger_sha256=ledger_hash, synthetic=ledger['synthetic'],
                      runner_version='020', metric_contract=METRIC_VERSION)
        selection = output/f'{fold}-selection.json'
        write_json(selection, choice)  # Mandatory lock precedes any test replay.
        choices[selection.name] = sha256(selection)
        tests = replay_window(ledger, ledger['windows'][f'{fold}-test'])
        if sha256(selection) != choices[selection.name]:
            raise ValueError('Locked training choice changed during test')
        for row in tests:
            name = f'{fold}-test-{row["candidate"]}-{row["cost"]}.json'
            write_json(output/name, {'ledger_sha256': ledger_hash, 'selection_sha256': choices[selection.name],
                                    'synthetic': ledger['synthetic'], **row})
            scenarios[name] = sha256(output/name)
        for cost in COSTS:
            metric = next(r['metrics'] for r in tests if r['candidate'] == choice['selected'] and r['cost'] == cost) \
                if choice['selected'] != 'CASH' else {'net_return': 0, 'net_pnl': 0, 'closed_trades': 0, 'max_tick_drawdown': 0}
            passed = metric['net_return'] > 0 and metric['closed_trades'] >= 20 and metric['max_tick_drawdown'] <= .10
            selected_tests.append({'fold': fold,'test_year': test_year,'candidate': choice['selected'],
                                   'cost': cost,'metrics': metric,'positive_edge_screen_passed': passed})
    if len(scenarios) != 40:
        raise ValueError('Declared forty-scenario budget differs')
    # Detect changed bytes/code during the run before reporting completion.
    verify(destination)
    for name, digest in {**scenarios, **choices}.items():
        if sha256(output/name) != digest:
            raise ValueError('Report or selection changed before completion')
    result = {'kind': 'completed_chronological_replay_020', 'ledger_sha256': ledger_hash,
        'runner_version': '020', 'metric_contract': METRIC_VERSION,
        'synthetic': ledger['synthetic'], 'status': 'synthetic_software_check_only' if ledger['synthetic'] else 'retrospective_research',
        'scenario_bindings': scenarios, 'selection_bindings': choices, 'selected_tests': selected_tests,
        'historical_positive_edge_screen_passed': not ledger['synthetic'] and all(r['positive_edge_screen_passed'] for r in selected_tests),
        'market_profitability_established': False, 'demo_execution_ready': False,
        'capital_restarts_not_concatenated': True}
    write_json(output/'summary.json', result)
    return result
