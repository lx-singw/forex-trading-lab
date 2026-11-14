"""Inspect reported demo costs read-only; never certify fees or enable orders."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import re

from forex_demo_lab.metadata_probe_127 import integer, native

DATE = "2026.10.14"
MAX_BYTES, MAX_US, MAX_QUERIES = 65536, 60000000, 5
PLAN = (("C", "clock_before"), ("K", "commissions"), ("M", "buy"),
        ("M", "sell"), ("C", "clock_after"))


def currency(value):
    if not re.fullmatch(r"EMPTY|[A-Z]{3}", value):
        raise ValueError("cost_currency")
    return None if value == "EMPTY" else value


def signed32(value):
    n = integer(value, 2**31, signed=True)
    if n > 2**31 - 1:
        raise ValueError("cost_enum")
    return n


def inspect_bytes(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("cost_size")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError("cost_encoding") from None
    lines = text.split("\r\n")
    tail = lines.pop()
    if len(lines) > 160 or any(len(x) > 2048 for x in lines + [tail]):
        raise ValueError("cost_frame_bounds")
    for line in lines + ([tail.removesuffix("\r")] if tail else []):
        if any((ord(c) < 32 and c != "\t") or ord(c) == 127 for c in line):
            raise ValueError("cost_framing")
    chain = "0" * 64
    origin = last = None
    kind = terminal = pending = None
    phase = attempted = 0
    rows, rules = [], []
    commission = None
    remaining_rules = None
    next_rule = next_tier = total_tiers = 0
    current_rule = None
    stop_code = None

    def clock(seconds, micros):
        nonlocal last
        if (seconds < last[0] or micros < last[1] or micros - origin[1] > MAX_US
                or abs(seconds - origin[0] - (micros - origin[1]) // 1000000) > 2):
            raise ValueError("cost_clock")
        try:
            date = datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y.%m.%d")
        except (ValueError, OSError, OverflowError):
            raise ValueError("cost_clock_range") from None
        if date != DATE:
            raise ValueError("cost_date")
        last = seconds, micros

    def inner_expected():
        if remaining_rules is None:
            return None
        return "T" if current_rule is not None else "R"

    def finish_rule():
        nonlocal remaining_rules, next_rule, next_tier, current_rule
        rules.append(current_rule)
        remaining_rules -= 1
        next_rule += 1
        next_tier = 0
        current_rule = None
        if remaining_rules == 0:
            remaining_rules = None

    for line_number, line in enumerate(lines):
        try:
            payload, digest = line.rsplit("\t", 1)
        except ValueError:
            raise ValueError("cost_checksum") from None
        if (not re.fullmatch("[0-9A-F]{64}", digest)
                or hashlib.sha256((chain + "\t" + payload + "\n").encode()).hexdigest().upper() != digest):
            raise ValueError("cost_checksum")
        chain = digest
        f = payload.split("\t")
        tag = f[0]
        if line_number == 0:
            if (len(f) != 6 or f[:2] != ["H", "FXDL_COST128_V1"]
                    or f[2] not in ("market_declared", "invented_fixture") or f[3] != DATE):
                raise ValueError("cost_header")
            origin = integer(f[4]), integer(f[5], 2**64 - 1)
            if min(origin) <= 0:
                raise ValueError("cost_origin")
            last, kind = origin, f[2]
            clock(*origin)
            continue
        if terminal is not None:
            raise ValueError("cost_after_terminal")
        if tag == "A":
            if (len(f) != 4 or pending is not None or inner_expected() is not None
                    or phase >= len(PLAN) or tuple(f[2:]) != PLAN[phase]
                    or integer(f[1], MAX_QUERIES) != attempted + 1):
                raise ValueError("cost_attempt")
            attempted += 1
            pending = attempted, f[2], f[3]
            continue
        if tag in ("C", "K", "M"):
            if len(f) < 11 or pending != (integer(f[1], MAX_QUERIES), tag, f[2]):
                raise ValueError("cost_unmatched_outcome")
            bs, ats, gs, bu, au, gu = [integer(v, 2**64 - 1) for v in f[3:9]]
            if not bs <= ats <= gs or not bu <= au <= gu:
                raise ValueError("cost_receipt_order")
            for pair in ((bs, bu), (ats, au), (gs, gu)):
                clock(*pair)
            succeeded = bool(integer(f[9], 1))
            error = integer(f[10], 2**31 - 1)
            if succeeded and error:
                raise ValueError("cost_query_error")
            row = dict(sequence=attempted, type=tag, key=f[2],
                       receipt_nominal_gmt_seconds=[bs, ats, gs],
                       receipt_monotonic_us=[bu, au, gu], query_succeeded=succeeded, error_code=error)
            values = f[11:]
            if tag == "C":
                if len(values) != 6 or not succeeded:
                    raise ValueError("cost_clock_fields")
                row["raw_clocks"] = dict(zip(
                    ("time_current", "time_trade_server", "time_gmt", "time_local", "gmt_offset", "daylight_savings"),
                    [integer(v, signed=True) for v in values]))
            elif tag == "M":
                if len(values) != 2:
                    raise ValueError("cost_margin_fields")
                decoded = [native(v) for v in values]
                if (succeeded and any(Decimal(v) < 0 for v in decoded)
                        or not succeeded and values != ["0000000000000000"] * 2):
                    raise ValueError("cost_margin_value")
                row["native_bits"] = values
                row["initial_rate"], row["maintenance_rate"] = decoded if succeeded else [None, None]
            else:
                if len(values) != 1:
                    raise ValueError("cost_commission_fields")
                count = signed32(values[0])
                if count < -1 or succeeded != (count >= 0 and error == 0):
                    raise ValueError("cost_commission_return")
                if succeeded and count > 8:
                    raise ValueError("cost_rule_limit")
                row["native_return_count"] = count
                commission = row
                if succeeded and count:
                    remaining_rules = count
            rows.append(row)
            pending = None
            phase += 1
            continue
        if tag in ("R", "T"):
            if (len(f) < 3 or pending is not None or tag != inner_expected()
                    or integer(f[1], MAX_QUERIES) != 2):
                raise ValueError("cost_rule_order")
            if tag == "R":
                if len(f) != 10 or integer(f[2], 7) != next_rule:
                    raise ValueError("cost_rule_fields")
                tier_count = integer(f[9], 16)
                total_tiers += tier_count
                if total_tiers > 128:
                    raise ValueError("cost_tier_limit")
                current_rule = dict(index=next_rule, currency=currency(f[3]),
                                    **dict(zip(("mode_range", "mode_charge", "mode_entry", "mode_direction", "mode_profit"),
                                               [signed32(v) for v in f[4:9]])),
                                    tier_count=tier_count, tiers=[])
                rows.append(dict(type="R", sequence=2, rule_index=next_rule, raw_fields=f[3:]))
                if tier_count == 0:
                    finish_rule()
            else:
                if (len(f) != 12 or integer(f[2], 7) != next_rule or integer(f[3], 15) != next_tier):
                    raise ValueError("cost_tier_fields")
                tier = dict(index=next_tier, mode=signed32(f[4]), volume_type=signed32(f[5]),
                            **dict(zip(("value", "min_value", "max_value", "range_from", "range_to"),
                                       [native(v) for v in f[6:11]])),
                            native_bits=f[6:11], currency=currency(f[11]))
                current_rule["tiers"].append(tier)
                rows.append(dict(type="T", sequence=2, rule_index=next_rule, tier=tier))
                next_tier += 1
                if next_tier == current_rule["tier_count"]:
                    finish_rule()
            continue
        if tag in ("E", "S"):
            if len(f) != (4 if tag == "E" else 3):
                raise ValueError("cost_footer")
            if tag == "E":
                if (pending is not None or inner_expected() is not None or phase != len(PLAN)
                        or integer(f[1], MAX_QUERIES) != attempted):
                    raise ValueError("cost_premature_end")
                clock(integer(f[2]), integer(f[3], 2**64 - 1))
                terminal = "complete"
            else:
                stop_code = integer(f[1], 22)
                if not 2 <= stop_code <= 22 or integer(f[2], MAX_QUERIES) != attempted:
                    raise ValueError("cost_stop")
                terminal = "stopped"
            continue
        raise ValueError("cost_record")
    if kind is None:
        raise ValueError("cost_header")
    if tail and terminal:
        raise ValueError("cost_tail_after_terminal")
    if commission is None or inner_expected() is not None:
        state = "incomplete"
    elif not commission["query_succeeded"]:
        state = "query_failed"
    elif commission["native_return_count"] == 0:
        state = "reported_empty"
    else:
        state = "reported_rules"
    return dict(schema="cost_probe128_inspection_v1", declared_kind=kind,
                capture_status=terminal or "incomplete", stop_code=stop_code,
                queries_attempted=attempted, queries_recorded=phase, pending_attempt=pending is not None,
                pending_rule_payload=inner_expected() is not None, truncated_tail=bool(tail),
                commission_state=state, commission_rules=rules if state == "reported_rules" else [],
                rows=rows, chain_head=chain, export_sha256=hashlib.sha256(data).hexdigest(),
                commission_cost_USD=None, margin_requirement_USD=None, slippage_terms=None,
                producer_authenticated=False, source_utc_certified=False, receipt_utc_certified=False,
                historical_cost_terms_certified=False, market_data_qualified=False,
                paper_evaluation_available=False, orders_available=False, real_money_execution_available=False)


def inspect_file(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise ValueError("cost_file")
    with p.open("rb") as stream:
        return inspect_bytes(stream.read(MAX_BYTES + 1))
