"""Independent quote/fill/protection accounting; never runs a strategy."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from forex_demo_lab import challenger_chronology_093 as wf
from forex_demo_lab.execution_audit import compare

accounting = runpy.run_path(str(ROOT / 'scripts/check-exit-experiment-030.py'))
arithmetic = runpy.run_path(str(ROOT / 'scripts/check-walk-forward-014.py'))
equal = accounting['equal']


def check_mark(account, mark, tick):
    assert mark['time_msc'] == tick['time_msc']
    equal(mark['bid'], tick['bid']); equal(mark['ask'], tick['ask'])
    equal(mark['balance'], account.cash); equal(mark['equity'], account.last_equity)
    position = mark['position']
    if account.active is None:
        assert position is None
    else:
        assert position is not None
        trade = account.trades[account.active]
        assert position['side'] == trade['side'] and position['opened'] == trade['opened']
        for name in ('lots', 'entry', 'target', 'entry_commission'):
            equal(position[name], trade[name])
        equal(position['stop'], account.level)
        equal(position['swap'], account.swap[account.active])


def check_window(ticks, rows, configs, window):
    if not __debug__:
        raise RuntimeError('Independent checker requires Python assertions enabled')
    expected = {(c, k) for c in wf.CANDIDATES for k in wf.COSTS}
    assert len(rows) == 10 and {(r['candidate'], r['cost']) for r in rows} == expected
    start = window['evaluation_start_ms']
    accounts = []
    for r in rows:
        assert r['synthetic'] is True and r['version'] == wf.VERSION and r['metric_contract'] == wf.METRIC_VERSION
        assert r['evaluation_start_ms'] == start and r['warmup_hours'] == 201
        assert r['training_start'] == datetime.fromtimestamp(wf.bound(window['start_year']) / 1000, timezone.utc).isoformat()
        assert r['training_end_exclusive'] == datetime.fromtimestamp(wf.bound(window['end_year']) / 1000, timezone.utc).isoformat()
        for name, value in wf.APPROVALS.items():
            assert r.get(name) is value
        cfg = configs[r['cost']]
        assert len(r['fill_lineage']) == len(r['trades'])
        assert [f['trade_index'] for f in r['fill_lineage']] == list(range(len(r['trades'])))
        assert len({f['entry_sequence'] for f in r['fill_lineage']}) == len(r['trades'])
        assert len({f['exit_sequence'] for f in r['fill_lineage']}) == len(r['trades'])
        for t, f in zip(r['trades'], r['fill_lineage'], strict=True):
            assert f['entry_sequence'] <= f['exit_sequence']
            assert int(datetime.fromisoformat(t['opened']).timestamp() * 1000) >= start
            q = lambda v: Fraction(str(v))
            gross = t['side'] * (q(t['exit']) - q(t['entry'])) * q(t['lots']) * q(cfg['contract_size'])
            equal(t['gross_pnl'], float(gross))
            equal(t['commission'], t['lots'] * cfg['commission_per_lot_round_turn'])
            equal(t['entry_commission'], t['commission'] / 2)
            equal(t['net_pnl'], float(gross - q(t['commission']) + q(t['swap'])))
        accounts.append(accounting['Account'](r, dict(candidate=r['candidate'], config=cfg), start))
    decisions = [{d['hour_start_ms']: d for d in r['flat_account_decisions']} for r in rows]
    for r, d in zip(rows, decisions, strict=True):
        assert len(d) == len(r['flat_account_decisions'])
        assert all(type(ms) is int and start <= ms < wf.bound(window['end_year']) for ms in d)
    current, history, previous_period, last = None, [], None, None
    marks = [{} for _ in rows]
    warmup, observed, features, count = set(), {}, 0, 0
    seen_entries, seen_exits = [set() for _ in rows], [set() for _ in rows]
    seen_decisions = [set() for _ in rows]
    for tick in ticks:
        assert tick['sequence'] == count and window['warmup_start_ms'] <= tick['time_msc'] < wf.bound(window['end_year'])
        assert last is None or tick['time_msc'] >= last['time_msc']
        instant = tick['time_msc']
        key = wf.period(instant) if instant >= start else None
        if instant < start:
            warmup.add(instant // wf.HOUR)
        else:
            assert len(warmup) == 201
            observed[key] = observed.get(key, 0) + 1
        if previous_period is not None and key != previous_period:
            for i, a in enumerate(accounts):
                check_mark(a, rows[i]['period_closing_marks'][previous_period], last)
        hour = instant // wf.HOUR
        new_hour = current is None or hour != current['hour']
        if new_hour:
            if current is not None:
                history.append(current); history = history[-201:]
                for a in accounts:
                    a.complete_hour(current['hour'])
            for i, r in enumerate(rows):
                if hour * wf.HOUR in decisions[i]:
                    assert instant >= start and len(history) == 201 and history[-1]['hour'] == hour - 1
                    assert accounts[i].active is None
                    seen_decisions[i].add(hour * wf.HOUR)
                    if r['candidate'] != 'C00':
                        accounting['feature_check'](decisions[i][hour * wf.HOUR],
                            {'C07': 'C05', 'C08': 'C06'}.get(r['candidate'], r['candidate']), history, configs[r['cost']])
                        features += 1
            current = dict(hour=hour, high=tick['bid'], low=tick['bid'], close=tick['bid'])
        for i, a in enumerate(accounts):
            if count in a.entries:
                index = a.entries[count]
                assert new_hour and hour * wf.HOUR in decisions[i]
                assert decisions[i][hour * wf.HOUR]['side'] == a.trades[index]['side']
                equal(decisions[i][hour * wf.HOUR]['stop_distance'], a.protection[index]['initial_distance'])
                assert int(datetime.fromisoformat(a.trades[index]['opened']).timestamp() * 1000) == instant
                seen_entries[i].add(index)
            if count in a.exits:
                index = a.exits[count]
                assert int(datetime.fromisoformat(a.trades[index]['closed']).timestamp() * 1000) == instant
                seen_exits[i].add(index)
            a.step(tick, new_hour)
            if key is not None:
                marks[i][key] = a.last_equity
        current['high'] = max(current['high'], tick['bid'])
        current['low'] = min(current['low'], tick['bid']); current['close'] = tick['bid']
        last, previous_period, count = tick, key, count + 1
    assert current is not None and previous_period is not None
    boundary_positions = 0
    for i, a in enumerate(accounts):
        r = rows[i]
        if a.active is not None:
            index = a.active
            assert r['fill_lineage'][index]['exit_sequence'] == count - 1
            assert int(datetime.fromisoformat(a.trades[index]['closed']).timestamp() * 1000) == last['time_msc']
            seen_exits[i].add(index)
        a.finish(current['hour'])
        marks[i][previous_period] = a.last_equity
        check_mark(a, r['period_closing_marks'][previous_period], last)
        assert set(r['period_closing_marks']) == set(marks[i])
        assert seen_entries[i] == seen_exits[i] == set(range(len(a.trades)))
        assert seen_decisions[i] == set(decisions[i])
        assert r['observed_ticks_by_quarter'] == observed
        equal(r['peak_tick_equity'], a.peak)
        equal(r['max_tick_drawdown'], a.drawdown)
        equal(r['metrics']['net_return'], (a.cash - configs[r['cost']]['initial_equity']) / configs[r['cost']]['initial_equity'])
        assert r['closed_trades'] == r['metrics']['closed_trades'] == len(a.trades)
        equal(r['net_winning_trade_sum'], sum(t['net_pnl'] for t in a.trades if t['net_pnl'] > 0))
        equal(r['net_losing_trade_sum'], sum(t['net_pnl'] for t in a.trades if t['net_pnl'] < 0))
        previous = configs[r['cost']]['initial_equity']
        assert set(r['years']) == {str(y) for y in range(window['start_year'], window['end_year'])}
        assert set(r['quarters']) == {f'{y}-Q{q}' for y in range(window['start_year'], window['end_year']) for q in range(1, 5)}
        for y in range(window['start_year'], window['end_year']):
            opening = previous
            for q in range(1, 5):
                key = f'{y}-Q{q}'; closing = marks[i].get(key, previous)
                equal(r['quarters'][key], closing - previous); previous = closing
            equal(r['years'][str(y)]['starting_equity'], opening)
            equal(r['years'][str(y)]['net_pnl'], previous - opening)
            assert r['years'][str(y)]['closed_trades'] == sum(datetime.fromisoformat(t['closed']).year == y for t in a.trades)
        equal(previous, a.cash)
        boundary_positions += sum(m['position'] is not None for m in r['period_closing_marks'].values())
    return dict(ticks_checked=count, equity_marks_checked=sum(a.marks for a in accounts),
        closed_bar_features_checked=features, arms_checked=sum(a.arms_checked for a in accounts),
        sizing_checked=sum(a.sizing_checked for a in accounts), boundary_positions_checked=boundary_positions)


def check(destination):
    if not __debug__:
        raise RuntimeError('Independent checker requires Python assertions enabled')
    destination = Path(destination)
    ledger = wf.verify(destination)
    summary = wf.load(destination / 'run/summary.json')
    assert summary['kind'] == 'completed_challenger_093' and summary['version'] == wf.VERSION
    assert summary['synthetic'] is True and summary['metric_contract'] == wf.METRIC_VERSION
    assert summary['ledger_sha256'] == wf.sha256(destination / 'ledger.json')
    for k, v in wf.APPROVALS.items():
        assert summary.get(k) is v
    expected = {f'{f}-{role}-{c}-{k}.json' for f in wf.FOLDS for role in ('training', 'test') for c in wf.CANDIDATES for k in wf.COSTS}
    assert set(summary['scenario_bindings']) == expected
    assert set(summary['selection_bindings']) == {'A-selection.json', 'B-selection.json'}
    assert len(summary['selected_tests']) == 4
    assert {(r['fold'], r['cost']) for r in summary['selected_tests']} == {(f, k) for f in wf.FOLDS for k in wf.COSTS}
    assert summary['capital_restarts_not_concatenated'] is True
    for name, digest in {**summary['scenario_bindings'], **summary['selection_bindings']}.items():
        assert wf.sha256(destination / 'run' / name) == digest
    rows = {name: wf.load(destination / 'run' / name) for name in expected}
    for name, row in rows.items():
        fold, role, candidate, cost = name[:-5].split('-')
        assert row['candidate'] == candidate and row['cost'] == cost
    checks = {}
    for fold in wf.FOLDS:
        names = {f'{fold}-training-{c}-{k}.json' for c in wf.CANDIDATES for k in wf.COSTS}
        choice = wf.load(destination / 'run' / f'{fold}-selection.json')
        assert choice['version'] == wf.VERSION and choice['metric_contract'] == wf.METRIC_VERSION
        assert choice['ledger_sha256'] == summary['ledger_sha256']
        for k, v in wf.APPROVALS.items():
            assert choice.get(k) is v
        assert choice['training_report_bindings'] == {n: summary['scenario_bindings'][n] for n in names}
        recomputed = wf.select_fold(wf.selection_rows([rows[n] for n in sorted(names)]), fold)
        compare({k: choice[k] for k in recomputed}, recomputed, label='training_only_choice')
        for role in ('training', 'test'):
            reports = [rows[f'{fold}-{role}-{c}-{k}.json'] for c in wf.CANDIDATES for k in wf.COSTS]
            for r in reports:
                assert r['ledger_sha256'] == summary['ledger_sha256']
                if role == 'test':
                    assert r['selection_sha256'] == summary['selection_bindings'][f'{fold}-selection.json']
            window = ledger['windows'][fold + '-' + role]
            checks[fold + '-' + role] = check_window(wf.base.window_ticks(ledger, window), reports, ledger['configs'], window)
        for r in (r for r in summary['selected_tests'] if r['fold'] == fold):
            assert r['test_year'] == wf.FOLDS[fold][1] and r['candidate'] == choice['selected'] and r['synthetic'] is True
            metric = rows[f'{fold}-test-{r["candidate"]}-{r["cost"]}.json']['metrics'] if r['candidate'] != 'CASH' \
                else dict(net_return=0, net_pnl=0, closed_trades=0, max_tick_drawdown=0)
            compare(r['metrics'], metric, label='selected_synthetic_metrics')
            assert r['positive_edge_screen_passed'] is wf.screen(metric)
    arithmetic['check'](destination)
    return dict(checks_passed=True, kind='independent_synthetic_challenger_accounting_093',
        scenarios=40, choices=2, window_checks=checks, summary_sha256=wf.sha256(destination / 'run/summary.json'),
        synthetic=True, **wf.APPROVALS)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination', type=Path); p.add_argument('--report', type=Path)
    args = p.parse_args()
    if args.report and args.report.exists():
        raise FileExistsError('Independent check report already exists')
    result = check(args.destination)
    if args.report:
        wf.save(args.report, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'window_checks'}))
