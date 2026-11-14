# Offline quote-flag audit 034 — 2026-10-06

The independent offline audit passes. In this one saved source hour, H1
tick_volume exactly equals the **8,368 BID-flagged events**, rather than all
13,769 quote events. The other 5,401 events carry ASK without BID among the
documented bits. This supports a relative event-definition explanation for the
033 count discrepancy. It does not prove the provider's bar algorithm or restore
the frozen 033 diagnostic: that result remains diagnostic_passed=false.

Exactly zero market requests, native connections, terminal actions or downloads
were made. Strategy/cost/risk settings and originals were unchanged.

| Fixed observation | Count |
|---|---:|
| Full half-open-hour events | 13,769 |
| BID flags | 8,368 |
| ASK flags | 9,423 |
| Both BID and ASK | 4,022 |
| Neither BID nor ASK | 0 |
| Actual bid-value transitions | 8,314 |
| Actual ask-value transitions | 9,423 |
| First row with no predecessor | 1 |
| Bid flag/value disagreements | 53 |
| Ask flag/value disagreements | 0 |
| Disagreements at tied timestamps | 0 |
| Complete 032 records matched uniquely | 196 |
| Missing / ambiguous witnesses | 0 / 0 |
| All binary/CSV fields independently verified | 111,728 |
| Full software regression | 457 passed, 16 new |

All 53 disagreements are BID flags with an unchanged bid value; none are a
changed bid value without its BID flag. Of these, 47 rows have flags 1026 and
six have flags 1030. Every identity and its predecessor's complete eight-field
record is listed in the sealed audit, without collapse or reordering. The first
and last disagreement are original row indices 331 and 13,456. These are
observed flags and recorded values, not an explanation of why the provider sent
those updates. Treat first-row inclusion separately: 8,314 bid transitions plus
one unobserved predecessor case gives 8,315, which is 53 below the bar count.

The histogram is 1026:4,346; 1028:5,401; 1030:4,022. Fixed known mask126 gives
2:4,346; 4:5,401; 6:4,022. Remaining mask1024 occurs in **all 13,769 rows** and
stays uninterpreted. No LAST/VOLUME/BUY/SELL documented bits were present.
The fixed constants and meaning came from the official sources checked during
033, before this audit's freeze: [MqlTick reference](https://www.mql5.com/en/docs/constants/structures/mqltick)
and [flag value table](https://www.mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick).
No new source lookup or speculation about mask1024 occurred during 034.

| Fixed event definition | Events | Count minus H1 tick_volume | Bid OHLC comparison |
|---|---:|---:|---|
| All | 13,769 | +5,401 | All four prices equal |
| BID flag | 8,368 | 0 | All four prices equal |
| ASK flag | 9,423 | +1,055 | Open lower by 0.00001 |
| Both flags | 4,022 | -4,346 | Open and close lower by 0.00001 |
| Neither flag | 0 | -8,368 | Unavailable: empty subset |
| Bid-value changes with first row | 8,315 | -53 | All four prices equal |
| Ask-value changes with first row | 9,424 | +1,056 | All four prices equal |

The bar's bid open/high/low/close is 1.12418 / 1.12485 / 1.12412 / 1.12427.
All seven definitions were declared before row processing. No definition was
chosen by searching for a successful match; all outcomes remain in the report.
First row has no known predecessor, so the with_first event is not claimed to
be an observed value change. There are no exact upper-boundary or outside-range
rows. All input order, tied events and complete identities were retained.

Before processing rows, 73 inputs were frozen after verifying the prior 990
bindings / 948 archive members / 42 external inputs. All 457 tests passed before
freeze. A separate set-based checker independently decoded originals and rebuilt
every histogram, category, event index, disagreement record, witness, subset
OHLC and comparison. It agrees with every reconstructed report field. Outputs
are exclusive and sealed; original 032/033 evidence hashes remain unchanged.

This clarifies a count discrepancy; it is not profit evidence. Unknown bit1024,
the cause of unchanged BID-flagged values, upstream completeness, historical
UTC/session meaning and executable costs remain unresolved. H1 spread0 and
real_volume0 are preserved observations, not a cost model. Fresh/annual
eligibility stays false, orders remain unavailable, and consumed2025/reserved
Nov–Dec2026/provider stops remain untouched.

Next: FRESH-REPLICATION-035-PLAN.md declares one bounded four-source-hour
tick/bar replication to test the fixed BID-count hypothesis beyond a single
hour. It is not executed and cannot qualify performance or lower existing gates.
