"""Windows entry point: read existing terminal history; never place orders."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_demo_lab.collection import capture
from forex_demo_lab.model import timestamp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True, help="Exclusive end timestamp")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        parser.exit(2, "Use Windows Python for the MT5 IPC collector.\n")
    # Refuse a new terminal launch. Enumerate only executable paths, never account data.
    status = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                             "ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })"],
                            capture_output=True, text=True, check=True, timeout=15)
    paths = json.loads(status.stdout)
    if os.path.normcase(str(args.terminal.resolve())) not in [os.path.normcase(p) for p in paths if p]:
        parser.exit(2, "The specified terminal must already be running.\n")
    import MetaTrader5 as mt5
    try:
        if not mt5.initialize(str(args.terminal), timeout=15000):
            raise ValueError("Could not connect to the running terminal; details intentionally not logged")
        metadata = capture(mt5, timestamp(args.start), timestamp(args.end), args.output,
                           progress=lambda message: print(message, flush=True))
        print(json.dumps({k: metadata[k] for k in ("rows", "first_bar", "last_bar", "clock_observation", "current_snapshot")}, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Capture stopped: {exc}\n")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
