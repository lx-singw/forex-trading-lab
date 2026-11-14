"""Deterministic, single-position OHLC simulation. No execution capability."""
from dataclasses import asdict, dataclass
from datetime import date, timedelta
import hashlib
import json
import math
from zoneinfo import ZoneInfo

from .model import Bar, Config, signal, size_lots


@dataclass
class Position:
    side: int
    lots: float
    entry: float
    stop: float
    target: float
    opened: str
    entry_commission: float
    swap: float = 0.0


class Simulator:
    def __init__(self, config: Config):
        self.config = config
        self.balance = config.initial_equity
        self.position: Position | None = None
        self.history: list[Bar] = []
        self.day: str | None = None
        self.day_start_equity = self.balance
        self.paused = False
        self.last_equity = self.balance
        self.trades: list[dict] = []
        self.curve: list[dict] = []
        self.exposed_bars = 0
        self.finished = False

    def equity(self, bid: float, spread: float) -> float:
        p = self.position
        if p is None:
            return self.balance
        quote = bid if p.side == 1 else bid + spread
        return self.balance + p.side * (quote - p.entry) * p.lots * self.config.contract_size

    def observe_loss(self, equity: float):
        if equity <= self.day_start_equity * (1 - self.config.daily_loss_fraction) + 1e-9:
            self.paused = True

    def _new_day(self, bar: Bar):
        new_day = bar.time.astimezone(ZoneInfo(self.config.broker_timezone)).date()
        if self.day == new_day.isoformat():
            return
        # Previous close reference retains overnight/weekend gap and rollover loss.
        self.day_start_equity = self.last_equity
        self.paused = False
        if self.day is not None and self.position:
            old_day = date.fromisoformat(self.day)
            p = self.position
            rate = self.config.swap_long_per_lot if p.side == 1 else self.config.swap_short_per_lot
            while old_day < new_day:
                # Five daily charges per week, with Wednesday tripled (no weekend charges).
                multiplier = 0 if old_day.weekday() >= 5 else 3 if old_day.weekday() == self.config.triple_swap_weekday else 1
                debit = rate * p.lots * multiplier
                self.balance += debit
                p.swap += debit
                old_day += timedelta(days=1)
        self.day = new_day.isoformat()

    def _open(self, bar: Bar, side: int, distance: float):
        if self.position or self.paused or self.balance <= 0 or bar.spread_pips > self.config.max_spread_pips:
            return
        spread = bar.spread_pips * 0.0001
        slip = self.config.slippage_pips * 0.0001
        entry = bar.open + (spread if side == 1 else 0) + side * slip
        # Prevent a stop within the entry spread or invalid price geometry.
        if distance <= spread + slip or entry - distance * max(1, self.config.reward_risk) <= 0:
            return
        lots = size_lots(self.balance, entry, distance, self.config)
        if lots == 0:
            return
        commission = lots * self.config.commission_per_lot_round_turn / 2
        self.position = Position(side, lots, entry, entry - side * distance,
                                 entry + side * distance * self.config.reward_risk,
                                 bar.time.isoformat(), commission)
        self.balance -= commission

    def _close(self, bar: Bar, exit_price: float, reason: str):
        p = self.position
        assert p is not None
        commission = p.lots * self.config.commission_per_lot_round_turn / 2
        gross = p.side * (exit_price - p.entry) * p.lots * self.config.contract_size
        self.balance += gross - commission
        self.trades.append({**asdict(p), "closed": bar.time.isoformat(), "exit": exit_price,
                            "reason": reason, "gross_pnl": gross,
                            "commission": p.entry_commission + commission,
                            "net_pnl": gross - p.entry_commission - commission + p.swap})
        self.position = None
        self.observe_loss(self.balance)

    def _exits(self, bar: Bar):
        p = self.position
        if not p:
            return
        spread = bar.spread_pips * 0.0001
        slip = self.config.slippage_pips * 0.0001
        adjustment = spread if p.side == -1 else 0
        opening, low, high = bar.open + adjustment, bar.low + adjustment, bar.high + adjustment
        stop_gap = opening <= p.stop if p.side == 1 else opening >= p.stop
        target_gap = opening >= p.target if p.side == 1 else opening <= p.target
        stop_hit = low <= p.stop if p.side == 1 else high >= p.stop
        target_hit = high >= p.target if p.side == 1 else low <= p.target
        if stop_gap:
            self._close(bar, opening - p.side * slip, "stop_gap")
        elif target_gap:
            # No favorable price improvement credited on gapped limit targets.
            self._close(bar, p.target, "target_gap")
        elif stop_hit:
            # Adverse-first when both boundaries are inside one OHLC bar.
            self._close(bar, p.stop - p.side * slip, "stop")
        else:
            # Conservative: adverse extreme may precede target; latch even after recovery.
            self.observe_loss(self.equity(bar.low if p.side == 1 else bar.high, spread))
            if target_hit:
                self._close(bar, p.target, "target")

    def step(self, bar: Bar) -> bool:
        if self.finished:
            raise ValueError("Simulation already finalized")
        if self.history and bar.time <= self.history[-1].time:
            if bar == self.history[-1]:
                return False  # Idempotent replay, including after checkpoint restoration.
            raise ValueError("Out-of-order or conflicting duplicate candle")
        if self.history and (bar.time - self.history[-1].time).total_seconds() % 3600:
            raise ValueError("Bars must be on the same H1 grid")
        self._new_day(bar)
        spread = bar.spread_pips * 0.0001
        self.observe_loss(self.equity(bar.open, spread))
        had_position = self.position is not None
        # Decision sees only prior closes. Stale signals are discarded after gaps.
        if not had_position and self.history and bar.time - self.history[-1].time == timedelta(hours=1):
            side, distance = signal(self.history, self.config)
            if side:
                self._open(bar, side, distance)
        if self.position:
            self.exposed_bars += 1
        self._exits(bar)
        self.last_equity = self.equity(bar.close, spread)
        self.observe_loss(self.last_equity)
        self.curve.append({"time": bar.time.isoformat(), "equity": self.last_equity, "paused": self.paused})
        self.history.append(bar)
        self.history = self.history[-self.config.slow-1:]
        return True

    def finish(self):
        if self.finished:
            return
        if self.position:
            bar = self.history[-1]
            p = self.position
            quote = bar.close + (bar.spread_pips * 0.0001 if p.side == -1 else 0)
            self._close(bar, quote - p.side * self.config.slippage_pips * 0.0001, "end_of_sample")
            self.last_equity = self.balance
            self.curve[-1].update(equity=self.balance, paused=self.paused)
        self.finished = True

    def metrics(self) -> dict:
        peak = self.config.initial_equity
        max_drawdown = 0.0
        for point in self.curve:
            peak = max(peak, point["equity"])
            max_drawdown = max(max_drawdown, (peak - point["equity"]) / peak)
        profits = [t["net_pnl"] for t in self.trades]
        wins, losses = [p for p in profits if p > 0], [p for p in profits if p < 0]
        return {"closed_trades": len(profits), "net_pnl": self.last_equity - self.config.initial_equity,
                "net_return": self.last_equity / self.config.initial_equity - 1,
                "max_close_drawdown": max_drawdown, "win_rate": len(wins) / len(profits) if profits else None,
                "average_win": sum(wins) / len(wins) if wins else None,
                "average_loss": sum(losses) / len(losses) if losses else None,
                "bar_exposure": self.exposed_bars / len(self.curve) if self.curve else 0,
                "commission": sum(t["commission"] for t in self.trades),
                "swap": sum(t["swap"] for t in self.trades)}

    def checkpoint(self) -> str:
        payload = {"version": 1, "config": asdict(self.config), "state": {
            **{key: value for key, value in vars(self).items() if key not in ("config", "position", "history")},
            "position": asdict(self.position) if self.position else None,
            "history": [b.to_dict() for b in self.history]}}
        body = json.dumps(payload, sort_keys=True, allow_nan=False)
        return json.dumps({"payload": payload, "sha256": hashlib.sha256(body.encode()).hexdigest()})

    @classmethod
    def restore(cls, value: str, config: Config):
        try:
            envelope = json.loads(value)
            payload = envelope["payload"]
            body = json.dumps(payload, sort_keys=True, allow_nan=False)
            if hashlib.sha256(body.encode()).hexdigest() != envelope["sha256"]:
                raise ValueError("Checkpoint checksum mismatch")
            if payload["version"] != 1 or payload["config"] != asdict(config):
                raise ValueError("Checkpoint version/config mismatch")
            result = cls(config)
            state = payload["state"]
            if set(state) != set(vars(result)) - {"config"}:
                raise ValueError("Checkpoint fields mismatch")
            result.__dict__.update(state)
            result.position = Position(**state["position"]) if state["position"] else None
            result.history = [Bar.from_dict(b) for b in state["history"]]
            if not all(math.isfinite(x) for x in (result.balance, result.day_start_equity, result.last_equity)):
                raise ValueError("Invalid checkpoint values")
            return result
        except (KeyError, TypeError, OverflowError) as exc:
            raise ValueError("Invalid checkpoint") from exc
