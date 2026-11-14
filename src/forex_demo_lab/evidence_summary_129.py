"""Summarize pinned native diagnostics offline; never qualify data or trade."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from . import forward_capture_111 as quotes
from . import metadata_probe_127 as metadata
from . import cost_probe_128 as costs

SCHEMA = "evidence_summary129_manifest_v1"
IDS = ("quotes111", "metadata127", "costs128")
MAX_MANIFEST = 65536
MAX_TOTAL = quotes.MAX_BYTES + metadata.MAX_BYTES + costs.MAX_BYTES
SPECS = {
    "quotes111": (r"data/forward-capture-112/(Run111-[1-9][0-9]*-[0-9]+-[1-9][0-9]*)/(Segment111-[0-9]{3}\.txt)", quotes.MAX_FILE, 64),
    "metadata127": (r"data/metadata-probe-127-native/(Run127-[1-9][0-9]*-[0-9]+-[1-9][0-9]*)/(Metadata127\.txt)", metadata.MAX_BYTES, 1),
    "costs128": (r"data/cost-probe-128-native/(Run128-[1-9][0-9]*-[0-9]+-[1-9][0-9]*)/(Costs128\.txt)", costs.MAX_BYTES, 1),
}


def _keys(obj, expected):
    if type(obj) is not dict or set(obj) != set(expected):
        raise ValueError("evidence_fields")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("evidence_duplicate_key")
        result[key] = value
    return result


def _no_constant(value):
    raise ValueError("evidence_json_constant")


def _read(path, maximum, allow_empty=False):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("evidence_file")
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if (not data and not allow_empty) or len(data) > maximum:
        raise ValueError("evidence_size")
    return data


def load_manifest(path):
    data = _read(path, MAX_MANIFEST)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_no_constant)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("evidence_manifest_json") from None


def _label(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _clock_groups(result):
    groups = []
    for row in result["rows"]:
        if row["type"] == "C":
            raw = row["raw_clocks"]
            groups.append(dict(key=row["key"], sequence=row["sequence"], raw=raw,
                               server_minus_computer_gmt_seconds=raw["time_current"] - raw["time_gmt"],
                               estimated_server_minus_computer_gmt_seconds=raw["time_trade_server"] - raw["time_gmt"],
                               local_minus_computer_gmt_seconds=raw["time_local"] - raw["time_gmt"]))
    return groups


def build_summary(manifest, root):
    _keys(manifest, ("schema", "sources"))
    if manifest["schema"] != SCHEMA or type(manifest["sources"]) is not list or len(manifest["sources"]) != 3:
        raise ValueError("evidence_manifest")
    root = Path(root).resolve()
    seen, sources, parsed = set(), [], {}
    total = 0
    for position, source in enumerate(manifest["sources"]):
        _keys(source, ("id", "files"))
        key = source["id"]
        if key != IDS[position]:
            raise ValueError("evidence_source_order")
        pattern, bound, count_bound = SPECS[key]
        if type(source["files"]) is not list or not 1 <= len(source["files"]) <= count_bound:
            raise ValueError("evidence_file_count")
        bindings, loaded, run_name = [], [], None
        for index, entry in enumerate(source["files"], 1):
            _keys(entry, ("path", "sha256"))
            relative, digest = entry["path"], entry["sha256"]
            if type(relative) is not str or type(digest) is not str or not re.fullmatch("[0-9a-f]{64}", digest):
                raise ValueError("evidence_binding")
            match = re.fullmatch(pattern, relative)
            if match is None or relative in seen:
                raise ValueError("evidence_path")
            folder, filename = match.groups()
            if (run_name is not None and run_name != folder
                    or key == "quotes111" and filename != f"Segment111-{index:03d}.txt"):
                raise ValueError("evidence_run_order")
            run_name = folder
            candidate = root
            for part in relative.split("/"):
                candidate = candidate / part
                if candidate.is_symlink():
                    raise ValueError("evidence_symlink")
            data = _read(candidate, bound, allow_empty=key == "quotes111")
            total += len(data)
            if total > MAX_TOTAL:
                raise ValueError("evidence_total_size")
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError("evidence_hash_mismatch")
            seen.add(relative)
            bindings.append(dict(path=relative, sha256=digest, bytes=len(data)))
            loaded.append((filename, data))
        if key == "quotes111":
            result = quotes.inspect_segments(loaded)
            seconds = result["origin_gmt_seconds"]
        else:
            result = (metadata if key == "metadata127" else costs).inspect_bytes(loaded[0][1])
            seconds = int(loaded[0][1].split(b"\r\n", 1)[0].split(b"\t")[4])
        if str(seconds) != run_name.split("-")[1]:
            raise ValueError("evidence_run_origin")
        parsed[key] = result
        sources.append(dict(id=key, files=bindings, declared_kind=result["declared_kind"],
                            capture_status=result["capture_status"], stop_code=result["stop_code"],
                            nominal_computer_gmt_origin_label=_label(seconds),
                            nominal_computer_gmt_origin_seconds=seconds, integrity="format_and_hashes_validated",
                            producer_authenticated=False, observation_scope={
                                "quotes111": "polled_quote_prefix", "metadata127": "reported_metadata_at_capture",
                                "costs128": "reported_cost_terms_at_capture"}[key]))
    q, m, c = [parsed[k] for k in IDS]
    observed = q["observations"]
    spreads = [Decimal(r["ask_decimal"]) - Decimal(r["bid_decimal"]) for r in observed]
    offsets = [r["source_millis"] - r["receipt_gmt_seconds"][1] * 1000 for r in observed]
    window = None if not observed else dict(
        first_sequence=observed[0]["sequence"], last_sequence=observed[-1]["sequence"],
        first_receipt_nominal_gmt_label=_label(observed[0]["receipt_gmt_seconds"][0]),
        last_receipt_nominal_gmt_label=_label(observed[-1]["receipt_gmt_seconds"][2]),
        observed_receipt_span_us=observed[-1]["receipt_monotonic_us"][2] - observed[0]["receipt_monotonic_us"][0],
        last_guard_elapsed_from_origin_us=observed[-1]["receipt_monotonic_us"][2] - q["origin_monotonic_us"])
    quote_evidence = dict(source_id="quotes111", capture_status=q["capture_status"], stop_code=q["stop_code"],
                          attempts=q["attempts"], observations=q["observed"], segments=q["segments"],
                          pending_attempt=q["pending_attempt"] is not None, truncated_tail=q["truncated_final_segment"],
                          repeated_snapshots=q["repeated_snapshots"], source_backwards=q["source_backwards"],
                          equal_time_changed=q["equal_time_changed"], receipt_gaps=q["receipt_gaps"],
                          missing=q["missing"], invalid=q["invalid"], window=window,
                          spread_min_price_units=str(min(spreads)) if spreads else None,
                          spread_max_price_units=str(max(spreads)) if spreads else None,
                          raw_source_minus_nominal_receipt_ms_min=min(offsets) if offsets else None,
                          raw_source_minus_nominal_receipt_ms_max=max(offsets) if offsets else None,
                          complete_tick_delivery=False, source_age=None)
    properties = []
    for row in m["rows"]:
        if row["type"] in ("I", "D", "V"):
            properties.append(dict(key=row["key"], sequence=row["sequence"],
                                   status="reported" if row["query_succeeded"] else "query_failed",
                                   value=row["value"], error_code=row["error_code"],
                                   native_bits=row.get("native_bits")))
    margins = []
    for row in c["rows"]:
        if row["type"] == "M":
            margins.append(dict(side=row["key"], sequence=row["sequence"],
                                status="reported" if row["query_succeeded"] else "query_failed",
                                initial_rate=row["initial_rate"], maintenance_rate=row["maintenance_rate"],
                                error_code=row["error_code"], native_bits=row["native_bits"]))
    sessions = [dict(key=r["key"], sequence=r["sequence"], query_succeeded=r["query_succeeded"],
                     error_code=r["error_code"], raw_from_seconds=r["raw_from_seconds"],
                     raw_to_seconds=r["raw_to_seconds"]) for r in m["rows"] if r["type"] == "W"]
    commission_row = next((r for r in c["rows"] if r["type"] == "K"), None)
    gaps = [
        dict(key="producer_and_cross_run_identity", status="unverified", detail="Hashes do not authenticate producers or join account identities across runs."),
        dict(key="utc_and_quote_age", status="unverified", detail="Raw clock differences are preserved without timezone or freshness conversion."),
        dict(key="quote_delivery", status="not_established", detail="Latest-quote polling does not establish complete tick delivery or executable prices."),
        dict(key="cost_completeness", status="not_established", detail="Current reports do not establish historical fees, all charges, slippage or USD margin requirements."),
        dict(key="calendar_and_coverage", status="not_established", detail="A weekly template and a short quote prefix do not certify historical coverage or holidays."),
        dict(key="untouched_evaluation", status="not_established", detail="This summary performs no strategy evaluation or validation-period admission."),
    ]
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return dict(schema="evidence_summary129_v1", manifest_semantic_sha256=hashlib.sha256(canonical).hexdigest(),
                input_files=len(seen), input_bytes=total, sources=sources, quotes=quote_evidence,
                metadata=dict(source_id="metadata127", capture_status=m["capture_status"],
                              queries_attempted=m["queries_attempted"], queries_recorded=m["queries_recorded"],
                              pending_attempt=m["pending_attempt"], truncated_tail=m["truncated_tail"],
                              properties=properties, weekly_sessions=sessions,
                              weekly_template_truncated=m["weekly_template_truncated"],
                              clock_groups=_clock_groups(m),
                              latest_quote_reads=[r for r in m["rows"] if r["type"] == "T"]),
                costs=dict(source_id="costs128", capture_status=c["capture_status"],
                           queries_attempted=c["queries_attempted"], queries_recorded=c["queries_recorded"],
                           pending_attempt=c["pending_attempt"], pending_rule_payload=c["pending_rule_payload"],
                           truncated_tail=c["truncated_tail"], commission_state=c["commission_state"],
                           commission_query=commission_row, commission_rules=c["commission_rules"],
                           margin_factors=margins, clock_groups=_clock_groups(c)),
                evidence_gaps=gaps, model_assumptions_applied=[], financial_model_changed=False,
                cross_run_contract_authenticated=False, continuous_history_across_sources=False,
                input_integrity_verified=True, producer_authenticated=False, source_utc_certified=False,
                receipt_utc_certified=False, source_age=None, commission_cost_USD=None,
                margin_requirement_USD=None, slippage_terms=None, historical_cost_terms_certified=False,
                strategy_evaluated=False, profitability_established=False, market_data_qualified=False,
                paper_evaluation_available=False, orders_available=False, real_money_execution_available=False)


def render_markdown(report):
    lines = ["# Offline evidence summary129", "", "The three saved sources remain separate observations with their original time labels.",
             "No new market data is collected and no model assumptions are applied.", "",
             "| Source | Nominal computer-GMT origin | Capture outcome | Files |", "|---|---|---|---:|"]
    for source in report["sources"]:
        lines.append(f"| {source['id']} | {source['nominal_computer_gmt_origin_label']} | {source['capture_status']} | {len(source['files'])} |")
    q, m, c = report["quotes"], report["metadata"], report["costs"]
    lines += ["", "## Reported facts", "",
              f"Quote pilot: {q['observations']} snapshots; {q['repeated_snapshots']} adjacent repeats; stop code {q['stop_code']}.",
              f"Receipt gaps: {q['receipt_gaps']}; missing/invalid outcomes: {q['missing']}/{q['invalid']}; source reversals: {q['source_backwards']}.",
              "Latest-quote polls do not establish complete tick delivery. Metadata quote reads are kept separate from that pilot.",
              "", "| Metadata property | Query status | Raw reported value |", "|---|---|---|"]
    for row in m["properties"]:
        lines.append(f"| {row['key']} | {row['status']} | {row['value'] if row['value'] is not None else 'unknown'} |")
    lines += ["", f"Commission response: **{c['commission_state']}**. No dollar fee is inferred."]
    if c["commission_rules"]:
        lines += ["", "Rule modes and tier values below are raw reported fields, with no new semantics assigned.", "",
                  "| Rule | Currency | Range / charge / entry / direction / profit modes |", "|---:|---|---|"]
        for rule in c["commission_rules"]:
            modes = ' / '.join(str(rule[k]) for k in ('mode_range', 'mode_charge', 'mode_entry', 'mode_direction', 'mode_profit'))
            lines.append(f"| {rule['index']} | {rule['currency'] or 'empty'} | {modes} |")
        lines += ["", "| Rule / tier | Mode / volume type | Value | Minimum / maximum | Range from / to | Currency |",
                  "|---|---|---:|---|---|---|"]
        for rule in c["commission_rules"]:
            for tier in rule["tiers"]:
                lines.append(f"| {rule['index']} / {tier['index']} | {tier['mode']} / {tier['volume_type']} | {tier['value']} | {tier['min_value']} / {tier['max_value']} | {tier['range_from']} / {tier['range_to']} | {tier['currency'] or 'empty'} |")
    lines += ["", "| Margin side | Query status | Initial factor | Maintenance factor |", "|---|---|---:|---:|"]
    for row in c["margin_factors"]:
        lines.append(f"| {row['side']} | {row['status']} | {row['initial_rate'] if row['initial_rate'] is not None else 'unknown'} | {row['maintenance_rate'] if row['maintenance_rate'] is not None else 'unknown'} |")
    lines += ["", "These factors are not dollar margin requirements. The weekly template is not a historical calendar.",
              "", "| Clock source / group | Server minus computer GMT, seconds | Estimated server minus GMT | Local minus GMT |",
              "|---|---:|---:|---:|"]
    for source in (m, c):
        for group in source['clock_groups']:
            lines.append(f"| {source['source_id']} / {group['key']} | {group['server_minus_computer_gmt_seconds']} | {group['estimated_server_minus_computer_gmt_seconds']} | {group['local_minus_computer_gmt_seconds']} |")
    lines += ["", "These differences are arithmetic on raw labels, not certified UTC offsets or quote ages.",
              "", "## Unverified or missing evidence", "", "| Evidence | Status | Limit |", "|---|---|---|"]
    for gap in report["evidence_gaps"]:
        lines.append(f"| {gap['key']} | {gap['status']} | {gap['detail']} |")
    lines += ["", "## Provenance", "", "Original file hashes are retained below. Valid hashes do not authenticate their producer.", "",
              "| Source | Canonical file | SHA256 |", "|---|---|---|"]
    for source in report["sources"]:
        for file in source["files"]:
            lines.append(f"| {source['id']} | {file['path']} | {file['sha256']} |")
    lines += ["", "No clock offsets, cross-run identity joins, historical cost substitutions or strategy returns are computed.",
              "Market qualification, paper evaluation, orders and real-money execution remain unavailable.", ""]
    return "\n".join(lines)
