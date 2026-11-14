"""Build distinct source/clock scenarios; no strategy evaluation in this step."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.research_data import build,mt5_month_ticks,shifted_histdata
from forex_demo_lab.tick_audit import sha256

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("scenario",choices=("january-mt5","july-new-york","july-fixed-est"))
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
evidence=Path("reports/cpi-clock-004.json")
if json.loads(evidence.read_text())["status"]!="empirical_new_york_clock_supported":
    parser.error("Fresh clock screen did not pass")
if args.scenario=="january-mt5":
    source=Path("data/mt5-january-004-chunks")
    ticks=mt5_month_ticks(source)
    origin={"kind":"normalized_mt5_ticks","source_manifest_sha256":sha256(source/"month.json"),
            "clock":"January source label minus 2 hours; empirical month-specific convention"}
else:
    source=Path("data/histdata-development-003-july")
    shift=-3600000 if args.scenario=="july-new-york" else 0
    ticks=shifted_histdata(source,shift)
    origin={"kind":"normalized_histdata_ticks","source_provenance_sha256":sha256(source/"provenance.json"),
            "clock":"July empirical New York UTC-04:00" if shift else "July documented fixed EST UTC-05:00 sensitivity"}
result=build(ticks,args.output,{**origin,"scenario":args.scenario,"clock_evidence_sha256":sha256(evidence)})
print(f"{args.scenario}: {result['ticks']} ticks, {result['observed_hours']} hours, {len(result['gaps_over_one_hour'])} gaps over an hour")
