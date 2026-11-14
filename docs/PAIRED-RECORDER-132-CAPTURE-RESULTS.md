# Paired recorder132 native results — inspected 20 October 2026

The run produced a valid **38 minutes 59.697095 seconds** of recorded paired
evidence before stopping at the connection guard: **code3, terminal reported
disconnected**. It did not reach the one-hour elapsed limit. The underlying
reason for the connection loss cannot be determined from this export.

There are **2,248 completed polls**,2,248 quotes,4,496 clock groups and6,744
recorded diagnostic attempts/outcomes. The stop is between fully completed
polls, with no pending read, unfinished pair or truncated tail. This validates
the recorded stopped prefix, not a completed one-hour capture.

The nominal computer-GMT origin is2026-10-19 18:40:12. The last recorded marker
is2,339.697095 seconds after the program's monotonic origin. The stop frame has
no receipt marker, so the exact later disconnect/stop time is not measured.
Neither the computer label nor the source labels are independently certified
UTC. The user launched this run; inspection did not start a native program.

## Quote and timing observations

| Observation | Result |
|---|---:|
| Recorded quote snapshots | 2,248 |
| Distinct source-millisecond labels | 1,307 |
| Adjacent source-label advances | 1,306 |
| Adjacent source-label reversals / below-prior-high-water labels | 0 / 0 |
| Identical full native snapshots | 941 of2,247 adjacent comparisons |
| Same-time changed native snapshots | 0 |
| Longest observed identical-snapshot span | 23.984088 seconds |
| Quote-receipt gaps greater than two seconds | 0 |
| Raw quote flag values | 1026,1028,1030 |

Quotes changed throughout this sample. Repeats measure identical received
snapshots over receipt-to-receipt time; they do not distinguish normal absence
of updates, delayed delivery or missed intermediate ticks. The repeat span is
not certified quote age or an executable-price guarantee. No strategy or P&L
was evaluated, and differing windows/sampling prevent inferring improvement
from comparisons with earlier captures.

Actual first-clock read starts are1.000129–1.292002 seconds apart, satisfying
the one-second minimum. Quote-read starts are0.996721–1.292339 seconds apart.
The latter markers follow the first clock group and intervening guards, whose
duration varies; they are not the first-clock spacing governed by the limit.
The shared quality report retains the fixed two-second quote-receipt gap
notice and128-event detail cap. All941 quote events are counted; the first128
details are stored with explicit truncation.

## Raw clock comparisons

TimeTradeServer minus TimeGMT stays+10,800 seconds and TimeLocal minus TimeGMT
+7,200 seconds. TimeCurrent minus TimeGMT ranges+10,798 to+10,800 seconds with
305 adjacent changes. None of the six raw clock fields has a numeric reversal.

Across all2,248 completed pairs, source milliseconds minus surrounding
TimeCurrent seconds ranges−24,354 to+990ms; the corresponding subtraction of
TimeTradeServer seconds ranges−24,354 to+662ms. These are raw sequential clock
arithmetic, not certified quote-age bounds, historical timezone rules or an
offset correction. Earlier runs keep their original missing clock evidence;
no offsets, observations or account identities are transferred across runs.

## Preservation and verification

One closed owned native file of2,002,532 bytes was copied through an exclusive
read handle to a fresh canonical folder without overwrite. Its SHA256 is
108f7964ff7bd8ac23489f9b2bac7c5a8194fa5ab557c7c5cada8f0d7556af19.
The original is preserved and the four deployed artifact hashes still match.
No account setting, native log or unrelated export was read.

The frozen132 wire reader and shared131 numerical engine agree with JSON and
Markdown CLI results. A separate raw frame walk verifies all13,490 frames and
chained digests,6,744 sequences/outcomes,2,248 complete pair calculations,
native doubles, source-change/repeat counters, spacing and raw clock changes.
Integrity and declared market provenance do not authenticate a producer.

See [native file](../data/paired-recorder-132-native/Run132-1792435212-389088906-3851/Paired132.txt),
[quality report](../reports/paired-recorder-132-capture-quality.md),
[summary](../reports/paired-recorder-132-capture-summary.json),
[independent review](../reports/paired-recorder-132-capture-independent-review.json)
and [copy record](../reports/paired-recorder-132-native-copy.json).

All615 source/config/test files and65 earlier native input hashes are unchanged;
the new raw file makes66 retained native inputs. Preparation's73 Python and
119,449 C++ checks remain retained, not rerun because code did not change.
No MT5 compile/deployment/launch, SDK, support contact, account/terminal setting
change, strategy replay or financial/risk/cost/weight change occurred during
inspection. October stays quarantined; November–December reserved/untouched;
2025 consumed; closed historical/provider/H.10/native090 routes stay closed.
Source/receipt UTC, quote age, complete delivery/costs, executable quality and
profitability remain unverified. Market/paper/order/real-money availability is
false. The recorder has no order interface.

## Next step

The connection guard stopped recording as designed. The next collection task
is a fresh uninterrupted hour after MT5 is connected again, keeping Algo
Trading off and using the existing USD demo account/EURUSD chart. During the
remaining19–23 October window, use the same tested132 script once as described
in [the instructions](PAIRED-RECORDER-132-USAGE.md). Keep MT5 connected and the
computer awake, then report Done after it finishes. No date or code edit is
needed. A restart must create a new run/file; this39-minute prefix cannot be
resumed or joined to another run and called a continuous hour.
