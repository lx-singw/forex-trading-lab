# Sprint 208 · 2022 Exness ordinary-hours timing

19 November 2026. Under the modeled Exness schedule, a two-second
publication delay leaves 51 H4 closes that could produce a decision
before the first scheduled H1 open. Every one is a shortened Friday H4
bar. With full-length H4 bars only, the timing ceiling is zero. These are
2022 schedule calculations. The Phase 10 gate requires actual opportunities
per strategy across the full development scope.

## Evidence and scenario assumptions

- The retained January and July Exness pages list ordinary forex trading
  hours at GMT+0. Winter runs from Sunday 22:05 to Friday 21:59 and summer
  from Sunday 21:05 to Friday 20:59. The calendar applies those windows to
  52 weeks starting 2 January through the last close on 30 December 2022.
  The ordinary-hours exercise uses the US DST Sundays of 13 March and
  6 November, for 34 summer and 18 winter weeks. A contemporary report
  corroborates the November schedule shift. [Dated provider captures](RESULTS-197.md) · [US DST rule](https://www.govinfo.gov/content/pkg/USCODE-2024-title15/html/USCODE-2024-title15-chap6-subchapIX-sec260a.htm) · [November 2022 report](https://www.brokerxplorer.com/news/us-daylight-saving-ends-exness-changes-trading-hours-3520)
- An affiliate repost dated 23 December lists normal hours for Forex and
  adjustments for several other instruments. The scenario repeats the
  ordinary hours throughout. A complete dated list of EURUSD holiday,
  maintenance and quote-only exceptions for the archive is still missing.
  [December repost](https://exn.fxsignup.com/news/2022122301.html) · [Provider schedule notes](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours)
- The model intersects whole-hour H1 and UTC 00:00/04:00/... H4 buckets
  with each weekly trading window. It treats the published Friday minute
  as the exclusive close and clips the first Sunday H1 open to `:05`.
  This is a research grid choice. MetaQuotes documents that native bar
  labels stay anchored to the grid even if the first tick comes later.
  The exact archive still needs a declared rule for partial bars, usable
  opens and historical publication. [MetaQuotes timeseries](https://www.mql5.com/pt/book/applications/timeseries) · [Protocol C4](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Timing calculation

The diagnostic uses the Sprint 207 timing comparison. It finds the first
scheduled H1 at or after each H4 close, within next-H4 expiry. The earliest
decision is the modeled H4 end plus the assumed publication delay. The
full-length case limits which H4 bars may trigger and preserves scheduled
H1 opens and expiry. No prices or setup rules enter the calculation.

| Eligible H4 bars | Delay | H4 closes | Before the opening | Tied with the opening | Already late | No opening in scope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All scheduled, including shortened | 0 ms | 1,612 | 51 | 1,560 | 0 | 1 |
| All scheduled, including shortened | 2,000 ms | 1,612 | 51 | 0 | 1,560 | 1 |
| Full-length H4 | 0 ms | 1,508 | 0 | 1,508 | 0 | 0 |
| Full-length H4 | 2,000 ms | 1,508 | 0 | 0 | 1,508 | 0 |

There are 6,240 modeled H1 windows. With a positive delay of two seconds,
the 51 pre-weekend triggers depend on a shortened Friday H4 becoming
available during the closure. A publication model that waits for the next
quote would need separate evidence before those decisions could be scored
as timely. At zero delay, ties still require a declared decision-before-open
order. The scenario neither assigns historical latency nor justifies a
later entry. [Timing audit](RESULTS-207.md) · [MetaQuotes server time](https://www.mql5.com/en/book/common/timing/timing_local_server)

An independent check matched the scenario to the nine weekend pairs saved
by the prior January and July audits. Every Friday’s last label is earlier
than the assumed close. Every Sunday’s first label follows the assumed
opening, by 17.540–268.088 seconds. Five are in the opening minute. The
strict exact-boundary method would find no opening price for these nine
Sunday edges. Level B’s historical bar-open approximation needs its own
price, spread and timing evidence. [January diagnostic](RESULTS-203.md) · [July diagnostic](RESULTS-204.md) · [Opening evidence](RESULTS-205.md)

## Verification and disposition

Reproduce the ordinary-hours report from the repository root.

```sh
PYTHONPATH=src python3 tools/exness_2022_timing.py new-timing-report.json
```

The retained January and July schedule captures matched the Sprint 197
hashes. The calendar, opening, fill, source coverage and counter suites
passed 72 tests. Both invented Sprint 207 reports reproduced byte for byte.
The metadata status remains `UNAVAILABLE` with null actual counts. No market
or validation files were opened. The immediate evidence needs are the exact archive’s
historical closures, treatment of shortened H4 bars and availability of
those bars before the Sunday opening. The archive source-use and coverage
checks continue to apply.
