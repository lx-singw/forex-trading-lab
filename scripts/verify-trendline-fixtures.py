"""Inspect Phase 1 fixture integrity and independently check stated arithmetic.

This is not a trendline implementation or an end-to-end strategy test. No market
files are discovered or read. All inputs are explicitly named repository fixtures.
"""
import hashlib
import json
import sys
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from forex_demo_lab.elliott_full.patterns import confirmed


def read(relative):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads((ROOT / relative).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def verify():
    fixture_path = "tests/trendline/fixtures/golden-161.json"
    rule_path = "docs/trendline/rules-161.json"
    fixture = read(fixture_path)
    rulebook = read(rule_path)
    assert fixture["market_prices"] is False
    assert fixture["end_to_end_market_evidence"] is False
    assert fixture["expectations_written_before_engine"] is True
    assert rulebook["market_trials_run"] == 0
    cases = {case["id"]: case for case in fixture["cases"]}
    assert len(cases) == len(fixture["cases"]) == 80
    rules = {rule["id"]: rule for rule in rulebook["rules"]}
    assert len(rules) == len(rulebook["rules"]) == 34
    assert len(rulebook["ambiguity_resolutions"]) == 24
    assert len(rulebook["parameter_declarations"]) == 34
    for number in range(1, 41):
        for side in ("LONG", "SHORT"):
            case = cases[f"G{number:02}_{side}"]
            assert case["direction"] == side
            assert case["hand_calculation"] and case["inputs"] and case["expected"]
            assert set(case["rules"]) <= rules.keys()
    for rule in rules.values():
        assert rule["implementation_status"] == "specified_not_implemented"
        assert rule["positive_and_negative_fixture_ids"]
        for identity in rule["positive_and_negative_fixture_ids"]:
            assert rule["id"] in cases[identity]["rules"], (rule["id"], identity)

    arithmetic_checks = 0
    existing_pivot_crosschecks = 0
    for side, sign in (("LONG", 1), ("SHORT", -1)):
        # Independent price-only gap arithmetic: no strategy detection.
        gap = cases[f"G16_{side}"]
        inp, expected = gap["inputs"], gap["expected"]
        fill = F(inp["first_breached_exit_side"]) - sign * F(inp["adverse_slippage"])
        assert fill == F(expected["fill"])
        estimate = sign * (F(inp["entry"]) - F(inp["stop"]))
        loss = sign * (F(inp["entry"]) - fill)
        assert estimate == F(expected["estimated_price_loss"])
        assert loss == F(expected["actual_price_loss"])
        assert loss - estimate == F(expected["excess"])
        arithmetic_checks += 4
        projected = cases[f"G21_{side}"]
        inp, expected = projected["inputs"], projected["expected"]
        assert F(inp["line_value"]) - sign * F(inp["buffer"]) == F(expected["core_stop"])
        assert (F(inp["line_value"]) + F(inp["slope"]) * inp["project_bars"]
                - sign * F(inp["buffer"])) == F(expected["projected_stop"])
        arithmetic_checks += 2
        costs = cases[f"G34_{side}"]
        inp, expected = costs["inputs"], costs["expected"]
        commission = F(inp["lots"]) * F(inp["commission_round_turn_per_lot"])
        financing = F(inp["lots"]) * F(inp["financing_charge_per_lot_per_unit"]) * inp["rollover_units"]
        assert commission == F(expected["commission"])
        assert financing == F(expected["financing"])
        assert F(inp["hypothetical_price_pnl"]) - commission - financing == F(expected["net"])
        arithmetic_checks += 3

        candle_case = cases[f"G35_{side}"]
        bars = [[F(v) for v in row] for row in candle_case["inputs"]["ohlc"]]
        assert len(bars) == 49
        for o, high, low, close in bars:
            assert low <= min(o, close) <= max(o, close) <= high
        # Reconcile the hand sum directly from its explicit 14 rows.
        true_ranges = []
        for index in range(35, 49):
            _, high, low, _ = bars[index]
            previous = bars[index-1][3]
            true_ranges.append(max(high-low, abs(high-previous), abs(low-previous)))
        assert sum(true_ranges) / 14 == F(candle_case["expected"]["atr_fraction"])
        arithmetic_checks += 1
        pivot_bars = [SimpleNamespace(high=Decimal(row[1]), low=Decimal(row[2]),
                                     end=index, available=index,
                                     lineage=f"invented-{side}-{index}")
                      for index,row in enumerate(candle_case["inputs"]["ohlc"])]
        journal, _ = confirmed(pivot_bars, 3)
        action_kind, safety_kind = (("high","low") if sign == 1 else ("low","high"))
        assert [p.index for p in journal if p.kind == action_kind] == candle_case["expected"]["action_pivot_indices"]
        assert [p.index for p in journal if p.kind == safety_kind] == candle_case["expected"]["safety_pivot_indices"]
        existing_pivot_crosschecks += 2

    # Every gate fixture contains both outcomes, including neutral/unavailable.
    outcomes = [cases[f"G{n:02}_{s}"]["expected"]["outcome"]
                for n in range(17, 21) for s in ("LONG", "SHORT")]
    assert len(outcomes) == 8 and outcomes.count("ALLOW") == 2
    summary = {"sprint":161,"kind":"fixture_integrity_and_arithmetic_not_engine_tests",
               "scenario_count":80,"direction_pairs":40,"rule_count":34,
               "d1_gate_outcomes":8,"independent_arithmetic_equalities":arithmetic_checks,
               "existing_batch_pivot_crosschecks":existing_pivot_crosschecks,
               "engine_implemented":False,"market_trials_run":0,
               "independent_human_review":"pending",
               "sha256":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                         for p in (fixture_path,rule_path)}}
    return summary


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
