# Source semantics and qualification review 036 — 2026-10-06

The bounded review and independent evidence checks pass. No data qualification
gate was lowered. Fresh/annual eligibility stays false and orders unavailable.
The review made zero market calls, native connections, terminal actions or
market-history downloads. Research used exactly four declared queries, eight
official-page opens and eight finds, within the four/12/eight caps.

| Qualification gate | Evidence status | Remaining requirement |
|---|---|---|
| Saved original integrity | Observed pass | Retain hashes and both source revisions; this says nothing about upstream delivery |
| Relative same-feed prices/volume | Observed pass | Independent provenance and broader predeclared chronological coverage |
| Complete metadata repeatability | Observed failure | Authoritative extra-bit/revision semantics and separately planned repeatability evidence |
| Source clock/session meaning | Unresolved | Calibrated UTC reference and provider-specific historical timezone/DST/session evidence |
| Upstream completeness | Unresolved | Provider coverage provenance and independently reconciled gaps/events |
| Historical executable costs | Unresolved | Date-effective contract fees/swaps/units/conversion and executable bid/ask/slippage evidence |

Each matrix entry in the sealed assessment cites bound local evidence or an
official finding, identifies observed equality/contradiction versus missing
provider evidence, and names its limitations and minimal missing evidence.
These statuses concern the saved scope, not profitability or trading readiness.

Official findings:

- The tick reference documents six flags; the book assigns BID=2, ASK=4,
  LAST=8, VOLUME=16, BUY=32, SELL=64. Tick fields contain complete state, including
  previous values for fields that did not change. [MqlTick](https://www.mql5.com/en/docs/constants/structures/mqltick),
  [official flag table](https://www.mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick).
- The reviewed tables do not define bits128 or1024. The official Python example
  nevertheless shows flags130 and134, both numerically including128. An example
  value supplies no bit definition or explanation for our observed revisions.
  This is bounded absence within the reviewed pages, not a claim that a definition
  exists nowhere. [Python tick example](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py).
- Python range documentation explicitly describes tick/bar times as UTC and
  requires UTC-aware request datetimes. Display-local offsets are distinguished
  from stored times. Our request code used aware datetimes, yet031 raw labels
  are10,795.879..10,798.642 seconds ahead of local receipts. That discrepancy
  remains unexplained; generic documentation does not calibrate the machine
  reference or certify this provider's historical/session meaning. No three-hour
  correction was applied. [Tick UTC contract](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py),
  [bar UTC contract](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).
- Tick APIs document local database synchronization, server retrieval when local
  history lacks requested ticks, and partial/error outcomes for synchronization
  timeout, static-buffer and memory limits. MQL EA/script waiting behavior is
  not a guaranteed Python cancellation bound. This offers context, without
  proving synchronization caused our flag changes or that all upstream events
  arrived. [CopyTicks](https://www.mql5.com/en/docs/series/copyticks),
  [CopyTicksRange](https://www.mql5.com/en/docs/series/copyticksrange).
- Bar records contain OHLC, tick_volume, spread and real_volume; Python bar
  history is limited by chart-available history and its maximum-bars setting.
  The field descriptions do not guarantee tick_volume counts every complete
  quote event or make zero bar spread an executable-cost model.
  [MqlRates](https://www.mql5.com/en/docs/constants/structures/mqlrates),
  [bar range limits](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).
- Symbol properties distinguish spread points and swap calculation models;
  the model determines swap-long/short units. Those properties do not provide
  a date-effective historical fee, swap, conversion or slippage schedule for
  this account. We do not interpret a swap number as a USD charge merely
  because the account is denominated in USD.
  [Symbol properties](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants).

Offline reconstruction verified709,616 native/CSV fields across old033 ticks,
new035 ticks and four bars. It rebuilt all13,769 ordinal overlap pairs, every
changed identity and full-record witness. All seven non-flag fields and order
agree;8,368 flag fields gained bit128, while5,401 complete records remain equal.
The flag transitions and every supplementary changed-row identity agree with
035's sealed evidence. Ordinal price agreement never replaces complete identity:
033 and035 diagnostics remain false, with8,368 complete035 witnesses missing.
Unknown bits remain numeric and uninterpreted.

All498 tests passed before freeze, including16 new authority/budget/attribution,
overlap/ambiguity and gate/policy tests. The ledger freezes100 inputs after
verifying all1,049 previous bindings,1,005 ZIP members and44 external inputs.
The independent checker validates action counts, primary source attribution,
every overlap field/identity, all six gate statuses and unchanged eligibility.
Original hashes, chronological evaluation/cost requirements, consumed2025,
reservedNov–Dec2026 and provider stops are preserved. No strategy/risk/cost
parameter changes, returns, accounts, contacts, paid services or execution.

RAW-DERIVED-POLICY-036.md is a proposal, not an implemented transformation:
retain each raw revision and full flags; keep any future derived known-mask
column separate with complete lineage. No overwriting, blending, clock
normalization, silent masking or retroactive gate changes.

Next is CLOCK-REFERENCE-037-PLAN.md, a bounded read-only machine/HTTP clock
reference diagnostic and at most one guarded current-demo quote. It is declared,
not executed. It can investigate current receipt versus raw-label timing, but
cannot by itself certify historical clock/session meaning, complete history or
costs, and cannot enable strategy returns or orders.
