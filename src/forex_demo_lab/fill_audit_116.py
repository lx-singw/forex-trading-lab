"""Independent arithmetic ledger for reported invented entries and observed quotes.

Does not call simulator, fill, equity or position-sizing methods. Admission votes
are reported inputs; strategy equivalence is tested separately on retained114.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
import math


def _require(condition, reason):
    if not condition:
        raise ValueError("independent_audit_" + reason)


def _close(a, b, reason):
    _require(type(a) in (int, float) and math.isfinite(a)
             and math.isclose(a, b, abs_tol=1e-8, rel_tol=1e-10), reason)


def _instant(milliseconds):
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc)


def audit(report, events, config, spread_floor_pips=0.0):
    """Verify one finished account. Returns no inferred market qualification."""
    _require(config.broker_timezone == "Etc/UTC", "clock")
    trades, lineage, admissions = report["trades"], report["fill_lineage"], report["trade_arbitration"]
    _require(len(trades) == len(lineage) == len(admissions) == len(report["cost_audit"]), "counts")
    entries = {}
    last_exit = -1
    for i, (trade, link, admission) in enumerate(zip(trades, lineage, admissions)):
        en, ex = link["entry_sequence"], link["exit_sequence"]
        _require(type(en) is int and type(ex) is int and last_exit < en <= ex < len(events), "one_position")
        _require(link["trade_index"] == admission["trade_index"] == i
                 and admission["entry_sequence"] == en, "lineage")
        entries[en] = (i, trade, link, admission["entry_decision"])
        last_exit = ex
    _require(report["rule"] != "CASH" or not entries, "cash")
    balance = config.initial_equity
    last_equity = peak = day_reference = balance
    max_tick = 0.0
    day = current_hour = None
    paused = exposed = False
    position = None
    curve, rows, closed_hours = [], [], []
    opened_checks = {c["sequence"]: c for c in report["entry_checks"] if c["opened"]}
    _require(len(opened_checks) == len(entries), "entry_count")
    paused_quotes = 0

    def mark(bid, ask):
        nonlocal last_equity, peak, max_tick, paused
        equity = balance
        if position:
            p = position
            quote = bid if p["side"] == 1 else ask
            stopped = quote <= p["stop"] if p["side"] == 1 else quote >= p["stop"]
            targeted = quote >= p["target"] if p["side"] == 1 else quote <= p["target"]
            price = quote - p["side"] * slip if stopped else p["target"] if targeted else quote
            equity += p["side"] * (price - p["entry"]) * p["lots"] * config.contract_size
            if stopped or targeted:
                equity -= p["lots"] * config.commission_per_lot_round_turn / 2
        peak = max(peak, equity)
        max_tick = max(max_tick, (peak - equity) / peak)
        if equity <= day_reference * (1 - config.daily_loss_fraction) + 1e-9:
            paused = True
        last_equity = equity

    def close_position(event, bid, ask, reason, exit_price):
        nonlocal position, balance, paused
        p = position
        i, trade, link = p["index"], p["trade"], p["link"]
        _require(link["exit_sequence"] == event["sequence"] and trade["reason"] == reason, "first_exit")
        _require(trade["closed"] == _instant(event["receipt_msc"]).isoformat(), "exit_time")
        units = p["lots"] * config.contract_size
        gross = p["side"] * (exit_price - p["entry"]) * units
        commission = p["lots"] * config.commission_per_lot_round_turn
        balance += gross - commission / 2
        net = gross - commission + p["swap"]
        for key, expected in (("exit", exit_price), ("gross_pnl", gross), ("commission", commission),
                              ("swap", p["swap"]), ("net_pnl", net)):
            _close(trade[key], expected, key)
        midpoint = exit_price if reason == "target_tick" else (bid + ask) / 2
        quote = bid if p["side"] == 1 else ask
        exit_spread = 0.0 if reason == "target_tick" else p["side"] * (midpoint - quote) * units
        exit_slip = 0.0 if reason == "target_tick" else p["side"] * (quote - exit_price) * units
        costs = {"reference_gross": p["side"] * (midpoint - p["entry_mid"]) * units,
                 "spread": p["entry_spread"] + exit_spread,
                 "slippage": p["entry_slip"] + exit_slip,
                 "commission": commission, "financing_debit": -p["swap"], "net": net}
        for key, expected in costs.items():
            _close(report["cost_audit"][i][key], expected, "cost_" + key)
        _close(costs["reference_gross"] - sum(costs[k] for k in
               ("spread", "slippage", "commission", "financing_debit")), net, "reconcile")
        rows.append({"trade_index": i, "entry_sequence": p["entry_sequence"],
                     "exit_sequence": event["sequence"], "entry_risk": p["risk"],
                     "entry_budget": p["budget"], "actual_loss": max(0.0, -net),
                     "loss_exceeds_entry_budget": -net > p["budget"] + 1e-9,
                     "financing_days": p["financing_days"], "costs": costs})
        position = None
        if balance <= day_reference * (1 - config.daily_loss_fraction) + 1e-9:
            paused = True

    slip = config.slippage_pips * .0001
    for event in events:
        seq, milliseconds = event["sequence"], event["receipt_msc"]
        bid, ask = event["bid"], max(event["ask"], event["bid"] + spread_floor_pips * .0001)
        hour = milliseconds // 3_600_000
        new_hour = current_hour is None or hour != current_hour
        if new_hour:
            if current_hour is not None:
                curve.append({"equity": last_equity, "paused": paused, "exposed": exposed})
                closed_hours.append(current_hour)
            today = _instant(milliseconds).date()
            if today != day:
                day_reference, paused = last_equity, False
                if position and day is not None:
                    charge_day = day
                    while charge_day < today:
                        multiplier = (0 if charge_day.weekday() >= 5 else
                                      3 if charge_day.weekday() == config.triple_swap_weekday else 1)
                        rate = config.swap_long_per_lot if position["side"] == 1 else config.swap_short_per_lot
                        fee = rate * position["lots"] * multiplier
                        balance += fee
                        position["swap"] += fee
                        position["financing_days"].append({"day": charge_day.isoformat(), "multiplier": multiplier})
                        charge_day += timedelta(days=1)
                day = today
            current_hour, exposed = hour, position is not None
        mark(bid, ask)
        if seq in entries:
            i, trade, link, decision = entries[seq]
            _require(position is None and new_hour and not paused and balance > 0, "entry_guard")
            _require(len(closed_hours) >= 201 and closed_hours[-1] == hour - 1, "stale_entry")
            _require(milliseconds >= report["evaluation_start_msc"], "warmup_entry")
            _require((ask - bid) / .0001 <= config.max_spread_pips, "spread_entry")
            votes = list(decision["features"]["votes"].values())
            active = [v for v in votes if v["side"]]
            sides = {v["side"] for v in active}
            required = 3 if report["rule"] == "UNANIMOUS" else 2
            _require(len(sides) == 1 and len(active) >= required, "agreement")
            side, distance = active[0]["side"], max(v["stop_distance"] for v in active)
            _require(decision["side"] == side and trade["side"] == side, "side")
            _close(decision["stop_distance"], distance, "supporting_stop")
            _require(decision["hour_msc"] == hour * 3_600_000, "admission_hour")
            entry = (ask if side == 1 else bid) + side * slip
            _require(distance > ask - bid + slip and entry - distance * max(1, config.reward_risk) > 0,
                     "price_geometry")
            loss_per_lot = (distance + slip) * config.contract_size + config.commission_per_lot_round_turn
            raw = min(balance * config.risk_fraction / loss_per_lot,
                      balance / (entry * config.contract_size / config.leverage
                                 + config.commission_per_lot_round_turn / 2), config.lot_max)
            step = Decimal(str(config.lot_step))
            lots = float((Decimal(str(raw)) / step).to_integral_value(rounding=ROUND_FLOOR) * step)
            budget, risk = balance * config.risk_fraction, lots * loss_per_lot
            _require(lots >= config.lot_min and risk <= budget + 1e-9, "risk_budget")
            stop, target = entry - side * distance, entry + side * distance * config.reward_risk
            for key, expected in (("entry", entry), ("lots", lots), ("stop", stop), ("target", target),
                                  ("entry_commission", lots * config.commission_per_lot_round_turn / 2)):
                _close(trade[key], expected, key)
            _require(trade["opened"] == _instant(milliseconds).isoformat(), "entry_time")
            _close(opened_checks[seq]["estimated_risk"], risk, "reported_risk")
            _close(opened_checks[seq]["risk_budget"], budget, "reported_budget")
            units = lots * config.contract_size
            mid = (bid + ask) / 2
            quote = ask if side == 1 else bid
            position = {"index": i, "trade": trade, "link": link, "entry_sequence": seq,
                        "side": side, "lots": lots, "entry": entry, "stop": stop, "target": target,
                        "entry_mid": mid, "entry_spread": side * (quote - mid) * units,
                        "entry_slip": side * (entry - quote) * units, "risk": risk,
                        "budget": budget, "swap": 0.0, "financing_days": []}
            balance -= lots * config.commission_per_lot_round_turn / 2
        if position:
            exposed = True
            p = position
            quote = bid if p["side"] == 1 else ask
            stopped = quote <= p["stop"] if p["side"] == 1 else quote >= p["stop"]
            targeted = quote >= p["target"] if p["side"] == 1 else quote <= p["target"]
            if stopped or targeted:
                close_position(event, bid, ask, "stop_tick" if stopped else "target_tick",
                               quote - p["side"] * slip if stopped else p["target"])
            elif p["link"]["exit_sequence"] == seq:
                _require(seq == events[-1]["sequence"] and p["trade"]["reason"] == "end_of_sample", "early_exit")
        mark(bid, ask)
        paused_quotes += int(paused)
    if position:
        event = events[-1]
        bid, ask = event["bid"], max(event["ask"], event["bid"] + spread_floor_pips * .0001)
        quote = bid if position["side"] == 1 else ask
        close_position(event, bid, ask, "end_of_sample", quote - position["side"] * slip)
        mark(bid, ask)
    curve.append({"equity": last_equity, "paused": paused, "exposed": exposed})
    totals = {k: sum(r["costs"][k] for r in rows) for k in report["cost_totals"]}
    for key, expected in totals.items():
        _close(report["cost_totals"][key], expected, "total_" + key)
    close_peak, max_close = config.initial_equity, 0.0
    for point in curve:
        close_peak = max(close_peak, point["equity"])
        max_close = max(max_close, (close_peak - point["equity"]) / close_peak)
    metrics = report["metrics"]
    for key, expected in (("net_pnl", balance - config.initial_equity), ("max_tick_drawdown", max_tick),
                          ("max_close_drawdown", max_close), ("commission", totals["commission"]),
                          ("swap", -totals["financing_debit"])):
        _close(metrics[key], expected, "metric_" + key)
    _require(metrics["closed_trades"] == len(rows), "trade_count")
    _require(not position, "unfinished_position")
    return {"passed": True, "ledger_version": "independent_observed_fill_116_v1",
            "trades": rows, "final_balance": balance, "max_tick_drawdown": max_tick,
            "max_close_drawdown": max_close, "final_paused": paused, "paused_quotes": paused_quotes,
            "entry_admissions_are_reported_inputs": True, "market_validation": False}
