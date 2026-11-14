# Strategy combination115 — local use

Run from the WSL repository root with Python3. The CLI works offline and has no
broker connection, execution API, orders or live mode. It reuses the strict
invented114 quote format, with a distinct115 manifest for the fixed member/rule
definitions. Earlier114 manifests are preserved and cannot be used as115 bindings.

Create all five cases and freeze them before producing demonstration reports:

```bash
mkdir data/strategy-combination-115-local
for case in continuation reversal flat partial_agreement conflicting_votes; do
    python3 scripts/strategy-combination-115.py create-fixture "$case" "data/strategy-combination-115-local/$case.json" || exit 1
    python3 scripts/strategy-combination-115.py freeze "data/strategy-combination-115-local/$case.json" "data/strategy-combination-115-local/$case-frozen.json" || exit 1
done
for case in continuation reversal flat partial_agreement conflicting_votes; do
    python3 scripts/strategy-combination-115.py evaluate "data/strategy-combination-115-local/$case.json" "data/strategy-combination-115-local/$case-frozen.json" "data/strategy-combination-115-local/$case-report.json" || exit 1
done
```

Report all predefined paths, including losses and no trades; don't select the
winning constructed path. Each case produces12 checks: UNANIMOUS/AGREE2/CASH,
base/adverse costs and development/validation. Both trading rules reject opposing
nonzero votes. UNANIMOUS requires three agreeing votes; AGREE2 requires at least
two and no opposition. Missing support means cash. Member decisions remain the
original C00/C05/C06 research rules on preceding completed bars.

Each rule has one position and one account risk budget. The largest supporting
stop distance enters inherited floor sizing; member positions/risk/capital are
never added together. Each rule/cost/partition has fresh $10,000. Costs, trades,
member votes, reasons/supporters, fill lineage, admitted entry decisions and entry
risk estimates/budgets are in the full report. Abstention does not remove an
existing position's exit protection. Gap loss can exceed the entry risk estimate.

`Replay(fixture, manifest, scenario='base', partition='development',
rule='UNANIMOUS')` supports incremental `step`, `checkpoint`, matching `restore`,
`finish` and `report`. A checkpoint requires the same rule, members/source/config,
fixture/manifest, scenario and partition. Restoring across rules or from114 rejects.
Vote trace semantics and position/cost/entry/lineage state are checked. Latest exact
duplicate replay is idempotent; missing/conflicting/older events reject.

Manifests and outputs are created exclusively. Changing fixture bytes, source,
rule definitions, members or costs invalidates the old binding. Keep old artifacts
and use new paths after changes. Hashes check consistency; they are not authenticity,
UTC certification or broker reconciliation.

`inspect-capture PATH --format 107|109|111` remains diagnostic and returns
`performance_unavailable`. Native clocks/quote age/quality are not translated or
qualified. No MT5 script launch is involved. Market/paper/order/real-money
availability remains false, including when invented tests show profits.

Focused verification:

```bash
PYTHONPATH=src:tests python3 -m unittest test_strategy_combination_115 test_strategy_adapter_114 test_strategy_experiment_028 test_shadow_engine_113 test_tick_simulation test_simulation test_model test_forward_capture_111 test_private_recorder_107 test_execution_metrics -q
```

Read [results and limits](STRATEGY-COMBINATION-115-RESULTS.md) before interpreting
any outcome. No strategy or combination weights are selected from these fixtures.
