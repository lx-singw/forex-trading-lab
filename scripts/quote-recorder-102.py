"""Offline invented bid/ask journal demo or local integrity inspection."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.quote_recorder_102 import Recorder, invented_events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Create invented journal and demonstrate restart").add_argument("output", type=Path)
    commands.add_parser("inspect", help="Verify a local synthetic journal").add_argument("input", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        events = invented_events()
        with Recorder.create(args.output) as recorder:
            for quote, received in events[:7]:
                recorder.record(quote, received)
        with Recorder.resume(args.output) as recorder:
            for quote, received in events[7:]:
                recorder.record(quote, received)
            report = recorder.summary()
        report["restart_demonstrated"] = True
    else:
        with Recorder.resume(args.input) as recorder:
            report = recorder.summary()
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
