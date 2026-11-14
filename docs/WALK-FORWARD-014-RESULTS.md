# Chronological runner 014 — 2026-10-02

The frozen 009 evaluation workflow is implemented. It runs C00–C04 under the
unchanged base/adverse risk and cost assumptions, saves each training-only
choice before test replay, and publishes all 40 controls. Every window starts
with $10,000 and no position. All candidates share 201 observed closed warmup
bars; positions carry across quarters and years inside a training window.
Annual and quarterly changes use marked equity at the last observed quote;
the final position closes at the last quote with the modeled exit costs.

**225 tests passed**. Sixteen new tests cover failed annual reviews, changed
evidence/data/ledger, synthetic/market separation, missing and reserved years,
future quotes, warmup, preserved same-ms events, year-end open equity/charges,
training-only choice ordering, choice tampering, independent accounting and
refusal to overwrite or resume a partial run. Existing risk, gap, stop, account
guard and restart tests remain passing. The batch itself deliberately refuses
partial-run resume; per-simulator checkpoint support is unchanged.

An end-to-end run used 3,456 invented ticks across four sparse annual fixtures.
The source archive, inputs, modeled costs and exact warmup bounds were frozen
before returns. All 40 scenarios completed; both choices were **CASH**. The
independent checker recalculated trade P&L, fees, period equity and report/choice
bindings, including **178 quarter-end marks with open positions**. These numbers
describe software verification, not observed forex trading performance or an
estimate of future income. Cash's zero return fails the positive-edge screen.

Current market review `correction-013-checks.json` was explicitly rejected
before performance because it does not approve all four annual datasets.
`walk-forward-014-market-gate.json` preserves that rejection. No market-data
approval, normalization or new historical profit result was created. Annual
clock approval, July 14 and other coverage defects remain unresolved, and
historical broker costs remain unverified. Modeled costs are the frozen 008
scenarios, not claimed actual historical charges. No order functionality,
broker calls, downloads, deployment or terminal changes were added.

## Artifacts and commands

Implementation: `src/forex_demo_lab/walk_forward.py`.
CLI: `scripts/walk-forward-014.py`.
Independent arithmetic: `scripts/check-walk-forward-014.py`.
Tests: `tests/test_walk_forward.py`.
Protocol: `WALK-FORWARD-014-PLAN.md`; keep it and the frozen source unchanged.

The completed synthetic artifacts are under `reports/walk-forward-014-synthetic`
(ledger, seal, source ZIP and run reports). Original invented inputs are under
`data/walk-forward-014-synthetic`. Separate checks are
`reports/walk-forward-014-independent-checks.json` and
`reports/walk-forward-014-checks.json`. Use new destinations for another run;
existing files and partial runs are never overwritten or silently resumed.

Verify the completed synthetic run from WSL:

```bash
PYTHONPATH=src python3 scripts/walk-forward-014.py verify reports/walk-forward-014-synthetic
python3 scripts/check-walk-forward-014.py reports/walk-forward-014-synthetic
```

For another invented software exercise, choose fresh directories and run the
following commands sequentially:

```bash
PYTHONPATH=src python3 scripts/walk-forward-014.py synthetic-fixture data/new-synthetic-fixture
PYTHONPATH=src python3 scripts/walk-forward-014.py freeze data/new-synthetic-fixture/bundle.json reports/new-synthetic-run
PYTHONPATH=src python3 scripts/walk-forward-014.py run reports/new-synthetic-run
python3 scripts/check-walk-forward-014.py reports/new-synthetic-run
```

## Future market input contract

A bundle JSON has `kind: chronological_ticks_input`, `synthetic: false`,
`review: path/to/review.json`, and `years` with exactly keys 2020–2023. Each year
contains `data` and `provenance` paths, relative to the bundle or absolute Linux
paths. Tick gzip CSV has the exact header `sequence,time_msc,bid,ask`; each
annual sequence starts at zero, preserves every event, and contains UTC
milliseconds within that calendar year. All twelve months must be present.
Provenance and the year-specific review bind the exact tick bytes and count.

The review schema and required evidence are in `WALK-FORWARD-014-PLAN.md`.
A global flag cannot rescue a blocked year. Evidence hashing verifies identity;
the reviewer must separately establish clock, source lineage, corroboration
and the absence of unresolved open-session gaps. This runner does not generate
approvals or reinterpret the earlier failures. Earlier development datasets
and correction diagnostics are not eligible substitutes for this annual input.

Next: implement separately declared normalization with exact replay lineage,
coverage inventories and month seams, then resolve the remaining clock and
missing-session evidence before issuing any annual approval. Market replay
remains gated. Keep 2025 excluded from tuning and November–December 2026 reserved.
These historical studies remain retrospective; neither a passing screen nor
software tests authorize execution or establish reliable profitability.
