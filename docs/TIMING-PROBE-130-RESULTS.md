# Timing diagnostic130 preparation results — 15 October 2026

The fresh default-off read-only EURUSD quote/clock diagnostic is implemented,
tested, compiled and deployed. **Native execution and actual timing results
are pending one manual launch.** No market performance is claimed.

The focused verification passes 43 Python tests: 24 new timing tests and 19
retained metadata127 tests covering the shared canonical integer/native-bit
reader. The exact new pure MQL decision header also passes 506 C++ schedule and
clock checks. The unchanged actual account/quote guard passes 48 retained C++
checks. Both C++ builds use C++17, Wall/Wextra/Werror. No failures or skipped
tests occurred. See [verification](../reports/timing-probe-130-verification-001.json)
and [the source freeze](../reports/timing-probe-130-development-source-001.json).

Invented fixtures cover changing quotes, repeats with advancing clocks, raw
server-domain changes/reversals, source-label reversals, same-time changed
snapshots, unknown flags, negative-zero bits, invalid quotes, spacing/no-catchup,
date/drift/deadline faults, every pending-attempt stop, unfinished pairs,
partial framing, malformed/rehashed sequences and CLI read-only behavior.
Default-off and fresh-file collision refusal are checked by source inspection;
they are not claims of a completed native filesystem/runtime trial.

The installed compiler is file version 5.0.0.6259, with the same hash as128's
recorded compiler. One compile produced a new 21,252-byte EX5, zero errors and
zero warnings. MetaEditor returned exit code **1**, retained honestly alongside
its successful diagnostics and fresh artifact hash. Four files were copied to
the new **ForexDemoLab130-0b357a86f0e4** folder; no other terminal settings or
scripts were changed. See [compilation](../reports/timing-probe-130-compilation-001.json)
and [deployment](../reports/timing-probe-130-deployment.json).

The envelope is nominal computer GMT 15 October 2026, up to 60 polls/180
diagnostic groups, minimum one-second first-clock spacing, one file/128 KiB,
and a 60-second elapsed cap checked on returns. A stopped valid prefix can have
fewer polls. Sequential read/guard boundaries and all raw clock values remain
visible. No UTC correction, source-age estimate, historical timezone rule,
executable-price certification or tick-delivery completeness is inferred.

All 597 old source/config/test hashes and 64 native input hashes remain
unchanged; seven new files make 604. Prior handoff bodies are preserved in
[the reservation](../reports/timing-probe-130-reservation.json) and its backup
folder. No old capture was converted, joined or replayed. Financial strategies,
costs, risk rules and ensemble weights remain fixed. October2026 is quarantined,
November–December2026 remain untouched/reserved and2025 is consumed. Historical,
provider, H.10 and native090 routes stay closed.

No terminal launch, native collection, SDK connection, support contact or order
was performed during preparation. Automated/real-money orders remain
unavailable. Next: [one manual launch](TIMING-PROBE-130-USAGE.md), then preserve
and inspect the resulting closed file before interpreting actual timing data.
