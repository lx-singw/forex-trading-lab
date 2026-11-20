# Sprint 227 · Per-opening receipt order

20 November 2026. At the scheduled H1 opening, the historical Level B
counter had applied the manifest's timing policy to both modeled bar
opens and paired quotes. A boundary quote has its own receipt order.
The counter now requires order evidence for a paired quote when its
receipt timestamp equals the decision timestamp.
[Frozen entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics) · [Historical opening records](RESULTS-221.md) · [Publication timing scenarios](RESULTS-226.md)

## Evidence accepted at a tie

A reviewed `paired_quote` opening may include a `same_time_order` object.
Supply the exact triggering H4 close in `trigger_end` as UTC epoch
milliseconds. Supply `decision_ordinal` and `opening_ordinal` as
nonnegative integers on the same reviewed receipt clock. The decision
must precede the opening in that order. The input digest binds the new
fields along with the paired bid, ask, source time and receipt time.
The ordinals resolve ordering at the timestamp derived by the counter.

The counter reports `UNRESOLVED_OPEN_ORDER` when the evidence is missing,
refers to a different H4 trigger, or gives the events the same or reversed
ordinals. A boundary pair whose decision is strictly earlier can still
reach the price filters on timestamp order. A tied `bar_open_assumption`
uses the reviewed manifest-wide policy for that model. An absent or late
first scheduled opening still removes that entry.

The optional order record requires both the paired quote source and
receipt times at the scheduled boundary. The file format supplies a way
to represent the evidence. The source review must establish the actual
shared clock, decision timing and first opening quote. The receipt's
`PAIRED_AT_BOUNDARY` tally continues to count timestamp alignment.

## Verification and disposition

The fabricated historical count case exercises a missing order under a
permissive model policy, equal ordinals, reversed order, and evidence
bound to a different close. The matching pair passes with an earlier
decision ordinal even when the manifest's modeled order is unresolved.
Reader cases check late quotes, triggers after the opening and invalid
ordinals. The existing model and strictly earlier paired quote cases
exercise their normal paths.

All 104 targeted tests passed. The canonical Phase 10 report matches
Sprint 226 byte for byte and remains `UNAVAILABLE` with null actual
counts. Source qualification and independently supported historical
receipt evidence remain open. Verification used fabricated inputs and
configuration metadata.
