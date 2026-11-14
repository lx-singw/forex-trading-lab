"""Explicit data-quality gate, immutable freeze and offline tick strategy replay."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.tick_workflow import freeze, evaluate

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("action",choices=("freeze","run"))
parser.add_argument("--dataset",type=Path,required=True)
parser.add_argument("--quality",type=Path,required=True)
parser.add_argument("--manifest",type=Path,required=True)
parser.add_argument("--config",type=Path)
parser.add_argument("--output",type=Path)
args=parser.parse_args()
try:
    if args.action=="freeze":
        if not args.config:parser.error("freeze requires config")
        freeze(args.dataset,args.config,args.quality,args.manifest)
        print("Frozen development tick experiment")
    else:
        if not args.output:parser.error("run requires output")
        result=evaluate(args.dataset,args.manifest,args.quality,args.output)
        print(result["status"])
except (ValueError,OSError,KeyError) as error:
    parser.exit(2,f"Tick experiment stopped: {error}\n")
