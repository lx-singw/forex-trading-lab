"""Whole-prefix research checkpoint, including counts, pending signals and ledger."""
from copy import deepcopy
from dataclasses import asdict
from .contracts import Bar, Quote, bindings, digest
from .execution import Ledger
from .strategy import Strategy


class Engine:
    def __init__(self,profile="base"):
        self.profile=profile
        self.strategy=Strategy()
        self.ledger=Ledger(profile)
        self.pending=None
        self.events=[]
        self.time=-1

    def step(self,event):
        if set(event)!={"kind","value"} or event["kind"] not in ("bar","quote","finish"):
            raise ValueError("engine event")
        event=deepcopy(event)
        if self.events and event==self.events[-1]:
            return "duplicate"
        if self.ledger.finished:
            raise ValueError("engine finished")
        before=dict(self.__dict__)
        self.strategy=self.strategy.fork()
        self.ledger=self.ledger.fork()
        self.events=list(self.events)
        try:
            if event["kind"]=="bar":
                bar=Bar(**event["value"])
                if bar.available<self.time:
                    raise ValueError("publication chronology")
                signals=self.strategy.on_bar(bar)
                if bar.timeframe=="H1":
                    self.pending=signals[0] if len(signals)==1 else None
                elif self.pending and any(s!=self.pending.side for s in self.strategy.contexts.values()):
                    self.pending=None
                self.time=bar.available
                result="bar"
            elif event["kind"]=="quote":
                quote=Quote(**event["value"])
                if quote.time<self.time:
                    raise ValueError("receipt chronology")
                result=self.ledger.on_quote(quote,self.pending)
                if self.pending and result not in ("signal_timing","entry_spread","unavailable_quote"):
                    self.pending=None
                self.time=quote.time
            else:
                quote=Quote(**event["value"])
                if quote.time!=self.time:
                    raise ValueError("boundary not latest observation")
                result=self.ledger.finish(quote)
                self.pending=None
            self.events.append(event)
            return result
        except Exception:
            self.__dict__.clear()
            self.__dict__.update(before)
            raise

    def state(self):
        def setup(s):
            return {k:str(v) if hasattr(v,"as_tuple") else v for k,v in asdict(s).items()}
        return deepcopy({"time":self.time,"ledger":self.ledger.state(),"snapshots":self.strategy.snapshots,
                         "pending":None if self.pending is None else setup(self.pending),
                         "policy":self.strategy.policy.record(),"contexts":self.strategy.contexts})

    def checkpoint(self):
        payload={"version":"EW_FULL_V1_ENGINE","bindings":bindings(),"profile":self.profile,
                 "events":deepcopy(self.events),"state":self.state()}
        return {"payload":payload,"digest":digest(payload)}

    @classmethod
    def restore(cls,checkpoint):
        p=checkpoint["payload"]
        if p["version"]!="EW_FULL_V1_ENGINE" or p["bindings"]!=bindings() or digest(p)!=checkpoint["digest"]:
            raise ValueError("engine checkpoint binding")
        engine=cls(p["profile"])
        for event in p["events"]:
            engine.step(event)
        if engine.state()!=p["state"]:
            raise ValueError("engine prefix mismatch")
        return engine
