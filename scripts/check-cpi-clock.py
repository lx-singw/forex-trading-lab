"""Fresh predeclared event-clock screen; activity is evidence, not clock certification."""
import csv
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256

results=[]
for month,day,url in (("202401","20240111","https://www.bls.gov/news.release/archives/cpi_01112024.htm"),
                      ("202407","20240711","https://www.bls.gov/news.release/archives/cpi_07112024.htm")):
    folder=Path(f"data/histdata-eurusd-{month}-original")
    metadata=json.loads((folder/"download.json").read_text())
    if sha256(folder/"original.zip")!=metadata["sha256"]:raise ValueError("Archive changed")
    groups={}
    with zipfile.ZipFile(folder/"original.zip") as archive:
        with archive.open(f"DAT_ASCII_EURUSD_T_{month}.csv") as binary,io.TextIOWrapper(binary) as stream:
            for row in csv.reader(stream):
                if not row[0].startswith(day) or row[0][9:13] not in ("0730","0830"):continue
                key=row[0][9:13];bid=float(row[1])
                item=groups.setdefault(key,{"ticks":0,"high":bid,"low":bid})
                item["ticks"]+=1;item["high"]=max(item["high"],bid);item["low"]=min(item["low"],bid)
    for g in groups.values():g["range_pips"]=(g["high"]-g["low"])/.0001
    a,b=groups["0730"],groups["0830"]
    passed=b["range_pips"]>=3*a["range_pips"] and b["ticks"]>=2*a["ticks"]
    results.append({"date":day,"archive_sha256":metadata["sha256"],"official_release":url,
                    "source_minutes":groups,"screen_passed":passed})
report={"status":"empirical_new_york_clock_supported" if all(r["screen_passed"] for r in results) else "unresolved",
        "events":results,"provider_certified":False,"scope":"January and July 2024 development pilot only"}
write_json(Path("reports/cpi-clock-004.json"),report)
print(json.dumps(report,indent=2))
