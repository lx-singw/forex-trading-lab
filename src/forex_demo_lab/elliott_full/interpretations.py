"""Prospective wave counts built exclusively from observed completed nodes."""
from dataclasses import dataclass, replace
from functools import cached_property
from .contracts import D, digest, precise
from .patterns import MOTIVE, CORRECTIVE
from .counts import observation_only
from .rulebook import diagnose


@dataclass(frozen=True)
class Interpretation:
    legs: tuple
    kind: str
    unresolved_location: int = 0

    @cached_property
    def side(self):
        return self.legs[0].side

    @cached_property
    def terminal(self):
        return self.legs[-1].anchors[-1]

    @cached_property
    def available(self):
        return max(n.available for n in self.legs)

    @cached_property
    def id(self):
        return digest([self.kind, [n.id for n in self.legs]])

    @cached_property
    def prices(self):
        return (self.legs[0].anchors[0].price,)+tuple(n.anchors[-1].price for n in self.legs)

    @cached_property
    def trigger(self):
        return self.legs[-2].anchors[-1].price

    @cached_property
    def origin(self):
        return self.prices[0]

    @cached_property
    @precise
    def ceiling(self):
        p=self.prices
        if self.kind!="EW5":
            return None
        one,three=abs((p[1]-p[0])/p[0]),abs((p[3]-p[2])/p[2])
        return p[4]*(1+self.side*three) if three<one else None

    @cached_property
    def resolved(self):
        return not self.unresolved_location and all(n.depth>=2 and diagnose(n,"impulse",str(i+1))["state"] not in ("invalid","unsupported")
                   for i,n in enumerate(self.legs))

    @cached_property
    def rare(self):
        return sum(observation_only(n) for n in self.legs)

    @precise
    def economic_rank(self, parents=()):
        resolved=D(sum(n.depth>=2 for n in self.legs))/len(self.legs)
        return (resolved,sum(p==self.side for p in parents),-(sum(n.depth<2 for n in self.legs)+self.rare+self.unresolved_location))

    @precise
    def rank(self, parents=(), bars=()):
        p=self.prices
        ratios=[abs((p[2]-p[1])/(p[1]-p[0])),None,None,None,None]
        if len(p)==5:
            ratios[1]=abs((p[4]-p[3])/(p[3]-p[2]))
            ratios[2]=abs((p[3]-p[2])/(p[1]-p[0]))
        matches,error=0,D(0)
        for i,ratio in enumerate(ratios):
            targets=tuple(map(D,(".382",".5",".618",".786") if i<2 else (".618","1","1.618","2.618")))
            distance=D(1) if ratio is None else min(D(1),min(abs(ratio-t) for t in targets))
            matches+=int(ratio is not None and distance<=D(".05"))
            error+=distance
        sharp={"zigzag","double_zigzag","triple_zigzag"}
        sideways=CORRECTIVE-sharp
        alternation=int(len(self.legs)==4 and ((self.legs[1].family in sharp and self.legs[3].family in sideways) or
                                              (self.legs[1].family in sideways and self.legs[3].family in sharp)))
        channel=0
        if len(self.legs)==4 and bars:
            a,b=self.legs[0].anchors[-1],self.legs[2].anchors[-1]
            c=self.legs[1].anchors[-1]
            if b.index>a.index:
                slope=(b.price-a.price)/(b.index-a.index)
                def envelope(i):
                    return sorted((a.price+slope*(i-a.index),c.price+slope*(i-c.index)))
                segment=bars[a.index:self.terminal.index+1]
                channel=int(bool(segment) and all(envelope(i)[0]-D(".000005")<=bar.low and bar.high<=envelope(i)[1]+D(".000005")
                                                      for i,bar in enumerate(segment,a.index)))
        connectors=sum(len(n.children) for n in self.legs)
        return (*self.economic_rank(parents),matches,-error,alternation,channel,-connectors,self.id)

    def record(self,parents=(),bars=()):
        return {"id":self.id,"kind":self.kind,"side":self.side,"terminal":self.terminal.id,
                "available":self.available,"resolved":self.resolved,"observation_only":bool(self.rare),
                "legs":[n.id for n in self.legs],"rank":[str(x) for x in self.rank(parents,bars)],
                "unresolved_parent_location":bool(self.unresolved_location),
                "trigger":str(self.trigger),"ceiling":None if self.ceiling is None else str(self.ceiling)}


def interpretations(nodes, budget=4096):
    """Enumerate joined 1/2 and 1/2/3/4 counts, without assuming future wave 5."""
    endings={}
    for n in nodes:
        endings.setdefault(n.anchors[-1].id,[]).append(n)
    result=[]
    steps=0
    def preceding(node):
        return endings.get(node.anchors[0].id,())
    first_families={"impulse","leading_53535","leading_33333"}
    for correction in nodes:
        if correction.family not in CORRECTIVE:
            continue
        for motive in preceding(correction):
            steps+=1
            if steps>budget:
                return result,True
            if motive.family not in first_families or motive.side==correction.side:
                continue
            side=motive.side
            if side*(correction.anchors[-1].price-motive.anchors[0].price)>0 and not correction.family.startswith("triangle"):
                result.append(Interpretation((motive,correction),"EW3"))
        for third in preceding(correction):
            if third.family!="impulse" or third.side==correction.side:
                continue
            for second in preceding(third):
                if second.family not in CORRECTIVE or second.family.startswith("triangle") or second.side==third.side:
                    continue
                for first in preceding(second):
                    steps+=1
                    if steps>budget:
                        return result,True
                    if first.family not in first_families or first.side!=third.side:
                        continue
                    count=Interpretation((first,second,third,correction),"EW5")
                    p=count.prices
                    x=[count.side*(v-p[0]) for v in p]
                    if 0<x[2]<x[1]<x[4]<x[3]:
                        result.append(count)
    # Starting a new wave-1 count at an observed wave 3 requires an additional
    # parent relabelling. Preserve it as an alternate with that unresolved
    # requirement; it must not mechanically tie a resolved 1/2/3/4 context.
    located=[c for c in result if c.kind=="EW5" and c.resolved and not c.rare]
    def relabels_parent(c):
        if c.kind!="EW3":
            return False
        start=c.legs[0].anchors[0].index
        for parent in located:
            if (parent.legs[0].anchors[0].index<=start<=parent.legs[2].anchors[0].index and
                c.legs[0].anchors[-1].index==parent.legs[2].anchors[-1].index and
                c.legs[1].anchors[0].index==parent.legs[3].anchors[0].index and
                c.terminal.index==parent.terminal.index):
                return True
        return False
    result=[replace(c,unresolved_location=1) if relabels_parent(c) else c for c in result]
    return list({c.id:c for c in result}.values()),False


def competitive_counts(counts,parents=()):
    counts=list({c.id:c for c in counts}.values())
    if not counts:
        return []
    terminal=max(c.terminal.index for c in counts)
    current=[c for c in counts if c.terminal.index==terminal]
    best=max(c.economic_rank(parents) for c in current)
    return sorted((c for c in current if c.economic_rank(parents)==best),key=lambda c:c.rank(parents),reverse=True)


def context_state(counts,bar,parents=(),incomplete=False,barriers=(),history=()):
    if incomplete:
        return {"side":None,"stage":"search_incomplete","counts":[]}
    # Parent contexts may stay active while their next leg acquires smaller
    # internal patterns. Recency is not ahead of the declared economic rank.
    def open_count(c):
        if c.available>bar.available:
            return False
        if history:
            if c.terminal.index>=len(history) or c.legs[0].anchors[0].index<0:
                return False
            segment=history[c.terminal.index:]
            source=history[c.legs[0].anchors[0].index:]
            if any(b.start!=a.end for a,b in zip(source,source[1:])):
                return False
            observed=segment[1:]
        else:
            observed=(bar,)
        return all(c.side*((b.low if c.side==1 else b.high)-c.terminal.price)>0 for b in observed)
    opened=list({c.id:c for c in counts if open_count(c)}.values())
    def prefix(c):
        return tuple((n.family,tuple((p.index,p.price) for p in n.anchors)) for n in c.legs)
    extensions=[c for c in opened if c.kind=="EW5" and c.resolved and not c.rare]
    # An observed, resolved1/2/3/4 phase replaces its identical1/2 prefix.
    # Its already-finished third leg must not block its own fifth-leg context.
    opened=[c for c in opened if not(c.kind=="EW3" and any(c.side==other.side and prefix(c)==prefix(other)[:2] for other in extensions))]
    best=max((c.economic_rank(parents) for c in opened),default=None)
    current=sorted((c for c in opened if c.economic_rank(parents)==best),key=lambda c:c.rank(parents),reverse=True)
    if not current:
        return {"side":None,"stage":"unresolved","counts":[]}
    # Completion evidence must address this parent boundary at comparable
    # subdivision, rather than an arbitrary smaller node inside its future leg.
    def completed_leg(c,n):
        roots=(c.legs[0].anchors[0],c.terminal)
        return (n.available<=bar.available and n.depth>=min(leg.depth for leg in c.legs) and n.actionable and
                n.anchors[-1].index>c.terminal.index and
                any(n.anchors[0].index==p.index and n.anchors[0].price==p.price for p in roots))
    if any(completed_leg(c,n) for c in current for n in barriers):
        return {"side":None,"stage":"new_terminal_unresolved","counts":[c.id for c in current]}
    sides={c.side for c in current}
    valid=all(c.resolved and not c.rare and c.available<=bar.available and
              c.side*((bar.low if c.side==1 else bar.high)-c.terminal.price)>0 for c in current)
    if len(sides)!=1 or not valid:
        return {"side":None,"stage":"ambiguous_or_invalid","counts":[c.id for c in current]}
    side=next(iter(sides))
    active=all(side*(bar.close-c.trigger)>0 for c in current)
    return {"side":side,"stage":"active_motive" if active else "correction_confirmed",
            "counts":[c.id for c in current]}
