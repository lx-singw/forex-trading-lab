"""Training-only selection for the frozen 009 protocol; no market or broker I/O.

Inputs are reconciled training aggregates, not test-year performance. Producing
those aggregates from reviewed data and freezing their provenance is the
chronological runner's responsibility. This module alone cannot approve data.
"""
import hashlib
import json
import math

from .strategies import CANDIDATES

FOLDS = {'A': (2020, 2022), 'B': (2021, 2023)}
COSTS = ('base', 'adverse')


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Expected finite numeric statistic')
    return value


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError('Expected nonnegative integer count')
    return value


def validate(row, start, end):
    if (row['training_start'] != f'{start}-01-01T00:00:00+00:00'
            or row['training_end_exclusive'] != f'{end}-01-01T00:00:00+00:00'):
        raise ValueError('Training bounds mismatch; test/future data prohibited')
    years = row['years']
    quarters = row['quarters']
    if set(years) != {str(y) for y in range(start, end)} or set(quarters) != {
            f'{y}-Q{q}' for y in range(start, end) for q in range(1, 5)}:
        raise ValueError('Missing or future calendar periods')
    equity, total, trades = 10000.0, 0.0, 0
    annual_returns = []
    for y in range(start, end):
        year = years[str(y)]
        pnl = number(year['net_pnl'])
        if not math.isclose(number(year['starting_equity']), equity, abs_tol=1e-8, rel_tol=1e-10) or equity <= 0:
            raise ValueError('Annual equity does not reconcile')
        quarter_pnl = sum(number(quarters[f'{y}-Q{q}']) for q in range(1, 5))
        if not math.isclose(pnl, quarter_pnl, abs_tol=1e-8, rel_tol=1e-10):
            raise ValueError('Quarter/year P&L does not reconcile')
        annual_returns.append(pnl / equity)
        equity += pnl
        total += pnl
        trades += count(year['closed_trades'])
    gross_wins = number(row['net_winning_trade_sum'])
    gross_losses = number(row['net_losing_trade_sum'])
    if gross_wins < 0 or gross_losses > 0 or not math.isclose(gross_wins + gross_losses, total, abs_tol=1e-8, rel_tol=1e-10):
        raise ValueError('Trade/year P&L does not reconcile')
    if count(row['closed_trades']) != trades:
        raise ValueError('Annual trade count does not reconcile')
    drawdown = number(row['max_tick_drawdown'])
    if drawdown < 0:
        raise ValueError('Negative drawdown')
    # A gap can produce drawdown above 100%; reject for selection, not as invalid data.
    reasons = []
    if any(r <= 0 for r in annual_returns): reasons.append('nonpositive_year')
    if trades < 60 or any(years[str(y)]['closed_trades'] < 20 for y in range(start, end)):
        reasons.append('insufficient_trades')
    if sum(v > 0 for v in quarters.values()) < 5: reasons.append('insufficient_positive_quarters')
    profit_factor = gross_wins / -gross_losses if gross_losses < 0 else None
    if profit_factor is None or profit_factor < 1.10: reasons.append('profit_factor_below_gate_or_undefined')
    if drawdown > .10: reasons.append('drawdown_above_gate')
    return {'qualified': not reasons, 'reasons': reasons, 'profit_factor': profit_factor,
            'worst_annual_return': min(annual_returns)}


def select_fold(rows, fold):
    """Require all five candidates at both costs; never replace missing runs with cash."""
    if fold not in FOLDS:
        raise ValueError('Unknown fold')
    start, end = FOLDS[fold]
    expected = {(candidate, cost) for candidate in CANDIDATES for cost in COSTS}
    keys = [(row['candidate'], row['cost']) for row in rows]
    if len(keys) != 10 or set(keys) != expected:
        raise ValueError('Exactly ten unique training scenarios are required')
    checked = {(r['candidate'], r['cost']): validate(r, start, end) for r in rows}
    candidates, qualifiers = {}, []
    for candidate in CANDIDATES:
        results = {cost: checked[(candidate, cost)] for cost in COSTS}
        qualified = all(r['qualified'] for r in results.values())
        score = results['adverse']['worst_annual_return']
        candidates[candidate] = {'qualified': qualified, 'score': score, 'costs': results}
        if qualified:
            qualifiers.append((-score, candidate))
    selected = min(qualifiers)[1] if qualifiers else 'CASH'
    # Sorting ensures input order cannot influence the choice or evidence hash.
    canonical = json.dumps(sorted(rows, key=lambda r: (r['candidate'], r['cost'])),
                           sort_keys=True, allow_nan=False, separators=(',', ':'))
    return {'fold': fold, 'test_year': end, 'selected': selected, 'candidates': candidates,
            'training_inputs_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
            'selection_only_not_data_or_execution_approval': True, 'demo_execution_ready': False}
