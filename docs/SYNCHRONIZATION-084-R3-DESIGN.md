# Separate084 R3 evidence audit correction — 2026-10-08

Retain frozen084 and084 R2 source, MQL, fixtures, model cases and artifacts.
Original0841718-test run had one expiry-cleanup fixture error; R2 replaced36
tests with38 corrected checks. R2's1720 active tests passed;14 injected cases
completed2/rejected11/default-off1. No full regression or model may be rerun.

R2's checker stopped at its guard-span equality assertion. In observed_guard,
75 guard callbacks started,74 valid spans were recorded, and the injected clock
reached120827ms during the final guard. Meter084's post-guard sample rejects
the unchanged120000ms whole limit before a valid span can be appended. There
is no missing successful guard to invent. Release was never attempted. All
model handles received closes; cleanup's overall clock validity remains false,
with zero uncertain model closes. This is a model observation, not native timing.

The earlier084/R2 narrative attributed the stop to stale publication. The
recorded scenario first reaches the whole-run deadline before final publication
validation. The additional serial guards also make the2s freshness requirement
infeasible for that scenario, but that is not the recorded first stop. This
document and results explicitly supersede that earlier causal wording, leaving
the frozen documents unchanged. Old070/native failure causes remain unknown.

R3 audits the retained JSON only, checks one explicitly incomplete final guard
in that exact failed scenario, and preserves exact equality for ordinary cases.
It does not manufacture a span, mark timed cleanup valid, rerun models, weaken
guards or extend time limits. Declare8 targeted auditor tests and one audit;
1720 full regression tests are retained, not rerun. Future full suites still use
084 R2 active_suite(); they discover these8 new tests too. A1728-test full run
has not been performed. Freeze source, prior failure capture, policy/next plan
and exact prior ledgers/tests/evidence before these new actions.

R2 produced no checks/seal/review record. Preserve an explicitly labelled tool
exit1 capture of its failed assertion, not a fabricated successful checker
record. The audit reconciles public counters/spans/frame fingerprints/error32
and once-cleanup records; detailed private frame/hold validation remains the
frozen decoder/matcher's injected generation result. Native ACL/pipe boundaries/
MQL blocking/compilation/runtime/profit remain unproven. No native backend,
SDK/MT5/compiler/deploy/log/market/orders/receipt authority exists.

Retain all2s/10s/30–31s/250ms/60s/120s caps, actualDEMO/default-off guards,
082 success, spent081/raw markers,075 reference, all older failures and all
033/035/data clock/cost/coverage/consumed2025/reserved Nov–Dec2026/provider
gates. Eligibility/orders stay false; no live/real/contest mode or martingale.
