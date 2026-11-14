# Combination stress116 — local use

Run offline from the WSL repository root. No broker connection, execution API or
MT5 launch is involved. Create the matrix in a new directory; the command generates
all eight accepted and nine malformed cases and freezes their exact bytes, rules,
costs, source/protocol versions and expected behavior before evaluation.

```bash
python3 scripts/combination-stress-116.py create-matrix data/combination-stress-116-local
python3 scripts/combination-stress-116.py evaluate data/combination-stress-116-local data/combination-stress-116-local/matrix-report.json
```

Creation and report writing reject existing artifacts. A failed partial creation
is preserved; use a new directory after resolving the failure. Changed inputs or
source files invalidate the binding. No malformed source is silently repaired.
Declared omissions and resequencing apply only to newly generated invented cases.

The report retains all96 rule/cost/partition paths, nine input-rejection outcomes
with no performance metrics,576 checkpoint-fault checks, and every verification
failure. Exit status is nonzero when matrix verification fails. Accepted paths
include trades, entry votes, lineage, costs, sizing/risk checks, independent ledger,
restart state and equality. Full decision lists are represented by their count and
canonical SHA256; reproduce them with unchanged115 Replay on the frozen fixture
and its115 manifest. No path selection or aggregate portfolio return is produced.

`restore_checked(fixture, manifest, checkpoint, scenario='base',
partition='development', rule='UNANIMOUS')` returns115 Replay only after its original
checks and a reconstruction of the exact observed prefix match complete state.
It checks altered balances/stops/pauses even if checksums are recomputed. This is
bounded offline replay, not authentication, a live checkpoint format or broker
reconciliation. Source/config/rule/cost/fixture bindings still apply.

The independent ledger checks reported admissions against observed side-specific
fills, floor sizing and risk, one-position limits, spread/pause/stale-hour guards,
calendar financing, cost reconciliation and corrected executable-fill equity.
It does not independently discover missing strategy entries or authenticate
prices. Tests separately compare all paths with the retained114 simulator using
independent agreement arithmetic.

Native captures remain diagnostic:

```bash
python3 scripts/combination-stress-116.py inspect-capture PATH --format 111
```

Formats107/109/111 return `performance_unavailable`; native quotes cannot enter
the matrix or simulation route. No guessed clock offset or paper/order promotion.

Focused verification:

```bash
PYTHONPATH=src:tests python3 -m unittest test_combination_stress_116 test_strategy_combination_115 test_strategy_adapter_114 test_strategy_experiment_028 test_shadow_engine_113 test_tick_simulation test_simulation test_model test_forward_capture_111 test_private_recorder_107 test_execution_metrics -q
```

Read the [fixed protocol](COMBINATION-STRESS-116-PROTOCOL.md) and
[results and limitations](COMBINATION-STRESS-116-RESULTS.md). These constructed
paths test software behavior, not profitability or the probability of a gap loss.
Stops and daily entry pauses do not guarantee a maximum loss.
