"""Prospective wave counts built exclusively from observed completed nodes."""
from dataclasses import dataclass
from functools import cached_property
from .contracts import D, digest, precise
from .patterns import MOTIVE, CORRECTIVE
from .counts import observation_only


@dataclass(frozen=True)
class Interpretation:
    legs: tuple
    kind: str

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
        return all(n.depth>=2 for n in self.legs)

    @cached_property
    def rare(self):
        return sum(observation_only(n) for n in self.legs)

    @precise
    def economic_rank(self, parents=()):
        resolved=D(sum(n.depth>=2 for n in self.legs))/len(self.legs)
        return (resolved,sum(p==self.side for p in parents),-(sum(n.depth<2 for n in self.legs)+self.rare))

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
    return list({c.id:c for c in result}.values()),False


def competitive_counts(counts,parents=()):
    counts=list({c.id:c for c in counts}.values())
    if not counts:
        return []
    terminal=max(c.terminal.index for c in counts)
    current=[c for c in counts if c.terminal.index==terminal]
    best=max(c.economic_rank(parents) for c in current)
    return sorted((c for c in current if c.economic_rank(parents)==best),key=lambda c:c.rank(parents),reverse=True)


def context_state(counts,bar,parents=(),incomplete=False,barriers=()):
    if incomplete:
        return {"side":None,"stage":"search_incomplete","counts":[]}
    current=competitive_counts(counts,parents)
    if not current:
        return {"side":None,"stage":"unresolved","counts":[]}
    # A completed competing terminal pattern can make a partial motive count obsolete.
    if any(n.anchors[-1].index>max(c.terminal.index for c in current) for n in barriers):
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
