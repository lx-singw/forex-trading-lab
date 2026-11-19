# Sprint 217 · Historical session coverage

19 November 2026. The reviewed EURUSD Level B input path now binds an
explicit session calendar to the development plan before opening prices.
The calendar covers the warmup and development dates and checks that each
H1 observation matches its scheduled start and end exactly. The approved
manifest list is empty. [Reviewed historical input](RESULTS-216.md)

## Bundle and calendar

Use `TRL_PHASE10_INPUT_217_V1` as the manifest schema. The manifest
includes a distinct, bundle-relative `calendar_file`, alongside the
existing plan and price paths. The plan's `calendar_sha256` binds the raw
calendar bytes. The reader checks the reviewed manifest, plan and calendar
in that order. A missing, changed or invalid calendar prevents the price
file from being opened.

The calendar object takes `kind` set to
`trendline_historical_session_calendar_217` and an ordered `segments`
array. Each segment has `start` and `end` in UTC epoch milliseconds.
A `session` segment specifies this value in `kind` and supplies `h1` and
`h4` arrays of explicit edges and a boolean `partial` flag. The session
defines one D1 window. A `closure` segment supplies `reason` as
`weekend`, `holiday` or `maintenance`. Segments tile the full reviewed
scope. A session stays within its warmup or development partition. As in
the original session rules, a shortened intraday window occurs at the
end of a session, and a shortened H1 window requires `partial`.

```sh
PYTHONPATH=src python3 tools/signal_count.py historical-input MANIFEST NEW-RECEIPT.json
```

## Causal coverage

The receipt includes H1, H4 and D1 coverage as of the start of development
for warmup and as of the scope end for development. A window is complete
once the plan's finalization delay has elapsed and all scheduled H1
children have arrived. Missing due windows include those with absent or
late children. Pending windows are reported separately. The reader checks
all three declared warmup quantities at the seam. A missing development
child appears in the report for its H1, H4 and D1 windows.

The full-size fabricated weekday schedule exercised 18,792 H1 observations
across 2020–2022. Tests also covered a shortened terminal H1/H4, a
calendar gap, a session crossing the seam, and a late H1 warmup receipt.
All 138 targeted tests passed. The canonical status report matches the
Sprint 216 report byte for byte.

This sprint used fabricated prices and schedules. The canonical Phase 10
status remains `UNAVAILABLE`. The next implementation step is to carry
the verified calendar and bar receipts into the counter, keeping warmup
signals out of the development totals. The count also requires independent
qualification of the source and its opening price, spread and timing.
[Development preflight](RESULTS-215.md) · [Opening alignment](RESULTS-213.md)
