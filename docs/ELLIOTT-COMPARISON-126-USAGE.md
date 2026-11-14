# Five-strategy comparison — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. This is invented
software evaluation with no broker connection, actual account lookup or order API.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/elliott-comparison-126-example
python3 scripts/elliott-comparison-126.py create-fixture ew_long_target data/elliott-comparison-126-example/input.json
python3 scripts/elliott-comparison-126.py freeze data/elliott-comparison-126-example/input.json data/elliott-comparison-126-example/frozen.json
python3 scripts/elliott-comparison-126.py evaluate data/elliott-comparison-126-example/input.json data/elliott-comparison-126-example/frozen.json data/elliott-comparison-126-example/run
python3 scripts/elliott-comparison-126.py verify data/elliott-comparison-126-example/input.json data/elliott-comparison-126-example/frozen.json data/elliott-comparison-126-example/run
```

The output root must not exist for evaluate. Verify re-derives all prefixes,
aggregation, signals, ledgers and statistics without writing files. Preserve a
failed or partially written root and choose a new name;126 adds no batch resume.
Existing120/125 account checkpoint/restore remains available separately. Local
checksums and reconstruction establish consistency, not signed source authenticity
or broker reconciliation.

`create-fixture --help` lists26 paths:20 unchanged execution125 cases prefixed ew_,
plus six unchanged daily-run122 cases prefixed daily_. Prices, clocks and calendar
declarations remain invented2000–2003. No optimization or market/live mode exists.

Each of two disjoint periods runs five unique candidates under two unchanged
cost profiles: EWPB_D124, T12_D, MR20_D, MIX50_D and CASH. CASH is already one of
the four117 candidates. Every row starts with separate freshUSD10,000. No equity,
position, reservation or pause carries to the later period, and no capitals or
returns are summed. Models retain their different fixed stop/sizing rules.

Each period retains shared raw-prefix input/freeze and aggregation, daily-wave
input/freeze and observations, Elliott compiled input/freeze, legacy compiled
input/freeze, comparisons.json with every account and statistics, and a partition
report. Both adapters must have identical quote/source/receipt/prices and published
feature identities. Root run-report.json includes all20 planned cells; REPORT.md
provides a readable account table. Common history/endpoint failure makes all ten
period cells unavailable. A nonpositive modeled exit makes only the affected
account unavailable; no partial ledger or return is reported for it.

Statistics include gross/net, fees and financing, observed equity drawdown,
exposure/flat intervals, turnover, price-adjustment memos, largest losses, entry
estimate breaches and monthly/quarterly observed windows. Memos are already
embedded in gross fill prices and must not be charged again. Sparse observed
windows are not certified calendar closes. Missing windows break return anchors;
no-trade or missing-denominator ratios remain null. Stops and daily entry pauses
are not guaranteed loss caps.

Run the comparison tests with:

```bash
PYTHONPATH=src:tests python3 -m unittest test_elliott_comparison_126 -v
```

Read [the frozen contract](ELLIOTT-COMPARISON-126-PROTOCOL.md) and
[results](ELLIOTT-COMPARISON-126-RESULTS.md). These constructed paths cannot rank
strategies or validate a combination. Market clocks/data/costs and genuinely
untouched chronological evidence remain unresolved; actual orders and real-money
execution remain unavailable. Synthetic DEMO mode is not an actual account check.
