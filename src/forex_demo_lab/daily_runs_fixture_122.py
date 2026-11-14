"""Fixed invented chronological windows and coherent quotes, never market data."""
from datetime import datetime, timezone
from decimal import Decimal

from .daily_bars_fixture_121 import fixture as quote_fixture
from .daily_features_118 import DAY

CASES = ("targets", "weekend_gap", "no_signal", "missing_history", "missing_endpoint", "stale_endpoint")


def fixture(case="targets"):
    if type(case) is not str or case not in CASES:
        raise ValueError("run_fixture_case")
    seed_case = {"targets": "long_path", "weekend_gap": "weekend_gap", "no_signal": "no_signal",
                 "missing_history": "missing_coverage"}.get(case, "half_risk")
    stream = quote_fixture(seed_case)
    start = stream["execution_start_msc"] - 3000
    messages = [m for m in stream["messages"] if m["receipt_msc"] < start + 3000]
    sessions = [s for s in stream["calendar"]["sessions"] if s["start_msc"] < start]
    evaluations = []
    while len(evaluations) < 9:
        prior = sessions[-1]
        source = prior["end_msc"]
        weekday = datetime.fromtimestamp(source / 1000, timezone.utc).weekday()
        row = {"session_id": prior["session_id"] + 1, "start_msc": source, "end_msc": source + DAY,
               "status": "closure" if weekday >= 5 else "trading"}
        sessions.append(row)
        if row["status"] == "trading":
            evaluations.append(row)
    last = sessions[-1]
    sessions.append({"session_id": last["session_id"] + 1, "start_msc": last["end_msc"],
                     "end_msc": last["end_msc"] + DAY, "status": "trading"})
    indexes = {row["session_id"]: i for i, row in enumerate(evaluations)}
    offsets = (3000, DAY // 4, DAY // 2, DAY - 1000)
    for row in sessions:
        if row["start_msc"] < start or row is sessions[-1]:
            continue
        if row["status"] == "trading":
            i = indexes[row["session_id"]]
            level = Decimal(".9") if case == "weekend_gap" and i >= 2 else Decimal("1.1")
            mids = [level, level + Decimal(".0004"), level - Decimal(".0004"), level]
            if case == "targets" and i == 0:
                mids = list(map(Decimal, ("1.1", "1.112", "1.098", "1.1")))
            for j, (offset, mid) in enumerate(zip(offsets, mids)):
                source, age = row["start_msc"] + offset, 2
                if case == "stale_endpoint" and i == 6 and j == 3:
                    source, age = row["end_msc"] - 3000, 2001
                messages.append({"sequence": 0, "kind": "quote", "source_msc": source, "receipt_msc": source + age,
                                 "bid": float(mid - Decimal(".00005")), "ask": float(mid + Decimal(".00005"))})
        messages.append({"sequence": 0, "kind": "advance", "receipt_msc": row["end_msc"] + 2000})
    for i, message in enumerate(messages):
        message["sequence"] = i
    stream.update(case=case, execution_start_msc=None, messages=messages)
    stream["calendar"]["sessions"] = sessions
    development_end = evaluations[6]["end_msc"]
    endpoint = development_end - (3000 if case == "stale_endpoint" else 500 if case == "missing_endpoint" else 1000)
    return {"format": "FXDL_DAILYRUNS122_V1", "kind": "invented_partitioned_daily_run",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case, "stream": stream,
            "partitions": [{"name": "development", "start_msc": start, "end_msc": development_end,
                            "endpoint_source_msc": endpoint},
                           {"name": "later_validation", "start_msc": evaluations[7]["start_msc"],
                            "end_msc": evaluations[8]["end_msc"], "endpoint_source_msc": evaluations[8]["end_msc"] - 1000}]}
