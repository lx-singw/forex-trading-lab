"""Record bounded research eligibility; never authorize forward execution."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.cli import write_json
from forex_demo_lab.research_data import compare_hourly
from forex_demo_lab.tick_audit import sha256

root=Path("data")
clock=Path("reports/cpi-clock-004.json")
clock_ok=json.loads(clock.read_text())["status"]=="empirical_new_york_clock_supported"
jan=root/"research-004-january-mt5"
reference=root/"histdata-development-003-january"
ref=json.loads((reference/"provenance.json").read_text())
if sha256(reference/"hourly-diagnostic.csv")!=ref["hourly_sha256"]:raise ValueError("Reference bars changed")
lower=int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp())//3600
upper=int(datetime(2024,2,1,tzinfo=timezone.utc).timestamp())//3600
comparison=compare_hourly(jan/"hourly-diagnostic.csv",reference/"hourly-diagnostic.csv",lower,upper)
price_ok=(comparison["reference_hours"]>500 and not comparison["missing_reference_hours"]
          and comparison["within_one_pip_fraction"]>=.95 and comparison["maximum_close_difference_pips"]<=5)
datasets=[]
for scenario in ("january-mt5","july-new-york","july-fixed-est"):
    folder=root/f"research-004-{scenario}"
    p=json.loads((folder/"provenance.json").read_text())
    if sha256(folder/"ticks.csv.gz")!=p["data_sha256"] or sha256(folder/"hourly-diagnostic.csv")!=p["hourly_sha256"]:
        raise ValueError("Research dataset changed")
    gaps=[g for g in p["gaps_over_one_hour"] if g["classification"]=="unresolved"]
    passed=clock_ok and price_ok and not gaps
    datasets.append({"scenario":scenario,"provenance_sha256":sha256(folder/"provenance.json"),
                     "ticks":p["ticks"],"observed_hours":p["observed_hours"],"unresolved_large_gaps":gaps,
                     "status":"ready_for_development_research" if passed else "blocked_data_quality"})
report={"status":"bounded_provisional_research_eligible" if all(d["status"]=="ready_for_development_research" for d in datasets) else "blocked_data_quality",
        "performance_evaluation_ready":all(d["status"]=="ready_for_development_research" for d in datasets),
        "demo_execution_ready":False,"datasets":datasets,"january_comparison":comparison,
        "clock_evidence_sha256":sha256(clock),"protocol_sha256":sha256(Path("docs/RESEARCH-004-PLAN.md")),
        "scope":"Explicit provisional development simulation, not validation of profitability or broker conditions",
        "clock_caveat":"Empirical New York hypothesis is uncertified; documented fixed-EST July is retained as sensitivity",
        "not_superseded":"003 candidates and their failed gate remain unchanged and blocked"}
write_json(Path("reports/research-quality-004.json"),report)
print(json.dumps(report,indent=2))
