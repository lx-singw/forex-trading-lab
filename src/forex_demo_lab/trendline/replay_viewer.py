"""Read-only receipt projection of saved, invented Level B accounting."""
from bisect import bisect_right
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from ..elliott_full.contracts import Bar
from . import breaks, data, engine, entries, exits, ledger, pivots, selection

VERSION = "TRL_B_VIEWER_187_V1"
TEMPLATE = Path(__file__).with_suffix(".html")
REPORT_LIMIT = 96 * 1024 * 1024


def _one_by(records, key):
    result = {row[key]: row for row in records}
    if len(result) != len(records):
        raise ValueError(f"duplicate viewer evidence for {key}")
    return result


def _headers(source, setups, priced, paths, account):
    action = setups["action_replay"]
    profile = action["profile"]
    if profile not in breaks.PROFILES:
        raise ValueError("known trendline replay profile required")
    family = breaks.SETUP_FAMILIES[profile]
    expected = ((setups, breaks.VERSION, f"invented_{family}_setup_replay", breaks.bindings()),
                (priced, entries.VERSION, f"invented_{family}_b_entry_replay", entries.bindings()),
                (paths, exits.VERSION, "invented_independent_b_exit_paths", exits.bindings()),
                (account, ledger.VERSION, "invented_b_usd_ledger", ledger.bindings()))
    for report, schema, kind, bindings in expected:
        if ((report["schema"], report["kind"], report.get("source_bindings"), report["orders_available"]) !=
                (schema, kind, bindings, False) or report["orders_available"] is not False):
            raise ValueError("matching invented Level B replay reports and source revisions required")
    if any(report["source_sha256"] != source.sha256 or report["profile"] != profile
           for report in (priced, paths, account)):
        raise ValueError("viewer report source or strategy mismatch")
    if ((action["declaration_sha256"], account["cost_profile"], account["as_of"], account["liquidation_at"]) !=
            (source.sha256, priced["cost_profile"]["name"], priced["as_of"], paths["liquidation_at"])
            or paths["as_of"] != priced["as_of"] or paths["cost_profile"] != priced["cost_profile"]
            or action["as_of"] > account["as_of"] or account["data_level"] != "B"
            or account["market_cells_run"] != 0 or setups["actual_source_admitted"] is not False):
        raise ValueError("viewer report cursor, costs or scope mismatch")
    return profile


def _frame_rows(replay, role, source, schedule, add):
    if (replay["schema"], replay["declaration_sha256"], replay["timeframe"]) != (engine.VERSION, source.sha256, "H4"):
        raise ValueError("matching H4 lifecycle replay required")
    registered, pokes = {}, {}
    events = _one_by(replay["journal"]["events"], "id")
    pivot_stream = pivots.PivotStream(source)
    confirmed, revisions = set(), {}
    for frame in replay["frames"]:
        bar = Bar(**frame["bar"])
        at, index = frame["as_of"], frame["bar_index"]
        data.integer(index)
        if (index >= len(schedule) or frame["event_type"] != "BAR"
                or (bar.available, schedule[index].start, schedule[index].end) != (at, bar.start, bar.end)):
            raise ValueError("viewer frame chronology mismatch")
        if role == "action":
            add(at, "CANDLE", {"index": index, **bar.record()})
        for point in pivot_stream.observe(bar):
            confirmed.add(point.id)
            if role == "action":
                add(at, "PIVOT", point.record())
        for event_id in frame["lifecycle_event_ids"]:
            command = events[event_id]["command"]
            operation, cursor, payload = (command[k] for k in ("op", "cursor", "payload"))
            if cursor != [at, frame["publication_ordinal"], index]:
                raise ValueError("viewer lifecycle event outside its frame")
            if operation == "REGISTER":
                line = selection.ValidatedLine.from_record(payload["line"])
                if not set(line.touch_ids) <= confirmed:
                    raise ValueError("viewer line uses a pivot before confirmation")
                registered[engine.instance_id(line)] = line.record()
            if operation == "POKE":
                if payload["bar"] != bar.record():
                    raise ValueError("viewer penetration bar mismatch")
                pokes[payload["line_id"]] = index
        for revision in frame["revisions"]:
            identity = revision["line_id"]
            previous = revisions.get(identity, 0)
            if (revision["at"] != {"available_at": at, "bar_index": index,
                                   "publication_ordinal": frame["publication_ordinal"]}
                    or revision["revision"] != previous + 1 or identity not in registered
                    or (revision["view"]["status"] == "POKED" and identity not in pokes)):
                raise ValueError("viewer line revision outside its known history")
            revisions[identity] = revision["revision"]
            add(at, "LINE", {"role": role, "line_id": identity, "revision": revision["revision"],
                             "ray": registered[identity]["ray"], "view": revision["view"],
                             "poke_index": pokes.get(identity), "available_at": at})
    return _one_by(replay["frames"], "id")


def _admissions(priced, account, decisions, add):
    attempts = _one_by(priced["attempts"], "id")
    gates = _one_by(account["decisions"], "attempt_id")
    if attempts.keys() != gates.keys():
        raise ValueError("viewer account does not cover the saved entry attempts")
    for identity, gate in gates.items():
        attempt = attempts[identity]
        setup = decisions[attempt["h4_frame_id"]]
        known = setup["available_at"]
        if (attempt["selected_line_id"] != setup["selected_line_id"]
                or attempt["request"]["decision_at"]["time"] != known
                or gate["opening_at"] != attempt["first_scheduled_open"]):
            raise ValueError("viewer entry attempt does not match its setup")
        start = gate.get("reserved_at")
        if start is not None:
            if start < known or start != gate["opening_at"]:
                raise ValueError("viewer reservation predates its setup")
            add(start, "ADMISSION", {"attempt_id": identity, "h4_frame_id": setup["h4_frame_id"],
                                     "status": "RESERVED", "reason": "AWAITING_ENTRY_BAR"})
        if gate["status"] in ("PENDING", "RESERVED"):
            continue
        receipt = gate.get("resolved_at")
        if receipt is None:
            # Price gates decided by the setup can precede the scheduled open.
            receipt = known if gate["reason"] in ("NO_SCHEDULED_ENTRY", "LATE_DECISION", "ENTRY_WINDOW_EXPIRED",
                                                   "EXECUTION_SIDE_DATA_UNAVAILABLE") else gate["opening_at"]
        if receipt is None or receipt < known or (start is not None and receipt < start):
            raise ValueError("viewer admission receipt missing or out of order")
        add(receipt, "ADMISSION", {**gate, "h4_frame_id": setup["h4_frame_id"]})
    return {identity: {**gate, "h4_frame_id": attempts[identity]["h4_frame_id"]}
            for identity, gate in gates.items()}


def _account_rows(schedule, paths, account, gates, add):
    path_by_id = _one_by(paths["paths"], "attempt_id")
    closed = _one_by(account["trades"], "attempt_id")
    positions = _one_by(account["positions"], "attempt_id")
    expected = {identity for identity, gate in gates.items() if gate["status"] == "ADMITTED"}
    if positions.keys() != expected or not expected <= path_by_id.keys() or not closed.keys() <= expected:
        raise ValueError("viewer position evidence does not match admissions")
    opened, settled = {}, set()
    held = None
    starts = [slot.start for slot in schedule]
    for event in account["events"]:
        effective, receipt, kind = (event[k] for k in ("effective_at", "available_at", "kind"))
        data.integer(effective)
        if effective > receipt:
            raise ValueError("viewer account event predates its effective time")
        item = {"event": event}
        if kind in ("ENTRY_FILL", "EXIT_FILL"):
            identity = event["attempt_id"]
            position = path_by_id[identity]["entry"]
            index = bisect_right(starts, effective) - 1
            # Intrahour exits are shown at their recorded effective time.
            item["index"] = index
            item["h4_frame_id"] = gates[identity]["h4_frame_id"]
            if kind == "ENTRY_FILL":
                if (held is not None or identity in opened or identity not in expected
                        or (receipt, effective, event["price"], event["lots"]) != (
                            gates[identity]["resolved_at"], position["entry_at"]["time"],
                            position["entry_price"], positions[identity]["lots"])):
                    raise ValueError("viewer entry fill does not match the sized admission")
                held = identity
                opened[identity] = receipt
                item["held"] = {k: position[k] for k in ("direction", "initial_stop", "target")}
            else:
                if (held != identity or identity not in closed or identity in settled
                        or (receipt, event["price"]) != (positions[identity]["release_at"], closed[identity]["exit_price"])):
                    raise ValueError("viewer exit fill does not match the released position")
                settled.add(identity)
                held = None
                item["trade"] = closed[identity]
        add(receipt, "ACCOUNT", item)
    if opened.keys() != expected or settled != closed.keys():
        raise ValueError("viewer missing entry or exit evidence")
    for identity, admission in opened.items():
        for change in path_by_id[identity]["protection_events"]:
            when = max(admission, change["decision_at"]["time"])
            release = positions[identity]["release_at"]
            if release is not None and when > release:
                raise ValueError("viewer protection change follows position release")
            add(when, "PROTECTION", {"attempt_id": identity, **change})
    liability = account["open_liability"]
    if liability is not None and (liability["attempt_id"] != held
                                 or liability["last_mark"]["available_at"] > account["as_of"]):
        raise ValueError("viewer terminal liability evidence mismatch")


def viewer_data(source, setups, priced, paths, account):
    profile = _headers(source, setups, priced, paths, account)
    calendar = source.calendar
    start, cutoff = calendar.start, account["as_of"]
    if not start <= cutoff <= calendar.end + 60000:
        raise ValueError("viewer cursor outside saved receipt scope")
    groups = defaultdict(list)

    def add(at, kind, value):
        data.integer(at)
        if not start <= at <= cutoff:
            raise ValueError("viewer evidence outside saved receipt scope")
        groups[at].append({"kind": kind, "value": value})

    add(start, "START", {})
    schedule = calendar.frame("H4")
    action = _frame_rows(setups["action_replay"], "action", source, schedule, add)
    safety = action if setups["safety_replay"] is None else _frame_rows(
        setups["safety_replay"], "safety", source, schedule, add)
    decisions = _one_by(setups["decisions"], "h4_frame_id")
    if decisions.keys() != action.keys() or len(safety) != len(action):
        raise ValueError("viewer setup publications do not cover the replay")
    for key, decision in decisions.items():
        at = decision["available_at"]
        if (action[key]["as_of"] != at or action[key]["bar_index"] != decision["bar_index"]
                or safety[decision["safety_frame_id"]]["bar"] != action[key]["bar"]):
            raise ValueError("viewer setup timing does not match its publications")
        add(at, "SETUP", decision)
    gates = _admissions(priced, account, decisions, add)
    _account_rows(schedule, paths, account, gates, add)
    add(cutoff, "END", {"status": account["status"], "open_liability": account["open_liability"]})
    return {"version": VERSION, "kind": "saved_invented_trendline_view", "profile": profile,
            "data_level": "B", "geometry_basis": source.record()["geometry_basis"],
            "partition": source.record()["partition"], "cost": account["cost_profile"],
            "groups": [{"at": at, "items": rows} for at, rows in sorted(groups.items())],
            "orders_available": False}


def render(view):
    payload = json.dumps(view, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return TEMPLATE.read_text(encoding="utf-8").replace("/*REPLAY_DATA*/",
                                                        payload.replace("<", "\\u003c").replace("&", "\\u0026"))


def export(descriptor, report_directory, output):
    raw, descriptor_sha = data.read_json(descriptor)
    source = data.Declaration.from_record(raw)
    root = data.no_links(report_directory)
    names = ("setups.json", "entries.json", "exits.json", "ledger.json")
    loaded = [data.read_json(root / name, limit=REPORT_LIMIT) for name in names]
    view = viewer_data(source, *(record for record, _ in loaded))
    html = render(view).encode("utf-8")
    manifest = {"version": VERSION, "kind": view["kind"], "source_sha256": source.sha256,
                "descriptor_file_sha256": descriptor_sha, "data_level": "B",
                "geometry_basis": view["geometry_basis"], "profile": view["profile"], "cost": view["cost"],
                "partition": view["partition"], "receipt_groups": len(view["groups"]),
                "reports": {name: result[1] for name, result in zip(names, loaded, strict=True)},
                "html_sha256": hashlib.sha256(html).hexdigest(), "orders_available": False}
    destination = data.no_links(output)
    destination.mkdir(exist_ok=False, parents=True)
    with (destination / "replay.html").open("xb") as handle:
        handle.write(html)
    data.write_new(destination / "manifest.json", manifest)
    return manifest
