"""Development opportunity counts before account state or exit evaluation."""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import hashlib

from ..elliott_study_145 import overlap, span
from . import breaks, context, data, entries, fills, geometry, quote_replay, quotes, selection, study


VERSION = "TRL_SIGNAL_COUNT_194_V1"
STATUS_VERSION = "TRL_PHASE10_STATUS_218_V1"
MINIMUM_OPPORTUNITIES = 60
PROFILES = tuple(profile for profile in breaks.PROFILES if profile in data.CANDIDATES)
COSTS = ("base", "adverse")
ENTRY_FILTERS = (("positive_stop", "NONPOSITIVE_STOP"), ("stop_side", "STOP_ALREADY_CROSSED"),
                 ("positive_entry", "NONPOSITIVE_ENTRY"), ("stop_atr_window", "STOP_OUT_OF_WINDOW"),
                 ("spread_to_stop_cap", "SPREAD_TOO_WIDE"), ("fxr_target", "NO_VALID_TARGET"))
ENTRY_REJECTIONS = {reason for _, reason in ENTRY_FILTERS}
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
COUNTS = ("scheduled_h4_due", "observed_h4", "valid_action_lines_found", "action_line_observations",
          "candidate_geometries_poked", "registered_action_lines_poked", "triggered_lines", "break_setups",
          "bounce_setups", "groups_consumed", "ready_setups", "setup_skips", "abstentions",
          "break_setups_without_safety", "entry_attempts", "entry_eligible_opportunities", "entry_skips", "entry_pending")


def _bindings(level):
    bound = entries.bindings()
    paths = ("src/forex_demo_lab/trendline/signal_count.py", "tools/signal_count.py")
    if level == "Q":
        paths += ("src/forex_demo_lab/trendline/quotes.py", "src/forex_demo_lab/trendline/quote_replay.py")
    return bound | {path: hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest() for path in paths}


def _scope(source, as_of, tick, profiles, costs):
    if source.record()["partition"] != "development":
        raise ValueError("signal counting requires an invented development partition")
    calendar = source.calendar
    cutoff = calendar.end if as_of is None else as_of
    data.integer(cutoff)
    if not calendar.start <= cutoff <= calendar.end:
        raise ValueError("count cursor must be inside the development receipt scope")
    fills.decimal(tick, positive=True)
    for choices, allowed in ((profiles, PROFILES), (costs, COSTS)):
        if (not isinstance(choices, (list, tuple)) or not choices or any(item not in allowed for item in choices)
                or len(set(choices)) != len(choices)):
            raise ValueError("distinct frozen strategies and cost profiles required")
    return cutoff


def _month(at):
    return (EPOCH + timedelta(milliseconds=at)).strftime("%Y-%m")


def _tally():
    return {key: Counter() for key in ("counts", "setup_states", "setup_reasons", "setup_skip_reasons",
                                      "abstention_reasons", "entry_statuses", "entry_skip_reasons", "lines_per_h4",
                                      "line_ages", "trigger_touches", "stop_atr", "spread_stop",
                                      "entry_filter_evaluated", "entry_filter_passed")}


def _setups(source, bars, tick, profile):
    replay = breaks.BreakReplay(source, tick, profile, count_only=type(source) is data.HistoricalDeclaration)
    frames = ("D1", "H4") if profile in (context.PROFILE, breaks.FXR_PROFILE) else ("H4",)
    for bar in bars:
        if bar.timeframe in frames:
            replay.observe(bar)
    return replay.report()


def _setup_months(report, calendar, cutoff, profile, development_start):
    monthly = defaultdict(_tally)
    for slot in calendar.frame("H4"):
        due = slot.end + calendar.delay
        if development_start <= slot.start and due <= cutoff:
            monthly[_month(due)]["counts"]["scheduled_h4_due"] += 1

    action = report["action_replay"]
    operations = {event["id"]: event["command"]["op"] for event in action["journal"]["events"]}
    views, pokes, trigger_exemptions = {}, set(), set()
    warmup = _tally()
    for frame, decision in zip(action["frames"], report["decisions"], strict=True):
        if (frame["id"], frame["as_of"], frame["bar_index"]) != (
                decision["h4_frame_id"], decision["available_at"], decision["bar_index"]):
            raise ValueError("setup and lifecycle frame identities differ")
        # Retain revisions, first pokes and trigger exemptions across the seam.
        row = warmup if frame["bar"]["start"] < development_start else monthly[_month(frame["as_of"])]
        counts = row["counts"]
        counts["observed_h4"] += 1
        lifecycle = Counter(operations[event_id] for event_id in frame["lifecycle_event_ids"])
        counts["valid_action_lines_found"] += lifecycle["VALID"]
        counts["registered_action_lines_poked"] += lifecycle["POKE"]
        eligible = frame["action_line_ids"]
        row["lines_per_h4"][len(eligible)] += 1
        counts["action_line_observations"] += len(eligible)
        row["line_ages"].update(frame["bar_index"] - views[line]["touch_indices"][0] for line in eligible)

        triggered = [views[item["line_id"]] for item in decision["triggered"]]
        if triggered:
            counts["triggered_lines"] += len(triggered)
            # Every trigger precedes the current frame's alias merges.
            counts["groups_consumed"] += len({line["resolved_group"] for line in triggered})
            row["trigger_touches"].update("exactly_two" if len(line["touch_indices"]) == 2 else "three_or_more"
                                          for line in triggered)
            if profile == breaks.BNC_PROFILE:
                counts["bounce_setups"] += 1
            else:
                counts["break_setups"] += 1
                counts["break_setups_without_safety"] += decision["reason"] == "NO_SAFETY_LINE"
                trigger_exemptions.update((line["geometry_id"], frame["bar_index"]) for line in triggered)
        for candidate in frame["candidates"]:
            poke = candidate["first_penetration"]
            identity = candidate["id"]
            if poke is not None and identity not in pokes and (identity, poke["bar_index"]) not in trigger_exemptions:
                pokes.add(identity)
                counts["candidate_geometries_poked"] += 1

        state, reason = decision["state"], decision["reason"]
        row["setup_states"][state] += 1
        if reason is not None:
            row["setup_reasons"][reason] += 1
        counts["ready_setups"] += state == "READY"
        if state in ("SKIPPED", "DISCARDED", "INVALIDATED"):
            counts["setup_skips"] += 1
            row["setup_skip_reasons"][reason] += 1
        elif state == "ABSTAINED":
            counts["abstentions"] += 1
            row["abstention_reasons"][reason] += 1
        views.update((record["line_id"], record["view"]) for record in frame["revisions"])
    return monthly


def _bar_attempts(source, observations, report, model, cutoff, liquidation, development_start, allow_equal_open):
    bid_only = source.record()["geometry_basis"] == "bid_only"
    historical = type(source) is data.HistoricalDeclaration
    for attempt, targets in entries._requests(report, source.calendar, model.costs["name"],
                                               development_start=development_start):
        request = attempt["request"]
        window = model.entry_window(request["trigger_end"])
        expires = attempt["expires_at"]
        if bid_only and window is not None and expires is not None and request["decision_at"]["time"] <= window.start < expires:
            if liquidation <= window.start:
                yield request, "SKIPPED", "ENTRY_AT_LIQUIDATION", None
                continue
            if not allow_equal_open and request["decision_at"]["time"] == window.start:
                # A historical paired quote is checked against its own order evidence in _resolve.
                evidence = observations.get(window.start) if historical else None
                if evidence is None or evidence.source_at is None:
                    yield request, "SKIPPED", "UNRESOLVED_OPEN_ORDER", None
                    continue
        yield (request, *entries._resolve(model, request, window, expires, observations, cutoff, bid_only, targets,
                                         historical=historical))


def _quote_candidates(tape, prefix, model):
    floor = Fraction(model.costs["spread_floor_pips"]) * fills.PIP
    quality, candidates = Counter(), []
    previous = None
    for quote in prefix:
        reason = quote_replay._quality(tape, quote, previous)
        previous = quote
        quality[reason] += 1
        if reason == "EXECUTABLE":
            if quote_replay._prices(quote, floor)[2] <= quotes.MAX_ENTRY_SPREAD:
                candidates.append(quote)
            else:
                quality["ENTRY_SPREAD_EXCEEDED"] += 1
    return floor, candidates, {"received": len(prefix), "passed_quote_quality": quality["EXECUTABLE"],
                               "passed_entry_spread_cap": len(candidates), "reasons": dict(sorted(quality.items()))}


def _quote_attempts(tape, report, model, cutoff, candidates, floor):
    decisions, chosen = quote_replay._decisions(tape, report, candidates, cutoff, model.costs["name"])
    by_sequence = {quote.sequence: quote for quote in candidates}
    picks = {attempt["id"]: (by_sequence[sequence], targets) for sequence, (attempt, targets) in chosen.items()}
    for attempt in decisions:
        request = attempt["request"]
        if attempt["id"] not in picks:
            yield request, attempt["status"], attempt["reason"], None
            continue
        quote, targets = picks[attempt["id"]]
        price = model._entry_at(request, quote_replay._prices(quote, floor),
                                fills.Event(quote.source, quote.sequence), targets)
        yield request, price["status"], price["reason"], price


def _record_attempts(monthly, attempts):
    for request, status, reason, price in attempts:
        row = monthly[_month(request["decision_at"]["time"])]
        counts = row["counts"]
        counts["entry_attempts"] += 1
        if status == "FILLED" or reason in ENTRY_REJECTIONS:
            for stage, rejected in ENTRY_FILTERS:
                if stage == "fxr_target" and request["exit_model"] != "E2":
                    continue
                row["entry_filter_evaluated"][stage] += 1
                if reason == rejected:
                    break
                row["entry_filter_passed"][stage] += 1
        if status == "FILLED":
            counts["entry_eligible_opportunities"] += 1
            row["entry_statuses"]["ELIGIBLE"] += 1
            distance = Fraction(price["stop_distance"])
            row["stop_atr"][distance / selection.fraction(request["atr"])] += 1
            row["spread_stop"][Fraction(price["effective_spread_pips"]) * fills.PIP / distance] += 1
        else:
            row["entry_statuses"][status] += 1
            if status == "PENDING":
                counts["entry_pending"] += 1
            else:
                counts["entry_skips"] += 1
                row["entry_skip_reasons"][reason] += 1


def _distribution(histogram):
    return [{"value": geometry.rational_record(value), "count": count} for value, count in sorted(histogram.items())]


def _summary(row):
    values = row["counts"]
    counts = {field: values[field] for field in COUNTS}
    if (counts["ready_setups"] != counts["entry_attempts"] or counts["entry_attempts"] !=
            sum(counts[field] for field in ("entry_eligible_opportunities", "entry_skips", "entry_pending"))):
        raise ValueError("entry opportunity counts do not reconcile")
    observed, age_count = counts["observed_h4"], counts["action_line_observations"]
    age_sum = sum(age * n for age, n in row["line_ages"].items())
    numerator, denominator = counts["break_setups_without_safety"], counts["break_setups"]
    return {"counts": counts, **{key: dict(sorted(row[key].items()))
                                 for key in ("setup_states", "setup_reasons", "setup_skip_reasons", "abstention_reasons",
                                             "entry_statuses", "entry_skip_reasons")},
            "entry_price_filters": {stage: {"evaluated": row["entry_filter_evaluated"][stage],
                                            "passed": row["entry_filter_passed"][stage]}
                                    for stage, _ in ENTRY_FILTERS},
            "diagnostics": {"action_lines_per_h4_histogram": {str(n): count for n, count in sorted(row["lines_per_h4"].items())},
                            "mean_action_lines_per_h4": geometry.rational_record(Fraction(age_count, observed)) if observed else None,
                            "mean_action_line_age_h4": geometry.rational_record(Fraction(age_sum, age_count)) if age_count else None,
                            "no_safety_line_break_share": {"numerator": numerator, "denominator": denominator,
                                                           "ratio": geometry.rational_record(Fraction(numerator, denominator)) if denominator else None},
                            "triggered_lines_by_touches": {key: row["trigger_touches"][key] for key in ("exactly_two", "three_or_more")},
                            "stop_distance_in_atr": _distribution(row["stop_atr"]),
                            "spread_to_stop_distance": _distribution(row["spread_stop"])}}


@data.replay_bindings()
def _cells(source, bars, observations, *, cutoff, tick, profiles, costs, liquidation,
           tape=None, development_start=None, allow_equal_open=True):
    level = "B" if tape is None else "Q"
    calendar = source.calendar
    development_start = calendar.start if development_start is None else development_start
    bound = _bindings(level)
    models = {cost: fills.PriceModel(source, cost) for cost in costs}
    quote_inputs = {} if tape is None else {
        cost: _quote_candidates(tape, observations, model) for cost, model in models.items()}
    cells = []
    for profile in profiles:
        report = _setups(source, bars, tick, profile)
        setup_months = _setup_months(report, calendar, cutoff, profile, development_start)
        for cost, model in models.items():
            monthly = deepcopy(setup_months)
            if tape is None:
                attempts = _bar_attempts(source, observations, report, model, cutoff, liquidation,
                                         development_start, allow_equal_open)
            else:
                floor, candidates, _ = quote_inputs[cost]
                attempts = _quote_attempts(tape, report, model, cutoff, candidates, floor)
            _record_attempts(monthly, attempts)
            total = _tally()
            for row in monthly.values():
                for key, values in row.items():
                    total[key].update(values)
            cells.append({"profile": profile, "cost_profile": cost, "total": _summary(total),
                          "months": {month: _summary(row) for month, row in sorted(monthly.items())}})
    if _bindings(level) != bound:
        raise ValueError("signal count source bindings changed")
    return {"schema": VERSION, "kind": "invented_development_opportunity_counts", "data_level": level,
            "geometry_basis": source.record()["geometry_basis"] if tape is None else "mid_sync",
            "symbol": "EURUSD", "partition": "development", "scope_start": development_start,
            "scope_end": calendar.end, "as_of": cutoff, "liquidation_at": liquidation, "tick_size": tick,
            "input_sha256": source.record()["input_sha256"] if tape is None else tape.sha256,
            "source_sha256": source.sha256, "calendar_sha256": calendar.sha256,
            "source_bindings": bound, "month_clock": "h4_setup_receipt_utc", "cells": cells,
            "quote_observation_filters_by_cost": {cost: value[2] for cost, value in quote_inputs.items()},
            "actual_source_admitted": False, "outcomes_computed": False, "orders_available": False,
            "feasibility": _unavailable()}


def _unavailable():
    return {"status": "UNAVAILABLE", "reason": "ACTUAL_SOURCE_NOT_ADMITTED",
            "minimum_opportunities_per_strategy": MINIMUM_OPPORTUNITIES, "actual_counts": None,
            "dly_status": "DISABLED_PENDING_DEVELOPMENT_EVIDENCE"}


def _liquidation(calendar, liquidation_at, *, start):
    starts = tuple(window.start for window in calendar.frame("H1") if window.start >= start)
    if not starts:
        raise ValueError("Level B counting requires a scheduled H1 partition")
    liquidation = starts[-1] if liquidation_at is None else liquidation_at
    data.integer(liquidation)
    if liquidation not in starts:
        raise ValueError("Level B count liquidation requires a scheduled H1 opening")
    return liquidation


def count_b(source, hours, *, tick, as_of=None, profiles=PROFILES, costs=COSTS, liquidation_at=None):
    """Count per declared B opening, using the price checks only."""
    cutoff = _scope(source, as_of, tick, profiles, costs)
    calendar = source.calendar
    liquidation = _liquidation(calendar, liquidation_at, start=calendar.start)
    if not isinstance(hours, (tuple, list)) or len(hours) > data.ROW_LIMIT:
        raise ValueError("bounded typed hourly observations required")
    stream = data.BarStream(source)
    visible = []
    for hour in hours:
        if not isinstance(hour, data.Hour):
            raise ValueError("typed completed hourly observation required")
        if hour.available_at > cutoff:
            break
        stream.observe(hour)
        visible.append(hour)
    stream.advance(cutoff)
    hourly = entries._visible_hours(source, visible, cutoff, calendar)
    return _cells(source, stream.bars(), hourly, cutoff=cutoff, tick=tick, profiles=profiles, costs=costs,
                  liquidation=liquidation)


def count_q(tape, *, tick, as_of=None, profiles=PROFILES, costs=COSTS):
    """Count at the first eligible quote, before account admission."""
    if not isinstance(tape, quotes.Tape):
        raise ValueError("typed invented quote tape required")
    cutoff = _scope(tape.geometry_source, as_of, tick, profiles, costs)
    prefix = tuple(tape.prefix(cutoff))
    bars = tape.publications(prefix, cutoff)
    return _cells(tape.geometry_source, bars, prefix, cutoff=cutoff, tick=tick, profiles=profiles, costs=costs,
                  liquidation=tape.liquidation, tape=tape)


_LATER_STUDY_CODES = {
    "prior_trial_history_incomplete", "undated_price_exposure_count_missing", "tried_alternatives_count_missing",
    "historical_costs_unknown", "hypothetical_costs_cannot_pass_qualified_track",
    "initial_28_cell_track_budget_exhausted", "paired_exit_analysis_not_declared",
    "initial_paired_analysis_budget_exhausted", "partitions_not_chronological_disjoint",
    "sensitivity_cannot_satisfy_broker_or_demo_gate", "level_B_cannot_satisfy_qualified_broker_or_demo_gate",
    "level_B_not_qualified_execution_data", "unchanged_control_input_compatibility_not_qualified",
    "qualified_market_runner_unavailable", "full_strategy_acceptance_incomplete", "uncertainty_sha256_unassigned",
}
_LATER_STUDY_EVIDENCE_CODES = {
    f"evidence_{check}_{gate}"
    for check in ("missing", "frames_incomplete", "scope_gap", "not_independently_qualified")
    for gate in ("prior_trials", "commission_swap", "contract_margin_conversion")
}


def _later_study_issue(issue, level):
    code = issue["code"]
    return (issue["scope"] == "validation" or code in _LATER_STUDY_CODES
            or code in _LATER_STUDY_EVIDENCE_CODES or (level == "B" and code == "liquidation_timestamp_unassigned"))


def _reserved_validation_overlap(plan):
    validation = span(plan["partitions"]["validation"]["interval"], nullable=True)
    if validation is None:
        return False
    development = plan["partitions"]["development"]
    return any(bounds is not None and overlap(bounds, validation) for bounds in (
        span(development["interval"], nullable=True), span(development["warmup"]["interval"], nullable=True),
    ))


def admission_status(plan):
    preflight = study.assess(plan)
    count_issues, study_issues = [], []
    for issue in preflight["issues"]:
        target = study_issues if _later_study_issue(issue, plan["data_level"]) else count_issues
        target.append(issue)
    if _reserved_validation_overlap(plan):
        count_issues.append({"code": "development_scope_overlaps_reserved_validation", "scope": "development",
                             "state": "BLOCKED"})
    if plan["data_level"] == "Q":
        count_issues.append({"code": "historical_signal_counter_unavailable", "scope": "development", "state": "UNAVAILABLE"})
    return {"schema": STATUS_VERSION, "kind": "development_feasibility_admission_status", "partition": "development",
            "plan_sha256": preflight["plan_sha256"], "actual_source_admitted": False, "market_data_read": False,
            "outcomes_computed": False, "orders_available": False, "feasibility": _unavailable(),
            "development_preflight_issues": count_issues, "later_study_preflight_issues": study_issues}
