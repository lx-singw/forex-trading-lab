"""Coherent invented quote paths for structural-stop accounting, never feed data."""
from datetime import datetime, timezone
from decimal import Decimal

from . import daily_features_118 as daily
from .elliott_execution_125 import VERSION

CASES = ("long_target", "short_target", "long_stop", "short_stop", "long_gap", "short_gap",
         "boundary_hold", "wide_exit", "quote_guards", "delayed_publication", "minimum_lot", "max_lot",
         "financing_pause", "held_signal_change", "invalid_geometry", "no_signal", "missing_history",
         "missing_endpoint", "stale_endpoint", "nonpositive_exit")
START = 978307200000
TAIL = ("1.002", "1", "1.005", "1.014", "1.02", "1.017", "1.014", "1.01", "1.015", "1.016", "1.022")


def fixture(case="long_target"):
    if type(case) is not str or case not in CASES:
        raise ValueError("elliott_execution_case")
    scale = Decimal("10") if case == "minimum_lot" else Decimal(".01") if case in ("max_lot", "financing_pause") else Decimal(1)
    short = case.startswith("short_")
    first_post = ["1.022"] * 5
    if case in ("long_gap", "short_gap"):
        first_post[1:] = [".9"] * 4
    if case == "held_signal_change":
        first_post = ["1.018", "1.016", "1.019", "1.023", "1.06"]
    closes = ["1"] + ["1.004"] * 252 + list(TAIL) + first_post + ["1.004"] * 15 + list(TAIL) + ["1.022"] * 5
    if case == "no_signal":
        closes = ["1.004"] * len(closes)
    sessions, dates, messages = [], {}, []
    day, i, added_closure, remaining = 0, 0, False, 0
    offsets = (3000, daily.DAY // 4, daily.DAY // 2, daily.DAY - 1000)
    def quote(source, mid, spread=None, age=2):
        effective = Decimal(".000001") if case in ("max_lot", "financing_pause") else Decimal(".0001")
        if spread is not None:
            effective = Decimal(str(spread))
        return {"sequence": 0, "kind": "quote", "source_msc": source, "receipt_msc": source + age,
                "bid": float(mid - effective / 2), "ask": float(mid + effective / 2)}
    while i < len(closes):
        if case == "financing_pause" and i == 265 and not added_closure:
            remaining, added_closure = 39, True
        start = START + day * daily.DAY
        weekday = datetime.fromtimestamp(start / 1000, timezone.utc).weekday()
        forced = remaining > 0
        if forced:
            remaining -= 1
        trading = not forced and weekday < 5
        row = {"session_id": day, "start_msc": start, "end_msc": start + daily.DAY, "status": "trading" if trading else "closure"}
        sessions.append(row)
        day += 1
        if trading:
            dates[i] = row
            close = Decimal(closes[i])
            mids = [close, close + Decimal(".0001"), close - Decimal(".0001"), close]
            if i == 264:
                mids[0] = Decimal("1.022")
                if case in ("long_target", "short_target", "max_lot", "quote_guards"):
                    mids[1] = Decimal("1.06")
                if case in ("long_stop", "short_stop", "wide_exit"):
                    mids[1] = Decimal("1.009")
                if case == "invalid_geometry":
                    mids[0] = Decimal(".99")
                if case == "delayed_publication":
                    mids[2] = Decimal("1.06")
                if case == "nonpositive_exit":
                    mids[1] = Decimal(".000005")
            if i == 265 and case == "financing_pause":
                mids[1] = Decimal("1.06")
            for j, (offset, mid) in enumerate(zip(offsets, mids)):
                if case == "missing_history" and i == 10 and j == 1:
                    continue
                if short:
                    mid = Decimal("2.2") - mid
                mid *= scale
                source, age = start + offset, 2
                if case == "stale_endpoint" and i == 268 and j == 3:
                    source, age = row["end_msc"] - 3000, 2001
                spread = ".001" if case == "wide_exit" and i == 264 and j == 1 else ".000001" if case == "nonpositive_exit" and i == 264 and j == 1 else None
                if case == "quote_guards" and i == 264 and j == 0:
                    messages.append(quote(source, mid, age=2001))
                    wide = quote(start + 6000, mid, ".0003")
                    messages.append(wide)
                    messages.append({**wide, "receipt_msc": start + 6200})
                    messages.append(quote(start + 7000, mid))
                else:
                    messages.append(quote(source, mid, spread, age))
            i += 1
        if not (case == "delayed_publication" and trading and i == 264):
            messages.append({"sequence": 0, "kind": "advance", "receipt_msc": row["end_msc"] + 2000})
    last = sessions[-1]
    sessions.append({"session_id": day, "start_msc": last["end_msc"], "end_msc": last["end_msc"] + daily.DAY,
                     "status": "trading" if datetime.fromtimestamp(last["end_msc"] / 1000, timezone.utc).weekday() < 5 else "closure"})
    for n, message in enumerate(messages):
        message["sequence"] = n
    development_end = dates[268]["end_msc"]
    endpoint = development_end - (500 if case == "missing_endpoint" else 3000 if case == "stale_endpoint" else 1000)
    stream = {"format": "FXDL_DAILYBARS121_V1", "kind": "invented_quote_bar_pipeline", "clock": "invented_utc_milliseconds",
              "symbol": "EURUSD", "case": case,
              "calendar": {"kind": "invented_calendar", "calendar_id": "invented_elliott_quotes125", "available_msc": START - 1, "sessions": sessions},
              "execution_start_msc": None,
              "initial_account": {"kind": "invented_flat_cash", "trade_mode": 0, "currency": "USD", "available_msc": START - 1, "balance_usd": 10000},
              "messages": messages}
    return {"format": VERSION, "kind": "invented_elliott_execution", "clock": "invented_utc_milliseconds", "symbol": "EURUSD",
            "case": case, "stream": stream,
            "partitions": [{"name": "development", "start_msc": dates[264]["start_msc"] + 2000, "end_msc": development_end, "endpoint_source_msc": endpoint},
                           {"name": "later_validation", "start_msc": dates[295]["start_msc"] + 2000, "end_msc": dates[299]["end_msc"], "endpoint_source_msc": dates[299]["end_msc"] - 1000}]}
