# Elliott expansion144 — implementation status

13 November 2026. **In progress; the full approved plan is not complete.**

Latest,15 November: [relay157 and independent checker](RECORDER-RELAY-157-RESULTS.md).
205 targeted recorder checks pass. Default-off measured orchestration and native
diagnostic/receipt reconciliation are implemented; ten invented jobs retain three
consistent completions and seven independent rejections. No native helper, MT5,
account or actual price is accessed.156's grant stays false. A bounded helper-only
trial with invented files, native IO/runtime proof,138/140 commit integration and
source/date/run admission remain open. All16 market cells remain unavailable/null;
this does not complete stage E/F or change the trading rules.

Latest,15 November: [native recorder156](NATIVE-RECORDER-156-RESULTS.md).
A distinct raw context/quote/clock binding compiles in isolated MetaEditor staging;
170 targeted recorder checks pass. Default-off input and an immutable unassigned
run grant prevent account/price access. No deployment, native runtime or market
qualification is claimed. The measured-clock owner/relay runner, independent
native-journal checks, lifecycle commit integration and source/date/run admission
remain open.136 stays expired; protected dates/routes and orders-off remain.

Other continuations since145, with separate component evidence:

- [149 session comparison](ELLIOTT-SESSION-COMPARISON-149-RESULTS.md) and
  [150 entry acceptance](ELLIOTT-SESSION-ACCEPTANCE-150-RESULTS.md): calendar-aware
  common invented inputs, automatic EW3/EW5 long/short entries and account checks.
- [151 saved replay viewer](ELLIOTT-SESSION-VIEWER-151-RESULTS.md): as-known-then
  projection and saved-account export; browser visual review remains outstanding.
- [152 session faults](ELLIOTT-SESSION-FAULTS-152-RESULTS.md) and
  [153 nested patterns](ELLIOTT-PATTERN-MATRIX-153-RESULTS.md): broader invented
  execution faults and candle-derived catalogue/extension examples. Broader
  acceptance is still incomplete.
- [154 source readiness](ELLIOTT-MT5-SOURCE-154-READINESS.md) and
  [155 payload boundary](RECORDER-BOUNDARY-155-RESULTS.md): distinguish the user's
  expired recorder from an export and bind invented payloads to supervision.

These test counts are separate revisions/suites, not additive strategy evidence.
All16 actual-market cells remain unavailable/null. Qualified historical admission
and runner, remaining viewer/acceptance work and native reconciliation remain open.

Latest, 14 November: [study145 metadata preflight](ELLIOTT-STUDY-145-RESULTS.md).
28 new tests pass without changing the172-test strategy runtime. The current
source/run draft assigns no data or dates and all16 market cells remain unavailable;
hashed declarations cannot self-qualify prices, costs or untouched validation.

Latest, 14 November: [shared entry and restart acceptance](ELLIOTT-EXPANSION-144-ENTRY-RESULTS.md).
172 tests pass together. Four shared-H1 EW3/EW5 long/short cases retain all64 invented
cells; eight primary entries pass target/gap accounting and pending/held restart.
The documented parent-context lifecycle correction changes prototype decisions;
earlier evidence retains its source revision. Qualified market/native admission
and broader acceptance remain unfinished; orders remain unavailable.

Latest, 14 November: [common invented hourly observations](ELLIOTT-EXPANSION-144-SHARED-RESULTS.md).
159 tests pass together; all16 invented cells run, with expected Elliott abstention.
The fuller Elliott strategy and its frozen controls now have a common H1-derived
observation path. Missing history is unavailable rather than a zero return.
This is invented-bar integration; positive shared Elliott-entry acceptance and
qualified market/native admission remain unfinished.

Latest, 14 November: [unchanged strategy control adapters](ELLIOTT-EXPANSION-144-CONTROLS-RESULTS.md).
143 tests pass together on the final runtime revision.
EWPB_D124, T12_D and CASH now expose common invented replay/report/checkpoint
interfaces while preserving their original engines. Four declared artificial
demonstrations retain all48 control accounts. The new-strategy common-input
adapter and qualified market/native admission remain unavailable.

Latest, 14 November: [longer histories and accounting comparisons](ELLIOTT-EXPANSION-144-WINDOW-RESULTS.md).
130 tests pass together. Rolling pivot scope preserves held and consumed state;
48 sizing cases and 24 accounting traces match within the declared component
domain. Four financing timing differences are retained explicitly. Full strategy
control parity and qualified market/native admission remain unavailable.

Latest,14 November: [rulebook, four discovery directions, boundaries and viewer](ELLIOTT-EXPANSION-144-RULES-RESULTS.md).
120 tests pass together on the final revision; the viewer has now been inspected
through signal, entry/protection and gap exit. Market/native admission remains off.

Latest continuation: [contexts, consensus and discovery results](ELLIOTT-EXPANSION-144-CONTEXT-RESULTS.md).
84 tests now pass together, including a public invented-bar discovery and
signal-pending restart test. The sections below retain the initial build's45-test
handoff and earlier artifacts; use the continuation for current coverage and gaps.

The user approved [the plan](ELLIOTT-EXPANSION-144-PLAN.md) with “proceed thoroughly”.
The new implementation lives in `src/forex_demo_lab/elliott_full/`, with the
declaration `config/elliott-full-v1.json` and `tests/test_elliott_full.py`.
Existing 117–126 strategy definitions and evidence were not edited.

## Implemented research prototype

- Strict invented EURUSD bar/quote schemas; malformed/nonfinite input and actual
  market wrappers reject. D1/H4/H1 publication order and input lineage are checked.
- A separately callable sampled-midpoint aggregator checks finalization, edge
  coverage, chronology and gaps. Supplied fixture bars remain invented declarations,
  not authenticated aggregation from a market source.
- Strict delayed radius-2/4/8 high/low pivots, immutable confirmation records,
  separate occurrence/confirmation times and current alternating views.
- Bounded recursive pattern enumeration, with geometry for ordinary/truncated
  impulses, zigzags, flat variants, diagonal profiles and triangle variants.
  Corrective combinations are composed from parsed child patterns. Insufficient
  subdivisions and exhausted search are explicit. Nested parse tests demonstrate
  resolved children rather than only matching a three-swing picture.
- Deterministic Fibonacci display ordering and a conservative completed-correction
  context path. EW3/EW5 setup construction exists but is not yet accepted as a full
  implementation of the approved count/consensus policy.
- A separate cost-aware invented ledger: bid/ask execution, adverse profile,
  cost-aware structural-stop sizing, lot flooring, margin/headroom, one position,
  consumed setup IDs, fixed targets, gap/slippage losses, financing, time exits,
  daily pause and no same-quote reentry. Wide-entry filters do not block exits.
- Atomic rejection and replay-verified, source/config-bound ledger and whole-engine checkpoints.
  Rehashing a forged saved balance does not make it valid. Checkpoints contain
  independent copies rather than references to mutable live input/events. Whole-engine
  checkpoints also bind count snapshots, active setups, emitted IDs and pending signals.
- An exclusive-output CLI and a local HTML time-cursor viewer. Future bars are
  hidden at the chosen cursor; preferred/alternate pattern overlays, the current
  count tree and no-trade reason are shown. Stop/target overlays use only entry
  events available by the cursor. A CSV trade ledger is exported.
- Explicit unavailable status for all 16 planned market-study cells. No zero or
  invented return substitutes for missing market evidence.
- A fail-closed inactive demo boundary tests enum rejection and ambiguous-outcome
  retention. It has **no native account query, broker transport or submission API**;
  these tests cannot establish actual connected-account safety.

## Verification and artifacts

45 focused tests pass in the retained final log. They exercise hard geometry,
nested parsing, delayed confirmation, future suffix invariance, search exhaustion,
coverage gaps, independent Fraction sizing, minimum volume, both trade directions,
stop gaps beyond estimated risk, widened exits, stale quotes, financing, daily
pause persistence, duplicate/conflicting signals, restart prefixes, rehashed
checkpoint forgeries, atomic failed exits and unavailable market/demo admission.
The earlier combined run also passed128 tests in477.146 seconds:37 tests from the
initial new suite and91 retained124–126 checks. The final45-test focused suite was
run after subsequent new-package changes; the unchanged legacy modules were not
rerun again. This accounts for136 distinct passing tests across the runs, not one
complete136-test final invocation.

The initial run found two fixture-type errors (floats supplied to a deliberately
decimal-string interface) and one implementation error: checkpoint payloads shared
mutable input/event lists. The fixture literals were corrected and checkpoint
payloads are now deep-copied. The atomic-rejection regression passes.

Artifacts:
- [Focused test log](../reports/elliott-full-144-demo-001/tests-final.txt).
- [Invented observational replay](../reports/elliott-full-144-demo-004/replay.html).
- [Structured output](../reports/elliott-full-144-demo-004/report.json).
- [Invented fixture](../reports/elliott-full-144-demo-004/fixture.json).
- [CSV trade schema](../reports/elliott-full-144-demo-004/trades.csv) (no demonstration trades).

The demonstration contains 165 bar publications across three timeframes. It is
deliberately below warmup, with no quotes/trades/P&L study. It exercises chart/count
observation and abstention; it is not a successful end-to-end trading example.
No qualified native or historical input was accessed.

From WSL:

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full
PYTHONPATH=src python3 scripts/elliott-full-demo.py reports/elliott-full-144-demo-NEW
PYTHONPATH=src python3 -m forex_demo_lab.elliott_full FIXTURE.json NEW_OUTPUT_DIRECTORY
```

## Outstanding work before software acceptance

The new prototype must not yet be presented as the complete EW_FULL_V1 strategy.
Remaining code and acceptance work includes:

1. Complete the executable rulebook, parent-location diagnostics, triangle/diagonal
   boundary cases and positive/negative tests for every catalogue profile. Current
   geometric matches do not certify every source rule or resolve every child.
2. Complete the approved active-motive higher-timeframe context states, alternation
   and channel ranking, cross-scale competitive-set treatment and count revisions.
   Current context deliberately supports fewer states than the approved plan.
3. Finish consensus reformation/cancellation, persistent anchor aliases, and
   independently reviewed integrated EW3/EW5 trade/loss/skipped examples. In
   particular the setup code is not yet certified against every alternate-count
   disagreement and parent-location case. Some matches can abstain unnecessarily.
4. Broaden integrated checkpoint tests to active consensuses and pending signals,
   add dataset-boundary liquidation and independent accounting differential checks
   against retained120/125 cases. Whole-engine prefix reconstruction is implemented,
   but not yet accepted on all required trading-state transitions.
5. Visually inspect the viewer and exercise overlays against integrated trade
   examples. Pattern labels, preferred/alternate lines, protection overlays and
   CSV export are implemented; fill markers and UI acceptance remain.
6. Implement and verify a separately typed qualified-data runner and unchanged
   control adapters before any market-performance calculation. Current source
   eligibility is unavailable; older data partitions and expired routes stay fixed.
7. Build a real default-off native demo adapter and test native enum checks,
   reconciliation, partial fills, protection failures and restart boundaries.
   The current inert boundary is not that adapter.

These are implementation tasks still authorized by the user's approval, not
requests for another approval. Historical/shadow results additionally require
qualified data and bounded runs as specified in the plan. No market win rate,
profitable edge, demo readiness or real-money capability has been established.
