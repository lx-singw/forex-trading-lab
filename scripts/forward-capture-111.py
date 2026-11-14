"""Inspect a closed111 run directory read-only. Does not launch MT5."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.forward_capture_111 import inspect_run,summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory',type=Path)
    args=parser.parse_args()
    try:result=summary(inspect_run(args.run_directory))
    except (ValueError,OSError):
        print(json.dumps({'accepted':False,'reason':'invalid_or_unreadable_run'}))
        sys.exit(1)
    print(json.dumps(result,sort_keys=True,indent=2))
