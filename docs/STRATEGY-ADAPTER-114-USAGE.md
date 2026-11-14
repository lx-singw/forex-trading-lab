# Strategy adapter114 — local use

From the WSL repository root, use Python3. The CLI has no connection, broker API,
orders or live mode. It accepts the distinct invented114 format only; prior113
fixtures and native captures cannot be evaluated through it. Keep old artifacts.

Create a new local directory, then create and freeze all cases before evaluating:

```bash
mkdir data/strategy-adapter-114-local
python3 scripts/strategy-adapter-114.py create-fixture continuation data/strategy-adapter-114-local/continuation.json
python3 scripts/strategy-adapter-114.py create-fixture reversal data/strategy-adapter-114-local/reversal.json
python3 scripts/strategy-adapter-114.py create-fixture flat data/strategy-adapter-114-local/flat.json
python3 scripts/strategy-adapter-114.py freeze data/strategy-adapter-114-local/continuation.json data/strategy-adapter-114-local/continuation-frozen.json
python3 scripts/strategy-adapter-114.py freeze data/strategy-adapter-114-local/reversal.json data/strategy-adapter-114-local/reversal-frozen.json
python3 scripts/strategy-adapter-114.py freeze data/strategy-adapter-114-local/flat.json data/strategy-adapter-114-local/flat-frozen.json
python3 scripts/strategy-adapter-114.py evaluate data/strategy-adapter-114-local/continuation.json data/strategy-adapter-114-local/continuation-frozen.json data/strategy-adapter-114-local/continuation-report.json
python3 scripts/strategy-adapter-114.py evaluate data/strategy-adapter-114-local/reversal.json data/strategy-adapter-114-local/reversal-frozen.json data/strategy-adapter-114-local/reversal-report.json
python3 scripts/strategy-adapter-114.py evaluate data/strategy-adapter-114-local/flat.json data/strategy-adapter-114-local/flat-frozen.json data/strategy-adapter-114-local/flat-report.json
```

Each report includes C00/C05/C06/CASH, base/adverse costs and development/validation:
16 independent checks. Run every predefined case; don't select the winning path.
All comparisons use common201-hour warmup and fresh capital per partition. Costs,
trades, decisions, lineage, exposure and corrected drawdown are in the report.
There is no portfolio aggregate, selected strategy or combination weight.

Files are created exclusively. Existing files, changed fixture/source/config/cost/
candidate bindings and invalid quotes reject with a fixed error and exit1.
After code changes, keep old manifests/results and freeze new ones in new paths.
Hashes check consistency, not authenticity or market qualification.

Python `Replay(fixture, manifest, scenario='base', partition='development',
candidate='C00')` supports incremental `step`, `checkpoint` and matching `restore`.
Restore requires the same candidate/scenario/partition; cross-candidate state
rejects. It also validates current fixture/code/config and event cursor. `finish`
requires every partition event; an identical latest duplicate is idempotent.
Validation replays earlier prices without opening positions until its boundary.

`inspect-capture PATH --format 107|109|111` remains diagnostic. It returns
`performance_unavailable` and never constructs a strategy engine. It does not
translate native clocks or qualify data. Orders and real-money execution remain
unavailable. No MT5 script launch is involved.

Focused verification:

```bash
PYTHONPATH=src:tests python3 -m unittest test_strategy_adapter_114 test_strategy_experiment_028 test_shadow_engine_113 test_tick_simulation test_simulation test_model test_forward_capture_111 test_private_recorder_107 test_execution_metrics -q
```

Read [results and limitations](STRATEGY-ADAPTER-114-RESULTS.md) before interpreting
any invented return. Historical/provider closures and reserved market periods remain.
