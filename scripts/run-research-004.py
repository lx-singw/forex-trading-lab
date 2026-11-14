"""Freeze all declared scenarios before any performance is computed."""
import argparse
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.tick_workflow import freeze,evaluate
from forex_demo_lab.tick_audit import sha256
from forex_demo_lab.cli import write_json,code_digest

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("action",choices=("freeze","run"))
args=parser.parse_args()
quality=Path("reports/research-quality-004.json")
scenarios=[(month,cost) for month in ("january-mt5","july-new-york","july-fixed-est") for cost in ("base","adverse")]
if args.action=="freeze":
    for month,cost in scenarios:
        config=Path("config/tick-pilot-003.json" if cost=="base" else "config/tick-pilot-003-adverse.json")
        freeze(Path(f"data/research-004-{month}"),config,quality,Path(f"reports/research-004-{month}-{cost}-manifest.json"))
        print(f"Frozen {month} / {cost}",flush=True)
    archive=Path("reports/research-004-source.zip")
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED) as z:
        for root in (Path("src"),Path("scripts"),Path("tests")):
            for path in sorted(root.rglob("*.py")):z.write(path,path.as_posix())
        for path in (Path("config/tick-pilot-003.json"),Path("config/tick-pilot-003-adverse.json"),Path("docs/RESEARCH-004-PLAN.md")):
            z.write(path,path.as_posix())
    write_json(Path("reports/research-004-freeze.json"),{"source_archive_sha256":sha256(archive),"code_sha256":code_digest(),
                "quality_sha256":sha256(quality),"manifests":{f"{m}-{c}":sha256(Path(f"reports/research-004-{m}-{c}-manifest.json")) for m,c in scenarios}})
else:
    frozen=json.loads(Path("reports/research-004-freeze.json").read_text())
    if frozen["code_sha256"]!=code_digest() or frozen["quality_sha256"]!=sha256(quality):raise ValueError("Frozen research changed")
    if frozen["source_archive_sha256"]!=sha256(Path("reports/research-004-source.zip")):raise ValueError("Source archive changed")
    # Validate every frozen scenario before starting any evaluation.
    for month,cost in scenarios:
        if frozen["manifests"][f"{month}-{cost}"]!=sha256(Path(f"reports/research-004-{month}-{cost}-manifest.json")):
            raise ValueError("Scenario manifest changed")
    for month,cost in scenarios:
        result=evaluate(Path(f"data/research-004-{month}"),Path(f"reports/research-004-{month}-{cost}-manifest.json"),
                        quality,Path(f"reports/research-004-{month}-{cost}.json"))
        print(json.dumps({"scenario":f"{month}-{cost}","metrics":result["metrics"]}),flush=True)
