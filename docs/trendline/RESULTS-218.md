# Sprint 218 · Historical development counter

19 November 2026. The Phase 10 counter now accepts a reviewed EURUSD
Level B bundle. The manifest, plan, calendar and price file pass through
the existing hash and date-scope checks. The repository has zero approved
historical manifests. [Historical session coverage](RESULTS-217.md)

## Reviewed run

```sh
PYTHONPATH=src python3 tools/signal_count.py historical-count MANIFEST NEW-COUNT.json
```

Use manifest schema `TRL_PHASE10_INPUT_218_V1` for both
`historical-input` and `historical-count`. Add `tick_size` as a positive
decimal string and `same_time_open_order` as `decision_before_open` when
the review supports that ordering, or `unresolved` otherwise. The
latter skips an entry when the decision and first scheduled H1 open share
a timestamp. A declared liquidation timestamp must match a development
H1 opening. The default is the last scheduled development H1 opening.

The counter uses the full reviewed development window, all five frozen
strategies and both frozen cost profiles. It derives H4 and D1 from the
verified H1 children and publishes each bar after the finalization delay
and the last child receipt. Equal-time D1 publications precede H4. A gap
leaves the corresponding parent unavailable. H1 opening evidence uses the
completed hour after its receipt and the same finalization delay.

Warmup publications build indicators, line state and group consumption.
The scheduled denominators, setup counts and entry attempts use the H4
window's partition. A warmup H4 still stays out of the totals when its
receipt reaches the development boundary. Development month totals use
the UTC setup receipt and the scheduled denominator uses the due time.

The report includes the input receipt, implementation hashes, diagnostics
and entry-eligible opportunity counts by strategy and cost. Each cell
applies the frozen 60-opportunity threshold. The counter evaluates entry
price eligibility before account occupancy or outcomes. It leaves the
DLY decision pending for development evidence. [Counting rule](PROTOCOL.md#c6-signal-counting)

## Verification and remaining work

The fabricated command test ran all ten strategy and cost combinations
with 390 warmup H4 and 253 warmup D1 bars. A BRK3 line formed during
warmup produced one eligible opportunity under each cost profile during
development. Reclassifying that trigger as warmup suppressed its setup
and entry counts. The unresolved-order case skipped the same-time entry.
The test blocked account and exit evaluation paths. All 220 targeted tests
passed. The end-to-end replay took several minutes on the test machine.
A full 24-month development replay with realistic bar coverage remains
unverified.

In a separate profiled 49-H4-bar fabricated run, pivot source-binding
checks accounted for 11.1 seconds of the 16.0-second runtime, including
their file reads and hashing. Profile the full-scope fabricated replay
before making performance changes.

The canonical metadata status reflects the Level B runner and remains
`UNAVAILABLE` with null actual counts. Independent source qualification
still needs the opening price, spread and availability evidence. Historical
Level Q remains outside the implemented runner. [Opening alignment](RESULTS-213.md)
