# Sprint 216 · Reviewed historical input

Sprint 217 adds the calendar file and documents the current manifest format.
[Historical session coverage](RESULTS-217.md)

19 November 2026. Phase 10 now has a reader for independently reviewed
EURUSD Level B H1 bid bars. The repository starts with zero approved
manifest hashes. The acceptance path was verified with fabricated prices
and a test-only hash. This sprint opened no historical prices and computed
no strategy counts. [Development preflight](RESULTS-215.md)

## Input and verification order

The manifest takes exactly these fields. Specify `TRL_PHASE10_INPUT_216_V1`
for `schema`, `trendline_development_level_b_manifest` for `kind`, and
`EURUSD` and `development` for `symbol` and `partition`. Use distinct
bundle-relative paths for `plan_file` and `price_file`. Provide the exact
plan file digest as `plan_file_sha256`.

1. Match the manifest's SHA-256 against the repository's reviewed hashes
   before decoding it or opening either file named by it. The review has
   to cover source use, price and spread semantics, availability, calendar
   and coverage evidence for the actual development scope.
2. Check the exact plan file hash and run the existing development
   preflight before opening the price file. Consumed, quarantined and
   protected dates and overlaps with a reserved validation period remain
   excluded. An unassigned validation period is allowed.
3. Match the price file's raw SHA-256 to the plan's `input_sha256` before
   parsing. Use a JSON array of H1 observations with `start`, `end` and
   `available_at` in UTC epoch milliseconds, and `open`, `high`, `low`,
   `close` and `spread_pips` as decimal strings. The declared Level B
   spread assumption applies.
4. Return separate typed warmup and development rows. Reject bars outside
   the declared intervals, overlapping bars, rows received out of order
   and bars crossing the interval boundary. Require the declared H1 warmup
   quantity to be available at development start and require development
   rows to be present.

The command writes a new receipt with the manifest, plan, input and
calendar hashes, H1 row totals and `actual_counts: null`. The importable
reader returns the typed rows to a caller for subsequent processing.

```sh
PYTHONPATH=src python3 tools/signal_count.py historical-input MANIFEST NEW-RECEIPT.json
```

## Phase 10 status

The reader checks the date bounds and H1 row quantity. The count still needs
a historical session calendar adapter to verify scheduled H1 coverage and
complete H4/D1 bars, and a connection to the development-only signal counter.
Independent source qualification also remains open, including the opening
price, spread and timing assumptions. The proposed 2020 warmup and
2021–2022 development dates remain candidates. The canonical metadata-only
status matches the Sprint 215 output byte for byte and reports
`UNAVAILABLE`. [Candidate dates](RESULTS-199.md) · [Opening alignment](RESULTS-213.md)

All 100 targeted tests passed, including 84 reader, status, study and
data tests and 16 counter and coverage regression tests.
