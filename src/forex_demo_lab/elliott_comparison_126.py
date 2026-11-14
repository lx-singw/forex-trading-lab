"""Five fixed hypotheses on shared invented quotes; descriptive reporting only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from . import elliott_execution_125 as ew

daily, bars, fills, runs, waves = ew.daily, ew.bars, ew.fills, ew.runs, ew.waves
VERSION = "FXDL_COMPARISON126_V1"
MODELS = (waves.CANDIDATE,) + daily.CANDIDATES
DEPENDENCIES = ew.DEPENDENCIES + (
    "src/forex_demo_lab/elliott_comparison_126.py", "src/forex_demo_lab/comparison_fixture_126.py",
    "scripts/elliott-comparison-126.py", "tests/test_elliott_comparison_126.py",
    "docs/ELLIOTT-COMPARISON-126-PLAN.md", "docs/ELLIOTT-COMPARISON-126-PROTOCOL.md",
)
COMMON_REASONS = {"no_observed_prefix", "missing_declared_endpoint", "invalid_endpoint_quote", "missing_required_session",
                  "incomplete_required_session", "no_execution_quotes", "no_available_feature"}
BASE_FILES = ("prefix-input.json", "prefix-frozen.json", "aggregation.json",
              "wave-input.json", "wave-frozen.json", "wave-report.json")


def rules():
    return {"schema": VERSION, "models": list(MODELS), "shared_cash_control": True,
            "common_quotes": "original_source_receipt_bid_ask_and_latest_published_session",
            "fresh_account_per_model_profile_partition_usd": 10000,
            "legacy_execution": fills.rules(), "elliott_execution": ew.rules(),
            "reporting": runs.rules(), "model_failure_scope": "individual_account",
            "history_endpoint_failure_scope": "all_accounts_in_partition",
            "strategy_selected": False, "capital_summed_as_portfolio": False,
            "orders_available": False, "real_money_execution_available": False}


def source_bindings():
    return {n: ew._hash(daily.ROOT / n) for n in DEPENDENCIES}


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "stream", "partitions"}, "comparison_fields")
    if value["format"] != VERSION or value["kind"] != "invented_strategy_comparison":
        raise ValueError("invented_comparison_required")
    runs.validate_fixture({**value, "format": runs.VERSION, "kind": "invented_partitioned_daily_run"})
    return value


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_COMPARISON126_FREEZE_V1", "kind": "invented_comparison_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                "case": value["case"], "partitions": value["partitions"], "sources": sources,
                "rules": rules(), "profiles": fills.risk.profiles(), "orders_available": False,
                "market_data_qualified": False, "untouched_validation_confirmed": False}
    daily.write_new(output, manifest)
    return manifest


def _load(path, manifest_path):
    raw, mraw = daily._read(path), daily._read(manifest_path)
    value, manifest = daily._json(raw), daily._json(mraw)
    daily._fields(manifest, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "partitions",
                            "sources", "rules", "profiles", "orders_available", "market_data_qualified",
                            "untouched_validation_confirmed"}, "comparison_manifest_fields")
    if (manifest["format"] != "FXDL_COMPARISON126_FREEZE_V1" or manifest["kind"] != "invented_comparison_freeze"
            or manifest["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
            or daily._canonical(manifest["sources"]) != daily._canonical(source_bindings())
            or daily._canonical(manifest["rules"]) != daily._canonical(rules())
            or daily._canonical(manifest["profiles"]) != daily._canonical(fills.risk.profiles())
            or any(manifest[k] is not False for k in ("orders_available", "market_data_qualified", "untouched_validation_confirmed"))):
        raise ValueError("comparison_freeze_binding")
    waves._utc_freeze(manifest["frozen_at_utc"])
    validate_fixture(value)
    if manifest["case"] != value["case"] or daily._canonical(manifest["partitions"]) != daily._canonical(value["partitions"]):
        raise ValueError("comparison_freeze_partitions")
    return value, hashlib.sha256(raw).hexdigest(), hashlib.sha256(mraw).hexdigest()


def _artifact(path, expected, write):
    if write:
        daily.write_new(path, expected)
    elif daily._canonical(daily._json(daily._read(path))) != daily._canonical(expected):
        raise ValueError("comparison_artifact_changed")


def _prepare(value, part, directory, write):
    if write:
        compiled = ew.prepare_partition(value, part, directory)
    else:
        prefix = ew._prefix(value, part)
        _artifact(directory / "prefix-input.json", prefix, False)
        replay = bars.Replay(directory / "prefix-input.json", directory / "prefix-frozen.json")
        aggregate = replay.run()
        _artifact(directory / "aggregation.json", aggregate, False)
        runs.Coordinator._endpoint(prefix, part)
        features = replay.features()
        wave_input = {"format": waves.VERSION, "kind": "invented_wave_detector", "clock": "invented_utc_milliseconds",
                      "symbol": "EURUSD", "case": prefix["case"], "daily": features}
        _artifact(directory / "wave-input.json", wave_input, False)
        observed = waves.Replay(directory / "wave-input.json", directory / "wave-frozen.json").run()
        _artifact(directory / "wave-report.json", observed, False)
        derivation = {n: ew._hash(directory / n) for n in BASE_FILES}
        compiled = ew._compile(prefix, aggregate, observed, part, derivation)
        _artifact(directory / "compiled-input.json", compiled, False)
    replay = bars.Replay(directory / "prefix-input.json", directory / "prefix-frozen.json")
    _artifact(directory / "aggregation.json", replay.run(), False)
    legacy = bars.compile_fills(replay)
    _artifact(directory / "legacy-input.json", legacy, write)
    if write:
        fills.freeze_fixture(directory / "legacy-input.json", directory / "legacy-frozen.json")
    # Both adapters must see identical quotes and publication identities, including bad-quality quotes.
    def quotes(events):
        return [{k: q[k] for k in ("sequence", "source_msc", "receipt_msc", "bid", "ask")} for q in events]
    if (quotes(compiled["events"]) != quotes(legacy["events"])
            or any(a["feature"]["session_id"] != b["target_session_id"]
                   or a["feature"]["available_msc"] != b["feature_decision_msc"]
                   for a, b in zip(compiled["events"], legacy["events"]))):
        raise ValueError("comparison_common_quotes")
    return compiled, legacy, daily._digest(quotes(compiled["events"]))


def _cell(part, profile, candidate, reason=None, report=None, statistics=None):
    return {"partition": deepcopy(part), "profile": profile, "candidate": candidate,
            "execution_adapter": "elliott_execution_125" if candidate == waves.CANDIDATE else "daily_fills_120",
            "status": "unavailable" if reason else "invented_descriptive_only", "reason": reason,
            "account_report": report, "statistics": statistics, "market_assessment": "unavailable_invented_unqualified",
            "orders_available": False, "real_money_execution_available": False}


def _calculate(value, part, directory, write):
    reason, shared = None, None
    try:
        if not any(m["receipt_msc"] < part["end_msc"] for m in value["stream"]["messages"]):
            raise ValueError("no_observed_prefix")
        compiled, legacy, shared = _prepare(value, part, directory, write)
    except ValueError as exc:
        if str(exc) not in COMMON_REASONS:
            raise
        reason = str(exc)
    cells = []
    for profile in fills.risk.profiles():
        for candidate in MODELS:
            if reason:
                cells.append(_cell(part, profile, candidate, reason))
                continue
            is_ew = candidate == waves.CANDIDATE
            cls = ew.Account if is_ew else fills.Replay
            stem = "compiled" if is_ew else "legacy"
            try:
                report = cls(directory / (stem + "-input.json"), directory / (stem + "-frozen.json"), profile, candidate).run()
            except ValueError as exc:
                if str(exc) != "nonpositive_exit_price":
                    raise
                cells.append(_cell(part, profile, candidate, str(exc)))
            else:
                statistics = runs._statistics(compiled if is_ew else legacy, report, part)
                cells.append(_cell(part, profile, candidate, report=report, statistics=statistics))
    _artifact(directory / "comparisons.json", {"kind": "invented_five_candidate_accounts", "cells": cells}, write)
    count = sum(c["statistics"] is not None for c in cells)
    record = {"partition": deepcopy(part), "common_reason": reason, "shared_quotes_sha256": shared,
              "planned_accounts": 10, "computed_accounts": count, "unavailable_accounts": 10 - count,
              "cells": cells, "status": "unavailable" if not count else "partially_available" if count != 10 else "invented_descriptive_only",
              "artifacts": {p.name: ew._hash(p) for p in sorted(directory.iterdir()) if p.name != "partition-report.json"},
              "capital_summed_as_portfolio": False, "strategy_selected": False, "orders_available": False}
    _artifact(directory / "partition-report.json", record, write)
    return record


def render_report(report):
    lines = ["# Five fixed strategies — invented comparison126", "",
             "Each row is a separate fresh USD10,000 account. Prices, clocks and calendars are invented.",
             "These paths test software behavior; market profitability and strategy selection remain unavailable.",
             "Net includes commissions and financing. Spread/slippage memos are already embedded in prices.",
             "Monthly/quarterly equity windows are observed sparse marks, not certified calendar closes.", "",
             "| Period | Costs | Candidate | Net USD | Gross USD | Fees USD | Financing USD | Max DD | Closed trades | Exposure fraction | Largest loss USD | Status/reason |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for p in report["partitions"]:
        for c in p["cells"]:
            s = c["statistics"]
            metrics = [s[k] for k in ("toy_net_usd", "gross_usd", "commissions_usd", "financing_usd", "max_drawdown", "trades", "exposure_fraction", "largest_loss_usd")] if s else ["unavailable"] * 8
            fields = [c["partition"]["name"], c["profile"], c["candidate"], *metrics, c["reason"] or "invented_descriptive_only"]
            lines.append("| " + " | ".join(map(str, fields)) + " |")
    lines += ["", "Full account ledgers, turnover, embedded-cost memos, estimate breaches and observed equity windows are in run-report.json.",
              "No accounts or capitals are combined. The fixed mixture is inherited; no new mixture, parameter search or winner ranking is performed.",
              "The later period is chronological invented data, not genuinely untouched market validation.",
              "Stop orders and entry pauses are not guaranteed maximum losses. No broker account lookup or order API exists here.", ""]
    return "\n".join(lines)


def _run(path, manifest_path, root, write):
    value, input_sha, manifest_sha = _load(path, manifest_path)
    root = Path(root)
    if write:
        root.mkdir()
    elif root.is_symlink() or not root.is_dir():
        raise ValueError("comparison_output_root")
    binding = {"kind": "invented_comparison_output_binding", "fixture_sha256": input_sha,
               "manifest_sha256": manifest_sha, "orders_available": False}
    _artifact(root / "run-binding.json", binding, write)
    records = []
    for part in value["partitions"]:
        directory = root / part["name"]
        if write:
            directory.mkdir()
        elif directory.is_symlink() or not directory.is_dir():
            raise ValueError("comparison_output_root")
        records.append(_calculate(value, part, directory, write))
    report = {"format": "FXDL_COMPARISON126_REPORT_V1", "kind": "invented_shared_quote_comparison",
              "case": value["case"], "fixture_sha256": input_sha, "manifest_sha256": manifest_sha,
              "models": list(MODELS), "partitions": records, "planned_accounts": 20,
              "computed_accounts": sum(r["computed_accounts"] for r in records),
              "capital_summed_as_portfolio": False, "strategy_selected": False, "market_cells_run": 0,
              "market_data_qualified": False, "untouched_validation_confirmed": False,
              "paper_evaluation_available": False, "orders_available": False, "real_money_execution_available": False}
    _artifact(root / "run-report.json", report, write)
    human = render_report(report)
    if write:
        with (root / "REPORT.md").open("x", encoding="utf-8", newline="\n") as output:
            output.write(human)
    elif (root / "REPORT.md").read_text() != human:
        raise ValueError("comparison_readable_report_changed")
    return report


def evaluate_fixture(path, manifest_path, output_root):
    return _run(path, manifest_path, output_root, True)


def verify_fixture(path, manifest_path, output_root):
    """Re-derive both histories, ledgers and statistics without writing any output."""
    return _run(path, manifest_path, output_root, False)
