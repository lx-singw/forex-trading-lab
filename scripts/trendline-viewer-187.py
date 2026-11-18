"""Export an offline viewer from saved invented Level B or Q ledger reports."""
import argparse
import json

from forex_demo_lab.trendline.replay_viewer import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor", help="Level B source descriptor or Level Q quote tape")
    parser.add_argument("report_directory", help="saved Level B --ledger or Level Q quote replay directory")
    parser.add_argument("new_output_directory", help="location for replay.html and its manifest")
    parser.add_argument("--unlock-receipt", help="matching invented Level Q validation receipt")
    args = parser.parse_args()
    result = export(args.descriptor, args.report_directory, args.new_output_directory,
                    unlock_receipt=args.unlock_receipt)
    print(json.dumps({key: result[key] for key in ("profile", "data_level", "partition", "receipt_groups")}))


if __name__ == "__main__":
    main()
