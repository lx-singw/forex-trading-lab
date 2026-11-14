"""Build a separate development tick dataset after the source diagnostic stage."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.tick_dataset import normalize

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source",type=Path,required=True)
parser.add_argument("--output",type=Path,required=True)
parser.add_argument("--gate",type=Path,required=True)
args=parser.parse_args()
r=normalize(args.source,args.output,args.gate)
print(f"{r['ticks']} validated rows, {r['observed_hours']} observed hours, {len(r['gaps_over_one_hour'])} gaps over an hour")
