"""Two predetermined invented paths, for software checks rather than forecasts."""
from datetime import datetime, timezone

START = int(datetime(2001, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def fixture(case="continuation"):
    if case not in ("continuation", "reversal"):
        raise ValueError("fixture_case")
    events = []
    for hour in range(192):
        block, offset = divmod(hour, 96)
        side = 1 if block == 0 else -1
        base = 1.1 + block * 0.002
        move = -offset * 0.00001 if offset <= 50 else (0.003 if offset <= 53 else (0.006 if case == "continuation" else 0.0))
        price = base + side * move
        for delta, wiggle in ((0, 0.0), (1800000, 0.00001), (3599000, -0.00001), (3599500, 0.0)):
            receipt = START + hour * 3600000 + delta
            bid = round(price + wiggle, 8)
            events.append({"sequence": len(events), "receipt_msc": receipt, "source_msc": receipt - 50,
                           "bid": bid, "ask": round(bid + 0.0001, 8)})
    return {"format": "FXDL_SHADOW113_V1", "kind": "invented_fixture",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case,
            "development_start_msc": START + 51 * 3600000,
            "validation_start_msc": START + 96 * 3600000, "events": events}
