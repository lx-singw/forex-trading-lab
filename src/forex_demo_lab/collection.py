"""Read-only MT5 history capture. Never submit orders or expose account identity."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

RAW_FIELDS = ["time", "open", "high", "low", "close", "tick_volume", "spread_points", "real_volume"]
SPEC_FIELDS = ("digits", "point", "trade_contract_size", "volume_min", "volume_step", "volume_max",
               "trade_tick_size", "trade_tick_value_loss", "trade_stops_level", "trade_freeze_level",
               "trade_calc_mode", "swap_mode", "swap_long", "swap_short", "swap_rollover3days",
               "currency_base", "currency_profit", "currency_margin")


def require_demo(api):
    terminal = api.terminal_info()
    account = api.account_info()
    if terminal is None or not terminal.connected or account is None:
        raise ValueError("A connected demo terminal is required")
    if type(account.trade_mode) is not int or account.trade_mode != api.ACCOUNT_TRADE_MODE_DEMO:
        raise ValueError("Capture rejected: actual account type must be demo")
    return terminal, account


def clock_observation(api) -> dict:
    """A current quote can disprove UTC encoding; it cannot prove past DST rules."""
    require_demo(api)
    tick = api.symbol_info_tick("EURUSD")
    received = datetime.now(timezone.utc)
    require_demo(api)
    if tick is None:
        return {"received_utc": received.isoformat(), "status": "unavailable"}
    label = datetime.fromtimestamp(int(tick.time), timezone.utc)
    delta = (label-received).total_seconds()
    return {"received_utc": received.isoformat(), "raw_tick_label": label.isoformat(),
            "raw_label_minus_system_seconds": round(delta, 3),
            "status": "ahead_of_utc" if delta > 60 else "stale_or_uncertain" if delta < -120 else "near_utc",
            "historical_timezone_verified": False}


def capture(api, start: datetime, end: datetime, output: Path, progress=None):
    """Capture [start,end), with account checks around each month's read.

    Caller owns initialize/shutdown. A fake API can exercise all safety paths.
    No full account/terminal tuple is printed, serialized, or returned.
    """
    now = datetime.now(timezone.utc)
    if start.tzinfo is None or end.tzinfo is None or not start < end <= now:
        raise ValueError("Request a nonempty past interval with explicit UTC offsets")
    if any(t.minute or t.second or t.microsecond for t in (start, end)):
        raise ValueError("H1 capture boundaries must be on an hour")
    if output.exists():
        raise FileExistsError("Capture destination already exists; choose a new directory")
    terminal, account = require_demo(api)
    if account.currency != "USD":
        raise ValueError("Only USD-account EURUSD research is supported")
    symbol = api.symbol_info("EURUSD")
    if symbol is None or not symbol.visible:
        raise ValueError("Exact EURUSD must already be visible in Market Watch")
    if symbol.currency_base != "EUR" or symbol.currency_profit != "USD":
        raise ValueError("Unexpected EURUSD contract currencies")
    clock = clock_observation(api)
    rows = []
    cursor = start
    windows = []
    while cursor < end:
        stop = min(cursor + timedelta(days=28), end)
        require_demo(api)
        rates = api.copy_rates_range("EURUSD", api.TIMEFRAME_H1, cursor, stop - timedelta(seconds=1))
        require_demo(api)
        if rates is None or len(rates) == 0:
            raise ValueError("A requested history window is unavailable; no complete capture written")
        count = 0
        for row in rates:
            time = datetime.fromtimestamp(int(row["time"]), timezone.utc)
            if not cursor <= time < stop:
                raise ValueError("Terminal returned history outside the requested window")
            if rows and time <= datetime.fromisoformat(rows[-1]["time"]):
                raise ValueError("Terminal returned duplicate or unordered history")
            rows.append({"time": time.isoformat(), **{k: float(row[k]) for k in ("open", "high", "low", "close")},
                         "tick_volume": int(row["tick_volume"]), "spread_points": int(row["spread"]),
                         "real_volume": int(row["real_volume"])})
            count += 1
        windows.append({"start": cursor.isoformat(), "end_exclusive": stop.isoformat(), "rows": count})
        if progress:
            progress(f"Captured history window {len(windows)}: {count} H1 candles")
        cursor = stop
    require_demo(api)
    output.mkdir(parents=True, exist_ok=False)
    raw = output / "rates.csv"
    with raw.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {"schema_version": 2, "kind": "mt5_readonly_capture", "symbol": "EURUSD",
                "timeframe": "H1", "price_side": "bid", "synthetic": False,
                "source": "Connected MT5 demo terminal; provider identity not exported",
                "captured_utc": now.isoformat(),
                "timestamp_convention": "Raw API numeric labels rendered with UTC formatter; UTC meaning unverified",
                "clock_observation": clock,
                "requested_start": start.isoformat(), "requested_end_exclusive": end.isoformat(),
                "first_bar": rows[0]["time"], "last_bar": rows[-1]["time"], "rows": len(rows),
                "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "windows": windows,
                "current_snapshot": {"account_type": "demo", "account_currency": account.currency,
                                     "leverage": account.leverage, "terminal_algo_trading": bool(terminal.trade_allowed),
                                     "symbol": {k: getattr(symbol, k) for k in SPEC_FIELDS}},
                "package_version": str(api.__version__),
                "limitations": ["Current contract properties do not verify historical terms",
                                 "API date request boundaries are raw labels; historical UTC mapping is unverified",
                                 "Broker daily rollover timezone is unverified",
                                 "Historical commission and swap schedules are unavailable",
                                 "Bar spread is a recorded minimum, not an executable entry quote",
                                 "No ticks, order history, account identity or credentials exported"]}
    (output / "capture.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return metadata
