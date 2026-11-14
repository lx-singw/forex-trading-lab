"""Causal bounded pattern scope; input provenance and risk state are not pruned."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PivotWindow:
    pivots: tuple
    discarded: int

    @property
    def start(self):
        return self.pivots[0].index if self.pivots else None

    def record(self):
        return {"pivot_count":len(self.pivots),"discarded_pivots":self.discarded,
                "first_source_bar":self.start,"left_truncated":self.discarded>0,
                "scope":"most_recent_256_confirmed_fine_pivots"}


def select_window(pivots,limit=256):
    if type(limit) is not int or not 1<=limit<=256:
        raise ValueError("pivot window limit")
    if any(a.index>=b.index or a.available>b.available for a,b in zip(pivots,pivots[1:])):
        raise ValueError("pivot window chronology")
    return PivotWindow(tuple(pivots[-limit:]),max(0,len(pivots)-limit))
