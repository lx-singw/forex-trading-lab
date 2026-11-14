# Elliott144 continuation — contexts, consensus and discovery

13 November 2026. The approved implementation continues. This increment implements
prospective context/count states and a persistent consensus policy, and exercises
a complete invented bar-to-count-to-signal-to-ledger path. Full strategy acceptance,
qualified market validation and native demo execution remain incomplete.

## Changes

- `interpretations.py` joins observed motive/corrective nodes into prospective
  EW3 and EW5 counts. It never uses a future fifth to justify wave-3 entry. Unknown
  parent position, unresolved subdivisions, exhausted search and opposing counts
  cannot manufacture a singleton context. Resolved corrections and still-valid
  active motive legs have distinct reported states.
- Contexts resolve D1, then H4 with D1 evidence, then H1 using both. A new D1
  publication reevaluates H4 context. Loss of supporting higher context cancels
  a pending unsubmitted signal, while held-position protection continues.
- Counts use the approved fixed Fibonacci slots, parent agreement, alternation
  and channel-conformity preferences. Guideline preference never erases a
  competitive structural disagreement. Equivalent count IDs are deduplicated.
- `setups.py` maintains one economic opportunity per side/source terminal across
  correction labels, pivot radii and setup aliases. Consensus uses the conservative
  trigger and stop, records membership revisions, preserves earliest expiry, and
  cannot reenter or reset expiry through relabelling.
- Invalidation during a context outage still consumes the original opportunity.
  Coverage breaks, missed pre-confirmation breakouts and expired old patterns
  cannot become fresh entries when warmup/context subsequently becomes available.
- Buffered protective stops are distinguished from raw structural invalidation.
  The raw boundary is checked again at the executable quote before entry.
- Fine-scale child evidence can support a coarse interpretation only when every
  coarse anchor independently confirms. Its later confirmation time remains a
  dependency; promotion cannot backdate a signal.
- Parser traversal follows existing child-node paths instead of enumerating large
  numbers of impossible partitions. Explicit search/candidate limits still block
  entry on exhaustion. This is not an exhaustive search over infinite degrees.
- Decimal arithmetic is locally fixed at precision50, independent of the caller's
  global Decimal settings. Immutable tree properties are cached; transactional
  processing copies mutable frontier state rather than deep-copying all previously
  published snapshots. Failed operations still roll back atomically.

## Verification

**84 tests passed together in175.822 seconds**, including an additional regression
for earliest-member consensus expiry:

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full test_elliott_full_policy test_elliott_full_discovery
```

The [saved full-suite log](../reports/elliott-full-144-policy-verification-003/tests.txt)
includes45 existing new-package tests,38 policy/count tests and one full-discovery
integration test. Earlier91 legacy124–126 checks remain historical results; those
unchanged modules were not rerun for this increment.
After the subsequent report-packaging-only refinement, the83 focused tests passed
again in0.509 seconds ([log](../reports/elliott-full-144-policy-verification-004/tests.txt)),
and the full-discovery CLI was repeated successfully. This is not a claim that the
complete84-test final invocation was rerun after the packaging change.

New checks include both entry types and directions; opposed/unresolved contexts;
unavailable counts; conservative coarse confirmation; duplicate membership; expiry
at bar10 versus11; late warmup; context loss; invalidation and breakout in one bar;
source gaps; frozen levels; changed membership on a breakout; structural checks
before fill; Decimal-context independence; and immutable saved policy/revisions.

### Public invented bar replay

[Replay](../reports/elliott-full-144-bar-discovery-005/replay.html),
[fixture](../reports/elliott-full-144-bar-discovery-005/fixture.json),
[structured results](../reports/elliott-full-144-bar-discovery-005/report.json) and
[complete compressed checkpoint](../reports/elliott-full-144-bar-discovery-005/checkpoint.json.gz).

The public input contains1,057 bar publications and two quotes. No supplied counts,
signals, positions or parent-context states enter this replay. The parser discovers
one EW3 signal, the ledger enters once, and the later gap closes it at an observed
price beyond the original stop. The integration test saves/restores the whole
engine with the signal pending, then checks identical entry/exit states. Independent
Fraction arithmetic reconciles the final trade cash and total balance.

The three timeframe histories are independently invented, including their warmup.
This does not certify aggregation from one underlying feed. It demonstrates one
constructed long EW3 discovery path, not complete automatic discovery acceptance
for all EW3/EW5 forms, shorts or market conditions. Public-input EW5 discovery still
needs an equivalent acceptance example; its component policy/fill paths are tested.

### Declared-count component examples

[All24 outcomes](../reports/elliott-full-144-policy-005/summary.csv),
[declaration](../reports/elliott-full-144-policy-005/declaration.json),
[EW3 target example](../reports/elliott-full-144-policy-005/EW3-long-target-base.html),
[EW5 gap example](../reports/elliott-full-144-policy-005/EW5-long-gap_stop-base.html)
and [skipped setup](../reports/elliott-full-144-policy-005/EW3-long-context_skip-base.html).

Two setups × two directions × target/gap/skip × two cost profiles produce24
deliberately constructed cases,16 closed invented trades and eight skips. Parent
contexts and resolved count nodes are supplied as explicit fixture assumptions in
these component examples. Their pages display that limitation. These are software
examples, not24 market trials, a win rate or strategy selection evidence. Their
declaration was saved before the outcomes; every gain, loss and skip is retained.

Reproduction requires `PYTHONPATH=src:tests` because the fixture templates are test
data. Run into new output directories; existing outputs are never overwritten:

```sh
PYTHONPATH=src:tests python3 scripts/elliott-full-policy-demo.py NEW_COMPONENT_OUTPUT
PYTHONPATH=src:tests python3 scripts/elliott-full-bar-demo.py NEW_DISCOVERY_OUTPUT
```

### Development findings

The first policy test fixtures had constant-price candles whose lows equalled the
structural boundary. Correct rejection exposed the inconsistent fixtures; they
were replaced with explicit interpolated source shapes. A deliberately wide EW5
fixture also correctly failed minimum volume; the component example prices were
rescaled before the fixed demonstration declaration, without changing risk caps.

The first full-discovery attempt was interrupted after excessive CPU use. Its
trace showed deep copying published history, in addition to repeated immutable
tree calculations. No completed report was produced for that attempt. Caching
immutable properties and copying only mutable frontier state fixed this runtime
problem; the final integration/restart/atomicity tests passed. This is not a formal
performance benchmark or a demonstrated production throughput guarantee.

Final review also caught an expiry nuance: consensus formation waits for the latest
member, but expiry must use the earliest member. The implementation and regression
now preserve that distinction, including when members first appear together.

The initial viewer embedded full checkpoints and repeated child trees, producing
a109,289,398-byte page. The final viewer contains only chart/cursor data and is
1,007,681 bytes. Complete replay state remains in a separate4,602,718-byte gzip
checkpoint. The primary report omits repeated child trees and references this
artifact using `EW_FULL_V1_REPORT_V2`. An added report test decompresses/restores a
checkpoint and verifies its ledger. Audit detail is retained rather than silently
dropped to reduce page size.

A Windows Node syntax attempt against a WSL UNC script failed during package
lookup with a connection reset. The actual compact viewer script subsequently
passed syntax checking from a local Windows path
([log](../reports/elliott-full-144-policy-verification-004/viewer-syntax.txt)). This
does not replace visual UI inspection, which remains pending.

## Remaining acceptance work

The original plan remains in progress. Next priorities are complete per-family
rule/location diagnostics and boundary coverage; automatic EW5/short discovery
examples; broader multi-scale ambiguity cases and pending-state fault sequences;
dataset-boundary liquidation and differential accounting against frozen controls;
viewer inspection; the separately typed qualified-data runner; and an actual
default-off native demo adapter with broker reconciliation/protection tests.

All16 market cells remain `UNAVAILABLE`, all orders remain unavailable, and no
terminal/account operation, reserved-price access, source acquisition or real-money
capability was added. Stops remain subject to gaps and slippage. This increment
establishes additional software behaviour, not a profitable market edge.
