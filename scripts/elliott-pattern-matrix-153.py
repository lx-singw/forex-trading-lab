"""Fixed invented candle-to-nested-pattern matrix; no strategy returns or orders."""
from bisect import bisect_right
from dataclasses import replace
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from forex_demo_lab import elliott_session_comparison_149 as comparison
from forex_demo_lab.elliott_full.contracts import Bar, D, digest, precise
from forex_demo_lab.elliott_full.patterns import CATALOGUE, Node, Pivot, Parser, confirmed, promote
from forex_demo_lab.elliott_full.rulebook import diagnose

ROOT = Path(__file__).resolve().parents[1]
HOUR = 3600000
START = 946684800000
PAD = 8
EXTENSIONS = ((0,), (2,), (4,), (0,2), (0,2,4))


def templates():
    spec = importlib.util.spec_from_file_location("rulebook153_templates", ROOT/"tests/test_elliott_full_rulebook.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def cases():
    result = [{"id": family+"_"+str(side), "family": family, "side": side, "extensions": []}
              for family in CATALOGUE for side in (1,-1)]
    result += [{"id": "extension_"+"".join(str(i+1) for i in positions)+"_"+str(side),
                "family": "impulse", "side": side, "extensions": list(positions)}
               for positions in EXTENSIONS for side in (1,-1)]
    return result


def sources():
    files = (Path(__file__), ROOT/"tests/test_elliott_full_rulebook.py")
    return {"runtime": comparison.source_bindings(), "generators": {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}


@precise
def resolve_impulse(leaf):
    children = []
    for leg, (a,b) in enumerate(zip(leaf.anchors, leaf.anchors[1:])):
        family = "impulse" if leg%2 == 0 else "zigzag"
        fractions = tuple(map(D, ("0",".25",".15",".75",".5","1") if family == "impulse" else ("0",".5",".25","1")))
        anchors = []
        for i,fraction in enumerate(fractions):
            index = a.index+(b.index-a.index)*i//(len(fractions)-1)
            price = a.price+(b.price-a.price)*fraction
            time = a.time+(b.time-a.time)*(index-a.index)//(b.index-a.index)
            anchors.append(a if i == 0 else b if i == len(fractions)-1 else
                           Pivot(digest(["declared153",index,str(price)]),index,time,time+a.available-a.time,
                                 price,"low" if (i%2 == 0) == (b.price>a.price) else "high",2))
        children.append(Node(family,tuple(anchors)))
    return replace(leaf, children=tuple(children), depth=2)


def declared(case):
    if case not in cases():
        raise ValueError("fixed_pattern_case_required")
    node,parent,position = templates().example(case["family"],case["side"] == -1)
    if case["extensions"]:
        def scale(n):
            return replace(n,anchors=tuple(replace(p,index=p.index*5,time=p.time*5,available=p.available*5) for p in n.anchors),
                           children=tuple(scale(c) for c in n.children))
        node = scale(node)
        node = replace(node,children=tuple(resolve_impulse(c) if i in case["extensions"] else c for i,c in enumerate(node.children)))
    def shift(n):
        return replace(n,anchors=tuple(replace(p,index=p.index+PAD,time=START+(p.index+PAD+1)*HOUR,
                           available=START+(p.index+PAD+3)*HOUR+2000) for p in n.anchors),
                       children=tuple(shift(c) for c in n.children))
    return shift(node),parent,position


def signature(node):
    def price(value):
        text = format(value,"f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    return [node.family,[[p.index,price(p.price)] for p in node.anchors], [signature(c) for c in node.children]]


@precise
def candle_fixture(case):
    node,parent,position = declared(case)
    points = {}
    def collect(n):
        for point in n.anchors:
            if point.index in points and points[point.index] != point.price:
                raise ValueError("conflicting_declared_anchor")
            points[point.index] = point.price
        for child in n.children:
            collect(child)
    collect(node)
    indices = sorted(points)
    bars = []
    for index in range(indices[-1]+PAD+1):
        if index < indices[0]:
            price = points[indices[0]]+node.side*D(".01")*(indices[0]-index)
        elif index > indices[-1]:
            price = points[indices[-1]]-node.side*D(".01")*(index-indices[-1])
        else:
            left = bisect_right(indices,index)-1
            a = indices[left]
            b = indices[min(left+1,len(indices)-1)]
            price = points[a] if a == b else points[a]+(points[b]-points[a])*(index-a)/(b-a)
        bars.append(Bar("H1",START+index*HOUR,START+(index+1)*HOUR,START+(index+1)*HOUR+2000,
                        price,price,price,price,digest(["invented_pattern153",case["id"],index,str(price)])))
    return node,parent,position,bars


def matching(nodes, target):
    wanted = signature(target)
    return [node for node in nodes if signature(node) == wanted]


def inspect(case):
    target,parent,position,bars = candle_fixture(case)
    journal,chain = confirmed(bars,2)
    parser = Parser()
    nodes = parser.parse(chain)
    exact = matching(nodes,target)
    last_index = target.anchors[-1].index
    before = bars[:last_index+2]  # one bar before radius-two confirmation
    before_nodes = Parser().parse(confirmed(before,2)[1])
    if matching(before_nodes,target):
        raise AssertionError("backdated_nested_pattern")
    at_confirmation = bars[:last_index+3]
    at_parser = Parser()
    at_nodes = at_parser.parse(confirmed(at_confirmation,2)[1])
    coarse = []
    for radius in (4,8):
        known = confirmed(bars,radius)[1]
        promoted = matching(promote(nodes,known),target)
        early = bars[:last_index+radius]
        early_promoted = matching(promote(nodes,confirmed(early,radius)[1]),target)
        coarse.append({"radius":radius,"exact_candidates":len(promoted),"before_confirmation":len(early_promoted),
                       "available":min((n.available for n in promoted),default=None),
                       "required_by":bars[last_index+radius].available})
    limited = Parser(budget=0)
    limited.parse(chain)
    full_span = [n for n in nodes if n.anchors[0].index == target.anchors[0].index
                 and n.anchors[-1].index == target.anchors[-1].index and n.children]
    return {"case":case,"bars":len(bars),"input_sha256":digest([b.record() for b in bars]),
            "declared_signature":signature(target),"declared_diagnostics":diagnose(target,parent,position),
            "confirmed_pivots":len(journal),"parser":{"budget":parser.budget,"cap":parser.cap,
                "expansions":parser.expansions,"incomplete":parser.incomplete,"rejection_count":parser.rejection_count},
            "status":"SEARCH_INCOMPLETE" if parser.incomplete else "RECOGNIZED" if exact else "NOT_RECOGNIZED",
            "exact_candidates":len(exact),"exact_records":[n.record() for n in exact],
            "diagnostics_at_declared_location":[diagnose(n,parent,position) for n in exact],
            "before_confirmation":0,"at_confirmation_exact":len(matching(at_nodes,target)),
            "at_confirmation_incomplete":at_parser.incomplete,"required_available":bars[last_index+2].available,
            "coarse_promotion":coarse,"full_span_alternatives":[{"id":n.id,"family":n.family,"height":n.height,
                "actionable_component":n.actionable} for n in full_span],
            "zero_budget_incomplete":limited.incomplete,"market_cells_run":0,"orders_available":False}


def run(output):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    bindings = sources()
    comparison.write(output/"declaration.json", {"kind":"invented_pattern153_pre_inspection_declaration",
                     "cases":cases(),"sources":bindings,"parser_budget":4096,"candidate_cap":128,
                     "scope":"H1_candle_confirmed_pivot_nested_parser_component_only",
                     "market_cells_run":0,"orders_available":False})
    records = []
    for case in cases():
        result = inspect(case)
        records.append(result)
        bars = [b.record() for b in candle_fixture(case)[3]]
        if digest(bars) != result["input_sha256"]:
            raise AssertionError("pattern153_input_changed")
        comparison.write(output/(case["id"]+".bars.json"), {"kind":"invented_pattern153_candles",
                         "case":case["id"],"bars":bars,"market_cells_run":0,"orders_available":False})
        comparison.write(output/(case["id"]+".json"),result)
    if sources() != bindings:
        raise ValueError("pattern153_sources_changed")
    report = {"kind":"invented_nested_pattern153_matrix","records":records,
              "market_cells_run":0,"market_returns":None,"orders_available":False,
              "limitations":["constructed OHLC with zero candle range; no executable quotes or market qualification",
                             "declared parent locations test diagnostics, not inferred higher-timeframe context",
                             "component eligibility is not a strategy signal; no ledger, full strategy or native run"]}
    comparison.write(output/"matrix.json",report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",help="new local matrix directory")
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"cases":len(report["records"]),"statuses":{s:sum(r["status"] == s for r in report["records"])
                      for s in ("RECOGNIZED","SEARCH_INCOMPLETE","NOT_RECOGNIZED")},"orders_available":False}))


if __name__ == "__main__":
    main()
