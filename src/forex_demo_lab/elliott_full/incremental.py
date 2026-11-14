"""Append-only delayed pivot confirmation; batch detector remains the reference."""
from copy import copy
from .contracts import digest
from .patterns import Pivot, confirmed


class ConfirmedPivots:
    def __init__(self,radius):
        if type(radius) is not int or radius not in (2,4,8):
            raise ValueError("incremental radius")
        self.radius=radius
        self.size=0
        self.last=None
        self.journal=[]
        self.chain=[]

    def fork(self):
        result=copy(self)
        result.journal=list(self.journal)
        result.chain=list(self.chain)
        return result

    def append(self,bars):
        if len(bars)!=self.size+1 or (self.size and bars[-2]!=self.last):
            raise ValueError("incremental append prefix")
        radius=self.radius
        i=len(bars)-radius-1
        if i>=radius:
            center=bars[i]
            neighbors=bars[i-radius:i]+bars[i+1:i+radius+1]
            high=all(center.high>b.high for b in neighbors)
            low=all(center.low<b.low for b in neighbors)
            if high!=low:
                kind="high" if high else "low"
                p=Pivot(digest([center.lineage,kind,radius]),i,center.end,bars[-1].available,
                        center.high if high else center.low,kind,radius)
                self.journal.append(p)
                if self.chain and self.chain[-1].kind==kind:
                    if (p.price-self.chain[-1].price)*(1 if high else -1)>0:
                        self.chain[-1]=p
                else:
                    self.chain.append(p)
        self.size=len(bars)
        self.last=bars[-1]
        return self.chain

    @classmethod
    def bootstrap(cls,bars,radius):
        result=cls(radius)
        result.journal,result.chain=confirmed(bars,radius)
        result.size=len(bars)
        result.last=bars[-1] if bars else None
        return result
