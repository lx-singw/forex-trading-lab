# Native timing observation130 — 15 October 2026

The manual run produced a valid bounded stopped prefix: **58 completed polls**,
58 quotes and 116 clock groups, with all 174 attempted diagnostic groups
recorded. The final stop code is **13, elapsed limit**. There is no pending
attempt or truncated tail. The last recorded guard marker is 59.247604 seconds
after the program's monotonic origin. The stop frame does not contain its own
receipt marker, so an exact stop-time overshoot is not measured here.

The roughly one-minute limit allows fewer than the maximum 60 polls because
guard/read/storage work and waits take time. Actual first-clock read starts
were 1.000915–1.134591 seconds apart, satisfying the one-second minimum without
catch-up. The recorded nominal computer-GMT origin is 2026-10-15 03:21:19; this
label is not independently certified UTC.

## Measured quote behavior

| Observation | Recorded result |
|---|---:|
| Quote snapshots | 58 |
| Distinct source-millisecond labels | 47 |
| Adjacent source-label advances | 46 |
| Source-label reversals | 0 |
| Adjacent identical full native snapshots | 11 of 57 comparisons |
| Same-time changed native snapshots | 0 |
| Longest observed identical-snapshot span | 5.212442 seconds |
| Bid range | 1.12236–1.12244 |
| Ask range | 1.12236–1.12244 |
| Raw flag values, preserved without reinterpretation | 1026, 1028, 1030 |

The quote changed repeatedly during this sample. A wholly frozen quote does
not explain this run. Repeats alone do not distinguish normal lack of updates,
feed delay or missed intermediate ticks. The observed repeat span measures
receipt-to-receipt repetition; it is not quote age or a delivery guarantee.

## Raw clock comparisons

Across 116 clock groups, TimeTradeServer minus TimeGMT stayed at +10,800 seconds
and TimeLocal minus TimeGMT at +7,200 seconds. TimeCurrent minus TimeGMT was
+10,800 or +10,801 seconds. Raw GMT offset was −7,200 seconds and DST zero.
The six raw fields had no numeric reversals; TimeCurrent advanced in 55 adjacent
clock-group comparisons, while TimeTradeServer, TimeGMT and TimeLocal advanced
in 57 each.

For the 58 completed polls, source milliseconds minus surrounding TimeCurrent
seconds ranged from −4,463 to +946 milliseconds, and minus surrounding
TimeTradeServer seconds from −4,463 to +1,157 milliseconds. These are sequential
raw-clock arithmetic, not certified age bounds. In particular, positive values
can arise from clock precision, estimates and sequential reads. The three-hour
numerical difference is consistent with distinct clock time bases, but this
short observation establishes no UTC mapping or historical timezone rule.

[TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent) describes the
latest quote time for a selected Market Watch symbol. It need not refer to
EURUSD. [TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver)
is a client-calculated server-time estimate affected by computer settings.
[TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt) uses the computer's
local time and daylight-saving settings. These definitions limit the inference
that can be made from the numerical comparisons.

## Preservation and verification

Exactly one owned native file was found: 50,456 bytes. It was read with an
exclusive read handle and copied without overwrite to the canonical
[Timing130.txt](../data/timing-probe-130-native/Run130-1792034479-1253652843-8665/Timing130.txt).
Its SHA256 is dd65884130636d9670d771ad5138aba00d3d05571ff8989c9993c0e52537441b.
The original was not modified. The four deployed artifact hashes still match.
No native log, account setting or unrelated export was read.

The frozen offline library and CLI give identical results. A separate raw
frame walk verifies all 350 frames and chained digests, 174 sequences/outcomes,
all 58 paired calculations, native double values, quote-change/repeat counts
and poll spacing. See [inspection](../reports/timing-probe-130-capture-inspection.json),
[summary](../reports/timing-probe-130-capture-summary.json),
[independent review](../reports/timing-probe-130-capture-independent-review.json)
and [native copy record](../reports/timing-probe-130-native-copy.json).

All 604 source/config/test files and all 64 earlier native input hashes are
unchanged. Preparation's 43 Python tests and 554 C++ checks remain retained;
they were not rerun because no code changed. No compiler/deployment, SDK
connection, support contact, native script launch by the assistant or terminal
setting change occurred during inspection. The user launched this observation.
The file's digest chain detects changes but does not authenticate its producer.

## Implication and next work

This establishes successful bounded recording and changing reported demo
quotes during this sample. It leaves executable freshness, complete tick
delivery, source/receipt UTC certification, complete costs, market-data
qualification, strategy performance and profitability unresolved. There was no
strategy replay or profit/loss calculation. Paper/order/real-money availability
remains false. All strategies, risk/cost rules and ensemble weights are fixed;
October2026 stays quarantined, November–December2026 untouched/reserved and2025
consumed. Historical/provider/H.10/native090 routes stay closed.

Next engineering work: carry the paired-clock and repeat observations into the
forward recorder's explicit quality report, test that integration offline,
then prepare a longer fixed read-only observation. Any eventual strategy
comparison still needs adequate chronological data, warm-up, complete cost
assumptions and untouched validation. No repeat launch is needed for this run.
