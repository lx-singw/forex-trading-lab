"""Package guards/recovery/report tests; economics reference the frozen122 matrix."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab import engine_demo_123 as demo

D = demo.daily
REFERENCE = D.ROOT / "data/daily-runs-122-invented-demo"


def read(path):
    return D._json(path.read_bytes())


def rewrite(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def stored_reports(root):
    return [read(root / c / "run/run-report.json") for c in demo.CASES]


def prepared(root):
    root.mkdir()
    inputs = {}
    for case in demo.CASES:
        d = root / case
        d.mkdir()
        for name, original in (("input.json", f"{case}.json"), ("frozen.json", f"{case}-frozen.json")):
            shutil.copyfile(REFERENCE / original, d / name)
        inputs[case] = {"input_sha256": demo._sha(d / "input.json"), "manifest_sha256": demo._sha(d / "frozen.json")}
    D.write_new(root / "package-frozen.json", {"format": demo.VERSION, "kind": "fixed_invented_demo_package",
        "cases": list(demo.CASES), "sources": demo.source_bindings(), "inputs": inputs,
        "readiness": demo.readiness(), "capabilities": demo.capability_audit(),
        "orders_available": False, "real_money_execution_available": False})
    records, previous = [], None
    previous = demo._checkpoint(root, demo._sha(root / "package-frozen.json"), records, previous)
    for case in demo.CASES:
        d, original = root / case, REFERENCE / f"{case}-run"
        shutil.copytree(original, d / "run")
        for i, name in enumerate(("checkpoint-initial.json", "checkpoint-development.json", "run-checkpoint.json")):
            shutil.move(d / "run" / name, d / f"checkpoint-{i}.json")
        records.append({"case": case, "files": demo._case_files(d)})
        previous = demo._checkpoint(root, demo._sha(root / "package-frozen.json"), records, previous)
    overview = demo._overview(stored_reports(root), demo._sha(root / "package-frozen.json"), demo.readiness())
    D.write_new(root / "overview.json", overview)
    demo._write_or_match(root / "REPORT.md", demo.render(overview, "../" * len(root.relative_to(D.ROOT).parts)), text=True)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.TemporaryDirectory(prefix="engine-demo-123-tests-", dir=D.ROOT / "data")
        cls.seed = Path(cls.home.name) / "seed"
        prepared(cls.seed)

    @classmethod
    def tearDownClass(cls):
        cls.home.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=self.home.name)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(self.seed, self.root)
        overview = read(self.root / "overview.json")
        (self.root / "REPORT.md").write_text(demo.render(overview, "../" * len(self.root.relative_to(D.ROOT).parts)))

    def tearDown(self):
        self.temp.cleanup()

    def progress(self):
        return demo._progress(self.root, demo._sha(self.root / "package-frozen.json"))

    def test_reviewed_dependency_graph_has_no_broker_or_process_imports(self):
        audit = demo.capability_audit()
        self.assertEqual(audit["network_process_broker_imports"], [])
        self.assertFalse(audit["actual_order_api_present"])
        self.assertEqual(len(audit["runtime_bindings"]), 12)
        self.assertIn("src/forex_demo_lab/__init__.py", audit["runtime_bindings"])

    def test_unexpected_imports_and_dynamic_execution_reject(self):
        for code in ("import socket", "import subprocess", "import MetaTrader5", "from . import execution",
                     "from .. import daily_features_118", "eval('1')", "__import__('socket')", "mt5.order_send({})"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                demo._review_python(code)

    def test_readiness_does_not_promote_flags_or_boolean_cell_counts(self):
        original_read = D._read
        inventory = demo.readiness()
        for key, value in (("orders_available", True), ("market_data_qualified", 0), ("market_cells_run", False),
                           ("market_cells_assigned", 1), ("actual_account_type_lookup_performed", True)):
            bad = deepcopy(inventory)
            bad[key] = value
            def substitute(path):
                return json.dumps(bad).encode() if Path(path).name == "engine-readiness-123.json" else original_read(path)
            with self.subTest(key=key), patch.object(D, "_read", substitute), self.assertRaises(ValueError):
                demo.readiness()

    def test_readiness_requires_fixed_cited_documents(self):
        original_read = D._read
        bad = demo.readiness()
        bad["market_requirements"][0]["evidence"] = "../../other-project/secret"
        with patch.object(D, "_read", lambda p: json.dumps(bad).encode() if Path(p).name == "engine-readiness-123.json" else original_read(p)):
            with self.assertRaisesRegex(ValueError, "readiness_evidence"):
                demo.readiness()

    def test_new_output_outside_repository_data_rejects(self):
        with self.assertRaisesRegex(ValueError, "package_output_under_repository_data_required"):
            demo.create(D.ROOT / "other-output")
        self.assertFalse((D.ROOT / "other-output").exists())

    def test_symlink_root_rejects(self):
        link = Path(self.temp.name) / "linked"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "package_symlink"):
            demo._root(link)

    def test_fixed_manifest_and_all_input_sources_validate(self):
        manifest = demo._manifest(self.root)
        self.assertEqual(manifest["cases"], list(demo.CASES))
        records, _ = self.progress()
        self.assertEqual(len(records), 6)

    def test_changed_source_binding_rejects(self):
        path = self.root / "package-frozen.json"
        value = read(path)
        value["sources"]["src/forex_demo_lab/model.py"] = "0" * 64
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "package_freeze_binding"):
            demo._manifest(self.root)

    def test_input_change_rejects_even_with_new_package_hash(self):
        input_path = self.root / "targets/input.json"
        value = read(input_path)
        value["stream"]["messages"][0]["bid"] += .00001
        rewrite(input_path, value)
        manifest_path = self.root / "package-frozen.json"
        manifest = read(manifest_path)
        manifest["inputs"]["targets"]["input_sha256"] = demo._sha(input_path)
        rewrite(manifest_path, manifest)
        with self.assertRaisesRegex(ValueError, "fixed_invented_input_changed"):
            demo._manifest(self.root)

    def test_manifest_cannot_enable_orders(self):
        path = self.root / "package-frozen.json"
        value = read(path)
        value["orders_available"] = True
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "package_freeze_binding"):
            demo._manifest(self.root)

    def test_duplicate_json_rejects(self):
        (self.root / "package-frozen.json").write_text('{"format":1,"format":2}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_field"):
            demo._manifest(self.root)

    def test_package_progress_gap_rejects(self):
        (self.root / "progress-002.json").unlink()
        with self.assertRaisesRegex(ValueError, "package_checkpoint_chain"):
            self.progress()

    def test_rehashed_boolean_progress_cursor_rejects(self):
        path = self.root / "progress-000.json"
        value = read(path)
        value["payload"]["cursor"] = False
        value["sha256"] = D._digest(value["payload"])
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "package_checkpoint_chain"):
            self.progress()

    def test_progress_parent_binding_rejects(self):
        path = self.root / "progress-006.json"
        value = read(path)
        value["payload"]["previous_checkpoint_sha256"] = "0" * 64
        value["sha256"] = D._digest(value["payload"])
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "package_checkpoint_chain"):
            self.progress()

    def test_modified_committed_ledger_rejects_before_replay(self):
        path = self.root / "targets/run/development-attempt00/fills-report.json"
        value = read(path)
        value["results"][0]["summary"]["toy_net_usd"] = "999"
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "package_completed_artifact_binding"):
            self.progress()

    def test_unknown_case_artifact_and_symlink_reject(self):
        path = self.root / "targets/unknown.txt"
        path.write_text("unrelated")
        with self.assertRaisesRegex(ValueError, "package_unexpected_artifact"):
            demo._manifest(self.root)
        path.unlink()
        path.symlink_to(self.root / "targets/input.json")
        with self.assertRaises(ValueError):
            demo._manifest(self.root)

    def test_all_gains_losses_cash_and_unavailable_cells_preserved(self):
        overview = read(self.root / "overview.json")
        self.assertEqual((overview["planned_toy_cells"], overview["available_accounts"], overview["unavailable_cells"]), (96, 56, 40))
        self.assertEqual(sum(c["statistics"] is None for c in overview["cells"]), 40)
        active = [c["statistics"] for c in overview["cells"] if c["statistics"]]
        self.assertTrue(any(demo.Decimal(s["toy_net_usd"]) > 0 for s in active))
        self.assertTrue(any(demo.Decimal(s["toy_net_usd"]) < -1000 for s in active))
        self.assertTrue(all(s["net_expectancy_usd"] is None for s in active if not s["trades"]))
        self.assertTrue(all(s["sample_status"] == "insufficient" for s in active))

    def test_separate_fresh_capital_and_no_portfolio_total(self):
        overview = read(self.root / "overview.json")
        self.assertFalse(overview["capital_summed_as_portfolio"])
        self.assertFalse(overview["profits_positions_pause_carried_between_partitions"])
        self.assertNotIn("total_profit", overview)
        for c in overview["cells"]:
            if c["statistics"]:
                self.assertEqual(c["statistics"]["initial_cash_usd"], "10000")
                self.assertFalse(c["statistics"]["memos_are_extra_debits"])

    def test_report_has_all_rows_costs_links_and_exact_json_is_unchanged(self):
        overview = read(self.root / "overview.json")
        before = deepcopy(overview)
        text = demo.render(overview, "../../")
        self.assertEqual(text.count("[insufficient invented sample]"), 56)
        self.assertEqual(text.count("[unavailable: "), 40)
        self.assertIn("-1001.35", text)
        self.assertIn("Gross fill P&L already embeds", text)
        self.assertIn("roughly three-hour", text)
        self.assertEqual(overview, before)

    def test_json_overview_and_readable_report_forgeries_reject_read_only(self):
        for filename, expected in (("overview.json", "package_overview_changed"), ("REPORT.md", "package_readable_report_changed")):
            path = self.root / filename
            original = path.read_bytes()
            if filename.endswith("json"):
                value = read(path)
                value["cells"][0]["statistics"]["toy_net_usd"] = "99999"
                rewrite(path, value)
            else:
                path.write_bytes(original + b"Hidden loss\n")
            before = demo._files(self.root)
            with patch.object(demo, "_completed_reports", lambda root, records: stored_reports(root)):
                with self.assertRaisesRegex(ValueError, expected):
                    demo.verify(self.root)
            self.assertEqual(demo._files(self.root), before)
            path.write_bytes(original)

    def test_real_completed_case_reconstructs_economics_without_writing(self):
        before = demo._files(self.root / "targets")
        run = demo._case_restore(self.root, "targets")
        self.assertEqual(run.report(), read(self.root / "targets/run/run-report.json"))
        self.assertEqual(demo._files(self.root / "targets"), before)

    def test_real_rehashed_economic_checkpoint_substitution_rejects(self):
        path = self.root / "targets/checkpoint-2.json"
        value = read(path)
        value["payload"]["state"]["partitions"][0]["statistics"][0]["toy_net_usd"] = "99999"
        value["sha256"] = D._digest(value["payload"])
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "checkpoint_reconstructed_state"):
            demo._case_restore(self.root, "targets")

    def test_rehashed_earlier_case_checkpoint_cannot_disagree_with_latest(self):
        path = self.root / "missing_history/checkpoint-0.json"
        value = read(path)
        value["payload"]["state"]["cursor"] = False
        value["sha256"] = D._digest(value["payload"])
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "case_checkpoint_chain"):
            demo._case_restore(self.root, "missing_history")

    def test_interrupted_attempt_resumes_once_preserving_prior_files(self):
        root = Path(self.temp.name) / "interrupted"
        original_calculate = demo.runs.Coordinator._calculate
        def interrupted(run, part, directory, write):
            D.write_new(directory / "prefix-input.json", {"interrupted": True})
            raise OSError("invented interruption")
        with patch.object(demo.runs.Coordinator, "_calculate", interrupted):
            with self.assertRaisesRegex(OSError, "invented interruption"):
                demo.create(root)
        preserved = demo._files(root / "targets/run/development-attempt00")
        # Fixed retained122 artifacts substitute only expensive calculation here;
        # real calculation/reconstruction is covered above and in the CLI demonstration.
        def fixed_calculation(run, part, directory, write):
            if not write:
                return original_calculate(run, part, directory, write)
            case = run._fixture["case"]
            original = REFERENCE / f"{case}-run" / f"{part['name']}-attempt00"
            for p in original.iterdir():
                if p.name not in {"attempt-binding.json", "partition-report.json"}:
                    shutil.copyfile(p, directory / p.name)
            result = read(original / "partition-report.json")
            result.pop("derived_files")
            return result
        with patch.object(demo.runs.Coordinator, "_calculate", fixed_calculation):
            report = demo.resume(root)
        self.assertEqual(report["available_accounts"], 56)
        self.assertEqual(demo._files(root / "targets/run/development-attempt00"), preserved)
        self.assertTrue((root / "targets/run/development-attempt01/partition-report.json").exists())
        self.assertEqual(len(demo._progress(root, demo._sha(root / "package-frozen.json"))[0]), 6)
        before = demo._files(root)
        with patch.object(demo, "_completed_reports", lambda r, records: stored_reports(r)):
            self.assertEqual(demo.resume(root), report)
        self.assertEqual(demo._files(root), before)

    def test_cli_rejects_live_options_and_existing_root_without_changes(self):
        before = demo._files(self.root)
        for arguments in (("demo", str(self.root)), ("demo", str(self.root), "--live")):
            result = subprocess.run([sys.executable, str(D.ROOT / "scripts/engine-demo-123.py"), *arguments], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(demo._files(self.root), before)


if __name__ == "__main__":
    unittest.main()
