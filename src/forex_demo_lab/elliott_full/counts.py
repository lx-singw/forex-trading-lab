"""Total deterministic display order. Guideline scores are not probabilities."""
from .contracts import D, precise
from .patterns import CORRECTIVE, OBSERVATION_ONLY


def observation_only(node):
    return node.family in OBSERVATION_ONLY or any(observation_only(c) for c in node.children)


@precise
def rank(node, parent_side=None):
    p = [a.price for a in node.anchors]
    ratios = [None]*5
    if len(p) >= 4 and node.family not in CORRECTIVE:
        ratios[0] = abs((p[2]-p[1])/(p[1]-p[0]))
        ratios[2] = abs((p[3]-p[2])/(p[1]-p[0]))
    if len(p)==4 and node.family in ("zigzag","flat_regular","flat_expanded","flat_running"):
        ratios[4]=abs((p[3]-p[2])/(p[1]-p[0]))
    if len(p) == 6 and node.family not in CORRECTIVE:
        ratios[1] = abs((p[4]-p[3])/(p[3]-p[2]))
        ratios[3] = abs((p[5]-p[4])/(p[1]-p[0]))
    matches, error = 0, D(0)
    for index, ratio in enumerate(ratios):
        targets = (D(".382"),D(".5"),D(".618"),D(".786")) if index < 2 else (D(".618"),D(1),D("1.618"),D("2.618"))
        distance = D(1) if ratio is None else min(D(1),min(abs(ratio-v) for v in targets))
        matches += int(ratio is not None and distance <= D(".05"))
        error += distance
    resolved = D(sum(c.depth >= 1 for c in node.children))/len(node.children) if node.children else D(0)
    direction = -node.side if node.family in CORRECTIVE else node.side
    return (resolved, int(parent_side is not None and direction == parent_side), -int(observation_only(node)),
            matches, -error, -len(node.children), node.id)


def competitive(nodes, parent_side=None):
    if not nodes:
        return []
    terminal = max(n.anchors[-1].index for n in nodes)
    current = [n for n in nodes if n.anchors[-1].index == terminal]
    best = max(rank(n,parent_side)[:3] for n in current)
    return sorted((n for n in current if rank(n,parent_side)[:3] == best), key=lambda n:rank(n,parent_side),reverse=True)
