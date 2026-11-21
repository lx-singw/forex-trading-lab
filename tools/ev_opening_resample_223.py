"""Compare the published 2024 EV H1 opens with the first M5 rows."""

import argparse
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
import gzip
import hashlib
import http.client
import io
import json

from forex_demo_lab.trendline import data

HOST = "evtradelabs.com"
FILES = {"H1": (3600, 195_309), "M5": (300, 1_896_108)}
COLUMNS = ("ts", "o", "h", "l", "c", "ao", "ah", "al", "ac", "v")


def year_bounds(year):
    if type(year) is not int or year not in (2020, 2021, 2022, 2024):
        raise ValueError("EV diagnostic year is outside the reviewed scope")
    return tuple(int(datetime(y, 1, 1, tzinfo=UTC).timestamp()) for y in (year, year + 1))


START, END = year_bounds(2024)


def download(frame, size, *, year=2024):
    year_bounds(year)
    connection = http.client.HTTPSConnection(HOST, timeout=15)
    try:
        connection.request("GET", f"/api/simulator/data/EURUSD/{frame}/{year}.json.gz")
        response = connection.getresponse()
        if response.status != 200 or response.getheader("Location") is not None:
            raise ValueError(f"{frame} public download did not return HTTP 200")
        body = response.read(size + 1)
        if len(body) != size:
            raise ValueError(f"{frame} gzip size differs from the catalogue")
        return body
    finally:
        connection.close()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate candle field")
        result[key] = value
    return result


def _invalid(_):
    raise ValueError("nonfinite candle value")


def _price(value):
    if value is None:
        return None
    if type(value) not in (Decimal, int) or value <= 0:
        raise ValueError("expected a positive candle price or null")
    return value


def price_rows(body, period, price_columns, *, year=2024):
    start, end = year_bounds(year)
    with gzip.GzipFile(fileobj=io.BytesIO(body)) as source:
        raw = source.read(data.BYTE_LIMIT + 1)
    if len(raw) > data.BYTE_LIMIT:
        raise ValueError("decoded candle file exceeds byte limit")
    document = json.loads(raw, parse_float=Decimal, object_pairs_hook=_object, parse_constant=_invalid)
    if type(document) is dict:
        data.fields(document, COLUMNS)
        rows = (dict(zip(COLUMNS, values, strict=True))
                for values in zip(*(document[column] for column in COLUMNS), strict=True))
    elif type(document) is list:
        rows = iter(document)
    else:
        raise ValueError("expected published candle rows or columns")
    previous = start - 1
    for row in rows:
        data.fields(row, COLUMNS)
        stamp = row["ts"]
        if type(stamp) is not int or not previous < stamp < end or stamp % period:
            raise ValueError(f"expected unique, aligned {year} candle timestamps in ascending order")
        yield stamp, tuple(_price(row[column]) for column in price_columns)
        previous = stamp
    if previous < start:
        raise ValueError("empty candle file")


def parse(body, period, *, year=2024):
    return dict(price_rows(body, period, ("o", "ao"), year=year))


def compare(hourly, five_minute):
    first = {}
    for stamp, pair in five_minute.items():
        first.setdefault(stamp - stamp % 3600, (stamp, pair))
    counts, start_lags = Counter(), Counter()
    for start, hour_pair in hourly.items():
        if start not in first:
            counts["missing_m5_hour"] += 1
            continue
        stamp, pair = first[start]
        start_lags[str(stamp - start)] += 1
        if None in (*hour_pair, *pair):
            counts["missing_open_side"] += 1
        elif hour_pair[1] < hour_pair[0] or pair[1] < pair[0]:
            counts["crossed_opening_pair"] += 1
        elif hour_pair == pair:
            counts["matching_bid_and_ask"] += 1
        else:
            counts["different_opening_pair"] += 1
    return {"h1_rows": len(hourly), "m5_rows": len(five_minute), "m5_hours_without_h1": len(first.keys() - hourly.keys()),
            "comparison_counts": dict(sorted(counts.items())),
            "first_m5_label_lag_seconds": dict(sorted(start_lags.items(), key=lambda item: int(item[0])))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON diagnostic report path")
    args = parser.parse_args()
    inputs, opens = {}, {}
    for frame, (period, length) in FILES.items():
        body = download(frame, length)
        inputs[frame] = {"sha256": hashlib.sha256(body).hexdigest(), "compressed_bytes": len(body)}
        opens[frame] = parse(body, period)
    data.write_new(args.output, {
        "kind": "ev_2024_h1_open_resample_diagnostic", "symbol": "EURUSD", "year": 2024,
        "inputs": inputs, **compare(opens["H1"], opens["M5"]),
        "first_tick_provenance_verified": False, "availability_model_qualified": False,
        "market_source_admitted": False, "actual_counts": None,
    })


if __name__ == "__main__":
    main()
