"""Causal top-down context and immutable consensus decision snapshots."""
from dataclasses import asdict
from .patterns import Parser, confirmed, promote
from .counts import rank
from .interpretations import interpretations, context_state
from .setups import Policy
from copy import copy,deepcopy


class Strategy:
    def __init__(self):
        self.bars={f:[] for f in ("D1","H4","H1")}
        self.snapshots=[]
        self.policy=Policy()
        self.contexts={"D1":None,"H4":None}
        self.context_details={}
        self.counts={}

    def fork(self):
        """Copy mutable frontier; published histories and snapshots are append-only."""
        result=copy(self)
        result.bars={k:list(v) for k,v in self.bars.items()}
        result.snapshots=list(self.snapshots)
        result.contexts=dict(self.contexts)
        result.context_details=dict(self.context_details)
        result.counts=dict(self.counts)
        result.policy=copy(self.policy)
        result.policy.active=deepcopy(self.policy.active)
        result.policy.groups=deepcopy(self.policy.groups)
        result.policy.emitted=set(self.policy.emitted)
        result.policy.revisions=list(self.policy.revisions)
        return result

    def _contexts(self):
        for frame in ("D1","H4"):
            if frame not in self.counts:
                self.contexts[frame]=None
                continue
            analysis=self.counts[frame]
            parents=() if frame=="D1" else (self.contexts["D1"],)
            detail=context_state(analysis["interpretations"],self.bars[frame][-1],parents,
                                 analysis["incomplete"],analysis["nodes"])
            self.context_details[frame]=detail
            self.contexts[frame]=detail["side"]
            if frame=="H4" and self.contexts["H4"]!=self.contexts["D1"]:
                self.contexts[frame]=None

    def on_bar(self,bar):
        history=self.bars[bar.timeframe]
        if history and bar==history[-1]:
            return []
        if history and (bar.start<history[-1].end or bar.available<history[-1].available):
            raise ValueError("bar chronology")
        history.append(bar)
        nodes,counts=[],[]
        _,fine=confirmed(history,2)
        parser=Parser()
        fine_nodes=parser.parse(fine)
        incomplete=parser.incomplete
        for radius in (2,4,8):
            _,pivots=confirmed(history,radius)
            parsed=fine_nodes if radius==2 else promote(fine_nodes,pivots)
            candidates,overflow=interpretations(parsed)
            if pivots and sum(n.anchors[-1]==pivots[-1] for n in parsed)>128:
                overflow=True
            incomplete|=parser.incomplete or overflow
            nodes.extend(parsed)
            if radius in (4,8) or bar.timeframe!="H1":
                counts.extend(candidates)
        self.counts[bar.timeframe]={"nodes":nodes,"interpretations":counts,"incomplete":incomplete}
        self._contexts()
        parents=(self.contexts["H4"],self.contexts["D1"])
        warm=all(len(h)>=253 for h in self.bars.values())
        signals=self.policy.update(counts,history,parents,warm,incomplete) if bar.timeframe=="H1" else []
        self.snapshots.append({"time":bar.available,"frame":bar.timeframe,"search_incomplete":incomplete,
                               "context":dict(self.contexts),"context_details":dict(self.context_details),
                               "counts":[n.record() for n in sorted(nodes,key=rank,reverse=True)[:128]],
                               "interpretations":[c.record(parents,history) for c in sorted(counts,key=lambda c:c.rank(parents,history),reverse=True)[:128]],
                               "reason":"warmup" if not warm else self.policy.reason,
                               "signals":[{k:str(v) if hasattr(v,"as_tuple") else v for k,v in asdict(s).items()} for s in signals]})
        return signals
