"""Independent invented EURUSD ledger. No network or order submission."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from decimal import ROUND_FLOOR, ROUND_CEILING
from .contracts import D, Quote, digest, bindings, precise
from copy import deepcopy,copy

TICK = D(".00001")
PIP = D(".0001")


@dataclass(frozen=True)
class Setup:
    key: str
    side: int
    kind: str
    formed: int
    expires: int
    trigger: object
    stop: object
    ceiling: object = None
    invalidation: object = None

    def __post_init__(self):
        if type(self.side) is not int or self.side not in (-1, 1) or self.kind not in ("EW3", "EW5"):
            raise ValueError("setup side/type")
        if type(self.formed) is not int or type(self.expires) is not int or not 0 <= self.formed < self.expires or not self.key:
            raise ValueError("setup times/key")
        for name in ("trigger", "stop"):
            object.__setattr__(self, name, D(getattr(self, name)))
        if self.ceiling is not None:
            object.__setattr__(self, "ceiling", D(self.ceiling))
        if self.invalidation is not None:
            object.__setattr__(self, "invalidation", D(self.invalidation))
        if self.stop <= 0 or (self.trigger-self.stop)*self.side <= 0:
            raise ValueError("setup geometry")


class Ledger:
    def __init__(self, profile="base"):
        if profile not in ("base", "adverse"):
            raise ValueError("profile")
        self.profile = profile
        self.fee = D(7 if profile == "base" else 10)
        self.slip = D(".2" if profile == "base" else ".5")*PIP
        self.latency = 250 if profile == "base" else 1000
        self.cash = D(10000)
        self.position = None
        self.used = set()
        self.paused = False
        self.day = None
        self.anchor = self.cash
        self.mark = self.cash
        self.last = None
        self.events = []
        self.trades = []
        self._inputs = []
        self._last_executable = None
        self._finish_quote = None
        self.finished = False

    def _price(self, q):
        return q.bid, max(q.ask, q.bid+D(".00012")) if self.profile == "adverse" else q.ask

    def _equity(self, q):
        if not self.position:
            return self.cash
        p = self.position
        bid, ask = self._price(q)
        return self.cash+p["side"]*((bid if p["side"] == 1 else ask)-p["entry"])*p["lots"]*100000

    def _roll(self, q):
        day = q.time//86400000
        if self.day is None:
            self.day = day
        while self.day < day:
            self.day += 1
            self.anchor, self.paused = self.mark, False
            if self.position:
                previous = datetime.fromtimestamp((self.day-1)*86400, timezone.utc)
                multiple = 3 if previous.weekday() == 2 else 0 if previous.weekday() >= 5 else 1
                rate = D("3" if self.profile == "base" else "4.5") if self.position["side"] == 1 else D("1.5" if self.profile == "base" else "2.25")
                debit = rate*multiple*self.position["lots"]
                self.cash -= debit
                self.position["financing"] += debit
                self.events.append({"kind": "financing", "time": self.day*86400000, "debit": str(debit)})
                self.mark -= debit

    def fork(self):
        result=copy(self)
        result.position=None if self.position is None else dict(self.position)
        result.used=set(self.used)
        result.events=list(self.events)
        result.trades=list(self.trades)
        result._inputs=list(self._inputs)
        return result

    @precise
    def on_quote(self, q, signal=None):
        before = self.fork().__dict__
        try:
            return self._apply(q, signal)
        except Exception:
            self.__dict__.clear()
            self.__dict__.update(before)
            raise

    def _apply(self, q, signal=None):
        if self.finished:
            raise ValueError("ledger finished")
        raw = q.record()
        sraw = None if signal is None else {k: str(v) if hasattr(v, "as_tuple") else v for k,v in asdict(signal).items()}
        record = {"quote": raw, "signal": sraw}
        if self._inputs and q.sequence == self._inputs[-1]["quote"]["sequence"]:
            if record == self._inputs[-1]:
                return "duplicate"
            raise ValueError("conflicting duplicate")
        if self.last and (q.sequence <= self.last.sequence or q.time < self.last.time or q.source < self.last.source):
            raise ValueError("chronology")
        self._inputs.append(record)
        self._roll(q)
        if self.last and q.time//86400000 != self.last.time//86400000 and q.time-self.last.time > 2000:
            self.paused = True  # No qualified boundary mark/calendar in this invented adapter.
        fresh = q.time-q.source <= 2000 and (not self.last or q.source > self.last.source) and q.session_open
        held = self.position is not None
        result = "no_signal"
        if fresh:
            self._last_executable=q
            self.mark = self._equity(q)
            if self.mark <= self.anchor*D(".99"):
                self.paused = True
            if held:
                p = self.position
                bid, ask = self._price(q)
                price = bid if p["side"] == 1 else ask
                stop = p["side"]*(price-p["stop"]) <= 0
                target = p["side"]*(price-p["target"]) >= 0
                timeout = q.time-p["time"] >= 72*3600000
                if stop or target or timeout:
                    fill = p["target"] if target and not stop else price-p["side"]*self.slip
                    self._close(q,fill,"stop" if stop else "target" if target else "time")
                result = "held"
            if signal is not None:
                result = self._enter(q, signal, held)
        else:
            result = "unavailable_quote"
        self.last = q
        self.events.append({"kind": "quote", "time": q.time, "sequence": q.sequence, "result": result,
                            "cash": str(self.cash), "observed_equity": str(self.mark), "paused": self.paused})
        return result

    def _close(self,q,fill,reason):
        if fill<=0:
            raise ValueError("nonpositive executable exit")
        p=self.position
        gross=p["side"]*(fill-p["entry"])*100000*p["lots"]
        self.cash+=gross-self.fee/2*p["lots"]
        trade={"key":p["key"],"reason":reason,"gross":str(gross),
               "net":str(gross-self.fee*p["lots"]-p["financing"]),
               "estimated_risk":str(p["risk"]),"exit":str(fill),"time":q.time}
        self.trades.append(trade)
        self.events.append({"kind":"exit",**trade})
        self.position=None
        self.mark=self.cash
        if self.mark<=self.anchor*D(".99"):
            self.paused=True

    @precise
    def finish(self,q):
        if self.finished:
            if q==self._finish_quote:
                return "duplicate_finish"
            raise ValueError("conflicting boundary")
        if q!=self.last or q!=self._last_executable:
            raise ValueError("declared final quote unavailable; no earlier-price fallback")
        before=self.fork().__dict__
        try:
            if self.position:
                bid,ask=self._price(q)
                side=self.position["side"]
                self._close(q,(bid if side==1 else ask)-side*self.slip,"boundary")
            self.finished=True
            self._finish_quote=q
            self.events.append({"kind":"finish","time":q.time,"sequence":q.sequence,"cash":str(self.cash)})
            return "finished"
        except Exception:
            self.__dict__.clear();self.__dict__.update(before)
            raise

    def _enter(self, q, s, held):
        if not s.formed+self.latency < q.source or q.time > min(s.expires, s.formed+60000):
            return "signal_timing"
        bid, ask = self._price(q)
        if ask-bid > D(".00015"):
            return "entry_spread"
        if s.key in self.used:
            return "consumed"
        self.used.add(s.key)
        if held or self.position:
            return "position_limit"
        if self.paused:
            return "daily_pause"
        if self.mark <= 0:
            return "insolvent"
        entry = ask+self.slip if s.side == 1 else bid-self.slip
        stop = (s.stop/TICK).to_integral_value(rounding=ROUND_FLOOR if s.side == 1 else ROUND_CEILING)*TICK
        distance = s.side*(entry-stop)
        boundary=stop if s.invalidation is None else s.invalidation
        if distance <= ask-bid+self.slip or s.side*((bid if s.side == 1 else ask)-boundary) <= 0:
            return "invalidated"
        target = ((entry+s.side*2*distance)/TICK).to_integral_value(rounding=ROUND_FLOOR if s.side == 1 else ROUND_CEILING)*TICK
        if min(entry, stop, target) <= 0 or (s.ceiling is not None and s.side*(target-s.ceiling) > 0):
            return "target_geometry"
        per_lot = (distance+self.slip)*100000+self.fee
        margin = entry*100000/30
        lots = (min(self.mark*D(".0025")/per_lot, self.cash/(margin+self.fee/2), D(1))/D(".01")).to_integral_value(rounding=ROUND_FLOOR)*D(".01")
        if lots < D(".01"):
            return "minimum_volume"
        if self.mark-lots*((ask-bid+2*self.slip)*100000+self.fee) <= self.anchor*D(".99"):
            return "daily_headroom"
        risk = per_lot*lots
        if risk > self.mark*D(".0025") or lots*(margin+self.fee/2) > self.cash:
            raise ValueError("risk invariant")
        self.cash -= self.fee/2*lots
        self.position = {"key": s.key, "side": s.side, "lots": lots, "entry": entry, "stop": stop,
                         "target": target, "time": q.time, "risk": risk, "financing": D(0)}
        self.mark = self._equity(q)
        self.events.append({"kind": "entry", **{k: str(v) for k,v in self.position.items()}})
        return "entered"

    def state(self):
        return {"cash": str(self.cash), "mark": str(self.mark), "position": None if self.position is None else
                {k: str(v) if hasattr(v,"as_tuple") else v for k,v in self.position.items()},
                "used": sorted(self.used), "day": self.day, "anchor": str(self.anchor), "paused": self.paused,
                "events": self.events, "trades": self.trades,"finished":self.finished}

    def checkpoint(self):
        payload = {"version": "EW_FULL_V1_LEDGER", "bindings": bindings(), "profile": self.profile, "inputs": self._inputs, "state": self.state(),
                   "finish_quote":None if self._finish_quote is None else self._finish_quote.record()}
        return deepcopy({"payload": payload, "digest": digest(payload)})

    @classmethod
    def restore(cls, checkpoint):
        p = checkpoint["payload"]
        if p["version"] != "EW_FULL_V1_LEDGER" or p["bindings"] != bindings() or digest(p) != checkpoint["digest"]:
            raise ValueError("checkpoint binding")
        ledger = cls(p["profile"])
        for event in p["inputs"]:
            ledger.on_quote(Quote(**event["quote"]), None if event["signal"] is None else Setup(**event["signal"]))
        if p["finish_quote"] is not None:
            ledger.finish(Quote(**p["finish_quote"]))
        if ledger.state() != p["state"]:
            raise ValueError("checkpoint replay mismatch")
        return ledger
