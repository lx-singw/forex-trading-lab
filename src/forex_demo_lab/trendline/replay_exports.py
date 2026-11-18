"""Readable and machine-readable exports of the saved receipt ledger."""
import csv
from datetime import datetime, timedelta, timezone
from html import escape
from io import StringIO
import json
import re


VERSION = "TRL_VIEWER_LEDGER_190_V1"
LEDGER_KINDS = {"SETUP", "CONTACT", "ADMISSION", "ACCOUNT", "PROTECTION", "END"}
COLUMNS = ("row_id", "receipt_at_ms", "receipt_order", "kind", "event", "status", "reason", "attempt_id",
           "setup_frame_id", "h4_index", "effective_at_ms", "decision_at_ms", "quote_source_at_ms",
           "quote_sequence", "direction", "lots", "price", "stop", "target", "fee_usd", "net_usd",
           "cash_usd", "equity_usd", "entries_paused")
SCOPE = ("data_level", "geometry_basis", "profile", "partition", "cost_profile", "as_of_ms")
UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def receipt_ledger(view):
    scope = {key: view[key] for key in SCOPE[:4]}
    scope.update(cost_profile=view["cost"], as_of_ms=view["groups"][-1]["at"])
    rows = []
    setup_for_attempt = {}
    for group in view["groups"]:
        for order, item in enumerate(group["items"], 1):
            kind, value = item["kind"], item["value"]
            if kind not in LEDGER_KINDS:
                continue
            event, trade, held = (value.get(key, {}) for key in ("event", "trade", "held"))
            account = event.get("account", value.get("account", {}))
            request, sizing = (value.get(key, {}) for key in ("request", "sizing"))
            liability = value.get("open_liability") or {}
            quote = value.get("quote", {})
            # The Level Q entry mark also carries the sequence of its quote.
            sequence = quote.get("sequence", event.get("mark", {}).get("sequence"))
            attempt = event.get("attempt_id") or value.get("attempt_id") or liability.get("attempt_id")
            if kind == "ADMISSION":
                attempt = attempt or value["id"]
                setup_for_attempt[attempt] = value["h4_frame_id"]
            frame = value.get("h4_frame_id") or setup_for_attempt.get(attempt)
            decision = value.get("decision_at", request.get("decision_at", {})).get("time")
            row = {"row_id": len(rows) + 1, "receipt_at_ms": group["at"], "receipt_order": order,
                   "kind": kind, "event": event.get("kind"), "status": value.get("status", value.get("state")),
                   "reason": value.get("reason") or trade.get("reason") or liability.get("reason"),
                   "attempt_id": attempt, "setup_frame_id": frame,
                   "h4_index": value.get("bar_index", value.get("h4_index", value.get("index"))),
                   "effective_at_ms": event.get("effective_at"), "decision_at_ms": decision,
                   "quote_source_at_ms": quote.get("source"), "quote_sequence": sequence,
                   "direction": value.get("direction") or held.get("direction") or request.get("direction") or trade.get("direction"),
                   "lots": event.get("lots") or sizing.get("lots") or trade.get("lots") or liability.get("lots"),
                   "price": event.get("price"), "stop": value.get("stop") or held.get("initial_stop") or request.get("stop") or liability.get("stop"),
                   "target": held.get("target") or liability.get("target"), "fee_usd": event.get("fee_usd"), "net_usd": trade.get("net_usd"),
                   "cash_usd": account.get("cash_usd"), "equity_usd": account.get("equity_usd"),
                   "entries_paused": account.get("entries_paused")}
            rows.append({**row, "evidence": value})
    return {"schema": VERSION, "kind": "invented_trendline_receipt_ledger", **scope,
            "orders_available": False, "rows": rows}


def _csv_cell(value):
    if type(value) is bool:
        return str(value).lower()
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        if not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
            return "'" + value
    return value


def csv_ledger(ledger):
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow((*SCOPE, *COLUMNS))
    scope = tuple(ledger[column] for column in SCOPE)
    for row in ledger["rows"]:
        writer.writerow(map(_csv_cell, (*scope, *(row[column] for column in COLUMNS))))
    return output.getvalue().encode("utf-8")


def _utc(epoch_ms):
    if epoch_ms is None:
        return None
    return (UNIX_EPOCH + timedelta(milliseconds=epoch_ms)).isoformat(" ", timespec="milliseconds").removesuffix("+00:00")


def _text(value):
    return "—" if value is None else escape(str(value))


def _table(title, headings, rows, empty):
    content = "<p>" + _text(empty) + "</p>"
    if rows:
        header = "".join(f'<th scope="col">{_text(value)}</th>' for value in headings)
        body = "".join("<tr>" + "".join(f"<td>{_text(value)}</td>" for value in row) + "</tr>" for row in rows)
        content = f'<div class="table" role="region" aria-label="{_text(title)}" tabindex="0"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'
    return f"<section><h2>{_text(title)}</h2>{content}</section>"


def render_report(ledger):
    """Summarize the same ordered ledger rows offered as JSON and CSV."""
    opened, trials, trades, no_trade = {}, [], [], []
    for row in ledger["rows"]:
        kind, event = row["kind"], row["event"]
        if event == "ENTRY_FILL":
            opened[row["attempt_id"]] = row
        elif event == "EXIT_FILL":
            entry = opened[row["attempt_id"]]
            trade = row["evidence"]["trade"]
            trades.append((row["direction"], row["lots"], _utc(entry["effective_at_ms"]), _utc(entry["receipt_at_ms"]),
                           entry["price"], _utc(row["effective_at_ms"]), _utc(row["receipt_at_ms"]), row["price"],
                           row["reason"], f'{trade["commission_usd"]} / {trade["financing_usd"]}', row["net_usd"], row["row_id"]))
        if kind == "ADMISSION":
            trials.append((_utc(row["receipt_at_ms"]), row["status"], row["reason"], row["direction"],
                           row["stop"], row["quote_sequence"], row["row_id"]))
        if ((kind == "SETUP" and row["reason"]) or (kind == "CONTACT" and row["reason"] != "CONTACT")):
            no_trade.append((_utc(row["receipt_at_ms"]), row["h4_index"], kind, row["reason"], row["row_id"]))
        for step in row["evidence"].get("dly_transitions", []):
            if step["reason"]:
                no_trade.append((_utc(row["receipt_at_ms"]), row["h4_index"], "DELAYED_SETUP", step["reason"], row["row_id"]))
    endpoint = ledger["rows"][-1]
    liability = endpoint["evidence"]["open_liability"]
    summary = [("Saved cutoff · UTC", _utc(ledger["as_of_ms"])), ("Final status", endpoint["status"]),
               ("Cash · USD", endpoint["cash_usd"]), ("Equity · USD", endpoint["equity_usd"]),
               ("Closed trades", len(trades))]
    if liability is not None:
        mark = liability["last_mark"]
        summary.extend((("Open liability", liability["reason"] or "Position held"),
                        ("Last mark · USD per EUR", mark["price"]), ("Mark received · UTC", _utc(mark["available_at"])),
                        ("Reported stop", liability["stop"]), ("Unpaid exit commission · USD", liability["unpaid_exit_commission_usd"])))
    facts = "".join(f"<div><dt>{_text(label)}</dt><dd>{_text(value)}</dd></div>" for label, value in summary)
    trade_table = _table("Closed trades", ("Side", "Lots", "Entry effective · UTC", "Entry received · UTC", "Entry price",
                                          "Exit effective · UTC", "Exit received · UTC", "Exit price", "Exit reason",
                                          "Commission / financing · USD", "Net · USD",
                                          "Ledger row"), trades, "No closed trades through the saved cutoff.")
    gate_table = _table("Entry gates", ("Received · UTC", "State", "Reason", "Side", "Requested stop", "Quote sequence", "Ledger row"),
                        trials, "No entry gate records through the saved cutoff.")
    reason_table = _table("Setup and bounce reasons", ("Received · UTC", "H4 index", "Kind", "Reason", "Ledger row"),
                          no_trade, "No setup or bounce rejection records through the saved cutoff.")
    level = _text(ledger["data_level"])
    scope = " · ".join(_text(ledger[key]) for key in ("geometry_basis", "profile", "partition", "cost_profile"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'">
<title>Saved trendline run report</title>
<style>
:root{{font:15px system-ui,sans-serif;color:#172338;background:#f5f7fa}}*{{box-sizing:border-box}}
body{{max-width:1340px;margin:auto;padding:clamp(16px,4vw,50px)}}h1{{margin:0;line-height:1.15}}h2{{font-size:1.15rem}}
p{{line-height:1.5}}a{{color:#17549c}}nav{{display:flex;flex-wrap:wrap;gap:14px}}section{{margin-top:26px}}
dl{{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px}}
dl div{{padding:13px;background:white;border:1px solid #d7dee9;border-radius:8px}}dt{{color:#435874}}dd{{margin:4px 0 0;font-weight:650}}
.table{{overflow:auto;border:1px solid #d7dee9;border-radius:8px}}table{{width:100%;background:white;border-collapse:collapse;font-size:.87rem}}
th,td{{text-align:left;padding:9px;border-bottom:1px solid #e0e6ee}}th{{background:#eaf0f7}}td{{font-variant-numeric:tabular-nums}}
</style></head><body>
<header><h1>Saved trendline run report</h1><p>Invented replay · Level {level} · {scope} costs</p>
<nav aria-label="Replay bundle"><a href="replay.html">Receipt replay</a>
<a href="ledger.json" target="_blank" rel="noopener" download>JSON ledger</a>
<a href="ledger.csv" target="_blank" rel="noopener" download>CSV ledger</a></nav></header>
<main><section><h2>Account at saved cutoff</h2><dl>{facts}</dl></section>
{trade_table}{gate_table}{reason_table}</main></body></html>
"""


def artifacts(view):
    ledger = receipt_ledger(view)
    return {"report.html": render_report(ledger).encode("utf-8"),
            "ledger.json": (json.dumps(ledger, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"),
            "ledger.csv": csv_ledger(ledger)}
