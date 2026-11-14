"""Draft/freeze/check study metadata without price, terminal or order access."""
import argparse
import json
from forex_demo_lab import elliott_study_145 as study


def main():
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest='command',required=True)
    draft=commands.add_parser('draft');draft.add_argument('output')
    freeze=commands.add_parser('freeze');freeze.add_argument('plan');freeze.add_argument('manifest')
    check=commands.add_parser('preflight');check.add_argument('plan');check.add_argument('manifest');check.add_argument('output')
    args=parser.parse_args()
    if args.command=='draft':
        study.write(args.output,study.draft());result={'status':'UNASSIGNED_METADATA_DRAFT','orders_available':False}
    elif args.command=='freeze':
        study.freeze(args.plan,args.manifest);result={'status':'FROZEN_METADATA_NOT_ADMISSION','orders_available':False}
    else:
        report=study.run(args.plan,args.manifest,args.output)
        result={k:report[k] for k in ('status','planned_cells','market_cells_run','market_data_read','orders_available')}
    print(json.dumps(result))


if __name__=='__main__':main()
