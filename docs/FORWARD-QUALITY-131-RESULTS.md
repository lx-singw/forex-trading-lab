# Forward recorder quality integration131 — 16 October 2026

The common offline quality adapter is implemented and verified for the existing
forward111 recorder and paired-clock130 format. The CLI produces deterministic
JSON and Markdown directly from pinned raw files. It has no terminal, strategy
or order interface. Longer native paired collection has not been implemented
or deployed in this integration.

## Verification

All **92 tests** pass: 30 new integration tests, 38 retained forward111 tests and
24 retained timing130 tests, with no failures/errors/skips. The forward suite
includes its shared C++ core/account-guard integration build and test. The exact
new sources and retained dependencies were frozen before testing. See
[verification](../reports/forward-quality-131-verification-001.json) and
[source freeze](../reports/forward-quality-131-development-source-001.json).

Invented paths cover missing paired clocks, completed/unfinished pairs, empty
and pending/partial captures, repeats across rotation, native bit/flag changes,
source reversals and high-water recovery, fixed receipt-gap boundaries, raw
clock/offset changes, event-detail caps with full counters, chronological event
prefixes, separate source boundaries, unsafe manifests and read-only CLI behavior.

## Saved-data application

The actual default report reads **61 files / 2,304,083 bytes**. The formats stay
separate and retain their own dates, hashes and capture states.

| Source | Quotes | Source-label advances | Adjacent repeats | Longest observed repeat | Paired clocks |
|---|---:|---:|---:|---:|---|
| Forward111 pilot | 7,188 | 2,782 | 4,405 | 24.515965 seconds | Not recorded |
| Timing130 observation | 58 | 46 | 11 | 5.212442 seconds | 58 complete pairs |

Both are stopped prefixes with code13 (elapsed limit), with no pending attempt
or truncated tail in the saved runs. There are no adjacent source-label
reversals or quote-receipt gaps over two seconds in either sample. The111 pilot
has 2,783 distinct source-millisecond labels;130 has 47. Repeat spans describe
receipt-to-receipt behavior, not quote age, stale executable prices or complete
tick delivery. Different dates/windows and sampling rates prevent attributing
the differing repeat counts to a feed improvement.

The timing report records eight changes in TimeCurrent-minus-TimeGMT between
+10,800 and +10,801 seconds. TimeTradeServer-minus-TimeGMT remains +10,800 and
TimeLocal-minus-TimeGMT +7,200. These are raw clock comparisons with no
timezone adjustment. The111 pilot's paired clocks remain explicitly absent;
the later offset cannot fill its missing observations.

Quote-read start gaps are 500,052–1,362,607us for111 and
1,000,308–1,135,791us for130. These quote-read markers differ from130's
first-clock poll-start markers documented in its capture report. The quality
notice threshold remains the existing fixed two-second engineering threshold,
without market-data admission or a new source-age assumption.

All 4,405 forward quote events are counted; the first 128 details are stored and
truncation is explicit. All 11 timing quote-event details fit. No run is joined
to the other. JSON/Markdown CLI outputs match the library; a repeat JSON run is
byte-identical. Retained wire-reader counters and all58 paired calculations
match, including130's saved capture summary. See
[application review](../reports/forward-quality-131-application-review.json),
[generated report](../reports/forward-quality-131-report.md) and
[JSON](../reports/forward-quality-131-report.json).

## Scope and next work

All 604 earlier source/config/test hashes and 65 native input hashes remain
unchanged. Four new files make608. Prior handoff bodies and sealed evidence are
preserved. No MT5 compilation/deployment/launch, SDK connection, account/terminal
setting change, support contact, historical strategy replay, P&L or tuning.
Financial strategies, risk/cost rules and weights remain fixed. October2026 is
quarantined; November–December remain reserved/untouched and2025 consumed.
Historical/provider/H.10/native090 routes stay closed.

The integration now exposes missing clock evidence, repeats, reversals,
sampling gaps and unfinished pairs consistently. It does not establish quote
age, complete costs, executable quality or a profitable strategy. Market/paper/
order/real-money availability remains false. Next is separately preparing a
longer fixed read-only recorder with paired timing fields, using these offline
checks before any manual collection. No MT5 action is needed for131, and the
old111/130 dated programs stay expired. See [usage](FORWARD-QUALITY-131-USAGE.md).
