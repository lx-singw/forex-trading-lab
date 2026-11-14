"""Offline reference-rate integrity and fixed invented chronology. No trading."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "daily_reference_098_v1"
SOURCE_SCHEMA = "daily_reference_098_source_v1"
MAX_BYTES = 1_048_576
UTC = timezone.utc
INVENTED_SOURCE = "invented:daily-reference-098"


class Role(str, Enum):
    SYNTHETIC = "synthetic_chronology"
    FINAL_VINTAGE = "final_vintage_inspection"


class MissingReason(str, Enum):
    SELECTED = "selected"
    NOT_YET_AVAILABLE = "not_yet_available"
    NO_OBSERVATION = "no_observation"
    NON_PUBLICATION_DAY = "non_publication_day"


@dataclass(frozen=True)
class Observation:
    series: str
    base_currency: str
    quote_currency: str
    value: Decimal
    observation_date: date
    vintage_id: str
    first_published_at: datetime | None
    available_at: datetime | None
    retrieved_at: datetime
    source_artifact_sha256: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class Policy:
    policy_id: str
    source_label: str
    document_date: date
    valid_from: date
    valid_through: date
    calendar: tuple[date, ...]
    timezone: str
    publication_semantics: str
    revision_semantics: str
    permitted_use: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SyntheticSeries:
    policy: Policy
    observations: tuple[Observation, ...]
    artifact_label: str
    artifact_content: str
    duplicate_records_removed: int


@dataclass(frozen=True)
class FinalVintageInspection:
    policy: Policy | None
    observations: tuple[Observation, ...]
    artifact_label: str
    artifact_content: str
    duplicate_records_removed: int


@dataclass(frozen=True)
class Availability:
    observation_date: date
    reason: MissingReason
    version: Observation | None


def _keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"Invalid {label} fields")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing {label}")
    return value


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Require an ISO observation/policy date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid date") from exc


def _instant(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("Require an explicit timezone-aware timestamp")
    try:
        instant = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Naive timestamp forbidden")
    return instant.astimezone(UTC)


def _refs(value):
    if not isinstance(value, list) or not value or any(not isinstance(s, str) or not s.strip() for s in value):
        raise ValueError("Missing evidence references")
    if len(value) != len(set(value)):
        raise ValueError("Duplicate evidence reference")
    return tuple(value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _decode(text):
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON") from exc


def _reject_constant(value):
    raise ValueError("Nonfinite JSON")


def _dump(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


ROW_FIELDS = ("series", "base_currency", "quote_currency", "value", "observation_date",
              "vintage_id", "first_published_at", "available_at", "retrieved_at", "evidence_refs")
POLICY_FIELDS = ("policy_id", "source_label", "document_date", "valid_from", "valid_through",
                 "calendar", "timezone", "publication_semantics", "revision_semantics",
                 "permitted_use", "evidence_refs")


def _policy(value):
    if value is None:
        return None
    _keys(value, POLICY_FIELDS, "policy")
    for key in ("policy_id", "source_label", "timezone", "publication_semantics", "revision_semantics", "permitted_use"):
        _text(value[key], key)
    start, end, document = (_date(value[k]) for k in ("valid_from", "valid_through", "document_date"))
    if start > end or document > start:
        raise ValueError("Policy dates do not establish historical applicability")
    if not isinstance(value["calendar"], list):
        raise ValueError("Missing explicit calendar")
    calendar = tuple(_date(d) for d in value["calendar"])
    if not calendar or len(set(calendar)) != len(calendar) or any(d < start or d > end for d in calendar):
        raise ValueError("Invalid policy calendar")
    return Policy(value["policy_id"], value["source_label"], document, start, end,
                  tuple(sorted(calendar)), value["timezone"], value["publication_semantics"],
                  value["revision_semantics"], value["permitted_use"], _refs(value["evidence_refs"]))


def _observation(value, digest):
    _keys(value, (*ROW_FIELDS, "source_artifact_sha256"), "observation")
    if value["source_artifact_sha256"] != digest:
        raise ValueError("Source artifact digest mismatch")
    for key in ("series", "vintage_id"):
        _text(value[key], key)
    base, quote = value["base_currency"], value["quote_currency"]
    if any(not isinstance(c, str) or not re.fullmatch(r"[A-Z]{3}", c) for c in (base, quote)) or base == quote:
        raise ValueError("Explicit distinct base/quote currencies required")
    if not isinstance(value["value"], str):
        raise ValueError("Decimal value must be a string")
    try:
        number = Decimal(value["value"])
    except InvalidOperation as exc:
        raise ValueError("Invalid Decimal value") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("Require a positive finite Decimal value")
    published = None if value["first_published_at"] is None else _instant(value["first_published_at"])
    available = None if value["available_at"] is None else _instant(value["available_at"])
    retrieved = _instant(value["retrieved_at"])
    if (published is None) != (available is None):
        raise ValueError("Incomplete availability history")
    if published is not None and not published <= available <= retrieved:
        raise ValueError("Publication, version and retrieval times are inconsistent")
    observed = _date(value["observation_date"])
    return Observation(value["series"], base, quote, number, observed, value["vintage_id"],
                       published, available, retrieved, digest, _refs(value["evidence_refs"]))


def _ordered(observations):
    unique = {}
    for row in observations:
        key = (row.series, row.observation_date, row.vintage_id)
        if key in unique and unique[key] != row:
            raise ValueError("Conflicting duplicate vintage")
        unique[key] = row
    rows = tuple(sorted(unique.values(), key=lambda r: (r.series, r.observation_date,
                       r.available_at or datetime.min.replace(tzinfo=UTC), r.vintage_id)))
    if len({(r.series, r.base_currency, r.quote_currency) for r in rows}) != 1:
        raise ValueError("Require one unambiguous series and currency direction")
    for observed in {r.observation_date for r in rows}:
        versions = [r for r in rows if r.observation_date == observed]
        if len({r.first_published_at for r in versions}) != 1:
            raise ValueError("Inconsistent first publication across vintages")
        if len(versions) > 1:
            if any(r.available_at is None for r in versions):
                raise ValueError("Multiple vintages without availability history")
            if len({r.available_at for r in versions}) != len(versions):
                raise ValueError("Ambiguous simultaneous vintages")
            if versions[0].first_published_at != versions[0].available_at:
                raise ValueError("Missing original vintage")
    return rows


def _invented_policy():
    return dict(policy_id="invented:policy-098", source_label=INVENTED_SOURCE,
                document_date="2030-01-01", valid_from="2030-01-07", valid_through="2030-01-11",
                calendar=["2030-01-07", "2030-01-08", "2030-01-10", "2030-01-11"], timezone="UTC",
                publication_semantics="invented explicit UTC releases; no inferred schedule",
                revision_semantics="invented explicit UTC version availability",
                permitted_use="invented software testing only", evidence_refs=["invented:policy-098"])


def _invented_rows():
    def row(day, vintage, number, available):
        return dict(series="invented:EURUSD-098", base_currency="EUR", quote_currency="USD", value=number,
                    observation_date=f"2030-01-{day:02d}", vintage_id=vintage,
                    first_published_at=f"2030-01-{day:02d}T16:00:00+00:00", available_at=available,
                    retrieved_at="2030-01-12T12:00:00+00:00", evidence_refs=["invented:release-098"])
    return [row(7, "v1", "1.10", "2030-01-07T16:00:00+00:00"),
            row(7, "v2", "1.11", "2030-01-08T17:00:00+00:00"),
            row(8, "v1", "1.12", "2030-01-08T16:00:00+00:00"),
            row(10, "v1", "1.13", "2030-01-10T16:00:00+00:00")]


def synthetic_fixture():
    """A fixed invented source, with its exact source bytes embedded for hashing."""
    content = _dump(dict(schema=SOURCE_SCHEMA, observations=_invented_rows()))
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return dict(schema=SCHEMA, role=Role.SYNTHETIC.value, policy=_invented_policy(),
                artifact=dict(label=INVENTED_SOURCE, content=content),
                observations=[dict(r, source_artifact_sha256=digest) for r in _invented_rows()])


def parse_bundle(document):
    _keys(document, ("schema", "role", "policy", "artifact", "observations"), "bundle")
    if document["schema"] != SCHEMA:
        raise ValueError("Unsupported schema")
    try:
        role = Role(document["role"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Unsupported role; market evaluation unavailable") from exc
    artifact = document["artifact"]
    _keys(artifact, ("label", "content"), "artifact")
    _text(artifact["label"], "artifact label")
    content = _text(artifact["content"], "artifact bytes")
    if len(content.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Source artifact too large")
    source = _decode(content)
    _keys(source, ("schema", "observations"), "source artifact")
    if source["schema"] != SOURCE_SCHEMA or not isinstance(source["observations"], list):
        raise ValueError("Invalid source artifact schema")
    if not isinstance(document["observations"], list) or not document["observations"]:
        raise ValueError("No observations")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    parsed = [_observation(r, digest) for r in document["observations"]]
    for r in source["observations"]:
        _keys(r, ROW_FIELDS, "source record")
    # Match source bytes to record contents, without assuming source order.
    original = {_observation(dict(r, source_artifact_sha256=digest), digest) for r in source["observations"]}
    if set(parsed) != original:
        raise ValueError("Records do not match source artifact contents")
    rows = _ordered(parsed)
    policy = _policy(document["policy"])
    duplicate_count = len(parsed) - len(rows)
    if role is Role.FINAL_VINTAGE:
        return FinalVintageInspection(policy, rows, artifact["label"], content, duplicate_count)
    if policy is None:
        raise ValueError("Synthetic chronology requires dated policy evidence")
    if any(r.first_published_at is None or r.available_at is None for r in rows):
        raise ValueError("Synthetic chronology requires release history")
    if any(not policy.valid_from <= r.observation_date <= policy.valid_through
           or r.observation_date not in policy.calendar for r in rows):
        raise ValueError("Observation is outside evidenced policy/calendar")
    # A role label cannot relabel external records as invented observations.
    fixture = synthetic_fixture()
    if (artifact != fixture["artifact"] or policy != _policy(fixture["policy"])
            or rows != _ordered([_observation(r, digest) for r in fixture["observations"]])):
        raise ValueError("Only exact fixed098 invented source/policy is selectable")
    return SyntheticSeries(policy, rows, artifact["label"], content, duplicate_count)


def load_bundle(path):
    """Read one supplied local JSON file; never resolve references or contact hosts."""
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Bundle too large")
    try:
        return parse_bundle(_decode(raw.decode("utf-8")))
    except UnicodeDecodeError as exc:
        raise ValueError("Require UTF-8 JSON") from exc


def _row_document(row):
    return dict(series=row.series, base_currency=row.base_currency, quote_currency=row.quote_currency,
                value=str(row.value), observation_date=row.observation_date.isoformat(), vintage_id=row.vintage_id,
                first_published_at=row.first_published_at.isoformat() if row.first_published_at else None,
                available_at=row.available_at.isoformat() if row.available_at else None,
                retrieved_at=row.retrieved_at.isoformat(), source_artifact_sha256=row.source_artifact_sha256,
                evidence_refs=list(row.evidence_refs))


def _document(bundle):
    if type(bundle) not in (SyntheticSeries, FinalVintageInspection):
        raise ValueError("Require a typed local reference bundle")
    p = bundle.policy
    policy = None if p is None else dict(policy_id=p.policy_id, source_label=p.source_label,
        document_date=p.document_date.isoformat(), valid_from=p.valid_from.isoformat(),
        valid_through=p.valid_through.isoformat(), calendar=[d.isoformat() for d in p.calendar],
        timezone=p.timezone, publication_semantics=p.publication_semantics, revision_semantics=p.revision_semantics,
        permitted_use=p.permitted_use, evidence_refs=list(p.evidence_refs))
    return dict(schema=SCHEMA, role=Role.SYNTHETIC.value if type(bundle) is SyntheticSeries else Role.FINAL_VINTAGE.value,
                policy=policy, artifact=dict(label=bundle.artifact_label,
                content=bundle.artifact_content), observations=[_row_document(r) for r in bundle.observations])


def save_bundle(path, bundle):
    document = _document(bundle)
    parse_bundle(document)  # Reject mutated/hand-constructed typed objects before writing.
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(_dump(document))


def select_as_of(bundle, observed, decision_at):
    if type(bundle) is not SyntheticSeries:
        raise ValueError("Market/final-vintage observations cannot enter the synthetic selector")
    checked = parse_bundle(_document(bundle))  # Do not trust a typed label alone.
    if type(observed) is not date:
        raise ValueError("Require an observation date")
    if not isinstance(decision_at, datetime) or decision_at.tzinfo is None or decision_at.utcoffset() != timedelta(0):
        raise ValueError("Require a declared UTC decision instant")
    if not checked.policy.valid_from <= observed <= checked.policy.valid_through:
        raise ValueError("Decision observation is outside evidenced policy")
    if observed not in checked.policy.calendar:
        return Availability(observed, MissingReason.NON_PUBLICATION_DAY, None)
    rows = [r for r in checked.observations if r.observation_date == observed]
    if not rows:
        return Availability(observed, MissingReason.NO_OBSERVATION, None)
    eligible = [r for r in rows if r.available_at < decision_at]
    if not eligible:
        return Availability(observed, MissingReason.NOT_YET_AVAILABLE, None)
    return Availability(observed, MissingReason.SELECTED, max(eligible, key=lambda r: r.available_at))


def integrity_summary(bundle):
    checked = parse_bundle(_document(bundle))
    return dict(schema=SCHEMA, role=Role.SYNTHETIC.value if type(checked) is SyntheticSeries else Role.FINAL_VINTAGE.value,
                unique_versions=len(checked.observations), observation_dates=len({r.observation_date for r in checked.observations}),
                versions_without_release_history=sum(r.available_at is None for r in checked.observations),
                duplicate_records_removed=bundle.duplicate_records_removed,
                historical_market_data_qualified=False, profitability_established=False, orders_available=False)
