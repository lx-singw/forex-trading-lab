"""Read reviewed historical Level B development input without running the counter."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, time, timezone
import hashlib
from pathlib import PurePosixPath

from ..elliott_study_145 import span
from ..paired_replay_133 import strict_json
from . import data, entries, historical_calendar, signal_count, study

VERSION = "TRL_PHASE10_INPUT_221_V1"
MANIFEST_KIND = "trendline_development_level_b_manifest"
METADATA_LIMIT = 256 * 1024

# A separate source review can pin exact manifest bytes in a repository change.
REVIEWED_MANIFESTS = frozenset()


@dataclass(frozen=True)
class HistoricalInput:
    source: data.HistoricalDeclaration
    warmup: tuple[data.Hour, ...]
    development: tuple[data.Hour, ...]
    openings: tuple[entries.HistoricalOpening, ...]
    tick_size: str
    same_time_open_order: str
    liquidation_at: int
    receipt: dict

    @property
    def calendar(self):
        return self.source.calendar


def _qualified_plan(plan):
    status = signal_count.admission_status(plan)
    if plan["data_level"] != "B" or plan["geometry_basis"] != "bid_only":
        raise ValueError("Level B bid bars required")
    if plan["case"] == "invented_claims" or plan["source"]["alias"] == "source_invented_claims":
        raise ValueError("invented source cannot enter the historical reader")
    blockers = [issue["code"] for issue in status["development_preflight_issues"]
                if issue["state"] in ("MISSING", "BLOCKED")]
    if blockers:
        raise ValueError("development scope rejected before price read: " + ", ".join(blockers))
    return status["plan_sha256"]


def _relative_file(name):
    if type(name) is not str or not name or "\\" in name or ":" in name:
        raise ValueError("relative reviewed filename required")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or ".." in path.parts or path.as_posix() != name:
        raise ValueError("relative reviewed filename required")
    return path


def _utc_bounds(interval):
    return tuple(int(datetime.combine(day, time(), timezone.utc).timestamp()) * 1000 for day in span(interval))


def _bounded_bytes(path, limit):
    with data.no_links(path).open("rb") as handle:
        raw = handle.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError("input byte limit")
    return raw


def _read_calendar(path, plan):
    raw = _bounded_bytes(path, historical_calendar.BYTE_LIMIT)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != plan["calendar_sha256"]:
        raise ValueError("calendar file differs from reviewed plan before price read")
    development = plan["partitions"]["development"]
    start, _ = _utc_bounds(development["warmup"]["interval"])
    development_start, end = _utc_bounds(development["interval"])
    return historical_calendar.Calendar.from_record(
        strict_json(raw, historical_calendar.BYTE_LIMIT), sha256=digest,
        start=start, development_start=development_start, end=end,
        delay=plan["latency"]["finalization_delay_ms"],
    )


def _read_hours(path, plan, calendar):
    raw = _bounded_bytes(path, data.BYTE_LIMIT)
    if hashlib.sha256(raw).hexdigest() != plan["input_sha256"]:
        raise ValueError("price file differs from the reviewed input before parsing")
    payload = strict_json(raw, data.BYTE_LIMIT)
    data.fields(payload, ("hours", "openings"))
    rows = payload["hours"]
    if type(rows) is not list or not 1 <= len(rows) <= data.ROW_LIMIT:
        raise ValueError("bounded nonempty H1 observations required")

    scheduled = {window.start: window.end for window in calendar.frame("H1")}
    warmup, development_hours = [], []
    previous = None
    for row in rows:
        hour = data.Hour.from_geometry_record(row)
        if scheduled.get(hour.start) != hour.end:
            raise ValueError("H1 row outside reviewed calendar window")
        if previous is not None and (hour.start < previous.end or hour.available_at < previous.available_at):
            raise ValueError("overlapping H1 bars or reordered receipts")
        (warmup if hour.start < calendar.development_start else development_hours).append(hour)
        previous = hour
    openings = _opening_rows(payload["openings"], scheduled, calendar.delay)
    return tuple(warmup), tuple(development_hours), openings


def _opening_rows(rows, scheduled, delay):
    if type(rows) is not list or len(rows) > data.ROW_LIMIT:
        raise ValueError("bounded opening evidence array required")
    openings = []
    for row in rows:
        evidence = entries.HistoricalOpening.from_record(row, delay=delay)
        if scheduled.get(evidence.price.start) != evidence.price.end:
            raise ValueError("opening evidence outside reviewed H1 window")
        if openings and evidence.price.start <= openings[-1].price.start:
            raise ValueError("unique opening evidence in scheduled order required")
        openings.append(evidence)
    return tuple(openings)


def _opening_coverage(calendar, openings):
    scheduled = sum(window.start >= calendar.development_start for window in calendar.frame("H1"))
    statuses = Counter(evidence.coverage_status(calendar.end) for evidence in openings
                       if evidence.price.start >= calendar.development_start)
    statuses["MISSING_OPENING_EVIDENCE"] = scheduled - sum(statuses.values())
    return {"scheduled": scheduled, "status_counts": dict(sorted(statuses.items()))}


def load_level_b(manifest_path, *, delayed_entry=False):
    """Return the reviewed calendar and typed H1 rows with a coverage receipt."""
    manifest_path = data.no_links(manifest_path)
    raw = _bounded_bytes(manifest_path, METADATA_LIMIT)
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in REVIEWED_MANIFESTS:
        raise ValueError("manifest has no recorded qualification before price read")
    manifest = strict_json(raw, METADATA_LIMIT)
    fields = ("schema", "kind", "symbol", "partition", "plan_file", "plan_file_sha256",
              "calendar_file", "price_file", "tick_size", "same_time_open_order")
    data.fields(manifest, (*fields, "entry_rule") if delayed_entry else fields)
    if delayed_entry and manifest["entry_rule"] != entries.DELAYED_ENTRY_RULE:
        raise ValueError("reviewed delayed-entry rule required before price read")
    if (manifest["schema"], manifest["kind"], manifest["symbol"], manifest["partition"]) != (
        VERSION, MANIFEST_KIND, "EURUSD", "development",
    ):
        raise ValueError("reviewed development-only EURUSD manifest required")
    if data.number(manifest["tick_size"]) <= 0:
        raise ValueError("positive reviewed price tick required")
    if manifest["same_time_open_order"] not in ("decision_before_open", "unresolved"):
        raise ValueError("reviewed same-time opening order policy required")
    data.sha(manifest["plan_file_sha256"])
    bundle = manifest_path.parent
    plan_file = _relative_file(manifest["plan_file"])
    calendar_file = _relative_file(manifest["calendar_file"])
    price_file = _relative_file(manifest["price_file"])
    if len({plan_file, calendar_file, price_file}) != 3:
        raise ValueError("reviewed plan, calendar and price files must be distinct")
    plan_bytes = _bounded_bytes(bundle / plan_file, METADATA_LIMIT)
    if hashlib.sha256(plan_bytes).hexdigest() != manifest["plan_file_sha256"]:
        raise ValueError("plan differs from reviewed development manifest")
    plan = strict_json(plan_bytes, METADATA_LIMIT)
    plan_sha = _qualified_plan(plan)
    calendar = _read_calendar(bundle / calendar_file, plan)
    endpoint = plan["endpoints"]["development"]["liquidation_at"]
    liquidation = None if endpoint is None else int(study.instant(endpoint).timestamp()) * 1000
    liquidation = signal_count._liquidation(calendar, liquidation, start=calendar.development_start)
    warmup, development, openings = _read_hours(bundle / price_file, plan, calendar)
    warmup_coverage = calendar.coverage(warmup, start=calendar.start, cutoff=calendar.development_start)
    claimed = plan["partitions"]["development"]["warmup"]["declared_complete_bars"]
    for frame, minimum in claimed.items():
        if warmup_coverage[frame]["complete_by_cutoff"] < minimum:
            raise ValueError(f"reviewed {frame} warmup coverage missing at development start")
    development_coverage = calendar.coverage(development, start=calendar.development_start, cutoff=calendar.end)
    if not development_coverage["H1"]["complete_by_cutoff"]:
        raise ValueError("reviewed H1 development coverage missing at scope end")
    receipt = {
        "schema": VERSION, "kind": "trendline_historical_input_check", "symbol": "EURUSD", "partition": "development",
        "manifest_sha256": digest, "plan_sha256": plan_sha, "plan_file_sha256": manifest["plan_file_sha256"],
        "input_sha256": plan["input_sha256"],
        "calendar_sha256": plan["calendar_sha256"], "warmup_rows": len(warmup), "development_rows": len(development),
        "warmup_at_development_start": warmup_coverage, "development_at_scope_end": development_coverage,
        "development_openings_at_scope_end": _opening_coverage(calendar, openings),
        "tick_size": manifest["tick_size"], "same_time_open_order": manifest["same_time_open_order"],
        "liquidation_at": liquidation,
        "market_data_read": True, "actual_counts": None,
    }
    if delayed_entry:
        receipt["entry_rule"] = entries.DELAYED_ENTRY_RULE
    source_record = {key: plan[key] for key in ("data_level", "geometry_basis", "spread_semantics",
                                               "input_sha256", "calendar_sha256")}
    source_record.update(kind="reviewed_historical_trendline_source", symbol="EURUSD", partition="development")
    source = data.HistoricalDeclaration(data.canonical(source_record).decode(), calendar)
    return HistoricalInput(source, warmup, development, openings, manifest["tick_size"], manifest["same_time_open_order"],
                           liquidation, receipt)
