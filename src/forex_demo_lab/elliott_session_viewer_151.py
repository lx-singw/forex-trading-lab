"""Read-only, local viewer for saved invented EW_FULL session149 accounts.

An export identifies saved bytes; it does not rerun or authenticate their trading
decisions. No strategy, source qualification or order interface is added.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from . import elliott_session_comparison_149 as comparison
from .elliott_full.contracts import Bar, Quote, integer

VERSION = "FXDL_ELLIOTT_SESSION_VIEWER151_V1"
TEMPLATE = Path(__file__).with_suffix(".html")
MAX_REPORT_BYTES = 256 * 1024 * 1024
SNAPSHOT_FIELDS = ("time", "frame", "reason", "context", "context_details",
                   "pattern_window", "search_incomplete", "rule_rejection_count",
                   "rule_rejections", "session_coverage", "signals", "interpretations")
NODE_FIELDS = ("id", "family", "side", "state", "depth", "available", "actionable",
               "diagnostics", "pivot_records", "anchors")


def source_bindings():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), TEMPLATE)}


def _snapshot(value):
    """Retain recorded ranking; never choose a newer terminal over that ranking."""
    now = value["time"]
    integer(now)
    if value["frame"] not in ("H1", "H4", "D1"):
        raise ValueError("viewer_snapshot_frame")
    def known(node):
        if node.get("available", now) > now:
            raise ValueError("viewer_future_count")
        for pivot in node.get("pivot_records", []):
            if pivot["available"] > now or pivot["time"] > pivot["available"]:
                raise ValueError("viewer_future_pivot")
        for child in node.get("children", []):
            known(child)
    for node in value["counts"]:
        known(node)
    for count in value["interpretations"]:
        known(count)
    if any(s["formed"] > now for s in value["signals"]):
        raise ValueError("viewer_future_signal")
    result = {k: deepcopy(value[k]) for k in SNAPSHOT_FIELDS if k in value}
    result["counts"] = [{k: deepcopy(n[k]) for k in NODE_FIELDS if k in n} for n in value["counts"]]
    return result


def viewer_data(account, bars, journal):
    """Join publication and ledger records using the original raw-event order.

    Quote effects are atomic. Financing is shown at receipt, even when its ledger
    effective date is earlier. Cancellation timestamps lack an event ordinal;
    place them conservatively after all other events at that timestamp.
    """
    if (account.get("kind") != "invented_session_account149"
            or account.get("candidate") != "EW_FULL_V1"
            or account.get("orders_available") is not False
            or account.get("market_status") != "UNAVAILABLE"
            or account.get("market_returns") is not None):
        raise ValueError("viewer_invented_EW_account_required")
    if account["profile"] not in comparison.PROFILES or account["partition"]["name"] not in comparison.PARTITIONS:
        raise ValueError("viewer_profile_partition")
    paper = account["original_report"]
    if (paper.get("kind") != "invented_session_paper_148"
            or paper.get("orders_available") is not False
            or paper.get("market_cells_run") != 0
            or paper.get("market_returns") is not None
            or paper.get("profile") != account["profile"]
            or paper["ledger"]["finished"] is not True
            or paper["decisions"].get("kind") != "invented_session_strategy_decisions_147"
            or paper["decisions"].get("orders_available") is not False):
        raise ValueError("viewer_finished_invented_paper_required")
    snapshots = paper["decisions"]["snapshots"]
    ledger = paper["ledger"]["events"]
    gates = paper["quote_gates"]
    rows = []
    si = li = qi = 0
    seen_bars = []
    last_time = -1
    for event in journal:
        kind, value = event["kind"], event["value"]
        if kind == "bars":
            if not value or len(value) > 3 or len({b["timeframe"] for b in value}) != len(value):
                raise ValueError("viewer_publication_batch")
            now = value[0]["available"]
            for raw in value:
                bar = Bar(**raw)
                if bar.available != now or si >= len(snapshots):
                    raise ValueError("viewer_publication_snapshot")
                snapshot = _snapshot(snapshots[si])
                if (snapshot["time"], snapshot["frame"]) != (now, bar.timeframe):
                    raise ValueError("viewer_snapshot_order")
                rows.append({"kind": "publication", "time": now, "bar_index": si,
                             "snapshot": snapshot, "label": bar.timeframe + ": " + snapshot["reason"]})
                seen_bars.append(raw)
                si += 1
        elif kind in ("quote", "finish"):
            quote = Quote(**value)
            now = quote.time
            effects = []
            while li < len(ledger):
                effect = ledger[li]
                li += 1
                effects.append(deepcopy(effect))
                if effect["kind"] == kind:
                    if (int(effect["time"]), effect["sequence"]) != (now, quote.sequence):
                        raise ValueError("viewer_quote_ledger_order")
                    break
                if effect["kind"] not in ("entry", "exit", "financing"):
                    raise ValueError("viewer_ledger_effect")
                if int(effect["time"]) > now or (effect["kind"] != "financing" and int(effect["time"]) != now):
                    raise ValueError("viewer_effect_receipt")
            if not effects or effects[-1]["kind"] != kind:
                raise ValueError("viewer_missing_ledger_event")
            row = {"kind": kind, "time": now, "effects": effects,
                   "quote": deepcopy(value), "label": kind + ": " + effects[-1].get("result", "finished")}
            if kind == "quote":
                if qi >= len(gates) or (gates[qi]["time"], gates[qi]["sequence"]) != (now, quote.sequence):
                    raise ValueError("viewer_quote_gate_order")
                row["gate"] = deepcopy(gates[qi])
                qi += 1
            rows.append(row)
        else:
            raise ValueError("viewer_session149_journal_kind")
        if now < last_time:
            raise ValueError("viewer_journal_clock")
        last_time = now
    if (si != len(snapshots) or li != len(ledger) or qi != len(gates)
            or seen_bars != bars or not rows or rows[-1]["kind"] != "finish"
            or paper["time"] != last_time):
        raise ValueError("viewer_incomplete_saved_account")
    for cancellation in paper["cancellations"]:
        integer(cancellation["time"])
        if not rows[0]["time"] <= cancellation["time"] <= last_time:
            raise ValueError("viewer_cancellation_clock")
        rows.append({"kind": "cancellation", "time": cancellation["time"],
                     "label": "Cancelled: " + cancellation["reason"],
                     "cancellation": deepcopy(cancellation), "timing": "after_all_events_at_recorded_time"})
    rows.sort(key=lambda r: (r["time"], r["kind"] == "cancellation"))
    return {"version": VERSION, "profile": account["profile"], "partition": account["partition"]["name"],
            "bars": deepcopy(bars), "rows": rows, "orders_available": False,
            "market_returns": None, "limitations": [
                "Constructed prices and hypothetical costs; no market performance established.",
                "Saved-report inspection only; decisions and accounting are not recomputed by this viewer.",
                "Only recorded confirmed pivots and bounded count candidates are available; provisional pivots are not reconstructed.",
                "Rank order is recorded order, not a new viewer-selected trading recommendation.",
                "Cancellation ordering within a timestamp is conservative; financing appears when received.",
                "Sparse quotes do not establish intrabar drawdown; inherited UTC financing limitations remain."]}


def state_at(view, index, frame="H1", limit=180):
    """Reference cursor projection, shared contract with the browser implementation."""
    if type(index) is not int or not 0 <= index < len(view["rows"]) or frame not in ("H1", "H4", "D1"):
        raise ValueError("viewer_cursor")
    snapshot = None
    bars, actions, cancellations = [], [], []
    cash = gate = position = None
    for row in view["rows"][:index + 1]:
        if row["kind"] == "publication":
            bar = view["bars"][row["bar_index"]]
            if bar["timeframe"] == frame:
                bars.append(bar)
                snapshot = row["snapshot"]
        for effect in row.get("effects", []):
            if effect["kind"] in ("entry", "exit"):
                actions.append(effect)
                position = effect if effect["kind"] == "entry" else None
            if "cash" in effect:
                cash = effect["cash"]
        if "gate" in row:
            gate = row["gate"]
        if "cancellation" in row:
            cancellations.append(row["cancellation"])
    return {"row": view["rows"][index], "snapshot": snapshot, "bars": bars[-limit:],
            "actions": actions, "position": position, "cash": cash,
            "gate": gate, "cancellations": cancellations}


def render(view):
    payload = json.dumps(view, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    payload = payload.replace("<", "\\u003c").replace("&", "\\u0026")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*VIEW_DATA*/", payload)


def export(directory, output, profile="base"):
    """Validate prepared bindings, then create a new export outside that directory."""
    if Path(output).is_symlink():
        raise ValueError("viewer_output_symlink")
    root, destination = Path(directory).resolve(), Path(output).resolve()
    if destination == root or root in destination.parents:
        raise ValueError("viewer_output_must_be_outside_prepared_directory")
    if destination.exists():
        raise FileExistsError("new viewer output directory required")
    checked = comparison.ComparisonReplay(directory, "EW_FULL_V1", profile)
    report_path = root / ("EW_FULL_V1-" + profile + ".json")
    if report_path.is_symlink() or report_path.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("viewer_report_file_bound")
    with report_path.open("rb") as file:
        raw = file.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("viewer_report_file_bound")
    account = comparison.legacy.c.daily._json(raw)
    if account["partition"] != checked.prepared["partition"] or account["profile"] != profile:
        raise ValueError("viewer_account_partition_profile")
    bars = comparison.legacy.c.daily._json(comparison.read(root / "derived-bars.json"))["bars"]
    sources = source_bindings()
    view = viewer_data(account, bars, checked.events)
    html = render(view).encode("utf-8")
    checked._check_binding()
    if hashlib.sha256(raw).hexdigest() != comparison.report_hash(report_path) or sources != source_bindings():
        raise ValueError("viewer_source_changed_during_export")
    manifest = {"version": VERSION, "kind": "saved_invented_report_view_not_replay_verification",
                "profile": profile, "partition": view["partition"], "viewer_sources": sources,
                "runtime_sources": checked.prepared["sources"], "prepared_sha256": checked.binding,
                "prepared_files": checked.prepared["files"], "report_sha256": hashlib.sha256(raw).hexdigest(),
                "html_sha256": hashlib.sha256(html).hexdigest(), "rows": len(view["rows"]),
                "market_cells_run": 0, "orders_available": False, "market_returns": None}
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "replay.html").write_bytes(html)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
