# Cost128 native capture results — 14 October 2026

The requested manual launch produced one closed, complete **1,466-byte export**.
All **five queries succeeded**, each with error code 0. The frozen CLI and
library inspector agree. Independent raw-byte review agrees on all outcomes,
native double bits, clock groups and timing. The later native-file hash still
matches the unchanged canonical copy.

The 12 digest-linked frames contain one header, five attempt/outcome pairs and
a normal end record. There is no pending attempt, pending rule payload or partial
tail. Recorded origin-to-end elapsed time is **3.061 milliseconds**, not a
general execution-latency or interruption guarantee.

## Observed cost and margin responses

| Query | Observed response |
|---|---|
| Commission rules | Successful return count 0; no rule or tier rows |
| Buy initial margin factor | 1.0; native bits 3FF0000000000000 |
| Buy maintenance margin factor | 0.0; native bits 0000000000000000 |
| Sell initial margin factor | 1.0; native bits 3FF0000000000000 |
| Sell maintenance margin factor | 0.0; native bits 0000000000000000 |

The commission result is **reported_empty**, a successful response rather than
a failed query. The documented API returns zero when no rules are specified for
the symbol. This observation supplies no commission tiers, charge conditions or
currency/value fields to interpret. It does not establish historical fees, all
account charges, slippage, financing or zero total trading costs.
[MetaQuotes commission return semantics](https://www.mql5.com/en/docs/marketinformation/symbolinfocommissions)

The margin values are directional factors. They are not dollar amounts, leverage
ratios or proof of margin-free trading. An initial factor of 1 is a multiplier on
the applicable base margin. The returned maintenance factor 0 is retained as a
reported value without computing a maintenance requirement or asserting that an
open position needs no margin.
[MetaQuotes margin-rate API](https://www.mql5.com/en/docs/marketinformation/symbolinfomarginrate)

The earlier [metadata127 capture](METADATA-PROBE-127-CAPTURE-RESULTS.md) reported
1:10 leverage, 100,000 contract size, EUR margin currency and raw swap properties.
It was recorded at a separate time. These two observations do not form an atomic
contract snapshot or authenticated cross-run account-identity proof. No current
or historical USD fee/margin model was built by combining their fields.

## Clock evidence

Both raw clock groups agree:

| Clock | Raw seconds | Label rendered without a timezone certification |
|---|---:|---|
| TimeGMT | 1,792,001,785 | 2026-10-14 18:16:25 |
| TimeLocal | 1,792,008,985 | 2026-10-14 20:16:25 |
| TimeCurrent | 1,792,012,585 | 2026-10-14 21:16:25 |
| TimeTradeServer | 1,792,012,585 | 2026-10-14 21:16:25 |

Server labels remain exactly 10,800 seconds above nominal computer GMT; local
time remains 7,200 seconds above it. The GMT-offset field is -7,200 and the
daylight-savings field 0. These are further raw observations consistent with
the earlier clock-domain hypothesis. No offset was applied, and this capture
contains no quotes from which to evaluate source age or feed liveness.

Recorded native call durations are clock-before 65 microseconds, commissions
519, buy margin 2, sell margin 2 and clock-after 3. Read/guard boundaries remain
distinct. These timings do not prove future delivery or blocked-call bounds.

## Preservation and verification

The original native file was opened read-only using an exclusive handle, copied
byte-for-byte into ignored storage and independently checked after copying. The
deployed MQ5, two headers and EX5 hashes still match their tested bindings.
All **593 source/config/test files and 63 earlier native input hashes** remain
unchanged. This export brings retained native input files to 64.

[Inventory](../reports/cost-probe-128-capture-inventory.json),
[frozen inspector outcome](../reports/cost-probe-128-capture-inspection.json),
[independent metrics](../reports/cost-probe-128-capture-independent-metrics.json),
[read-only review](../reports/cost-probe-128-capture-readonly-review.json),
[native recheck](../reports/cost-probe-128-capture-native-recheck.json).
The [capture source closure](../reports/cost-probe-128-capture-final-source.json)
and [completion review](../reports/cost-probe-128-capture-completion-review.json)
preserve this capture and earlier handoff bodies.

The preparation's 44 Python tests and 140 C++ checks remain retained evidence;
they were not rerun here because source did not change. The actual captured
file separately passed the frozen CLI/library inspector and independent review.

The location beside the matching deployed source, launch confirmation and
complete export provide runtime evidence. An unkeyed hash chain does not
authenticate the producer or independently prove every guard/account query.
Account identifiers, server strings and credentials were not exported.

No trading, profit/loss calculation, strategy selection, parameter tuning,
financial-rule change, SDK connection, terminal launch/settings change by the
assistant, contact, account creation, paid service or historical/reserved replay
occurred. Market, paper, order and real-money availability stays false.
October remains quarantined, November–December2026 reserved and2025 consumed.
Closed historical/provider/H.10/090 and old dated107/111 routes stay closed.

## Next concrete work

Prepare an offline source-and-cost evidence summary from the preserved111,
127 and128 captures. Keep each observation's original hash, time labels,
query status and scope. Display reported facts separately from absent,
unqualified or model-assumed terms. Do not silently join different runs into a
single authenticated contract, override historical costs or admit strategy
performance. This is read-only integration work requiring no MT5 action.

After that summary, address the remaining clock, freshness, coverage/calendar
and cost evidence before any market strategy comparison. Current successful
metadata reads do not repair historical gaps or supply sufficiently long,
untouched chronological evaluation periods. No more MT5 clicks are needed
for this completed capture review.
