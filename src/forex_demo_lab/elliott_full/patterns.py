"""Finite pattern grammar. Geometry never establishes unseen child subdivisions."""
from dataclasses import dataclass, replace
from decimal import Decimal
from itertools import combinations
from functools import cached_property
from .contracts import D, digest, precise

MOTIVE = {"impulse", "truncated_impulse", "leading_53535", "leading_33333", "ending_diagonal", "expanding_diagonal"}
CORRECTIVE = {"zigzag", "flat_regular", "flat_expanded", "flat_running", "triangle_contracting", "triangle_barrier", "triangle_running", "triangle_expanding", "double_zigzag", "triple_zigzag", "double_three", "triple_three"}
OBSERVATION_ONLY = {"leading_33333", "expanding_diagonal", "triangle_expanding", "triple_three"}
CATALOGUE = sorted(MOTIVE | CORRECTIVE)


@dataclass(frozen=True)
class Pivot:
    id: str
    index: int
    time: int
    available: int
    price: Decimal
    kind: str
    radius: int

    def __deepcopy__(self,memo):
        return self


def confirmed(bars, radius):
    journal, alternating = [], []
    for i in range(radius, len(bars) - radius):
        window = bars[i-radius:i+radius+1]
        high = all(bars[i].high > b.high for j, b in enumerate(window) if j != radius)
        low = all(bars[i].low < b.low for j, b in enumerate(window) if j != radius)
        if high == low:
            continue
        p = Pivot(digest([bars[i].lineage, "high" if high else "low", radius]), i,
                  bars[i].end, bars[i+radius].available, bars[i].high if high else bars[i].low,
                  "high" if high else "low", radius)
        journal.append(p)
        if alternating and alternating[-1].kind == p.kind:
            if (p.price - alternating[-1].price) * (1 if high else -1) > 0:
                alternating[-1] = p
        else:
            alternating.append(p)
    return journal, alternating


@precise
def geometry(prices, tick=D(".000005")):
    """Return all matching geometric families; internal grammar checked separately."""
    p = list(map(D, prices))
    if len(p) not in (4, 6) or min(p) <= 0 or p[0] == p[1]:
        return []
    side = 1 if p[1] > p[0] else -1
    x = [side * (v-p[0]) for v in p]
    if any((x[i]-x[i-1]) * (1 if i % 2 else -1) <= 0 for i in range(1, len(x))):
        return []
    result = []
    if len(p) == 4:
        a, b, c = x[1:]
        if 0 < b < a and c > a:
            result.append("zigzag")
        retrace = (a-b)/a
        if D(".90") <= retrace <= 1 and c >= a+tick:
            result.append("flat_regular")
        if b <= -tick and c >= a+tick:
            result.append("flat_expanded")
        if b <= -tick and 0 < c <= a-tick:
            result.append("flat_running")
        return result
    a, b, c, d, e = x[1:]
    lengths = [abs((p[i]-p[i-1])/p[i-1]) for i in range(1, 6)]
    motive = b > 0 and c > a and d > b and e > d and lengths[2] >= min(lengths[0], lengths[4])
    if motive and d > a:
        result.append("impulse" if e > c else "truncated_impulse")
    if motive and d < a:
        contracting = (c-a)/(2) > (e-c)/(2) and lengths[0] > lengths[2] > lengths[4]
        expanding = lengths[0] < lengths[2] < lengths[4]
        if contracting:
            result.extend(["leading_53535", "leading_33333", "ending_diagonal"])
        if expanding:
            result.append("expanding_diagonal")
    # Corrective ABCDE, including a running B. E may overshoot A-C.
    widths = (a-b, c-d)
    if e > b and e < a and d > b and c < a and widths[1] < widths[0]:
        result.append("triangle_running" if b < 0 else "triangle_contracting")
    tolerance = max(abs(x[i]-x[i-1]) for i in range(1, 6))*D(".05")
    if e > b and e < a and c < a and abs(d-b) <= tolerance:
        result.append("triangle_barrier")
    if c > a and d < b and e > c:
        result.append("triangle_expanding")
    return result


def grammar(family, children):
    kinds = ["M" if c.family in MOTIVE else "C" for c in children]
    forms = {"impulse": "MCMCM", "truncated_impulse": "MCMCM", "zigzag": "MCM",
             "leading_53535": "MCMCM", "leading_33333": "CCCCC", "ending_diagonal": "CCCCC", "expanding_diagonal": "CCCCC"}
    required = forms.get(family, "CCC" if family.startswith("flat") else "CCCCC")
    if "".join(kinds) != required:
        return False
    if family in ("impulse", "truncated_impulse"):
        if children[2].family != "impulse" or children[0].family not in ("impulse","leading_53535","leading_33333") or children[4].family not in ("impulse","truncated_impulse","ending_diagonal"):
            return False
        if any(c.family.startswith("triangle") for c in children[1:2]):
            return False
    if family == "zigzag" and children[0].family == "ending_diagonal":
        return False
    if family.startswith("flat") and children[2].family not in ("impulse","truncated_impulse","ending_diagonal"):
        return False
    return True


@dataclass(frozen=True)
class Node:
    family: str
    anchors: tuple
    children: tuple = ()
    depth: int = 1

    def __deepcopy__(self,memo):
        return self

    @cached_property
    def id(self):
        return digest([self.family, [p.id for p in self.anchors], [c.id for c in self.children]])

    @cached_property
    def side(self):
        return 1 if self.anchors[1].price > self.anchors[0].price else -1

    @cached_property
    def available(self):
        return max([p.available for p in self.anchors] + [c.available for c in self.children])

    @cached_property
    def actionable(self):
        def rare(n):
            return n.family in OBSERVATION_ONLY or any(rare(c) for c in n.children)
        return self.depth >= 2 and not rare(self)

    def record(self):
        return {"id": self.id, "family": self.family, "anchors": [p.id for p in self.anchors],
                "pivot_records": [{"id":p.id,"time":p.time,"available":p.available,"price":str(p.price),"index":p.index} for p in self.anchors],
                "side": self.side, "available": self.available, "depth": self.depth,
                "state": "valid_at_resolution" if self.depth >= 2 else "insufficient_resolution",
                "children": [c.record() for c in self.children], "actionable": self.actionable}


class Parser:
    def __init__(self, budget=4096, cap=128):
        self.budget, self.cap = budget, cap
        self.expansions, self.incomplete = 0, False

    @precise
    def parse(self, pivots):
        self.expansions, self.incomplete = 0, False
        if len(pivots) > 256:
            self.incomplete = True
            return []
        table, starts, nodes = {}, {}, []
        class Exhausted(Exception):
            pass
        def spend():
            self.expansions += 1
            if self.expansions > self.budget:
                raise Exhausted()
        def add(start, end, node):
            key = (start, end)
            bucket = table.setdefault(key, {})
            if node.id in bucket:
                return
            bucket[node.id] = node
            starts.setdefault(start, {}).setdefault(end, {})[node.id] = node
            nodes.append(node)
            if len(bucket) > self.cap:
                raise Exhausted()
        def routes(start, end, remaining):
            if remaining == 1:
                for child in tuple(table.get((start, end), {}).values()):
                    spend()
                    yield (child,)
                return
            for boundary, bucket in tuple(starts.get(start, {}).items()):
                if boundary > end-3*(remaining-1):
                    continue
                spend()
                for child in tuple(bucket.values()):
                    for suffix in routes(boundary, end, remaining-1):
                        yield (child, *suffix)
        try:
            for width in range(3, len(pivots)):
                for start in range(len(pivots)-width):
                    spend()
                    end = start+width
                    if width in (3,5):
                        anchors = tuple(pivots[start:end+1])
                        for family in geometry([p.price for p in anchors]):
                            add(start,end,Node(family,anchors))
                    for count in (3,5):
                        if width < count*3:
                            continue
                        for children in routes(start,end,count):
                            spend()
                            if 1+max(c.depth for c in children)>3:
                                continue
                            depth=1+min(c.depth for c in children)
                            anchors=(children[0].anchors[0],)+tuple(c.anchors[-1] for c in children)
                            for family in geometry([p.price for p in anchors]):
                                if grammar(family,children):
                                    add(start,end,Node(family,anchors,children,depth))
                            if not all(c.family in CORRECTIVE for c in children):
                                continue
                            components=children[::2]
                            direction=components[0].side
                            if any(c.side!=direction for c in components) or any(c.side!=-direction for c in children[1::2]):
                                continue
                            if all(c.family=='zigzag' for c in components):
                                if any(direction*(b.anchors[-1].price-a.anchors[-1].price)<=0 for a,b in zip(components,components[1:])):
                                    continue
                                family='double_zigzag' if count==3 else 'triple_zigzag'
                            elif sum(c.family=='zigzag' for c in components)<=1 and not any(c.family.startswith('triangle') for c in components[:-1]):
                                family='double_three' if count==3 else 'triple_three'
                            else:
                                continue
                            add(start,end,Node(family,anchors,children,depth))
        except Exhausted:
            self.incomplete=True
        return nodes


def promote(nodes, coarse):
    """Use fine-scale child evidence with independently confirmed coarse anchors.

    A coarse anchor's later confirmation remains a dependency of the promoted
    node. Missing coarse endpoints cannot be inferred from the fine interpretation.
    """
    lookup={(p.index,p.kind):p for p in coarse}
    result=[]
    for node in nodes:
        anchors=[lookup.get((p.index,p.kind)) for p in node.anchors]
        if all(p is not None for p in anchors) and all(a.price==b.price for a,b in zip(anchors,node.anchors)):
            result.append(replace(node,anchors=tuple(anchors)))
    # Also retain unresolved coarse-only pictures; they must not masquerade as
    # fully subdivided patterns or disappear because fine parsing found no match.
    for width in (3,5):
        for start in range(len(coarse)-width):
            anchors=tuple(coarse[start:start+width+1])
            for family in geometry([p.price for p in anchors]):
                result.append(Node(family,anchors))
    return list({n.id:n for n in result}.values())
