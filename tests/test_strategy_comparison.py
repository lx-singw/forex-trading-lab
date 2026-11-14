import importlib.util
from pathlib import Path
import tempfile
import unittest

from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256

spec = importlib.util.spec_from_file_location("comparison008", Path(__file__).resolve().parents[1] / "scripts/compare-strategies-008.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComparisonGateTests(unittest.TestCase):
    def fixture(self, root):
        folder = root / "dataset"
        folder.mkdir()
        (folder / "ticks.csv.gz").write_bytes(b"hash-test-only")
        write_json(folder / "provenance.json", {"data_sha256": sha256(folder / "ticks.csv.gz")})
        digest = sha256(folder / "provenance.json")
        return folder, digest

    def test_global_pass_does_not_rescue_blocked_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder, digest = self.fixture(root)
            quality = root / "quality.json"
            write_json(quality, {"performance_evaluation_ready": True,
                                "datasets": [{"provenance_sha256": digest, "status": "blocked_data_quality"}]})
            with self.assertRaisesRegex(ValueError, "Dataset-specific"):
                module.reviewed_dataset(folder, quality)

    def test_changed_quote_file_is_rejected_even_with_matching_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder, digest = self.fixture(root)
            quality = root / "quality.json"
            write_json(quality, {"performance_evaluation_ready": True,
                                "datasets": [{"provenance_sha256": digest, "status": "ready_for_development_research"}]})
            self.assertEqual(module.reviewed_dataset(folder, quality)["provenance_sha256"], digest)
            (folder / "ticks.csv.gz").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Dataset changed"):
                module.reviewed_dataset(folder, quality)

    def test_unreviewed_provenance_cannot_enter_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder, _ = self.fixture(root)
            quality = root / "quality.json"
            write_json(quality, {"performance_evaluation_ready": True,
                                "datasets": [{"provenance_sha256": "another-dataset", "status": "ready_for_development_research"}]})
            with self.assertRaises(ValueError):
                module.reviewed_dataset(folder, quality)
