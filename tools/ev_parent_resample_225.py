"""Audit EV 2024 H4 and D1 UTC resamples against published H1 bars."""

import argparse
from collections import Counter
import hashlib

from forex_demo_lab.trendline import data
from tools.ev_calendar_224 import PINNED, ordinary_open
from tools.ev_opening_resample_223 import END, FILES, START, download, price_rows

HOUR = 3600
FRAMES = {"H1": FILES["H1"], "H4": (4 * HOUR, 55_333), "D1": (24 * HOUR, 11_838)}
OHLC = ("o", "h", "l", "c", "ao", "ah", "al", "ac")


def buckets(starts, period):
    result = {}
    for stamp in sorted(starts):
        result.setdefault(stamp - stamp % period, []).append(stamp)
    return result


def aggregate(children):
    prices = []
    for side in (0, 4):
        prices.extend((
            children[0][side], max(row[side + 1] for row in children),
            min(row[side + 2] for row in children), children[-1][side + 3],
        ))
    return tuple(prices)


def compare(hourly, parents, scheduled, period):
    groups = buckets(hourly, period)
    expected = buckets(scheduled, period)
    stats = Counter()
    differences = Counter()
    child_totals = Counter()
    hours_before_first = Counter()
    hours_after_last = Counter()
    for start, prices in parents.items():
        child_starts = groups.get(start, [])
        due = expected.get(start, [])
        child_totals[len(child_starts)] += 1
        if due and len(due) < period // HOUR:
            stats["short_ordinary_session_buckets"] += 1
        if set(due) - set(child_starts):
            stats["published_buckets_missing_ordinary_h1"] += 1
        if not child_starts:
            stats["no_published_h1_children"] += 1
            continue

        hours_before_first[(child_starts[0] - start) // HOUR] += 1
        hours_after_last[(start + period - child_starts[-1] - HOUR) // HOUR] += 1
        children = [hourly[stamp] for stamp in child_starts]
        if None in prices or any(None in row for row in children):
            stats["missing_price_fields"] += 1
            continue
        delta = [field for field, observed, derived in zip(OHLC, prices, aggregate(children), strict=True)
                 if observed != derived]
        if delta:
            stats["differing_ohlc"] += 1
            differences.update(delta)
        else:
            stats["matching_ohlc"] += 1

    return {
        "published_buckets": len(parents),
        "buckets_with_h1_children_but_no_published_parent": len(groups.keys() - parents.keys()),
        "unpublished_buckets_with_ordinary_h1": len(expected.keys() - parents.keys()),
        "published_buckets_without_ordinary_h1": len(parents.keys() - expected.keys()),
        "published_bucket_counts": dict(sorted(stats.items())),
        "different_fields": dict(sorted(differences.items())),
        "published_h1_children_per_bucket": dict(sorted(child_totals.items())),
        "hours_from_bucket_label_to_first_child": dict(sorted(hours_before_first.items())),
        "hours_from_last_child_end_to_bucket_end": dict(sorted(hours_after_last.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    inputs, frames = {}, {}
    for frame, (period, size) in FRAMES.items():
        body = download(frame, size)
        digest = hashlib.sha256(body).hexdigest()
        if frame == "H1" and digest != PINNED["H1"]:
            raise ValueError("H1 gzip digest differs from Sprint 223")
        inputs[frame] = {"sha256": digest, "compressed_bytes": len(body)}
        frames[frame] = dict(price_rows(body, period, OHLC))
    hourly = frames["H1"]
    scheduled = {stamp for stamp in range(START, END, HOUR) if ordinary_open(stamp)}
    data.write_new(args.output, {
        "kind": "ev_2024_utc_parent_resample_diagnostic",
        "symbol": "EURUSD",
        "year": 2024,
        "inputs": inputs,
        "published_h1_rows": len(hourly),
        "frames": {frame: compare(hourly, frames[frame], scheduled, FRAMES[frame][0]) for frame in ("H4", "D1")},
        "session_calendar_qualified": False,
        "opening_availability_qualified": False,
        "market_source_admitted": False,
        "actual_counts": None,
    })


if __name__ == "__main__":
    main()
