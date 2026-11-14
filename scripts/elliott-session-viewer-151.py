"""Export a local read-only viewer from a saved invented session149 EW account."""
import argparse
import json

from forex_demo_lab.elliott_session_viewer_151 import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="existing session149 prepared partition directory")
    parser.add_argument("output", help="new directory outside the prepared directory")
    parser.add_argument("--profile", choices=("base", "adverse"), default="base")
    args = parser.parse_args()
    result = export(args.directory, args.output, args.profile)
    print(json.dumps({k: result[k] for k in ("version", "rows", "profile", "partition", "orders_available")}))


if __name__ == "__main__":
    main()
