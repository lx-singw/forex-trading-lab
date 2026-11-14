# Daily fills120 — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. No MT5, SDK,
credentials, broker or account connection is required.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/daily-fills-120-example
python3 scripts/daily-fills-120.py create-fixture long_target data/daily-fills-120-example/fixture.json
python3 scripts/daily-fills-120.py freeze data/daily-fills-120-example/fixture.json data/daily-fills-120-example/frozen.json
python3 scripts/daily-fills-120.py evaluate data/daily-fills-120-example/fixture.json data/daily-fills-120-example/frozen.json data/daily-fills-120-example/ledger.json
```

Files are created exclusively. Use new names for a new run; preserve existing
frozen inputs and outputs. The CLI exposes14 invented cases. Evaluation writes
eight separate candidate/profile accounts, including no-trade and loss outcomes.
Their capitals and profits must not be added together as a portfolio. Numeric
economic fields are decimal strings with precision50 and no cent rounding.

Reports include original entry proposals, reservation transitions, entry/exit
fills, financing per rollover, cash, open equity, used/free margin, daily pause
and drawdown. Toy net/return summaries reconcile the ledger; they are not market
performance or evidence that a strategy wins. Inputs accept initial flat invented
cash only; supplied held positions/equity/free-margin/account identifiers reject.
Synthetic DEMO checks are not an actual broker-account lookup.

`Replay(fixture, manifest, profile, candidate)` supports `step(event)`, `finish()`,
`checkpoint()`, checked `restore(...)`, `run()` and `report()`. State is copied on
read. Identical latest event/finish is idempotent. Restore rebuilds only the observed
prefix and checks all economic state. Local checksums do not authenticate a feed.

Finish closes a held position on the final executable observed quote with costs.
A stale/repeated/closure endpoint rejects instead of silently using an earlier
price. Stale/closure quotes cannot execute; financing continues through elapsed
rollovers. Wide quotes can close positions even though they block entry.

Focused verification includes both retained direct dependencies:

```bash
PYTHONPATH=src:tests python3 -m unittest test_daily_fills_120 test_daily_risk_119 test_daily_features_118 -v
```

Read [the frozen contract](DAILY-FILLS-120-PROTOCOL.md) and
[results](DAILY-FILLS-120-RESULTS.md). Actual source/clock/coverage/cost qualification,
market evaluation, forward paper testing and all orders remain unavailable.
