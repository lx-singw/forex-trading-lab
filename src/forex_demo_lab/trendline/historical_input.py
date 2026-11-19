"""Read reviewed historical Level B development input without running the counter."""

from dataclasses import dataclass
from datetime import datetime, time, timezone
import hashlib
from pathlib import PurePosixPath

from ..elliott_study_145 import span
from ..paired_replay_133 import strict_json
from . import data, historical_calendar, signal_count

VERSION = "TRL_PHASE10_INPUT_217_V1"
MANIFEST_KIND = "trendline_development_level_b_manifest"
METADATA_LIMIT = 256 * 1024

# A separate source review can pin exact manifest bytes in a repository change.
REVIEWED_MANIFESTS = frozenset()


@dataclass(frozen=True)
class HistoricalInput:
    calendar: historical_calendar.Calendar
    warmup: tuple[data.Hour, ...]
    development: tuple[data.Hour, ...]
    receipt: dict


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
    rows = strict_json(raw, data.BYTE_LIMIT)
    if type(rows) is not list or not 1 <= len(rows) <= data.ROW_LIMIT:
        raise ValueError("bounded nonempty H1 observations required")

    scheduled = {window.start: window.end for window in calendar.frame("H1")}
    warmup, development_hours = [], []
    previous = None
    for row in rows:
        hour = data.Hour.from_record(row, "bid_only")
        if scheduled.get(hour.start) != hour.end:
            raise ValueError("H1 row outside reviewed calendar window")
        if previous is not None and (hour.start < previous.end or hour.available_at < previous.available_at):
            raise ValueError("overlapping H1 bars or reordered receipts")
        (warmup if hour.start < calendar.development_start else development_hours).append(hour)
        previous = hour
    return tuple(warmup), tuple(development_hours)


def load_level_b(manifest_path):
    """Return the reviewed calendar and typed H1 rows with a coverage receipt."""
    manifest_path = data.no_links(manifest_path)
    raw = _bounded_bytes(manifest_path, METADATA_LIMIT)
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in REVIEWED_MANIFESTS:
        raise ValueError("manifest has no recorded qualification before price read")
    manifest = strict_json(raw, METADATA_LIMIT)
    data.fields(manifest, ("schema", "kind", "symbol", "partition", "plan_file", "plan_file_sha256",
                           "calendar_file", "price_file"))
    if (manifest["schema"], manifest["kind"], manifest["symbol"], manifest["partition"]) != (
        VERSION, MANIFEST_KIND, "EURUSD", "development",
    ):
        raise ValueError("reviewed development-only EURUSD manifest required")
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
    warmup, development = _read_hours(bundle / price_file, plan, calendar)
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
        "market_data_read": True, "actual_counts": None,
    }
    return HistoricalInput(calendar, warmup, development, receipt)
