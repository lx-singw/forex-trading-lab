# Sprint 163 — Phase 2 invented data boundary

16 November 2026 (Africa/Johannesburg). **93 tests pass together:34 new,59
existing**, zero failures/errors. Six invented exercises pass. Phase2 engineering
is in progress; actual market-source acceptance remains unavailable. Sprint162
was committed/pushed as cdcdb69 before this sprint began.

## Implemented

New trendline/data.py and its module CLI provide strict invented B descriptors,
bounded decimal H1 records, file-byte bindings, explicit validation unlock records,
causal H1/H4/D1 publication and coverage diagnostics. See
[usage](DATA-163-USAGE.md) and [verification summary](verification-163.json).

The component imports unchanged146 calendars/observations and the existing Bar
contract through their current interfaces. Full-day output matches existing
aggregation; a separate hand calculation reconciles H4 OHLC. Explicit23/25-hour,
partial and closed sessions retain their declared boundaries. Missing children
block parents, and late data publish only when available. Valid future suffix
changes preserve earlier published geometry and lineage. Full-file hashes bind
the report separately from causal-prefix identities.

Source-kind/level/geometry/spread labels are mandatory. Mid-only observations
never supply invented executable sides. Duplicate/out-of-order/invalid observations
reject without mutating the accepted stream. Validation unlock is checked before
opening the hourly file, binds its descriptor/hash/scope and cannot admit a market
kind. The receipt is an explicit audit marker, not authentication or data permission.
Outputs are exclusive; duplicate JSON, nonfinite values and symlink paths reject.

The metadata-only config/trendline-data-163.json assigns no source/date/geometry.
Even fully populated claims remain UNAVAILABLE pending independent qualification
and a market reader. All28 new comparison cells retain null returns. Protected
dates are checked for warmup and funded scopes; existing16 cells stay unchanged.
This lint is not the complete study145-equivalent preflight.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_data_163 test_elliott_sessions_146 test_elliott_study_145 -v
```

All93 tests pass in1.783seconds on the recorded run. New tests cover schema/price
rejection, aggregation parity and hand OHLC, variable/partial sessions, missing/
late/future input, defensive copies, source binding changes, file/unlock ordering,
typed receipt equality, exclusive outputs, metadata refusal and public CLI paths.
The full unrelated trading suite was not rerun; frozen strategy/accounting source
was not edited. Phase1's80 fixture records remain unchanged from162.

| Invented exercise | H1 | H4 | D1 | Finding |
| --- | ---: | ---: | ---: | --- |
| Clean24-hour session | 24 | 6 | 1 | Complete declared coverage |
| 23/25-hour sessions and48-hour closure | 48 | 13 | 2 | Short terminal H4 buckets retained |
| One missing child | 23 | 5 | 0 | One H1/H4/D1 gap, no fill |
| Late missing child | 24 | 6 | 1 | Restored coverage at later receipt |
| Supplied mid candles only | 24 | 6 | 1 | Geometry only; execution-side data unavailable |
| Explicitly unlocked invented validation | 24 | 6 | 1 | Bound receipt required before price-file open |

Generated files/test log are in ignored reports/trendline-163/. Portable counts
and source hashes are in verification-163.json. No actual market file, account,
terminal, helper, native API, credential or quote endpoint was accessed.

## Source finding and remaining work

Two additional primary-documentation searches and one provider help-page open
found Twelve Data's [composite-feed description](https://support.twelvedata.com/en/articles/12528665-how-the-composite-currency-feed-works).
It describes weighted source midpoints. This supports investigating composite
geometry, not assuming historical broker bid candles/spreads. It does not by
itself establish the exact returned H1 history's basis, coverage, licensing or
spread semantics; no series/API request or signup occurred. Previous source-use
and prior-exposure limitations remain in force.

Next Phase2 slice: the invented B entry/exit-price model using the first scheduled
H1 open after an available decision, post-fill bid/ask-side stops/targets and
adverse unresolved intrabar outcomes. A permitted real source with declared
calendar/coverage/price/spread/use evidence remains separately required for phase
completion. Do not mark Phase2 accepted or start a market study from these fixtures.
No order, real-money mode, native grant renewal or protected-data access is added.
