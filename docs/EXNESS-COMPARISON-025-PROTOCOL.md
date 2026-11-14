# Comparison implementation contract 025

Declared before selected quote statistics. The frozen 025 plan's windows and
three presence/tail questions remain unchanged. No additional market windows.

Read sources in order: Exness, HistData candidate, broker conditional, Forexite
reference; March then July. Exness reads its original monthly ZIP and the exact
024B format. HistData reads the frozen 015 monthly derivative, inventory and
provenance, retaining original source sequence/label. The independent checker
rebuilds HistData directly from its original ZIP: parse wall labels, add seven
hours, then apply the preserved Athens hypothesis (UTC+3 for these selected
late-March/July rows), equivalently source wall +4h. No October rows are involved.
Check selected timestamps against derivative values, never relabel originals.

Broker March uses only data/correction-013-gaps/2023-03-27, originally raw02..03;
neighbor hours are unavailable, not empty captures. Broker July uses original
data/recovery-010/chunk-081, raw July13..15. Subtract three hours conditionally
for both selected summer windows. Require preserved actual-demo capture metadata,
Algo Trading false, original data/report hashes, sequences and capture bounds.
Do not connect to a terminal or request additional quotes.

Forexite uses the frozen diagnostic minute lineage. Independently rebuild its
three original daily ZIPs with original row/date/time and the frozen 016B exact
next-day-midnight convention. Use the manual calendar's UTC+2 for these dates;
retain literal labels, unknown bar start/end and unknown quote side. Publish
reference OHLC separately from tick bid/ask. Do not infer ask, spread or ticks.

For every hour, emit explicit available/empty/unavailable source status, counts,
endpoints, full bid/ask OHLC for tick streams, literal reference OHLC, and first/
last original row provenance. Exness additionally has all minute bins, including
empty ones. A separate selected-row CSV retains every selected original event's
path/member/one-based CSV record/raw label and numeric values; HistData values
are its already frozen derivative's representation, checked numerically against
originals. Headers are record1; headerless HistData record1 is source sequence0.
Never sort, deduplicate, repair gaps or suppress tied quote events.

Each source/window has a SHA256 of original-order canonical events. Serialize
compact JSON arrays followed by newline: [path, member-or-null, record, raw_label,
event_ms, values], where values is [bid,ask] for ticks or [open,high,low,close] for
reference bars. Each numeric value is its exact rational numerator/denominator
string. Thus representation-only trailing zeros do not create a price mismatch.
HistData raw_label is its original wall time rendered ISO with three fractional
digits; broker raw_label is its unchanged integer API label rendered as a string.
Exness raw timestamp and Forexite date+' '+time remain literal.

Report all pairwise absolute hourly OHLC distances in pips (1 pip=0.0001), using
bid when both are ticks and literal reference OHLC for Forexite. Use Decimal
arithmetic, serialize exact decimal strings, and do not apply an acceptance
threshold, align a minute shift or choose a source winner. Missing counterparts
produce null distances. Ask/bid/reference prices never become executable inputs.
The independent checker uses rational arithmetic and direct original files,
without importing this stage's reader/aggregation functions. It verifies selected
event hashes, lineage rows, every hourly/minute field, distances and question
answers. Tests exercise half-open endpoints, strict tail cutoff, tied/order
handling, unavailable/empty distinctions and full-precision/missing prices.

Freeze plan/protocol/code/tests and all selected data/metadata/review bindings
before computing. Run old 013/015/016/016B/017/024/024B preflights before and after
comparison; preserve 024 snapshot and all its bound groups/archive members.
Use exclusive ledgers/reports and sealed outputs. Annual eligibility remains
false regardless of three answers; no requests, returns, data blending or orders.
