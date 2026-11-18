# Sprint 196 · EURUSD archive inventory and access

18 November 2026. The existing Exness selector record provides exact links for
the unsuffixed `EURUSD` series. This sprint checks the retained inventory and
separates advertised months, HTTP metadata and actual source admission.

## Metadata scope

Use January–December 2020 as a candidate warmup inventory and January 2021
through December 2022 as a candidate 24-month development inventory. The block
starts with the first full year in the retained selector review and follows in
calendar order. These are catalog labels for a feasibility check. The study
plan assigns its permitted UTC intervals only after source and exposure review.

The four exact links below were observed in the [retained public selector review](../SOURCE-INVENTORY-022-RESULTS.md).
Check each once in the listed order with HTTPS `HEAD`, a short timeout and
redirects disabled. Stop the batch on access denial, rate limiting or transport
failure. Read response status and public file headers. Preserve the evidence
locally under the existing report ignore rules.

1. [2020 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2020/Exness_EURUSD_2020.zip)
2. [January 2020 archive](https://ticks.ex2archive.com/ticks/EURUSD/2020/01/Exness_EURUSD_2020_01.zip)
3. [January 2021 archive](https://ticks.ex2archive.com/ticks/EURUSD/2021/01/Exness_EURUSD_2021_01.zip)
4. [January 2022 archive](https://ticks.ex2archive.com/ticks/EURUSD/2022/01/Exness_EURUSD_2022_01.zip)

Check the public selector for an annual link for each of the two development
catalog years. Use its standard controls and inspect each link without
activating it. If the selector exposes links for the exact instrument and
years, record the observed URLs before any separate header checks.

The public selector showed `Instrument EURUSD` and `Month All months` for the
two years below. Use the same one-request header check and stop conditions for
each newly observed link. The browser resolved the links without starting a
download.

5. [2021 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2021/Exness_EURUSD_2021.zip)
6. [2022 annual archive](https://ticks.ex2archive.com/ticks/EURUSD/2022/Exness_EURUSD_2022.zip)

## Verified availability

The retained selector advertised all 36 months for 2020–2022. The prior
review captured the 2020 annual URL and three January URLs. The current
selector resolved exact annual URLs for 2021 and 2022. Its responses,
together with the header checks, establish a candidate delivery set for
three years of one archive series. [Public selector](https://www.exness.co.za/tick-history/)

| Archive | Link evidence | HTTP status | Advertised ZIP bytes |
| --- | --- | ---: | ---: |
| 2020 annual | Retained selector | 200 | 102,292,491 |
| January 2020 | Retained selector | 200 | 3,572,707 |
| January 2021 | Retained selector | 200 | 7,152,600 |
| January 2022 | Retained selector | 200 | 5,412,286 |
| 2021 annual | Current selector | 200 | 65,861,027 |
| 2022 annual | Current selector | 200 | 123,089,859 |

The three annual sizes total 291,243,377 bytes. The January files overlap
those labeled annual spans and are excluded from the total. All six responses
advertised `application/zip`, had no redirect and reported last modification
on 5 June 2024 UTC. No archive bodies were requested. Those dates and sizes
describe the HTTP objects. Quote-level date bounds, completeness and warmup
bar counts still need to be measured. The exact `EURUSD` link identifies the
archive symbol. Historical account/feed attribution still needs dated evidence.

## What still blocks the count

- **Use and retention.** The provider’s public guide describes downloading and
  backtesting. The applicability of those terms to the lab’s private storage,
  processing and derived H1 history remains open after the sprint 195 review.
  [Provider guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/) · [Use review](RESULTS-195.md)
- **Historical clock and sessions.** Current help states that trading servers
  use UTC+0 and describes a date-filtered schedule. Its static holiday and
  maintenance material covers current rules. The retained 2023 sample’s `Z`
  labels and the current rules leave the 2020–2022 archive clock and dated
  closures unresolved. Do not classify historical gaps from those rules alone.
  [Instrument hours](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours) · [Holiday hours](https://get.exness.help/hc/en-us/articles/17923046759836-Holiday-trading-hours)
- **Admitted coverage.** Before acquiring prices, establish permissible file
  and study scope against the exposure record. Then audit actual spans, eligible
  D1/H4/H1 warmup bars including the FXR angle window, and gaps on a reviewed
  calendar. No validation window is proposed by this inventory. [Protocol](PROTOCOL.md)

The canonical Phase 10 preflight still reports `UNAVAILABLE` and
`actual_counts` is null. All 37 source/run preflight tests passed. The
six local header receipts and metadata status are under the ignored
`reports/trendline-source-196/` directory. Verification matched the exact
request order, both declaration hashes and the retained selector record.
