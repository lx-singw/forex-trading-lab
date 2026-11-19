# Sprint 205 · Scheduled H1 opening evidence

19 November 2026. The January and July 2022 diagnostics found just 3 of
1,010 observed wall-clock hourly bins with the first source timestamp
exactly on the hour. Another 680 began less than one second later and 327
began at least one second later. The archive CSVs contain source times and
bid/ask pairs. Receipt timing, event order with the strategy, and the set of
scheduled H1 openings still need evidence. These totals describe the two
samples and establish no strategy opportunity count. [January diagnostic](RESULTS-203.md) · [July diagnostic](RESULTS-204.md)

## Prototype

The opening diagnostic reads a validated invented quote tape. At an inclusive
receipt timestamp it reports each scheduled H1 opening reached so far.

| Evidence through the cutoff | Treatment |
| --- | --- |
| First quote is labeled and received exactly at the scheduled open | Take the bid and the ask-minus-bid spread in pips from the same pair. Use the first pair in feed order when several share the boundary. |
| Boundary-labeled first quote is received later | Record the source and receipt times. The scheduled open supplies no price assumption. |
| First source label falls after the scheduled open | Record the timing. A later quote may contribute to completed geometry, subject to the publication rules. |
| No quote for the window has been observed | Record absence through the cutoff. A later report can show the first late quote if it arrives. |

An exact-boundary pair can be passed to the existing Level B price model as
an invented opening assumption with an explicitly supplied ordinal on the same
clock as the H4 decision. The ordinal describes the joint order of those
events. The feed sequence only orders quotes. A decision later than the
scheduled open is skipped. Equal-time entry requires the decision ordinal to
precede the opening ordinal. If the first scheduled entry lacks opening
evidence, a quote from the next hour cannot substitute for it. [Protocol C4 and revision 3](PROTOCOL.md#c4-entry-and-data-level-semantics)

Run the diagnostic on an invented development tape from the repository root.

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline.opening_evidence \
  invented-tape.json new-opening-report.json --as-of EPOCH_MILLISECONDS
```

Use a new report path and replace `EPOCH_MILLISECONDS` with an in-scope
receipt cutoff. The JSON contains time and quote evidence per H1 window,
status totals, the input-file hash and the calendar hash.

## Historical decision

The exact-boundary method is a conservative prototype for deriving an
opening assumption from quotes with source and receipt evidence. The frozen
protocol also permits a declared native historical bar-open approximation.
That route needs defensible bid-open and spread construction, the actual H1
schedule, and a declared model for publication and same-time order. The
availability model must carry any applicable finalization delay into the
first-open eligibility check. A bound on source-label lag alone cannot
establish receipt time or justify reporting a later quote as the open.

The metadata-only Phase 10 report returned `UNAVAILABLE` with null actual
counts. Historical counting still needs source admission, including use and
retention evidence, clock and session mapping, and full development and
warmup coverage. The availability declaration also needs review. This sprint
used only the retained January and July aggregate reports and invented
fixtures. It read no additional market or validation prices.

Verification covers the report command, first-pair selection, delayed
receipt, geometry from a late source quote, missing and closed windows, late
decisions, and equal-time ordering through the existing Level B price model.
