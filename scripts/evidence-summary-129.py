"""Summarize pinned existing diagnostics read-only; no MT5 or broker connection."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.evidence_summary_129 import build_summary, load_manifest, render_markdown

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?", default=ROOT / "config/evidence-summary-129.json")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    try:
        report = build_summary(load_manifest(args.manifest), args.root)
        output = render_markdown(report) if args.format == "markdown" else json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
    except (ValueError, OSError, OverflowError):
        print(json.dumps({"accepted": False, "reason": "invalid_or_unreadable_evidence_inputs"}))
        sys.exit(1)
    print(output)
