"""Offline comparison of bounded tick captures with frozen bar/reference trades."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from forex_demo_lab.cli import code_digest, write_json
from forex_demo_lab.tick_audit import first_exit, load_ticks, sha256, summarize, valid_quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--raw-bars", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path)
    parser.add_argument("--trade-index", type=int)
    args = parser.parse_args()
    try:
        if (args.reference_report is None) != (args.trade_index is None):
            raise ValueError("Supply both reference report and trade index, or neither")
        result = summarize(args.capture, args.raw_bars)
        result["audit_code_sha256"] = code_digest()
        if args.reference_report:
            reference = json.loads(args.reference_report.read_text(encoding="utf-8"))
            provenance = reference["experiment"]["provenance"]
            if reference["partition"] != "development" or provenance["raw_sha256"] != sha256(args.raw_bars):
                raise ValueError("Use the matching frozen development report/raw source")
            if not 0 <= args.trade_index < len(reference["trades"]):
                raise ValueError("Trade index outside reference report")
            trade = reference["trades"][args.trade_index]
            zone = ZoneInfo(provenance["api_label_timezone"])
            opening = datetime.fromisoformat(trade["opened"]).astimezone(zone).replace(tzinfo=timezone.utc)
            ending = (datetime.fromisoformat(trade["closed"])+timedelta(hours=1)).astimezone(zone).replace(tzinfo=timezone.utc)
            metadata, ticks = load_ticks(args.capture)
            if (not metadata["requests_without_api_errors"]
                    or datetime.fromisoformat(metadata["source_label_start"]) > opening
                    or datetime.fromisoformat(metadata["source_label_end_exclusive"]) < ending):
                raise ValueError("Capture must cover the reference entry through its entire closing candle without API errors")
            selected = [t for t in ticks if opening.timestamp()*1000 <= t["time_msc"] < ending.timestamp()*1000]
            if not selected or not all(valid_quote(t) for t in selected):
                raise ValueError("Valid bid/ask ticks are required throughout the selected records")
            hit = first_exit(selected, trade["side"], trade["stop"], trade["target"],
                             reference["experiment"]["config"]["slippage_pips"])
            if hit:
                hit["source_time_label"] = datetime.fromtimestamp(hit["time_msc"]/1000, timezone.utc).isoformat()
                hit["exit_difference_pips_vs_bar_model"] = (hit["modeled_exit"]-trade["exit"])/.0001
            spread = (selected[0]["ask"]-selected[0]["bid"])/.0001
            result["reference_trade_diagnostic"] = {
                "report_sha256": sha256(args.reference_report), "trade_index": args.trade_index,
                "original_side": trade["side"], "original_entry": trade["entry"],
                "original_stop": trade["stop"], "original_target": trade["target"],
                "original_exit": trade["exit"], "original_reason": trade["reason"],
                "opening_tick_bid": selected[0]["bid"], "opening_tick_ask": selected[0]["ask"],
                "opening_spread_pips": spread,
                "opening_spread_would_block_entry": spread > reference["experiment"]["config"]["max_spread_pips"]+1e-9,
                "first_quote_delay_seconds": selected[0]["time_msc"]/1000-opening.timestamp(),
                "first_observed_boundary": hit,
                "scope": "Conditional crossing of original fixed boundaries only; no position or net P&L recomputation",
                "historical_clock_verified": False, "complete_market_history_verified": False}
        write_json(args.output, result)
        print(json.dumps({"ticks": result["ticks"], "invalid_quotes": result["invalid_quotes"],
                          "hour_statuses": dict(Counter(h["status"] for h in result["hours"])),
                          "spread_pips": result["spread_pips"],
                          "reference_trade_diagnostic": result.get("reference_trade_diagnostic")}, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Audit stopped: {exc}\n")


if __name__ == "__main__":
    main()
