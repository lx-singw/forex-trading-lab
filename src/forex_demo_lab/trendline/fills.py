"""Invented Level B price calculations, not an account or order executor.

Opening prices are explicit historical assumptions. A completed hour's range is
never used to choose an entry or to create a stop before the hypothetical fill.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import re

from . import data

VERSION = "TRL_B_PRICES_164_V1"
PIP = F("0.0001")
PROFILE_SHA = "fc9629f0922700e9ea8118cbf23460f550870a5ecf17ff14e6246833766faf6f"


def decimal(value, positive=False):
    # Calculated ask/entry values may have16 places (12-place pips *0.0001).
    # Keep them exact without widening the observed Hour parser's input bounds.
    if type(value) is not str or not re.fullmatch(r"[0-9]{1,20}(?:\.[0-9]{1,20})?",value):
        raise ValueError("bounded nonnegative decimal string required")
    result = F(value)
    if positive and result <= 0:
        raise ValueError("positive decimal required")
    return result


def _entry_atr(value):
    if type(value) is str:
        return decimal(value, positive=True)
    data.fields(value, ("numerator", "denominator"))
    numerator, denominator = value["numerator"], value["denominator"]
    if any(type(part) is not int or not 0 < part <= 10**40 for part in (numerator, denominator)):
        raise ValueError("bounded positive rational ATR required")
    return F(numerator, denominator)


def text(value):
    """Exact finite decimal spelling, independent of global Decimal precision."""
    value = F(value)
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("finite decimal output required")
    places = max(twos, fives)
    coefficient = abs(value.numerator) * 2**(places-twos) * 5**(places-fives)
    digits = str(coefficient).zfill(places+1)
    result = digits if places == 0 else (digits[:-places]+"."+digits[-places:]).rstrip("0").rstrip(".")
    return ("-" if value < 0 else "") + result


def rounded(value, tick, upward):
    units = value / tick
    count = -((-units.numerator)//units.denominator) if upward else units.numerator//units.denominator
    return count * tick


def profile(name):
    if type(name) is not str or name not in ("base", "adverse"):
        raise ValueError("fixed hypothetical profile required")
    value, sha = data.read_json(data.ROOT/"config/research-candidates-117.json")
    if sha != PROFILE_SHA:
        raise ValueError("frozen cost declaration changed")
    item = value["cost_profiles"][name]
    return {"name":name, "kind":"inherited_hypothetical_not_broker_terms",
            "slippage_pips":text(F(str(item["slippage_pips_per_fill"]))),
            "spread_floor_pips":text(F(str(item["spread_floor_pips"]))),
            "commission_and_financing_applied":False}


def bindings():
    result = data.source_bindings()
    for path in (data.ROOT/"src/forex_demo_lab/trendline/fills.py",
                 data.ROOT/"config/research-candidates-117.json"):
        result[path.relative_to(data.ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


@dataclass(frozen=True, order=True)
class Event:
    time: int
    ordinal: int

    def __post_init__(self):
        data.integer(self.time)
        data.integer(self.ordinal)

    @classmethod
    def from_record(cls, value):
        data.fields(value, ("time", "ordinal"))
        return cls(**value)

    def record(self):
        return {"time":self.time, "ordinal":self.ordinal}


@dataclass(frozen=True)
class Opening:
    start: int
    end: int
    ordinal: int
    bid: F
    spread_pips: F

    @classmethod
    def from_record(cls, value):
        data.fields(value, ("kind", "start", "end", "ordinal", "bid", "spread_pips"))
        if value["kind"] != "invented_b_opening_assumption":
            raise ValueError("invented opening assumption required")
        for key in ("start", "end", "ordinal"):
            data.integer(value[key])
        if value["start"] >= value["end"]:
            raise ValueError("opening window")
        return cls(value["start"], value["end"], value["ordinal"],
                   decimal(value["bid"],True), decimal(value["spread_pips"]))

    @classmethod
    def from_hour(cls, hour, ordinal):
        # Revalidate the supplied row, then discard all later range/receipt fields.
        hour = data.Hour.from_record(hour.record(), "bid_only")
        return cls.from_record({"kind":"invented_b_opening_assumption",
                                "start":hour.start, "end":hour.end, "ordinal":ordinal,
                                "bid":str(hour.open), "spread_pips":str(hour.spread_pips)})

    @property
    def event(self):
        return Event(self.start, self.ordinal)

    def record(self):
        return {"kind":"invented_b_opening_assumption", "start":self.start,
                "end":self.end, "ordinal":self.ordinal, "bid":text(self.bid),
                "spread_pips":text(self.spread_pips)}


@dataclass(frozen=True)
class Position:
    """Hypothetical price/protection record; no lots, balance or broker identity."""
    _json: str

    @classmethod
    def from_record(cls, value):
        data.fields(value, ("kind", "schema", "direction", "entry_at", "entry_price",
                           "initial_stop", "stop", "target", "stop_effective_at", "tick",
                           "exit_model", "profile", "geometry_identity"))
        if value["kind"] != "invented_b_price_position" or value["schema"] != VERSION:
            raise ValueError("invented price position required")
        if value["direction"] not in ("LONG", "SHORT") or value["exit_model"] not in ("E1", "E2"):
            raise ValueError("direction/exit model")
        if value["profile"] not in ("base", "adverse"):
            raise ValueError("hypothetical profile")
        side = 1 if value["direction"] == "LONG" else -1
        entry, initial, stop, tick = (decimal(value[key],True) for key in ("entry_price","initial_stop","stop","tick"))
        if (side*(entry-initial) <= 0 or side*(stop-initial) < 0
                or (stop/tick).denominator != 1 or (initial/tick).denominator != 1):
            raise ValueError("initial risk, tightening and tick geometry")
        opened, effective = Event.from_record(value["entry_at"]), Event.from_record(value["stop_effective_at"])
        if effective < opened or (stop != initial and effective <= opened):
            raise ValueError("prospective protection timing")
        target = value["target"]
        if value["exit_model"] == "E1":
            if target is not None:
                raise ValueError("E1 has no target")
        else:
            target = decimal(target,True)
            if (stop != initial or effective != opened or (target/tick).denominator != 1
                    or side*(target-entry) < 2*side*(entry-initial)):
                raise ValueError("E2 fixed stop and qualifying rounded target required")
        data.sha(value["geometry_identity"])
        return cls(data.canonical(value).decode())

    def record(self):
        import json
        return json.loads(self._json)


class PriceModel:
    """Pure calculations; repeated calls cannot place orders or mutate an account."""
    def __init__(self, source, cost_profile="base"):
        self.source = data.research_declaration(source)
        declaration = self.source.record()
        self._geometry_identity = data.digest({k:v for k,v in declaration.items() if k != "input_sha256"})
        self._source_sha = self.source.sha256
        self.costs = profile(cost_profile)
        self._cost_sha = data.digest(self.costs)
        self._bindings = bindings()
        self._hours = {w.start:w for w in self.source.calendar.frame("H1")}
        self._h4 = self.source.calendar.frame("H4")

    @property
    def geometry_identity(self):
        return self._geometry_identity

    def _result(self, status, reason, **values):
        if (self._bindings != bindings() or self._source_sha != self.source.sha256
                or self._cost_sha != data.digest(self.costs)):
            raise ValueError("price model source/profile/protocol changed")
        return {"schema":VERSION,"kind":"invented_b_price_result", "data_level":"B",
                "geometry_basis":self.source.record()["geometry_basis"],
                "status":status, "reason":reason, "profile":dict(self.costs),
                "declaration_sha256":self._source_sha,"input_sha256":self.source.record()["input_sha256"],
                "geometry_identity":self.geometry_identity, "source_bindings":dict(self._bindings),
                "price_only":True, "account_ledger_available":False,
                "market_cells_run":0,"demo_eligible":False,"orders_available":False,
                **values}

    def _can_execute(self):
        return self.source.record()["geometry_basis"] == "bid_only"

    def _opening(self, opening):
        opening = Opening.from_record(opening.record())
        window = self._hours.get(opening.start)
        if window is None or window.end != opening.end:
            raise ValueError("opening not in declared H1 schedule")
        return opening

    def _position(self, position):
        value = Position.from_record(position.record()).record()
        opened = Event.from_record(value["entry_at"])
        effective = Event.from_record(value["stop_effective_at"])
        if (value["geometry_identity"] != self.geometry_identity or value["profile"] != self.costs["name"]
                or opened.time not in self._hours or effective.time > self.source.calendar.end+60000):
            raise ValueError("position/source/profile mismatch")
        return value

    def _sides(self, opening):
        spread = max(opening.spread_pips, F(self.costs["spread_floor_pips"])) * PIP
        return opening.bid, opening.bid+spread, spread

    def entry_window(self, trigger_end):
        data.integer(trigger_end)
        if trigger_end not in {w.end for w in self._h4}:
            raise ValueError("declared H4 trigger close required")
        return next((w for w in self._hours.values() if w.start >= trigger_end), None)

    def entry(self, request, opening, *, target_levels=None):
        data.fields(request, ("kind", "direction", "trigger_end", "decision_at", "stop", "target", "atr", "tick", "exit_model"))
        if request["kind"] != "invented_b_price_request" or request["direction"] not in ("LONG","SHORT"):
            raise ValueError("invented entry request required")
        if request["exit_model"] not in ("E1", "E2"):
            raise ValueError("exit model")
        data.integer(request["trigger_end"])
        decision = Event.from_record(request["decision_at"])
        if decision.time < request["trigger_end"]:
            raise ValueError("decision cannot precede trigger close")
        decimal(request["stop"], positive=True)
        decimal(request["tick"], positive=True)
        _entry_atr(request["atr"])
        target = None if request["target"] is None else decimal(request["target"],True)
        if request["exit_model"] == "E1" and target is not None:
            raise ValueError("E1 has no target")
        if target_levels is not None and (
                request["exit_model"] != "E2" or target is not None
                or not isinstance(target_levels, (tuple, list))
                or any(not isinstance(level, F) or level <= 0 for level in target_levels)):
            raise ValueError("exact level candidates require E2 without a specified target")
        window = self.entry_window(request["trigger_end"])
        if not self._can_execute():
            return self._result("UNAVAILABLE","EXECUTION_SIDE_DATA_UNAVAILABLE")
        if window is None:
            return self._result("SKIPPED","NO_SCHEDULED_ENTRY")
        if opening is None:
            return self._result("SKIPPED","MISSING_ENTRY_BAR", expected_start=window.start)
        opening = self._opening(opening)
        if opening.start != window.start:
            return self._result("SKIPPED","MISSING_ENTRY_BAR", expected_start=window.start)
        if decision.time > opening.start:
            return self._result("SKIPPED","LATE_DECISION")
        if decision >= opening.event:
            return self._result("SKIPPED","UNRESOLVED_OPEN_ORDER")
        return self._entry_at(request, self._sides(opening), opening.event, target_levels, opening=opening.record())

    def _entry_at(self, request, prices, event, target_levels, **evidence):
        """Price an already ordered, eligible observation for either replay."""
        stop, tick = (decimal(request[k],True) for k in ("stop","tick"))
        atr = _entry_atr(request["atr"])
        target = None if request["target"] is None else decimal(request["target"],True)
        side = 1 if request["direction"] == "LONG" else -1
        bid, ask, spread = prices
        stop = rounded(stop,tick,upward=side == -1)
        if stop <= 0:
            return self._result("SKIPPED","NONPOSITIVE_STOP")
        exit_side = bid if side == 1 else ask
        if side*(exit_side-stop) <= 0:
            return self._result("SKIPPED","STOP_ALREADY_CROSSED")
        fill = (ask if side == 1 else bid) + side*F(self.costs["slippage_pips"])*PIP
        if fill <= 0:
            return self._result("SKIPPED","NONPOSITIVE_ENTRY")
        distance = side*(fill-stop)
        if not F("0.5")*atr <= distance <= F("2.5")*atr:
            return self._result("SKIPPED","STOP_OUT_OF_WINDOW")
        if spread > F("0.10")*distance:
            return self._result("SKIPPED","SPREAD_TOO_WIDE")
        target_evidence = {}
        if request["exit_model"] == "E2":
            candidates = (() if target is None else (target,)) if target_levels is None else target_levels
            for level in sorted(candidates, key=lambda price: side * price):
                target = rounded(level, tick, upward=side == -1)
                if target > 0 and side * (target - fill) >= 2 * distance:
                    if target_levels is not None:
                        target_evidence["target_level"] = {
                            "numerator": level.numerator, "denominator": level.denominator,
                        }
                    break
            else:
                return self._result("SKIPPED","NO_VALID_TARGET")
        position = {"kind":"invented_b_price_position","schema":VERSION,
                    "direction":request["direction"],"entry_at":event.record(),
                    "entry_price":text(fill),"initial_stop":text(stop),"stop":text(stop),
                    "target":None if target is None else text(target),
                    "stop_effective_at":event.record(),"tick":text(tick),
                    "exit_model":request["exit_model"],"profile":self.costs["name"],
                    "geometry_identity":self.geometry_identity}
        Position.from_record(position)
        return self._result("FILLED","H1_OPEN_PRICE", price=text(fill), stop_distance=text(distance),
                            effective_spread_pips=text(spread/PIP), position=position,
                            **evidence, **target_evidence)

    def exit_open(self, position, opening, scheduled_exit=False):
        if type(scheduled_exit) is not bool:
            raise ValueError("explicit scheduled-exit flag required")
        if not self._can_execute():
            return self._result("UNAVAILABLE","EXECUTION_SIDE_DATA_UNAVAILABLE")
        p, opening = self._position(position), self._opening(opening)
        opened, effective = Event.from_record(p["entry_at"]), Event.from_record(p["stop_effective_at"])
        if opened >= opening.event:
            return self._result("NO_EXIT","HELD_NOT_BEFORE_OPEN")
        if effective > opening.event:
            return self._result("UNAVAILABLE","PROTECTION_NOT_YET_EFFECTIVE")
        return self._exit_at(p, self._sides(opening), opening.event, scheduled_exit)

    def _exit_at(self, p, prices, event, scheduled_exit):
        """Apply hard protection and scheduled exits to an eligible point observation."""
        side = 1 if p["direction"] == "LONG" else -1
        bid, ask, _ = prices
        price = bid if side == 1 else ask
        stop = decimal(p["stop"],True)
        if side*(price-stop) <= 0:
            return self._exit(p,price-side*F(self.costs["slippage_pips"])*PIP,"STOP_OPEN_GAP",event.record())
        if p["target"] is not None and side*(price-decimal(p["target"],True)) >= 0:
            return self._exit(p,decimal(p["target"],True),"TARGET_OPEN_REACH",event.record())
        if scheduled_exit:
            return self._exit(p,price-side*F(self.costs["slippage_pips"])*PIP,"SCHEDULED_OPEN_EXIT",event.record())
        return self._result("NO_EXIT","OPEN_INSIDE_PROTECTION")

    def exit_hour(self, position, hour, *, as_of, open_ordinal):
        """Evaluate a fully post-fill interval; unknown stop/target order is adverse."""
        data.integer(as_of)
        if not self.source.calendar.start <= as_of <= self.source.calendar.end+60000:
            raise ValueError("as-of outside invented source scope")
        if not self._can_execute():
            return self._result("UNAVAILABLE","EXECUTION_SIDE_DATA_UNAVAILABLE")
        p = self._position(position)
        hour = data.Hour.from_record(hour.record(), "bid_only")
        opening = self._opening(Opening.from_hour(hour,open_ordinal))
        if as_of < hour.available_at:
            return self._result("UNAVAILABLE","HOUR_NOT_AVAILABLE")
        opened, effective = Event.from_record(p["entry_at"]), Event.from_record(p["stop_effective_at"])
        if hour.end <= opened.time:
            return self._result("NO_EXIT","PRE_ENTRY_BAR")
        if opened.time > hour.start or (opened.time == hour.start and opened != opening.event):
            return self._result("UNAVAILABLE","PARTIAL_ENTRY_INTERVAL")
        if effective > opening.event:
            return self._result("UNAVAILABLE","PROTECTION_NOT_EFFECTIVE_FOR_WHOLE_BAR")
        at_open = self.exit_open(position,opening)
        if at_open["status"] == "EXIT":
            # Known opening reach precedes the unresolved later intrabar path.
            return at_open
        side = 1 if p["direction"] == "LONG" else -1
        spread = self._sides(opening)[2]
        low, high = F(hour.low), F(hour.high)
        if side == -1:
            low, high = low+spread, high+spread
        stop = decimal(p["stop"],True)
        target = None if p["target"] is None else decimal(p["target"],True)
        stop_hit = low <= stop if side == 1 else high >= stop
        target_hit = target is not None and (high >= target if side == 1 else low <= target)
        window = {"start":hour.start,"end":hour.end,"available_at":hour.available_at}
        if stop_hit:
            return self._exit(p,stop-side*F(self.costs["slippage_pips"])*PIP,
                              "STOP_ADVERSE_AMBIGUITY" if target_hit else "STOP_RANGE",None,window)
        if target_hit:
            return self._exit(p,target,"TARGET_RANGE",None,window)
        return self._result("NO_EXIT","RANGE_INSIDE_PROTECTION",event_window=window)

    def _exit(self, p, price, reason, event, window=None):
        if price <= 0:
            return self._result("UNAVAILABLE","NONPOSITIVE_EXIT_MODEL")
        side = 1 if p["direction"] == "LONG" else -1
        planned = side*(decimal(p["entry_price"],True)-decimal(p["initial_stop"],True))
        loss = max(F(0),side*(decimal(p["entry_price"],True)-price))
        return self._result("EXIT",reason,price=text(price),event=event,event_window=window,
                            estimated_initial_price_risk=text(planned),observed_price_loss=text(loss),
                            price_risk_excess=text(max(F(0),loss-planned)),
                            event_time_kind=("declared_h1_open_assumption" if event is not None
                                             else "unknown_within_completed_h1"))
