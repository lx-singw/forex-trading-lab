"""Describe frozen trades without selecting parameters or rewriting performance."""
from collections import Counter
from datetime import datetime
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from forex_demo_lab.cli import write_json
from forex_demo_lab.tick_audit import sha256
import json


def diagnose(report, config):
    trades = report["trades"]
    if not trades:
        raise ValueError("No trades to diagnose")
    rows = []
    for index, trade in enumerate(trades):
        if trade["side"] not in (-1, 1) or trade["lots"] <= 0:
            raise ValueError("Invalid trade direction or size")
        for key in ("entry", "exit", "stop", "lots", "gross_pnl", "commission", "swap", "net_pnl"):
            if not math.isfinite(trade[key]):
                raise ValueError("Nonfinite trade value")
        if not math.isclose(trade["gross_pnl"] - trade["commission"] + trade["swap"], trade["net_pnl"], abs_tol=1e-8):
            raise ValueError("Trade accounting mismatch")
        duration = (datetime.fromisoformat(trade["closed"]) - datetime.fromisoformat(trade["opened"])).total_seconds() / 3600
        if duration < 0:
            raise ValueError("Exit before entry")
        beyond = quote_beyond = 0
        if trade["reason"] == "stop_tick":
            beyond = max(0, -trade["side"] * (trade["exit"] - trade["stop"]))
            observed_quote = trade["exit"] + trade["side"] * config["slippage_pips"] * .0001
            quote_beyond = max(0, -trade["side"] * (observed_quote - trade["stop"]))
        rows.append({"index": index, "opened": trade["opened"], "closed": trade["closed"],
                     "reason": trade["reason"], "side": trade["side"], "net_pnl": trade["net_pnl"],
                     "holding_hours": duration, "fill_beyond_nominal_stop_pips": beyond / .0001,
                     "observed_quote_beyond_stop_pips": quote_beyond / .0001,
                     "fill_beyond_nominal_stop_dollars": beyond * config["contract_size"] * trade["lots"]})
    gross, net = (sum(t[key] for t in trades) for key in ("gross_pnl", "net_pnl"))
    commission = sum(t["commission"] for t in trades)
    swap = sum(t["swap"] for t in trades)
    if len(trades) != report["metrics"]["closed_trades"] or not math.isclose(net, report["metrics"]["net_pnl"], abs_tol=1e-8):
        raise ValueError("Report totals mismatch")
    positive = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    negative = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    return {"trades": len(trades), "wins": len(positive), "losses": len(negative),
            "flat": len(trades) - len(positive) - len(negative), "exit_reasons": dict(Counter(t["reason"] for t in trades)),
            "net_pnl": net, "pnl_before_commission_and_swap_includes_spread_and_slippage": gross,
            "commission": commission, "swap": swap, "average_net_win": sum(positive) / len(positive) if positive else None,
            "average_net_loss": sum(negative) / len(negative) if negative else None,
            "stop_overshoot_dollars_including_modeled_exit_slippage": sum(r["fill_beyond_nominal_stop_dollars"] for r in rows),
            "maximum_observed_quote_overshoot_pips": max(r["observed_quote_beyond_stop_pips"] for r in rows),
            "trade_diagnostics": rows}


def main():
    results = []
    for sample in ("004-january-mt5", "005-april-new-york", "004-july-new-york"):
        for cost in ("base", "adverse"):
            report_path = Path(f"reports/research-{sample}-{cost}.json")
            manifest_path = Path(f"reports/research-{sample}-{cost}-manifest.json")
            report = json.loads(report_path.read_text())
            manifest = json.loads(manifest_path.read_text())
            if report["manifest_sha256"] != sha256(manifest_path):
                raise ValueError("Frozen report/manifest link mismatch")
            result = {"sample": sample, "cost": cost, "report_sha256": sha256(report_path),
                      "manifest_sha256": sha256(manifest_path), **diagnose(report, manifest["config"])}
            results.append(result)
            print(json.dumps({k: v for k, v in result.items() if k != "trade_diagnostics"}))
    write_json(Path("reports/baseline-diagnosis-008.json"), {"status": "descriptive_existing_development_trades",
               "results": results, "not_new_performance": True, "demo_execution_ready": False,
               "limitations": ["Only 26 baseline trades; cost variants reuse observations",
                               "Gross P&L still includes spread and slippage; not frictionless performance",
                               "Stop overshoot is accounting attribution, not a recoverable profit forecast",
                               "No causal attribution to trends, ranges or news without further analysis",
                               "No annual or continuous return across independent monthly starts"]})


if __name__ == "__main__":
    main()
