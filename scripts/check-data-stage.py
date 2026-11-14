"""Stop the ordered research workflow when either predeclared clock check fails."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256


def evaluate(winter, summer, original_failure=None):
    original = None
    if original_failure:
        original = json.loads(original_failure.read_text())
        if original.get("status") != "blocked_clock_discrepancy":
            raise ValueError("Amendment must retain the original failed check")
    checks = []
    for season, path, offset in (("winter",winter,2),("summer",summer,2 if original else 3)):
        report = json.loads(path.read_text())
        checks.append({"season":season, "report_sha256":sha256(path),
                       "histdata_archive_sha256":report.get("histdata_archive_sha256"),
                       "status":report["status"], "expected_offset":report["expected_offset"],
                       "passes_predeclared_check":report["status"] == "sample_corroborated" and report["expected_offset"] == offset})
    passed = all(c["passes_predeclared_check"] for c in checks)
    return {"stage":1,"status":"sample_checks_passed" if passed else "blocked_clock_discrepancy",
            "original_failed_gate_sha256":sha256(original_failure) if original_failure else None,
            "protocol":"fresh_fixed_offset_amendment" if original else "initial_seasonal_hypothesis",
            "checks":checks, "dataset_construction_ready":passed,
            "strategy_evaluation_ready":False, "demo_execution_ready":False,
            "next_action":"Review sample limits before dataset construction" if passed else
                "Resolve summer historical timestamp convention using additional independent evidence; preserve failed hypothesis",
            "limitation":"This gate summarizes local diagnostic reports; it is not market-feed certification or execution authorization"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--winter",type=Path,required=True)
    parser.add_argument("--summer",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--original-failed-gate",type=Path)
    args = parser.parse_args()
    result = evaluate(args.winter,args.summer,args.original_failed_gate)
    write_json(args.output,result)
    print(result["status"])
    if not result["dataset_construction_ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
