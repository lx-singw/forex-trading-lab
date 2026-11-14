"""Versioned structural diagnostics. Guidelines cannot repair failed rules.

Definitions follow the sources in ELLIOTT-EXPANSION-144-PLAN.md. Numeric tolerances,
finite depth and strict location profiles are explicitly project conventions.
"""
from .contracts import D, precise
from .patterns import MOTIVE, CORRECTIVE, OBSERVATION_ONLY, geometry, grammar

SOURCE="https://www.elliottwave.com/waveopedia/"
RULES={
    "ordered_anchors":{"status":"structural_rule","description":"Positive alternating price turns with increasing source indices"},
    "family_geometry":{"status":"structural_rule","description":"The claimed family matches its own geometric constraints"},
    "child_grammar":{"status":"structural_rule","description":"Resolved children satisfy the family's motive/corrective grammar"},
    "child_endpoints":{"status":"project_convention","description":"Parent and child source endpoints and directional spans agree"},
    "parent_location":{"status":"structural_rule","description":"Diagonal and triangle positions respect the declared parent structure"},
    "boundary_lines":{"status":"project_convention","description":"Contracting/expanding boundary lines use observed bar indices"},
    "finite_depth":{"status":"project_convention","description":"At most three explicitly resolved pattern levels"},
    "resolution":{"status":"project_convention","description":"Geometry without child evidence is insufficient resolution"},
}
RULEBOOK={"version":"EW_FULL_RULEBOOK_V1","source_index":SOURCE,"rules":RULES,
          "ordinary_impulse_overlap":"boundary touch rejected","shortest_third":"proportional; equality allowed",
          "flat_B_band":["0.90","1.00"],"barrier_tolerance":"0.05 largest leg",
          "observation_only":sorted(OBSERVATION_ONLY),
          "guidelines":["Fibonacci proximity","alternation","channel conformity"]}
for family in sorted(MOTIVE|CORRECTIVE):
    path=("flats/" if family.startswith("flat") else "triangles/" if family.startswith("triangle") else
          "elliott-wave-pattern-diagonals/" if "diagonal" in family or family.startswith("leading") else
          "zigzags/" if family.endswith("zigzag") else "combinations/" if family.endswith("three") else
          "truncation/" if family=="truncated_impulse" else "impulse/")
    RULEBOOK.setdefault("families",{})[family]={"source":SOURCE+path,"mode":"motive" if family in MOTIVE else "corrective",
                                               "observation_only":family in OBSERVATION_ONLY}


def positions(node):
    if node.family in ("double_zigzag","double_three"):
        return ("W","X","Y")
    if node.family in ("triple_zigzag","triple_three"):
        return ("W","X","Y","X2","Z")
    if node.family.startswith("triangle"):
        return tuple("ABCDE")
    if node.family in CORRECTIVE:
        return tuple("ABC")
    return ("1","2","3","4","5")


def location(family,parent,position):
    if parent is None or position is None:
        return None if family.startswith(("leading","ending","expanding_diagonal","triangle")) else True
    if family.startswith("leading"):
        return (position=="1" and parent in ("impulse","truncated_impulse")) or (position=="A" and parent=="zigzag")
    if family in ("ending_diagonal","expanding_diagonal"):
        return (position=="5" and parent in ("impulse","truncated_impulse")) or (position=="C" and parent in ("zigzag","flat_regular","flat_expanded","flat_running"))
    if family.startswith("triangle"):
        return ((position=="4" and parent in ("impulse","truncated_impulse")) or
                (position=="B" and parent in ("zigzag","flat_regular","flat_expanded","flat_running")) or
                (position=="X" and parent in ("double_zigzag","double_three")) or
                (position=="X2" and parent in ("triple_zigzag","triple_three")) or
                (position=="Y" and parent=="double_three") or (position=="Z" and parent=="triple_three") or
                (position=="E" and parent.startswith("triangle")))
    return True


def same_endpoint(a,b):
    # Radius-specific confirmation events may differ; source endpoints may not.
    return (a.index,a.time,a.price)==(b.index,b.time,b.price)


@precise
def diagnose(node,parent=None,position=None):
    failed=[]
    if node.family not in MOTIVE|CORRECTIVE:
        return {"state":"unsupported","failed":["unknown_family"],"location":None}
    p=node.anchors
    if len(p)<4 or any(a.index>=b.index for a,b in zip(p,p[1:])) or any(not a.price.is_finite() or a.price<=0 or a.available<a.time for a in p):
        return {"state":"invalid","failed":["ordered_anchors"],"location":None}
    combination=node.family in ("double_zigzag","triple_zigzag","double_three","triple_three")
    if not combination and node.family not in geometry([a.price for a in p]):
        failed.append("family_geometry")
    place=location(node.family,parent,position)
    if place is False:
        failed.append("parent_location")
    if node.children:
        if len(p)!=len(node.children)+1:
            failed.append("child_endpoints")
        else:
            for i,c in enumerate(node.children):
                if not same_endpoint(p[i],c.anchors[0]) or not same_endpoint(p[i+1],c.anchors[-1]):
                    failed.append("child_endpoints")
            if not combination and not grammar(node.family,node.children):
                failed.append("child_grammar")
            if combination:
                expected=3 if node.family.startswith("double") else 5
                if len(node.children)!=expected or any(c.family not in CORRECTIVE for c in node.children):
                    failed.append("child_grammar")
                else:
                    components=node.children[::2]
                    if any(c.side!=node.side*(1 if i%2==0 else -1) for i,c in enumerate(node.children)):
                        failed.append("child_grammar")
                    if node.family.endswith("zigzag"):
                        if any(c.family!="zigzag" for c in components) or any(node.side*(b.anchors[-1].price-a.anchors[-1].price)<=0 for a,b in zip(components,components[1:])):
                            failed.append("child_grammar")
                    elif (sum(c.family=="zigzag" for c in components)>1 or
                          any(c.family.startswith("triangle") for c in components[:-1])):
                        failed.append("child_grammar")
            for child,pos in zip(node.children,positions(node)):
                check=diagnose(child,node.family,pos)
                if check["state"] in ("invalid","unsupported"):
                    failed.extend("child:"+r for r in check["failed"])
    elif node.depth!=1 or combination:
        failed.append("resolution")
    if len(p)==6 and node.family.startswith(("triangle","leading","ending","expanding_diagonal")):
        side=node.side
        y=[side*a.price for a in p]
        upper=(y[3]-y[1])/(p[3].index-p[1].index)
        lower=(y[4]-y[2])/(p[4].index-p[2].index)
        width_at_end=y[1]+upper*(p[5].index-p[1].index)-y[2]-lower*(p[5].index-p[2].index)
        expanding=node.family in ("triangle_expanding","expanding_diagonal")
        if width_at_end<=0 or (upper<=lower if expanding else upper>=lower):
            failed.append("boundary_lines")
    height=1+max((c.height for c in node.children),default=0)
    if height>3:
        return {"state":"unsupported","failed":sorted(set(failed+["finite_depth"])),"location":place}
    state="invalid" if failed else "unknown_location" if place is None else "valid_at_resolution" if node.children else "insufficient_resolution"
    return {"state":state,"failed":sorted(set(failed)),"location":place,
            "rulebook":RULEBOOK["version"],"observation_only":node.family in OBSERVATION_ONLY}
