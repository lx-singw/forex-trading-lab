# Reference 016B midnight boundary correction — 2026-10-06

Supplement REFERENCE-016-PLAN.md; keep all nine files, comparisons and numeric
thresholds unchanged. No reference statistics were published by 016. The first
run stopped at March 26's following-day 00:00 label. Its frozen code, ledger,
source archive and failure report remain unchanged. A bounded schema inspection
found that March 26 and March 27 each include a following-day 00:00 label.
January/July/November selected files showed no unexpected date labels.

Accept only exactly next-calendar-day 000000 as an additional date boundary.
Interpret its literal local instant as next-day midnight, without deciding
whether it labels the start or end of a minute bar. Preserve the original
source date/time/row. Implement an adapter to the frozen 016 parser's existing
240000 handling, then restore original labels. Reject every other out-of-file
date/time, duplicate midnight, reversal, or overlapping reference stream.

The reference 016B CLI copies the frozen 016 runner with only parser,
ledger/source/report paths, revision label and bound file list replaced. The
new independent checker copies frozen 016 arithmetic, changes output/ledger
paths and independently accepts exactly next-day midnight using its original
literal date. It does not import the boundary adapter. Bind all old and new
code, both plans, schema
inspection evidence and the failed attempt before fresh reference statistics.
Add boundary/lineage/rejection tests and run the complete suite first.

No additional downloads. No annual approval, changes to failed gates, source
mixing, returns, session closure inference or execution. All original 016
limitations and false approval flags remain in force.
