# Offline paired replay133 results

Completed 23 October 2026. The saved132 files now have a tested offline pull
cursor and a read-only JSON/Markdown CLI. This completes transport replay
integration; it does not establish a profitable strategy or admit these files
to financial simulation.

| Separate capture | Paired packets | Repeated adjacent snapshots | Quote receipt gaps over 2s |
| --- | ---: | ---: | --- |
| 20 October | 3,496 | 496 | None |
| 23 October | 3,483 | 1,047 | 4.919093s and 6.497732s |

All 6,979 packets preserve their original clock-before, quote and clock-after
rows, native numeric bits, raw flags and recorder sequence. Repeated snapshots
remain separate observations. No source reversals occurred in these two runs.
The gaps are recorder sampling pauses; they are not proof of missing market
ticks or measured network latency. The runs are never joined into two hours.
Their final after-guard offsets are 3,599.608010s and 3,599.044037s. Both retain
their original stop13 status; neither contains an unfinished final poll.

The cursor uses each completed poll's after-clock guard marker relative to
that run's origin. This is an as-recorded replay clock, not a certified UTC,
delivery or availability timestamp. Write/flush/transport delay after that
marker is unknown. Complete-file structural validation precedes delivery;
packet content and identities depend only on the validated prefix through
that poll. Changing a later valid quote or footer does not change earlier
packets. Quotes are not sorted by source labels, interpolated or resampled.

Peek returns an independent copy. Ack accepts the next exact JSON packet;
an immediate repeat of the last committed ack is a no-op. Changed, skipped or
older acknowledgments are rejected. Checkpoints bind the exact input bytes,
cursor, committed packet chain and relevant reader/runtime source files.
An unacknowledged packet is redelivered after restore. Checksums detect
inconsistency, not malicious authorship. External exactly-once effects still
require an idempotent consumer or an atomic joint consumer/cursor checkpoint.
This module performs no external effects. Final incomplete polls are excluded
from packet delivery and explicitly counted as quarantined in the final audit.

Verification: **70 Python tests passed**, including 14 new replay tests plus
the frozen132 reader and existing risk/metric/simulation tests. Invented wire
fixtures cover prefix causality, exact timing, repeats, reversals, incomplete
polls, corrupt inputs, strict manifests, checkpoint rejection and recovery.
An explicit test-only invented UTC embedding exercises the unchanged cost and
risk engine for long/short gap stops, target overshoots, the single-position
limit, cost-aware sizing, daily loss latching, duplicate delivery and restart.
The gap cases lose more than estimated stop risk; a stop is not a guaranteed
maximum loss. These invented outcomes are not market returns or strategy tests.

The actual-file CLI JSON/Markdown match the library; repeated JSON output is
identical. A separate reference walk compares all packet rows with the sealed
132 inspection and original wire prefixes, recomputes causal hashes and gaps,
and checks midpoint recovery against uninterrupted replay. All 615 old source/
config/test hashes and 68 native input hashes remain unchanged. Four new files
bring the source/config/test inventory to 619. This is a local consistency
check; it is not an independent feed or producer-authentication check.

Use [the replay instructions](PAIRED-REPLAY-133-USAGE.md),
[separate-run audit](../reports/paired-replay-133-summary.md),
[test evidence](../reports/paired-replay-133-tests-001.json) and
[reference review](../reports/paired-replay-133-reference-review.json).

The financial-engine bridge rejects these captures: verified absolute time,
source age, executable freshness, complete delivery/costs and sufficient
strategy warm-up remain unresolved. No historical clock correction or account
metadata was transferred onto them. No P&L, strategy ranking or profitability
claim is produced. There was no SDK connection, native launch/build/deployment,
settings change, support contact or automated order. All market/paper/order/
real-money admission remains false. October stays quarantined, November–
December reserved and untouched, 2025 consumed, and closed routes remain closed.

Next is a concrete eligibility check for a longer forward research input:
identify how source time, receipt time, calendar, quote age and costs can be
measured or explicitly bounded, and set sufficient strategy warm-up and
untouched validation length before more collection. The two short runs remain
useful transport fixtures. No further MT5 action is needed for this replay.
