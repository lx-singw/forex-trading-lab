# Daily bars121 — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. No broker,
terminal, SDK or actual account is required.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/daily-bars-121-example
python3 scripts/daily-bars-121.py create-fixture weekend_gap data/daily-bars-121-example/quotes.json
python3 scripts/daily-bars-121.py freeze data/daily-bars-121-example/quotes.json data/daily-bars-121-example/integration-frozen.json
python3 scripts/daily-bars-121.py evaluate data/daily-bars-121-example/quotes.json data/daily-bars-121-example/integration-frozen.json data/daily-bars-121-example/run
```

The run directory must not exist. Existing input, freeze and output files are
never overwritten. The eight fixed cases include complete paths, missing/stale
coverage and a final unfinished session. All prices and clocks are invented.

`aggregation.json` records bars, publication evidence, excluded quote outcomes
and pending sessions. Completed bars are reconstructed from the same bid/ask
messages used by accounting. The exact midpoint evidence is retained alongside
the float OHLC required by118. Sparse invented coverage rules are not proof of
a complete tick feed or broker calendar.

For a usable invented pipeline, `fills-input.json` contains the derived118 history
and original bid/ask execution quotes. Its separate `fills-frozen.json` is written
before `fills-report.json`, which contains eight independent candidate/cost accounts.
`pipeline-report.json` binds every derived artifact and reports status/reason.
Missing required history produces unavailable status and no return report; it is
not a zero return. A still-open endpoint may be used for boundary execution but
cannot supply a daily feature. No strategy ranking follows from toy ledger values.

`Replay(input, manifest)` supports `step(message)`, `features(...)`, `checkpoint()`,
checked `restore(...)`, `run()` and `report()`. Restore rebuilds only the observed
prefix and verifies pending/finalized state. Latest identical message replay is
idempotent; changed/older duplicates reject. Hashes are consistency checks, not
source authentication. `compile_fills(replay)` derives120 input after aggregation.

Focused verification includes retained118/119/120 dependencies:

```bash
PYTHONPATH=src:tests python3 -m unittest test_daily_bars_121 test_daily_fills_120 test_daily_risk_119 test_daily_features_118 -v
```

Read [the frozen contract](DAILY-BARS-121-PROTOCOL.md) and
[results](DAILY-BARS-121-RESULTS.md). Source/UTC/age/calendar/coverage/contract/cost
qualification, market performance, forward paper testing and all orders remain
unavailable. Do not provide credentials or actual account identifiers.
