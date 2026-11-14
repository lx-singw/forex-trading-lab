"""Export diagnostic bid/ask bars without patching frozen research inputs."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.reconstruction import reconstruct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--raw-bars", type=Path)
    parser.add_argument("--repeat-capture", type=Path)
    args = parser.parse_args()
    try:
        report = reconstruct(args.capture, args.output, args.raw_bars, args.repeat_capture)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"Reconstruction failed: {error}\n")
    print(f"{report['rows']} diagnostic candles from {report['ticks']} ticks; not validated for backtesting")


if __name__ == "__main__":
    main()
