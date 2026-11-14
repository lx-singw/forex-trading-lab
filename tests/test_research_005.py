import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("research005", Path(__file__).resolve().parents[1] / "scripts/research-005.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class Research005GateTests(unittest.TestCase):
    def test_short_missing_edges_and_unexplained_gaps_block(self):
        lower = study.epoch("20240401") + 4 * 3600000
        upper = study.epoch("20240501") + 4 * 3600000
        good = {"first_ms": lower, "last_ms": upper - 1, "observed_hours": 528,
                "gaps_over_one_hour": [{"classification": "weekend_pattern_not_certified"}]}
        self.assertEqual(study.coverage_failures(good, lower, upper), [])
        for updates, expected in [({"first_ms": lower + 7 * 3600000}, "start_boundary_coverage"),
                                  ({"last_ms": upper - 7 * 3600000}, "end_boundary_coverage"),
                                  ({"observed_hours": 499}, "fewer_than_500_observed_hours"),
                                  ({"gaps_over_one_hour": [{"classification": "unresolved"}]}, "unresolved_gap_over_one_hour")]:
            self.assertIn(expected, study.coverage_failures({**good, **updates}, lower, upper))

    def test_missing_or_incorrect_broker_hour_fails_even_when_other_prices_match(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "capture.json").write_text("{}")
            lower = study.epoch("20240409") + 12 * 3600000
            ticks = [{"time_msc": lower + i * 3600000, "bid": 1.1 + i * .001, "ask": 1.1001 + i * .001}
                     for i in range(6)]
            reference = {(lower // 3600000) - 3 + i: t["bid"] for i, t in enumerate(ticks)}
            with patch.object(study, "checked_capture", return_value=({}, ticks, lower, lower + 6 * 3600000)):
                self.assertTrue(study.compare_window(reference, folder, 3)["passed"])
                self.assertFalse(study.compare_window(reference, folder, 2)["passed"])
                bad = dict(reference)
                bad[min(bad)] += .0006
                self.assertFalse(study.compare_window(bad, folder, 3)["passed"])
            with patch.object(study, "checked_capture", return_value=({}, ticks[:-1], lower, lower + 6 * 3600000)):
                result = study.compare_window(reference, folder, 3)
                self.assertFalse(result["passed"])
                self.assertEqual(len(result["missing_hours"]), 1)

    def test_event_screen_requires_observed_activity_in_both_minutes(self):
        lower = study.epoch("20240410") + 5 * 3600000
        ticks = [{"time_msc": lower + minute * 60000 + i, "bid": bid}
                 for minute, bids in ((450, [1.1, 1.1001]), (510, [1.1, 1.101, 1.102, 1.103]))
                 for i, bid in enumerate(bids)]
        with patch.object(study, "archive_ticks", return_value=iter(ticks)):
            self.assertTrue(study.event_screen(Path("unused"), "20240410")["passed"])
        with patch.object(study, "archive_ticks", return_value=iter(ticks[2:])):
            self.assertFalse(study.event_screen(Path("unused"), "20240410")["passed"])

    def test_blocked_study_cannot_freeze_any_performance_manifest(self):
        review = {"protocol_sha256": "frozen", "datasets": [{"status": "blocked_data_quality"}]}
        with patch.object(study, "load", return_value=review), patch.object(study, "sha256", return_value="frozen"), \
                patch.object(study, "freeze") as freeze:
            with self.assertRaisesRegex(ValueError, "All declared months blocked"):
                study.freeze_all()
            freeze.assert_not_called()

    def test_changed_protocol_cannot_freeze(self):
        with patch.object(study, "load", return_value={"protocol_sha256": "original"}), \
                patch.object(study, "sha256", return_value="changed"), patch.object(study, "freeze") as freeze:
            with self.assertRaisesRegex(ValueError, "Protocol changed"):
                study.freeze_all()
            freeze.assert_not_called()
