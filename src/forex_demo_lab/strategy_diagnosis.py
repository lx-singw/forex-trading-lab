"""Descriptive attribution of frozen trades/decisions; no simulation or trading."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import math

HOUR = 3_600_000


def instant(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('Explicit timestamp offset required')
    delta = dt.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def close(a, b, tolerance=1e-8):
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a, b, rel_tol=0, abs_tol=tolerance):
        raise ValueError('Accounting or geometry mismatch')


def branch(decision, candidate):
    if candidate == 'C04':
        mode = decision['features'].get('selected_mode')
        if mode is None:
            if decision['side']:
                raise ValueError('C04 signal missing branch')
            return 'unavailable'
        er = decision['features'].get('efficiency_ratio')
        if not isinstance(er, (float, int)) or not math.isfinite(er) or not 0 <= er <= 1 + 1e-12:
            raise ValueError('Invalid efficiency ratio')
        expected = 'trend' if er >= .35 else 'range' if er <= .20 else 'neutral'
        if mode != expected or not decision['reason'].startswith('selector_' + mode):
            raise ValueError('Selector branch mismatch')
        if mode == 'neutral' and decision['side']:
            raise ValueError('Neutral branch cannot signal')
        return mode
    return {'C00': 'sma20_50', 'C01': 'sma50_200', 'C02': 'breakout', 'C03': 'range'}[candidate]


def diagnose(report, config, candidate, evaluation_start_ms):
    decisions = report['flat_account_decisions']
    by_hour = defaultdict(list)
    reason_counts, branch_counts, signal_branches = Counter(), Counter(), Counter()
    previous_hour = None
    for i, d in enumerate(decisions):
        hour = d['hour_start_ms']
        if type(hour) is not int or hour % HOUR or hour < evaluation_start_ms:
            raise ValueError('Invalid decision hour')
        if previous_hour is not None and hour < previous_hour:
            raise ValueError('Decision logs out of order')
        if type(d['side']) is not int or d['side'] not in (-1, 0, 1):
            raise ValueError('Invalid decision side')
        if not math.isfinite(d['stop_distance']) or (d['side'] and d['stop_distance'] <= 0):
            raise ValueError('Invalid signal distance')
        mode = branch(d, candidate)
        reason_counts[d['reason']] += 1
        branch_counts[mode] += 1
        if d['side']:
            signal_branches[mode] += 1
            by_hour[hour].append((i, d, mode))
        previous_hour = hour
    rows, used, groups = [], set(), defaultdict(list)
    last_exit = None
    streak = maximum_streak = 0
    for i, t in enumerate(report['trades']):
        for key in ('entry', 'exit', 'stop', 'target', 'lots', 'gross_pnl', 'commission',
                    'entry_commission', 'swap', 'net_pnl'):
            if not math.isfinite(t[key]):
                raise ValueError('Nonfinite trade')
        side, lots = t['side'], t['lots']
        if type(side) is not int or side not in (-1, 1) or lots <= 0 or min(t['entry'], t['exit'], t['stop'], t['target']) <= 0:
            raise ValueError('Invalid trade')
        opened, exited = instant(t['opened']), instant(t['closed'])
        if opened < evaluation_start_ms or exited < opened or (last_exit is not None and opened < last_exit):
            raise ValueError('Warmup, reversed or overlapping trade')
        distance = side * (t['entry'] - t['stop'])
        if distance <= 0:
            raise ValueError('Invalid initial risk')
        close(t['target'], t['entry'] + side * distance * config['reward_risk'], 1e-10)
        gross = side * (t['exit'] - t['entry']) * lots * config['contract_size']
        close(gross, t['gross_pnl'])
        close(t['commission'], lots * config['commission_per_lot_round_turn'])
        close(t['entry_commission'], t['commission'] / 2)
        close(t['net_pnl'], gross - t['commission'] + t['swap'])
        risk = distance * lots * config['contract_size']
        if not math.isfinite(risk) or risk <= 0:
            raise ValueError('Invalid initial cash risk')
        eligible = [(j, d, mode) for j, d, mode in by_hour[opened // HOUR * HOUR]
                    if d['side'] == side and abs(d['stop_distance'] - distance) <= 1e-10]
        status = 'matched' if len(eligible) == 1 else 'missing' if not eligible else 'ambiguous'
        index, mode, features, reason = None, 'unattributed', {}, None
        if status == 'matched':
            index, d, mode = eligible[0]
            if index in used:
                raise ValueError('Decision reused for more than one trade')
            used.add(index)
            features, reason = dict(d['features']), d['reason']
        overshoot = quote_overshoot = 0.0
        if t['reason'] == 'stop_tick':
            overshoot = max(0, side * (t['stop'] - t['exit']))
            quote_overshoot = max(0, overshoot - config['slippage_pips'] * .0001)
        elif t['reason'] not in ('target_tick', 'end_of_sample'):
            raise ValueError('Unknown frozen exit reason')
        rapid = last_exit is not None and 0 <= opened - last_exit <= HOUR
        after_loss = rapid and rows[-1]['net_pnl'] < 0
        same_side = rapid and rows[-1]['side'] == side
        streak = streak + 1 if t['net_pnl'] < 0 else 0
        maximum_streak = max(maximum_streak, streak)
        row = dict(index=i, opened=t['opened'], closed=t['closed'], side=side,
            match_status=status, decision_index=index, branch=mode, features=features,
            decision_reason=reason, exit_reason=t['reason'], initial_cash_risk=risk,
            gross_pnl=gross, net_pnl=t['net_pnl'], commission=t['commission'], swap=t['swap'],
            gross_r=gross/risk, net_r=t['net_pnl']/risk,
            commission_r=t['commission']/risk, financing_debit_r=-t['swap']/risk,
            holding_hours=(exited-opened)/HOUR,
            stop_fill_overshoot_dollars=overshoot * lots * config['contract_size'],
            observed_quote_overshoot_pips=quote_overshoot/.0001,
            rapid_reentry=rapid, rapid_after_loss=after_loss, rapid_same_side=same_side)
        rows.append(row)
        groups[mode].append(row)
        last_exit = exited
    metrics = report['metrics']
    if len(rows) != metrics['closed_trades'] or sum(signal_branches.values()) != metrics['signals_observed']:
        raise ValueError('Trade or signal count mismatch')
    for key in ('net_pnl', 'commission', 'swap'):
        close(sum(row[key] for row in rows), metrics[key])
    close(metrics['net_return'], metrics['net_pnl']/config['initial_equity'], 1e-10)
    close(report['equity'][-1]['equity'], config['initial_equity']+metrics['net_pnl'])

    def totals(values):
        return dict(trades=len(values), wins=sum(r['net_pnl'] > 0 for r in values),
            losses=sum(r['net_pnl'] < 0 for r in values),
            gross_pnl=sum(r['gross_pnl'] for r in values), net_pnl=sum(r['net_pnl'] for r in values),
            commission=sum(r['commission'] for r in values), swap=sum(r['swap'] for r in values),
            mean_net_r=sum(r['net_r'] for r in values)/len(values) if values else None,
            exits=dict(Counter(r['exit_reason'] for r in values)))

    return dict(**totals(rows), scenario=report['scenario'], candidate=candidate,
        decisions=len(decisions), reason_counts=dict(reason_counts), branch_decisions=dict(branch_counts),
        branch_signals=dict(signal_branches), signal_count=sum(signal_branches.values()),
        unfilled_or_unattributed_signals=sum(signal_branches.values())-len(used),
        reported_spread_rejections=metrics['spread_rejections'],
        paused_equity_points=sum(bool(p['paused']) for p in report['equity']),
        match_counts=dict(Counter(r['match_status'] for r in rows)),
        longest_loss_streak=maximum_streak,
        rapid_reentries=sum(r['rapid_reentry'] for r in rows),
        rapid_after_losses=sum(r['rapid_after_loss'] for r in rows),
        rapid_same_side=sum(r['rapid_same_side'] for r in rows),
        stop_overshoot_dollars=sum(r['stop_fill_overshoot_dollars'] for r in rows),
        maximum_observed_quote_overshoot_pips=max((r['observed_quote_overshoot_pips'] for r in rows), default=0),
        mean_holding_hours=sum(r['holding_hours'] for r in rows)/len(rows) if rows else None,
        branches={mode: totals(values) for mode, values in groups.items()}, trades_detail=rows)


def paired_paths(base, adverse):
    a = {(r['opened'], r['side']): r for r in base['trades_detail']}
    b = {(r['opened'], r['side']): r for r in adverse['trades_detail']}
    if len(a) != base['trades'] or len(b) != adverse['trades']:
        raise ValueError('Duplicate entry identity')
    shared = a.keys() & b.keys()
    return dict(base_scenario=base['scenario'], adverse_scenario=adverse['scenario'],
        shared_entries=len(shared), base_only_entries=len(a.keys()-b.keys()),
        adverse_only_entries=len(b.keys()-a.keys()),
        net_pnl_difference=adverse['net_pnl']-base['net_pnl'],
        shared_entry_net_difference=sum(b[k]['net_pnl']-a[k]['net_pnl'] for k in shared),
        shared_entries_with_different_exit=sum(a[k]['closed'] != b[k]['closed'] or
            a[k]['exit_reason'] != b[k]['exit_reason'] for k in shared))
