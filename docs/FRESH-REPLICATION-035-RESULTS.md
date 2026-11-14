# Four-source-hour replication 035 — 2026-10-06

The bounded collector and independent integrity check pass; the **overall frozen
replication diagnostic fails**. All four H1 bars exactly match full-event bid
OHLC and BID-flag counts. However, only 5,401 of the 13,769 complete saved033
records match uniquely: 8,368 records have changed flags. This criterion stays
unchanged, so price agreement cannot silently replace full-record agreement.

Exactly three guarded market reads ran once: one horizon quote, one inclusive
four-source-hour tick range and one four-bar H1 range. Actual DEMO/USD, Algo
Trading off and stable private identity were checked around each read and at
completion. No IDs exported, alternate request, retry, orders, terminal settings
change or strategy replay. All 482 tests passed before acquisition (25 new).

| Raw source-hour formatter | Full quote events | BID flags / H1 tick_volume | Bid flag/value disagreements | Bid OHLC agreement |
|---|---:|---:|---:|---|
| 10:00–11:00 | 24,381 | 16,257 / 16,257 | 44 | Exact |
| 11:00–12:00 | 19,788 | 12,941 / 12,941 | 45 | Exact |
| 12:00–13:00 | 16,991 | 11,033 / 11,033 | 53 | Exact |
| 13:00–14:00 | 13,769 | 8,368 / 8,368 | 54 | Exact |

These are numeric source labels displayed with an API UTC formatter, without
certified UTC meaning. There are zero ASK flag/value disagreements. Each hour
reports all seven fixed event definitions and their original indices, price
and count deltas in the sealed analysis. No definition was searched or adapted.
The last hour has54 disagreements rather than034's53 because its first tick now
has a predecessor in the preceding hour; we do not treat each hour as a restart.
The first full original row alone has an unknown predecessor.

The saved033 hour and new035 overlapping hour have exactly the same row count
and original order. A separate, explicitly **post-result ordinal comparison**
checked every corresponding record. All seven non-flag fields are identical in
all13,769 pairs, including time/time_msc, bid/ask, last and both volume fields.
Only flags changed:

| Old flags | New flags | Records | XOR difference |
|---:|---:|---:|---:|
| 1026 | 1154 | 4,346 | 128 |
| 1030 | 1158 | 4,022 | 128 |
| 1028 | 1028 | 5,401 | 0 |

The supplemental report lists each changed old/new original row index and label.
It explains the observed full-record mismatch; it neither resolves missing
full-identity witnesses nor revises the frozen success criterion. Documented
BID/ASK bits remain unchanged. Remaining masks in the new four-hour response
are1024 on ASK-only rows and1152 (1024+128) on BID-flagged rows. Both extra bits
remain uninterpreted. No claim about their cause, history reconstruction or the
provider's revision policy follows from this comparison. Both sealed originals
are retained as separate observations, never overwritten or merged.

| Verification | Result |
|---|---:|
| New ticks / bars preserved | 74,929 / 4 |
| Complete033 witnesses matched / missing / ambiguous | 5,401 / 8,368 / 0 |
| Native/CSV fields checked, including old033 originals | 709,616 |
| Source-row validation errors | 0 |
| Same-millisecond / exact duplicate transitions | 213 / 0 |
| Largest observed intertick gap | 26.114 seconds |
| Native tick / bar elapsed | 1.2966912 / 0.0001818 seconds |
| Combined native history elapsed | 1.296873 seconds |
| Combined original evidence | 8,743,924 bytes |
| Frozen input bindings | 83 |
| Prior snapshot bindings / ZIP members / external inputs verified | 1,014 / 971 / 43 |

New labels run1791280800009..1791295199789. No exact request-upper-boundary or
hour-boundary events were returned. Every numeric field, hash, byte/row count,
layout, order audit, receipt arithmetic, complete witness and analytical report
field was independently reconstructed. Analysis/checks preserve
diagnostic_passed=false despite four relative hourly hypotheses passing.

The qualification review was sealed before acquisition: historical source clock
and executable costs uncertified, upstream completeness unresolved, performance
testing/normalization/publication unavailable. All four returned bar spreads and
real volumes are zero as observed; no executable-cost inference is made.
035 does not change the older033 failed diagnostic, consumed2025/reserved
Nov–Dec2026, provider stops, strategy/cost/risk settings or disabled execution.
Fresh/annual eligibility remains false. This is infrastructure evidence, not a
profit demonstration or independently verified complete history.

Next: DATA-QUALIFICATION-036-PLAN.md declares a bounded official-documentation
and evidence-gap review, with no market API calls. It will investigate what is
documented about flags/clock/history revisions/cost fields and identify which
qualification evidence is still missing before further acquisition or returns.
