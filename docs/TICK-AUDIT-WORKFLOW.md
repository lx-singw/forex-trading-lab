# Bounded read-only tick audit

Run from the repository root. The Windows terminal must already be running on
an actual demo account. Capture checks the account type before and after reads;
it never enables trading, logs identity or submits orders. Use new output paths.

```powershell
$labPython = Join-Path $env:USERPROFILE '.forex-demo-lab\mt5-python\Scripts\python.exe'
& $labPython scripts/capture-ticks.py `
  --terminal 'C:\Program Files\MetaTrader 5\terminal64.exe' `
  --start 2024-01-04T19:00:00Z --end 2024-01-05T09:00:00Z `
  --output data/new-tick-capture
```

These bounds refer to raw API source labels. The `Z` syntax does not validate
the terminal's historical UTC interpretation. Requests are limited to 48 hours
and split into six-hour chunks. Inclusive API endpoints are filtered to each
half-open chunk, retaining final-millisecond events and same-millisecond order.
Empty reads and API errors remain distinct; neither establishes completeness.
Interrupted `.partial` files are not valid captures.

Analyze offline in WSL (standard-library Python):

```bash
python3 scripts/audit-ticks.py --capture data/new-tick-capture \
  --raw-bars data/mt5-2024-2025-capture-v2/rates.csv \
  --reference-report reports/experiment-001-development.json --trade-index 0 \
  --output reports/new-tick-audit.json
```

Omit `--reference-report` and `--trade-index` for a data-only comparison. A trade
comparison requires the matching development report and coverage through its
closing hour. It diagnoses fixed-position exits; it is not a strategy replay
or a new performance result. Report times use the explicitly provisional
source-clock interpretation described in the historical-data documentation.

To repeat the bounded July H1/M1/H1 history probe in Windows:

```powershell
& $labPython scripts/probe-history-gap.py `
  --terminal 'C:\Program Files\MetaTrader 5\terminal64.exe' `
  --start 2024-07-02T12:00:00Z --end 2024-07-03T01:00:00Z `
  --output data/new-gap-probe.json
```

Response validation checks requested bounds, ordering, period alignment and
OHLC/count validity even when MT5 reports success. Invalid rows are diagnostic
evidence only. Do not import them or overwrite the original experiment.

API references: [copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py),
[tick fields](https://www.mql5.com/en/docs/constants/structures/mqltick) and
[inclusive range semantics](https://www.mql5.com/en/docs/series/copyticksrange).
Local observations and unresolved timestamp discrepancies are documented in
[the results](TICK-AUDIT-RESULTS.md).
