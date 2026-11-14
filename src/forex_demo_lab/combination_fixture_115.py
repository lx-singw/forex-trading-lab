"""Fixed vote-case fixtures, with unchanged 114 control prices. Invented only."""
from .strategy_fixture_114 import fixture as control_fixture

CASES = ("continuation", "reversal", "flat", "partial_agreement", "conflicting_votes")


def fixture(case="continuation"):
    if case not in CASES:
        raise ValueError("fixture_case")
    if case in CASES[:3]:
        return control_fixture(case)
    result = control_fixture("continuation")
    result["case"] = case
    for event in result["events"]:
        hour, quote = divmod(event["sequence"], 4)
        block, offset = divmod(hour, 288)
        side, base = (1 if block == 0 else -1), 1.1 + block * 0.002
        if case == "partial_agreement":
            price = (1.25 if offset <= 150 else 1.125 if offset <= 199
                     else 1.1875 if offset == 200 else 1.2 if offset <= 223
                     else 1.23 if offset <= 226 else 1.16)
        else:
            price = (1.1 if offset <= 149 else 1.0 if offset == 150
                     else 1.103 if offset <= 179 else 1.1 if offset <= 199
                     else 1.1001 if offset == 200 else 1.104 if offset <= 223
                     else 1.108 if offset <= 226 else 1.096)
        bid = round(base + side * (price - 1.1) + (0.0, .00001, -.00001, 0.0)[quote], 8)
        event.update(bid=bid, ask=round(bid + .0001, 8))
    return result
