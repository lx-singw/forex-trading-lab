# Whole-month diagnostic audit 024

Declared before inspecting ZIP members or CSV rows. Supplements the acquisition
plan with implementation details; it does not relax its format requirements.

Read March then July, ZIP central-directory order and original CSV record order.
CSV files must have a basename only; allow only empty, safe single-component
directory entries. Reject duplicate member names, traversal, encrypted members,
non-CSV files, more than 64 members, over 256 MiB declared or actual uncompressed
bytes per ZIP, or over 512 MiB across both. Verify each complete member's CRC
with bounded streaming before parsing. No extraction. Require UTF-8 without BOM,
exact header `Exness,Symbol,Timestamp,Bid,Ask`, and exactly five fields per record.
The first two fields must be `Exness` and `EURUSD`. Timestamps must use
`YYYY-MM-DDTHH:MM:SS.sssZ`, with a valid calendar time within the named UTC month.
Prices use finite positive Decimal values, Ask >= Bid. No sorting or filtering.

Report every row's validity through total/error counts; preserve the first 20
offending records per error type with member and CSV record number. Originals
preserve all remaining errors. A failed header stops row interpretation for that
member, while CRC and archive inspection still precede it. Any invalid quote,
backward timestamp or archive/schema error fails the diagnostic audit.

Count tied adjacent timestamps and repeated five-field records within their
timestamp group without changing their order. Report first/last original event,
all UTC-hour counts (including zero hours at month edges), and every gap strictly
greater than 3,600 seconds. Empty hours and long gaps receive no closure or outage
classification. Do not calculate strategy returns or compare old market sources.

Freeze parser, runner, independent checker, tests, this protocol, acquisition
plan, original ZIP hashes and receipt hashes before the first full audit. The
checker re-reads original rows independently, using fixed-position timestamps
and exact rational prices; it compares row accounting, endpoints, hour counts,
tied/repeated records and gaps. It must not call the primary parser. Both outputs
are exclusive. Synthetic malformed/archive-boundary tests precede the market run.
No diagnostic success grants annual eligibility, independent UTC certification,
historical session knowledge, feed independence, permission or executable costs.
