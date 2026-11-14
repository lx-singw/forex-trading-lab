"""Strict invented-input contracts; market admission remains unavailable."""
from dataclasses import dataclass, asdict
from decimal import Decimal, localcontext
from functools import wraps
import hashlib
import json
from pathlib import Path


def precise(function):
    """Freeze arithmetic precision independently of the caller's global context."""
    @wraps(function)
    def wrapped(*args,**kwargs):
        with localcontext() as context:
            context.prec=50
            return function(*args,**kwargs)
    return wrapped


def D(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("decimal string or integer required")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("finite value required")
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def bindings():
    root = Path(__file__).resolve().parent
    paths = list(root.glob("*.py")) + [root.parents[2]/"config"/"elliott-full-v1.json"]
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative integer required")
    return value


@dataclass(frozen=True)
class Bar:
    timeframe: str
    start: int
    end: int
    available: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    lineage: str

    def __post_init__(self):
        if self.timeframe not in ("H1", "H4", "D1"):
            raise ValueError("timeframe")
        for key in ("start", "end", "available"):
            integer(getattr(self, key))
        if not self.start < self.end <= self.available or not self.lineage:
            raise ValueError("bar chronology/lineage")
        for key in ("open", "high", "low", "close"):
            object.__setattr__(self, key, D(getattr(self, key)))
        if not 0 < self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("bar geometry")

    def record(self):
        return {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(self).items()}


@dataclass(frozen=True)
class Quote:
    time: int
    source: int
    sequence: int
    bid: Decimal
    ask: Decimal
    session_open: bool = True

    def __post_init__(self):
        for key in ("time", "source", "sequence"):
            integer(getattr(self, key))
        object.__setattr__(self, "bid", D(self.bid))
        object.__setattr__(self, "ask", D(self.ask))
        if not 0 < self.bid <= self.ask or self.source > self.time or type(self.session_open) is not bool:
            raise ValueError("quote")

    def record(self):
        return {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(self).items()}


def validate_bundle(value):
    if set(value) not in ({"kind", "symbol", "bars", "quotes"},{"kind", "symbol", "bars", "quotes","boundary"}) or value["kind"] != "invented_ew_full_v1" or value["symbol"] != "EURUSD":
        raise ValueError("invented EURUSD bundle required; market admission unavailable")
    if len(value["bars"]) > 30000 or len(value["quotes"]) > 200000:
        raise ValueError("input limit")
    bars = [Bar(**b) for b in value["bars"]]
    quotes = [Quote(**q) for q in value["quotes"]]
    if bars != sorted(bars, key=lambda b: (b.available, {"D1": 0, "H4": 1, "H1": 2}[b.timeframe], b.start)):
        raise ValueError("bar publication order")
    for frame in ("D1", "H4", "H1"):
        previous = None
        for bar in (b for b in bars if b.timeframe == frame):
            if previous and (bar.start < previous.end or bar.available < previous.available):
                raise ValueError("overlapping bars")
            previous = bar
    for a, b in zip(quotes, quotes[1:]):
        if b.sequence <= a.sequence or b.time < a.time or b.source < a.source:
            raise ValueError("quote chronology")
    if "boundary" in value:
        boundary=value["boundary"]
        if not isinstance(boundary,dict) or set(boundary)!={"end_time","quote_sequence","quote_source","quote_time"}:
            raise ValueError("declared boundary fields")
        for number in boundary.values():
            integer(number)
        if not quotes:
            raise ValueError("declared endpoint missing")
        last=quotes[-1]
        if (last.sequence,last.source,last.time)!=(boundary["quote_sequence"],boundary["quote_source"],boundary["quote_time"]):
            raise ValueError("declared endpoint mismatch")
        if not last.time<boundary["end_time"] or any(b.available>last.time for b in bars):
            raise ValueError("boundary cannot borrow later observations")
    return bars, quotes
