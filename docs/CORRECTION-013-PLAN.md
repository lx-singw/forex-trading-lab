# Explicit diagnostic correction 013 — post-hypothesis development

Study012 establishes that the two repeated October hours are identical ordered
timestamp/bid/ask/volume sequences in all four years (3,800/1,695/4,625/2,559
rows). Its proposed late-Sunday fold mapping is not approved. All original
archives, failed mapping, event screens and reports remain untouched.

Implement a separate candidate correction, explicitly post-hoc development:
collapse only the second exact replay block in a derived diagnostic stream.
Keep canonical raw files and both copies in the original archive. Bind the
correction to those exact archive hashes, month, original row ranges and all
record content. Record every collapsed original row's correspondence to the
retained first copy. No other duplicate, gap, quote or period may be removed.
Any changed record/count/boundary aborts the correction before publication.

Test a calendar hypothesis: raw source label +7h behaves as an Eastern
European wall clock with winter +2h/summer +3h and European calendar dates.
Use the frozen Europe/Athens timezone data as a representative rule, not a
claim about broker location. Reject nonexistent or ambiguous wall times;
do not guess a fold. This calendar changes at Sunday01:00UTC, earlier than
the observed late-Sunday archive defects. Primary calendar rule:
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32000L0084 .

Review the same eight March/October source months. Recompute the same six-hour
transition comparisons and alternative offsets. Preserve March's actual
one-hour data gaps; do not compress elapsed time to disguise missing quotes.
Record original/corrected counts, replay lineage, gap inventory and candidate
UTC labels. No price is fabricated, averaged or changed, and no provider is
mixed into the derived stream. Original same-ms events remain in order.

Tests must reject an incomplete or altered replay, an unlisted reversal,
wrong month/sequence, invalid quote, ambiguous/nonexistent calendar time and
out-of-scope years. Check both European/US autumn mismatch and March gaps.
Only diagnostic JSON is published; this is no eligible simulator dataset.
Existing failed 007/009/010/012 reviews stay failed. The eleven 012 anchor
screens did not all pass and do not certify annual UTC. Missing source hours
and July14 coverage remain blockers. No strategy returns, orders or settings.
