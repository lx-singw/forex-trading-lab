"""Read-only inspection of bounded107 exports. Never connects or places orders."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import math
from pathlib import Path
import re
import struct

MAX_BYTES = 262144
DATE = "2026.10.12"
ZERO = "0" * 64
INTEGER = re.compile(r"0|[1-9][0-9]{0,19}")
HEX64 = re.compile(r"[0-9A-F]{16}")
SHA = re.compile(r"[0-9A-F]{64}")


def number(text, maximum=2**64-1):
    if not INTEGER.fullmatch(text):
        raise ValueError("invalid_integer")
    value = int(text)
    if value > maximum:
        raise ValueError("integer_overflow")
    return value


def native_price(text):
    if not HEX64.fullmatch(text):
        raise ValueError("invalid_native_bits")
    value = struct.unpack(">d", bytes.fromhex(text))[0]
    if not math.isfinite(value):
        raise ValueError("nonfinite_price")
    return value


def inspect_bytes(data):
    """Return fixed metadata/diagnostics plus validated observations, without writes.

    A hash-consistent file is not authenticated producer/account evidence.
    Incomplete files retain prior validated rows and cannot be resumed/admitted.
    """
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("invalid_export_size")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError("invalid_export_encoding") from None
    if any(ord(c) < 32 and c not in "\t\r\n" for c in text):
        raise ValueError("invalid_export_control")
    chunks = text.split("\n")
    tail = chunks.pop()
    if len(chunks) > 243 or any(len(s) > 2048 for s in chunks) or len(tail) > 2048:
        raise ValueError("invalid_export_bounds")
    rows = []
    previous = ZERO
    for line in chunks:
        line = line.removesuffix("\r")
        if "\r" in line or not line:
            raise ValueError("invalid_export_line")
        try:
            payload, checksum = line.rsplit("\t", 1)
        except ValueError:
            raise ValueError("missing_checksum") from None
        if not SHA.fullmatch(checksum) or hashlib.sha256(
                (previous + "\t" + payload + "\n").encode("ascii")).hexdigest().upper() != checksum:
            raise ValueError("checksum_mismatch")
        rows.append(payload.split("\t"))
        previous = checksum
    if not rows:
        raise ValueError("header_missing")
    h = rows.pop(0)
    if len(h) != 9 or h[:2] != ["H", "FXDL107_V1"] or h[2] not in (
            "market_declared", "invented_fixture") or h[3:7] != [DATE, "120", "60000000", "500000"]:
        raise ValueError("invalid_header")
    origin_s, origin_us = number(h[7], 32535215999), number(h[8])

    def clock(seconds, micros):
        if not origin_s or seconds < origin_s or micros < origin_us:
            raise ValueError("clock_reversal")
        if micros-origin_us > 60000000:
            raise ValueError("deadline_exceeded")
        if abs((seconds-origin_s)-(micros-origin_us)//1000000) > 2:
            raise ValueError("clock_jump")
        try:
            date = datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y.%m.%d")
        except (ValueError, OverflowError, OSError):
            raise ValueError("clock_range") from None
        if date != DATE:
            raise ValueError("date_mismatch")

    clock(origin_s, origin_us)
    attempts = 0
    pending = None
    observations = []
    missing = invalid = repeats = equal_changed = backwards = gaps = 0
    previous_tick = None
    source_highwater = 0
    last_s, last_us, last_read_us = origin_s, origin_us, None
    terminal = None
    stop_code = None
    required_stop = None
    for fields in rows:
        if terminal is not None:
            raise ValueError("data_after_terminal")
        kind = fields[0]
        if required_stop is not None and kind != "S":
            raise ValueError("missing_terminal_stop")
        if kind == "A":
            if len(fields) != 2 or pending is not None or attempts >= 120:
                raise ValueError("invalid_attempt")
            seq = number(fields[1], 120)
            if seq != attempts+1:
                raise ValueError("attempt_sequence")
            attempts = pending = seq
        elif kind in ("Q", "N"):
            if len(fields) != (16 if kind == "Q" else 9) or pending is None:
                raise ValueError("unmatched_outcome")
            seq, bs, ats, gs, bu, au, gu = [number(s) for s in fields[1:8]]
            if seq != pending or not last_s <= bs <= ats <= gs or not last_us <= bu <= au <= gu:
                raise ValueError("receipt_order")
            for seconds, micros in ((bs, bu), (ats, au), (gs, gu)):
                clock(seconds, micros)
            if last_read_us is not None:
                if bu-last_read_us < 500000:
                    raise ValueError("sampling_interval")
                if bu-last_read_us > 2000000:
                    gaps += 1
            last_s, last_us, last_read_us = gs, gu, bu
            if kind == "N":
                code = number(fields[8], 18)
                if code not in (15, 16):
                    raise ValueError("invalid_missing_code")
                missing += code == 15
                invalid += code == 16
                required_stop = code
            else:
                seconds = number(fields[8], 32535215999)
                millis = number(fields[9], 32535215999999)
                bid, ask, last, real_volume = [native_price(fields[i]) for i in (10, 11, 12, 15)]
                volume, flags = number(fields[13]), number(fields[14], 2**32-1)
                if not seconds or not millis or millis//1000 != seconds or bid <= 0 or ask < bid or last < 0 or real_volume < 0:
                    raise ValueError("invalid_quote")
                tick = tuple(fields[8:16])
                repeats += tick == previous_tick
                equal_changed += previous_tick is not None and tick[1] == previous_tick[1] and tick != previous_tick
                backwards += millis < source_highwater
                source_highwater = max(millis, source_highwater)
                previous_tick = tick
                observations.append({"sequence": seq, "receipt_gmt_seconds": [bs, ats, gs],
                    "receipt_monotonic_us": [bu, au, gu], "source_seconds": seconds,
                    "source_millis": millis, "native_bits": dict(zip(
                        ("bid", "ask", "last", "volume_real"), (fields[10], fields[11], fields[12], fields[15]))),
                    "bid_decimal": str(Decimal(str(bid))), "ask_decimal": str(Decimal(str(ask))),
                    "volume": volume, "flags": flags})
            pending = None
        elif kind == "S":
            if len(fields) != 3 or number(fields[2], 120) != attempts:
                raise ValueError("invalid_stop")
            stop_code = number(fields[1], 18)
            if stop_code < 2:
                raise ValueError("invalid_stop_code")
            if required_stop is not None and stop_code != required_stop:
                raise ValueError("stop_reason_mismatch")
            terminal = "stopped"
        elif kind == "E":
            if len(fields) != 6 or pending is not None:
                raise ValueError("invalid_completion")
            count, quoted, seconds, micros, guards = [number(s) for s in fields[1:]]
            if count != attempts or count != 120 or quoted != len(observations) or quoted != 120 or guards != 3*attempts+3:
                raise ValueError("completion_counts")
            if seconds < last_s or micros < last_us:
                raise ValueError("completion_clock_order")
            clock(seconds, micros)
            terminal = "complete"
        else:
            raise ValueError("unknown_record")
    if tail and terminal is not None:
        raise ValueError("trailing_partial_data")
    return {"schema": "private_recorder_107_inspection_v1", "declared_kind": h[2],
        "synthetic": True if h[2] == "invented_fixture" else None,
        "producer_authentication": "unverified", "symbol": "EURUSD", "sampling": "poll_latest",
        "source_clock": "raw_unverified", "receipt_clock": "pc_gmt_unverified",
        "use_rights_certified": False, "private_research_scope": True,
        "capture_status": terminal or "incomplete", "stop_code": stop_code,
        "pending_attempt": pending, "truncated_tail": bool(tail), "attempts": attempts,
        "observed": len(observations), "missing": missing, "invalid": invalid,
        "repeated_snapshots": repeats, "equal_time_changed": equal_changed,
        "source_backwards": backwards, "receipt_gaps": gaps,
        "source_age_known": False, "provider_tick_identity": False, "complete_tick_delivery": False,
        "journal_sha256": hashlib.sha256(data).hexdigest(), "chain_head": previous,
        "resume_available": False, "market_data_qualified": False,
        "paper_evaluation_available": False, "orders_available": False,
        "real_money_execution_available": False, "observations": observations}


def inspect_file(path):
    # Open read-only and bound the read even if a file grows after opening.
    with Path(path).open("rb") as handle:
        data = handle.read(MAX_BYTES+1)
    return inspect_bytes(data)


def summary(result):
    return {k: v for k, v in result.items() if k != "observations"}
