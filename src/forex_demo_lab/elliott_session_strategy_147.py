"""Session-aware Elliott decision replay, invented inputs only; no ledger/API.

Calendar edges do not qualify a source. The separate driver rejects source-order
backfill instead of sorting late prices into an earlier decision history.
"""
from bisect import bisect_right
from copy import copy, deepcopy
import hashlib
from pathlib import Path
import re
from types import MappingProxyType

from .elliott_sessions_146 import Calendar, FRAMES, fields
from .elliott_full.contracts import Bar, digest, integer
from .elliott_full.controls import source_bindings as strategy_bindings
from .elliott_full.strategy import Strategy

VERSION="FXDL_ELLIOTT_SESSION_STRATEGY147_V1"
MAX_EVENTS=60000


def source_bindings():
    root=Path(__file__).resolve().parent
    files=(Path(__file__).resolve(),root/"elliott_sessions_146.py")
    return {"adapter":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            "strategy":strategy_bindings()}


class Coverage:
    """Immutable declared schedule shared by forks; no mutable receipt state."""
    __slots__=("calendar","_windows","_indexes","_deadlines","_opens","_sha","_sealed")

    def __init__(self,calendar):
        validated=Calendar.from_record(calendar.record())
        if validated!=calendar:
            raise ValueError("calendar indexes differ from declaration")
        self.calendar=validated
        self._windows=MappingProxyType({f:validated.frame(f) for f in FRAMES})
        self._indexes=MappingProxyType({f:MappingProxyType({w.start:i for i,w in enumerate(ws)})
                                       for f,ws in self._windows.items()})
        self._deadlines=MappingProxyType({f:tuple(w.end+validated.delay for w in ws)
                                         for f,ws in self._windows.items()})
        self._opens=tuple(w.start for w in self._windows["D1"])
        self._sha=validated.sha256
        self._sealed=True

    def __setattr__(self,key,value):
        if getattr(self,"_sealed",False):raise AttributeError("immutable session coverage")
        object.__setattr__(self,key,value)

    def __delattr__(self,key):
        raise AttributeError("immutable session coverage")

    def validate(self,bar):
        if not isinstance(bar,Bar):raise ValueError("bar required")
        if type(bar.lineage) is not str or not re.fullmatch(r"[0-9a-f]{64}",bar.lineage):
            raise ValueError("immutable SHA256 lineage declaration required")
        index=self._indexes[bar.timeframe].get(bar.start)
        if index is None or self._windows[bar.timeframe][index].end!=bar.end:
            raise ValueError("bar outside declared schedule")
        if not bar.end+self.calendar.delay<=bar.available<=self.calendar.end+60_000:
            raise ValueError("bar finalization/receipt boundary")

    def consecutive(self,previous,current):
        if previous.timeframe!=current.timeframe:return False
        try:self.validate(previous);self.validate(current)
        except ValueError:return False
        indexes=self._indexes[current.timeframe]
        return indexes[current.start]==indexes[previous.start]+1

    def issue(self,frame,history,now):
        integer(now)
        if not self.calendar.start<=now<=self.calendar.end+60_000:
            return "calendar_boundary_unknown"
        due=bisect_right(self._deadlines[frame],now)
        if not due:return "no_completed_scheduled_bar"
        if len(history)!=due:return "missing_completed_scheduled_bar"
        expected=self._windows[frame][:due]
        if any(b.timeframe!=frame or b.start!=w.start or b.end!=w.end or b.available>now
               for b,w in zip(history,expected)):
            return "missing_or_unavailable_scheduled_bar"
        return None

    def is_open(self,now):
        integer(now)
        days=self._windows["D1"]
        i=bisect_right(self._opens,now)-1
        return i>=0 and days[i].start<=now<days[i].end

    def ready(self,histories,now):
        return self.is_open(now) and all(self.issue(f,histories[f],now) is None for f in FRAMES)

    def record(self,histories,now):
        return {"calendar_sha256":self._sha,"as_of":now,"session_open":self.is_open(now),
                "ready":self.ready(histories,now),
                "frames":{f:{"issue":self.issue(f,histories[f],now),"observed":len(histories[f]),
                             "scheduled_complete":bisect_right(self._deadlines[f],now)} for f in FRAMES}}


class DecisionReplay:
    """Transactional append-only bar/clock journal; never submits or fills orders.

    Completed bars must come from the invented146 observation component. This
    driver validates timing/bounds; it does not authenticate their price lineage.
    """
    def __init__(self,calendar):
        self.coverage=Coverage(calendar)
        self.strategy=Strategy(self.coverage)
        self.time=calendar.start
        self.events=[]
        self._bindings=source_bindings()

    def publish(self,bar):
        self.coverage.validate(bar)
        event={"kind":"bar","value":bar.record()}
        if self.events and self.events[-1]==event:return []
        if len(self.events)>=MAX_EVENTS:raise ValueError("decision journal limit")
        if bar.available<self.time:raise ValueError("publication receipt reversal")
        if (self.events and self.events[-1]["kind"]=="bar" and bar.available==self.time
                and FRAMES.index(bar.timeframe)<=FRAMES.index(self.events[-1]["value"]["timeframe"])):
            raise ValueError("same-clock publication must order D1/H4/H1")
        trial=self.strategy.fork()
        signals=trial.on_bar(bar)
        self.strategy=trial
        self.time=bar.available
        self.events.append(event)
        return signals

    def publish_batch(self,bars):
        """Commit one receipt's D1/H4/H1 publications together, or none of them."""
        if type(bars) not in (list,tuple) or not 1<=len(bars)<=3 or any(not isinstance(b,Bar) for b in bars):
            raise ValueError("one bounded publication batch required")
        if len({b.available for b in bars})!=1:
            raise ValueError("publication batch must share availability")
        trial=copy(self)
        trial.strategy=self.strategy.fork()
        trial.events=list(self.events)
        signals=[]
        for bar in bars:signals.extend(trial.publish(bar))
        self.__dict__.update(trial.__dict__)
        return signals

    def advance(self,now):
        integer(now)
        if not self.time<=now<=self.coverage.calendar.end+60_000:
            raise ValueError("bounded monotonic decision clock")
        if now==self.time:return
        if len(self.events)>=MAX_EVENTS:raise ValueError("decision journal limit")
        trial=self.strategy.fork()
        trial._contexts(now)
        self.strategy=trial
        self.time=now
        self.events.append({"kind":"clock","value":now})

    def state(self):
        return deepcopy({"time":self.time,"snapshots":self.strategy.snapshots,
                         "policy":self.strategy.policy.record(),"contexts":self.strategy.contexts,
                         "context_details":self.strategy.context_details,
                         "coverage":self.coverage.record(self.strategy.bars,self.time),
                         "kind":"invented_session_strategy_decisions_147",
                         "orders_available":False,"market_cells_run":0,"returns_computed":False})

    def checkpoint(self):
        if self._bindings!=source_bindings():raise ValueError("decision sources changed during run")
        payload={"version":VERSION,"bindings":deepcopy(self._bindings),"calendar":self.coverage.calendar.record(),
                 "events":deepcopy(self.events),"state":self.state()}
        return {"payload":payload,"digest":digest(payload)}

    @classmethod
    def restore(cls,checkpoint):
        fields(checkpoint,("payload","digest"))
        p=checkpoint["payload"]
        fields(p,("version","bindings","calendar","events","state"))
        if p["version"]!=VERSION or p["bindings"]!=source_bindings() or digest(p)!=checkpoint["digest"]:
            raise ValueError("decision checkpoint binding")
        if type(p["events"]) is not list or len(p["events"])>MAX_EVENTS:
            raise ValueError("bounded decision journal required")
        replay=cls(Calendar.from_record(p["calendar"]))
        for event in p["events"]:
            fields(event,("kind","value"))
            if event["kind"]=="bar":
                fields(event["value"],("timeframe","start","end","available","open","high","low","close","lineage"))
                replay.publish(Bar(**event["value"]))
            elif event["kind"]=="clock":replay.advance(event["value"])
            else:raise ValueError("decision event kind")
        if replay.events!=p["events"] or replay.state()!=p["state"]:
            raise ValueError("decision journal/state mismatch")
        return replay
