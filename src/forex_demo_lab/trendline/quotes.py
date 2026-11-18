"""Invented ordered bid/ask tape and synchronized midpoint publications."""
from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction

from ..elliott_full.contracts import Bar, Quote
from ..elliott_sessions_146 import Calendar, Observations, Window
from . import data, fills

VERSION = "TRL_Q_TAPE_185_V1"
KIND = "invented_trendline_quotes"
MAX_AGE = 2000
MAX_ENTRY_SPREAD = Fraction("0.00015")


def _geometry_source(document):
    data.fields(document, ("schema", "kind", "symbol", "data_level", "geometry_basis", "partition",
                           "calendar", "liquidation_at", "quotes"))
    if (document["schema"], document["kind"], document["symbol"], document["data_level"],
            document["geometry_basis"]) != (VERSION, KIND, "EURUSD", "Q", "mid_sync"):
        raise ValueError("invented Level Q EURUSD midpoint tape required")
    # The setup engine already accepts completed midpoint publications
    # through this declaration. The quote adapter owns the Q provenance.
    return data.Declaration.from_record({
        "schema": data.VERSION, "kind": "invented_trendline_source", "symbol": "EURUSD",
        "data_level": "B", "geometry_basis": "mid_candles_source", "spread_semantics": "not_available",
        "partition": document["partition"], "input_sha256": data.digest(document), "calendar": document["calendar"],
    })


def validation_unlock(document):
    """Declare intentional access to this invented validation tape."""
    return data.unlock_record(_geometry_source(document))


@dataclass(frozen=True, init=False)
class Tape:
    sha256: str
    geometry_source: data.Declaration
    calendar: Calendar
    windows: tuple[Window, ...]
    starts: tuple[int, ...]
    liquidation: int
    quotes: tuple[Quote, ...]

    def __init__(self, document, unlock=None):
        source = _geometry_source(document)
        if document["partition"] == "validation":
            if unlock != data.unlock_record(source):
                raise ValueError("matching invented validation unlock required")
        elif unlock is not None:
            raise ValueError("unexpected invented validation unlock")
        calendar = source.calendar
        windows = calendar.frame("H1")
        liquidation = document["liquidation_at"]
        data.integer(liquidation)
        if not calendar.start <= liquidation < calendar.end:
            raise ValueError("quote liquidation must be inside the declared partition")
        if type(document["quotes"]) is not list or not 1 <= len(document["quotes"]) <= data.ROW_LIMIT:
            raise ValueError("bounded nonempty quote tape required")

        quotes = []
        for row in document["quotes"]:
            data.fields(row, ("source_at", "received_at", "sequence", "bid", "ask"))
            quote = Quote(row["received_at"], row["source_at"], row["sequence"],
                          data.number(row["bid"]), data.number(row["ask"]))
            if not calendar.start <= quote.source < calendar.end or quote.time > calendar.end + 60000:
                raise ValueError("quote outside invented scope")
            if quotes:
                previous = quotes[-1]
                if quote.sequence <= previous.sequence or quote.source < previous.source or quote.time < previous.time:
                    raise ValueError("monotonic source, receipt and unique quote sequence required")
            quotes.append(quote)
        object.__setattr__(self, "sha256", source.record()["input_sha256"])
        object.__setattr__(self, "geometry_source", source)
        object.__setattr__(self, "calendar", calendar)
        object.__setattr__(self, "windows", windows)
        object.__setattr__(self, "starts", tuple(w.start for w in windows))
        object.__setattr__(self, "liquidation", liquidation)
        object.__setattr__(self, "quotes", tuple(quotes))

    def slot(self, at):
        i = bisect_right(self.starts, at) - 1
        if i >= 0 and at < self.windows[i].end:
            return self.windows[i]
        return None

    def prefix(self, as_of):
        data.integer(as_of)
        if not self.calendar.start <= as_of <= self.calendar.end + 60000:
            raise ValueError("quote cursor outside invented scope")
        for quote in self.quotes:
            if quote.time > as_of:
                break
            yield quote

    def publications(self, prefix, as_of):
        groups = {}
        for quote in prefix:
            slot = self.slot(quote.source)
            if slot is not None and quote.time <= slot.end + self.calendar.delay:
                groups.setdefault(slot.start, []).append(quote)
        stream = Observations(self.calendar)
        for slot in self.windows:
            received = slot.end + self.calendar.delay
            group = groups.get(slot.start)
            if group and received <= as_of:
                midpoints = [(Fraction(q.bid) + Fraction(q.ask)) / 2 for q in group]
                prices = [fills.text(v) for v in (midpoints[0], max(midpoints), min(midpoints), midpoints[-1])]
                stream.observe(Bar("H1", slot.start, slot.end, received, *prices,
                                   data.digest([q.record() for q in group])))
        stream.advance(as_of)
        return stream.bars()
