# Forward capture112 — observed one-hour pilot

The user's native111 recorder run recorded **7,188 valid EURUSD snapshots across 60 files**
and reported stop code 13, the one-hour limit. It ended cleanly with no pending
attempt or truncated tail. This is a successful bounded collection pilot; the
format correctly reports `stopped`, rather than claiming all 7,200 completed.

The unchanged111 CLI and library agree on the entire copied run. All sequence,
cross-file header/hash links, clock consistency and global limits validate.
The 59 rotation files contain 120 observations each; the final file contains 108
and a stop record. No missing/invalid quotes, source reversals, equal-time changed
snapshots or receipt intervals over two seconds were recorded.

## Timing and continuity

| Measurement | Observed value |
|---|---:|
| Attempts / valid observations | 7,188 / 7,188 |
| Files / bytes | 60 / 2,253,627 |
| First read after origin | 1.974ms |
| Last successful guard after origin | 3,599.899897s |
| Minimum / median read interval | 500.052 / 500.149ms |
| 95th / 99th percentile interval | 500.310 / 501.466ms |
| Maximum read interval | 1,362.607ms |
| Median / maximum rotation interval | 500.184 / 500.493ms |
| Median / maximum quote call | 0.003 / 1.526ms |

Percentiles use nearest rank. All 7,187 intervals, including 59 file boundaries,
preserve the 500ms minimum. Their average is 500.890ms. Small delays accumulate,
so the time cap stopped this run 12 observations short of the attempt cap; no
samples were fabricated or acquired faster to catch up. Five-minute blocks contain
598–600 observations. Rotation preserved the global sequence and timing in this
run. This does not establish a hard Windows scheduling or power-loss guarantee.

The nominal computer-GMT start label was 2026-10-12T18:15:59. It is not certified
UTC. The last guard timestamp precedes the stop write/close; the stop record itself
has no elapsed timestamp. Therefore the recorded prefix and declared stop support
the bounded outcome, without independently proving the exact shutdown instant or
a hard latency limit on blocked native calls.

## What these snapshots can establish

There are 4,405 adjacent identical snapshots, or 61.29% of adjacent pairs, and 2,783
distinct source millisecond labels. The longest identical sequence lasts 50 reads,
spanning 24.516 seconds. These are repeated latest-quote polls, not a complete tick
stream. An unchanged quote can reflect inactivity or delayed delivery; this export
cannot distinguish those explanations or establish executable quote age.

Raw source labels minus nominal receipt seconds range from 10,775.162 to 10,800.735
seconds, median 10,799.371, still roughly three hours. No offset is applied and no
broker timezone, UTC alignment or freshness conclusion is drawn from that difference.

Observed spread is approximately 0–0.1 pip, median 0.1, with 2,836 equal bid/ask
snapshots and 4,352 positive spreads. The exact unrounded decimal-conversion maximum
is 0.100000000001 pip and is retained in the metrics report. One pip means 0.0001
EURUSD price units. This demo sample does not certify commission, slippage, financing
or executable costs; existing research cost assumptions stay unchanged.

Raw flags 1026/1028/1030 occur 2,124/3,841/1,223 times. They are retained without
masking unknown bits or assigning new semantics. No trades, returns, win rate,
strategy tuning or performance selection were evaluated. One hour also supplies
too little history for the existing 51-hour baseline warmup or 201-hour common
research warmup.

## Preservation and verification

Matching deployed script, two headers and EX5 were verified before copying.
All 60 source files were opened read-only with exclusive access, read within the
per-file/global byte limits, checked against a stable directory listing and copied
byte-for-byte into ignored local data under `data/forward-capture-112/`.
Every copied hash matches. CLI/library inspection and count/timing consistency
checks passed; inspection left the copied bytes unchanged. Exclusive readable files
alone do not prove completion—the validated stop marker establishes the outcome.

Evidence: `reports/forward-capture-112-copy.json`, `-inspection.json`, `-metrics.json`
and `-consistency.json`, with SHA256 sidecars and final source/evidence closure.
The shared final chain head is
FD66C292A9DA6DCA88214C352E4C6998FC49AA723309C16FADD5ED55B5AF0D43.
Hashes check consistency, not independent producer or account authentication.

All 524 retained implementation/config/test source hashes remain unchanged.
No new code or test suite was run; the prior 84 focused tests and older 2,095 active
suite tests retain their original results. Existing111 source/archive evidence and
four earlier handoff bodies are preserved. The user ran the collector; the agent
only copied and inspected its output. No SDK connection, agent script execution,
terminal launch/settings/log/account inspection, support contact or orders occurred.

Market qualification, source age, UTC, use-right certification and paper/order
admission remain unproved/false as applicable. Real-money execution remains
unavailable. Original historical gaps, provider stops, H.10/native090 closures,
strategy/cost rules and untouched validation reservations remain intact.

## Next concrete work

Build the offline paper-engine integration specified in
[SHADOW-ENGINE-113-PLAN.md](SHADOW-ENGINE-113-PLAN.md). Use invented quotes first,
reuse the fixed baseline and tested simulator, and test causality, costs and restart
behavior before admitting any market data. This observed run remains diagnostic
evidence. No further manual MT5 launch is required to complete this inspection.
