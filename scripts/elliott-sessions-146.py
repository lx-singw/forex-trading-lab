"""Run the embedded invented calendar example; accepts no external price input."""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from forex_demo_lab import elliott_sessions_146 as s
from forex_demo_lab.elliott_full.contracts import Bar, digest


def demonstration():
    cursor = s.START+22*s.HOUR
    start = cursor
    rows = []
    for i, hours in enumerate((23, 25)):
        end = cursor+hours*s.HOUR
        rows.append({"kind": "session", "label": f"session_demo_{i}", "start": cursor, "end": end,
                     "h1": list(range(cursor, end, s.HOUR))+[end],
                     "h4": list(range(cursor, end, 4*s.HOUR))+[end], "partial": False})
        cursor = end
        if i == 0:
            rows.append({"kind": "closure", "start": cursor, "end": cursor+48*s.HOUR, "reason": "invented"})
            cursor += 48*s.HOUR
    declared = {"kind": "invented_session_calendar_146", "scope": {"start": start, "end": cursor},
                "finalization_delay_ms": 2000, "segments": rows}
    calendar = s.Calendar.from_record(declared)
    # Capture schedule/source identity before generating any invented prices.
    freeze = {"kind": "invented_component_freeze_not_admission", "calendar": declared,
              "calendar_sha256": calendar.sha256, "source_bindings": s.source_bindings()}
    stream = s.Observations(calendar)
    windows = calendar.frame("H1")

    def observation(index, available=None):
        w = windows[index];p = Decimal("1.1")+Decimal(index)/10000
        return Bar("H1", w.start, w.end, w.end+2000 if available is None else available,
                   p, p+Decimal(".0003"), p-Decimal(".0002"), p+Decimal(".0001"),
                   digest(["invented_demo", index, w.start]))

    late_index = 24
    for i in range(len(windows)):
        if i != late_index:stream.observe(observation(i))
    before = stream.report();checkpoint = stream.checkpoint()
    restarted = s.Observations.restore(calendar, checkpoint)
    late = observation(late_index, calendar.end+5000)
    stream.observe(late);restarted.observe(late)
    return {"schema": s.VERSION, "kind": "invented_session_demonstration_only",
            "freeze": freeze, "before_late_child": before, "checkpoint": checkpoint,
            "after_late_child": stream.report(), "restart_equal": stream.report() == restarted.report(),
            "orders_available": False, "market_cells_run": 0, "returns_computed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = demonstration()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output/"demonstration.json").open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(json.dumps({k: result[k] for k in ("kind", "restart_equal", "orders_available", "market_cells_run")}))


if __name__ == "__main__":main()
