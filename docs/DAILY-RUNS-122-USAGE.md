# Daily runs122 — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. No terminal,
broker, SDK, credentials or actual account is required.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/daily-runs-122-example
python3 scripts/daily-runs-122.py create-fixture targets data/daily-runs-122-example/input.json
python3 scripts/daily-runs-122.py freeze data/daily-runs-122-example/input.json data/daily-runs-122-example/frozen.json
python3 scripts/daily-runs-122.py evaluate data/daily-runs-122-example/input.json data/daily-runs-122-example/frozen.json data/daily-runs-122-example/run
```

The output root must not exist. All six fixed cases are invented. Each declares
development and a later period, with explicit boundaries and required last-quote
timestamps. The later label does not certify untouched market data. Every funded
comparison starts at$10,000 with no incoming position, reservation or pause.

Partition attempt directories contain derived121 input/freeze, aggregation,
derived120 input/freeze, fill and statistics reports when available, and a final
partition report with hashes. Unavailable partitions retain their reason and no
return report. `run-report.json` contains16 planned separate toy comparisons,
including unavailable ones; do not add their capitals as a portfolio.

Statistics report fill costs, financing, net expectancy, turnover, holding/flat
intervals, observed monthly/quarterly windows, drawdown and losses beyond entry
estimates. Price-adjustment memos are embedded in fill prices and are not extra
debits. Sparse observed marks are not certified calendar-close market returns.
Short duration/sample and unqualified input remain explicit insufficiency.

For checked incremental recovery, use `Coordinator(input, manifest)`,
`step(output_root)`, `checkpoint()`, `Coordinator.restore(input, manifest,
checkpoint_string, output_root)`, `run(output_root)` and `report()`. Persist the
checkpoint after each completed partition. Restore checks/rebuilds only completed
prefixes. An interrupted uncommitted attempt stays preserved; resume uses a new
numbered attempt and counts the completed partition once. A completed repeated
run is idempotent. Do not overwrite files to resume or change a frozen input.

The CLI saves `run-checkpoint.json` as a JSON envelope. To use it with restore,
read that file's text; checksums bind local state and artifacts, not feed authenticity.
Existing roots need checked restore; a fresh CLI run never overwrites an old root.

Focused verification includes all retained direct stages:

```bash
PYTHONPATH=src:tests python3 -m unittest test_daily_runs_122 test_daily_bars_121 test_daily_fills_120 test_daily_risk_119 test_daily_features_118 -v
```

Read [the frozen contract](DAILY-RUNS-122-PROTOCOL.md) and
[results](DAILY-RUNS-122-RESULTS.md). No market validation, forward paper execution,
strategy selection or orders are enabled. No real-money toggle exists.
