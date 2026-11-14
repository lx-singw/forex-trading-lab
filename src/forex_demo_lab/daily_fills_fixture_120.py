"""Predeclared invented fill/accounting paths, never market forecasts."""
from datetime import datetime, timezone

from .daily_risk_fixture_119 import fixture as risk_fixture
from .daily_features_118 import DAY

CASES = ("long_target", "short_target", "long_stop", "short_stop", "long_gap", "short_gap",
         "half_risk", "opposing", "warmup", "zero_range", "weekend_financing",
         "release_next_session", "quality_guards", "minimum_capital")


def fixture(case="long_target"):
    if type(case) is not str or case not in CASES:
        raise ValueError("fill_fixture_case")
    risk_case = "full_short" if case.startswith("short_") else {
        "half_risk": "half_long", "opposing": "opposing", "warmup": "warmup",
        "zero_range": "zero_range", "minimum_capital": "minimum_risk"}.get(case, "full_long")
    seed = risk_fixture(risk_case)
    features = seed["features"]
    start = seed["events"][0]["source_msc"]

    def quote(time, bid=1.1, ask=None, age=2):
        bar = max((b for b in features["bars"] if b["available_msc"] <= time), key=lambda b: b["session_id"])
        return {"sequence": 0, "source_msc": time, "receipt_msc": time + age,
                "bid": bid, "ask": bid + .0001 if ask is None else ask,
                "target_session_id": bar["session_id"], "feature_decision_msc": bar["available_msc"]}

    exit_bid = {"long_target": 1.12, "short_target": 1.08, "long_stop": 1.09, "short_stop": 1.11,
                "long_gap": .9, "short_gap": 1.3}.get(case, 1.1)
    events = [quote(start), quote(start + 1000, exit_bid)]
    if case == "weekend_financing":
        wednesday = next(r for r in features["calendar"]["sessions"] if r["start_msc"] >= start and
                         datetime.fromtimestamp(r["start_msc"] / 1000, timezone.utc).weekday() == 2)
        begin = wednesday["start_msc"] + 2000
        events = [quote(begin), quote(begin + 5 * DAY)]
    elif case == "release_next_session":
        events = [quote(start), quote(start + 1000, 1.12), quote(start + 2000)]
        following = next(r for r in features["calendar"]["sessions"] if r["start_msc"] > start and r["status"] == "trading")
        events += [quote(following["start_msc"] + 2000), quote(following["start_msc"] + 3000, 1.12)]
    elif case == "quality_guards":
        events = [quote(start, ask=1.1002), quote(start + 1000, age=2001), quote(start + 4000),
                  quote(start + 4000, age=20), quote(start + 5000, 1.09, 1.0905), quote(start + 6000)]
    for i, event in enumerate(events):
        event["sequence"] = i
    return {"format": "FXDL_DAILYFILLS120_V1", "kind": "invented_daily_fills_fixture",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case, "features": features,
            "initial_account": {"kind": "invented_flat_cash", "trade_mode": 0, "currency": "USD",
                                "available_msc": events[0]["source_msc"] - 1,
                                "balance_usd": 10. if case == "minimum_capital" else 10000.}, "events": events}
