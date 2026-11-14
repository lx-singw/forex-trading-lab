# Paired capture replay133 plan

Reserved 23 October 2026. See the sealed reservation and the four prior handoff
bodies under reports/paired-replay-133. The existing 615 source/config/test and
68 native input hashes must remain unchanged.

Implement an offline pull cursor over each frozen132 file separately. Deliver
only complete clock-before/quote/clock-after polls, in recorder sequence. Keep
native bits, raw clocks, repeated observations, source reversals and actual
monotonic gaps. Use the after-clock guard marker as the as-recorded replay
clock; it is not a certified delivery time, UTC or quote age. No resampling,
clock correction, merging, interpolation or market admission.

Use causal prefix identities so future frames cannot change earlier packets.
Peek/ack must reject mutation and skipped acknowledgments; committed cursor
checkpoints must bind the exact input, rules and runtime. Recovery redelivers
an uncommitted packet. External exactly-once effects are not promised: a
consumer needs idempotent event IDs or an atomic joint state/cursor commit.
Incomplete final polls remain quarantined, with explicit status and counts.

Pin the two duration-limit captures individually in a strict bounded manifest.
Expose a read-only CLI with separate JSON/Markdown run audits. No broker, SDK,
network, account, native launch or order interface. The financial-engine bridge
remains unavailable because absolute UTC, source age, executable freshness,
complete costs and sufficient strategy warm-up are unverified.

Before inspecting the real captures with the new code, test invented wire
fixtures for causality, timing/gaps, repeats, corruption, prefix quarantine,
cursor recovery and strict manifest/checkpoint rejection. In tests only, use
explicit invented UTC embedding to exercise unchanged cost/risk engines:
position limits, cost-aware sizing, gap stops beyond estimated risk, target
fills, duplicate ticks, daily loss latching and joint restart equivalence.
No invented financial results will be attributed to native data.

Freeze new source before tests; retain any failed revision and rerun only after
necessary fixes. Compare real-run replay counts and gaps independently with
the frozen132 inspection, verify repeatability and checkpoint recovery, recheck
all old source/native hashes, and seal results and handoff evidence. Keep old
handoff bodies intact. October remains quarantined; November–December reserved;
2025 consumed; closed historical/provider/H.10/native090 routes stay closed.
