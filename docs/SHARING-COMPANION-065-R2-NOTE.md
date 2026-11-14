# Revision2: clock test fixture correction

Original065 full regression ran1091 tests with one failure, zero errors/skips.
The reversal fixture advanced a clock but did not let Meter065 observe that
later value before subtracting one nanosecond. The resulting value remained
ahead of its recorded baseline, so rejecting it as a reversal was wrong.

Add a meter sample after advancing, then decrease the monotonic value. Core,
native files, private guards and session implementation are unchanged. Preserve
original initial-source ZIP/JSON/ledger/test-started/test-result/sidecars and
verify ZIP contents against frozen bindings. No original native session or
compiler started; do not rerun original test budget. R2 permits one new frozen
regression after this fixture fix and binds all original failure evidence.
Runtime/compile/preparation reports use the R2 prefix and one exclusive marker.
Source phase/date and native compatibility/compiler maximum remain one each,
not an additional allowance. Runner/controller source binding updates are
explicit. Any new failure must remain visible; no overwritten reports.
