# Sprint 207 · Source methodology and first-opening timing

19 November 2026. The EV Trading Labs H1 catalogue remains a candidate.
The public methodology adds detail about the source M1 series. The Level B
audit now shows how many scheduled H4 closes could reach the first H1 open
under any given finalization delay on an invented calendar.

## EV Trading Labs review

- **Opening fields.** The catalogue describes H1 UTC opening labels, an M1
  resampling step and two sets of OHLC fields. The publisher’s separate
  EURUSD research method describes M1 candles with observations and uses a
  midpoint for its opening and closing calculations, with a bid fallback
  when the ask is absent. That methodology concerns the publisher’s research
  calculations. The catalogue still leaves open how the H1 `o` and `ao` are
  selected and whether each pair comes from the same underlying tick.
  [File catalogue](https://evtradelabs.com/data) · [EURUSD methodology](https://evtradelabs.com/blog/eurusd-seasonality-day-month-session)
- **Coverage.** The research article describes the M1 observations included
  in its analysis and the cutoff it applies to sparse days. The downloadable
  H1 series still needs its own missing-minute, partial-hour and closure
  definitions. A year listed in the catalogue establishes product scope.
  Historical completeness and intraday calendar edges still need review.
  [File catalogue](https://evtradelabs.com/data) · [EURUSD methodology](https://evtradelabs.com/blog/eurusd-seasonality-day-month-session)
- **Terms.** The distributor states that the files are free to use with
  attribution and describes them as derived from Dukascopy. The reviewed
  public material leaves open which upstream terms cover the distributed
  resamples. Dukascopy’s general website terms alone do not establish the
  terms of any separate arrangement with the distributor.
  [Distributor catalogue](https://evtradelabs.com/data) · [Dukascopy website terms](https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/)

A single H1 file could show which labels and prices the distributor published
but could not recover the original tick times or settle whether the sides were
paired. Defer a price sample while those construction and source-use questions
remain open. Exness remains the lead for paired tick data.

## Calendar-only audit

For each H4 close, find the first scheduled H1 open at or after the close,
within the next-H4 expiry. The earliest possible H4 publication is the H4
close plus the calendar's declared finalization delay. Child bars can arrive
later. An early lower bound leaves the timing possible. A tie needs the
decision to precede the opening in a declared event order. A lower bound
after the opening makes the entry too late. These timing bounds leave
coverage, setup, spread, and other eligibility checks to their existing gates.
[Protocol C4](PROTOCOL.md#c4-entry-and-data-level-semantics)

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline.entry_timing \
  invented-calendar.json new-timing-report.json
```

The reproducible example uses 104 invented five-day weeks, six H4 slots per
24-hour day and a 48-hour closure between weeks. The last close has no
following slot in scope. Both cases use the same schedule.

| Finalization delay | H4 closes | Earliest decision before open | Tied and order-dependent | Already late | No scheduled entry |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 ms | 3,120 | 103 | 3,016 | 0 | 1 |
| 2,000 ms | 3,120 | 103 | 0 | 3,016 | 1 |

At two seconds, only the 103 pre-closure H4 closes have enough time in this
example. The 60-opportunity strategy gate therefore has little room for
filters if a later source calendar produces a similar result. The figures
are counts of dated slots in an invented calendar. Phase 10 still needs
actual strategy opportunities from an admitted EURUSD development source.

## Verification and next decision

The timing, opening, Level B fill, signal-count and source-coverage suites
passed 68 tests. The command reproduced both calendar totals. The canonical
metadata status still reports `UNAVAILABLE` with null actual counts. This
sprint used public documentation and invented calendars. It opened no market or validation
files and sent no messages. The next source decision depends on the dated
H1/H4 session calendar and earliest H4 decision model for the exact feed.
