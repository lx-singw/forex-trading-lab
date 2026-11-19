# Sprint 204 · Summer archive timing diagnostic

19 November 2026. Repeat the source diagnostic on one July 2022 EURUSD
archive from the already-examined development years. July was chosen from
the independent archived provider schedule published in summer. It can
test seasonal consistency with the January sample without using either
candidate validation year. [January diagnostic](RESULTS-203.md) · [July schedule](https://web.archive.org/web/20220703093843/https://www.exness.com/forex/)

## Scope declared before archive access

Use the public Exness selector for the exact unsuffixed `EURUSD` July 2022
link. Record the displayed URL. Make one ordinary HTTPS HEAD followed by
one GET only if HEAD returns HTTP 200, ZIP type and a positive length no
greater than 25 MiB. Require matching GET type and length. Stop on failures.
Use bounded timeouts, public access without credentials, and no redirects
or retries. Keep source bytes in memory. Apply the same two frozen CSV and
CRC checks and the 256 MiB uncompressed cap used in January. Retain metadata,
source timestamps and aggregates from the diagnostic. [Public archive guide](https://www.exness.com/blog/product/exness-tick-history-bid-ask-prices/)

Use the last Friday and first Sunday labels for July 1/3, 8/10, 15/17,
22/24 and 29/31. Measure signed time differences from the published Friday
20:59 and Sunday 21:05 GMT+0 markers, and record whether each observation
falls in the stated minute. Keep all five comparisons. Compare these
differences with the January schedule and its one-hour seasonal shift.
Use the same three H1 first-label lag categories. These are source diagnostics
within Phase 10. The study’s admission and timing rules continue to apply.

The [public selector](https://www.exness.co.za/tick-history/) displayed
`EURUSD`, `2022`, `July` and this exact
[monthly ZIP link](https://ticks.ex2archive.com/ticks/EURUSD/2022/07/Exness_EURUSD_2022_07.zip).

## Sample results

HEAD and GET returned HTTP 200, ZIP media type and a matching length of
11,300,072 bytes. CRC checks passed. The two parsers agreed on the one CSV
member and all **1,626,091** valid rows, with two tied-timestamp transitions,
zero backwards timestamps and zero exact duplicate records. In the labeled
month, 504 of 744 hourly bins contain quotes. Five consecutive-quote gaps
exceed one hour.

| Weekend | Last Friday label | Difference from 20:59 | First Sunday label | Difference from 21:05 |
| --- | --- | ---: | --- | ---: |
| 1–3 July | 20:58:56.038 | −3.962 s | 21:05:17.659 | +17.659 s |
| 8–10 July | 20:58:51.676 | −8.324 s | 21:07:29.771 | +149.771 s |
| 15–17 July | 20:58:51.615 | −8.385 s | 21:05:27.295 | +27.295 s |
| 22–24 July | 20:58:59.964 | −0.036 s | 21:06:25.532 | +85.532 s |
| 29–31 July | 20:58:59.347 | −0.653 s | 21:05:39.574 | +39.574 s |

All five Friday labels are seconds before the published marker. None falls
in the 20:59 minute. Three Sunday labels fall in the published opening
minute, and two arrive later. Across the January and July samples, Friday
last-label and Sunday first-label hours both shift one hour earlier in July.
This corroborates the seasonal schedule in the source labels. Continuous UTC
clock accuracy, date-specific exceptions and broader coverage remain open.
[January schedule](https://web.archive.org/web/20220118223244/https://www.exness.com/forex/) · [July schedule](https://web.archive.org/web/20220703093843/https://www.exness.com/forex/)

## Implication for the opening rule

| First source label within observed hour | January | July | Both months |
| --- | ---: | ---: | ---: |
| Exactly at the hour | 0 | 3 | 3 |
| Later by less than one second | 303 | 377 | 680 |
| Later by at least one second | 203 | 124 | 327 |
| Observed hours | 506 | 504 | 1,010 |

This measures the first **source timestamp** recorded within each wall-clock
bin. A Level B bid open and its entry spread are a declared approximation
at the scheduled H1 open. If using these files for Level B, that declaration
needs to specify and justify the opening price and spread construction, the
source-to-strategy availability model, and decision ordering. The frozen
rule skips an entry when the decision arrives after the scheduled open.
Using the later quote as the actual entry time would need a separately
declared timing model. Level Q additionally needs strategy-visible receipt
evidence for its freshness and event ordering. [Protocol C4](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Status and verification

Both source samples are qualification evidence. Phase 10 remains
`UNAVAILABLE` with null actual counts pending archive admission and a
reviewed opening model. The July 2022 Exness file is recorded as known
development exposure. The in-memory diagnostic stored a hash and report
under the ignored `reports/trendline-source-204/` directory.

All 46 targeted tests passed, including the audit, preflight and first-open
ordering checks. The local verifier reconciled the sample to the frozen
declaration, response headers, January audit and current Phase 10 status.
