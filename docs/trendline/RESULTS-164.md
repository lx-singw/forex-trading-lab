# Sprint 164 — Phase 2 invented Level B prices

16 November 2026 (Africa/Johannesburg). **190 tests pass together:41 new and149
existing**, zero failures/errors, in44.479seconds. Sixteen hand-checked invented
component exercises also pass. Phase2 source/run acceptance remains open; no
market result, account simulation or native order capability is introduced.
Predecessor4930d85 was already pushed before this sprint began.

## Delivered behaviour

New trendline/fills.py implements pure, exact-rational opening and completed-hour
price calculations. [Usage and limits](FILLS-164-USAGE.md) document the API and
[verification-164.json](verification-164.json) binds the recorded source/tests.

An entry uses only an explicitly declared historical H1 bid open, spread and
event order. It must be the first scheduled open after the H4 trigger with the
decision already available. A missing first hour, late decision or unresolved
same-clock order abstains instead of borrowing a later price. Supplied midpoint
candles cannot produce executable sides. Entry outputs are independent of later
high/low/close/receipt fields. A finalization delay can legitimately make all
otherwise eligible entries late; no delay is silently removed to obtain trades.

Long enters at ask+slippage, short at bid-slippage. The fixed117 declaration's
base/adverse spread floors and slippage match retained119 profiles. Stops round
outward; exit-side crossing, ATR-distance and spread/distance gates are rechecked.
E2 targets round toward entry and must still offer2R after entry costs. All
calculations remain exact even with16-place computed asks and low global Decimal
precision. Commissions/financing are not applied in a price-only component.

Held long exits use bid, short use ask. Opening gaps use the first supplied
opening-side price plus adverse stop slippage; reached limits retain their price
without favourable overshoot or extra slippage. A known opening reach precedes
an unresolved later range. Otherwise a completed post-fill bar that spans both
levels takes the adverse stop. Trigger-bar movement cannot stop a later fill,
future protection cannot execute against an earlier range, and held protection
continues despite entry spread filters. Intrabar trigger time is left unknown.

Protocol revision3 records the opening/range interpretation before any market
trial. Parameter values remain unchanged; original160-163 revisions stay in Git.
The price-position record validates structural risk, timing, tick and profile/
source consistency. It is a caller-supplied price request, not an authenticated
account checkpoint. E1 protection may tighten prospectively; E2 never trails.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_fills_164 test_trendline_data_163 test_elliott_sessions_146 test_elliott_study_145 test_daily_fills_120 -v
PYTHONPATH=src python3 scripts/trendline-fill-demo-164.py reports/NEW-INVENTED-PRICE-EXERCISES
```

41 new checks cover directions/profiles, frozen-profile parity, first-open timing,
missing/late data, stop/spread/ATR/target boundaries, rounding, bid/ask gap losses,
adverse range ambiguity, known opening reach, pre-fill exclusion, unavailable and
prospective protection, widening spreads, malformed types, source/profile changes,
defensive copies, exact arithmetic and future-file identity. A fresh process
reconstructs a price request and reproduces its gap result. This is not a complete
ledger restart or duplicate-order-prevention acceptance test.

The combined190 invocation includes34 existing163 data,31 session146,28 study145
and56 retained120 account checks. It is not the entire repository suite. Existing
strategy, risk, account, source-plan and native runtime files were unchanged.

The public demo produces16 cases:2 directions x2 costs x4 modes. Four late decisions
skip;12 independent price exercises reach gap stops, adverse ambiguity or known
opening targets. These are not12 strategy trades or account returns. Each saves
its declared invented source/hours/request/result and compares literal expected
prices/reasons. Existing output directories are refused.

For base gap cases, long entry1.10054 exits1.09698 and short1.09946 exits1.10302:
price loss0.00356 versus initial stop distance0.00204, excess0.00152 per unit.
Adverse excess is0.00155. These deliberately constructed exceedances do not
estimate broker execution and do not make stops guaranteed loss caps.

Generated cases/logs remain ignored under reports/trendline-164/. Portable
summary/source hashes are committed. Phase1's80 records remain unchanged, and its
existing verifier still passes. No actual prices, accounts, credentials, terminals,
native helpers, provider requests, capture dates or orders were accessed.

## Remaining phase gates

Phase2 actual source/use/price/spread/calendar/coverage qualification is not
established. All28 trendline market cells remain unavailable/null; the16 earlier
cells and protected dates/routes are unchanged. No source metadata self-claim or
invented fixture unlock can satisfy market/demo admission.

Before Phase2 completion, finish the admissible source/run declaration and the
required reviewed bar/coverage evidence; do not silently mark this phase complete
from software tests. Phase7 still needs setup-to-ledger integration, sizing,
margin, one-position reservations, consumption, daily latches, complete financing,
partition liquidation cutoffs, missing-path handling and sequence/restart audits.
The native boundary stays unavailable; no real-money mode or order transport exists.
