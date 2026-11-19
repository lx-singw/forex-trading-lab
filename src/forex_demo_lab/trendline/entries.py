"""Resolve invented break and bounce setups at the first scheduled H1 opening."""
import hashlib

from . import breaks, data, fills, selection

VERSION = "TRL_BRK3_B_ENTRIES_174_V1"
H4_DECISION_ORDINAL = 0
H1_OPEN_ORDINAL = 1


@data.cached_bindings
def bindings():
    result = breaks.bindings() | fills.bindings()
    path = "src/forex_demo_lab/trendline/entries.py"
    result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def _visible_hours(source, hours, as_of, calendar):
    if not isinstance(hours, (list, tuple)) or len(hours) > data.ROW_LIMIT:
        raise ValueError("bounded invented hourly prefix required")
    scheduled = {window.start: window.end for window in calendar.frame("H1")}
    basis = source.record()["geometry_basis"]
    result = {}
    clock = calendar.start
    for hour in hours:
        if not isinstance(hour, data.Hour):
            raise ValueError("typed completed hour required")
        hour = data.Hour.from_record(hour.record(), basis)
        if (scheduled.get(hour.start) != hour.end or hour.start in result
                or not clock <= hour.available_at <= as_of):
            raise ValueError("unique declared hours in receipt order through as-of required")
        result[hour.start] = hour
        clock = hour.available_at
    return result


def _resolve(model, request, window, expires_at, hours, as_of, bid_only, target_levels):
    if not bid_only:
        price = model.entry(request, None)
        return price["status"], price["reason"], price
    if window is None or expires_at is None or window.start >= expires_at:
        return "SKIPPED", "NO_SCHEDULED_ENTRY", None
    decision_time = request["decision_at"]["time"]
    if decision_time >= expires_at:
        return "EXPIRED", "ENTRY_WINDOW_EXPIRED", None
    if decision_time > window.start:
        return "SKIPPED", "LATE_DECISION", None

    hour = hours.get(window.start)
    if hour is not None and hour.available_at <= expires_at:
        opening = fills.Opening.from_hour(hour, H1_OPEN_ORDINAL)
        price = model.entry(request, opening, target_levels=target_levels)
        return price["status"], price["reason"], price
    if as_of >= expires_at:
        return "EXPIRED", "MISSING_ENTRY_BAR", None
    return "PENDING", "AWAITING_ENTRY_BAR", None


def evaluate(replay, hours, *, as_of, cost_profile="base"):
    """Evaluate a setup replay and completed-hour receipt prefix from its source."""
    if not isinstance(replay, breaks.BreakReplay):
        raise ValueError("setup replay required")
    data.integer(as_of)
    source = replay.source
    calendar = source.calendar
    if (not calendar.start <= as_of <= calendar.end + 60000
            or any(bar.available > as_of for bar in replay.publications)):
        raise ValueError("as-of must cover the setup replay within its declared scope")
    bound = bindings()
    hourly = _visible_hours(source, hours, as_of, calendar)
    report = replay.report()
    profile = report["action_replay"]["profile"]
    model = fills.PriceModel(source, cost_profile)
    bid_only = source.record()["geometry_basis"] == "bid_only"
    attempts = []
    for attempt, target_levels in _requests(report, calendar, cost_profile):
        request = attempt["request"]
        window = model.entry_window(request["trigger_end"])
        status, reason, price = _resolve(model, request, window, attempt["expires_at"],
                                         hourly, as_of, bid_only, target_levels)
        attempt.update(first_scheduled_open=None if window is None else window.start,
                       status=status, reason=reason, price_result=price)
        attempts.append(attempt)

    if bound != bindings():
        raise ValueError("entry replay source bindings changed")
    return {
        "schema": VERSION,
        "kind": f"invented_{breaks.SETUP_FAMILIES[profile]}_b_entry_replay",
        "data_level": "B",
        "source_sha256": source.sha256,
        "source_bindings": bound,
        "profile": profile,
        "cost_profile": dict(model.costs),
        "as_of": as_of,
        "attempts": attempts,
        "price_only": True,
        "account_ledger_available": False,
        "orders_available": False,
        "market_cells_run": 0,
    }


def _requests(report, calendar, cost_profile, *, development_start=None):
    fxr = report["action_replay"]["profile"] == breaks.FXR_PROFILE
    h4 = calendar.frame("H4")
    expiry = {left.end: right.end for left, right in zip(h4, h4[1:])}
    trigger_bars = {frame["id"]: frame["bar"] for frame in report["action_replay"]["frames"]}
    tick = fills.text(selection.fraction(report["tick"]))
    fills.decimal(tick, positive=True)
    for decision in report["decisions"]:
        if decision["state"] != "READY":
            continue
        publication = trigger_bars[decision["h4_frame_id"]]
        if development_start is not None and publication["start"] < development_start:
            continue
        stop = fills.text(selection.fraction(decision["safety"]["stop"]))
        request = {
            "kind": "invented_b_price_request",
            "direction": decision["direction"],
            "trigger_end": publication["end"],
            "decision_at": fills.Event(publication["available"], H4_DECISION_ORDINAL).record(),
            "stop": stop,
            "target": None,
            "atr": decision["safety"]["atr_sma14"],
            "tick": tick,
            "exit_model": "E2" if fxr else "E1",
        }
        expires_at = expiry.get(publication["end"])
        target_levels = None
        if fxr:
            kind = "high" if decision["direction"] == "LONG" else "low"
            target_levels = tuple(selection.fraction(level["price"])
                                  for level in decision["target_levels"]["clusters"]
                                  if level["eligible"] and level["kind"] == kind)
        attempt = {
            "id": data.digest([decision["h4_frame_id"], decision["selected_line_id"], cost_profile]),
            "h4_frame_id": decision["h4_frame_id"],
            "selected_line_id": decision["selected_line_id"],
            "safety_line_id": decision["safety"]["line_id"],
            "expires_at": expires_at,
            "request": request,
        }
        if "dly_origin" in decision:
            attempt["dly_origin"] = decision["dly_origin"]
        yield attempt, target_levels
