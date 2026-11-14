# Daily features118 — offline usage

Run from the canonical WSL repository. No installation, account, SDK, broker or
terminal is needed. Python3.11+ and the standard library suffice.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/daily-features-118-example
python3 scripts/daily-features-118.py create-fixture trend_up_reentry_long data/daily-features-118-example/fixture.json
python3 scripts/daily-features-118.py freeze data/daily-features-118-example/fixture.json data/daily-features-118-example/frozen.json
python3 scripts/daily-features-118.py evaluate data/daily-features-118-example/fixture.json data/daily-features-118-example/frozen.json data/daily-features-118-example/features.json
```

Files are created exclusively; existing artifacts are rejected, not overwritten.
Use a fresh directory or filename for another demonstration. Preserve frozen
inputs/manifests/reports. Changing source, tests, protocol, schema, rule metadata
or fixture bytes invalidates an existing freeze. Do not edit the completed
`data/daily-features-118-invented-demo` demonstration to rerun it.

The example's trend/reentry signals both point long; its mixture multiplier is1.
`trend_up_reentry_none` has multiplier0.5. `trend_up_reentry_short` cancels with0.
All11 available case names are exposed by CLI help. These hand-constructed examples
check fixed arithmetic and abstention, not forecast quality. The output contains
no return, position or fill. Multipliers are not sized lots or submitted orders.

The library's `decisions(value)` accepts the exact invented schema in
[the protocol](DAILY-STRATEGY-118-PROTOCOL.md). It returns immutable decisions
with availability, target and observed-prefix lineage. A later valid bar can be
present in the bundle without affecting a decision for an earlier target. Open,
missing, unobservable or conflicting required sessions reject the bundle. No
market source can become admitted by adding a qualification boolean or changing
its clock label; this prototype has no market-admission path.

Focused verification command:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_daily_features_118.py' -v
```

The completed results are in [DAILY-STRATEGY-118-RESULTS.md](DAILY-STRATEGY-118-RESULTS.md).
Earlier hourly engines and the117 declaration are unchanged. The historical117
declaration's unimplemented status refers to its original rule freeze;118 now
implements the pure feature portion, not a market or execution adapter.
