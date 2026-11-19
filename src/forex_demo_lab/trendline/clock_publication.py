"""Model weekend H4 publication from invented source-time-only quotes."""

import argparse

from ..elliott_sessions_146 import Calendar
from . import data, opening_evidence, quotes, weekend_publication

KIND = "invented_clock_publication_source"


def audit(source, *, as_of):
    data.fields(source, ("kind", "calendar", "h4_end", "assumed_delivery_delay_ms", "quotes"))
    if source["kind"] != KIND:
        raise ValueError("invented source-time-only quote document required")
    calendar = Calendar.from_record(source["calendar"])
    delay = source["assumed_delivery_delay_ms"]
    data.integer(delay)
    opening_window = weekend_publication.weekend_opening(calendar, source["h4_end"])
    trigger = next(window for window in calendar.frame("H4") if window.end == source["h4_end"])
    if type(source["quotes"]) is not list or not 1 <= len(source["quotes"]) <= data.ROW_LIMIT:
        raise ValueError("bounded nonempty source-time-only quote list required")

    # Sealing before the assumed delivery bound would exclude trailing source
    # quotes. The same grace applies to every child and parent in this model.
    finalization = max(calendar.delay, delay)
    model_calendar = {**calendar.record(), "finalization_delay_ms": finalization}
    rows = []
    for sequence, row in enumerate(source["quotes"], start=1):
        data.fields(row, ("source_at", "bid", "ask"))
        data.integer(row["source_at"])
        rows.append({**row, "received_at": row["source_at"] + delay, "sequence": sequence})
    tape = quotes.Tape({
        "schema": quotes.VERSION, "kind": quotes.KIND, "symbol": "EURUSD",
        "data_level": "Q", "geometry_basis": "mid_sync", "partition": "development",
        "calendar": model_calendar, "liquidation_at": calendar.end - 1, "quotes": rows,
    })
    published = {(bar.timeframe, bar.start): bar for bar in tape.publications(tape.prefix(as_of), as_of)}
    parent = published.get(("H4", trigger.start))
    opening = next((row.record() for row in opening_evidence.inspect(tape, as_of=as_of)
                    if row.window.start == opening_window.start), None)
    return {
        "kind": "invented_clock_publication_audit", "original_calendar_sha256": calendar.sha256,
        "modeled_calendar_sha256": tape.calendar.sha256, "as_of": as_of,
        "market_source_admitted": False, "qualified_receipt_evidence": False,
        "assumed_delivery_delay_ms": delay, "effective_finalization_delay_ms": finalization,
        "scheduled_h1_open": opening_window.start, "modeled_opening_evidence": opening,
        "h4": {"start": trigger.start, "end": trigger.end, "due_at": trigger.end + finalization,
               "unpublished_children": [start for start in trigger.children if ("H1", start) not in published],
               "modeled_available_at": parent.available if parent is not None else None,
               "midpoint_publication_sha256": parent.lineage if parent is not None else None},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="invented source-time-only EURUSD JSON")
    parser.add_argument("output", help="new JSON report path")
    parser.add_argument("--as-of", required=True, type=int, help="inclusive modeled receipt cutoff in epoch ms")
    args = parser.parse_args()
    source, input_sha256 = data.read_json(args.source)
    data.write_new(args.output, {**audit(source, as_of=args.as_of), "input_sha256": input_sha256})


if __name__ == "__main__":
    main()
