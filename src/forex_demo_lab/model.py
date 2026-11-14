"""Fixed baseline and explicit EURUSD/USD simulation assumptions."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import math
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Config:
    symbol: str = "EURUSD"
    account_currency: str = "USD"
    fast: int = 20
    slow: int = 50
    atr_period: int = 14
    stop_atr: float = 2.0
    reward_risk: float = 2.0
    risk_fraction: float = 0.0025
    daily_loss_fraction: float = 0.01
    max_spread_pips: float = 1.5
    initial_equity: float = 10000.0
    contract_size: float = 100000.0
    lot_min: float = 0.01
    lot_step: float = 0.01
    lot_max: float = 1.0
    # Hypothetical inputs, not discovered broker/account specifications.
    leverage: float = 30.0
    commission_per_lot_round_turn: float = 7.0
    slippage_pips: float = 0.2
    swap_long_per_lot: float = -3.0
    swap_short_per_lot: float = -1.5
    triple_swap_weekday: int = 2  # Wednesday's rollover at the next midnight
    broker_timezone: str = "Etc/UTC"

    def __post_init__(self):
        for key, value in asdict(self).items():
            if isinstance(value, (int, float)) and (isinstance(value, bool) or not math.isfinite(value)):
                raise ValueError(f"{key} must be finite and numeric")
        if self.symbol != "EURUSD" or self.account_currency != "USD":
            raise ValueError("Only EURUSD with USD accounting is implemented")
        for value in (self.fast, self.slow, self.atr_period, self.triple_swap_weekday):
            if type(value) is not int:
                raise ValueError("Periods and weekday must be integers")
        if not 1 <= self.fast < self.slow or not 1 <= self.atr_period < self.slow:
            raise ValueError("Invalid indicator periods")
        if not 0 < self.risk_fraction <= 0.0025 or not 0 < self.daily_loss_fraction <= 0.01:
            raise ValueError("Risk caps cannot exceed 0.25% per trade and 1% per day")
        for key in ("stop_atr", "reward_risk", "max_spread_pips", "initial_equity",
                    "contract_size", "lot_min", "lot_step", "lot_max", "leverage"):
            if getattr(self, key) <= 0:
                raise ValueError(f"{key} must be positive")
        if self.lot_min > self.lot_max or not 0 <= self.triple_swap_weekday <= 6:
            raise ValueError("Invalid volume bounds or rollover weekday")
        if self.commission_per_lot_round_turn < 0 or self.slippage_pips < 0:
            raise ValueError("Costs cannot be negative")
        if self.swap_long_per_lot > 0 or self.swap_short_per_lot > 0:
            raise ValueError("This conservative model supports swap debits only")
        ZoneInfo(self.broker_timezone)


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamps require an explicit UTC offset")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    spread_pips: float

    def __post_init__(self):
        if self.time.tzinfo is None or self.time.utcoffset() is None:
            raise ValueError("Timezone-aware timestamps required")
        if self.time.minute or self.time.second or self.time.microsecond:
            raise ValueError("H1 bars must start on an hour")
        values = (self.open, self.high, self.low, self.close, self.spread_pips)
        if not all(math.isfinite(x) for x in values) or min(values[:4]) <= 0 or self.spread_pips < 0:
            raise ValueError("Invalid price/spread")
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("Inconsistent OHLC")

    def to_dict(self):
        return {**asdict(self), "time": self.time.isoformat()}

    @classmethod
    def from_dict(cls, value):
        return cls(**{**value, "time": timestamp(value["time"])})


def signal(history: list[Bar], config: Config) -> tuple[int, float]:
    """History contains closed candles only; decide for the following open."""
    if len(history) < config.slow + 1:
        return 0, 0.0
    closes = [b.close for b in history]
    previous = (sum(closes[-config.fast-1:-1]) / config.fast
                - sum(closes[-config.slow-1:-1]) / config.slow)
    current = sum(closes[-config.fast:]) / config.fast - sum(closes[-config.slow:]) / config.slow
    side = 1 if previous <= 0 < current else -1 if previous >= 0 > current else 0
    ranges = [max(history[i].high - history[i].low,
                  abs(history[i].high - history[i-1].close),
                  abs(history[i].low - history[i-1].close))
              for i in range(len(history) - config.atr_period, len(history))]
    return side, sum(ranges) / config.atr_period * config.stop_atr


def size_lots(equity: float, entry: float, stop_distance: float, config: Config) -> float:
    """Floor to step; include exit slippage and both commissions in risk budget.

    Entry already includes entry slippage. Stops can still gap beyond this estimate.
    Margin is a simplified EURUSD estimate, not a broker margin calculation.
    """
    if not all(math.isfinite(x) and x > 0 for x in (equity, entry, stop_distance)):
        return 0.0
    loss_per_lot = ((stop_distance + config.slippage_pips * 0.0001) * config.contract_size
                    + config.commission_per_lot_round_turn)
    margin_per_lot = entry * config.contract_size / config.leverage
    raw = min(equity * config.risk_fraction / loss_per_lot,
              equity / (margin_per_lot + config.commission_per_lot_round_turn / 2), config.lot_max)
    step = Decimal(str(config.lot_step))
    lots = float((Decimal(str(raw)) / step).to_integral_value(rounding=ROUND_FLOOR) * step)
    if lots < config.lot_min or lots * loss_per_lot > equity * config.risk_fraction + 1e-9:
        return 0.0
    return lots
