# Source-hour collection protocol 033

Implements the unchanged FRESH-CONTEXT-033-PLAN.md as a separate diagnostic.
No strategy replay or parameter selection is included. Eligibility remains false.

Run the complete regression with scripts/test-fresh-context-033.py, then freeze
with scripts/fresh-context-033.py freeze. The ledger binds the new source,
scripts, tests and documents, all 032 originals/checks/ledger/final snapshot,
and the three previously pinned Windows runtime files. Verify the entire 032
snapshot, including external inputs, before freezing. No SDK reads precede it.

Run scripts/fresh-context-033.py run once in the pinned Windows Python runtime.
Require the already-running exact installed terminal; initialization connects
only after checking process presence. Do not launch, log in, select a symbol,
change settings or deploy an EA. Reserve a new exclusive output folder before
connection. Actual DEMO/USD and disabled terminal Algo Trading are required.
Private account/server identity stays in memory and must remain unchanged.

The sequential native reads are exactly one EURUSD horizon quote, one inclusive
COPY_TICKS_ALL request for raw labels 1791291600000..1791295200000, then one H1
bar request for raw seconds 1791291600..1791295199. Dates are merely UTC API
formatters for numeric source labels; their UTC meaning is not certified.
Require the horizon strictly beyond the upper label and within 24 hours of
the current receipt. Date 2026-10-06 is checked around every read and completion.
Clock reversal, actual account/identity/Algo changes and SDK failures stop later
reads. No retry or alternate interval. Preserve a sealed no-call failure if
preflight fails. Never export private identifiers or SDK exception text.

Keep all eight numeric fields of each bounded tick and bar response in original
order, in native binary plus lossless numeric CSV. Reject unknown/object fields,
overlapping/unsupported layout and nonzero padding. Preserve bounded invalid or
empty originals with a failure; do not repair or truncate. Oversize responses
record safe row/byte/schema/hash evidence and export no prefix. Budgets are
100,000 ticks, 10 bars and 32 MiB combined originals, with 64 KiB reserved for
metadata. Soft elapsed limits are 60 seconds per native history read and 120
seconds combined. Native SDK allocation and cancellation cannot be bounded by
Python before return. A timeout preserves guarded bounded originals and stops
later requests. Ordinary filesystem work is excluded from native elapsed time.

Wait for the collector process to exit and capture.sha256 to exist before
running scripts/check-fresh-context-033.py. This independent stdlib checker
reconstructs each binary field and CSV value, hashes, counts, sizes, order,
ties, duplicates and audits. It decodes all 196 frozen 032 complete records;
each witness gets every matching 033 original row index. Ambiguity is reported,
never silently resolved. Reconstruct bid OHLC and event count only over the
half-open hour, with exact upper-boundary rows separately identified. Compare
all four bar prices and tick_volume, reporting every difference. Preserve all
bar fields including spread/real_volume as observations, not inferred costs.

25 new tests cover guarded sequencing, requests, dates, horizon, size/schema,
timeouts, immutable outputs, complete field fidelity and checker mutations,
ambiguous complete-record matches and explicit boundary exclusions. Full
regression must pass before freeze. Post-capture reports/review and a new source
snapshot bind originals and handoff changes; no frozen collector edits occur
after acquisition. Checker integrity and diagnostic agreement are separate:
mismatches are retained rather than changing rules to force a pass.

Same-feed relative agreement cannot prove independent-provider completeness,
historical UTC/session labels, historical executable costs or profitability.
Fresh/annual eligibility remains false. No orders, real-money toggle, accounts,
contacts, paid services, provider retries, consumed 2025 or reserved Nov–Dec 2026.
