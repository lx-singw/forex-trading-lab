"""Fixed invented sizing/guard cases; account marks are inputs, never trade results."""
from copy import deepcopy
from datetime import datetime, timezone

from .daily_fixture_118 import fixture as daily_fixture
from .daily_features_118 import DAY, bar_lineage

CASES = ("full_long", "half_long", "full_short", "half_short", "opposing", "warmup", "zero_range",
         "wide_then_valid", "stale_then_valid", "before_then_valid", "minimum_risk", "minimum_margin",
         "max_lot", "pause_recovery", "open_loss", "daily_headroom", "held_signal_change",
         "reservation_next_session", "gap_pause", "stale_feature", "closed_then_valid", "repeated_source")


def fixture(case="full_long"):
    if type(case) is not str or case not in CASES:
        raise ValueError("risk_fixture_case")
    name = {"half_long": "trend_up_reentry_none", "full_short": "trend_down_reentry_short",
            "half_short": "trend_down_reentry_none", "opposing": "trend_up_reentry_short",
            "warmup": "warmup", "zero_range": "zero_range", "max_lot": "trend_up_reentry_none"}.get(case, "trend_up_reentry_long")
    features = daily_fixture(name)
    original_target, decision = features["target_session_id"], features["decision_msc"]
    calendar = features["calendar"]
    for _ in range(20):
        previous = calendar["sessions"][-1]
        start = previous["end_msc"]
        day = datetime.fromtimestamp(start / 1000, timezone.utc).weekday()
        row = {"session_id": previous["session_id"] + 1, "start_msc": start, "end_msc": start + DAY,
               "status": "closure" if day >= 5 else "trading"}
        calendar["sessions"].append(row)
        if row["status"] == "trading":
            bar = {"session_id": row["session_id"], "start_msc": start, "end_msc": start + DAY,
                   "observation_msc": start + DAY - 1000, "available_msc": start + DAY + 1000,
                   "open": 1.1, "high": 1.1004, "low": 1.0996, "close": 1.1}
            bar["lineage_sha256"] = bar_lineage(features["case"], calendar["calendar_id"], row, bar)
            features["bars"].append(bar)
    first_row = next(r for r in calendar["sessions"] if r["status"] == "trading" and r["start_msc"] >= decision - 1000)
    start = max(decision + 1000, first_row["start_msc"] + 2000)

    def event(source, target=original_target, feature_time=decision, equity=10000., margin=10000., spread=.0001, age=2):
        return {"sequence": 0, "source_msc": source, "receipt_msc": source + age, "bid": 1.1, "ask": 1.1 + spread,
                "target_session_id": target, "feature_decision_msc": feature_time,
                "equity_usd": equity, "free_margin_usd": margin}

    events = [event(start), event(start + 1000)]
    held = None
    initial_equity, initial_margin = 10000., 10000.
    if case == "wide_then_valid":
        events = [event(start, spread=.0002), event(start + 1000), event(start + 2000)]
    elif case == "stale_then_valid":
        events = [event(start, age=2001), event(start + 3000), event(start + 4000)]
    elif case == "before_then_valid":
        events = [event(decision), event(start), event(start + 1000)]
    elif case == "minimum_risk":
        initial_equity = initial_margin = 10.
        events = [event(start, equity=10., margin=10.), event(start + 1000, equity=10., margin=10.)]
    elif case == "minimum_margin":
        initial_margin = 1.
        events = [event(start, margin=1.), event(start + 1000)]
    elif case == "max_lot":
        initial_equity = initial_margin = 1e6
        events = [event(start, equity=1e6, margin=1e6), event(start + 1000, equity=1e6, margin=1e6)]
    elif case == "pause_recovery":
        events = [event(start, equity=9900., margin=9900.), event(start + 1000)]
    elif case == "daily_headroom":
        events = [event(start, equity=9900.01, margin=9000.), event(start + 1000)]
    elif case in ("held_signal_change", "reservation_next_session"):
        bar = next(b for b in features["bars"] if b["session_id"] > original_target)
        following = next(r for r in calendar["sessions"] if r["status"] == "trading" and r["start_msc"] >= bar["end_msc"])
        new_source = following["start_msc"] + 2000
        events = [event(start), event(new_source, bar["session_id"], bar["available_msc"])]
    elif case == "stale_feature":
        bar = next(b for b in features["bars"] if b["session_id"] > original_target)
        following = next(r for r in calendar["sessions"] if r["status"] == "trading" and r["start_msc"] >= bar["end_msc"])
        new_source = following["start_msc"] + 2000
        events = [event(start, spread=.0002), event(new_source),
                  event(new_source + 1000, bar["session_id"], bar["available_msc"])]
    elif case in ("gap_pause", "closed_then_valid"):
        monday = next(r for r in calendar["sessions"] if r["start_msc"] > start + DAY and
                      datetime.fromtimestamp(r["start_msc"] / 1000, timezone.utc).weekday() == 0)
        new_source = monday["start_msc"] + 2000
        bar = max((b for b in features["bars"] if b["available_msc"] < new_source), key=lambda b: b["session_id"])
        if case == "gap_pause":
            events = [event(start, spread=.0002), event(new_source, bar["session_id"], bar["available_msc"], 9700., 9700.)]
        else:
            closure = next(r for r in calendar["sessions"] if r["start_msc"] > start and r["status"] == "closure")
            events = [event(closure["start_msc"] + 2000), event(new_source, bar["session_id"], bar["available_msc"])]
    elif case == "repeated_source":
        events = [event(start), event(start, age=20), event(start + 1000)]
    if case in ("open_loss", "held_signal_change"):
        held = {"kind": "invented_held_position", "name": "invented_position_a", "side": 1, "lots": .1,
                "entry": 1.2, "stop": 1., "target": 1.6, "opened_msc": events[0]["source_msc"] - DAY}
        initial_margin = 9000.
        if case == "open_loss":
            events = [event(start, equity=9890., margin=9000.), event(start + 1000, margin=9000.)]
        for row in events:
            row["free_margin_usd"] = min(row["free_margin_usd"], 9000.)
    for i, row in enumerate(events):
        row["sequence"] = i
    return {"format": "FXDL_DAILYRISK119_V1", "kind": "invented_daily_risk_fixture",
            "clock": "invented_utc_milliseconds", "symbol": "EURUSD", "case": case, "features": features,
            "initial_account": {"kind": "invented_account_state", "trade_mode": 0, "currency": "USD",
                                "available_msc": events[0]["source_msc"] - 1,
                                "equity_usd": initial_equity, "free_margin_usd": initial_margin, "held": held},
            "events": events}
