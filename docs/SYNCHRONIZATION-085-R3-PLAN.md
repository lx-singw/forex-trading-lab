# Next085 after084 R3 audit — unexecuted

Follow SYNCHRONIZATION-085-R2-PLAN.md and original085 plan, subject to this
corrected evidence: the concrete1611ms scenario starts75 guards, records74
valid spans and reaches120827ms before release. It fails the whole-run clock
while also being incompatible with2s response freshness. Do not claim its
first stop was the final freshness check or invent a completed75th span.

Verify084 R3 closure, retained1720 passing active tests,8 new targeted auditor
checks and14 retained model cases (2 complete/11 reject/1 default-off). Original
0841718 fixture failure and R2 checker exit1 remain preserved. Full suites must
use084 R2 active_suite(), excluding both retired fixture classes and including
the new auditor tests; no1728-test full run has occurred yet.

Redesign/review the private response boundary and blocking close behavior before
native admission. Keep every full guard and2s/10s/30–31s/250ms/60s/120s limits;
no caching/retimestamping/quiet extension or bounds from finite maxima. Prepare
concrete native backend/source-bound compilation in separately declared stages.
No native SDK/compiler/MT5/deploy/log/market/order/receipt authority is granted.
ExpiredOct8 declarations need fresh phases/dates; preserve all older artifacts,
failures, spent markers and data/reserved/provider gates. Profit remains unproven.
