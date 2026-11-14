"""Separate training-only selector; immutable009 numeric screens, no execution."""
import hashlib
import json

from .selection import COSTS, FOLDS, validate

CANDIDATES = ('C00', 'C05', 'C06', 'C07', 'C08')
FIELDS = ('candidate', 'cost', 'training_start', 'training_end_exclusive', 'years',
          'quarters', 'closed_trades', 'net_winning_trade_sum', 'net_losing_trade_sum',
          'max_tick_drawdown')


def selection_rows(reports):
    return [{k: r[k] for k in FIELDS} for r in reports]


def select_fold(rows, fold):
    if fold not in FOLDS or not isinstance(rows, list):
        raise ValueError('Unknown fold or invalid training inputs')
    expected = {(c, k) for c in CANDIDATES for k in COSTS}
    try:
        if (len(rows) != 10 or any(set(r) != set(FIELDS) for r in rows)
                or {(r['candidate'], r['cost']) for r in rows} != expected):
            raise ValueError('Exactly ten unique training-only scenarios required')
        start, end = FOLDS[fold]
        checked = {(r['candidate'], r['cost']): validate(r, start, end) for r in rows}
    except (KeyError, TypeError) as exc:
        raise ValueError('Malformed training inputs') from exc
    candidates, qualifiers = {}, []
    for c in CANDIDATES:
        results = {k: checked[(c, k)] for k in COSTS}
        qualified = all(r['qualified'] for r in results.values())
        score = results['adverse']['worst_annual_return']
        candidates[c] = dict(qualified=qualified, score=score, costs=results)
        if qualified:
            qualifiers.append((-score, c))
    canonical = json.dumps(sorted(rows, key=lambda r: (r['candidate'], r['cost'])),
                           sort_keys=True, allow_nan=False, separators=(',', ':'))
    return dict(fold=fold, test_year=end, selected=min(qualifiers)[1] if qualifiers else 'CASH',
        candidates=candidates, training_inputs_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        selection_only_not_data_or_execution_approval=True, synthetic=True,
        demo_execution_ready=False, orders_available=False)
