"""Coherent invented quotes; output bars are never supplied to the adapter."""
from datetime import datetime, timezone
from decimal import Decimal

from .daily_fixture_118 import fixture as daily_fixture
from .daily_features_118 import DAY

CASES = ("long_path", "short_path", "weekend_gap", "half_risk", "no_signal",
         "missing_coverage", "stale_coverage", "partial_session")


def fixture(case="long_path"):
    if type(case) is not str or case not in CASES:
        raise ValueError("bars_fixture_case")
    name = {"short_path": "trend_down_reentry_short", "no_signal": "trend_flat_reentry_none",
            "half_risk": "trend_up_reentry_none", "partial_session": "trend_up_reentry_none"}.get(case, "trend_up_reentry_long")
    seed = daily_fixture(name)
    calendar = seed["calendar"]
    calendar["calendar_id"] = "invented_utc_quotes121"
    warmup_closes = {b["session_id"]: b["close"] for b in seed["bars"]}
    warmup_last = seed["bars"][-1]["session_id"]
    evaluations = []
    while len(evaluations) < 3:
        prior = calendar["sessions"][-1]
        start = prior["end_msc"]
        weekday = datetime.fromtimestamp(start / 1000, timezone.utc).weekday()
        row = {"session_id": prior["session_id"] + 1, "start_msc": start, "end_msc": start + DAY,
               "status": "closure" if weekday >= 5 else "trading"}
        calendar["sessions"].append(row)
        if row["status"] == "trading":
            evaluations.append(row["session_id"])
    last = calendar["sessions"][-1]
    calendar["sessions"].append({"session_id": last["session_id"] + 1, "start_msc": last["end_msc"],
                                 "end_msc": last["end_msc"] + DAY, "status": "trading"})
    execution_start = calendar["sessions"][evaluations[0]]["start_msc"] + 3000
    messages = []
    warmup_index = 0
    offsets = (3000, DAY // 4, DAY // 2, DAY - 1000)
    for row in calendar["sessions"][:-1]:
        if row["status"] == "trading":
            close = warmup_closes.get(row["session_id"], 1.1)
            d = Decimal(str(close))
            mids = [d, d + Decimal(".0004"), d - Decimal(".0004"), d]
            if row["session_id"] == evaluations[0]:
                if case == "long_path":
                    mids = list(map(Decimal, ("1.1", "1.112", "1.098", "1.1")))
                elif case == "short_path":
                    mids = list(map(Decimal, ("1.1", "1.088", "1.102", "1.1")))
            if case == "weekend_gap" and row["session_id"] == evaluations[-1]:
                mids = list(map(Decimal, (".9", ".9004", ".8996", ".9")))
            for j, (offset, mid) in enumerate(zip(offsets, mids)):
                if case == "missing_coverage" and warmup_index == 10 and j == 1:
                    continue
                if case == "partial_session" and row["session_id"] == evaluations[-1] and j == 3:
                    break
                source = row["start_msc"] + offset
                age = 2001 if case == "stale_coverage" and warmup_index == 10 and j == 1 else 2
                messages.append({"sequence": len(messages), "kind": "quote", "source_msc": source,
                                 "receipt_msc": source + age, "bid": float(mid - Decimal(".00005")),
                                 "ask": float(mid + Decimal(".00005"))})
            if row["session_id"] <= warmup_last:
                warmup_index += 1
        if case == "partial_session" and row["session_id"] == evaluations[-1]:
            break
        messages.append({"sequence": len(messages), "kind": "advance", "receipt_msc": row["end_msc"] + 2000})
    return {"format": "FXDL_DAILYBARS121_V1", "kind": "invented_quote_bar_pipeline",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case, "calendar": calendar,
            "execution_start_msc": execution_start,
            "initial_account": {"kind": "invented_flat_cash", "trade_mode": 0, "currency": "USD",
                                "available_msc": execution_start - 1, "balance_usd": 10000.}, "messages": messages}
