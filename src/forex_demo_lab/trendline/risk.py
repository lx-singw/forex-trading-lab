"""One-position Level B admission using declared invented USD snapshots."""
from fractions import Fraction
import hashlib

from . import data, entries, exits, fills, geometry

VERSION = "TRL_B_RISK_182_V1"
SNAPSHOT_KIND = "invented_b_risk_snapshots"
RISK_FRACTION = Fraction("0.0025")
DAILY_FLOOR = Fraction("0.99")
UTC_DAY_MS = 86_400_000


def bindings():
    result = exits.bindings()
    path = "src/forex_demo_lab/trendline/risk.py"
    result[path] = hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest()
    return result


def _terms(profile):
    declaration, sha = data.read_json(data.ROOT / "config/research-candidates-117.json")
    if sha != fills.PROFILE_SHA:
        raise ValueError("frozen cost declaration changed")
    costs = declaration["cost_profiles"]
    common = costs["common"]
    return {**{key: Fraction(str(common[key])) for key in ("contract_size", "lot_min", "lot_step", "lot_max")},
            "leverage": Fraction(str(common["hypothetical_leverage"])),
            "commission": Fraction(str(costs[profile]["commission_usd_per_lot_round_turn"])),
            "slippage": Fraction(str(costs[profile]["slippage_pips_per_fill"])) * fills.PIP}


def _signed_usd(value):
    if isinstance(value, str) and value.startswith("-"):
        return -fills.decimal(value[1:])
    return fills.decimal(value)


def _snapshots(document, source, priced):
    data.fields(document, ("kind", "source_sha256", "profile", "cost_profile", "snapshots"))
    if (document["kind"], document["source_sha256"], document["profile"], document["cost_profile"]) != (
            SNAPSHOT_KIND, source.sha256, priced["profile"], priced["cost_profile"]["name"]):
        raise ValueError("invented risk snapshots must match the source, strategy and costs")
    rows = document["snapshots"]
    if type(rows) is not list or len(rows) > data.ROW_LIMIT:
        raise ValueError("bounded risk snapshot list required")
    scheduled = {window.start for window in source.calendar.frame("H1")}
    snapshots = {}
    previous, day = -1, None
    reference, paused = None, False
    for row in rows:
        data.fields(row, ("opening_at", "equity_usd", "free_margin_usd", "day_reference_usd", "entry_paused"))
        at = row["opening_at"]
        data.integer(at)
        if at not in scheduled or at <= previous or type(row["entry_paused"]) is not bool:
            raise ValueError("unique scheduled risk snapshots in opening order required")
        previous = at
        equity = _signed_usd(row["equity_usd"])
        free = _signed_usd(row["free_margin_usd"])
        anchor = fills.decimal(row["day_reference_usd"], positive=True)
        if at > priced["as_of"]:
            continue
        today = at // UTC_DAY_MS
        if today != day:
            day, reference, paused = today, anchor, False
        if anchor != reference:
            raise ValueError("daily reference equity must stay fixed within one UTC day")
        floor = reference * DAILY_FLOOR
        paused = paused or row["entry_paused"] or equity <= floor
        snapshots[at] = (equity, free, floor, paused, row)
    return snapshots


def _volume(terms, equity, free, headroom, stop_loss, margin_with_fee):
    step = terms["lot_step"]
    maximum = min(equity * RISK_FRACTION / stop_loss, max(0, free) / margin_with_fee,
                  headroom / stop_loss, terms["lot_max"])
    return (maximum // step) * step


def _size(terms, snapshot, price):
    equity, free, floor, _, _ = snapshot
    units, slip, fee = terms["contract_size"], terms["slippage"], terms["commission"]
    loss = (Fraction(price["stop_distance"]) + slip) * units + fee
    margin = Fraction(price["price"]) * units / terms["leverage"]
    debit = (Fraction(price["effective_spread_pips"]) * fills.PIP + 2 * slip) * units + fee
    headroom = equity - floor
    # The opening gate requires the stop past the exit-side quote, so
    # stop loss is strictly greater than the immediate liquidation debit.
    lots = _volume(terms, equity, free, headroom, loss, margin + fee / 2)
    if lots < terms["lot_min"]:
        lots = Fraction(0)
    return {"lots": fills.text(lots), "risk_budget_usd": fills.text(equity * RISK_FRACTION),
            "daily_headroom_usd": fills.text(headroom), "stop_loss_per_lot_usd": fills.text(loss),
            "estimated_stop_loss_usd": fills.text(lots * loss),
            "estimated_margin_usd": geometry.rational_record(lots * margin),
            "estimated_entry_commission_usd": fills.text(lots * fee / 2),
            "estimated_immediate_liquidation_debit_usd": fills.text(lots * debit)}


def _release(path, hours):
    if path["state"] != "CLOSED":
        return None
    exit_fill = path["exit"]
    if exit_fill["event"] is not None:
        # This is an opening price assumption learned from a completed row.
        # Occupancy at that opening survives its exit and release requires evidence.
        return hours[exit_fill["event"]["time"]].available_at
    return exit_fill["event_window"]["available_at"]


def _timeline(priced, exit_report, hours, snapshots, terms):
    paths = {path["attempt_id"]: path for path in exit_report["paths"]}
    as_of, liquidation = priced["as_of"], exit_report["liquidation_at"]
    decisions, positions = [], []
    occupant, release = None, None
    ordered = sorted(priced["attempts"], key=lambda a: a["first_scheduled_open"] or as_of + 1)
    for attempt in ordered:
        start, expires = attempt["first_scheduled_open"], attempt["expires_at"]
        price, reason = attempt["price_result"], attempt["reason"]
        record = {"attempt_id": attempt["id"], "opening_at": start,
                  "status": attempt["status"], "reason": reason}
        decisions.append(record)
        if ((price is None and reason not in ("AWAITING_ENTRY_BAR", "MISSING_ENTRY_BAR"))
                or attempt["status"] == "UNAVAILABLE" or start > as_of):
            continue
        if start >= liquidation:
            record.update(status="SKIPPED", reason="ENTRY_AT_LIQUIDATION")
            continue
        if occupant is not None and (release is None or start < release):
            record.update(status="SKIPPED", reason="POSITION_LIMIT", occupied_by=occupant["attempt_id"])
            continue
        snapshot = snapshots.get(start)
        if snapshot is None:
            record.update(status="UNAVAILABLE", reason="RISK_SNAPSHOT_UNAVAILABLE")
            continue
        equity, _, _, paused, _ = snapshot
        if equity <= 0 or paused:
            record.update(status="SKIPPED", reason="NONPOSITIVE_EQUITY" if equity <= 0 else "DAILY_PAUSE")
            continue

        release = expires if price is None else hours[start].available_at
        occupant = {"kind": "RESERVATION", "attempt_id": attempt["id"]}
        record.update(reserved_at=start, resolved_at=release if release <= as_of else None)
        if attempt["status"] == "PENDING":
            record.update(status="RESERVED")
        if attempt["status"] != "FILLED":
            continue
        sizing = _size(terms, snapshot, price)
        record["sizing"] = sizing
        if sizing["lots"] == "0":
            record.update(status="SKIPPED", reason="BELOW_MIN_LOT")
            continue
        record.update(status="ADMITTED", reason="SIZED_OPEN")
        path = paths[attempt["id"]]
        release = _release(path, hours)
        occupant = {"kind": "POSITION", "attempt_id": attempt["id"]}
        positions.append({"attempt_id": attempt["id"], "lots": sizing["lots"], "state": path["state"],
                          "reason": path["reason"], "release_at": release})

    active = occupant if release is None or as_of < release else None
    return decisions, positions, active


def _evaluate(source, hours, priced, exit_report, document):
    bound = bindings()
    snapshots = _snapshots(document, source, priced)
    terms = _terms(priced["cost_profile"]["name"])
    decisions, positions, active = _timeline(priced, exit_report, {hour.start: hour for hour in hours},
                                             snapshots, terms)
    if bound != bindings():
        raise ValueError("risk replay source bindings changed")
    return {"schema": VERSION, "kind": "invented_b_risk_admission", "source_sha256": source.sha256,
            "source_bindings": bound, "profile": priced["profile"], "as_of": priced["as_of"],
            "cost_profile": priced["cost_profile"], "liquidation_at": exit_report["liquidation_at"],
            "snapshot_prefix_sha256": data.digest([s[-1] for s in snapshots.values()]),
            "position_limit": 1, "risk_fraction": fills.text(RISK_FRACTION),
            "terms": {key: fills.text(value) for key, value in terms.items()},
            "decisions": decisions, "positions": positions, "active": active,
            "account_ledger_available": False, "orders_available": False}


def evaluate(replay, hours, document, *, as_of, cost_profile="base", liquidation_at=None):
    """Assess one invented strategy/cost/partition run using its supplied opening snapshots."""
    priced = entries.evaluate(replay, hours, as_of=as_of, cost_profile=cost_profile)
    exit_report = exits._evaluate(replay, hours, priced, liquidation_at)
    return _evaluate(replay.source, hours, priced, exit_report, document)
