# Daily reference098 — offline publication-aware import preparation

Implement a small local daily-reference importer and chronological availability
selector, with invented fixtures only. Read CONTEXT.md, PLAN.md and097 results
first. This is a software task; no external documentation/data request, SDK/MT5/
compiler/deployment/log/account/payment/provider contact or order action. Never
derive request syntax from the two failed097 help-page reads. No current code or
historical evaluation is authorized to accept market data through this module.

Use an explicit versioned local schema. Each observation must declare series,
base/quote currency, positive finite Decimal value, observation date, vintage
identifier, timezone-aware first publication timestamp, timezone-aware version
availability timestamp, source artifact digest and evidence references. Publication,
observation, revision and retrieval are distinct fields. Pair/direction must be
declared, never inferred from a price magnitude or an ambiguous filename. Synthetic
fixtures must declare their invented nature; do not attach a genuine publisher's
identity or URL as provenance for invented values.

Keep source policy separate from observations. Dated policy evidence must cover
the observation period, calendar/timezone interpretation, publication and revision
semantics and permitted study use. Missing historical evidence is a reason to
reject causal use. Do not construct2020–2023 schedules by backdating the2026
framework. Do not add a permissive switch to waive missing evidence.

Support two separate, typed roles: synthetic chronology demonstration, and local
final-vintage integrity inspection. The latter may check an already supplied file's
schema/provenance but must never make it eligible as a historical decision input.
Real market observations are rejected by the selector in this phase; a future
qualified-data route requires a separate implementation and acquisition protocol.

For synthetic records, selection at a declared UTC decision instant returns only
versions with evidenced availability strictly earlier than that instant. Choose
the latest eligible version for each observation deterministically, independent
of input order. Reject conflicting duplicates or inconsistent vintage ordering;
an identical repeated record may be deduplicated explicitly. A later correction
must not rewrite an earlier decision. No carry-forward or interpolation across
missing observations. Return a typed missing result with reason rather than an
invented value. Do not equate an observation's date with its availability time.

Meaningful tests must cover an exact publication-time boundary, one instant after
it, later revisions at earlier/later decisions, reordered inputs, conflicting
duplicates, malformed/naive timestamps, non-finite/nonpositive values, ambiguous
currency direction, absent policy/provenance, holiday/missing-day input, a final
vintage supplied without release history, a market record sent to the synthetic
selector, and deterministic save/reload behavior. Use manually declared expected
versions/times; tests must not generate expected results by calling the importer.

The demonstration reports eligible record/version counts and missing/rejected
reasons only. No returns, winning strategy, tuning, ranking, execution-cost model
or trade simulation. Do not connect it to093 or original009/020 runners. Existing
003/028/030 strategy/cost rules and all data/provider/reserved-period gates stay
unchanged. Keep real-money execution unavailable and orders disabled.

Inspect existing source conventions, add the isolated module/fixtures/tests, run
its focused tests, then the existing corrected084R2 active suite if integration
requires it. Retain old failure records and existing43/36 retired fixtures; no new
exclusions. Seal a separate098 outcome with actual checks and limitations. A
software pass is not historical-data qualification or profitability evidence.
This plan is unexecuted in097.
