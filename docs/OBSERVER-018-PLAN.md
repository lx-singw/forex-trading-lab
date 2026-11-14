# Observation runtime experiment 018

Declared 2026-10-06 before compilation or execution. Preserve the original
`mt5/Experts/ForexDemoObserver.mq5` and fixed baseline. No market files, broker
connection, performance evaluation or order submission are part of this stage.

Generate an include containing the exact original observer bytes from
`datetime last_closed = 0;` onward. A separate MQL harness redirects only its
platform APIs to synthetic responses and renames its event handlers. Execute
these original function bodies inside MT5's Math calculations tester. This
tests compiled MQL decisions with controlled responses; it does not establish
actual terminal/broker account-switch safety or execution readiness.

Freeze all synthetic fixtures and Python baseline expectations before compile.
Use 51 closed hourly candles dated January 2024. Cover BUY, SELL, flat history,
true-range gaps, zero ATR, warmup, copy failure, duplicate/restart suppression,
closed/current-hour discontinuities, invalid/wide quotes, positions, pending
orders, wrong symbol/timeframe, disconnected/REAL/CONTEST/unknown/error account
responses, stale errors and account changes during the final recheck. The
copy adapter records whether the original requests shift 1 and count 51.
Compare exact case inventory, statuses, read counts and state; compare direction
and ATR distance with Python's frozen baseline (absolute tolerance 1e-12).
Every declared case must pass; failed attempts stay on disk. No selective pass.

Use an isolated, uniquely named portable Windows runtime with installed MT5
binaries, no copied account configuration or primary terminal settings. Disable
expert trading, DLL imports, remote/cloud agents and optimization. Math mode
uses no market history. Compilation and runtime are separate evidence. A
unique result file under Common/Files/ForexDemoLab/observer018 is permitted;
reject existing output. If first-run setup or tester availability prevents
execution, preserve compiled artifacts and state that runtime remains unverified.
No account registration or paid services. Do not capture account identifiers.

Bind source, generated inputs and previous 017 report hashes in an exclusive
ledger and source archive before execution. Verify the ledger before compile
and result checking. Record binary/config/output hashes and compiler diagnostics
separately. Software tests and successful runtime cases cannot approve annual
data, profitability, sizing, loss limits or automated execution. Existing data
gates, reserved November–December 2026 and consumed 2025 remain unchanged.

Primary references: [Math calculations](https://www.mql5.com/en/docs/runtime/testing)
calls initialization, tester and deinitialization without ticks/history;
[startup options](https://www.metatrader5.com/en/terminal/help/start_advanced/start)
document portable mode, custom configuration and local tester settings;
[file sandbox](https://www.mql5.com/en/docs/files/fileopen) supports a shared
Common/Files output. These platform facts do not substitute for measured results.
