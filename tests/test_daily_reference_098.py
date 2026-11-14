from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

from forex_demo_lab import daily_reference_098 as ref


def dt(value):
    return datetime.fromisoformat(value)


def update_source(document):
    """Invented test author re-embeds changed source bytes, not an importer oracle."""
    raw = [{k: v for k, v in r.items() if k != "source_artifact_sha256"} for r in document["observations"]]
    content = json.dumps(dict(schema=ref.SOURCE_SCHEMA, observations=raw), sort_keys=True, indent=2) + "\n"
    document["artifact"]["content"] = content
    digest = hashlib.sha256(content.encode()).hexdigest()
    for row in document["observations"]:
        row["source_artifact_sha256"] = digest
    return document


class DailyReference098Tests(unittest.TestCase):
    def setUp(self):
        self.document = ref.synthetic_fixture()
        self.bundle = ref.parse_bundle(self.document)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def select(self, instant, day=7):
        return ref.select_as_of(self.bundle, date(2030, 1, day), dt(instant))

    def test_fixture_has_explicit_decimal_direction_and_separate_times(self):
        original = self.bundle.observations[0]
        self.assertEqual((original.base_currency, original.quote_currency, original.value), ("EUR", "USD", Decimal("1.10")))
        self.assertEqual(original.observation_date, date(2030, 1, 7))
        self.assertEqual(original.first_published_at, dt("2030-01-07T16:00:00+00:00"))
        self.assertEqual(original.retrieved_at, dt("2030-01-12T12:00:00+00:00"))
        self.assertEqual(self.bundle.policy.source_label, "invented:daily-reference-098")

    def test_exact_publication_boundary_is_missing(self):
        result = self.select("2030-01-07T16:00:00+00:00")
        self.assertEqual(result.reason, ref.MissingReason.NOT_YET_AVAILABLE)
        self.assertIsNone(result.version)

    def test_one_microsecond_after_publication_selects_original(self):
        result = self.select("2030-01-07T16:00:00.000001+00:00")
        self.assertEqual((result.reason, result.version.vintage_id, result.version.value),
                         (ref.MissingReason.SELECTED, "v1", Decimal("1.10")))

    def test_exact_revision_boundary_keeps_original(self):
        result = self.select("2030-01-08T17:00:00+00:00")
        self.assertEqual((result.version.vintage_id, result.version.value), ("v1", Decimal("1.10")))

    def test_after_revision_selects_correction(self):
        result = self.select("2030-01-08T17:00:00.000001+00:00")
        self.assertEqual((result.version.vintage_id, result.version.value), ("v2", Decimal("1.11")))

    def test_future_revision_never_mutates_earlier_decision(self):
        self.select("2030-01-10T18:00:00+00:00")
        result = self.select("2030-01-07T18:00:00+00:00")
        self.assertEqual(result.version.vintage_id, "v1")

    def test_observation_date_is_not_release_time(self):
        self.assertIsNone(self.select("2030-01-08T15:59:59+00:00", 8).version)
        self.assertEqual(self.select("2030-01-08T16:00:01+00:00", 8).version.value, Decimal("1.12"))

    def test_invented_holiday_has_typed_missing_no_carry_forward(self):
        result = self.select("2030-01-09T18:00:00+00:00", 9)
        self.assertEqual(result.reason, ref.MissingReason.NON_PUBLICATION_DAY)
        self.assertIsNone(result.version)

    def test_missing_expected_observation_is_not_interpolated(self):
        result = self.select("2030-01-11T18:00:00+00:00", 11)
        self.assertEqual(result.reason, ref.MissingReason.NO_OBSERVATION)
        self.assertIsNone(result.version)

    def test_reordered_records_have_same_versions_and_decisions(self):
        self.document["observations"].reverse()
        reordered = ref.parse_bundle(self.document)
        self.assertEqual(reordered, self.bundle)
        self.assertEqual(ref.select_as_of(reordered, date(2030, 1, 7), dt("2030-01-08T18:00:00+00:00")).version.vintage_id, "v2")

    def test_identical_duplicate_is_explicitly_deduplicated(self):
        self.document["observations"].append(deepcopy(self.document["observations"][0]))
        result = ref.parse_bundle(self.document)
        self.assertEqual(result.duplicate_records_removed, 1)
        self.assertEqual(len(result.observations), 4)

    def test_conflicting_duplicate_rejects_even_with_updated_digest(self):
        row = deepcopy(self.document["observations"][0]); row["value"] = "1.19"
        self.document["observations"].append(row)
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            ref.parse_bundle(update_source(self.document))

    def test_ambiguous_simultaneous_vintages_reject(self):
        self.document["observations"][1]["available_at"] = "2030-01-07T16:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "simultaneous"):
            ref.parse_bundle(update_source(self.document))

    def test_inconsistent_first_publication_rejects(self):
        self.document["observations"][1]["first_published_at"] = "2030-01-08T16:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "first publication"):
            ref.parse_bundle(update_source(self.document))

    def test_two_revised_vintages_without_original_reject(self):
        self.document["observations"][0]["available_at"] = "2030-01-07T17:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "Missing original"):
            ref.parse_bundle(update_source(self.document))

    def test_nonfinite_nonpositive_or_float_prices_reject(self):
        for value in ("NaN", "Infinity", "-Infinity", "0", "-1", "bad", 1.1, True):
            doc = deepcopy(self.document); doc["observations"][0]["value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.parse_bundle(update_source(doc))

    def test_naive_malformed_or_incomplete_timestamps_reject(self):
        for value in ("2030-01-07T16:00:00", "invalid", "2030-01-07", None):
            doc = deepcopy(self.document); doc["observations"][0]["available_at"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.parse_bundle(update_source(doc))

    def test_availability_before_publication_or_retrieval_rejects(self):
        for field, value in (("available_at", "2030-01-07T15:00:00+00:00"),
                             ("retrieved_at", "2030-01-06T12:00:00+00:00")):
            doc = deepcopy(self.document); doc["observations"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ref.parse_bundle(update_source(doc))

    def test_naive_non_utc_or_non_datetime_decision_rejects(self):
        for value in (datetime(2030, 1, 7, 18), dt("2030-01-07T18:00:00+02:00"), "2030-01-07T18:00:00Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ref.select_as_of(self.bundle, date(2030, 1, 7), value)

    def test_missing_ambiguous_or_mixed_currency_direction_rejects(self):
        for change in ({"quote_currency": ""}, {"quote_currency": "EUR"},
                       {"base_currency": "USD", "quote_currency": "EUR"}):
            doc = deepcopy(self.document); doc["observations"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                ref.parse_bundle(update_source(doc))

    def test_missing_policy_or_evidence_rejects(self):
        doc = deepcopy(self.document); doc["policy"] = None
        with self.assertRaisesRegex(ValueError, "dated policy"):
            ref.parse_bundle(doc)
        doc = deepcopy(self.document); doc["policy"]["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "evidence"):
            ref.parse_bundle(doc)
        doc = deepcopy(self.document); doc["observations"][0]["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "evidence"):
            ref.parse_bundle(update_source(doc))

    def test_later_policy_cannot_be_backdated(self):
        self.document["policy"]["document_date"] = "2031-01-01"
        with self.assertRaisesRegex(ValueError, "historical applicability"):
            ref.parse_bundle(self.document)

    def test_out_of_period_observation_or_invalid_calendar_rejects(self):
        for field, value in (("valid_from", "2030-01-08"), ("calendar", ["2030-01-08", "2030-01-08"]),
                             ("calendar", ["2030-01-07", "2030-01-08"])):
            doc = deepcopy(self.document); doc["policy"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ref.parse_bundle(doc)

    def test_missing_or_changed_artifact_digest_rejects(self):
        for change in ("remove", "change"):
            doc = deepcopy(self.document)
            if change == "remove": del doc["observations"][0]["source_artifact_sha256"]
            else: doc["observations"][0]["source_artifact_sha256"] = "0" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                ref.parse_bundle(doc)

    def test_record_must_match_embedded_artifact(self):
        self.document["observations"][0]["value"] = "1.19"
        with self.assertRaisesRegex(ValueError, "artifact contents"):
            ref.parse_bundle(self.document)

    def test_updated_digest_and_synthetic_label_do_not_admit_other_data(self):
        self.document["observations"][0]["value"] = "9.99"
        with self.assertRaisesRegex(ValueError, "exact fixed098"):
            ref.parse_bundle(update_source(self.document))

    def test_invented_source_cannot_claim_real_publisher_identity(self):
        self.document["policy"]["source_label"] = "ECB"
        self.document["artifact"]["label"] = "ECB"
        with self.assertRaisesRegex(ValueError, "exact fixed098"):
            ref.parse_bundle(self.document)

    def test_final_vintage_without_release_history_is_inspection_only(self):
        self.document["role"] = ref.Role.FINAL_VINTAGE.value
        self.document["policy"] = None
        self.document["observations"] = [self.document["observations"][1]]
        self.document["observations"][0]["first_published_at"] = None
        self.document["observations"][0]["available_at"] = None
        inspected = ref.parse_bundle(update_source(self.document))
        self.assertIs(type(inspected), ref.FinalVintageInspection)
        self.assertEqual(ref.integrity_summary(inspected)["versions_without_release_history"], 1)
        with self.assertRaisesRegex(ValueError, "cannot enter"):
            ref.select_as_of(inspected, date(2030, 1, 7), dt("2030-01-08T18:00:00+00:00"))

    def test_final_vintage_with_policy_still_cannot_enter_selector(self):
        self.document["role"] = ref.Role.FINAL_VINTAGE.value
        inspected = ref.parse_bundle(self.document)
        with self.assertRaises(ValueError):
            ref.select_as_of(inspected, date(2030, 1, 7), dt("2030-01-08T18:00:00+00:00"))
        self.assertFalse(ref.integrity_summary(inspected)["historical_market_data_qualified"])

    def test_hand_constructed_synthetic_object_is_revalidated(self):
        rows = (replace(self.bundle.observations[0], value=Decimal("9.99")), *self.bundle.observations[1:])
        forged = replace(self.bundle, observations=rows)
        with self.assertRaises(ValueError):
            ref.select_as_of(forged, date(2030, 1, 7), dt("2030-01-08T18:00:00+00:00"))
        with self.assertRaises(ValueError): ref.save_bundle(self.root / "forged.json", forged)
        self.assertFalse((self.root / "forged.json").exists())

    def test_deterministic_save_reload_and_existing_file_rejection(self):
        a, b = self.root / "a.json", self.root / "b.json"
        ref.save_bundle(a, self.bundle)
        loaded = ref.load_bundle(a)
        ref.save_bundle(b, loaded)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertEqual(loaded, self.bundle)
        self.assertEqual(ref.select_as_of(loaded, date(2030, 1, 7), dt("2030-01-08T17:00:01+00:00")).version.vintage_id, "v2")
        with self.assertRaises(FileExistsError): ref.save_bundle(a, self.bundle)

    def test_inspection_roundtrip_preserves_label_and_normalizes_offsets(self):
        self.document["role"] = ref.Role.FINAL_VINTAGE.value
        self.document["policy"] = None
        self.document["artifact"]["label"] = "invented:inspection-example"
        self.document["observations"][0]["available_at"] = "2030-01-07T18:00:00+02:00"
        inspected = ref.parse_bundle(update_source(self.document))
        target = self.root / "inspection.json"
        ref.save_bundle(target, inspected)
        self.assertEqual(ref.load_bundle(target), inspected)
        self.assertEqual(inspected.artifact_label, "invented:inspection-example")
        self.assertEqual(inspected.observations[0].available_at, dt("2030-01-07T16:00:00+00:00"))

    def test_unknown_role_schema_or_extra_field_rejects(self):
        for field, value in (("schema", "v2"), ("role", "market_evaluation"), ("allow_market", True)):
            doc = deepcopy(self.document); doc[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): ref.parse_bundle(doc)

    def test_bad_date_empty_bundle_and_non_date_query_reject(self):
        doc = deepcopy(self.document); doc["observations"][0]["observation_date"] = "2030-02-31"
        with self.assertRaises(ValueError): ref.parse_bundle(update_source(doc))
        doc = deepcopy(self.document); doc["observations"] = []
        with self.assertRaises(ValueError): ref.parse_bundle(doc)
        with self.assertRaises(ValueError):
            ref.select_as_of(self.bundle, "2030-01-07", dt("2030-01-08T18:00:00+00:00"))
        with self.assertRaises(ValueError):
            ref.select_as_of(self.bundle, date(2030, 1, 12), dt("2030-01-12T18:00:00+00:00"))

    def test_oversized_local_file_duplicate_json_keys_and_bad_encoding_reject(self):
        path = self.root / "bad.json"
        for raw in (b" " * (ref.MAX_BYTES + 1), b'{"schema":1,"schema":2}', b"\xff", b'{"value":NaN}'):
            path.write_bytes(raw)
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): ref.load_bundle(path)

    def test_demo_reports_manual_expected_versions_and_counts_without_returns(self):
        script = Path(__file__).resolve().parents[1] / "scripts/daily-reference-098.py"
        demonstration = runpy.run_path(str(script))["demonstration"]
        report = demonstration(self.bundle)
        self.assertEqual((report["unique_versions"], report["observation_dates"], report["selected_cases"], report["missing_cases"]), (4, 3, 4, 4))
        self.assertEqual([r["vintage_id"] for r in report["cases"]], [None, "v1", "v1", "v2", None, None, None, "v1"])
        self.assertFalse(report["historical_market_data_qualified"])
        self.assertFalse(report["profitability_established"])
        self.assertFalse(report["orders_available"])
        self.assertNotIn("returns", report)


if __name__ == "__main__":
    unittest.main()
