"""Freeze or replay invented raw quotes through unchanged control strategies."""
import argparse
import json
from forex_demo_lab.elliott_full.controls import freeze, evaluate


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    declaration = commands.add_parser("freeze")
    declaration.add_argument("input")
    declaration.add_argument("manifest")
    replay = commands.add_parser("replay")
    replay.add_argument("input")
    replay.add_argument("manifest")
    replay.add_argument("output")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.input, args.manifest)
        print(json.dumps({"status": "invented_controls_frozen", "orders_available": False}))
    else:
        result = evaluate(args.input, args.manifest, args.output)
        print(json.dumps({k: result[k] for k in ("computed_control_cells", "market_cells_run", "orders_available")}))


if __name__ == "__main__":
    main()
