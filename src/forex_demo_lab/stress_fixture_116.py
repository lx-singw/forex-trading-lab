"""Fixed invented adversarial inputs. No market source or data repair."""
import json

from .combination_fixture_115 import fixture
from .strategy_fixture_114 import START

HOUR = 3_600_000
ACCEPTED = ("control", "wide_entry", "wide_short", "gap_down_long", "gap_up_short",
            "calendar_outage", "missing_previous_hour", "repeated_quote")
REJECTED = {
    "stale_source": "invented_quote_age", "future_source": "invented_quote_age",
    "broken_sequence": "event_order", "conflicting_source": "same_source_time_changed",
    "clock_reversal": "event_order", "crossed_quote": "invalid_quote",
    "boolean_source": "integer_range", "native_clock": "invented114_fixture_required",
    "duplicate_field": "duplicate_json_field",
}


def definitions():
    return {
        "base": "combination115_continuation", "start_msc": START,
        "accepted": list(ACCEPTED), "rejected": dict(REJECTED),
        "wide_entry": {"hours_inclusive": [201, 227], "spread": .0003},
        "wide_short": {"first_quote_hour": 466, "spread": .0003},
        "gap_down_long": {"hour": 203, "bid_base": 1.05, "spread": .0001},
        "gap_up_short": {"hour": 491, "bid_base": 1.15, "spread": .0001},
        "calendar_outage": {"omit_hours_inclusive": [300, 450], "generated_resequence": True},
        "missing_previous_hour": {"omit_hours_inclusive": [201, 201], "generated_resequence": True},
        "repeated_quote": {"first_quote_hours": [202, 490], "receipt_delay_ms": 500,
                           "generated_resequence": True},
        "restart_hours": {"development": 203, "validation": 491},
        "checkpoint_faults": ["checksum", "cross_rule", "boolean_cursor", "rehashed_balance",
                              "metric_version", "rehashed_protection"],
    }


def invented(case):
    if case not in ACCEPTED and case not in REJECTED:
        raise ValueError("stress_case")
    value = fixture("continuation")
    value["case"] = case
    events = value["events"]
    if case in ACCEPTED:
        output = []
        for event in events:
            hour, delta = divmod(event["receipt_msc"] - START, HOUR)
            if (case == "calendar_outage" and 300 <= hour <= 450
                    or case == "missing_previous_hour" and hour == 201):
                continue
            e = dict(event)
            if (case == "wide_entry" and 201 <= hour <= 227
                    or case == "wide_short" and hour == 466 and delta == 0):
                e["ask"] = round(e["bid"] + .0003, 8)
            if (case == "gap_down_long" and hour == 203
                    or case == "gap_up_short" and hour == 491):
                first = events[hour * 4]["bid"]
                e["bid"] = round((1.05 if hour == 203 else 1.15) + event["bid"] - first, 8)
                e["ask"] = round(e["bid"] + .0001, 8)
            output.append(e)
            if case == "repeated_quote" and hour in (202, 490) and delta == 0:
                output.append({**e, "receipt_msc": e["receipt_msc"] + 500})
        for sequence, event in enumerate(output):
            event["sequence"] = sequence
        value["events"] = output
    else:
        e, previous = events[1], events[0]
        if case == "stale_source":
            e["source_msc"] = e["receipt_msc"] - 2001
        elif case == "future_source":
            e["source_msc"] = e["receipt_msc"] + 1
        elif case == "broken_sequence":
            e["sequence"] = 2
        elif case == "conflicting_source":
            e.update(receipt_msc=previous["receipt_msc"] + 500,
                     source_msc=previous["source_msc"],
                     bid=previous["bid"] + .00001, ask=previous["ask"] + .00001)
        elif case == "clock_reversal":
            e.update(receipt_msc=previous["receipt_msc"] - 1,
                     source_msc=previous["source_msc"] - 1)
        elif case == "crossed_quote":
            e["ask"] = e["bid"] - .0001
        elif case == "boolean_source":
            e["source_msc"] = True
        elif case == "native_clock":
            value["clock"] = "broker_server"
    return value


def fixture_bytes(case):
    body = json.dumps(invented(case), sort_keys=True, indent=2, allow_nan=False) + "\n"
    if case == "duplicate_field":
        body = body.replace('{\n', '{\n  "clock": "invented_utc_milliseconds",\n', 1)
    return body.encode()
