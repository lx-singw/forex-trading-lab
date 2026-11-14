"""Bounded read-only MT5 tick capture; no order submission or terminal changes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.model import timestamp
from forex_demo_lab.tick_audit import capture_ticks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal", type=Path, required=True)
    parser.add_argument("--start", required=True, help="Raw source-clock label, with UTC-format suffix")
    parser.add_argument("--end", required=True, help="Exclusive raw source-clock label, at most 48h after start")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        parser.exit(2, "Run with the isolated Windows MT5 Python environment.\n")
    running = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                              "ConvertTo-Json -Compress -InputObject @(Get-Process terminal64 -ErrorAction SilentlyContinue | ForEach-Object { $_.Path })"],
                             capture_output=True, text=True, check=True, timeout=15)
    if os.path.normcase(str(args.terminal.resolve())) not in [os.path.normcase(p) for p in json.loads(running.stdout) if p]:
        parser.exit(2, "The specified terminal must already be running.\n")
    import MetaTrader5 as mt5
    try:
        if not mt5.initialize(str(args.terminal), timeout=15000):
            raise ValueError("Read-only connection failed")
        result = capture_ticks(mt5, timestamp(args.start), timestamp(args.end), args.output,
                               progress=lambda message: print(message, flush=True))
        print(json.dumps({k: result[k] for k in ("ticks", "requests_without_api_errors", "complete_market_history_verified")}, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Tick capture stopped: {exc}\n")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
