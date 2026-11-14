"""Strict streaming reader for provider-documented fixed-EST EURUSD ticks."""
import calendar
import csv
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
import zipfile

from .tick_audit import sha256


def archive_ticks(folder: Path):
    metadata = json.loads((folder/"download.json").read_text(encoding="utf-8"))
    path = folder/"original.zip"
    if metadata.get("source") != "HistData" or sha256(path) != metadata.get("sha256"):
        raise ValueError("Original HistData archive hash/source mismatch")
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if m.filename.endswith(".csv")]
        if len(members) != 1:
            raise ValueError("Expected exactly one EURUSD tick CSV")
        member = members[0]
        name = member.filename
        month = name.removeprefix("DAT_ASCII_EURUSD_T_").removesuffix(".csv")
        if name != f"DAT_ASCII_EURUSD_T_{month}.csv" or len(month) != 6 or not month.isdigit():
            raise ValueError("Unexpected instrument/format/month in archive")
        if member.file_size > 500_000_000:
            raise ValueError("Uncompressed archive exceeds size bound")
        previous = None
        with archive.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
            for sequence, row in enumerate(csv.reader(stream)):
                if len(row) != 4:
                    raise ValueError("Invalid HistData tick row")
                label = row[0]
                if len(label) != 18 or label[8] != " " or not (label[:8]+label[9:]).isdigit() or label[:6] != month:
                    raise ValueError("Malformed or out-of-month HistData timestamp")
                local = datetime(int(label[:4]), int(label[4:6]), int(label[6:8]),
                                 int(label[9:11]), int(label[11:13]), int(label[13:15]), tzinfo=timezone.utc)
                # Provider says EST without DST. Fixed +5h conversion, never America/New_York.
                msc = (calendar.timegm(local.utctimetuple())+5*3600)*1000+int(label[15:])
                bid, ask, volume = map(float, row[1:])
                if (not all(math.isfinite(v) for v in (bid,ask,volume)) or not 0 < bid <= ask or volume < 0
                        or (previous is not None and msc < previous)):
                    raise ValueError("Invalid/crossed quote, volume or out-of-order tick")
                previous = msc
                yield {"sequence": sequence, "time_msc": msc, "bid": bid, "ask": ask}


def hourly(ticks, lower=None, upper=None):
    """Aggregate sequentially; never synthesize missing hours."""
    current = None
    for tick in ticks:
        ms = tick["time_msc"]
        if lower is not None and ms < lower:
            continue
        if upper is not None and ms >= upper:
            # Consume the archive anyway: validation must include its full contents.
            continue
        hour = ms//3_600_000
        if current is None or current["hour"] != hour:
            if current is not None:
                yield current
            current = {"hour": hour, "ticks": 0, "first_ms": ms, "last_ms": ms,
                       "spread_pips": (tick["ask"]-tick["bid"])/.0001,
                       **{f"{s}_{p}": tick[s] for s in ("bid", "ask") for p in ("open","high","low","close")}}
        current["ticks"] += 1
        current["last_ms"] = ms
        for side in ("bid", "ask"):
            current[f"{side}_high"] = max(current[f"{side}_high"],tick[side])
            current[f"{side}_low"] = min(current[f"{side}_low"],tick[side])
            current[f"{side}_close"] = tick[side]
    if current is not None:
        yield current
