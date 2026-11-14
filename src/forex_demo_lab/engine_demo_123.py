"""One fixed offline invented demonstration; checked recovery and readable evidence."""
import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import re

from . import daily_features_118 as daily
from . import daily_runs_122 as runs
from .daily_runs_fixture_122 import CASES, fixture

VERSION = "FXDL_ENGINEDEMO123_V1"
EVIDENCE = (
    "AGENTS.md", "docs/STRATEGY-EVIDENCE-117-PROTOCOL.md",
    "docs/DAILY-STRATEGY-118-RESULTS.md", "docs/DAILY-RISK-119-RESULTS.md",
    "docs/DAILY-FILLS-120-RESULTS.md", "docs/DAILY-BARS-121-RESULTS.md",
    "docs/DAILY-RUNS-122-RESULTS.md", "docs/SOURCE-DECISION-105-RESULTS.md",
    "docs/FORWARD-CAPTURE-112-RESULTS.md",
)
LOCAL = (
    "daily_features_118", "daily_fixture_118", "daily_risk_119", "model",
    "daily_fills_120", "daily_bars_121", "daily_bars_fixture_121",
    "daily_runs_122", "daily_runs_fixture_122", "engine_demo_123",
)
RUNTIME = tuple(f"src/forex_demo_lab/{n}.py" for n in LOCAL) + (
    "src/forex_demo_lab/__init__.py", "scripts/engine-demo-123.py",
)
STDLIB = {"argparse", "ast", "calendar", "copy", "dataclasses", "datetime",
          "decimal", "hashlib", "json", "math", "pathlib", "re", "statistics", "sys", "zoneinfo"}
DEPENDENCIES = tuple(dict.fromkeys(runs.DEPENDENCIES + RUNTIME + EVIDENCE + (
    "tests/test_engine_demo_123.py", "config/engine-readiness-123.json",
    "docs/ENGINE-READINESS-123-PROTOCOL.md", "docs/ENGINE-READINESS-123-PLAN.md",
)))
FLAGS = ("market_data_qualified", "paper_evaluation_available", "orders_available",
         "real_money_execution_available", "strategy_selected", "untouched_validation_confirmed")


def _sha(path):
    return hashlib.sha256(daily._read(path)).hexdigest()


def source_bindings():
    return {n: _sha(daily.ROOT / n) for n in DEPENDENCIES}


def _review_python(raw):
    """Narrow dependency review of known code, not a general Python sandbox."""
    tree = ast.parse(raw)
    imports, local = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in STDLIB:
                    raise ValueError("unexpected_runtime_import")
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1:
                names = [node.module] if node.module else [a.name for a in node.names]
                if any(n not in LOCAL for n in names):
                    raise ValueError("unexpected_runtime_import")
                local.update(names)
            elif node.level == 0 and node.module in {f"forex_demo_lab.{n}" for n in LOCAL}:
                local.add(node.module.split(".")[-1])
            elif node.level == 0 and node.module == "forex_demo_lab" and all(a.name in LOCAL for a in node.names):
                local.update(a.name for a in node.names)
            elif node.level == 0 and node.module in STDLIB:
                imports.add(node.module)
            else:
                raise ValueError("unexpected_runtime_import")
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
            if name in {"eval", "exec", "compile", "__import__", "order_send", "order_check", "initialize", "login"}:
                raise ValueError("unexpected_runtime_call")
    return sorted(imports), sorted(local)


def capability_audit():
    graph, stdlib = {}, set()
    for n in RUNTIME:
        imports, local = _review_python(daily._read(daily.ROOT / n))
        graph[n] = local
        stdlib.update(imports)
    reachable, pending = set(), ["engine_demo_123"]
    while pending:
        n = pending.pop()
        if n not in reachable:
            reachable.add(n)
            pending.extend(graph[f"src/forex_demo_lab/{n}.py"])
    if reachable != set(LOCAL):
        raise ValueError("runtime_graph_changed")
    return {"scope": "reviewed_fixed_offline_dependency_graph_not_security_sandbox",
            "runtime_bindings": {n: _sha(daily.ROOT / n) for n in RUNTIME},
            "local_import_graph": graph, "standard_library_imports": sorted(stdlib),
            "network_process_broker_imports": [], "dynamic_python_calls": [],
            "actual_order_api_present": False}


def readiness():
    value = daily._json(daily._read(daily.ROOT / "config/engine-readiness-123.json"))
    daily._fields(value, {"format", "as_of", "scope", "market_cells_planned", "market_cells_assigned",
        "market_cells_run", "market_data_qualified", "paper_evaluation_available", "actual_account_type_lookup_performed",
        "orders_available", "real_money_execution_available", "components", "market_requirements"}, "readiness_fields")
    if (value["format"] != "FXDL_ENGINE_READINESS123_V1" or value["as_of"] != "2026-10-13"
            or value["scope"] != "local_invented_software_evidence"):
        raise ValueError("readiness_scope")
    for k, n in (("market_cells_planned", 16), ("market_cells_assigned", 0), ("market_cells_run", 0)):
        if type(value[k]) is not int or value[k] != n:
            raise ValueError("market_cells_unavailable")
    for k in ("market_data_qualified", "paper_evaluation_available", "actual_account_type_lookup_performed",
              "orders_available", "real_money_execution_available"):
        if value[k] is not False:
            raise ValueError("readiness_admission_unavailable")
    for group, count in (("components", 5), ("market_requirements", 9)):
        rows = value[group]
        if type(rows) is not list or len(rows) != count:
            raise ValueError("readiness_inventory")
        for row in rows:
            daily._fields(row, {"name", "status", "evidence", "finding"}, "readiness_row")
            if any(type(v) is not str for v in row.values()) or row["evidence"] not in EVIDENCE:
                raise ValueError("readiness_evidence")
            allowed = {"implemented_invented_only"} if group == "components" else {"unqualified", "insufficient", "unavailable"}
            if row["status"] not in allowed:
                raise ValueError("readiness_admission_unavailable")
    return value


def _root(path):
    supplied = Path(path)
    if not supplied.is_absolute():
        supplied = daily.ROOT / supplied
    if any(p.is_symlink() for p in (supplied, *supplied.parents)):
        raise ValueError("package_symlink")
    root = supplied.resolve()
    if root == daily.ROOT / "data" or not root.is_relative_to(daily.ROOT / "data"):
        raise ValueError("package_output_under_repository_data_required")
    return root


def _files(directory):
    files = {}
    for p in sorted(directory.rglob("*")):
        if p.is_symlink():
            raise ValueError("package_symlink")
        if p.is_file():
            files[p.relative_to(directory).as_posix()] = _sha(p)
        elif not p.is_dir():
            raise ValueError("package_file_type")
        if len(files) > 256:
            raise ValueError("package_file_limit")
    return files


def _write_or_match(path, value, text=False):
    if path.exists():
        if text:
            same = daily._read(path) == value.encode("utf-8")
        else:
            same = daily._canonical(daily._json(daily._read(path))) == daily._canonical(value)
        if not same:
            raise ValueError("package_artifact_conflict")
    elif text:
        with path.open("x", encoding="utf-8", newline="\n") as f:
            f.write(value)
    else:
        daily.write_new(path, value)


def _case_files(directory):
    allowed = {"input.json", "frozen.json", "run", *(f"checkpoint-{i}.json" for i in range(3))}
    if any(p.name not in allowed or p.is_symlink() for p in directory.iterdir()):
        raise ValueError("package_unexpected_artifact")
    run = directory / "run"
    if run.exists():
        for p in run.iterdir():
            if p.name in {"run-binding.json", "run-report.json"} and p.is_file():
                continue
            if not p.is_dir() or not re.fullmatch(r"(development|later_validation)-attempt[0-9]{2}", p.name):
                raise ValueError("package_unexpected_artifact")
            names = {"attempt-binding.json", "prefix-input.json", "prefix-frozen.json", "aggregation.json",
                     "fills-input.json", "fills-frozen.json", "fills-report.json", "statistics.json", "partition-report.json"}
            if any(q.name not in names or not q.is_file() for q in p.iterdir()):
                raise ValueError("package_unexpected_artifact")
    return _files(directory)


def _manifest(root):
    value = daily._json(daily._read(root / "package-frozen.json"))
    daily._fields(value, {"format", "kind", "cases", "sources", "inputs", "readiness", "capabilities",
                         "orders_available", "real_money_execution_available"}, "package_manifest_fields")
    if (value["format"] != VERSION or value["kind"] != "fixed_invented_demo_package"
            or daily._canonical(value["cases"]) != daily._canonical(list(CASES))
            or daily._canonical(value["sources"]) != daily._canonical(source_bindings())
            or daily._canonical(value["readiness"]) != daily._canonical(readiness())
            or daily._canonical(value["capabilities"]) != daily._canonical(capability_audit())
            or value["orders_available"] is not False or value["real_money_execution_available"] is not False):
        raise ValueError("package_freeze_binding")
    daily._fields(value["inputs"], set(CASES), "package_inputs")
    for case in CASES:
        d = root / case
        _case_files(d)
        expected = {"input_sha256": _sha(d / "input.json"), "manifest_sha256": _sha(d / "frozen.json")}
        if daily._canonical(value["inputs"][case]) != daily._canonical(expected):
            raise ValueError("package_input_binding")
        if daily._canonical(daily._json(daily._read(d / "input.json"))) != daily._canonical(fixture(case)):
            raise ValueError("fixed_invented_input_changed")
        runs.Coordinator(d / "input.json", d / "frozen.json")
    return value


def _checkpoint(root, manifest_sha, records, previous):
    payload = {"schema": "engine_demo123_checkpoint_v1", "manifest_sha256": manifest_sha,
               "cursor": len(records), "records": records, "previous_checkpoint_sha256": previous}
    path = root / f"progress-{len(records):03d}.json"
    daily.write_new(path, {"payload": payload, "sha256": daily._digest(payload)})
    return _sha(path)


def _progress(root, manifest_sha):
    paths = sorted(root.glob("progress-*.json"))
    if not paths or len(paths) > 7:
        raise ValueError("package_checkpoint_chain")
    prior, records = None, []
    for cursor, path in enumerate(paths):
        if path.name != f"progress-{cursor:03d}.json":
            raise ValueError("package_checkpoint_chain")
        value = daily._json(daily._read(path))
        daily._fields(value, {"payload", "sha256"}, "package_checkpoint_envelope")
        p = value["payload"]
        daily._fields(p, {"schema", "manifest_sha256", "cursor", "records", "previous_checkpoint_sha256"}, "package_checkpoint_fields")
        if (p["schema"] != "engine_demo123_checkpoint_v1" or p["manifest_sha256"] != manifest_sha
                or type(p["cursor"]) is not int or p["cursor"] != cursor or p["previous_checkpoint_sha256"] != prior
                or value["sha256"] != daily._digest(p) or type(p["records"]) is not list
                or len(p["records"]) != cursor or daily._canonical(p["records"][:cursor-1 if cursor else 0]) != daily._canonical(records)):
            raise ValueError("package_checkpoint_chain")
        for i, record in enumerate(p["records"]):
            daily._fields(record, {"case", "files"}, "package_checkpoint_record")
            if record["case"] != CASES[i] or daily._canonical(record["files"]) != daily._canonical(_case_files(root / CASES[i])):
                raise ValueError("package_completed_artifact_binding")
        records, prior = p["records"], _sha(path)
    return records, prior


def _case_restore(root, case):
    d = root / case
    paths = sorted(d.glob("checkpoint-*.json"))
    if not paths or len(paths) > 3 or [p.name for p in paths] != [f"checkpoint-{i}.json" for i in range(len(paths))]:
        raise ValueError("case_checkpoint_chain")
    result = runs.Coordinator.restore(d / "input.json", d / "frozen.json", paths[-1].read_text(), d / "run")
    for i, p in enumerate(paths):
        cp = daily._json(daily._read(p))
        expected = daily._json(result.checkpoint())["payload"]
        expected["cursor"] = i
        expected["state"] = {"cursor": i, "partitions": result.state["partitions"][:i]}
        if daily._canonical(cp) != daily._canonical({"payload": expected, "sha256": daily._digest(expected)}):
            raise ValueError("case_checkpoint_chain")
    return result


def _check_report(report, case):
    if (report["kind"] != "invented_chronological_run_report" or report["case"] != case
            or report["market_cells_run"] != 0 or report["planned_toy_comparisons"] != 16
            or report["capital_summed_as_portfolio"] is not False or any(report[k] is not False for k in FLAGS)):
        raise ValueError("package_report_scope")
    for part in report["partitions"]:
        if part["status"] == "unavailable":
            if part["statistics"] != [] or part["returns"] is not None or not part["reason"] or part["computed_comparisons"] != 0:
                raise ValueError("unavailable_has_no_returns")
        elif part["status"] == "invented_descriptive_only":
            pairs = [(s["profile"], s["candidate"]) for s in part["statistics"]]
            if pairs != [(p, c) for p in runs.fills.risk.profiles() for c in daily.CANDIDATES]:
                raise ValueError("package_account_set")
            for s in part["statistics"]:
                if Decimal(s["initial_cash_usd"]) != 10000 or any(s[k] is not False for k in FLAGS if k not in {"paper_evaluation_available", "market_data_qualified"}):
                    raise ValueError("package_account_scope")
                if s["market_assessment"] != "unavailable_invented_unqualified" or s["qualified_monthly_marks"] != 0:
                    raise ValueError("package_account_scope")
        else:
            raise ValueError("package_report_status")


def _overview(reports, manifest_sha, inventory):
    if type(reports) is not list or len(reports) != len(CASES):
        raise ValueError("package_case_count")
    cells = []
    for case, report in zip(CASES, reports):
        _check_report(report, case)
        for part in report["partitions"]:
            by_pair = {(s["profile"], s["candidate"]): s for s in part["statistics"]}
            for profile in runs.fills.risk.profiles():
                for candidate in daily.CANDIDATES:
                    cells.append({"case": case, "partition": part["partition"]["name"], "profile": profile,
                        "candidate": candidate, "status": part["status"], "reason": part["reason"],
                        "detail_path": f"{case}/run/{part['attempt_directory']}/partition-report.json",
                        "statistics": deepcopy(by_pair.get((profile, candidate)))})
    if len(cells) != 96:
        raise ValueError("package_cell_count")
    return {"format": VERSION, "kind": "invented_demo_overview", "package_manifest_sha256": manifest_sha,
            "planned_toy_cells": len(cells), "available_accounts": sum(c["statistics"] is not None for c in cells),
            "unavailable_cells": sum(c["statistics"] is None for c in cells), "cells": cells,
            "hypothetical_profiles": runs.fills.risk.profiles(), "readiness": deepcopy(inventory),
            "fresh_cash_per_account_usd": "10000", "capital_summed_as_portfolio": False,
            "profits_positions_pause_carried_between_partitions": False,
            "market_cells_run": 0, **{k: False for k in FLAGS}}


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _money(value):
    return "—" if value is None else format(Decimal(value), ".2f")


def render(overview, doc_prefix):
    text = ["# Forex lab — local invented demo", "",
        "**Software demonstration only. Market testing, forward paper evaluation and all orders are unavailable.**", "",
        "All prices, UTC labels and daily schedules are invented, restricted to2000–2003. "
        "Each account starts separately withUSD10,000. Later periods carry no funded positions or profits. "
        "The later label does not establish untouched market validation. Do not add accounts as a portfolio.", "",
        f"{overview['planned_toy_cells']} planned toy cells: {overview['available_accounts']} computed accounts and "
        f"{overview['unavailable_cells']} unavailable cells. Unavailable metrics remain null, never zero. "
        "All computed samples are insufficient for the fixed market research requirements.", "",
        "Prices deliberately exercise targets and adverse gaps. Positive amounts prove arithmetic, not an edge. "
        "Stops and daily pauses cannot guarantee a maximum loss.", "", "## Hypothetical costs", "",
        "Base: $7/lot round-turn commission,0.2pip slippage per fill, long/short rollover debits$3/$1.50 per lot. "
        "Adverse: $10,0.5pip,$4.50/$2.25, with a1.2pip spread floor. Both use100,000 units/lot,30:1 leverage, "
        "0.01 minimum/step,1 maximum lot,0.25% maximum entry risk and1% daily entry pause. "
        "These are assumptions, not qualified broker terms.", "",
        "Gross fill P&L already embeds bid/ask and modeled slippage; net=gross−commissions+financing. "
        "Spread/slippage memos in the linked exact statistics are not additional debits. Target exits have "
        "no separately observed spread decomposition. Display rounds to cents; JSON preserves exact amounts.", "",
        "## Every fixed comparison", "",
        "Sample limits: under24 calendar months per period; active candidates under50 closed trades; "
        "under24 observed monthly marks. Cash is exempt only from the trade-count minimum. "
        "Sparse monthly/quarterly observation windows are not certified calendar-close market returns.", ""]
    for case in CASES:
        text += [f"### {_cell(case)}", "", f"[Run and artifact bindings]({case}/run/run-report.json) · "
                 f"[Final checked state]({case}/checkpoint-2.json)", "",
                 "| Period | Candidate | Cost | Status / reason | Trades | Gross USD | Commission USD | Financing USD | Net USD | Drawdown % |",
                 "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for c in overview["cells"]:
            if c["case"] != case:
                continue
            s = c["statistics"]
            status = "insufficient invented sample" if s else "unavailable: " + c["reason"]
            fields = [c["partition"], c["candidate"], c["profile"], f"[{_cell(status)}]({c['detail_path']})",
                str(s["trades"]) if s else "—", *[_money(s[k]) if s else "—" for k in
                ("gross_usd", "commissions_usd", "financing_usd", "toy_net_usd")],
                _money(Decimal(s["max_drawdown"]) * 100) if s else "—"]
            text.append("| " + " | ".join(fields) + " |")
        text.append("")
        for name in runs.NAMES:
            c = next(c for c in overview["cells"] if c["case"] == case and c["partition"] == name)
            attempt = str(Path(c["detail_path"]).parent)
            if c["statistics"] is not None:
                text.append(f"{name}: [exact statistics, cost memos and sample reasons]({attempt}/statistics.json) · "
                    f"[full fill/financing ledger]({attempt}/fills-report.json) · [aggregation]({attempt}/aggregation.json).")
            else:
                text.append(f"{name}: [{_cell(c['reason'])}]({c['detail_path']}); no return report.")
        text.append("")
    text += ["## Implemented software and missing market evidence", "",
             "This is an evidence inventory dated2026-10-13, not a fresh source qualification. "
             "The observed one-hour native pilot is retained as diagnostic evidence; its prices are not inputs here. "
             "Hashes preserve local consistency, not source authenticity.", "",
             "| Component / requirement | Evidence status | Finding |",
             "| --- | --- | --- |"]
    for group in ("components", "market_requirements"):
        for r in overview["readiness"][group]:
            text.append(f"| {_cell(r['name'])} | [{_cell(r['status'])}]({doc_prefix}{r['evidence']}) | {_cell(r['finding'])} |")
    text += ["", "All16 planned market cells remain unassigned/unrun. No strategy is selected. "
        "Synthetic DEMO mode checks are not an actual account lookup. This package contains no broker connection, "
        "order placement capability or real-money toggle.", "",
        "[Package source/input/readiness freeze](package-frozen.json) · [Full overview](overview.json) · "
        "[Completed package checkpoint](progress-006.json)", ""]
    return "\n".join(text)


def _completed_reports(root, records):
    reports = []
    for record in records:
        case = record["case"]
        restored = _case_restore(root, case)
        report = restored.report()
        saved = daily._json(daily._read(root / case / "run/run-report.json"))
        if daily._canonical(saved) != daily._canonical(report):
            raise ValueError("package_reconstructed_report")
        _check_report(report, case)
        reports.append(report)
    return reports


def _top_level(root, cursor):
    allowed = set(CASES) | {"package-frozen.json"} | {f"progress-{i:03d}.json" for i in range(cursor + 1)}
    if cursor == 6:
        allowed |= {"overview.json", "REPORT.md"}
    if any(p.name not in allowed or p.is_symlink() for p in root.iterdir()):
        raise ValueError("package_unexpected_artifact")


def create(path):
    root = _root(path)
    sources, audit, inventory = source_bindings(), capability_audit(), readiness()
    root.mkdir()
    inputs = {}
    for case in CASES:
        d = root / case
        d.mkdir()
        daily.write_new(d / "input.json", fixture(case))
        runs.freeze_fixture(d / "input.json", d / "frozen.json")
        inputs[case] = {"input_sha256": _sha(d / "input.json"), "manifest_sha256": _sha(d / "frozen.json")}
    if source_bindings() != sources:
        raise ValueError("package_sources_changed_during_freeze")
    daily.write_new(root / "package-frozen.json", {"format": VERSION, "kind": "fixed_invented_demo_package",
        "cases": list(CASES), "sources": sources, "inputs": inputs, "readiness": inventory, "capabilities": audit,
        "orders_available": False, "real_money_execution_available": False})
    _checkpoint(root, _sha(root / "package-frozen.json"), [], None)
    return resume(root)


def resume(path):
    root = _root(path)
    manifest = _manifest(root)
    manifest_sha = _sha(root / "package-frozen.json")
    records, previous = _progress(root, manifest_sha)
    _top_level(root, len(records))
    reports = _completed_reports(root, records)
    for case in CASES[len(records):]:
        d = root / case
        if (d / "run").exists():
            run = _case_restore(root, case)
        else:
            run = runs.Coordinator(d / "input.json", d / "frozen.json")
            _write_or_match(d / "checkpoint-0.json", daily._json(run.checkpoint()))
        while run.state["cursor"] < 2:
            run.step(d / "run")
            _write_or_match(d / f"checkpoint-{run.state['cursor']}.json", daily._json(run.checkpoint()))
        report = run.report()
        _check_report(report, case)
        _write_or_match(d / "run/run-report.json", report)
        reports.append(report)
        records.append({"case": case, "files": _case_files(d)})
        previous = _checkpoint(root, manifest_sha, records, previous)
    overview = _overview(reports, manifest_sha, manifest["readiness"])
    prefix = "../" * len(root.relative_to(daily.ROOT).parts)
    _write_or_match(root / "overview.json", overview)
    _write_or_match(root / "REPORT.md", render(overview, prefix), text=True)
    return overview


def verify(path):
    root = _root(path)
    before = _files(root)  # Read-only consistency check around reconstruction.
    manifest = _manifest(root)
    records, _ = _progress(root, _sha(root / "package-frozen.json"))
    if len(records) != 6:
        raise ValueError("package_incomplete")
    _top_level(root, 6)
    reports = _completed_reports(root, records)
    overview = _overview(reports, _sha(root / "package-frozen.json"), manifest["readiness"])
    if daily._canonical(daily._json(daily._read(root / "overview.json"))) != daily._canonical(overview):
        raise ValueError("package_overview_changed")
    expected = render(overview, "../" * len(root.relative_to(daily.ROOT).parts))
    if daily._read(root / "REPORT.md") != expected.encode("utf-8"):
        raise ValueError("package_readable_report_changed")
    if _files(root) != before:
        raise ValueError("package_changed_during_verification")
    return {"verified": True, "read_only": True, "planned_toy_cells": 96,
            "available_accounts": overview["available_accounts"], "unavailable_cells": overview["unavailable_cells"],
            "market_cells_run": 0, "orders_available": False, "real_money_execution_available": False}
