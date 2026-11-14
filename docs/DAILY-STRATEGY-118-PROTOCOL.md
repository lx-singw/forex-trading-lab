# Daily features118 — implementation contract

Implement the fixed [117 declaration](../config/research-candidates-117.json) and
[117 protocol](STRATEGY-EVIDENCE-117-PROTOCOL.md) as pure invented-data features.
This source version does not aggregate quotes, accept market observations,
calculate returns, create positions or execute orders. The117 performance cells
remain unassigned and unrun. No candidate or threshold optimization.

The input is strict JSON `FXDL_DAILY118_V1`, kind `invented_daily_fixture`, clock
`invented_utc_milliseconds`, symbol `EURUSD`. Extra qualification flags, native,
historical or market labels are rejected. JSON duplicates/nonfinite constants,
boolean numeric fields, unknown fields and oversized files are rejected. The
allowed2000–2003 timestamps and explicit invented label are fixture conventions,
not a certificate of true origin. No input can make market admission available.

An invented calendar declares contiguous24-hour UTC days, sequential IDs and
trading/closure status before its first session. Weekday closures in the supplied
generator are an invented schedule, not discovered broker hours. Each DailyBar
has matching session boundaries, positive finite consistent midpoint OHLC, an
observation within that session, availability at/after completion and a SHA256
lineage digest binding its fields, session, case and calendar ID. The digest checks
consistency, not authenticity. Bars must be unique and strictly ordered. Bars on
declared closures are forbidden; missing required trading bars are rejected.

A requested target must be a trading session. All trading bars through it must
exist and be available by the requested decision time. Future complete bars may
be present but contribute no arithmetic or decision lineage. An unavailable target
is rejected; a valid earlier completed target can be evaluated without consuming
later observations. Open bars whose declared availability precedes their end are
rejected structurally. No filling of missing sessions or guessed closures.

The snapshot contains at most253 prior completed trading-session bars and a digest
of only the calendar prefix through the target. The pure `decisions` function
returns four immutable dataclass decisions. Each exposes side, raw signal score,
stop distance, risk multiplier, component sides, trend/z-score features, reason,
availability/decision times, target, used bar digests and fixed rule digest.
Identical replay has identical output. Future valid price/calendar continuation
changes cannot change an earlier decision. Invalid future records still make the
whole bundle structurally invalid; no claim that invalid data is silently ignored.

Active rules share253-session warmup. Trend uses the latest close divided by the
253rd latest minus1. Reentry uses two overlapping20-close windows, population
standard deviations and strict old/inclusive new2-sigma crossings. Zero variance
abstains. ATR uses the latest14 true ranges with each previous close, an arithmetic
mean and multiplier2. Zero ATR blocks active decisions. Cash always abstains with
zero risk/stop. The50/50 mixture returns half risk for a lone side, full risk for
agreement and zero for opposition. Multipliers are feature outputs, not sized
positions. A zero-ATR decision retains its raw signal score/components for
diagnostics while its admitted side/risk are zero. Stop distance is not a loss cap.

The CLI creates new artifacts only. Freeze validates structure/timing and hashes
the fixture, exact fixed117 declaration, rule/schema definitions and source/test/
protocol files before feature evaluation. Evaluation requires those bindings to
match, rejects boolean target substitution and non-UTC freeze timestamps, then
writes decisions with returns/positions/fills explicitly unavailable. Rule/schema
comparisons preserve JSON types rather than treating `false` as numeric zero.
Hashes are consistency records, not signed origin authentication.

Fixed demonstration cases are all nine trend/reentry-side pairs, zero true range
and insufficient warmup:11 cases,44 candidate decisions. Before any demonstration,
freeze every accepted input and its manifest. Preserve malformed-case inputs and
exact rejection reasons as a separate predeclared matrix. Do not rank these
invented outputs, call them profits or treat them as the16 market-performance cells.

Tests independently calculate feature values and cover timing, chronology,
lineage, closure/missing distinctions, exact boundaries, future invariance,
abstention and mixture arithmetic. This phase adds no position/risk execution
adapter. Later sizing/fill/cost/financing/duplicate/restart implementation requires
a separate source freeze and meaningful independent tests; old hourly tests do
not certify that adapter. No support/provider contact, acquisition, SDK or MT5
action, reserved-data access, paid service, broker account or order in118.
