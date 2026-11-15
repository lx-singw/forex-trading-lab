"""Default-off recorder boundary; optional fixed invented exercise only."""
import argparse
import json

from forex_demo_lab.paired_replay_133 import DENIED
from forex_demo_lab.recorder_fixture_155 import exercise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise-invented',action='store_true')
    parser.add_argument('--output')
    args=parser.parse_args()
    if not args.exercise_invented:
        result=dict(schema='recorder155_off',enabled=False,native_source_available=False,
                    native_helper_launched=False,actual_account_queried=False,actual_quotes_read=False,collection_dates=None,**DENIED)
    else:
        if args.output is None:parser.error('invented exercise requires a new output directory')
        report=exercise(args.output)
        result=dict(schema=report['schema'],invented_cases=len(report['cases']),native_source_available=False,
                    native_helper_launched=False,actual_quotes_read=False,collection_dates=None,**DENIED)
    print(json.dumps(result))


if __name__=='__main__':main()
