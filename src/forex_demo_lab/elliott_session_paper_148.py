"""Invented session-aware paper replay. No account, terminal or order interface.

Calendar gating surrounds the unchanged hypothetical ledger. Its UTC receipt-day
financing and conservative missing-boundary pause are intentionally preserved.
"""
from copy import copy, deepcopy
from dataclasses import asdict, replace
import hashlib
from pathlib import Path

from . import elliott_session_strategy_147 as decisions
from .elliott_sessions_146 import Calendar, fields
from .elliott_full.contracts import Bar, Quote, digest, integer
from .elliott_full.execution import Ledger

VERSION="FXDL_ELLIOTT_SESSION_PAPER148_V1"
MAX_EVENTS=60000
BAR_FIELDS=("timeframe","start","end","available","open","high","low","close","lineage")
QUOTE_FIELDS=("time","source","sequence","bid","ask","session_open")


def source_bindings():
    path=Path(__file__).resolve()
    return {"paper":{path.name:hashlib.sha256(path.read_bytes()).hexdigest()},"decisions":decisions.source_bindings()}


def setup_record(setup):
    return None if setup is None else {k:str(v) if hasattr(v,"as_tuple") else v for k,v in asdict(setup).items()}


def publication_batch(value):
    if type(value) is not list or not 1<=len(value)<=3:raise ValueError("paper publication batch")
    for row in value:fields(row,BAR_FIELDS)
    bars=[Bar(**row) for row in value]
    if len({bar.timeframe for bar in bars})!=len(bars):raise ValueError("one publication per timeframe per batch")
    return bars


class PaperReplay:
    """Atomic raw-event journal; paper cash only, independent of study admission."""
    def __init__(self,calendar,profile="base"):
        self.decisions=decisions.DecisionReplay(calendar)
        self.ledger=Ledger(profile)
        self.profile=profile
        self.pending=None
        self.time=calendar.start
        self.events=[]
        self.cancellations=[]
        self.quote_gates=[]
        self.last_quote=None
        self.last_publications={}
        self._bindings=source_bindings()

    def fork(self):
        trial=copy(self)
        trial.decisions=copy(self.decisions)
        trial.decisions.strategy=self.decisions.strategy.fork()
        trial.decisions.events=list(self.decisions.events)
        trial.ledger=self.ledger.fork()
        trial.events=list(self.events)
        trial.cancellations=list(self.cancellations)
        trial.quote_gates=list(self.quote_gates)
        trial.last_publications=dict(self.last_publications)
        return trial

    def _cancel(self,reason):
        if self.pending is not None:
            self.cancellations.append({"time":self.time,"key":self.pending.key,"reason":reason})
            self.pending=None

    def _recheck(self):
        if self.pending is None:return
        coverage=self.decisions.coverage
        strategy=self.decisions.strategy
        if self.time>min(self.pending.expires,self.pending.formed+60000):self._cancel("expired")
        elif not coverage.is_open(self.time):self._cancel("calendar_closed")
        elif not coverage.ready(strategy.bars,self.time):self._cancel("scheduled_coverage_missing")
        elif any(side!=self.pending.side for side in strategy.contexts.values()):self._cancel("parent_context_lost")

    def _effective_quote(self,quote):
        coverage=self.decisions.coverage
        source_open=coverage.is_open(quote.source)
        receipt_open=coverage.is_open(quote.time)
        effective=replace(quote,session_open=quote.session_open and source_open and receipt_open)
        return effective,{"time":quote.time,"sequence":quote.sequence,"declared_open":quote.session_open,
                          "calendar_source_open":source_open,"calendar_receipt_open":receipt_open,
                          "effective_open":effective.session_open}

    def step(self,event):
        fields(event,("kind","value"))
        if event["kind"] not in ("bars","clock","quote","finish"):raise ValueError("paper event kind")
        event=deepcopy(event)
        if self.ledger.finished:
            if event["kind"]=="finish" and self.events and event==self.events[-1]:return "duplicate_finish"
            raise ValueError("paper replay finished")
        if event["kind"]=="quote":
            fields(event["value"],QUOTE_FIELDS)
            quote=Quote(**event["value"])
            if self.last_quote is not None and quote.sequence==self.last_quote.sequence:
                if quote==self.last_quote:return "duplicate"
                raise ValueError("conflicting raw quote duplicate")
        elif event["kind"]=="bars":
            bars=publication_batch(event["value"])
            if all(self.last_publications.get(bar.timeframe)==bar for bar in bars):return "duplicate"
        elif self.events and event==self.events[-1]:return "duplicate"
        if len(self.events)>=MAX_EVENTS:raise ValueError("paper journal limit")
        trial=self.fork()
        result=trial._apply(event)
        trial.events.append(event)
        self.__dict__.update(trial.__dict__)
        return result

    def _apply(self,event):
        kind,value=event["kind"],event["value"]
        if kind=="bars":
            bars=publication_batch(value)
            signals=self.decisions.publish_batch(bars)
            self.last_publications.update({bar.timeframe:bar for bar in bars})
            self.time=self.decisions.time
            if any(b.timeframe=="H1" for b in bars):
                self._cancel("new_h1_decision")
                self.pending=signals[0] if len(signals)==1 else None
            self._recheck()
            return "bars"
        if kind=="clock":
            integer(value);self.decisions.advance(value);self.time=self.decisions.time
            self._recheck()
            return "clock"
        fields(value,QUOTE_FIELDS)
        quote=Quote(**value)
        if kind=="finish":
            if quote!=self.last_quote or quote.time!=self.time:raise ValueError("boundary must be exact latest raw quote")
            effective,_=self._effective_quote(quote)
            result=self.ledger.finish(effective)
            self.pending=None
            return result
        self.decisions.advance(quote.time);self.time=self.decisions.time
        self._recheck()
        effective,gate=self._effective_quote(quote)
        # Calendar-inconsistent/closed quotes remain in the journal, unavailable
        # for fills. Missing bars do not suppress protection on executable quotes.
        result=self.ledger.on_quote(effective,self.pending)
        gate["result"]=result
        self.quote_gates.append(gate)
        if self.pending is not None and result not in ("signal_timing","entry_spread","unavailable_quote"):
            self.pending=None
        self.last_quote=quote
        return result

    def state(self):
        return deepcopy({"kind":"invented_session_paper_148","profile":self.profile,"time":self.time,
                         "decisions":self.decisions.state(),"ledger":self.ledger.state(),
                         "pending":setup_record(self.pending),"cancellations":self.cancellations,
                         "quote_gates":self.quote_gates,"last_raw_quote":None if self.last_quote is None else self.last_quote.record(),
                         "last_publications":{frame:bar.record() for frame,bar in self.last_publications.items()},
                         "orders_available":False,"market_cells_run":0,"market_returns":None,
                         "limitations":["invented observations and hypothetical costs only",
                                        "unchanged UTC receipt-day financing and conservative boundary pause",
                                        "no qualified source/control comparison or native adapter"]})

    def checkpoint(self):
        if self._bindings!=source_bindings():raise ValueError("paper sources changed during run")
        p={"version":VERSION,"bindings":deepcopy(self._bindings),"calendar":self.decisions.coverage.calendar.record(),
           "profile":self.profile,"events":deepcopy(self.events),"state":self.state()}
        return {"payload":p,"digest":digest(p)}

    @classmethod
    def restore(cls,checkpoint):
        fields(checkpoint,("payload","digest"))
        p=checkpoint["payload"]
        fields(p,("version","bindings","calendar","profile","events","state"))
        if p["version"]!=VERSION or p["bindings"]!=source_bindings() or digest(p)!=checkpoint["digest"]:
            raise ValueError("paper checkpoint binding")
        if type(p["events"]) is not list or len(p["events"])>MAX_EVENTS:raise ValueError("paper journal bound")
        replay=cls(Calendar.from_record(p["calendar"]),p["profile"])
        for event in p["events"]:replay.step(event)
        if replay.events!=p["events"] or replay.state()!=p["state"]:raise ValueError("paper prefix/state mismatch")
        return replay
