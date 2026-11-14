"""Deterministic invented daily OHLC bundles; not observations of a market."""
from datetime import datetime, timezone

from .daily_features_118 import DAY, VERSION, bar_lineage

START = 978_307_200_000  # 2001-01-01, explicitly invented UTC.
PAIRS = {"up": 1, "flat": 0, "down": -1}
REENTRIES = {"long": 1, "none": 0, "short": -1}
CASES = tuple(f"trend_{t}_reentry_{r}" for t in PAIRS for r in REENTRIES) + ("zero_range", "warmup")


def fixture(case="trend_up_reentry_long"):
    if type(case) is not str or case not in CASES:
        raise ValueError("fixture_case")
    if case in ("zero_range", "warmup"):
        trend, reentry = "flat", "none"
    else:
        _, trend, _, reentry = case.split("_")
    count = 252 if case == "warmup" else 253
    first = {"up": 1.0, "flat": 1.1, "down": 1.2}[trend]
    closes = [first] * (count - 21) + [1.1] * 19
    closes += [{"long": 1.09, "none": 1.1, "short": 1.11}[reentry], 1.1]
    rows, bars = [], []
    day, bar_index = 0, 0
    cal_id = "invented_utc_day_schedule"
    while bar_index < count:
        start = START + day * DAY
        weekday = datetime.fromtimestamp(start / 1000, timezone.utc).weekday()
        session = {"session_id": day, "start_msc": start, "end_msc": start + DAY,
                   "status": "closure" if weekday >= 5 else "trading"}
        rows.append(session)
        if session["status"] == "trading":
            close = closes[bar_index]
            width = 0.0 if case == "zero_range" else .0004
            bar = {"session_id": day, "start_msc": start, "end_msc": start + DAY,
                   "observation_msc": start + DAY - 1000, "available_msc": start + DAY + 1000,
                   "open": close, "high": close + width, "low": close - width, "close": close}
            bar["lineage_sha256"] = bar_lineage(case, cal_id, session, bar)
            bars.append(bar)
            bar_index += 1
        day += 1
    return {"format": VERSION, "kind": "invented_daily_fixture", "clock": "invented_utc_milliseconds",
            "symbol": "EURUSD", "case": case,
            "calendar": {"kind": "invented_calendar", "calendar_id": cal_id,
                         "available_msc": START - 1, "sessions": rows},
            "bars": bars, "target_session_id": bars[-1]["session_id"],
            "decision_msc": bars[-1]["available_msc"]}
