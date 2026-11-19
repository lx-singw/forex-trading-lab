"""Run the pre-account counter on a reviewed historical Level B bundle."""

from dataclasses import replace
import hashlib

from . import data, entries, historical_input, signal_count

VERSION = "TRL_PHASE10_COUNT_218_V1"


def _bindings():
    paths = ("src/forex_demo_lab/elliott_study_145.py",
             "src/forex_demo_lab/trendline/study.py",
             "src/forex_demo_lab/trendline/historical_count.py",
             "src/forex_demo_lab/trendline/historical_input.py",
             "src/forex_demo_lab/trendline/historical_calendar.py")
    return {path: hashlib.sha256((data.ROOT / path).read_bytes()).hexdigest() for path in paths}


def _completed_hours(dataset):
    calendar = dataset.calendar
    for hour in dataset.warmup + dataset.development:
        available = max(hour.available_at, hour.end + calendar.delay)
        if available > calendar.end:
            break
        yield hour if available == hour.available_at else replace(hour, available_at=available)


def count(manifest_path):
    """Check the reviewed scope and count each frozen strategy under both costs."""
    bound = _bindings()
    dataset = historical_input.load_level_b(manifest_path)
    calendar = dataset.calendar
    hours = tuple(_completed_hours(dataset))
    bars = calendar.publications(hours, calendar.end)
    hourly = entries._visible_hours(dataset.source, hours, calendar.end, calendar)
    report = signal_count._cells(
        dataset.source, bars, hourly, cutoff=calendar.end, tick=dataset.tick_size,
        profiles=signal_count.PROFILES, costs=signal_count.COSTS, liquidation=dataset.liquidation_at,
        development_start=calendar.development_start,
        allow_equal_open=dataset.same_time_open_order == "decision_before_open",
    )
    if bound != _bindings():
        raise ValueError("historical count input bindings changed")
    threshold = signal_count.MINIMUM_OPPORTUNITIES
    actual = []
    for cell in report["cells"]:
        count = cell["total"]["counts"]["entry_eligible_opportunities"]
        actual.append({
            "profile": cell["profile"], "cost_profile": cell["cost_profile"],
            "entry_eligible_opportunities": count, "status": "PASS" if count >= threshold else "INSUFFICIENT",
        })
    report.update(schema=VERSION, kind="historical_development_opportunity_counts",
                  actual_source_admitted=True, market_data_read=True,
                  source_bindings=report["source_bindings"] | bound,
                  input_receipt=dataset.receipt, warmup_start=calendar.start,
                  feasibility={"status": "COUNTED", "minimum_opportunities_per_strategy": threshold,
                               "actual_counts": actual, "dly_status": "DISABLED_PENDING_DEVELOPMENT_EVIDENCE"})
    return report
