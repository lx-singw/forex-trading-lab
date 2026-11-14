"""Persistent consensus opportunities; relabelling never refreshes an opportunity."""
from .contracts import D, digest, precise
from .execution import Setup
from .interpretations import competitive_counts
from copy import deepcopy


class Policy:
    def __init__(self,coverage=None):
        self.coverage=coverage
        self.active={}
        self.groups={}
        self.emitted=set()
        self.revisions=[]
        self.reason="warmup"

    def record(self):
        return deepcopy({"active":self.active,"groups":self.groups,"emitted":sorted(self.emitted),
                         "revisions":self.revisions,"reason":self.reason})

    @precise
    def update(self,counts,bars,parents,eligible=True,incomplete=False):
        bar,index=bars[-1],len(bars)-1
        previous=bars[-2].close if len(bars)>1 else bar.close
        def abstain(reason):
            self.active.clear()
            self.reason=reason
            return []
        for key,active in list(self.active.items()):
            boundary=D(active["boundary"])
            if index>active["expiry_index"] or (bar.low<=boundary if active["side"]==1 else bar.high>=boundary):
                self.groups[key]["consumed"]=True
        if len(bars)>1 and (not self.coverage.consecutive(bars[-2],bar) if self.coverage else bar.start!=bars[-2].end):
            for group in self.groups.values():
                group["consumed"]=True
            return abstain("coverage_break")
        if incomplete or not eligible or len(bars)<15:
            return abstain("search_incomplete" if incomplete else "warmup_or_context")
        current=competitive_counts(counts,parents)
        if not current:
            return abstain("no_count")
        if any(c.available>bar.available for c in current):
            return abstain("unavailable_count")
        if any(not c.resolved or c.rare for c in current) or len({(c.side,c.kind) for c in current})!=1:
            return abstain("competitive_disagreement")
        side,kind=current[0].side,current[0].kind
        if tuple(parents)!=(side,side):
            return abstain("context_disagreement")
        terminals={bars[c.terminal.index].lineage for c in current}
        if len(terminals)!=1:
            return abstain("terminal_disagreement")
        terminal=next(iter(terminals))
        alias=digest(["EURUSD",kind,side,terminal])
        economic=digest(["EURUSD",side,terminal])
        # Consensus formation waits for every member, but its expiry belongs to
        # the earliest member. A late coarse confirmation must not extend it.
        known=min(c.available for c in current)
        formation_index=next((i for i,b in enumerate(bars) if b.available>=known),index)
        group=self.groups.setdefault(economic,{"first_index":formation_index,"expiry_index":formation_index+10,"consumed":False,"aliases":[]})
        group["first_index"]=min(group["first_index"],formation_index)
        group["expiry_index"]=min(group["expiry_index"],formation_index+10)
        if alias not in group["aliases"]:
            group["aliases"].append(alias)
        signature=digest(sorted(c.id for c in current))
        trigger=max(c.trigger for c in current) if side==1 else min(c.trigger for c in current)
        starts=[c.legs[-1].anchors[0].index for c in current]
        segment=bars[min(starts):current[0].terminal.index+1]
        boundary=min(b.low for b in segment) if side==1 else max(b.high for b in segment)
        ranges=[max(b.high-b.low,abs(b.high-bars[i-1].close),abs(b.low-bars[i-1].close))
                for i,b in enumerate(bars) if i>=len(bars)-14]
        buffer=max(D(".00001"),sum(ranges)/14*D(".10"))
        stop=boundary-side*buffer
        ceilings=[c.ceiling for c in current if c.ceiling is not None]
        ceiling=(min(ceilings) if side==1 else max(ceilings)) if ceilings else None
        active=self.active.get(economic)
        self.active={economic:active} if active else {}
        if group["consumed"] or index>group["expiry_index"]:
            group["consumed"]=True
            return abstain("consumed_or_expired")
        if (bar.low<=boundary if side==1 else bar.high>=boundary):
            group["consumed"]=True
            return abstain("structural_invalidation")
        if active is None or active["signature"]!=signature:
            if any((b.low<=boundary if side==1 else b.high>=boundary) for b in bars[current[0].terminal.index+1:]):
                group["consumed"]=True
                return abstain("invalidated_before_confirmation")
            if any(side*(b.close-trigger)>0 for b in bars[current[0].terminal.index+1:]):
                group["consumed"]=True
                return abstain("missed_before_confirmation")
            active={"signature":signature,"formed":bar.available,"trigger":str(trigger),"stop":str(stop),
                    "boundary":str(boundary),"kind":kind,"side":side,"ceiling":None if ceiling is None else str(ceiling),
                    "counts":sorted(c.id for c in current),"expiry_index":group["expiry_index"]}
            self.active={economic:active}
            self.revisions.append({"time":bar.available,"group":economic,**active})
            self.reason="formed"
            return []
        self.reason="armed"
        trigger,boundary=D(active["trigger"]),D(active["boundary"])
        if (bar.low<=boundary if side==1 else bar.high>=boundary):
            group["consumed"]=True
            return abstain("structural_invalidation")
        crossed=previous<=trigger<bar.close if side==1 else previous>=trigger>bar.close
        if crossed and bar.available>active["formed"]:
            group["consumed"]=True
            self.emitted.add(economic)
            self.active.clear()
            self.reason="signal"
            return [Setup(economic,side,kind,bar.available,bar.available+60000,trigger,D(active["stop"]),
                          None if active["ceiling"] is None else D(active["ceiling"]),boundary)]
        return []
