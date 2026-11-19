# Sprint 209 · H4 publication at the weekend boundary

19 November 2026. The 51 potentially timely shortened Friday H4 bars in the
2022 ordinary-hours model depend on publication during the closure. If
publication waits for a quote at or after the first scheduled H1 opening,
even the earliest possible quote is too late with two seconds of processing.
[Ordinary-hours calendar](RESULTS-208.md)

## Platform and archive evidence

- MetaQuotes documents that an MT5 bar can carry its grid timestamp even
  when the tick that creates the bar arrives later. `CopyRates` uses index 0
  to identify the current bar. Its documentation supplies no historical
  event timestamp for when a shortened Friday H4 became available as a
  completed bar. [Tick and bar creation](https://www.mql5.com/en/docs/runtime/testing) · [CopyRates](https://www.mql5.com/en/docs/series/copyrates)
- MT5 schedules `OnTimer` callbacks independently of `OnTick`. Outside
  `OnTick`, `TimeCurrent` reflects the last quote for any Market Watch
  symbol. Timer firings therefore provide no evidence on their own of
  completed EURUSD H4 availability. The platform documents a separate
  calculated server clock and simulated tester times. A clock-based
  aggregator could publish before the reopen if its declared clock,
  calendar and finalization establish a completed bar. That availability
  remains unverified for this archive. [Timer behavior](https://www.mql5.com/en/book/automation/tester/tester_time) · [TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent) · [TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver)
- All nine saved Sunday first labels are later than the modeled opening by
  17.540–268.088 seconds. Under a model in which those Sunday quotes first
  release the Friday decision, each would be late even at zero processing
  time. Those summaries contain source labels. They leave strategy receipt,
  Friday bar publication and the absence of intervening updates unverified.
  [January diagnostic](RESULTS-203.md) · [July diagnostic](RESULTS-204.md) · [Weekend reconciliation](RESULTS-208.md)

## Timing scenarios

The quote-dependent case assumes no qualifying quote arrives between the
H4 close and its first scheduled H1 open. It places the earliest possible
quote at that H1 boundary and starts the processing delay there. Calendar,
bar lengths and expiry come from Sprint 208. The table includes shortened
H4 bars and the final H4 close with no scheduled entry in scope.

| Publication assumption | Processing delay | Before open | Same timestamp | Late | No scheduled entry |
| --- | ---: | ---: | ---: | ---: | ---: |
| Clock at H4 close | 2,000 ms | 51 | 0 | 1,560 | 1 |
| Wait for first possible quote | 0 ms | 0 | 1,611 | 0 | 1 |
| Wait for first possible quote | 2,000 ms | 0 | 0 | 1,611 | 1 |

Timestamp equality still requires decision-before-open order. If the same
quote defines the opening and enables the decision, the decision cannot
precede it. The 1,611 ties therefore carry no established eligibility.
[Frozen entry order](PROTOCOL.md#c4-entry-and-data-level-semantics)

```sh
PYTHONPATH=src python3 tools/exness_2022_timing.py --wait-for-first-open new-timing-report.json
```

## Verification and disposition

The default report reproduced Sprint 208 byte for byte. All 74 targeted
timing, opening, fill, signal-count and source-coverage tests passed. The
metadata-only Phase 10 result remains `UNAVAILABLE` with null actual counts.
No market or validation files were opened and no provider message was sent.

The specific missing evidence is an ordered record of the completed Friday
H4 becoming visible, any intervening EURUSD updates, and the Sunday H1
opening on the same clock. A future read-only demo observation could test
that mechanism for its own feed and dates. The historical archive would
still need source and timing evidence for its own study period.
