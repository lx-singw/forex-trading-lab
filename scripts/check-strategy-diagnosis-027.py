"""Independent Fraction accounting and causal log attribution of every 027 trade."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import csv
import json
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/strategy-diagnosis-027.py'))
ledger = API['verify']()
sha, write = API['sha'], API['write']
path = ROOT/'reports/strategy-diagnosis-027.json'
assert sha(path) == path.with_suffix('.sha256').read_text().strip()
result = json.loads(path.read_text())
assert result['ledger_sha256'] == sha(ROOT/'reports/strategy-diagnosis-027-ledger.json')
assert len(result['scenarios']) == 30


def number(value):
    return Fraction(str(value))


def equal(actual, expected, tolerance=1e-8):
    assert math.isfinite(actual) and abs(number(actual)-expected) <= number(tolerance), (actual, float(expected))


def ms(text):
    d = datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)
    delta = d-datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days*86400000+delta.seconds*1000+delta.microseconds//1000


checked = decisions_checked = withheld_checks = 0
for spec, output in zip(ledger['scenarios'], result['scenarios'], strict=True):
    report = json.loads((ROOT/('reports/comparison-008-'+spec['id']+'.json')).read_text())
    assert output['scenario'] == spec['id']
    assert len(output['trades_detail']) == len(report['trades'])
    config = spec['config']
    counts = Counter()
    signals = Counter()
    for d in report['flat_account_decisions']:
        if spec['candidate'] == 'C04':
            f = d['features']
            mode = 'unavailable' if 'selected_mode' not in f else ('trend' if f['efficiency_ratio'] >= .35 else 'range' if f['efficiency_ratio'] <= .20 else 'neutral')
            assert mode == f.get('selected_mode', 'unavailable')
        else:
            mode = {'C00': 'sma20_50', 'C01': 'sma50_200', 'C02': 'breakout', 'C03': 'range'}[spec['candidate']]
        counts[mode] += 1
        if d['side']:
            signals[mode] += 1
        decisions_checked += 1
    assert output['branch_decisions'] == dict(counts) and output['branch_signals'] == dict(signals)
    assert output['reason_counts'] == dict(Counter(d['reason'] for d in report['flat_account_decisions']))
    grouped = defaultdict(list)
    prev = None
    streak = longest = 0
    for t, r in zip(report['trades'], output['trades_detail'], strict=True):
        vol = number(t['lots'])*number(config['contract_size'])
        risk = abs(number(t['entry'])-number(t['stop']))*vol
        gross = t['side']*(number(t['exit'])-number(t['entry']))*vol
        net = gross-number(t['commission'])+number(t['swap'])
        equal(t['gross_pnl'], gross)
        equal(t['commission'], number(config['commission_per_lot_round_turn'])*number(t['lots']))
        equal(t['net_pnl'], net)
        equal(r['initial_cash_risk'], risk)
        for key, value in (('gross_r', gross/risk), ('net_r', net/risk),
                           ('commission_r', number(t['commission'])/risk),
                           ('financing_debit_r', -number(t['swap'])/risk)):
            equal(r[key], value)
        hour = ms(t['opened'])//3600000*3600000
        matches = [(i, d) for i, d in enumerate(report['flat_account_decisions'])
                   if d['hour_start_ms'] == hour and d['side'] == t['side']
                   and abs(number(d['stop_distance'])-risk/vol) <= number(1e-10)]
        status = 'matched' if len(matches) == 1 else 'missing' if not matches else 'ambiguous'
        assert r['match_status'] == status
        if status == 'matched':
            i, d = matches[0]
            assert r['decision_index'] == i and r['features'] == d['features']
            assert r['decision_reason'] == d['reason']
            expected_mode = d['features']['selected_mode'] if spec['candidate'] == 'C04' else next(iter(counts))
            assert r['branch'] == expected_mode
            # Withhold future decision logs; the causal entry match must survive.
            prefix = [q for q in report['flat_account_decisions'] if q['hour_start_ms'] <= hour]
            prefix_matches = [q for q in prefix if q['hour_start_ms'] == hour and q['side'] == t['side']
                              and abs(number(q['stop_distance'])-risk/vol) <= number(1e-10)]
            assert prefix_matches == [d]
            withheld_checks += 1
        else:
            assert r['branch'] == 'unattributed' and r['decision_index'] is None
        rapid = prev is not None and 0 <= ms(t['opened'])-ms(prev['closed']) <= 3600000
        assert r['rapid_reentry'] == rapid
        assert r['rapid_after_loss'] == (rapid and prev['net_pnl'] < 0)
        assert r['rapid_same_side'] == (rapid and prev['side'] == t['side'])
        streak = streak+1 if t['net_pnl'] < 0 else 0
        longest = max(longest, streak)
        equal(r['holding_hours'], Fraction(ms(t['closed'])-ms(t['opened']), 3600000))
        beyond = max(Fraction(0), t['side']*(number(t['stop'])-number(t['exit']))) if t['reason'] == 'stop_tick' else Fraction(0)
        equal(r['stop_fill_overshoot_dollars'], beyond*vol)
        quote_beyond = max(Fraction(0), beyond-number(config['slippage_pips'])*number(.0001))
        equal(r['observed_quote_overshoot_pips'], quote_beyond/number(.0001))
        grouped[r['branch']].append(r)
        checked += 1
        prev = t
    assert output['longest_loss_streak'] == longest
    assert output['trades'] == report['metrics']['closed_trades']
    for field in ('net_pnl', 'commission', 'swap'):
        equal(output[field], sum((number(t[field]) for t in report['trades']), Fraction(0)))
    for mode, values in grouped.items():
        group = output['branches'][mode]
        assert group['trades'] == len(values)
        equal(group['net_pnl'], sum((number(r['net_pnl']) for r in values), Fraction(0)))
        equal(group['mean_net_r'], sum((number(r['net_r']) for r in values), Fraction(0))/len(values))
    if output['trades']:
        equal(output['mean_net_r'], sum((number(r['net_r']) for r in output['trades_detail']), Fraction(0))/output['trades'])

scenarios = {r['scenario']: r for r in result['scenarios']}
assert len(result['cost_path_comparisons']) == 15
for pair in result['cost_path_comparisons']:
    a, b = (scenarios[pair[k]] for k in ('base_scenario', 'adverse_scenario'))
    ka, kb = ({(t['opened'], t['side']) for t in r['trades_detail']} for r in (a, b))
    assert pair['shared_entries'] == len(ka & kb)
    assert pair['base_only_entries'] == len(ka-kb) and pair['adverse_only_entries'] == len(kb-ka)
    equal(pair['net_pnl_difference'], number(b['net_pnl'])-number(a['net_pnl']))
with (ROOT/'reports/strategy-diagnosis-027-table.csv').open(newline='') as f:
    table = list(csv.DictReader(f))
assert [r['scenario'] for r in table] == [s['id'] for s in ledger['scenarios']]
for row in table:
    for key, value in row.items():
        if key != 'scenario':
            equal(float(value), number(scenarios[row['scenario']][key]))
write(ROOT/'reports/strategy-diagnosis-027-checks.json', dict(
    kind='independent_fraction_diagnosis_check_027', passed=True,
    output_sha256=sha(path), table_sha256=sha(ROOT/'reports/strategy-diagnosis-027-table.csv'),
    ledger_sha256=sha(ROOT/'reports/strategy-diagnosis-027-ledger.json'),
    scenarios_checked=30, cost_pairs_checked=15, trades_checked=checked,
    decisions_checked=decisions_checked, future_log_withholding_checks=withheld_checks,
    prefix_check_limit='Attribution stability, not newly reconstructed signal causality',
    quote_rows_read=0, new_strategy_runs=0, annual_eligible=False, orders_available=False))
print(json.dumps(dict(passed=True, trades_checked=checked, decisions_checked=decisions_checked,
                     future_log_withholding_checks=withheld_checks)))
