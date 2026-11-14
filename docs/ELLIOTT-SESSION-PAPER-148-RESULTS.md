# Elliott148 — calendar-aware paper execution

14 November 2026. Connects the invented147 decision replay to the existing
hypothetical ledger. No provider, account, terminal, quote feed, source permission
or market study is admitted. No native order interface or enabling toggle exists.

## Implemented behavior

`elliott_session_paper_148.py` journals bar batches, receipt-clock changes, quotes
and explicit finish events. One raw event commits its decision state, pending
signal, paper ledger and audit together, or none of them. Same-receipt bar batches
retain the147 ordering/backfill rules and allow one publication per timeframe.

Before a pending signal can reach the ledger, the replay refreshes context and
checks elapsed expiry, the receipt session, complete scheduled coverage and both
parent directions. A new H1 decision supersedes the prior pending action. Missing
coverage, lost parent direction, expiry or session closure cancels it. The emitted
strategy opportunity remains consumed; a later quote cannot revive that action.

The existing latency and spread rules remain in the ledger. A timing, wide-spread,
stale, repeated-source or explicitly closed quote can leave a still-valid pending
signal waiting for a later executable observation. Successful entry and terminal
entry rejections clear it. Repeated raw quotes cannot reapply an order decision,
including after an intervening clock event. Conflicting duplicates reject.
Equivalent most-recent bar publications also remain idempotent across intervening
clock/quote events, including an H1-only retry of a previously accepted batch.
The per-timeframe retry cache is included in checkpoint state and reconstruction.

Both source time and receipt time must lie in declared open sessions before a
quote is executable. The raw quote and its supplied session flag remain recorded.
Closed/calendar-inconsistent observations are retained with an explicit gate audit
and passed to the ledger as unavailable; they cannot create entries or exits.
This is an invented-input rule, not authentication of a provider's session facts.

Missing bars block new entries but do not suppress existing position protection
on executable quotes. Gap stops, target limits, elapsed72-hour exits, position
limits, minimum-volume rejection, margin/risk sizing and loss pauses use the
unchanged ledger. A position can survive an unavailable closed-session quote and
exit at the first executable reopening quote, including a loss beyond estimated
stop risk. A protective stop is not a guaranteed maximum loss.

The ledger's existing UTC receipt-day financing, weekday multipliers, anchor
handling and conservative pause after a missing midnight boundary are preserved.
An explicit closure does not relax that pause or certify broker rollover costs.
Calendar-aware broker financing and the old financing-clock differences remain
unresolved; these costs are hypothetical.

Finish requires the exact latest raw quote at the current clock and the ledger's
latest executable observation, even when flat. Stale, repeated, closed or altered
marks reject. There is no earlier-price fallback or borrowed future mark. Exact
finish repetition is idempotent; other post-finish events reject.

Checkpoints bind calendar, profile,148/147/146/strategy/control source identities,
the complete raw prefix and the whole decision/ledger/pending/audit state.
Restore reconstructs that prefix and compares state. Source, calendar, profile,
state and journal changes reject. Journal limits apply before mutation; returned
checkpoint data cannot mutate running bindings or history. Hashes establish local
consistency and do not qualify market facts or an external order outcome.

## Verification

**156 tests passed together, with zero failures or errors, in476.955 seconds.**
The invocation covers39 new148 tests and117 relevant existing checks (41 policy,
14 boundary,3 cross-accounting,31 session146 and28 study145). Source hashes stayed
unchanged throughout the recorded run.

The prior258-test source graph and all files in its retained snapshot are checked
byte for byte against that revision. The new module, CLI and tests are outside the
existing strategy package and do not change its bindings. The full258-test matrix
is not rerun; the156 count describes this targeted invocation. All46 frozen-control
bindings remain unchanged.

Small, explicitly labelled component tests supply declared setups/parent context
to isolate quote gates and ledger safety. They are separate from automatic
discovery. Cases cover exact latency/expiry boundaries, unavailable quotes,
coverage/context/closure cancellation, duplicates, atomic errors, both-direction
gap exits, time exits, financing, position limits, minimum volume and daily pauses.

The automatic cases supply common invented H1 prices through146 aggregation and
147 discovery, with complete253-bar warmup and declared closures. No count, parent
direction or signal is injected. EW3 long target and gap outcomes exercise both
cost profiles. Independent rational arithmetic checks entry, stop, target, lot
floor, risk, commission, exit, net and final cash. One adverse pending restart and
one base held restart must reconstruct the complete prefix and agree with the
continuous final state. Future exit prices must leave earlier snapshots unchanged.
Automatic EW5 and short-side session-paper acceptance remain wider coverage work.

Review found that retrying an accepted H1 publication after a clock event could
cancel its pending action. The correction records the latest accepted publication
per timeframe and makes equivalent retries inert. Conflicting retries still
reject without changing state. The original154-test run/source remain archived
under verification001; verification002 is the current156-test release evidence.
This correction changes retry handling, not wave, sizing, cost or exit rules.

All four automatic paper accounts reconcile exactly. Both full-prefix restarts
match the continuous state, including the ledger, pending action, decision history
and gate/cancellation audit. The public CLI gap case finishes after one stop exit
with the loss pause set; its pending and held checkpoints are retained.

The public CLI accepts an exclusive output directory and fixed invented outcome
and cost-profile choices. It accepts no source, input price file, account, native
session or live-mode option. Its embedded common-H1 example emits a report plus
pending/held checkpoints. The target/gap choice is declared software coverage,
not selection of a profitable market strategy or a performance estimate.

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_session_paper_148 test_elliott_full_policy test_elliott_full_boundary test_elliott_full_crosscheck test_elliott_sessions_146 test_elliott_study_145 -v
PYTHONPATH=src:tests python3 scripts/elliott-session-paper-148.py NEW-OUTPUT-DIRECTORY --profile base --outcome gap
```

The [portable verification record](evidence/elliott-session-paper-148/README.md)
contains the full log, completion and automatic-account/restart/CLI summaries.
Full artifacts remain under ignored local reports:

- [Verification and source snapshot](../reports/elliott-session-paper-148-verification-002/verification-summary.json)
- [Automatic account evidence](../reports/elliott-session-paper-148-verification-002/automatic-accounts.json)
- [Adverse pending restart](../reports/elliott-session-paper-148-verification-002/pending-adverse-result.json)
- [Base held restart](../reports/elliott-session-paper-148-verification-002/held-base-result.json)
- [Public CLI report](../reports/elliott-session-paper-148-verification-002/public-cli/report.json)

The generated-artifact inventory identifies19 files totaling291,260,794 bytes.
It excludes itself and its referencing verification summary. The ZIP and tested
source bytes were verified against the recorded source snapshot. Large reports,
checkpoints and runtime artifacts remain outside Git.

## Remaining scope

This is a single-strategy invented paper adapter, not the qualified chronological
study or four-candidate comparison runner. The three controls retain their frozen
UTC daily interface. Unsupported session schedules must remain unavailable in
that comparison path. Actual source/use/clock/coverage/cost/prior-trial evidence,
qualified partitions and run admission remain unresolved.

Native demo reconciliation, actual account-type checks immediately before any
future submission, ambiguous acknowledgements, partial fills and broker restart
reconciliation remain separate disabled work. No actual market prices, accounts,
terminals, credentials or reserved dates were accessed. No source or acquisition
window is assigned. All16 market cells and order submissions remain unavailable.
