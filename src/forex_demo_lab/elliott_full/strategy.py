"""Causal top-down context and immutable consensus decision snapshots."""
from dataclasses import asdict
from .patterns import Parser, promote
from .incremental import ConfirmedPivots
from .counts import rank
from .interpretations import interpretations, context_state
from .setups import Policy
from .windows import select_window
from .bars import PERIOD
from copy import copy,deepcopy


class Strategy:
    def __init__(self):
        self.bars={f:[] for f in ("D1","H4","H1")}
        self.snapshots=[]
        self.policy=Policy()
        self.contexts={"D1":None,"H4":None}
        self.context_details={}
        self.context_cache={}
        self.counts={}
        self.pivot_streams={f:{r:ConfirmedPivots(r) for r in (2,4,8)} for f in self.bars}

    def fork(self):
        """Copy mutable frontier; published histories and snapshots are append-only."""
        result=copy(self)
        result.bars={k:list(v) for k,v in self.bars.items()}
        result.snapshots=list(self.snapshots)
        result.contexts=dict(self.contexts)
        result.context_details=dict(self.context_details)
        result.context_cache=dict(self.context_cache)
        result.counts=dict(self.counts)
        result.pivot_streams={f:{r:s.fork() for r,s in streams.items()} for f,streams in self.pivot_streams.items()}
        result.policy=copy(self.policy)
        result.policy.active=deepcopy(self.policy.active)
        result.policy.groups=deepcopy(self.policy.groups)
        result.policy.emitted=set(self.policy.emitted)
        result.policy.revisions=list(self.policy.revisions)
        return result

    def _contexts(self,decision_time=None):
        if decision_time is None:
            decision_time=max((h[-1].available for h in self.bars.values() if h),default=0)
        for frame in ("D1","H4"):
            if frame not in self.counts:
                self.contexts[frame]=None
                continue
            latest=self.bars[frame][-1]
            if decision_time>=latest.end+PERIOD[frame]:
                # This invented wrapper has no qualified closure calendar. A
                # missing completed parent bar cannot be presumed a holiday.
                self.contexts[frame]=None
                self.context_details[frame]={"side":None,"stage":"missing_completed_parent_bar",
                                             "latest_end":latest.end,"expected_by":latest.end+PERIOD[frame],"counts":[]}
                continue
            analysis=self.counts[frame]
            parents=() if frame=="D1" else (self.contexts["D1"],)
            cached=self.context_cache.get(frame)
            if cached and cached[0] is analysis and cached[1]==parents and cached[2] is latest:
                detail=cached[3]
            else:
                detail=context_state(analysis["interpretations"],latest,parents,
                                     analysis["incomplete"],analysis["nodes"],self.bars[frame])
                self.context_cache[frame]=(analysis,parents,latest,detail)
            if frame=="H4" and detail["side"]!=self.contexts["D1"]:
                detail={**detail,"local_side":detail["side"],"side":None,"stage":"parent_context_disagreement"}
            self.context_details[frame]=detail
            self.contexts[frame]=detail["side"]

    def on_bar(self,bar):
        history=self.bars[bar.timeframe]
        if history and bar==history[-1]:
            return []
        if history and (bar.start<history[-1].end or bar.available<history[-1].available):
            raise ValueError("bar chronology")
        history.append(bar)
        nodes,counts=[],[]
        streams=self.pivot_streams[bar.timeframe]
        for radius in (2,4,8):
            if streams[radius].size==0 and len(history)>1:
                streams[radius]=ConfirmedPivots.bootstrap(history,radius)
            else:
                streams[radius].append(history)
        all_fine=streams[2].chain
        window=select_window(all_fine)
        fine=window.pivots
        parser=Parser()
        fine_nodes=parser.parse(fine)
        incomplete=parser.incomplete
        for radius in (2,4,8):
            pivots=streams[radius].chain
            if window.start is not None:
                pivots=[p for p in pivots if p.index>=window.start]
            parsed=fine_nodes if radius==2 else promote(fine_nodes,pivots)
            candidates,overflow=interpretations(parsed)
            if pivots and sum(n.anchors[-1]==pivots[-1] for n in parsed)>128:
                overflow=True
            incomplete|=parser.incomplete or overflow
            nodes.extend(parsed)
            if radius in (4,8) or bar.timeframe!="H1":
                counts.extend(candidates)
        self.counts[bar.timeframe]={"nodes":nodes,"interpretations":counts,"incomplete":incomplete,"window":window.record()}
        self._contexts(bar.available)
        parents=(self.contexts["H4"],self.contexts["D1"])
        warm=all(len(h)>=253 for h in self.bars.values())
        signals=self.policy.update(counts,history,parents,warm,incomplete) if bar.timeframe=="H1" else []
        self.snapshots.append({"time":bar.available,"frame":bar.timeframe,"search_incomplete":incomplete,
                               "context":dict(self.contexts),"context_details":dict(self.context_details),
                               "pattern_window":window.record(),
                               "rule_rejection_count":parser.rejection_count,
                               "rule_rejections":parser.rejections,
                               "counts":[n.record() for n in sorted(nodes,key=rank,reverse=True)[:128]],
                               "interpretations":[c.record(parents,history) for c in sorted(counts,key=lambda c:c.rank(parents,history),reverse=True)[:128]],
                               "reason":"warmup" if not warm else self.policy.reason,
                               "signals":[{k:str(v) if hasattr(v,"as_tuple") else v for k,v in asdict(s).items()} for s in signals]})
        return signals
