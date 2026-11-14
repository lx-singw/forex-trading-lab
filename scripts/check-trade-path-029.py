"""Independent witness membership/Fraction values and preselected full paths."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/trade-path-029.py'))
BASE = API['API']
sha, write, sealed = API['sha'], API['write'], API['sealed']


def ms(text):
    dt = datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)
    delta = dt-datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days*86400000+delta.seconds*1000+delta.microseconds//1000


def fraction(value):
    return Fraction(str(value))


def near(actual, expected, tolerance=1e-8):
    assert abs(fraction(actual)-expected) <= fraction(tolerance), (actual, float(expected))


def financed(trade, config, time_msc):
    day = datetime.fromisoformat(trade['opened']).astimezone(timezone.utc).date()
    end = datetime.fromtimestamp(time_msc/1000, timezone.utc).date()
    rate = config['swap_long_per_lot'] if trade['side'] == 1 else config['swap_short_per_lot']
    units = 0
    while day < end:
        weekday = day.weekday()
        units += 0 if weekday >= 5 else 3 if weekday == config['triple_swap_weekday'] else 1
        day += timedelta(days=1)
    return fraction(rate)*fraction(trade['lots'])*units


class Reference:
    def __init__(self, t, f, config):
        self.t, self.f, self.c = t, f, config
        self.swap, self.previous_day, self.count = 0.0, None, 0
        self.risk = abs(t['entry']-t['stop'])*t['lots']*config['contract_size']
        self.witnesses = {}

    def step(self, tick):
        t, c, seq = self.t, self.c, tick['sequence']
        day = datetime.fromtimestamp(tick['time_msc']/1000, timezone.utc).date()
        if self.previous_day is not None:
            old = self.previous_day
            while old < day:
                weekday = old.weekday()
                units = 0 if weekday >= 5 else 3 if weekday == c['triple_swap_weekday'] else 1
                rate = c['swap_long_per_lot'] if t['side'] > 0 else c['swap_short_per_lot']
                self.swap += rate*t['lots']*units
                old += timedelta(days=1)
        self.previous_day = day
        raw = tick['bid'] if t['side'] > 0 else tick['ask']
        price = raw-t['side']*c['slippage_pips']*.0001
        if seq == self.f['exit_sequence']:
            price = t['exit']
        value = t['side']*(price-t['entry'])*t['lots']*c['contract_size']-t['commission']+self.swap
        if 'maximum' not in self.witnesses or value > self.witnesses['maximum'][1]:
            self.witnesses['maximum'] = (seq, value)
        if 'minimum' not in self.witnesses or value < self.witnesses['minimum'][1]:
            self.witnesses['minimum'] = (seq, value)
        for key, hit in (('positive', value > 0), ('half_r', value >= .5*self.risk),
                         ('one_r', value >= self.risk), ('stop_region', t['side']*(raw-t['stop']) <= 0)):
            if hit and key not in self.witnesses:
                self.witnesses[key] = (seq, value)
        if seq == self.f['exit_sequence']:
            self.witnesses['endpoint'] = (seq, value)
        self.count += 1


def main():
    ledger = API['verify']()
    witness_count = endpoint_count = full_count = full_quotes = 0
    sample_counts = {}
    for sample in BASE['SAMPLES']:
        paths = sealed(ROOT/f'reports/trade-path-029-{sample}.json')
        assert paths['ledger_sha256'] == sha(API['LEDGER'])
        pending = defaultdict(list)
        refs = []
        for s in [s for s in ledger['scenarios'] if s['sample'] == sample]:
            original = sealed(ROOT/f'reports/strategy-experiment-028-{s["id"]}.json')
            extracted = next(r for r in paths['scenarios'] if r['scenario'] == s['id'])
            assert len(original['trades']) == len(extracted['trades'])
            for i, (t, f, row) in enumerate(zip(original['trades'], original['fill_lineage'], extracted['trades'], strict=True)):
                assert row['trade_index'] == i and row['entry_sequence'] == f['entry_sequence'] and row['exit_sequence'] == f['exit_sequence']
                assert row['quote_count'] == f['exit_sequence']-f['entry_sequence']+1
                for key, w in row['witnesses'].items():
                    pending[w['sequence']].append((key, w, t, f, s['config']))
                if i in ledger['independent_full_path_indices'][s['id']]:
                    refs.append((Reference(t, f, s['config']), row))
        read = 0
        for tick in BASE['read_ticks'](ROOT/BASE['SAMPLES'][sample][0]):
            seq = tick['sequence']
            assert seq == read
            for key, w, t, f, c in pending.pop(seq, []):
                assert w['time_msc'] == tick['time_msc'] and w['bid'] == tick['bid'] and w['ask'] == tick['ask']
                assert f['entry_sequence'] <= seq <= f['exit_sequence']
                price = fraction(tick['bid'] if t['side'] == 1 else tick['ask'])-t['side']*fraction(c['slippage_pips'])*fraction(.0001)
                if seq == f['exit_sequence']:
                    assert ms(t['closed']) == tick['time_msc']
                    if t['reason'] == 'target_tick':
                        price = fraction(t['target'])
                    near(t['exit'], price, 1e-10)
                accrued = financed(t, c, tick['time_msc'])
                value = t['side']*(price-fraction(t['entry']))*fraction(t['lots'])*fraction(c['contract_size'])-fraction(t['commission'])+accrued
                risk = abs(fraction(t['entry'])-fraction(t['stop']))*fraction(t['lots'])*fraction(c['contract_size'])
                near(w['liquidation_price'], price, 1e-10)
                near(w['net_pnl'], value)
                near(w['net_r'], value/risk)
                near(w['accrued_swap'], accrued)
                if key == 'endpoint':
                    near(t['net_pnl'], value)
                    near(t['swap'], accrued)
                    endpoint_count += 1
                witness_count += 1
            for ref, _ in refs:
                if ref.f['entry_sequence'] <= seq <= ref.f['exit_sequence']:
                    ref.step(tick)
            read += 1
            if read % 1000000 == 0:
                print(json.dumps(dict(independent_sample=sample, ticks=read)), flush=True)
        assert not pending and read == ledger['datasets'][sample]['ticks']
        for ref, row in refs:
            assert ref.count == row['quote_count']
            assert set(ref.witnesses) == set(row['witnesses'])
            for key, (seq, value) in ref.witnesses.items():
                assert seq == row['witnesses'][key]['sequence'], (row['trade_index'], key)
                near(row['witnesses'][key]['net_pnl'], fraction(value))
            full_count += 1
            full_quotes += ref.count
        sample_counts[sample] = read
    assert endpoint_count == 266 and full_count == sum(map(len, ledger['independent_full_path_indices'].values()))
    summary = sealed(ROOT/'reports/trade-path-029-summary.json')
    assert len(summary['scenarios']) == 30
    for row in summary['scenarios']:
        data = sealed(ROOT/f'reports/trade-path-029-{row["sample"]}.json')
        path = next(r for r in data['scenarios'] if r['scenario'] == row['scenario'])
        stops = [t for t in path['trades'] if t['exit_reason'] == 'stop_tick']
        assert row['stops'] == len(stops)
        for field, threshold in (('stops_prior_positive', 'positive'), ('stops_prior_half_r', 'half_r'), ('stops_prior_one_r', 'one_r')):
            assert row[field] == sum(threshold in t['witnesses'] and t['witnesses'][threshold]['sequence'] < t['exit_sequence'] for t in stops)
        near(row['net_pnl'], sum((fraction(t['net_pnl']) for t in path['trades']), Fraction(0)))
    write(ROOT/'reports/trade-path-029-checks.json', dict(kind='independent_path_witness_check_029', passed=True,
        ledger_sha256=sha(API['LEDGER']), summary_sha256=sha(ROOT/'reports/trade-path-029-summary.json'),
        table_sha256=sha(ROOT/'reports/trade-path-029-table.csv'), scenarios_checked=30,
        endpoints_checked=endpoint_count, witnesses_checked=witness_count,
        preselected_full_paths_checked=full_count, full_path_quotes_checked=full_quotes,
        sample_source_ticks_checked=sample_counts, new_strategy_runs=0, annual_eligible=False, orders_available=False))
    print(json.dumps(dict(passed=True, endpoints=endpoint_count, witnesses=witness_count, full_paths=full_count)))


if __name__ == '__main__':
    main()
