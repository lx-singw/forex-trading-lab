"""Invented chronological run control and descriptive ledger reports; no orders."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import calendar
import hashlib
import json
from pathlib import Path
import re

from . import daily_features_118 as daily
from . import daily_bars_121 as bars
from . import daily_fills_120 as fills

VERSION = "FXDL_DAILYRUNS122_V1"
NAMES = ("development", "later_validation")
DEPENDENCIES = bars.DEPENDENCIES + (
    "src/forex_demo_lab/daily_runs_122.py", "src/forex_demo_lab/daily_runs_fixture_122.py",
    "scripts/daily-runs-122.py", "tests/test_daily_runs_122.py",
    "docs/DAILY-RUNS-122-PROTOCOL.md", "docs/DAILY-RUNS-122-PLAN.md",
)
D, S = fills.D, fills.S


def rules():
    return {"schema": VERSION, "partition_names": list(NAMES), "fresh_cash_usd": 10000,
            "cutoff": "receipt_strictly_before_end", "bounds": "source_half_open",
            "endpoint": "declared_last_source_new_fresh_trading", "warmup_funded": False,
            "capital_positions_and_pause_carried": False, "precision": 50,
            "periods": "observed_month_and_quarter_windows_not_certified_closes",
            "exposure": "fill_to_fill_source_duration_over_declared_window",
            "market_months_minimum": 24, "active_closed_trades_minimum": 50, "monthly_marks_minimum": 24,
            "market_assessment": "unavailable_invented_unqualified", "orders_available": False}


def _partitions(value, stream):
    if type(value) is not list or len(value) != 2:
        raise ValueError("partition_count")
    low = stream["calendar"]["sessions"][0]["start_msc"]
    high = stream["calendar"]["sessions"][-1]["end_msc"]
    for i, part in enumerate(value):
        daily._fields(part, {"name", "start_msc", "end_msc", "endpoint_source_msc"}, "partition_fields")
        if type(part["name"]) is not str or part["name"] != NAMES[i]:
            raise ValueError("partition_order")
        for k in ("start_msc", "end_msc", "endpoint_source_msc"):
            daily._integer(part[k], low, high, "partition_time")
        if not part["start_msc"] <= part["endpoint_source_msc"] < part["end_msc"]:
            raise ValueError("partition_bounds")
        if i and part["start_msc"] < value[i - 1]["end_msc"]:
            raise ValueError("partition_overlap")


def validate_fixture(value):
    daily._fields(value, {"format", "kind", "clock", "symbol", "case", "stream", "partitions"}, "run_fixture_fields")
    if (value["format"] != VERSION or value["kind"] != "invented_partitioned_daily_run"
            or value["clock"] != "invented_utc_milliseconds" or value["symbol"] != "EURUSD"):
        raise ValueError("invented_daily_run_required")
    daily._name(value["case"], "run_fixture_case")
    bars.validate_fixture(value["stream"])
    if value["stream"]["execution_start_msc"] is not None:
        raise ValueError("unfunded_stream_required")
    if D(value["stream"]["initial_account"]["balance_usd"]) != D(10000):
        raise ValueError("fixed_fresh_capital_required")
    _partitions(value["partitions"], value["stream"])
    return value


def source_bindings():
    return {n: hashlib.sha256(daily._read(daily.ROOT / n)).hexdigest() for n in DEPENDENCIES}


def freeze_fixture(path, output):
    raw = daily._read(path)
    value = validate_fixture(daily._json(raw))
    sources = source_bindings()
    if sources["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
        raise ValueError("fixed_declaration_changed")
    manifest = {"format": "FXDL_DAILYRUNS122_FREEZE_V1", "kind": "invented_run_freeze",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                "case": value["case"], "partitions": value["partitions"], "sources": sources,
                "run_rules": rules(), "aggregation_rules": bars.rules(), "feature_rules": daily.rule_definitions(),
                "fill_rules": fills.rules(), "profiles": fills.risk.profiles(), "orders_available": False,
                "market_data_qualified": False, "untouched_validation_confirmed": False}
    daily.write_new(output, manifest)
    return manifest


def _hash(path):
    return hashlib.sha256(daily._read(path)).hexdigest()


def _month_add(instant, months):
    index = instant.year * 12 + instant.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    return instant.replace(year=year, month=month, day=min(instant.day, calendar.monthrange(year, month)[1]))


def _instant(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc)


def _periods(start, end, months):
    instant = _instant(start)
    month = instant.month if months == 1 else (instant.month - 1) // 3 * 3 + 1
    left = instant.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
    while int(left.timestamp() * 1000) < end:
        right = _month_add(left, months)
        yield left.strftime("%Y-%m") if months == 1 else f"{left.year}-Q{(left.month - 1) // 3 + 1}", int(left.timestamp() * 1000), int(right.timestamp() * 1000)
        left = right


def _statistics(compiled, report, part):
    """Private reporting of coordinator-derived, source-bound120 ledger state."""
    with localcontext() as ctx:
        ctx.prec = 50
        state, summary = report["final_state"], report["summary"]
        ledger, outcomes, events = state["ledger"], state["outcomes"], compiled["events"]
        initial = D(compiled["initial_account"]["balance_usd"])
        entries = {r["position_id"]: r for r in ledger if r["kind"] == "entry_fill"}
        exits = [r for r in ledger if r["kind"] == "exit_fill"]
        nets = [D(r["net_trade_usd"]) for r in exits]
        wins, losses = [v for v in nets if v > 0], [v for v in nets if v < 0]
        gross = sum((D(r["gross_usd"]) for r in exits), D(0))
        fees = sum((D(r["fee_usd"]) for r in ledger if "fee_usd" in r), D(0))
        financing = sum((D(r["amount_usd"]) for r in ledger if r["kind"] == "financing"), D(0))
        net = gross - fees + financing
        if abs(net - D(summary["toy_net_usd"])) > D("1e-35") or abs(sum(nets, D(0)) - net) > D("1e-35"):
            raise ValueError("statistics_cash_reconciliation")
        intervals = [(entries[r["position_id"]]["source_msc"], r["source_msc"]) for r in exits]
        exposure_ms = sum(b - a for a, b in intervals)
        flat, cursor = [], part["start_msc"]
        for a, b in intervals:
            if a < cursor or b < a:
                raise ValueError("statistics_position_overlap")
            if a > cursor:
                flat.append({"start_msc": cursor, "end_msc": a, "duration_msc": a - cursor})
            cursor = b
        if cursor < part["end_msc"]:
            flat.append({"start_msc": cursor, "end_msc": part["end_msc"], "duration_msc": part["end_msc"] - cursor})
        if exposure_ms + sum(v["duration_msc"] for v in flat) != part["end_msc"] - part["start_msc"]:
            raise ValueError("statistics_time_reconciliation")
        fills_rows = [r for r in ledger if r["kind"] in ("entry_fill", "exit_fill")]
        units = sum((D(r["lots"]) * 100000 for r in fills_rows), D(0))
        notional = sum((D(r["lots"]) * 100000 * D(r["price"]) for r in fills_rows), D(0))
        memo = {k: D(0) for k in ("entry_spread_usd", "entry_slippage_usd", "nonlimit_exit_spread_usd", "nonlimit_exit_slippage_usd")}
        profile = fills.risk.profiles()[report["profile"]]
        slip = D(profile["config"]["slippage_pips"]) * D(".0001")
        floor = D(profile["spread_floor_pips"]) * D(".0001")
        for row in fills_rows:
            event = events[row["sequence"]]
            spread = max(D(event["ask"]) - D(event["bid"]), floor)
            volume = D(row["lots"]) * 100000
            if row["kind"] == "entry_fill":
                memo["entry_spread_usd"] += spread / 2 * volume
                memo["entry_slippage_usd"] += slip * volume
            elif row["reason"] != "target":
                memo["nonlimit_exit_spread_usd"] += spread / 2 * volume
                memo["nonlimit_exit_slippage_usd"] += slip * volume
        marks = []
        for event, outcome in zip(events, outcomes):
            if outcome["execution_quote"]:
                equity = state["equity_usd"] if event is events[-1] else outcome["account"]["equity_usd"]
                marks.append((event["source_msc"], D(equity)))
        def periods(width):
            previous = initial
            records = []
            for name, a, b in _periods(part["start_msc"], part["end_msc"], width):
                observed = [(t, v) for t, v in marks if a <= t < b]
                rows = [r for r in ledger if a <= r["source_msc"] < b]
                change = sum((D(r["gross_usd"]) if r["kind"] == "exit_fill" else D(0) for r in rows), D(0))
                change -= sum((D(r["fee_usd"]) for r in rows if "fee_usd" in r), D(0))
                change += sum((D(r["amount_usd"]) for r in rows if r["kind"] == "financing"), D(0))
                closing = observed[-1][1] if observed else None
                ret = (closing - previous) / previous if closing is not None and previous is not None and previous > 0 else None
                records.append({"period": name, "kind": "observed_window_not_certified_calendar_close",
                    "start_msc": max(a, part["start_msc"]), "end_msc": min(b, part["end_msc"]),
                    "partial_calendar_period": part["start_msc"] > a or part["end_msc"] < b,
                    "status": "unobservable" if closing is None else "observed" if ret is not None else "observed_without_positive_anchor",
                    "opening_equity_usd": None if previous is None else S(previous),
                    "closing_equity_usd": None if closing is None else S(closing),
                    "observed_window_return": None if ret is None else S(ret),
                    "first_observation_msc": observed[0][0] if observed else None,
                    "last_observation_msc": observed[-1][0] if observed else None,
                    "ledger_cash_change_usd": S(change)})
                previous = closing
            if abs(sum((D(r["ledger_cash_change_usd"]) for r in records), D(0)) - net) > D("1e-35"):
                raise ValueError("statistics_period_reconciliation")
            return records
        monthly, quarterly = periods(1), periods(3)
        longest_loss = max((-v for v in nets), default=D(0))
        breaches = [{"position_id": r["position_id"], "loss_usd": S(max(D(0), -D(r["net_trade_usd"]))),
                     "entry_estimate_usd": r["estimated_stop_risk_usd"],
                     "excess_usd": S(max(D(0), -D(r["net_trade_usd"]) - D(r["estimated_stop_risk_usd"]))) }
                    for r in exits if -D(r["net_trade_usd"]) > D(r["estimated_stop_risk_usd"])]
        elapsed_required = int(_month_add(_instant(part["start_msc"]), 24).timestamp() * 1000)
        insufficiency = []
        if part["end_msc"] < elapsed_required:
            insufficiency.append("fewer_than_24_calendar_months")
        if report["candidate"] != "CASH" and len(exits) < 50:
            insufficiency.append("fewer_than_50_closed_trades")
        if sum(r["closing_equity_usd"] is not None for r in monthly) < 24:
            insufficiency.append("fewer_than_24_observed_monthly_marks")
        return {"kind": "invented_descriptive_account_statistics", "partition": deepcopy(part),
                "profile": report["profile"], "candidate": report["candidate"],
                "fill_fixture_sha256": report["fixture_sha256"], "fill_manifest_sha256": report["manifest_sha256"],
                "initial_cash_usd": S(initial), "final_cash_usd": state["balance_usd"], "toy_net_usd": S(net),
                "gross_usd": S(gross), "commissions_usd": S(fees), "financing_usd": S(financing),
                "trades": len(exits), "wins": len(wins), "losses": len(losses), "breakeven": sum(v == 0 for v in nets),
                "toy_win_fraction": None if not nets else S(D(len(wins)) / len(nets)),
                "net_expectancy_usd": None if not nets else S(net / len(nets)),
                "payoff_ratio": None if not wins or not losses else S((sum(wins) / len(wins)) / (-sum(losses) / len(losses))),
                "profit_factor": None if not losses else S(sum(wins, D(0)) / -sum(losses)),
                "largest_loss_usd": S(max(D(0), longest_loss)), "loss_beyond_entry_estimate": breaches,
                "max_drawdown": summary["max_drawdown"], "exposure_msc": exposure_ms,
                "exposure_fraction": S(D(exposure_ms) / (part["end_msc"] - part["start_msc"])),
                "flat_intervals": flat, "turnover_eur_units": S(units), "turnover_usd_notional": S(notional),
                "turnover_over_initial_cash": S(notional / initial), "embedded_price_adjustment_memos": {k: S(v) for k, v in memo.items()},
                "memos_are_extra_debits": False, "target_exit_spread_decomposition": None,
                "observed_quote_gaps": [{"start_msc": a, "end_msc": b, "duration_msc": b - a}
                                         for (a, _), (b, _) in zip(marks, marks[1:])],
                "monthly": monthly, "quarterly": quarterly, "sample_status": "insufficient" if insufficiency else "descriptive_only",
                "insufficiency_reasons": insufficiency, "market_assessment": "unavailable_invented_unqualified",
                "qualified_monthly_marks": 0, "untouched_validation_confirmed": False, "strategy_selected": False,
                "orders_available": False, "real_money_execution_available": False}


class Coordinator:
    """Two isolated offline partitions, with checked completed-prefix recovery."""
    def __init__(self, path, manifest_path):
        raw, mraw = daily._read(path), daily._read(manifest_path)
        m = daily._json(mraw)
        daily._fields(m, {"format", "kind", "frozen_at_utc", "fixture_sha256", "case", "partitions", "sources", "run_rules",
                          "aggregation_rules", "feature_rules", "fill_rules", "profiles", "orders_available",
                          "market_data_qualified", "untouched_validation_confirmed"}, "run_manifest_fields")
        expected = {"sources": source_bindings(), "run_rules": rules(), "aggregation_rules": bars.rules(),
                    "feature_rules": daily.rule_definitions(), "fill_rules": fills.rules(), "profiles": fills.risk.profiles()}
        if (m["format"] != "FXDL_DAILYRUNS122_FREEZE_V1" or m["kind"] != "invented_run_freeze"
                or m["fixture_sha256"] != hashlib.sha256(raw).hexdigest()
                or any(daily._canonical(m[k]) != daily._canonical(v) for k, v in expected.items())
                or any(m[k] is not False for k in ("orders_available", "market_data_qualified", "untouched_validation_confirmed"))):
            raise ValueError("run_freeze_binding")
        if expected["sources"]["config/research-candidates-117.json"] != daily.DECLARATION_SHA256:
            raise ValueError("fixed_declaration_changed")
        try:
            if type(m["frozen_at_utc"]) is not str:
                raise ValueError("freeze_time")
            instant = datetime.fromisoformat(m["frozen_at_utc"])
            if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
                raise ValueError("freeze_time")
        except (TypeError, ValueError) as exc:
            raise ValueError("freeze_time") from exc
        self._fixture = deepcopy(validate_fixture(daily._json(raw)))
        if m["case"] != self._fixture["case"] or daily._canonical(m["partitions"]) != daily._canonical(self._fixture["partitions"]):
            raise ValueError("run_freeze_partitions")
        self._fixture_sha, self._binding = hashlib.sha256(raw).hexdigest(), hashlib.sha256(mraw).hexdigest()
        self._root = None
        self._state = {"cursor": 0, "partitions": []}

    @property
    def state(self):
        return deepcopy(self._state)

    def _owner(self):
        return {"kind": "invented_run_output_binding", "fixture_sha256": self._fixture_sha, "manifest_sha256": self._binding}

    def _prefix(self, part):
        stream = deepcopy(self._fixture["stream"])
        stream["case"] = "run_" + part["name"]
        stream["messages"] = [m for m in stream["messages"] if m["receipt_msc"] < part["end_msc"]]
        stream["calendar"]["sessions"] = [s for s in stream["calendar"]["sessions"] if s["start_msc"] < part["end_msc"]]
        stream["execution_start_msc"] = part["start_msc"]
        stream["initial_account"] = {"kind": "invented_flat_cash", "trade_mode": 0, "currency": "USD",
                                     "available_msc": part["start_msc"], "balance_usd": 10000.}
        if not stream["messages"]:
            raise ValueError("no_observed_prefix")
        bars.validate_fixture(stream)
        return stream

    @staticmethod
    def _endpoint(prefix, part):
        quotes = [q for q in prefix["messages"] if q["kind"] == "quote" and q["source_msc"] >= part["start_msc"]]
        if not quotes or quotes[-1]["source_msc"] != part["endpoint_source_msc"]:
            raise ValueError("missing_declared_endpoint")
        last = quotes[-1]
        row = next(s for s in prefix["calendar"]["sessions"] if s["start_msc"] <= last["source_msc"] < s["end_msc"])
        repeated = len(quotes) > 1 and last["source_msc"] == quotes[-2]["source_msc"]
        if repeated or last["receipt_msc"] - last["source_msc"] > 2000 or row["status"] != "trading":
            raise ValueError("invalid_endpoint_quote")

    def _attempt_owner(self, part):
        return {**self._owner(), "partition": part}

    def _attempt(self, part):
        for i in range(100):
            directory = self._root / f"{part['name']}-attempt{i:02d}"
            if directory.exists():
                if directory.is_symlink() or daily._canonical(daily._json(daily._read(directory / "attempt-binding.json"))) != daily._canonical(self._attempt_owner(part)):
                    raise ValueError("attempt_binding")
                continue
            directory.mkdir()
            daily.write_new(directory / "attempt-binding.json", self._attempt_owner(part))
            return directory
        raise ValueError("attempt_limit")

    def _calculate(self, part, directory, write):
        try:
            prefix = self._prefix(part)
        except ValueError as exc:
            if str(exc) != "no_observed_prefix":
                raise
            return {"partition": deepcopy(part), "status": "unavailable", "reason": str(exc),
                    "planned_comparisons": 8, "computed_comparisons": 0, "returns": None, "statistics": [],
                    "market_assessment": "unavailable_invented_unqualified", "untouched_validation_confirmed": False,
                    "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}
        if write:
            daily.write_new(directory / "prefix-input.json", prefix)
            bars.freeze_fixture(directory / "prefix-input.json", directory / "prefix-frozen.json")
        elif daily._canonical(daily._json(daily._read(directory / "prefix-input.json"))) != daily._canonical(prefix):
            raise ValueError("derived_prefix_changed")
        replay = bars.Replay(directory / "prefix-input.json", directory / "prefix-frozen.json")
        aggregation = replay.run()
        if write:
            daily.write_new(directory / "aggregation.json", aggregation)
        elif daily._canonical(daily._json(daily._read(directory / "aggregation.json"))) != daily._canonical(aggregation):
            raise ValueError("aggregation_changed")
        reason, reports, statistics = None, [], []
        try:
            self._endpoint(prefix, part)
            compiled = bars.compile_fills(replay)
        except ValueError as exc:
            reason = str(exc)
        else:
            if write:
                daily.write_new(directory / "fills-input.json", compiled)
                fills.freeze_fixture(directory / "fills-input.json", directory / "fills-frozen.json")
            elif daily._canonical(daily._json(daily._read(directory / "fills-input.json"))) != daily._canonical(compiled):
                raise ValueError("derived_fills_changed")
            try:
                for profile in fills.risk.profiles():
                    for candidate in daily.CANDIDATES:
                        execution = fills.Replay(directory / "fills-input.json", directory / "fills-frozen.json", profile, candidate)
                        report = execution.run()
                        reports.append(report)
                        statistics.append(_statistics(compiled, report, part))
            except ValueError as exc:
                reason, reports, statistics = str(exc), [], []
            else:
                for name, content in (("fills-report.json", {"kind": "invented_partition_accounts", "results": reports}),
                                      ("statistics.json", {"kind": "invented_partition_statistics", "results": statistics})):
                    if write:
                        daily.write_new(directory / name, content)
                    elif daily._canonical(daily._json(daily._read(directory / name))) != daily._canonical(content):
                        raise ValueError("partition_results_changed")
        return {"partition": deepcopy(part), "status": "unavailable" if reason else "invented_descriptive_only",
                "reason": reason, "planned_comparisons": 8, "computed_comparisons": len(statistics),
                "returns": None if reason else "toy_ledger_only", "statistics": statistics,
                "market_assessment": "unavailable_invented_unqualified", "untouched_validation_confirmed": False,
                "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}

    def step(self, output_root):
        root = Path(output_root).resolve()
        if self._root is None:
            root.mkdir()
            daily.write_new(root / "run-binding.json", self._owner())
            self._root = root
        elif root != self._root:
            raise ValueError("output_root_changed")
        if self._state["cursor"] == 2:
            return False
        part = self._fixture["partitions"][self._state["cursor"]]
        directory = self._attempt(part)
        result = self._calculate(part, directory, True)
        result["derived_files"] = {p.name: _hash(p) for p in sorted(directory.iterdir())}
        daily.write_new(directory / "partition-report.json", result)
        record = {**result, "attempt_directory": directory.name, "partition_report_sha256": _hash(directory / "partition-report.json")}
        self._state = {"cursor": self._state["cursor"] + 1, "partitions": self._state["partitions"] + [record]}
        return True

    def run(self, output_root):
        while self._state["cursor"] < 2:
            self.step(output_root)
        if Path(output_root).resolve() != self._root:
            raise ValueError("output_root_changed")
        return self.report()

    def report(self):
        if self._state["cursor"] != 2:
            raise ValueError("unfinished_run_report")
        return {"kind": "invented_chronological_run_report", "case": self._fixture["case"],
                "fixture_sha256": self._fixture_sha, "manifest_sha256": self._binding, "partitions": self.state["partitions"],
                "planned_toy_comparisons": 16, "market_cells_run": 0, "capital_summed_as_portfolio": False,
                "market_data_qualified": False, "paper_evaluation_available": False, "untouched_validation_confirmed": False,
                "strategy_selected": False, "orders_available": False, "real_money_execution_available": False}

    def checkpoint(self):
        p = {"schema": "daily_runs122_checkpoint_v1", "fixture_sha256": self._fixture_sha,
             "manifest_sha256": self._binding, "cursor": self._state["cursor"], "state": self.state}
        return json.dumps({"payload": p, "sha256": daily._digest(p)}, sort_keys=True, allow_nan=False)

    @classmethod
    def restore(cls, path, manifest_path, checkpoint, output_root):
        if type(checkpoint) is not str or len(checkpoint.encode()) > daily.MAX_BYTES:
            raise ValueError("checkpoint_size")
        value = daily._json(checkpoint)
        daily._fields(value, {"payload", "sha256"}, "checkpoint_envelope")
        p = value["payload"]
        daily._fields(p, {"schema", "fixture_sha256", "manifest_sha256", "cursor", "state"}, "checkpoint_payload")
        result = cls(path, manifest_path)
        if (value["sha256"] != daily._digest(p) or p["schema"] != "daily_runs122_checkpoint_v1"
                or p["fixture_sha256"] != result._fixture_sha or p["manifest_sha256"] != result._binding):
            raise ValueError("checkpoint_binding")
        cursor = daily._integer(p["cursor"], 0, 2, "checkpoint_cursor")
        daily._fields(p["state"], {"cursor", "partitions"}, "checkpoint_state")
        if type(p["state"]["partitions"]) is not list or len(p["state"]["partitions"]) != cursor:
            raise ValueError("checkpoint_reconstructed_state")
        root = Path(output_root)
        if root.is_symlink() or not root.is_dir() or daily._canonical(daily._json(daily._read(root / "run-binding.json"))) != daily._canonical(result._owner()):
            raise ValueError("output_binding")
        result._root = root.resolve()
        records = []
        for i in range(cursor):
            record = p["state"]["partitions"][i]
            if type(record) is not dict or type(record.get("attempt_directory")) is not str or not re.fullmatch(NAMES[i] + r"-attempt[0-9]{2}", record["attempt_directory"]):
                raise ValueError("checkpoint_attempt")
            directory = result._root / record["attempt_directory"]
            if directory.is_symlink():
                raise ValueError("attempt_binding")
            actual = daily._json(daily._read(directory / "partition-report.json"))
            if _hash(directory / "partition-report.json") != record.get("partition_report_sha256"):
                raise ValueError("partition_artifact_binding")
            derived = actual.get("derived_files")
            if type(derived) is not dict or any(type(n) is not str or Path(n).name != n for n in derived):
                raise ValueError("partition_artifact_binding")
            for n, h in derived.items():
                if _hash(directory / n) != h:
                    raise ValueError("partition_artifact_binding")
            if daily._canonical(daily._json(daily._read(directory / "attempt-binding.json"))) != daily._canonical(result._attempt_owner(result._fixture["partitions"][i])):
                raise ValueError("attempt_binding")
            rebuilt = result._calculate(result._fixture["partitions"][i], directory, False)
            rebuilt["derived_files"] = derived
            if daily._canonical(rebuilt) != daily._canonical(actual):
                raise ValueError("checkpoint_reconstructed_state")
            records.append({**rebuilt, "attempt_directory": directory.name, "partition_report_sha256": _hash(directory / "partition-report.json")})
        result._state = {"cursor": cursor, "partitions": records}
        if daily._canonical(result._state) != daily._canonical(p["state"]):
            raise ValueError("checkpoint_reconstructed_state")
        return result


def evaluate_fixture(path, manifest_path, output_root):
    run = Coordinator(path, manifest_path)
    report = run.run(output_root)
    daily.write_new(Path(output_root) / "run-report.json", report)
    daily.write_new(Path(output_root) / "run-checkpoint.json", daily._json(run.checkpoint()))
    return report
