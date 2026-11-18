# Sprint 198 · Timestamp coverage and warmup audit

18 November 2026. Added a coverage audit for invented source timestamps and
explicit warmup and development calendars. The two calendars meet at the
development start. The audit reuses the existing H1, H4 and D1 windows and
reports the evidence a later archive and calendar review would need.

## What the report measures

- H1 openings with a quote exactly on the scheduled timestamp, with a late
  first quote, or with no quote in the window. Late openings report the delay
  in milliseconds. Equal timestamps and quotes during declared closures have
  separate counts. Timestamp order and half-open scope are enforced.
- H1, H4 and D1 coverage. An H4 or D1 window has complete timestamp coverage
  only when every scheduled H1 child has at least one quote. These counts
  measure presence within a window. A quote’s precise timing within that
  window is a separate finding from the first-opening audit.
- Warmup at the development start. The report counts complete windows due by
  the seam under the declared finalization delay and shows pending windows
  separately. It compares both total and trailing complete counts to the
  existing 253 H1, 390 H4 and 253 D1 thresholds. Trailing counts show how
  much contiguous history is available under the declared schedule.

An exact source timestamp shows that the recorded timestamp and the declared
opening coincide. Receipt timing, a price available to the strategy and Level B
admissibility require separate evidence. The audit takes timestamp arrays and
emits coverage counts.

## Run and verify

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline.source_coverage SCOPE.json TIMESTAMPS.json NEW-REPORT.json
```

The scope JSON uses schema `TRL_SOURCE_COVERAGE_198_V1`, kind
`invented_trendline_coverage_scope`, symbol `EURUSD`, `warmup_calendar`,
`development_calendar` and `input_sha256` for the exact timestamp-file bytes.
The calendars follow the bounded invented session declaration. The timestamp
JSON contains kind `invented_trendline_source_timestamps` and a `timestamps`
array of ordered integer source milliseconds. The CLI validates the scope
before opening that file. The report binds both inputs and the calendars.
[Calendar example](DATA-163-USAGE.md)

All 110 targeted tests passed, including eight new coverage tests. The CLI
smoke run used an invented 2000 warmup and invented 2001–2002 development.
Its warmup produced 6,240 H1, 1,560 H4 and 260 D1 windows with timestamp
coverage. Delaying one first development quote by 17 ms left that H1 observed
and classified the opening as late. Removing a quote from another H1 left its
hour and the corresponding H4 and D1 windows incomplete. The input and report
files are under the ignored `reports/trendline-source-198/` directory.

## Historical feasibility

The Exness 2020–2022 archive feed and timestamp mapping, dated session
exceptions, and applicable retention terms still need confirmation. Source
dispatch, archive layout and CRC validation, price parsing and independent
qualification belong to the acquisition and audit after those checks.
Phase 10 remains `UNAVAILABLE` with `actual_counts` null. No real archives
were accessed. [Historical source evidence](RESULTS-197.md)
