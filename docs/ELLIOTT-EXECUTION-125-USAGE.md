# Elliott standalone simulator — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. This simulator
has no broker connection, actual account lookup or order-placement capability.
All quotes, clocks and calendar declarations are invented2000–2003 values.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/elliott-execution-125-example
python3 scripts/elliott-execution-125.py create-fixture long_target data/elliott-execution-125-example/input.json
python3 scripts/elliott-execution-125.py freeze data/elliott-execution-125-example/input.json data/elliott-execution-125-example/frozen.json
python3 scripts/elliott-execution-125.py evaluate data/elliott-execution-125-example/input.json data/elliott-execution-125-example/frozen.json data/elliott-execution-125-example/run
```

The output root must not exist. The CLI lists twenty fixed paths with
`create-fixture --help`; it offers no parameter search, market input, mixture or
live mode. The raw wrapper declares two disjoint periods and exact endpoints.
Each period/profile/model starts separately with freshUSD10,000. Later warmup
may include prior prices but imports no funded positions, profits or pause.

Each period directory retains derived121 quote input/freeze and aggregation,
derived124 daily input/freeze and observations, compiled125 quote/feature input
and ledger freeze, account reports when available, and a hash-bound partition
report. Missing history or unsafe endpoints retain their reason and no return
report, including cash. `run-report.json` contains all eight planned comparisons.
Do not add their capitals or P&L as a portfolio.

The standalone entry stop remains the observed wave invalidation. The cost-aware
lot floor includes actual modeled entry-to-stop distance, exit slip, commissions
and available margin; target is2R from that entry/stop. Ledger records retain every
reserve/fill/financing/exit/release and calculated equity/drawdown mark. Gross P&L
already embeds bid/ask and modeled slippage; do not charge them again. Gaps and
rollovers can exceed the entry estimate. Actual venue contract/costs remain unknown.

For checked account-level recovery, load the period's `compiled-input.json` and
`compiled-frozen.json` with `Account(path, manifest, profile, candidate)`, process
its events with `step(event)`, save `checkpoint()`, then use
`Account.restore(path, manifest, checkpoint_dictionary, profile, candidate)`.
`run()` finishes at the final executable quote. Latest exact event and completed
finish/run are idempotent. Restore rebuilds only the completed event prefix and
rejects forged cash/levels/slots/consumption, even with new checksums. The batch
CLI does not resume a partially written root; preserve it and choose a new name.
There is no crash-durability or outside-interference guarantee.

Only the public raw-stream path derives bars/signals. Compiled input/freezes are
internal artifacts; they are not a public path for injecting supplied signals.
Local hashes establish consistency, not signed origin or broker reconciliation.
Synthetic DEMO guards are not actual account-type checks. A future order component
would still require an actual DEMO lookup and recheck; no such component exists here.

Run focused tests:

```bash
PYTHONPATH=src:tests python3 -m unittest test_elliott_execution_125 test_elliott_waves_124 test_daily_bars_121 test_daily_fills_120 test_daily_risk_119 test_daily_features_118 -v
```

Read [the frozen contract](ELLIOTT-EXECUTION-125-PROTOCOL.md) and
[results](ELLIOTT-EXECUTION-125-RESULTS.md). These short constructed paths establish
software behavior only; market profitability and forward-paper validation remain
unavailable. All actual orders and real-money execution remain unavailable.
