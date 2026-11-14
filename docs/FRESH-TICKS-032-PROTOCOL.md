# Full-tick original preservation protocol 032

Implements the unchanged FRESH-TICKS-032-PLAN.md. Numeric source-label request
is inclusive1791293942000..1791294003000,61 seconds. No alternate timestamp
interpretation, retry, price transformation, filtering or strategy simulation.

Before the sole request, reserve the exclusive output directory and reservation
JSON. Record UTC/monotonic bounds around the request, with current receipt date
2026-10-06, actual DEMO/USD, Algo Trading off and unchanged private account/server
identity around metadata/read/completion. Export only approved contract fields.
No terminal launch, login, symbol selection, orders or terminal settings changes.

For the exact eight numeric fields time,bid,ask,last,volume,time_msc,flags,
volume_real, preserve all bounded rows as raw.csv using round-trip float text.
Also preserve response.bin and numeric field offsets/formats/item size. This
extra lossless evidence lets the independent stdlib checker reconstruct every
CSV value directly from the original response bytes. Require no object/string
fields or hidden fields; record padding must be zero before export. Do not serialize unknown-field values or API
exception text. For an unsupported schema preserve safe count/schema fingerprints
and numeric-buffer hash when available; this privacy rejection cannot be called
a complete original or dataset. A failed post-read account guard likewise
exports no untrusted quote payload. This follows the project identity/privacy rule.

Known-schema bounded rows are preserved before checking quotes, range or
chronology; validation failure retains the entire original, never a prefix.
Oversized rows/bytes retain count/schema/safe hash, no prefix. Combined binary,
CSV and metadata evidence stays within4MiB. The SDK can allocate an oversized
response before Python can inspect it; this bound limits exported evidence.
One read only,60-second soft native-call timeout, no cancellation guarantee.

Audit every row for positive ordered bid/ask, finite nonnegative last/real-volume,
nonnegative integer volume/flags (flags within uint32), time/time_msc agreement,
inclusive request bounds and nondecreasing labels. Retain exact duplicates and
same-millisecond events. Report counts, every error category and bounded first
error indices, first/last labels and maximum nonnegative intertick gap. A gap in
this small sample is descriptive, not a closure/outage/completeness classification.

The independent checker uses struct, csv, integer timestamps and its own row
validation, not collector audit helpers. Compare all eight binary/CSV fields,
all original counts/errors/ties/duplicates/gaps, and each031 timestamp/bid/ask
witness against original row indices. Report unmatched and ambiguous witness
counts rather than picking a row or repairing quotes. Repeated poll snapshots
may map to the same source row; they are not separate ticks.

Freeze all implementation/tests/protocol/031 inputs/runtime bindings after the
full regression suite, before connecting or requesting. Finish with sealed
originals/review/source archive and updated handoff. Passing this short diagnostic
does not authorize larger acquisition, UTC normalization, costs, selection,
fresh/annual validation or execution. Preserve2025/reservedNov–Dec2026 exclusions.
