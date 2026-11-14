# Clock diagnosis 012 results — 2026-10-01

All eleven guarded anchor captures and eight full March/October audits completed.
No jobs remain active. The initial hypothesis, event screen and source were
frozen before these statistics in `clock-012-ledger.json`.

The sequence hypothesis preserved 23,711,389 quotes and produced monotonic
candidate timestamps, but its physical interpretation failed. Moving the clock
at the late-Sunday archive discontinuity assigns quotes to incorrect hours.
Monotonic timestamps alone do not establish correct time. The failed candidate
and all comparisons remain preserved.

A separate ordered-content check found each October's repeated source 19:00
hour is an exact replay: every timestamp, bid, ask and volume matches the first
copy in order. Replayed rows: 2020=3,800; 2021=1,695; 2022=4,625; 2023=2,559;
total **12,679**. `clock-012-repeat-content.json` records hashes and original
ranges. Canonical archives retain both copies. This motivated separately
declared correction 013; the original hypothesis was not rewritten.

The unchanged eleven release screens failed their all-required gate:
HistData 7/11, broker 2/11, both 1/11 (2023-11-03). Each event needed at least
three times both control ranges and twice both control quote counts. Several
failures concern counts despite large price activity; failure of this heuristic
does not alone establish a wrong timestamp. July 2023 also has missing coverage.
Thresholds and dates remain fixed. See `clock-012-anchors.json` and the official
[BLS release archive](https://www.bls.gov/bls/news-release/empsit.htm).

Nine software tests were added for exact boundaries, invalid input, repeated
events and checkpoint restoration; 201 tests passed at this stage. Tests verify
software behavior, not the clock hypothesis or market completeness. No eligible
normalized dataset, returns, source blending or execution followed.

Public probe 011 acquired zero bytes: WSL transport error, then separately
declared Windows follow-up HTTP429. Requests stopped. See `CLOCK-011-RESULTS.md`.
No paid source or access workaround. Next: `CORRECTION-013-RESULTS.md`.
