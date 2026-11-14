"""Demonstrate or inspect the invented broker-free104 journal. No connection mode."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.snapshot_collector_104 import Clock, Collector, Frame, Guard, Journal, ReplayClock, ReplaySource, Tick


def demo(output):
    output.mkdir(parents=False, exist_ok=False)
    start = datetime(2030, 1, 7, tzinfo=timezone.utc)
    raw = int(start.timestamp() * 1000) + 10800000
    def clock(ms, origin=0):
        return Clock(start + timedelta(milliseconds=ms), (ms - origin) * 1000000)
    def tick(offset=0, bid=1.1, ask=1.1002):
        return Tick((raw + offset) // 1000, raw + offset, bid, ask, flags=1154)
    def frame(value, kind="poll_snapshot"):
        return Frame(Guard(), value, Guard(), kind)
    good = output / "observations.sqlite"
    with Journal.create(good) as j:
        source = ReplaySource([frame(tick()), frame(tick()), frame(tick(bid=1.1001))])
        c = Collector(j, source, ReplayClock([clock(ms) for ms in [0, 100, 110, 120, 200, 210, 220, 300, 310, 320, 330]]))
        for _ in range(3):
            c.poll()
        early = c.decision()["sequence"]
    with Journal.resume(good) as j:
        source = ReplaySource([frame(tick(-1000), "late_history_model"), frame(None), frame(tick(bid=1.2)),
                               frame(tick(10000)), frame(tick(10000))])
        readings = [400, 500, 510, 520, 600, 610, 620, 700, 710, 720, 800, 810, 820, 900, 910, 920, 950]
        c = Collector(j, source, ReplayClock([clock(ms, 400) for ms in readings]))
        for _ in range(5):
            c.poll()
        late = c.decision()["sequence"]
        summary = j.summary()
        summary.update(early_decision=early, early_visible=list(j.visible(early)),
                       late_decision=late, late_visible=list(j.visible(late)), restart_demonstrated=True)
    stop = output / "stopped.sqlite"
    with Journal.create(stop) as j:
        c = Collector(j, ReplaySource([Frame(Guard(), tick(), Guard(identity=b"invented-role-B"))]),
                      ReplayClock([clock(ms) for ms in [0, 100, 110, 120]]))
        c.poll()
    with Journal.resume(stop) as j:
        try:
            Collector(j, ReplaySource([]), ReplayClock([clock(200, 200)]))
            raise AssertionError("stopped model resumed")
        except ValueError:
            stopped = j.summary()
            stopped["restart_blocked"] = True
    pending = output / "pending.sqlite"
    with Journal.create(pending) as j:
        session = j.start_session(clock(0))
        j.begin_attempt(session)
    with Journal.resume(pending) as j:
        try:
            Collector(j, ReplaySource([]), ReplayClock([clock(200, 200)]))
            raise AssertionError("pending attempt resumed")
        except ValueError:
            unfinished = j.summary()
            unfinished["restart_blocked"] = True
    return dict(observations=summary, stopped=stopped, pending=unfinished,
                synthetic=True, broker_entry_available=False, market_data_qualified=False, orders_available=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Create three invented demonstration journals").add_argument("output", type=Path)
    commands.add_parser("inspect", help="Verify an invented104 local journal").add_argument("input", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        result = demo(args.output)
    else:
        with Journal.resume(args.input) as j:
            result = j.summary()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
