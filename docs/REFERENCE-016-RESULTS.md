# Independent reference diagnostics 016/016B — 2026-10-06

Nine original Forexite daily archives downloaded successfully. The separate
check recomputed all 11,153 EURUSD minute rows and every saved hourly aggregate,
216 UTC-day comparisons, six fixed clock screens and three gap probes. A
diagnostic CSV additionally preserves each original date/time and source row;
an independent comparison checked every saved field against the original ZIPs.
254 software tests pass, including 15 new reference/boundary tests.

The reference contains 60 minute rows at both 2023-03-26 UTC23 and
2023-07-14 UTC20, where the 015 candidate has no quotes. July 14 UTC19 has
60 reference rows and 3,321 candidate ticks; their close distance is 0.9 pip.
On July 7, reference rows also exist in all six candidate-empty UTC hours
10, 13, 16, 18, 19 and 20. On July 14 those hours are 10, 12, 14, 16, 18 and 20.
These are selected-file observations under the declared clock conventions,
not a count of missing trading hours throughout the year. Reference presence
does not establish HistData's own historical operating schedule. Missing
reference rows would not prove closure either.

## Fixed clock screen

Compare literal reference labels with candidate hourly bid closes in UTC06–17.
The declared screen requires all 36 aligned/control pairs, aligned median
<=2 pips, >=10/12 aligned distances <=2 pips, and a strictly smaller aligned
median than both one-hour shifts. No threshold or date was changed.

| Day | Aligned median, pips | Earlier-hour median | Later-hour median | Aligned pairs <=2 pips | Screen |
| --- | ---: | ---: | ---: | ---: | --- |
| 2022-01-07 | 1.25 | 4.05 | 5.55 | 7/12 | Fail |
| 2022-07-08 | 1.30 | 6.50 | 7.55 | 9/12 | Fail |
| 2022-11-04 | 1.25 | 15.25 | 19.75 | 7/12 | Fail |
| 2023-01-06 | 1.25 | 11.80 | 11.90 | 9/12 | Fail |
| 2023-07-07 | Unavailable | Unavailable | Unavailable | 7/12 | Missing pairs |
| 2023-11-03 | 1.65 | 4.75 | 4.70 | 8/12 | Fail |

The five complete days support the proposed hour alignment relative to the
one-hour alternatives, but fail the fixed price-distance screen. July 7 lacks
candidate UTC10/13/16 within the fixed window and additional required controls.
The overall screen is failed. This neither certifies annual UTC nor establishes
that the candidate clock is wrong: feed differences, precision and minute-bar
label conventions remain unresolved. Do not select a new minute shift after
seeing this result or weaken the failed 012 activity screen.

## Format evidence and limits

[Forexite's original history documentation](https://www.forexite.com/free_forex_quotes/forex_history.html)
describes MetaStock minute files in CET in winter and CEST in summer; its
ProSuite format instead uses GMT. We used the original index-listed MetaStock
ZIPs and a bound Europe/Berlin conversion, independently checked with manual
last-Sunday arithmetic. This distinguishes formats; no broker-location claim
follows. [Forex Tester's Basic redistribution](https://desktop.forextester.com/data/datasources)
describes Bid prices and GMT without DST, but that distribution was not acquired.
Its clock was not assigned to Forexite's original MetaStock files.

The reviewed primary pages do not establish original MetaStock bid semantics
or whether minute labels mark bar start or end. Keep comparisons provisional.
Different publishers do not prove independent upstream lineage. Minute OHLC
provides no original ask quotes, spread history or intraminute execution path.
It cannot replace bid/ask ticks or be inserted into the 015 source.

[HistData's FAQ](https://www.histdata.com/f-a-q/) and
[file specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/)
publish fixed EST without DST and warn that gaps can include normal pauses.
Those reviewed pages supply no source-specific historical 2020–2023
session/holiday calendar. Their clock statement does not resolve the observed
October replay and other chronology evidence. No generic calendar or another
broker's hours were used to approve HistData closures.

## Preserved initial failure and corrected boundary handling

The frozen 016 parser rejected a following-day midnight label in the March 26
file. No review was published. Its ledger, source ZIP and failure report remain
intact. A bounded schema inspection recorded one following-day 00:00 label in
each March file. The separately declared 016B adapter permits only that exact
boundary, preserves original labels/row numbers, and retains all other date,
order and price rejection rules. Its comparisons and thresholds are identical.
The independent checker accepts this boundary using the literal original date,
without importing the adapter. No new archive requests followed.

## Verification and artifacts

- `REFERENCE-016-PLAN.md` and `REFERENCE-016B-PLAN.md`: frozen scope and correction.
- `reference.py` / `reference_boundary.py`: parser, format clock and fixed screens.
- `scripts/reference-016b.py`: freeze/verify/run; old 016 code stays unchanged.
- `scripts/check-reference-016b.py`: independent ZIP/calendar/price recomputation.
- `scripts/export-reference-016-lineage.py`: diagnostic CSV and independent lineage.
- `data/reference-016`: nine original ZIPs, outcomes, source HTML, boundary schema
  evidence and explicitly diagnostic minute-lineage CSV/provenance.
- `reports/reference-016-attempt.json`: preserved failed first run.
- `reports/reference-016b-ledger.json`, seal and source ZIP: frozen corrected run.
- `reports/reference-016b-review.json` and `reference-016b-independent.json`:
  every observed/missing hour, price/control distance and independent checks.
- `reports/reference-016-source-review.json`: primary-source evidence and limits.
- `reports/reference-016-market-gate.json`, preservation and checks:
  actual pre-performance rejection, previous bindings and final verification.
- `reports/reference-016-final-source.json/.zip`: completed source/evidence snapshot.

Before reuse, verify both old 013/015 preflights, then `reference-016.py verify`
and `reference-016b.py verify`. Completed run/check/export outputs use exclusive
creation; do not rerun them over their existing results or re-download archives.
Original 008/010/013/014/015 reports and all 144 monthly 015 metadata bindings
remain unchanged. The normalizer's source archives retain their original hashes.

## Decision and next work

Annual data approval remains blocked. The actual 014 market review gate rejects
this minute diagnostic before performance. No new returns or profitable edge
are established; historical costs remain unverified. Orders remain unavailable.
No broker calls, terminal changes, deployment, source blending or paid services.
2025 stays excluded; reserved November–December 2026 data stays untouched.

Next declare a bounded diagnosis of the original minute-label convention, then
plan acquisition/review of complete bid/ask history for affected 2023 windows.
A separate replacement source must satisfy its own chronology, completeness,
cost and lineage review. Keep existing strategy/cost/selection rules fixed and
all current failed gates intact. No further returns are justified yet.
