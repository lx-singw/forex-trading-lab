"""Predetermined invented paths; no measured market prices or forecasts."""
from .shadow_fixture_113 import START

CASES = ("continuation", "reversal", "flat")


def fixture(case="continuation"):
    if case not in CASES:
        raise ValueError("fixture_case")
    events = []
    for hour in range(576):
        block, offset = divmod(hour, 288)
        side, base = (1 if block == 0 else -1), 1.1 + block * 0.002
        if case == "flat":
            price = 1.1
        else:
            if offset <= 200:
                move = -offset * 0.00001
            elif offset <= 203:
                move = 0.003
            elif offset <= 223:
                move = 0.006 if case == "continuation" else 0.0
            elif offset <= 226:
                move = 0.009
            else:
                move = 0.015 if case == "continuation" else -0.004
            price = base + side * move
        for delta, wiggle in ((0, 0.0), (1800000, 0.00001),
                              (3599000, -0.00001), (3599500, 0.0)):
            receipt = START + hour * 3600000 + delta
            bid = round(price + (wiggle if case != "flat" else 0.0), 8)
            events.append({"sequence": len(events), "receipt_msc": receipt,
                           "source_msc": receipt - 50, "bid": bid,
                           "ask": round(bid + 0.0001, 8)})
    return {"format": "FXDL_STRATEGY114_V1", "kind": "invented_fixture",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case,
            "development_start_msc": START + 201 * 3600000,
            "validation_start_msc": START + 288 * 3600000, "events": events}
