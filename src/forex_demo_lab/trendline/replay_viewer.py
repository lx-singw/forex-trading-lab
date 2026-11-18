"""Read-only receipt projection of saved, invented Level B and Q accounting."""
from bisect import bisect_right
from collections import Counter, defaultdict, deque
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from ..elliott_full.contracts import Bar
from . import breaks, context, data, engine, entries, exits, fills, ledger, pivots, quote_replay, quotes, replay_exports, selection

VERSION = "TRL_VIEWER_191_V1"
ANNOTATION_SCHEMA = "TRL_MANUAL_LINES_191_V1"
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


def _strict_extreme(kind, center, neighbors):
    if kind == "high":
        return all(center.high > bar.high for bar in neighbors)
    return all(center.low < bar.low for bar in neighbors)


def _provisional_pivots(window):
    """Show only still-possible extrema from the contiguous H4 prefix."""
    radius = pivots.RADIUS
    result = {}
    for offset in range(radius, len(window)):
        index, center = window[offset]
        neighbors = [bar for _, bar in window[offset - radius:offset] + window[offset + 1:]]
        remaining = radius - (len(window) - offset - 1)
        for kind in ("high", "low"):
            if _strict_extreme(kind, center, neighbors):
                identity = data.digest([center.lineage, kind, radius])
                result[identity] = {"id": identity, "kind": kind, "bar_index": index,
                                    "price": str(getattr(center, kind)), "occurred_at": center.end,
                                    "first_available_at": center.available, "right_bars_needed": remaining}
    return result


def _pivot_frontier(window, prior, index, bar, confirmed, add):
    gap = bool(window and window[-1][0] + 1 != index)
    if gap:
        window.clear()
    window.append((index, bar))
    active = _provisional_pivots(list(window))
    if active == prior:
        return active
    confirmed_ids = {point.id for point in confirmed}
    resolved = []
    for identity in prior.keys() - active.keys():
        candidate = prior[identity]
        kind = candidate["kind"]
        if identity in confirmed_ids:
            reason = "CONFIRMED"
        elif gap:
            reason = "DATA_GAP"
        else:
            disqualified = (bar.high >= Fraction(candidate["price"]) if kind == "high"
                            else bar.low <= Fraction(candidate["price"]))
            reason = "RIGHT_EXTREME_OR_TIE" if disqualified else "DUAL_EXTREME"
        resolved.append({**candidate, "reason": reason})
    resolved.sort(key=lambda item: (item["bar_index"], item["kind"]))
    add(bar.available, "PIVOT_CANDIDATES", {"bar_index": index, "active": list(active.values()),
                                            "resolved": resolved})
    return active


def _frame_rows(replay, role, source, schedule, add):
    if (replay["schema"], replay["declaration_sha256"], replay["timeframe"]) != (engine.VERSION, source.sha256, "H4"):
        raise ValueError("matching H4 lifecycle replay required")
    registered, pokes = {}, {}
    events = _one_by(replay["journal"]["events"], "id")
    pivot_stream = pivots.PivotStream(source)
    confirmed, revisions = set(), {}
    pivot_window, provisional = deque(maxlen=2 * pivots.RADIUS), {}
    for frame in replay["frames"]:
        bar = Bar(**frame["bar"])
        at, index = frame["as_of"], frame["bar_index"]
        data.integer(index)
        if (index >= len(schedule) or frame["event_type"] != "BAR"
                or (bar.available, schedule[index].start, schedule[index].end) != (at, bar.start, bar.end)):
            raise ValueError("viewer frame chronology mismatch")
        if role == "action":
            add(at, "CANDLE", {"index": index, **bar.record()})
        points = pivot_stream.observe(bar)
        for point in points:
            confirmed.add(point.id)
            if role == "action":
                add(at, "PIVOT", point.record())
        if role == "action":
            provisional = _pivot_frontier(pivot_window, provisional, index, bar, points, add)
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
    linked = {}
    for identity, gate in gates.items():
        attempt = attempts[identity]
        setup = decisions[attempt["h4_frame_id"]]
        known = setup["available_at"]
        if (attempt["selected_line_id"] != setup["selected_line_id"]
                or attempt["request"]["decision_at"]["time"] != known
                or gate["opening_at"] != attempt["first_scheduled_open"]):
            raise ValueError("viewer entry attempt does not match its setup")
        plan = {key: attempt[key] for key in ("h4_frame_id", "request", "expires_at")}
        linked[identity] = {**gate, **plan}
        start = gate.get("reserved_at")
        if start is not None:
            if start < known or start != gate["opening_at"]:
                raise ValueError("viewer reservation predates its setup")
            add(start, "ADMISSION", {**plan, "attempt_id": identity, "opening_at": start,
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
        add(receipt, "ADMISSION", linked[identity])
    return linked


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
            item["admission"] = gates[identity]
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


def _timeline(calendar, cutoff):
    data.integer(cutoff)
    if not calendar.start <= cutoff <= calendar.end + 60000:
        raise ValueError("viewer cursor outside saved receipt scope")
    groups = defaultdict(list)

    def add(at, kind, value):
        data.integer(at)
        if not calendar.start <= at <= cutoff:
            raise ValueError("viewer evidence outside saved receipt scope")
        groups[at].append({"kind": kind, "value": value})

    add(calendar.start, "START", {})
    return groups, add


def _line_search_evidence(frame):
    return {"coverage_state": frame["coverage_state"], "snapshot_reasons": frame["snapshot_reasons"],
            "action_lines": len(frame["action_line_ids"]), "eligible_lines": len(frame["eligible_line_ids"]),
            "anchor_rejections": dict(Counter(reason for row in frame["pair_rejections"] for reason in row["reasons"])),
            "candidate_rejections": dict(Counter(reason for row in frame["candidates"] for reason in row["reasons"]))}


def _setup_rows(source, setups, schedule, add):
    action = _frame_rows(setups["action_replay"], "action", source, schedule, add)
    safety = action if setups["safety_replay"] is None else _frame_rows(
        setups["safety_replay"], "safety", source, schedule, add)
    decisions = _one_by(setups["decisions"], "h4_frame_id")
    if decisions.keys() != action.keys() or len(safety) != len(action):
        raise ValueError("viewer setup publications do not cover the replay")
    known_action_lines = set()
    for key, frame in action.items():
        decision = decisions[key]
        at = decision["available_at"]
        safety_frame = safety[decision["safety_frame_id"]]
        if (frame["as_of"] != at or frame["bar_index"] != decision["bar_index"]
                or safety_frame["bar"] != frame["bar"]):
            raise ValueError("viewer setup timing does not match its publications")
        search = {"action": _line_search_evidence(frame)}
        if safety is not action:
            search["safety"] = _line_search_evidence(safety_frame)
        add(at, "SETUP", {**decision, "line_search": search})
        known_action_lines.update(row["line_id"] for row in frame["revisions"])
        for contact in decision.get("contacts", []):
            if contact["line_id"] not in known_action_lines:
                raise ValueError("viewer bounce contact precedes its action line")
            add(at, "CONTACT", {**contact, "h4_frame_id": key, "bar_index": frame["bar_index"]})
    return decisions


def _view(groups, add, *, account, source, profile, level, basis):
    add(account["as_of"], "END", {key: account[key] for key in ("status", "open_liability", "account")})
    partition = source.record()["partition"]
    chart = {"source_sha256": source.sha256, "symbol": "EURUSD", "timeframe": "H4",
             "data_level": level, "geometry_basis": basis, "partition": partition}
    return {"version": VERSION, "kind": "saved_invented_trendline_view", "profile": profile,
            "data_level": level, "geometry_basis": basis, "partition": partition, "chart": chart,
            "cost": account["cost_profile"],
            "groups": [{"at": at, "items": rows} for at, rows in sorted(groups.items())],
            "orders_available": False}


def viewer_data(source, setups, priced, paths, account):
    profile = _headers(source, setups, priced, paths, account)
    groups, add = _timeline(source.calendar, account["as_of"])
    schedule = source.calendar.frame("H4")
    decisions = _setup_rows(source, setups, schedule, add)
    gates = _admissions(priced, account, decisions, add)
    _account_rows(schedule, paths, account, gates, add)
    return _view(groups, add, account=account, source=source, profile=profile, level="B",
                 basis=source.record()["geometry_basis"])


def _quote_setups(tape, account, prefix):
    as_of, profile = account["as_of"], account["profile"]
    publications = tape.publications(prefix, as_of)
    if account["publications"] != [bar.record() for bar in publications]:
        raise ValueError("viewer publications do not match the bound quote receipts")
    replay = breaks.BreakReplay(tape.geometry_source, account["tick_size"], profile,
                               enable_dly=account["enable_dly"])
    frames = ("D1", "H4") if profile in (context.PROFILE, breaks.FXR_PROFILE) else ("H4",)
    for bar in publications:
        if bar.timeframe in frames:
            replay.observe(bar)
    report = replay.report(as_of=as_of)
    if account["setup_decisions"] != report["decisions"]:
        raise ValueError("viewer setup decisions do not match the bound publications")
    return report


def _quote_rows(tape, account, prefix, add):
    model = fills.PriceModel(tape.geometry_source, account["cost_profile"])
    floor = Fraction(model.costs["spread_floor_pips"]) * fills.PIP
    executable, candidates, quality = [], [], Counter()
    previous = None
    for quote in prefix:
        reason = quote_replay._quality(tape, quote, previous)
        previous = quote
        quality[reason] += 1
        observation = {"quote": quote.record(), "reason": reason}
        if reason == "EXECUTABLE":
            executable.append(quote)
            bid, ask, spread = quote_replay._prices(quote, floor)
            entry_spread_passes = spread <= quotes.MAX_ENTRY_SPREAD
            observation.update(modeled_bid=fills.text(bid), modeled_ask=fills.text(ask),
                               effective_spread_pips=fills.text(spread / fills.PIP),
                               entry_spread_passes=entry_spread_passes)
            if entry_spread_passes:
                candidates.append(quote)
            else:
                quality["ENTRY_SPREAD_EXCEEDED"] += 1
        add(quote.time, "QUOTE", observation)
    if quality != account["quote_quality"]:
        raise ValueError("viewer quote quality does not match the bound tape")
    return executable, candidates


def _quote_gates(tape, setups, account, candidates, add):
    expected, at_quote = quote_replay._decisions(tape, setups, candidates, account["as_of"], account["cost_profile"])
    assignments = {attempt["id"]: sequence for sequence, (attempt, _) in at_quote.items()}
    by_sequence = {quote.sequence: quote for quote in candidates}
    gates = _one_by(account["decisions"], "id")
    if gates.keys() != {attempt["id"] for attempt in expected}:
        raise ValueError("viewer quotes do not cover the saved entry decisions")
    for attempt in expected:
        identity = attempt["id"]
        gate = gates[identity]
        at = attempt["request"]["decision_at"]["time"]
        if any(gate.get(key) != value for key, value in attempt.items() if key not in ("status", "reason")):
            raise ValueError("viewer quote decision does not match its setup")
        sequence = assignments.get(identity)
        if sequence is None:
            if gate != attempt:
                raise ValueError("viewer quote expiry or pending state mismatch")
            if gate["status"] == "PENDING":
                add(at, "ADMISSION", gate)
                continue
            receipt = at if gate["reason"] == "ENTRY_WINDOW_EXPIRED" else max(
                at, min(gate["expires_at"], tape.liquidation))
        else:
            quote = by_sequence[sequence]
            if gate.get("quote") != quote.record() or gate["status"] not in ("ADMITTED", "SKIPPED", "UNAVAILABLE"):
                raise ValueError("viewer gate does not match the first eligible quote")
            receipt = quote.time
        if receipt > at:
            add(at, "ADMISSION", {**attempt, "status": "PENDING", "reason": "AWAITING_ELIGIBLE_QUOTE"})
        add(receipt, "ADMISSION", gate)
    return gates


def _quote_account_rows(schedule, account, gates, executable, add):
    positions = _one_by(account["positions"], "attempt_id")
    trades = _one_by(account["trades"], "attempt_id")
    expected = {identity for identity, gate in gates.items() if gate["status"] == "ADMITTED"}
    if positions.keys() != expected or not trades.keys() <= expected:
        raise ValueError("viewer quote positions do not match their admissions")
    starts = [slot.start for slot in schedule]
    sources = [quote.source for quote in executable]
    by_sequence = {quote.sequence: quote.record() for quote in executable}
    opened, closed = set(), set()
    held, last_receipt = None, 0
    for event in account["events"]:
        at, receipt, kind = (event[key] for key in ("effective_at", "available_at", "kind"))
        data.integer(at)
        if at > receipt or receipt < last_receipt:
            raise ValueError("viewer quote account events are out of receipt order")
        last_receipt = receipt
        item = {"event": event}
        if kind in ("ENTRY_FILL", "EXIT_FILL"):
            identity = event["attempt_id"]
            position, gate = positions[identity], gates[identity]
            index = bisect_right(starts, at) - 1
            item.update(index=index, h4_frame_id=gate["h4_frame_id"], admission=gate)
            if kind == "ENTRY_FILL":
                quote = position["opening_quote"]
                if (held is not None or identity in opened or quote != gate["quote"]
                        or receipt != gate["reserved_at"] or event["mark"]["sequence"] != quote["sequence"]
                        or event["lots"] != gate["sizing"]["lots"]):
                    raise ValueError("viewer quote entry does not match its admission")
                held = identity
                opened.add(identity)
                item["held"] = {"direction": gate["request"]["direction"], "initial_stop": position["stop"],
                                "target": position["target"]}
            else:
                quote = position["closing_quote"]
                trade = trades[identity]
                if (held != identity or receipt != position["release_at"] or event["price"] != trade["exit_price"]
                        or trade["exit_at"] != {"time": at, "ordinal": quote["sequence"]}):
                    raise ValueError("viewer quote exit does not match its position release")
                held = None
                closed.add(identity)
                item["trade"] = trade
            if (quote != by_sequence.get(quote["sequence"]) or (at, receipt) != (quote["source"], quote["time"])
                    or index < 0 or at >= schedule[index].end):
                raise ValueError("viewer fill quote lies outside its receipt or H4 window")
            item["quote"] = quote
        add(receipt, "ACCOUNT", item)
    if opened != expected or closed != trades.keys():
        raise ValueError("viewer quote ledger is missing fills")
    liability = account["open_liability"]
    if ((None if liability is None else liability["attempt_id"]) != held
            or (liability is not None and liability["last_mark"]["available_at"] > account["as_of"])):
        raise ValueError("viewer quote liability does not match its held position")
    for identity, position in positions.items():
        opening = position["opening_quote"]
        closing = position.get("closing_quote")
        for change in position["protection_events"]:
            at = change["decision_at"]["time"]
            if not opening["source"] < at <= account["as_of"]:
                raise ValueError("viewer quote protection decision is outside its source scope")
            index = bisect_right(sources, at)
            # Finish may derive a pending stop at the saved boundary without a quote ever using it.
            # The endpoint exposes that liability separately from quote-applied changes.
            if index == len(executable):
                continue
            quote = executable[index]
            if closing is not None and quote.sequence > closing["sequence"]:
                raise ValueError("viewer quote protection applied after the closing quote")
            add(quote.time, "PROTECTION", {"attempt_id": identity, **change, "quote": quote.record()})


def quote_viewer_data(tape, account):
    if ((account["schema"], account["kind"], account["data_level"], account["geometry_basis"],
         account["tape_sha256"], account["source_bindings"], account["liquidation_at"], account["partition_end"]) !=
            (quote_replay.VERSION, "invented_q_usd_ledger", "Q", "mid_sync", tape.sha256,
             quote_replay.bindings(), tape.liquidation, tape.calendar.end)
            or account["actual_source_admitted"] is not False or account["orders_available"] is not False
            or account["market_cells_run"] != 0 or type(account["enable_dly"]) is not bool):
        raise ValueError("matching invented Level Q ledger and tape required")
    source, as_of = tape.geometry_source, account["as_of"]
    groups, add = _timeline(tape.calendar, as_of)
    schedule = tape.calendar.frame("H4")
    prefix = tuple(tape.prefix(as_of))
    setups = _quote_setups(tape, account, prefix)
    _setup_rows(source, setups, schedule, add)
    executable, candidates = _quote_rows(tape, account, prefix, add)
    gates = _quote_gates(tape, setups, account, candidates, add)
    _quote_account_rows(schedule, account, gates, executable, add)
    return _view(groups, add, account=account, source=source, profile=account["profile"], level="Q", basis="mid_sync")


def render(view):
    payload = json.dumps(view, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return TEMPLATE.read_text(encoding="utf-8").replace("/*REPLAY_DATA*/",
                                                        payload.replace("<", "\\u003c").replace("&", "\\u0026"))


def export(descriptor, report_directory, output, *, unlock_receipt=None):
    raw, descriptor_sha = data.read_json(descriptor)
    root = data.no_links(report_directory)
    if raw["schema"] == quotes.VERSION:
        unlock, unlock_sha = (None, None) if unlock_receipt is None else data.read_json(unlock_receipt)
        tape = quotes.Tape(raw, unlock)
        account, account_sha = data.read_json(root / "quote-ledger.json", limit=REPORT_LIMIT)
        checkpoint, checkpoint_sha = data.read_json(root / "checkpoint.json")
        if checkpoint != quote_replay.checkpoint(account):
            raise ValueError("saved quote ledger does not match its checkpoint")
        view = quote_viewer_data(tape, account)
        inputs = {"tape_sha256": tape.sha256, "tape_file_sha256": descriptor_sha,
                  "reports": {"quote-ledger.json": account_sha, "checkpoint.json": checkpoint_sha}}
        if unlock_sha is not None:
            inputs["unlock_file_sha256"] = unlock_sha
    else:
        if unlock_receipt is not None:
            raise ValueError("a viewer unlock receipt applies only to Level Q")
        source = data.Declaration.from_record(raw)
        names = ("setups.json", "entries.json", "exits.json", "ledger.json")
        loaded = {name: data.read_json(root / name, limit=REPORT_LIMIT) for name in names}
        view = viewer_data(source, *(record for record, _ in loaded.values()))
        inputs = {"source_sha256": source.sha256, "descriptor_file_sha256": descriptor_sha,
                  "reports": {name: digest for name, (_, digest) in loaded.items()}}
    html = render(view).encode("utf-8")
    template = {"schema": ANNOTATION_SCHEMA, "chart": view["chart"], "lines": []}
    artifacts = {"replay.html": html, **replay_exports.artifacts(view),
                 "annotation-template.json": (json.dumps(template, indent=2) + "\n").encode("utf-8")}
    manifest = {"version": VERSION, "kind": view["kind"], **inputs, "data_level": view["data_level"],
                "geometry_basis": view["geometry_basis"], "profile": view["profile"], "cost": view["cost"],
                "partition": view["partition"], "chart": view["chart"], "receipt_groups": len(view["groups"]),
                "as_of_ms": view["groups"][-1]["at"],
                "files": {name: hashlib.sha256(content).hexdigest() for name, content in artifacts.items()},
                "orders_available": False}
    manifest["html_sha256"] = manifest["files"]["replay.html"]
    artifacts["manifest.json"] = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode("utf-8")
    destination = data.no_links(output)
    destination.mkdir(exist_ok=False, parents=True)
    created = []
    try:
        for name, content in artifacts.items():
            path = destination / name
            with path.open("xb") as handle:
                created.append(path)
                handle.write(content)
    except OSError:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        destination.rmdir()
        raise
    return manifest
