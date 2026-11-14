# Elliott152 — automatic session fault acceptance

15 November 2026. Extends constructed-data acceptance from automatically discovered
EW3 long and EW5 short setups under both hypothetical cost profiles. The new tool
is an offline fixture/exercise/resume CLI. Trading/runtime, risk, cost, viewer,
existing generators and frozen-control sources are unchanged.

## Fixed scope before returns

The matrix declares two fixed setup/direction examples, two cost profiles and ten
fault branches before executing an account. Each example starts from the existing
149 hourly price template. Its first72 contiguous hours are explicitly resegmented
into12-,12-,23- and25-hour sessions, with the12-hour sessions marked partial.
Hourly prices, observation times and subsequent session/closure boundaries are
preserved; lineage is recomputed against the new case/calendar declaration.

Those72 hours now produce four D1 bars and19 H4 bars from72 H1 bars. The remaining
schedule resumes its original edges. This exercises variable-session aggregation
in the warmup history, not variable boundaries inside the later wave formation.
No provider timezone, DST rule, actual calendar or qualified tick coverage is
inferred. Partial H1 bars and every possible session combination are not covered.
The original UTC-only controls reject this calendar; their rules are not adapted.

Each automatic setup prefix is built through146 observations,147 causal interpretation
and148 paper execution. Counts, parent directions and pending setups are not
injected or patched. Prefix records bind the complete input, calendar, published
snapshot history, observed frame counts, coverage, automatic signal and parents.

The ten branches fork the same pre-entry state, each with independent synthetic
USD10,000 capital. This isolates operational behaviour; these are not additional
funded chronological study cells or repeated opportunities to recover a loss.
Closure and missing-bar stresses deliberately extend beyond the original example's
funded endpoint without importing later market prices. They use fixed invented
quotes and the already declared synthetic calendar.

| Branch | Behaviour exercised |
| --- | --- |
| Baseline | Original automatic entry and fixed target/gap exit |
| Wide retry | Wide entry rejected; later fresh narrow quote can enter |
| Stale retry | Stale source quote unavailable; fresh quote can enter |
| Raw closed retry | Raw closed flag blocks entry within an open calendar session |
| Repeated source retry | Repeated source cannot fill; genuinely new source can enter |
| Expired | Unavailable entry followed by expiry; later quote cannot revive signal |
| Missing bars gap | Held protection still operates after scheduled bars become missing |
| Closure gap | Calendar rejects raw-open quote and boundary finish; reopening gap closes held position |
| Duplicate conflict | Duplicate after clock advance is idempotent; conflicting retry rejects atomically |
| Invalid batch | Rejected duplicate-frame publication preserves automatic pending state |

Future fault events must leave the published snapshot history unchanged. Expired
branches stay flat; other branches have a single entry and exit. Gap losses are
checked against estimated entry risk and the loss-pause state. Stops and pauses
are not guaranteed loss caps.

## Verification

**144 targeted tests passed together, zero failures/errors, in676.025seconds.**
This is11 new152 checks and133 relevant existing148 component/journal,146 session,
145 preflight, boundary, accounting and151/original-viewer checks. The full prior
trading suites are not rerun or added to this invocation. Recorded source hashes
stay unchanged throughout the run.

All four automatic prefixes form the expected setup and direction with aligned
D1/H4 contexts and complete scheduled coverage beyond253 bars in every frame.
Each runs through all ten predeclared branches:40 independent account branches
remain, including36 filled accounts and four expired, flat accounts. No recovery
entry, counterfactual source-price selection or aggregate performance portfolio is
introduced. The future fault trajectories leave published snapshot histories
unchanged.

Independent Fraction arithmetic reconciles all36 filled accounts: executable
bid/ask and adverse spread floor, directional slippage, protective tick rounding,
2R target rounding, volume flooring, risk/margin/cap constraints, entry timing,
commission, exit, financing, net and final cash. Financing is reconstructed from
entry/exit UTC receipt days and weekday multiples, including non-executable closed
quotes. The four expiry cases retain synthetic USD10,000 without entries. The
eight missing-bar/closure gap witnesses lose more than estimated entry risk and
latch the loss pause; those observations do not guarantee maximum losses.

Two fault-boundary checkpoints are restored in separate Python processes through
the public CLI: EW5 short/adverse pending after a rejected wide quote, and EW3
long/base held after a calendar-closed quote and rejected boundary finish. The
held checkpoint retains the original stop and target. Both final whole-state
digests and ledgers match uninterrupted execution. These are local journal
restoration checks, not broker acknowledgements or position reconciliation.

The trading source graph, including all46 frozen-control bindings, matches150
exactly. No previous generator, risk rule, cost profile or execution algorithm is
modified. Original UTC-only controls remain unsupported on the variable calendar;
this sprint does not rerun the16-cell common-comparison matrix or claim new
chronological market results.

The [portable verification record](evidence/elliott-session-faults-152/README.md)
contains the test log, source hashes, global pre-return declaration, automatic
prefixes,40-branch summary,36 accounting audits and two restart summaries. Full
anonymous invented inputs, branch ledgers, checkpoints, continuations, restored
outputs and source archive remain under ignored
`reports/elliott-session-faults-152-verification-001/`. The archived runner is
`reports/elliott-session-faults-152-run.py`; the recorded invocation identifies all
selected tests. Large generated files remain outside Git.

## Reproduction

```sh
PYTHONPATH=src:tests python3 scripts/elliott-session-faults-152.py fixture NEW-INPUT.json --case ew5_short
PYTHONPATH=src:tests python3 scripts/elliott-session-faults-152.py exercise NEW-OUTPUT --case ew5_short --profile adverse
PYTHONPATH=src:tests python3 scripts/elliott-session-faults-152.py resume NEW-OUTPUT/wide_retry.json.gz NEW-OUTPUT/wide_retry.json.continuation.json NEW-RESTORED.json
PYTHONPATH=src:tests python3 -m unittest test_elliott_session_faults_152 -v
```

Output paths must be new. There is no market-source selector, order event, account
connection or live option. The matrix uses at most two isolated exercise processes
when CPU/memory permit; each chronological replay remains sequential.

## Remaining scope

This is deterministic constructed-price software evidence. There is no market
win rate, edge estimate, income result or broker reconciliation claim. Invented
funded and fault outcomes are not selected as a performance portfolio. The full
144 plan remains incomplete: broader nested-pattern/direction/session/fault
combinations, qualified source/use/prior-trial/clock/DST/coverage/cost/contract/
margin/conversion admission, the qualified chronological runner and disabled
native demo reconciliation remain unfinished. Visual browser review and the
remaining provisional/nested viewer work from151 are also outstanding.
The152 fault-summary format is not imported by151's saved149-account viewer.

Financing uses the inherited hypothetical UTC receipt-day rules, including the
conservative boundary pause; this does not qualify provider rollover costs.
Sparse invented quotes cannot establish true intrabar drawdown or complete tick
paths. No actual market data, acquisition dates, account, terminal or credentials
are assigned/accessed. Protected periods, closed routes and expired capture
restrictions remain unchanged. All16 actual market cells retain unavailable/null
results and native submissions remain unavailable. Real-money execution remains
unavailable.
