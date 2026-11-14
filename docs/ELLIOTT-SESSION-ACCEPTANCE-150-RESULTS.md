# Elliott150 — automatic EW3/EW5 session acceptance

14 November 2026. Extends the149 invented fixture generator and verifies the
existing session-aware comparison pipeline with both setup families/directions.
The trading runtime, risk rules, costs and frozen controls are unchanged.

## Declared cases and source scope

Four fixed cases are declared with source/generator hashes before any paper
returns: EW3 long target, EW3 short gap, EW5 long gap and EW5 short target. Each
uses the complete four-candidate, two-cost, two-partition comparison:64 paper cells
in total. Eight development EW_FULL accounts are primary entry witnesses. Cases
cover targets and gap losses across both families/directions; they do not cover
every setup/direction/outcome combination or imply general pattern acceptance.

The public149 fixture command adds `--setup EW3|EW5`, `--side -1|1` and
`--outcome target|gap`. These select predetermined constructed prices, not strategy
or risk overrides. The price template supplies no counts, parent direction,
preferred label or entry signal to the replay. Counts and signals arise through
146 aggregation,147 interpretation,148 paper execution and149 common comparison.

All examples include253-bar warmup requirements and explicit UTC sessions with
declared closures. H1/H4/D1 observations share the same underlying invented hourly
history. The first funded quote obeys the original latency/freshness rules; no
later quote can close an earlier partition. Each independent account starts with
synthetic USD10,000. Later prices may warm the later account; earlier cash,
positions and financing cannot carry over.

Only the149 fixture CLI is extended among prior tested files. Its three original
defaults retain the exact canonical input digests recorded by149. The149 runtime
and all underlying148/147/146/strategy/frozen-control bindings stay unchanged.
Existing source-bound checkpoints are not migrated or invalidated by a generator
option. The source archive records the extended generator and new tests explicitly.

## Acceptance checks

**127 tests passed together, with zero failures or errors, in1962.993 seconds.**
The invocation covers10 new acceptance checks and117 relevant existing policy,
boundary, cross-accounting, session and preflight checks. Source hashes stayed
unchanged throughout the recorded run.
The full prior155/156/258 suites are not rerun or added to this invocation's count.

The new checks require all64 comparison cells to remain present, with all market
statuses unavailable and returns null. All48 original control accounts receive
independent rational accounting audits. The eight primary EW accounts must form
the expected setup and direction with aligned parents and complete as-known
coverage; each must enter and close once.

Independent Fraction arithmetic reconstructs executable entry, side-dependent
protective tick rounding,2R target rounding toward entry, volume flooring,
risk/margin/cap constraints, commission, exit, net and final cash. Both cost
profiles are checked. Gap losses must exceed the estimated entry risk and latch
the loss pause. These observations do not turn stops or pauses into guaranteed
maximum loss caps.

Two EW5 witnesses receive full-prefix, separate-process restart checks: adverse
short pending before entry, and base long held after entry. Their complete final
reports must match continuous replay, including snapshots, pending state, ledger,
coverage and quote/cancellation audits. Saved comparison ledgers must also match.
These are local paper restarts, not broker reconciliation or order acknowledgements.

All64 comparison cells were computed and retained. All eight primary accounts
reconciled exactly with independent rational calculations, including protective
rounding and cost handling on both sides. All48 control accounts passed independent
audits. Both EW5 restart reports matched continuous replay in full across separate
Python processes, and the saved comparison ledgers agreed. Later accounts also
reconciled from their own fresh starting capital without incoming positions.

| Setup/direction | Fixed exit case | Primary cost profiles |
| --- | --- | --- |
| EW3 long | Target | Base and adverse |
| EW3 short | Gap stop | Base and adverse |
| EW5 long | Gap stop | Base and adverse |
| EW5 short | Target | Base and adverse |

The fixture checks retain the old default digests, reject unsupported options,
exercise the public flags and verify that choosing a future EW5 short target or
gap leaves the earlier decision-event prefix identical. The source/generator
declaration fixes all cases before returns. Two isolated comparison processes at
most are used when memory/CPU availability permits; each replay stays chronological.

```sh
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py fixture NEW-INPUT.json --case wave --setup EW5 --side -1 --outcome target
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py freeze NEW-INPUT.json NEW-FREEZE.json
PYTHONPATH=src:tests python3 scripts/elliott-session-comparison-149.py replay NEW-INPUT.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
PYTHONPATH=src:tests python3 -m unittest test_elliott_session_acceptance_150 test_elliott_full_policy test_elliott_full_boundary test_elliott_full_crosscheck test_elliott_sessions_146 test_elliott_study_145 -v
```

The [portable verification record](evidence/elliott-session-acceptance-150/README.md)
contains the full test log, completion, pre-return case declaration, primary-account
and restart summaries. Full source/data artifacts remain under ignored reports:

- [Verification/source summary](../reports/elliott-session-acceptance-150-verification-001/verification-summary.json)
- [All64 comparison cells](../reports/elliott-session-acceptance-150-verification-001/matrix/cells.json)
- [Eight primary account checks](../reports/elliott-session-acceptance-150-verification-001/matrix/primary-accounts.json)
- [48 control accounting audits](../reports/elliott-session-acceptance-150-verification-001/matrix/control-audits.json)
- [Separate-process restart checks](../reports/elliott-session-acceptance-150-verification-001/matrix/restarts.json)

The generated-artifact inventory identifies246 files totaling3,083,591,174 bytes.
It excludes itself and its referencing verification summary. Tested source/archive
bytes, declared generator identities and generated account-report hashes were
verified. Large source archives, report histories and checkpoints stay outside Git.

## Remaining scope

This is wider deterministic software coverage using constructed data, not a market
win rate, performance estimate, trading-income demonstration or study admission.
All16 actual market cells and native submissions stay unavailable. No market
source, acquisition window, account, terminal, credentials or reserved prices are
accessed or assigned. Protected dates, closed routes and the expired capture
restrictions remain unchanged. No real-money mode or order toggle is added.

Qualified source/use/clock/coverage/cost/prior-trial qualification, the qualified
chronological runner, broader nested/fault/variable-session acceptance, new-adapter
viewer integration and disabled native demo reconciliation remain unfinished.
Unsupported control calendars retain149's explicit unavailable results. Sparse
invented quotes do not establish complete tick paths or true intrabar drawdown;
the inherited rollover/timing differences remain explicit limitations.
