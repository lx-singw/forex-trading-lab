# Historical data workflow

The research package stays dependency-free in WSL. The optional collector uses
Windows Python and the official MetaTrader5 package to read an **already running**
terminal. It never calls an order API, changes terminal settings, logs in to a
different account, or creates an account. Each read is guarded by the actual
demo account type; a switch to real/contest aborts capture.

## 1. Read-only capture on Windows

From this repository in PowerShell, create an isolated optional runtime once:

```powershell
$labRuntime = Join-Path $env:USERPROFILE '.forex-demo-lab\mt5-python'
py -3.13 -m venv $labRuntime
$labPython = Join-Path $labRuntime 'Scripts\python.exe'
& $labPython -m pip install -r scripts/requirements-mt5.txt
```

For this machine the runtime already exists; do not recreate it unnecessarily.
Rediscover the executable with `Get-Process terminal64 | Select-Object Path`, then:

```powershell
& $labPython scripts/collect-mt5.py `
  --terminal 'C:\Program Files\MetaTrader 5\terminal64.exe' `
  --start 2024-01-01T00:00:00Z --end 2026-01-01T00:00:00Z `
  --output data/mt5-new-capture
```

The output directory must not exist. Requests use 28-day windows and end-exclusive
boundaries. They are **API source-clock labels** until the timestamp convention
is established. Files are published only after all windows return data and
account checks pass. A failed filesystem write can leave an incomplete directory;
it is not a valid capture without matching `capture.json` and `rates.csv`.

The collector exports bid OHLC, bar spread/volume, requested and observed ranges,
hashes, a current clock comparison and selected current contract properties.
It excludes account identity, balance, credentials and order history. Current
properties do not prove historical contract/cost terms. Collection may cause
MT5 to download public history through its existing connection.

## 2. Interpret timestamps, then normalize

The API documentation says UTC, but this installation returned quote labels
about three hours ahead of system UTC. The collector preserves raw numeric
labels; its formatted `+00:00` suffix is **not proof of UTC meaning**. The
normalizer requires `--api-timezone` and `--timezone-notes`; it rejects an
`Etc/UTC` interpretation if the collector's clock witness contradicts it.
A current offset does not establish historical DST rules. Never apply today's
offset to all historical dates.

Example in WSL for the explicitly provisional EET/EEST scenario:

```bash
export PYTHONPATH=src
python3 -m forex_demo_lab.cli import-mt5 \
  --input data/mt5-new-capture/rates.csv \
  --capture data/mt5-new-capture/capture.json \
  --output data/eurusd-new-import \
  --source 'Connected demo MT5 EURUSD H1 history' \
  --as-of '<exact captured_utc string from capture.json>' \
  --api-timezone Europe/Helsinki \
  --timezone-notes 'Provisional EET/EEST assumption; historical DST unverified' \
  --point-size 0.00001 --spread-pips 1.2 \
  --spread-notes 'Hypothetical constant spread; not the historical bar minimum'
```

Replace the as-of placeholder with the captured timestamp. To avoid PowerShell
automatic date conversion when reading JSON, pass that timestamp as an ISO-8601
string or explicitly format the converted DateTime with `ToString('o')`.

Native MT5 tab-separated or comma-separated exports are also supported in
UTF-8 (optional BOM) and BOM-marked UTF-16. Expected native header:

```text
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>
```

Use actual tabs/commas, not the spaces in the display above. Date/time format is
`YYYY.MM.DD HH:MM:SS`. Supply `--source-timezone` instead of `--api-timezone`
and omit `--capture` for native files. Confirm EURUSD, bid prices and H1 export
settings: sparse timestamps alone cannot prove the selected timeframe.

The importer rejects invalid prices, negative/nonfinite fields, duplicate or
unordered bars and ambiguous/nonexistent DST wall times. It removes only a
currently forming final candle and records that count; future rows are errors.
Gaps are recorded and never filled. Source bytes, completed normalized prices,
point size and time/spread assumptions are linked by hashes in `provenance.json`.

The bar spread is a historical statistic. We retain it for auditing only; using
its minimum to decide whether entry spread was acceptable can leak future
information. Current imports use an explicit fixed spread hypothesis. They
do not reconstruct intrabar bid/ask paths or measured historical entry spreads.

## 3. Freeze and evaluate

```bash
python3 -m forex_demo_lab.cli freeze \
  --data data/eurusd-new-import/bars.csv \
  --provenance data/eurusd-new-import/provenance.json \
  --config config/baseline.json --holdout-start 2025-01-01T00:00:00Z \
  --manifest reports/new-experiment-manifest.json \
  --source 'Connected demo MT5 EURUSD H1 history' \
  --cost-notes 'List assumed/verified spread, commission, swaps, slippage, margin and broker day'
python3 -m forex_demo_lab.cli run \
  --data data/eurusd-new-import/bars.csv --manifest reports/new-experiment-manifest.json \
  --partition development --output reports/new-experiment-development.json
python3 -m forex_demo_lab.cli run \
  --data data/eurusd-new-import/bars.csv --manifest reports/new-experiment-manifest.json \
  --partition holdout --output reports/new-experiment-holdout.json
```

Market experiments require matching provenance. Boundary dates may fall on
market holidays; an hourly cutoff separates the partitions without requiring a
tradeable candle at that instant. Freeze strategy and assumptions before looking
at either result. The 2025 holdout in Experiment 001 has already been examined;
it is no longer untouched data for future strategy changes.

Original synthetic manifests used engine version 1; provenance-aware freezing
uses version 2. Old reports are retained as records, but old manifests correctly
reject replay with changed code. Generate a newly named synthetic experiment to
test the current code. The market manifest also locks the exact code used.

## Evidence and remaining limitations

[Experiment 001 declaration](EXPERIMENT-001.md) and
[results](EXPERIMENT-001-RESULTS.md) preserve the first historical run. It remains
unvalidated research: historical timezone, costs, weekday gaps and real-tick
execution need verification. No demo execution is authorized by these results.

Primary references:

- [Official copy_rates_range API and its UTC claim](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py)
- [MT5 bar construction and recorded minimum spread](https://www.metatrader5.com/en/terminal/help/trading_advanced/price_data)
- [Symbol properties from the Python API](https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfo_py)
- [Historical MetaQuotes discussion of EET/DST](https://www.mql5.com/en/forum/63796)
