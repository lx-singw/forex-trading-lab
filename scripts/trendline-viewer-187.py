"""Export an offline viewer from saved invented Level B ledger reports."""
import argparse
import json

from forex_demo_lab.trendline.replay_viewer import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor", help="source descriptor used to generate the reports")
    parser.add_argument("report_directory", help="saved Level B replay made with --ledger")
    parser.add_argument("new_output_directory", help="location for replay.html and its manifest")
    args = parser.parse_args()
    result = export(args.descriptor, args.report_directory, args.new_output_directory)
    print(json.dumps({key: result[key] for key in ("profile", "data_level", "partition", "receipt_groups")}))


if __name__ == "__main__":
    main()
