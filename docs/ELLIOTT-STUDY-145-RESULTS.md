# Elliott145 — prospective study metadata preflight

14 November 2026. This sprint implements the metadata preflight from section 11
of the [approved Elliott plan](ELLIOTT-EXPANSION-144-PLAN.md). It does not implement
the qualified-price runner or admit a market study. No source, capture date,
account, price file or new provider route is assigned or accessed.

## Implemented

`elliott_study_145.py` and its CLI create, freeze and check a separately typed
prospective plan. The schema has anonymous source aliases, source-route category,
development/validation date proposals and warmup declarations, a prior-exposure
ledger, evidence-reference hashes/scopes, fixed117 cost-profile identity and the
initial per-track trial budget. Price arrays, returns, account identifiers,
credentials, arbitrary evidence paths and policy overrides are rejected fields.

The module is outside `elliott_full/`. Its freeze binds its own implementation,
CLI/tests and the unchanged strategy/control source graph. It does not modify the
172-test strategy revision or invalidate its checkpoints. Ignored local price and
runtime artifacts are not discovered or read by this preflight.

The checker enforces these declared-plan constraints:

- Two chronological, disjoint funded partitions, each at least24 calendar months.
  Calendar-month arithmetic handles leap days;730 elapsed days is not a substitute.
- Contiguous prior warmup coverage and at least253 declared complete bars in each
  required timeframe. A declared count is not proof of qualified complete sessions.
- Immutable date policy:2024 already-seen development prices cannot serve as
  untouched funded validation;2025 remains consumed/excluded; October2026 remains
  quarantined; November–December2026 remains reserved/untouched. Warmup access to
  consumed, quarantined or reserved dates is also blocked. Seen prior prices can
  warm an otherwise admissible validation interval; they are not validation returns.
- Recorded prior prices, returns, rule adjustments or friend examples that overlap
  validation mark it exposed. A matching declaration of a joint, pre-return freeze
  for the other track requires independent review; it does not grant qualification.
  Same-track reuse, mismatched joint declarations and rule adjustment remain blocked.
- Fixed four-candidate ×two-cost ×two-partition scope:16 cells per track. Declared
  prior cells count against the initial16-cell budget for that track. These supplied
  counters are not independently certified or an authoritative global trial ledger.
- Unknown costs remain unknown. Hypothetical117 costs cannot pass the qualified
  broker-performance track. Sensitivity always retains its separate label and
  cannot satisfy a historical broker-performance or demo gate. Contradictory terms
  require a new declared profile rather than silently changing the existing one.
- Evidence-reference intervals must cover the proposed funded and warmup scopes,
  without filling gaps, and declare all required timeframes. A SHA256 identifies
  a declaration; it does not authenticate a provider fact or show independent review.

Both closed090 and attach-only SDK routes remain blocked under their recorded
project constraints. A proposed native-capture route also reports no assigned
bounded plan. This neither renews136 nor makes a legal finding about feed use.
The source-use and clock findings remain dated unresolved project evidence, not
fresh verification of an actual provider's terms or clock.

## Result and limits

The generated current draft assigns no source or dates. Its report retains all16
cells as `UNAVAILABLE`, with null returns and scoped requirement codes. The code
also keeps a fully populated plan unavailable: every evidence declaration still
requires independent qualification, full strategy acceptance is incomplete and a
qualified-data runner is absent. There is no data-access or order-enabling branch.

The freeze is explicitly `frozen_metadata_plan_not_admission`. It binds exact plan
bytes, canonical content, immutable policy and source hashes before assessment.
Changes to a source, policy, flag or plan reject; source changes during assessment
reject before an output directory is created. Outputs are created exclusively.
Duplicate JSON keys, nonfinite values, oversized files and symlink inputs reject.

Evidence hashes are not opened as file paths. Only the explicit plan/manifest and
known repository source files are read. Thus this step can identify missing or
contradictory declarations without examining reserved prices or computing returns.
It cannot establish source permission, clock correctness, executable coverage,
actual costs, genuine unseen history or true completeness from self-declarations.

The separate eight evidence requirements are source use, prior trials,
clock/timezone/DST, session calendar, coverage/lineage, quote availability,
commission/swap and contract/margin/conversion. The smallest external next step is
to identify a candidate source and the applicable evidence for these requirements.
No such evidence has been newly obtained, and the friend remains optional.

## Verification and reproduction

**28 tests passed in the recorded run, with zero failures or errors.** The earlier
172 strategy checks were not rerun: the runtime and all46 frozen-control bindings
match the previously tested source exactly. This is not a new combined200-test
invocation.

The [portable verification record](evidence/elliott-study-145/README.md) includes
the test log, completion, unassigned draft and current requirement report. Full
metadata freezes and the source snapshot stay under ignored local `reports/`:

- [Current draft](../reports/elliott-study-145-preflight-001/plan.json)
- [Frozen metadata](../reports/elliott-study-145-preflight-001/freeze.json)
- [All16 unavailable cells](../reports/elliott-study-145-preflight-001/out/preflight.json)
- [Missing evidence table](../reports/elliott-study-145-preflight-001/out/requirements.md)

The verification log and a generated unassigned plan/preflight are retained with
this sprint. Tests cover both tracks, all16 unavailable cells, complete unverified
claims, calendar months, date boundaries, funded/warmup distinctions, prior
exposures/joint freezes, costs/budgets, closed routes, scope gaps, strict schema,
freeze tampering, mid-run source changes, exclusive output, no evidence-path reads
and the public CLI. The existing strategy admission remains unavailable.

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_study_145 -v
PYTHONPATH=src python3 scripts/elliott-study-145.py draft NEW-PLAN.json
PYTHONPATH=src python3 scripts/elliott-study-145.py freeze NEW-PLAN.json NEW-FREEZE.json
PYTHONPATH=src python3 scripts/elliott-study-145.py preflight NEW-PLAN.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
```

Plan dates are proposals being checked, not source assignments or acquisition
grants. Frozen metadata drafts do not themselves run or certify comparison cells.
Any actual study still needs the independent source/run qualification and prior
trial-budget review before its pre-return freeze and untouched validation.

Remaining authorized work includes the qualified-data/unchanged-control runner,
session-aware aggregation and count coverage, wider pattern/fault acceptance and
disabled native demo transport/reconciliation. The original financing-clock
differences remain. The full approved plan is incomplete; no market advantage,
win rate, income, native readiness or real-money capability is established.
