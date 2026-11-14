import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("research006", Path(__file__).resolve().parents[1] / "scripts/research-006.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class Research006Tests(unittest.TestCase):
    def test_event_screen_rejects_missing_flat_or_weak_control_comparison(self):
        control = {"ticks": 10, "range_pips": 1}
        self.assertTrue(study.event_passes(control, {"ticks": 20, "range_pips": 3}))
        self.assertFalse(study.event_passes({"ticks": 0, "range_pips": 0}, {"ticks": 20, "range_pips": 3}))
        self.assertFalse(study.event_passes(control, {"ticks": 19, "range_pips": 30}))
        self.assertFalse(study.event_passes(control, {"ticks": 200, "range_pips": 2.9}))

    def test_activity_obeys_half_open_minutes_and_declared_shift(self):
        ticks = [{"time_msc": ms, "bid": bid} for ms, bid in
                 ((60000, 1.0), (119999, 1.0002), (120000, 2.0))]
        groups = study.activity(ticks, [0], shift=-60000)
        self.assertEqual(groups[0]["ticks"], 2)
        self.assertAlmostEqual(groups[0]["range_pips"], 2)

    def test_capture_cannot_use_another_day_even_with_six_hours(self):
        day = "20241030"
        lower = study.prior.epoch(day) + 12 * 3600000
        with patch.object(study, "checked_capture", return_value=({}, [], lower, lower + 6 * 3600000)):
            self.assertEqual(study.expected_capture(Path("unused"), day), [])
            with self.assertRaisesRegex(ValueError, "bounds"):
                study.expected_capture(Path("unused"), "20241031")

    def test_alternative_offset_never_rescues_failed_primary_evidence(self):
        events = [{"date": d, "histdata_event_passed": True, "broker_event_passed": True,
                   "utc_plus_3_comparison": {"passed": True}, "utc_plus_2_alternative": {"passed": True}}
                  for d in ("20241030", "20241031")]
        coverage = {"new-york": [], "fixed-est": []}
        self.assertTrue(study.all_evidence_passes(events, coverage))
        events[1]["utc_plus_3_comparison"]["passed"] = False
        self.assertFalse(study.all_evidence_passes(events, coverage))
        events[1]["utc_plus_3_comparison"]["passed"] = True
        self.assertFalse(study.all_evidence_passes(events, {"new-york": [], "fixed-est": ["gap"]}))
        self.assertFalse(study.all_evidence_passes(events[:1], coverage))
        self.assertFalse(study.all_evidence_passes([events[0], events[0]], coverage))

    def test_blocked_clock_gate_never_creates_performance_manifests(self):
        review = {"protocol_sha256": "same", "clock_evidence_sha256": "same", "performance_evaluation_ready": False}
        with patch.object(study.prior, "load", return_value=review), patch.object(study, "sha256", return_value="same"), \
                patch.object(study, "freeze") as freeze:
            with self.assertRaisesRegex(ValueError, "does not permit"):
                study.freeze_all()
            freeze.assert_not_called()

    def test_matching_prices_cannot_override_failed_absolute_clock_events(self):
        events = [{"date": d, "histdata_event_passed": False, "broker_event_passed": False,
                   "utc_plus_3_comparison": {"passed": True}} for d in ("20241030", "20241031")]
        self.assertFalse(study.all_evidence_passes(events, {"new-york": [], "fixed-est": []}))
