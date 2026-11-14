# Source-hour context 033 results — 2026-10-06

The guarded collection and original-integrity checks pass. The frozen diagnostic
does **not** pass: hourly bid OHLC agrees exactly, but H1 tick_volume is 8,368
versus 13,769 full-source quote events, a difference of 5,401. Preserve this
failure unchanged; no gate was redefined after observing it.

Exactly three market reads ran once: horizon, full inclusive tick range, H1 bar.
Actual DEMO/USD, disabled Algo Trading and stable private account identity were
checked around each read and at completion. No identity was exported. No orders,
settings changes, strategy replay or alternate request occurred.

| Observation | Result |
|---|---:|
| Full tick originals | 13,769 |
| H1 bars returned | 1 |
| All 196 complete 032 records matched uniquely | 196 |
| Missing / ambiguous witnesses | 0 / 0 |
| Binary/CSV fields independently compared | 110,160 |
| Exact upper-boundary events | 0 |
| Same-millisecond transitions / exact duplicate transitions | 30 / 0 |
| Invalid rows | 0 |
| Largest observed intertick gap | 26.114 seconds |
| Native tick / bar call elapsed | 0.0009028 / 0.0001099 seconds |
| Combined native history elapsed | 0.0010127 seconds |
| Combined original evidence | 1,611,633 bytes |
| Software tests before acquisition | 441 passed, including 25 new |

The original labels run from 1791291600012 through 1791295199789. These are raw
source labels, without certified UTC interpretation. The horizon label
1791297333273 is beyond the completed hour and within the declared receipt
bound. H1 bid open/high/low/close is 1.12418 / 1.12485 / 1.12412 / 1.12427;
all four equal the direct half-open-hour reconstruction. Bar spread and
real_volume are both zero as returned; neither establishes executable costs.

The independent checker waited for the collector process and metadata seal to
complete. It verified every original field, hash, row/byte count, layout, audit,
receipt arithmetic and complete-record witness. It passes **checker integrity**,
while preserving **diagnostic_passed=false** for the volume disagreement.
The collector, checker, tests, protocol and 65 ledger bindings remain frozen.
The prior 963 bindings / 922 archive members / 41 external inputs were verified.

A clearly separate, post-result flag observation offers a hypothesis, not a
revised success criterion. Flags 1026 occur 4,346 times, 1030 occur 4,022 times,
and 1028 occur 5,401 times. The first two counts sum to the bar's 8,368.
Installed SDK constants, inspected without connecting or requesting market data,
define BID=2 and ASK=4. Their documented meaning is a bid or ask update flag.
See the official [MqlTick reference](https://www.mql5.com/en/docs/constants/structures/mqltick)
and [flag value table](https://www.mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick).
The observed equality therefore suggests this bar's volume counts bid-flagged
events, while the full response also includes ask-flagged events without BID.
This is an inference about one hour, not proof of the broker's bar algorithm.
An additional 1024 bit appears in every row and remains unexplained. Consecutive
bid values change on only 8,314 transitions (8,315 including the first row),
so flag presence must not be silently replaced by counting value changes.
One official-documentation search and one SDK-constant-only inspection occurred
after the frozen checker result; neither made a market-history request.

Same-feed agreement cannot certify upstream completeness, historical UTC/session
meaning, realistic historical spreads/fees/swaps or an edge. Maximum gaps are
observations, not proof of missing or complete events. Fresh and annual
eligibility remain false. Consumed 2025, reserved Nov–Dec 2026, existing provider
stops and all strategy/cost/risk settings remain unchanged.

Next is the separately declared, entirely offline FRESH-FLAGS-034-PLAN.md.
Audit the flag/count hypothesis and flagged-versus-value-change differences on
these sealed originals before planning larger acquisition or returns. It cannot
retroactively turn this stage's frozen volume comparison into a pass.
