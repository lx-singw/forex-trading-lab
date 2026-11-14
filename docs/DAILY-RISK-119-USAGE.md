# Daily risk119 — offline usage

Use the canonical WSL checkout and Python3.11+ standard library. No broker,
terminal, SDK, credentials or actual account snapshot is required.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/daily-risk-119-example
python3 scripts/daily-risk-119.py create-fixture full_long data/daily-risk-119-example/fixture.json
python3 scripts/daily-risk-119.py freeze data/daily-risk-119-example/fixture.json data/daily-risk-119-example/frozen.json
python3 scripts/daily-risk-119.py evaluate data/daily-risk-119-example/fixture.json data/daily-risk-119-example/frozen.json data/daily-risk-119-example/proposals.json
```

Evaluation reports eight separate candidate/profile comparisons, each with its own
invented state. Do not add their capital or proposals as one portfolio. Files are
created exclusively; choose new names for another example. Preserve frozen inputs
and outputs. The completed `data/daily-risk-119-invented-demo` matrix is immutable.

The CLI exposes22 fixed cases through help, including full/half budgets, opposing
signals, minimum risk/margin, wide/stale quotes, pauses, held/reserved slots,
closure/gap behavior and signal changes. Results contain proposal quantities and
estimated levels, not fills or profits. The initial account and executable-equity
marks are invented inputs. Synthetic DEMO trade-mode rejection is not an actual
MT5 account-type check. Actual market/paper/order admission remains unavailable.

For a bound prefix replay, `Replay(fixture, manifest, profile, candidate)` exposes
`step(event)`, `checkpoint()`, checked `restore(...)`, `run()` and `report()`.
`state` returns a defensive copy. Latest identical replay changes no state;
conflicting events and rehashed state changes reject. Restore reconstructs only
the observed prefix; a checksum is not an authenticity or broker-reconciliation
guarantee. Reservations do not imply fills and are not released in119.

Focused tests, including the directly dependent118 feature suite:

```bash
PYTHONPATH=src:tests python3 -m unittest test_daily_risk_119 test_daily_features_118 -v
```

Read [the119 contract](DAILY-RISK-119-PROTOCOL.md) and
[results](DAILY-RISK-119-RESULTS.md). No other source or terminal settings are changed.
