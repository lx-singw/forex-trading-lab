# Elliott-inspired detector124 — implementation and observations

Implemented separate EWPB_D124 close-swing detection, frozen before demonstration
outputs. It confirms a turning point only after the next completed trading bar
becomes available, records both times, and observes a later closing-price breakout
of a qualifying pullback. Existing117–123 sources, strategies, costs, risk controls
and results are unchanged. This is a narrow Elliott-inspired hypothesis, not full
Elliott wave counting or a replication of the published neural-network approach.

The fixed rule requires a1% minimum impulse,38.2–61.8% close retracement, one active
setup, a ten subsequent trading-bar expiry,253-bar warmup and matching252-session
trend. Wick-based prospective invalidation takes precedence over a breakout on an
ambiguous OHLC bar. A confirmation that already passed breakout is discarded.
Same-kind swing replacement keeps the immutable confirmed-pivot journal. No
threshold, timeframe or mixture search was conducted.

**86 focused tests pass:38 new detector tests and48 retained118 tests**, no failures,
errors or skips,41.213 seconds including runner overhead. Independent Fraction
calculations cover both directions, boundary equality/epsilon cases, strict ties,
delayed confirmation, closures, original-origin/confirmation invalidation, ambiguous
bars, expiry, warmup/trend suppression and occupied slots. Future continuation
invariance, prefix-only restore, duplicates, immutable published state, rehashed
forgeries, schema/source/lineage/availability guards and CLI preservation pass.
Older accounting/run-control suites retain their saved results and were not rerun.

The original rule freeze and a pre-test clarification are preserved. The latter
states that Decimal arithmetic uses the string representation of118's validated
JSON numbers; the inherited float parser does not preserve arbitrary-precision
JSON literals. No numerical threshold or trading rule changed. There was one
tested source version; no executed test or demonstration check failed.

All53 input/manifest/malformed/matrix files,14 tested source/contract bindings and
separate independent review source froze before demonstration outputs. All17
accepted invented paths and18 malformed inputs were retained. The independent
rational reviewer reconciled **4,265 processed bars,52 confirmed pivots,31 setup
actions and7 breakout observations**. All signal/pivot availability times and
observed-only bar/calendar hashes match. All17 CLI results agree with library
reports. Demonstration duration83.748 seconds.

| Invented case | Confirmed pivots | Observations | Main outcome |
| --- | ---: | ---: | --- |
| long_breakout | 3 | 1 | Later upward close breakout |
| short_breakout | 3 | 1 | Later downward close breakout |
| no_pivots | 0 | 0 | Flat/tied closes |
| small_impulse | 3 | 0 | Impulse below fixed minimum |
| deep_pullback | 3 | 0 | Retracement outside fixed band |
| invalidation | 5 | 0 | Active setup invalidated; later patterns also rejected |
| ambiguous_breakout | 3 | 0 | Invalidation precedes possible breakout |
| expiry_boundary | 3 | 1 | Age10 crossing remains eligible |
| expired | 3 | 0 | Age11 expires; no late catch-up |
| warmup | 3 | 0 | Crossed setup consumed before253 bars |
| opposite_trend | 3 | 0 | Long pattern conflicts with longer direction |
| flat_trend | 3 | 0 | Zero longer direction |
| late_confirmation | 3 | 0 | Breakout already occurred when pullback became knowable |
| delayed_availability | 3 | 1 | Six-hour confirmation delay retained |
| same_kind_plateau | 5 | 1 | More-extreme high replaces current interpretation only |
| retracement_minimum | 3 | 1 | Exact38.2% boundary admitted |
| retracement_maximum | 3 | 1 | Exact61.8% boundary admitted |

These deliberately constructed paths are software checks. Seven observations
are not seven trades, wins or a success rate. Each report has `trades=null` and
`returns=null`; no lots, entry/exit fills, fees, financing or profit are calculated.
A future fill cannot use the pivot price or signal candle close. The independent
reference implements the frozen feature definition; it does not validate an
economic edge or unique Elliott interpretation.

All51 initial/prefix/finished restores match, with guards preventing future steps
during reconstruction. Latest/finished replay is idempotent. All51 checkpoint
faults and18 malformed inputs reject with their exact reasons; invalid inputs
create no manifest.68 output/checkpoint files plus53 frozen inputs make121 data
artifacts. All566 predecessor source/config/test and62 native evidence hashes
remain unchanged; five new files make571. Prior handoff body bytes are preserved.

Existing16 planned market cells remain unassigned/unrun. Four additional standalone
EWPB_D124 cost/period cells are separately declared and also unassigned/unrun. No
market data, untouched validation, selected strategy, calibrated probability or
profitability is established. Data/clock/calendar/coverage/cost/financing evidence
remains unqualified. This detector cannot accept account/position fields or enable
market/paper/order/real-money execution. No actual broker-account lookup, native
price use, historical/reserved replay, contact/acquisition, SDK, MT5 operation,
paid service, account creation or actual order occurred.

Read [the exact definition](ELLIOTT-WAVES-124-PROTOCOL.md),
[usage](ELLIOTT-WAVES-124-USAGE.md) and
[independent audit](../reports/elliott-waves-124-demonstration.json).
Next is [the prepared125 standalone invented fill/cost adapter](ELLIOTT-EXECUTION-125-PLAN.md).
It is unimplemented here and requires meaningful structural-stop risk/ledger tests.
Stops and daily pauses cannot guarantee a maximum loss through gaps.
