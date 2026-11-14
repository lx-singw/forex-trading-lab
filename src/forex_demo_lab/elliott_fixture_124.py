"""Fixed invented daily paths for a causal wave-inspired detector, never prices from a feed."""
from datetime import datetime, timezone
from decimal import Decimal

from . import daily_features_118 as daily
from .elliott_waves_124 import VERSION

CASES = ("long_breakout", "short_breakout", "no_pivots", "small_impulse", "deep_pullback",
         "invalidation", "ambiguous_breakout", "expiry_boundary", "expired", "warmup",
         "opposite_trend", "flat_trend", "late_confirmation", "delayed_availability",
         "same_kind_plateau", "retracement_minimum", "retracement_maximum")
START = 978307200000
TAIL = ("1.02", "1", "1.03", "1.08", "1.12", "1.10", "1.08", "1.06", "1.075", "1.09", "1.13")


def bundle(closes, case="custom", overrides=None):
    rows, bars, day = [], [], 0
    cal_id = "invented_wave_days"
    for i, price in enumerate(closes):
        while True:
            start = START + day * daily.DAY
            trading = datetime.fromtimestamp(start / 1000, timezone.utc).weekday() < 5
            session = {"session_id": day, "start_msc": start, "end_msc": start + daily.DAY,
                       "status": "trading" if trading else "closure"}
            rows.append(session)
            day += 1
            if trading:
                break
        close = Decimal(str(price))
        width = Decimal(".0001")
        bar = {"session_id": session["session_id"], "start_msc": start, "end_msc": start + daily.DAY,
               "observation_msc": start + daily.DAY - 1000, "available_msc": start + daily.DAY + 1000,
               "open": float(close), "high": float(close + width), "low": float(close - width), "close": float(close)}
        bar.update((overrides or {}).get(i, {}))
        bar["lineage_sha256"] = daily.bar_lineage(case, cal_id, session, bar)
        bars.append(bar)
    value = {"format": daily.VERSION, "kind": "invented_daily_fixture", "clock": "invented_utc_milliseconds",
             "symbol": "EURUSD", "case": case,
             "calendar": {"kind": "invented_calendar", "calendar_id": cal_id, "available_msc": START - 1, "sessions": rows},
             "bars": bars, "target_session_id": bars[-1]["session_id"], "decision_msc": max(b["available_msc"] for b in bars)}
    return {"format": VERSION, "kind": "invented_wave_detector", "clock": "invented_utc_milliseconds",
            "symbol": "EURUSD", "case": case, "daily": value}


def fixture(case="long_breakout"):
    if type(case) is not str or case not in CASES:
        raise ValueError("wave_fixture_case")
    base = ["1"] + ["1.04"] * 252
    tail, overrides = list(TAIL), {}
    if case == "no_pivots":
        return bundle(["1.04"] * 264, case)
    if case == "small_impulse":
        tail = ["1.002", "1", "1.003", "1.007", "1.009", "1.007", "1.006", "1.0045", "1.006", "1.008", "1.011"]
    if case == "deep_pullback":
        tail[7] = "1.02"
    if case == "invalidation":
        tail[9] = "1.04"
    if case == "ambiguous_breakout":
        overrides[263] = {"low": 1.05}
    if case in ("expiry_boundary", "expired"):
        tail = tail[:9] + ["1.09"] * (9 if case == "expiry_boundary" else 11) + ["1.13"]
    if case == "warmup":
        base = ["1"] + ["1.04"] * 9
    if case == "opposite_trend":
        base = ["1.3"] * 253
    if case == "flat_trend":
        base = ["1.13"] * 253
    if case == "late_confirmation":
        tail[8:] = ["1.13", "1.14", "1.15"]
    if case == "same_kind_plateau":
        tail = ["1.02", "1", "1.10", "1.05", "1.05", "1.12", "1.08", "1.08", "1.115", "1.09", "1.06", "1.075", "1.13"]
    if case in ("retracement_minimum", "retracement_maximum"):
        tail[7] = "1.07416" if case == "retracement_minimum" else "1.04584"
    closes = base + tail
    if case == "short_breakout":
        closes = [Decimal("2.2") - Decimal(c) for c in closes]
    value = bundle(closes, case, overrides)
    if case == "delayed_availability":
        bar = value["daily"]["bars"][261]
        bar["available_msc"] = bar["end_msc"] + 6 * 3600000
        session = value["daily"]["calendar"]["sessions"][bar["session_id"]]
        bar["lineage_sha256"] = daily.bar_lineage(case, value["daily"]["calendar"]["calendar_id"], session, bar)
    return value
