"""Create/freeze/check explicitly named trendline metadata; no price inputs."""
import argparse
import json

from forex_demo_lab.trendline import data, study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command",required=True)
    draft = commands.add_parser("draft");draft.add_argument("output")
    freeze = commands.add_parser("freeze");freeze.add_argument("plan");freeze.add_argument("output")
    check = commands.add_parser("check");check.add_argument("plan");check.add_argument("freeze");check.add_argument("output")
    args = parser.parse_args()
    if args.command == "draft":
        data.write_new(args.output,study.draft())
    elif args.command == "freeze":
        study.freeze(args.plan,args.output)
    else:
        result = study.run(args.plan,args.freeze,args.output)
        print(json.dumps({"status":result["status"],"planned_cells":28,"market_cells_run":0,"orders_available":False}))


if __name__ == "__main__":
    main()
