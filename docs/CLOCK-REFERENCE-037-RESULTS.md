# Current clock-reference diagnostic 037 results

Completed 2026-10-06. The single guarded demo quote's raw label is about three
hours ahead of the local clock and two usable public HTTP Date references.
This is observed disagreement, not a timezone diagnosis or UTC certification.
No original timestamp was changed and performance eligibility remains false.

522 synthetic tests passed (24 new; no failures, errors or skips), before any
external reads. The previous snapshot's 1,077 bindings, 1,032 archive members and
45 external inputs verified. 88 inputs were frozen. An exclusive sealed
reservation preceded the Windows service query, three sequential verified-TLS
HEAD requests and one existing-terminal connection/quote. The independent
checker reconstructed all intervals, budgets, quote validity and false gates.

| Target | Status | Accepted | Coarse reference minus local interval |
| --- | --- | --- | --- |
| time.gov | 200 | No: strict whitelisted-header validation failed | Not used |
| microsoft.com | 200 | Yes | −1.901 to +1.935 seconds |
| mql5.com | 200 | Yes | −1.641 to +2.099 seconds |

The Date headers of accepted responses were 15:05:25 and 15:05:28 GMT. Age was
absent in both; Microsoft's Cache-Control was absent, MQL5's was no-cache,no-store.
Neither absence nor these directives certify origin clock accuracy or freshness.
The rejected response remains recorded, without retries or inference about that
host's time accuracy. HEAD request durations were 4.259734, 2.836115 and 2.739166
seconds; the complete request span was 9.835607 seconds. All declared deadlines
passed. The accepted uncertainty widths, including one-second Date resolution
and receipt bounds, were 3.836 and 3.740 seconds.

Windows Time service existed but was not running. No service, clock or timezone
setting was changed. That status alone does not demonstrate synchronization or
identify the cause of the discrepancy. UTC and monotonic receipts had no detected
reversal/discontinuity and remained within the declared date.

After two hosts passed, the pinned SDK connected to the already-running exact
terminal. Actual DEMO/USD, Algo Trading off, connectivity and private stable
account/server identity passed before/after the quote and at completion. No
identity, raw exception text or private command output was exported. One EURUSD
quote was read; SDK last-error numeric code was 1. No history/order API was used.

The quote receipt was 2026-10-06 15:05:31.338 UTC, with 0.636 ms monotonic read
duration. Its raw time_msc was 1791309929268, which *formats* as 18:05:29.268
under UTC rendering; that formatting does not establish its actual time basis.
Bid/ask were 1.12569/1.12570. Raw-minus-local was 10,797.930 seconds.
Using the full two-host envelope of −1.901 to +2.099 seconds, raw-minus-coarse-
reference was 10,795.831 to 10,799.831 seconds (roughly 2h59m56s to 3h).
This is far outside the frozen five-second agreement tolerance. Quotes can be
stale; a single quote does not identify provider timezone, DST/session history,
runtime conventions or the meaning of flag bits 128/1024.

The local machine being three hours behind these two coarse public references
is not supported by this observation. A provider/server label convention is a
possible explanation, not an established one. No constant-offset subtraction,
historical normalization, metadata masking, source blending or gate promotion
was performed. Prior033/035 repeatability failures and clock/completeness/cost
blockers remain. No strategies, costs, risk settings, returns, orders, terminal
settings or EAs changed. Consumed2025, reservedNov–Dec2026 and provider stops
remain in force.

Next: CLOCK-SEMANTICS-038-PLAN.md proposes an offline audit of the saved native
seconds/milliseconds fields, a bounded review of official clock-function semantics
and preparation/compilation of a read-only demo clock observer. No observer is
attached or run in that stage. New terminal evidence requires a separate declared
runtime plan and review. This is a path to identifying the time basis, not a claim
that historical data or trading performance is qualified.

Originals and arithmetic are sealed in reports/clock-reference-037-capture.json,
reservation.json, ledger.json, tests.json and checks.json (each has a SHA256 seal).
Post-result review and final snapshot bind these files and this handoff. As in
prior stages, older large data/ZIP/runtime files remain externally hash-bound and
must be retained; the archive is not a self-contained reproduction package.
