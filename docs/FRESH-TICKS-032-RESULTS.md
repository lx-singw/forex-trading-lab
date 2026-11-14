# Full-tick sample 032 — completed

The single declared EURUSD request returned **196 ticks**. All **120** snapshots
from031 match original rows with no ambiguity. The67 distinct polled quote
identities map to67 original rows; the sample contains129 additional ticks that
polling did not observe. This demonstrates why polling is insufficient for a
historical tick replay; it does not prove complete provider delivery.

The request used raw numeric labels1791293942000..1791294003000 inclusive,
61 seconds. First/last returned labels are1791293942095 and1791294002620.
Those labels are not interpreted as UTC or shifted. Current receipt clocks are
separate, and the preceding probe's approximately three-hour lead is retained
as a clock limitation.

| Original-row audit | Result |
|---|---:|
| Rows | 196 |
| Invalid quote/time/auxiliary/range/chronology rows | 0 |
| Same-millisecond transitions | 1 |
| Exact duplicate transitions | 0 |
| Maximum intertick gap | 3.121 seconds |
| Polled witnesses matched | 120/120 |
| Ambiguous witnesses | 0 |
| Binary fields independently compared with CSV | 1,568 |

The largest gap is descriptive; it is not classified as an outage or closure.
The native call took33.5071578 seconds, below the declared60-second soft timeout.
No second request, alternate offset, retry, symbol selection, terminal launch,
login, order or terminal setting/EA change occurred. Actual DEMO/USD, Algo Trading
off and stable private identity were checked around the request and completion.
No identity or credential values are exported.

## Implementation and preservation

Separate fresh_ticks_032.py and fresh-ticks-032.py reserve exclusive output
before connection, perform the one frozen request, and preserve bounded source
rows before quote/range/chronology validation. Oversized and unsupported schema
responses stop without exporting a truncated prefix or unknown/private fields.
Known-schema failures preserve all rows and a safe failure, without sorting,
dropping duplicates, price rounding, timestamp normalization or interpolation.
The SDK can allocate or block before Python can enforce export/time limits;
the limits do not guarantee bounded native memory or cancellation.

Originals under data/fresh-ticks-032:

- raw.csv: all eight source fields,11,171 bytes, round-trip numeric text.
- response.bin: lossless numerical response,11,760 bytes,60 bytes per row.
- capture.json/.sha256: safe metadata, request/receipt/layout/current contract,
  counts, hashes and explicit failed eligibility flags.
- reservation.json: exclusive one-request ownership before connection.

The independent checker uses struct and csv rather than the collector audit
helpers. It reconstructs every field, every original audit statistic, and all
snapshot matches. It reports original row indices for every witness and keeps
repeated poll snapshots distinct from source ticks. Runtime account checks are
collector evidence; the independent checker does not reconnect to the broker
or independently prove account identity.

## Verification

All **416 software tests pass**, including16 new collector tests. Cases cover
actual account types/changes, disconnect, Algo Trading/currency/symbol rejection,
date/range bounds, immutable destinations, errors/empty responses, schema/privacy,
row/byte budgets, complete failure preservation, binary padding, invalid fields,
ties/duplicates/gaps and soft timeout. Tests passed before freezing or connection.
The ledger binds63 exact code/test/protocol/031/runtime inputs. Prior936 bindings,
896 archived members and40 external inputs verified intact before acquisition.

The checker initially ran while the native request was still in progress and
failed because capture.json was not yet available. This zero-data preflight
failure is preserved in reports/fresh-ticks-032-check-preflight-failure.json.
The unchanged checker ran after request completion; no additional API read.
Both checker integrity and the source/witness diagnostic then passed.

Reports fresh-ticks-032-{ledger,tests,checks,review,final-source}.json and seals
retain the evidence. The final ZIP includes source/reports/small original sample;
large old cached data, prior ZIPs, timezone files and pinned Windows runtime
remain externally hash-bound. It is not a self-contained replay environment.

## Limits and next step

This is a same-feed collection diagnostic informed by031 observations, not an
unseen performance test. API success and witness inclusion cannot certify all
unobserved ticks, absolute/historical UTC, historical sessions/outages, upstream
independence, executable commissions/swaps/slippage or an edge. Current contract
properties are not historical execution evidence. Fresh and annual eligibility
remain false. No strategy returns or selection; orders remain unavailable.
Consumed2025, reservedNovember–December2026 and stopped providers are untouched.

Next is FRESH-CONTEXT-033-PLAN.md: one completed source-hour tick/bar consistency
audit containing this sample, with strict guards and a separately frozen budget.
It is declared, not executed. A wider audit can establish collection consistency;
qualified chronological strategy testing still requires a separate data review.
