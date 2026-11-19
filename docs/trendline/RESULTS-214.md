# Sprint 214 · Prior quote age at the Sunday opening

19 November 2026. The archived quote immediately before the scheduled
Sunday opening is at least 48 hours and 6 minutes old in all nine sampled
weekends. The first Sunday quote is later than the opening in every case.
[January opening diagnostic](RESULTS-212.md) · [July H4 alignment](RESULTS-213.md)

## Evidence and calculation

Match January and July's retained Friday/Sunday summaries to their later
window-coverage diagnostics by archive hash and row count. Both diagnostics
found zero rows outside the modeled H1 windows. Validate that each summary
pair corresponds to adjacent weeks in the candidate ordinary-hours schedule.
The last Friday label then gives the youngest possible archived source quote
before the scheduled Sunday opening. With nonnegative delivery delay, a
strategy that has yet to receive that quote would have an older quote or none.
These are bounds under the candidate timestamp and calendar mapping.
Complete archive capture and actual strategy receipt still need evidence.
[January boundaries](RESULTS-203.md) · [July boundaries](RESULTS-204.md) · [Calendar model](RESULTS-208.md)

| Sample | Weekends | Minimum previous quote age at open | Maximum previous quote age at open | First Sunday source lag |
| --- | ---: | ---: | ---: | ---: |
| January | 4 | 48h 6m 0.698s | 48h 6m 21.925s | 17.540–268.088s |
| July | 5 | 48h 6m 0.036s | 48h 6m 8.385s | 17.659–149.771s |

The existing two-second Level Q freshness limit is a comparison reference.
Three Friday labels are within two seconds of the modeled Friday close, and
zero prior quotes are within two seconds of the Sunday opening. The frozen
closure provision can carry a fresh closing mark for held-position accounting.
A Sunday entry still requires evidence for its opening price, spread and
availability. [Frozen entry and closure rules](PROTOCOL.md)

## Verification and disposition

The diagnostic reads four named retained summaries, binds their hashes and
rejects mismatched archives, nonadjacent pairs and evidence of closure quote
rows. The four hashes and nine age bounds reconciled independently. All 81
targeted tests passed. This sprint used retained metadata and invented test fixtures.

```sh
PYTHONPATH=src python3 -m tools.exness_weekend_opening_214 new-bounds-report.json
```

Phase 10 remains `UNAVAILABLE` with null actual counts. The prior Friday
pairs and the first later Sunday pairs leave the modeled opening price and
spread unverified. The calendar-only candidates from shortened Friday bars
still need independent opening-side evidence before consideration for the
historical counter. [Calendar-only bounds](RESULTS-208.md) · [Weekend publication model](RESULTS-209.md)
