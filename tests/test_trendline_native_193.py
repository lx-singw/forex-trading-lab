"""Compile the disabled native contract and exercise it with invented inventory."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPILER = shutil.which("g++")


@unittest.skipUnless(COMPILER, "g++ is required for the native contract fault tests")
class TrendlineNativeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary_folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(binary_folder.cleanup)
        cls.binary = Path(binary_folder.name) / "trendline-native-193"
        source = ROOT / "mt5" / "Tests" / "TrendlineExecution193.cpp"
        compile_result = subprocess.run([COMPILER, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                                         str(source), "-o", str(cls.binary)], capture_output=True, text=True)
        if compile_result.returncode:
            raise AssertionError(compile_result.stderr)

    def exercise(self, *scenarios):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "fixture-state"
            for scenario in scenarios:
                result = subprocess.run([str(self.binary), scenario, str(journal)], capture_output=True,
                                        text=True, timeout=10)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(f"{scenario} passed", result.stdout.strip())
                # The record carries transition numbers only. Account continuity is in memory.
                fields = journal.read_text().split()
                self.assertEqual(13, len(fields))
                self.assertTrue(all(field.lstrip("-").isdigit() for field in fields))

    def test_demo_enum_and_continuity_checked_again_for_every_action(self):
        self.exercise("accounts")

    def test_disabled_route_level_q_loss_pause_size_and_persisted_single_use_offer(self):
        self.exercise("gates")

    def test_partial_fill_owned_quantity_and_protection_on_both_sides(self):
        self.exercise("partial")

    def test_missing_protection_cancels_first_then_closes_and_keeps_halt(self):
        self.exercise("emergency")

    def test_restart_after_durable_intent_before_send_needs_flat_evidence(self):
        self.exercise("prepare-before", "recover-flat")

    def test_restart_after_ambiguous_send_reconciles_partial_without_resending(self):
        self.exercise("prepare-after", "recover-partial")
