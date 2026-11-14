"""Fixed research candidates; decisions see completed bars only, never broker APIs."""
from dataclasses import dataclass, replace
import math
from statistics import pstdev

from .model import signal

CANDIDATES = ("C00", "C01", "C02", "C03", "C04")
MINIMUM_BARS = {"C00": 51, "C01": 201, "C02": 22, "C03": 21, "C04": 22}


@dataclass(frozen=True)
class Decision:
    side: int
    stop_distance: float
    reason: str
    features: dict


def efficiency_mode(value):
    if not math.isfinite(value) or not 0 <= value <= 1 + 1e-12:
        raise ValueError("Invalid price efficiency")
    return "trend" if value >= .35 else "range" if value <= .20 else "neutral"


def _breakout(history):
    previous, current = history[-22:-2], history[-21:-1]
    old, new = history[-2].close, history[-1].close
    upper, lower = max(b.high for b in current), min(b.low for b in current)
    side = 1 if new > upper and old <= max(b.high for b in previous) else (
        -1 if new < lower and old >= min(b.low for b in previous) else 0)
    return side, "channel_breakout" if side else "no_breakout", {"channel_high": upper, "channel_low": lower}


def _reentry(history):
    closes = [b.close for b in history]
    previous, current = closes[-21:-1], closes[-20:]
    old_sd, new_sd = pstdev(previous), pstdev(current)
    if not old_sd or not new_sd:
        return 0, "zero_price_deviation", {}
    old = (previous[-1] - sum(previous) / 20) / old_sd
    new = (current[-1] - sum(current) / 20) / new_sd
    side = 1 if old < -2 <= new else -1 if old > 2 >= new else 0
    return side, "range_reentry" if side else "no_reentry", {"previous_z": old, "current_z": new}


def decide(candidate, history, config):
    if candidate not in CANDIDATES:
        raise ValueError("Unknown research candidate")
    if len(history) < max(MINIMUM_BARS[candidate], config.atr_period + 1):
        return Decision(0, 0, "warmup", {})
    if any(b.time <= a.time for a, b in zip(history, history[1:])):
        raise ValueError("Completed history must be strictly chronological")
    if candidate in ("C00", "C01"):
        fast, slow = (20, 50) if candidate == "C00" else (50, 200)
        side, distance = signal(history, replace(config, fast=fast, slow=slow))
        return Decision(side, distance, "sma_cross" if side else "no_cross", {"fast": fast, "slow": slow})
    ranges = [max(history[i].high - history[i].low,
                  abs(history[i].high - history[i-1].close), abs(history[i].low - history[i-1].close))
              for i in range(len(history) - config.atr_period, len(history))]
    distance = sum(ranges) / config.atr_period * config.stop_atr
    if not math.isfinite(distance) or distance <= 0:
        return Decision(0, 0, "zero_or_invalid_atr", {})
    mode, features = None, {}
    if candidate == "C04":
        closes = [b.close for b in history[-21:]]
        path = sum(abs(b - a) for a, b in zip(closes, closes[1:]))
        if not path:
            return Decision(0, distance, "zero_price_path", {})
        ratio = abs(closes[-1] - closes[0]) / path
        mode = efficiency_mode(ratio)
        features = {"efficiency_ratio": ratio, "selected_mode": mode}
        if mode == "neutral":
            return Decision(0, distance, "selector_neutral", features)
    side, reason, detail = _breakout(history) if candidate == "C02" or mode == "trend" else _reentry(history)
    return Decision(side, distance, (f"selector_{mode}:" if mode else "") + reason, {**features, **detail})
