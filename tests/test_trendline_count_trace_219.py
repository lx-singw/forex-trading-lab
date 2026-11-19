"""Historical count frames preserve the replay's strategy and cost totals."""

import unittest
from unittest.mock import patch

from forex_demo_lab.trendline import breaks, context, signal_count
from test_trendline_signal_count_194 import bar_fixture, count_b


class CountTraceTests(unittest.TestCase):
    def test_compact_trace_matches_full_trace_across_strategies_and_costs(self):
        source, rows, opening = bar_fixture()
        options = {"cutoff": opening["available_at"], "profiles": signal_count.PROFILES, "costs": signal_count.COSTS}
        full = count_b(source, rows, **options)

        def compact_setups(declaration, bars, tick, profile):
            replay = breaks.BreakReplay(declaration, tick, profile, count_only=True)
            frames = ("D1", "H4") if profile in (context.PROFILE, breaks.FXR_PROFILE) else ("H4",)
            for bar in bars:
                if bar.timeframe in frames:
                    replay.observe(bar)
            report = replay.report()
            for frame in report["action_replay"]["frames"]:
                self.assertNotIn("pair_rejections", frame)
            with self.assertRaisesRegex(ValueError, "use a full replay"):
                replay.checkpoint()
            return report

        with patch.object(signal_count, "_setups", side_effect=compact_setups):
            compact = count_b(source, rows, **options)
        self.assertEqual(full["cells"], compact["cells"])
