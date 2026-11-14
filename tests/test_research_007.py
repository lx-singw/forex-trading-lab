import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("research007", Path(__file__).resolve().parents[1] / "scripts/research-007.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class IntervalMappingTests(unittest.TestCase):
    def ticks(self, source):
        offset = 5 * study.HOUR if source == "histdata" else 0
        return [{"sequence": i, "time_msc": study.prior.epoch(day) + offset,
                 "bid": 1.1 + i * .001, "ask": 1.1001 + i * .001}
                for i, day in enumerate(("20241025", "20241028"))]

    def test_scoped_offsets_preserve_quotes_and_sequence(self):
        for source, shifts in (("histdata", (4, 5)), ("broker", (-3, -2))):
            ticks = self.ticks(source)
            actual = list(study.interval_ticks(ticks, source))
            for i, day in enumerate(("20241025", "20241028")):
                self.assertEqual(actual[i]["time_msc"], study.prior.epoch(day) + shifts[i] * study.HOUR)
                for key in ("sequence", "bid", "ask"):
                    self.assertEqual(actual[i][key], ticks[i][key])
            self.assertLess(actual[0]["time_msc"], actual[1]["time_msc"])

    def test_observed_quote_inside_quiet_period_rejects_mapping(self):
        for source in ("histdata", "broker"):
            tick = self.ticks(source)[0]
            tick["time_msc"] = study.limits(source)[0] + (5 * study.HOUR if source == "histdata" else 0)
            with self.assertRaisesRegex(ValueError, "quiet interval"):
                list(study.interval_ticks([tick], source, require_sides=False))

    def test_ambiguous_cutoff_outside_empty_interval_is_rejected(self):
        for source in ("histdata", "broker"):
            with self.assertRaisesRegex(ValueError, "Cutoff"):
                list(study.interval_ticks(self.ticks(source), source, cutoff=study.limits(source)[1]))

    def test_any_cutoff_within_empty_interval_maps_observed_quotes_identically(self):
        for source in ("histdata", "broker"):
            lower, upper = study.limits(source)
            a = list(study.interval_ticks(self.ticks(source), source, cutoff=lower))
            b = list(study.interval_ticks(self.ticks(source), source, cutoff=upper - 1))
            self.assertEqual(a, b)

    def test_same_millisecond_quotes_keep_order_and_are_not_collapsed(self):
        ticks = self.ticks("histdata")
        ticks.insert(1, {**ticks[0], "sequence": 1, "bid": 1.10001})
        ticks[2]["sequence"] = 2
        result = list(study.interval_ticks(ticks, "histdata"))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["time_msc"], result[1]["time_msc"])
        self.assertEqual(result[1]["bid"], 1.10001)

    def test_missing_side_bad_sequence_order_and_other_month_are_rejected(self):
        ticks = self.ticks("broker")
        with self.assertRaisesRegex(ValueError, "Missing quotes"):
            list(study.interval_ticks(ticks[:1], "broker"))
        for bad in ([{**ticks[0], "sequence": 1}, ticks[1]],
                    [{**ticks[0], "time_msc": study.prior.epoch("20240930")}, ticks[1]],
                    [{**ticks[1], "sequence": 0}, {**ticks[0], "sequence": 1}]):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                list(study.interval_ticks(bad, "broker"))

    def test_price_agreement_does_not_rescue_missing_or_failed_event(self):
        comparisons = {d: {"passed": True} for d in ("20241024", "20241025", "20241028")}
        events = {d: {"histdata": {"passed": True}, "broker": {"passed": True}}
                  for d in ("20241024", "20241029")}
        self.assertTrue(study.passed(events, comparisons, True))
        self.assertFalse(study.passed(events, comparisons, False))
        self.assertFalse(study.passed({}, comparisons, True))
        events["20241024"]["broker"]["passed"] = False
        self.assertFalse(study.passed(events, comparisons, True))

    def test_failed_evidence_prevents_dataset_construction(self):
        with patch.object(study.prior, "load", return_value={"protocol_sha256": "same", "passed": False}), \
                patch.object(study, "sha256", return_value="same"), patch.object(study, "build") as build:
            with self.assertRaisesRegex(ValueError, "blocks dataset"):
                study.build_dataset()
            build.assert_not_called()
