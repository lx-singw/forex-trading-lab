"""Independent cash, financing, fill-lineage and full tick-equity reconstruction."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/exit-experiment-030.py'))
sha, write = API['sha'], API['write']
HOUR = 3600000


def equal(a, b, tolerance=1e-8):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance, (a, b)


class Account:
    def __init__(self, report, spec, start):
        self.report, self.config, self.start = report, spec['config'], start
        self.trades = report['trades']
        self.protection = report['protection_lineage']
        assert len(self.protection) == len(self.trades)
        self.protect = spec['candidate'] in ('C07', 'C08')
        self.level = None
        self.armed = False
        self.arms_checked = 0
        self.sizing_checked = 0
        self.entries = {f['entry_sequence']: f['trade_index'] for f in report['fill_lineage']}
        self.exits = {f['exit_sequence']: f['trade_index'] for f in report['fill_lineage']
                      if self.trades[f['trade_index']]['reason'] != 'end_of_sample'}
        assert len(self.entries) == len(self.trades)
        self.cash = self.peak = self.last_equity = self.config['initial_equity']
        self.drawdown = 0.0
        self.active = None
        self.day = None
        self.day_start = self.cash
        self.paused = False
        self.swap = [0.0]*len(self.trades)
        self.curve = []
        self.exposed = False
        self.exposed_bars = 0
        self.marks = 0
        self.last_tick = None

    def pause(self, equity):
        if equity <= self.day_start*(1-self.config['daily_loss_fraction'])+1e-9:
            self.paused = True

    def mark(self, bid, ask):
        value = self.cash
        if self.active is not None:
            t = self.trades[self.active]
            price = bid if t['side'] == 1 else ask
            stop = price <= self.level if t['side'] == 1 else price >= self.level
            target = price >= t['target'] if t['side'] == 1 else price <= t['target']
            if stop or target:
                price = price-t['side']*self.config['slippage_pips']*.0001 if stop else t['target']
            value += t['side']*(price-t['entry'])*t['lots']*self.config['contract_size']
            if stop or target:
                value -= t['lots']*self.config['commission_per_lot_round_turn']/2
        self.peak = max(self.peak, value)
        self.drawdown = max(self.drawdown, (self.peak-value)/self.peak)
        self.pause(value)
        self.last_equity = value
        self.marks += 1

    def complete_hour(self, hour):
        if hour*HOUR >= self.start:
            self.curve.append(dict(time=datetime.fromtimestamp(hour*3600, timezone.utc).isoformat(),
                                   equity=self.last_equity, paused=self.paused))
        if self.exposed:
            self.exposed_bars += 1

    def step(self, tick, new_hour):
        seq, bid, ask = tick['sequence'], tick['bid'], tick['ask']
        day = tick['time_msc']//86400000
        if new_hour:
            self.exposed = self.active is not None
        if day != self.day:
            self.day_start = self.last_equity
            self.paused = False
            if self.day is not None and self.active is not None:
                t = self.trades[self.active]
                rate = self.config['swap_long_per_lot'] if t['side'] == 1 else self.config['swap_short_per_lot']
                for old_day in range(self.day, day):
                    weekday = (old_day+3)%7
                    multiplier = 0 if weekday >= 5 else 3 if weekday == self.config['triple_swap_weekday'] else 1
                    debit = rate*t['lots']*multiplier
                    self.cash += debit
                    self.swap[self.active] += debit
            self.day = day
        self.mark(bid, ask)
        if seq in self.entries:
            assert self.active is None and not self.paused
            self.active = self.entries[seq]
            t = self.trades[self.active]
            p = self.protection[self.active]
            assert p['trade_index'] == self.active
            self.level = p['initial_stop']
            self.armed = False
            risk = abs(t['entry']-self.level)*t['lots']*self.config['contract_size']
            equal(risk, p['initial_risk'])
            equal(abs(t['entry']-self.level), p['initial_distance'], 1e-10)
            equal(t['target'], t['entry']+(t['entry']-self.level)*self.config['reward_risk'], 1e-10)
            estimated = risk+t['lots']*(self.config['commission_per_lot_round_turn']+self.config['slippage_pips']*.0001*self.config['contract_size'])
            assert estimated <= self.cash*self.config['risk_fraction']+1e-8
            margin = t['lots']*t['entry']*self.config['contract_size']/self.config['leverage']
            assert margin+t['entry_commission'] <= self.cash+1e-8
            self.sizing_checked += 1
            equal(t['entry'], (ask if t['side'] == 1 else bid)+t['side']*self.config['slippage_pips']*.0001, 1e-10)
            assert (ask-bid)/.0001 <= self.config['max_spread_pips']+1e-9
            self.cash -= t['entry_commission']
        if self.active is not None:
            self.exposed = True
        if self.active is not None:
            t = self.trades[self.active]
            quote = bid if t['side'] == 1 else ask
            crossed = t['side']*(quote-self.level) <= 0 or t['side']*(quote-t['target']) >= 0
            assert crossed == (seq in self.exits), 'Missing or premature exit'
        if seq in self.exits:
            index = self.exits[seq]
            assert self.active == index
            t = self.trades[index]
            price = bid if t['side'] == 1 else ask
            if t['reason'] == 'stop_tick':
                assert price <= self.level if t['side'] == 1 else price >= self.level
                price -= t['side']*self.config['slippage_pips']*.0001
            else:
                assert t['reason'] == 'target_tick'
                assert price >= t['target'] if t['side'] == 1 else price <= t['target']
                price = t['target']
            equal(t['exit'], price, 1e-10)
            self.close(index)
        self.mark(bid, ask)
        if self.active is not None and self.protect and not self.armed:
            t = self.trades[self.active]
            p = self.protection[self.active]
            quote = bid if t['side'] == 1 else ask
            volume = t['lots']*self.config['contract_size']
            slip = self.config['slippage_pips']*.0001
            net = t['side']*(quote-t['side']*slip-t['entry'])*volume-t['commission']+self.swap[self.active]
            if net >= p['initial_risk']/2:
                arm = p['arm']
                assert arm is not None and arm['sequence'] == seq and arm['time_msc'] == tick['time_msc'], 'Not first eligible quote'
                equal(arm['trigger_net'], net)
                equal(arm['accrued_swap'], self.swap[self.active])
                equal(arm['initial_risk'], p['initial_risk'])
                equal(arm['old_stop'], self.level, 1e-10)
                expected = t['entry']+t['side']*((t['commission']-self.swap[self.active])/volume+slip)
                expected = max(self.level, expected) if t['side']==1 else min(self.level, expected)
                equal(arm['new_stop'], expected, 1e-10)
                assert t['side']*(expected-self.level) >= 0
                assert t['side']*(quote-expected)>0 and t['side']*(t['target']-expected)>0
                self.level = expected
                self.armed = True
                self.arms_checked += 1
        self.last_tick = tick

    def close(self, index):
        t = self.trades[index]
        equal(self.swap[index], t['swap'])
        equal(t['stop'], self.level, 1e-10)
        p = self.protection[index]
        assert (p['arm'] is not None) == self.armed
        if self.armed:
            assert p['arm']['sequence'] < self.report['fill_lineage'][index]['exit_sequence'] or t['reason']=='end_of_sample'
        self.cash += t['gross_pnl']-t['commission']/2
        self.active = None
        self.pause(self.cash)

    def finish(self, hour):
        if self.active is not None:
            index = self.active
            t = self.trades[index]
            assert t['reason'] == 'end_of_sample'
            price = self.last_tick['bid'] if t['side'] == 1 else self.last_tick['ask']
            equal(t['exit'], price-t['side']*self.config['slippage_pips']*.0001, 1e-10)
            self.close(index)
            self.mark(self.last_tick['bid'], self.last_tick['ask'])
        self.complete_hour(hour)
        m = self.report['metrics']
        equal(self.cash-self.config['initial_equity'], m['net_pnl'])
        equal(self.drawdown, m['max_tick_drawdown'], 1e-10)
        assert len(self.curve) == len(self.report['equity'])
        for actual, expected in zip(self.curve, self.report['equity'], strict=True):
            assert actual['time'] == expected['time'] and actual['paused'] == expected['paused']
            equal(actual['equity'], expected['equity'])
        peak, dd = self.config['initial_equity'], 0
        for p in self.curve:
            peak = max(peak, p['equity'])
            dd = max(dd, (peak-p['equity'])/peak)
        equal(dd, m['max_close_drawdown'], 1e-10)
        equal(self.exposed_bars/len(self.curve), m['bar_exposure'], 1e-10)


def feature_check(d, candidate, history, config):
    assert len(history) == 201
    closes = [b['close'] for b in history]
    ranges = [max(history[i]['high']-history[i]['low'], abs(history[i]['high']-history[i-1]['close']),
                  abs(history[i]['low']-history[i-1]['close'])) for i in range(len(history)-14, len(history))]
    distance = sum(ranges)/14*2
    equal(d['stop_distance'], distance, 1e-10)
    prior, current = history[-22:-2], history[-21:-1]
    old, new = closes[-2:]
    side = 1 if new > max(b['high'] for b in current) and old <= max(b['high'] for b in prior) else -1 if new < min(b['low'] for b in current) and old >= min(b['low'] for b in prior) else 0
    if not distance:
        side = 0
    if candidate == 'C05':
        tail = closes[-21:]
        path = sum(abs(b-a) for a, b in zip(tail, tail[1:]))
        if path:
            er = abs(tail[-1]-tail[0])/path
            equal(d['features']['efficiency_ratio'], er, 1e-10)
            side = side if er >= .35 else 0
        else:
            side = 0
    else:
        fast, slow = sum(closes[-50:])/50, sum(closes[-200:])/200
        equal(d['features']['sma50'], fast, 1e-10)
        equal(d['features']['sma200'], slow, 1e-10)
        direction = 1 if fast > slow else -1 if fast < slow else 0
        assert d['features']['slow_direction'] == direction
        side = side if side == direction else 0
    assert d['side'] == side


def check_stream(ticks, reports, specs, start):
    accounts = [Account(r, s, start) for r, s in zip(reports, specs, strict=True)]
    decision_maps = [{d['hour_start_ms']: d for d in r['flat_account_decisions']} for r in reports]
    current, history, features_checked, count = None, [], 0, 0
    for tick in ticks:
        assert tick['sequence'] == count
        hour = tick['time_msc']//HOUR
        new_hour = current is None or hour != current['hour']
        if new_hour:
            if current is not None:
                history.append(current)
                history = history[-201:]
                for a in accounts:
                    a.complete_hour(current['hour'])
            for i, spec in enumerate(specs):
                if spec['candidate'] in ('C05', 'C06', 'C07', 'C08') and hour*HOUR in decision_maps[i]:
                    assert history[-1]['hour'] < hour
                    feature_check(decision_maps[i][hour*HOUR], {'C07':'C05','C08':'C06'}.get(spec['candidate'],spec['candidate']), history, spec['config'])
                    features_checked += 1
            current = dict(hour=hour, high=tick['bid'], low=tick['bid'], close=tick['bid'])
        for a in accounts:
            a.step(tick, new_hour)
        current['high'] = max(current['high'], tick['bid'])
        current['low'] = min(current['low'], tick['bid'])
        current['close'] = tick['bid']
        count += 1
        if count % 1000000 == 0:
            print(json.dumps(dict(independent_ticks=count)), flush=True)
    for a in accounts:
        a.finish(current['hour'])
    return dict(ticks_checked=count, equity_marks_checked=sum(a.marks for a in accounts),
                closed_bar_features_checked=features_checked,
                arms_checked=sum(a.arms_checked for a in accounts), sizing_checked=sum(a.sizing_checked for a in accounts))


def synthetic():
    from dataclasses import asdict
    from forex_demo_lab.model import Config
    from forex_demo_lab.exit_experiment_030 import Experiment030Simulator
    cfg = Config()
    base = 1704067200000
    start = base+201*HOUR
    cases = 0
    for candidate in ('C07', 'C08'):
        for side in (1, -1):
            for outcome in ('target', 'stop', 'protect', 'end'):
                flat = 1.125
                jump = flat+side*.125
                ticks = [dict(sequence=i, time_msc=base+i*HOUR,
                              bid=flat if i < 200 else jump,
                              ask=(flat if i < 200 else jump)+.0001) for i in range(202)]
                sim = Experiment030Simulator(cfg, candidate, start)
                for tick in ticks:
                    sim.step_tick(tick)
                assert sim.position is not None
                def append(price):
                    tick = dict(sequence=len(ticks), time_msc=start+len(ticks)-201,
                                bid=price if side==1 else price-.0001,
                                ask=price+.0001 if side==1 else price)
                    ticks.append(tick)
                    sim.step_tick(tick)
                p = sim.position
                if outcome=='stop':
                    append(p.stop-side*.001)
                else:
                    append(p.entry+side*abs(p.entry-p.stop)*.7)
                    assert sim.pending_protection['arm'] is not None
                    if outcome=='target':
                        append(p.target+side*.1)
                    elif outcome=='protect':
                        append(p.stop-side*.001)
                sim.finish()
                report = dict(trades=sim.trades, fill_lineage=sim.fill_lineage,
                              protection_lineage=sim.protection_lineage,
                              metrics=sim.metrics(), flat_account_decisions=sim.decision_log,
                              equity=[p for p in sim.curve if int(datetime.fromisoformat(p['time']).timestamp()*1000) >= start])
                check_stream(ticks, [report], [dict(candidate=candidate, config=asdict(cfg))], start)
                cases += 1
    write(ROOT/'reports/exit-experiment-030-synthetic-checks.json', dict(
        kind='independent_checker_synthetic_preflight_030', passed=True, cases_checked=cases,
        market_quote_rows_read=0, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(synthetic_passed=True, cases=cases)))


def market():
    ledger = API['verify']()
    summary = API['sealed'](ROOT/'reports/exit-experiment-030-summary.json')
    sample_checks, trades_checked, controls = {}, 0, 0
    for sample in API['SAMPLES']:
        specs = [s for s in ledger['scenarios'] if s['sample'] == sample]
        reports = [API['sealed'](ROOT/('reports/exit-experiment-030-'+s['id']+'.json')) for s in specs]
        for s, r in zip(specs, reports, strict=True):
            assert r['ledger_sha256'] == sha(API['LEDGER'])
            for t, p in zip(r['trades'], r['protection_lineage'], strict=True):
                q = lambda value: Fraction(str(value))
                gross = t['side']*(q(t['exit'])-q(t['entry']))*q(t['lots'])*q(s['config']['contract_size'])
                equal(t['gross_pnl'], float(gross))
                equal(t['net_pnl'], float(gross-q(t['commission'])+q(t['swap'])))
                equal(t['commission'], t['lots']*s['config']['commission_per_lot_round_turn'])
                equal(t['target'], t['entry']+(t['entry']-p['initial_stop'])*s['config']['reward_risk'], 1e-10)
                trades_checked += 1
            if s['candidate'] in ('C00', 'C05', 'C06'):
                assert API['control_parity'](r)['passed']
                controls += 1
        ticks = API['read_ticks'](ROOT/API['SAMPLES'][sample][0])
        checked = check_stream(ticks, reports, specs, ledger['datasets'][sample]['evaluation_start_ms'])
        assert checked['ticks_checked'] == ledger['datasets'][sample]['ticks']
        sample_checks[sample] = checked
    assert len(summary['scenarios']) == 30 and controls == 18
    write(ROOT/'reports/exit-experiment-030-checks.json', dict(
        kind='independent_full_tick_equity_check_030', passed=True,
        ledger_sha256=sha(API['LEDGER']), summary_sha256=sha(ROOT/'reports/exit-experiment-030-summary.json'),
        scenarios_checked=30, controls_matching_original=18, trades_checked=trades_checked,
        sample_checks=sample_checks, selection_authorized=False, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(passed=True, controls=18, trades=trades_checked, samples=sample_checks)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('synthetic', 'market'))
    {'synthetic': synthetic, 'market': market}[parser.parse_args().action]()
