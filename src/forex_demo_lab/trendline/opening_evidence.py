"""Scheduled H1 opening evidence on invented source-and-receipt tapes."""

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction

from ..elliott_full.contracts import Quote
from ..elliott_sessions_146 import Window
from . import data, fills, quotes


@dataclass(frozen=True)
class OpeningEvidence:
    window: Window
    first: Quote | None

    @property
    def status(self):
        if self.first is None:
            return "NO_QUOTE_OBSERVED"
        if self.first.source > self.window.start:
            return "FIRST_SOURCE_AFTER_OPEN"
        if self.first.time > self.window.start:
            return "BOUNDARY_QUOTE_RECEIVED_AFTER_OPEN"
        return "BOUNDARY_QUOTE_OBSERVED"

    def record(self):
        status = self.status
        row = {"start": self.window.start, "end": self.window.end, "status": status}
        if self.first is not None:
            row.update(first_source_at=self.first.source, first_received_at=self.first.time,
                       first_quote_sequence=self.first.sequence)
        if status == "BOUNDARY_QUOTE_OBSERVED":
            spread = (Fraction(self.first.ask) - Fraction(self.first.bid)) / fills.PIP
            row.update(bid=fills.text(self.first.bid), spread_pips=fills.text(spread))
        return row

    def assumption(self, *, opening_ordinal):
        """Use an explicitly declared ordinal shared with the invented decision clock."""
        data.integer(opening_ordinal)
        row = self.record()
        if row["status"] != "BOUNDARY_QUOTE_OBSERVED":
            return None
        return fills.Opening.from_record({
            "kind": "invented_b_opening_assumption", "start": row["start"], "end": row["end"],
            "ordinal": opening_ordinal, "bid": row["bid"], "spread_pips": row["spread_pips"],
        })


def inspect(tape, *, as_of):
    """Return evidence for scheduled opens reached by the receipt-time cutoff."""
    if not isinstance(tape, quotes.Tape):
        raise ValueError("invented ordered quote tape required")
    first = {}
    for quote in tape.prefix(as_of):
        window = tape.slot(quote.source)
        if window is not None:
            first.setdefault(window.start, quote)
    return tuple(OpeningEvidence(window, first.get(window.start))
                 for window in tape.windows if window.start <= as_of)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", help="invented development quote tape JSON")
    parser.add_argument("report", help="new JSON report path")
    parser.add_argument("--as-of", type=int, required=True, help="inclusive receipt cutoff in epoch ms")
    args = parser.parse_args()
    document, input_sha256 = data.read_json(args.tape)
    tape = quotes.Tape(document)
    rows = [evidence.record() for evidence in inspect(tape, as_of=args.as_of)]
    data.write_new(args.report, {
        "kind": "invented_level_b_opening_evidence", "input_sha256": input_sha256,
        "calendar_sha256": tape.calendar.sha256, "as_of": args.as_of,
        "scheduled_opens_reached": len(rows),
        "status_counts": dict(Counter(row["status"] for row in rows)), "h1": rows,
    })


if __name__ == "__main__":
    main()
