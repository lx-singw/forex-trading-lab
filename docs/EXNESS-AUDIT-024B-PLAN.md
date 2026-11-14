# Supplemental format interpretation 024B

Declared after 024's preserved strict failure and before any 024B parsing.
024 acquired exactly two originals; no further network requests are authorized
by this supplement. ZIP CRC inspection succeeded. Independent row accounting
matched March 1,385,093 and July 1,151,933 records. Every row failed the frozen
024 provider check. Preserved examples show lowercase `exness`, exact EURUSD,
and `YYYY-MM-DD HH:MM:SS.sssZ` rather than the assumed uppercase provider and T.
024's all-zero accepted-hour counts describe rejection, not market coverage.

Create separate versioned parser and checker, retaining 024 unchanged. Permit
only exact lowercase `exness` and exactly one ASCII space at timestamp position
10; continue requiring Z, exactly three fractional digits, a valid UTC calendar,
the same exact five-column header, EURUSD, month boundaries, finite positive
Decimal prices, Ask >= Bid and unchanged original event order. Header `Exness`
remains uppercase. Preserve original price strings and full precision; never
round the observed float-like decimals. Reject uppercase row tag, T separator,
offsets and other variants in this version. Canonical hour-key lookup replaces
the one date/time space with T; original endpoint/record strings are preserved.
A string-based derivation must prove that only these four primary-parser
replacements (regex, parse format, tag, hour-key lookup) and three independent
checker replacements (regex, tag, hour-key lookup) occurred, plus checker output
version names. No numeric
method, gap threshold, ordering, ZIP limits, acceptance or eligibility change.

Freeze source, tests, this plan, original acquisition ledger and both original
audit/check reports and seals before the supplemental audit. Independently
re-read all original rows again, with exact rational price checks and manual
timestamp construction. Preserve separate 024B outputs and seals. Whole-month
counts, endpoints, ties, repeated records, UTC-hour counts and gaps >3,600 seconds
use unchanged 024 metrics. Synthetic tests must exercise accepted original
format, rejected alternative formats, crossed/nonfinite prices, boundaries,
backwards/tied events and the derivation proof. Both source versions stay bound.

No old-source market comparison occurs in this step. Such comparison needs its
own frozen windows, metrics, acceptance rules and preserved old-input preflights.
Successful parsing establishes neither absolute clock certification, historical
sessions nor independent upstream prices. Annual/performance eligibility stays
false; no return computation, interpolation, blending, paid access, accounts,
2025/reserved late-2026 data, provider contact or orders.
