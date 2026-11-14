"""Bounded read-only January research capture through the guarded collector CLI."""
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path("data/mt5-january-004-chunks")
root.mkdir(parents=True,exist_ok=False)
start=datetime(2024,1,1,2,tzinfo=timezone.utc)
end=datetime(2024,2,1,2,tzinfo=timezone.utc)
windows=[]
while start<end:
    stop=min(start+timedelta(hours=48),end)
    folder=root/f"chunk-{len(windows):02d}"
    subprocess.run([sys.executable,str(Path(__file__).with_name("capture-ticks.py")),
                    "--terminal",r"C:\Program Files\MetaTrader 5\terminal64.exe",
                    "--start",start.isoformat(),"--end",stop.isoformat(),"--output",str(folder)],check=True)
    metadata=json.loads((folder/"capture.json").read_text())
    if not metadata["requests_without_api_errors"]:raise ValueError("Capture API failure; month not published")
    windows.append({"folder":folder.name,"capture_sha256":hashlib.sha256((folder/"capture.json").read_bytes()).hexdigest(),"ticks":metadata["ticks"]})
    start=stop
manifest={"kind":"bounded_mt5_month_capture","month":"202401","source_label_offset_hours":2,
          "source_label_start":"2024-01-01T02:00:00+00:00","source_label_end_exclusive":"2024-02-01T02:00:00+00:00",
          "offset_basis":"Empirical January comparison and event anchoring; not year-wide certification",
          "windows":windows,"ticks":sum(w["ticks"] for w in windows),"complete_market_history_verified":False}
(root/"month.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(f"January capture complete: {manifest['ticks']} ticks",flush=True)
