# Diagnostic lifecycle159 — offline binding slice

15 November2026. Connect checked156/158 diagnostics to unchanged138/140 lifecycle
journals using invented replay observations. This is offline integration, not a
live source adapter, historical dataset, account attestation or collection grant.
No helper/MT5 process or actual price request is needed. Preserve prior sources.

Admission requires a complete158-consistent diagnostic job and a stable bounded
manifest of its native journal, relay receipt, claim and named request/reply files.
Allow only the two predeclared157 fixture economic/clock payload profiles below.
The projection includes tags, query IDs/keys, success/error values, every native
scalar/clock/quote value and commission rule/tier field; guard timing and helper
records remain bound by the complete native/source hashes. Do not round doubles,
convert prices to155 integer points or turn missing costs into zero.

| Profile | SHA256 of canonical projected payload rows |
| --- | --- |
| Full invented metadata | `5dae9da43571ed2d44ab68d719d4599ca2e6d799175271f34ec73892d971e2e1` |
| Failed/absent invented metadata | `b1060237d6f1d453aadd5f8aa20757d61227981038017f1d600b4d0ac6fbd5e1` |

This deliberately narrow gate does not authenticate provenance; it prevents this
slice from becoming arbitrary market ingestion. All real-market gates stay false.
Account checks and helper observations are explicitly invented replay inputs,
using138's named enum, never converted from native account integers. A fresh job
nonce and separate replay clock prevent native/source timestamps being relabelled.

A new bounded159 binding journal references the exact source manifest and raw
context/triple blocks. It joins138 context/begin/commit/abort and140 supervision
heads. Required order: open, context, begin, prepared, lifecycle commit, binding
commit acknowledgement, end/close and a final publication receipt. Source hashes
are rechecked before commit and finish. Only a consistent successful receipt may
publish the one diagnostic triple. No live execution or append/resume is offered.

Keep physical frames, acknowledged prefixes, final publication and caller receipt
acknowledgement separate. A present lifecycle or binding commit beyond an
acknowledged prefix cannot self-publish. A crash with no final receipt publishes
nothing in the independent inspector. Receipt bytes after an uncertain write
cannot prove caller acknowledgement or crash durability. Keep failures/partial
files; poison writers instead of retrying. New jobs cannot reuse an old directory.

Verify full/failed metadata, invalid source/projection/hash/receipt, source change,
guard/helper loss, commit/abort, duplicate calls, deadline/reversal, binding/life/
supervision storage failures, uncertain commit acknowledgement, crash prefixes
and fresh-job restart. Independent inspection must join all journals and source
hashes and reject rehashed semantic corruption. The CLI defaults off and offers
only invented exercises plus separate read-only inspection. No native launch.

Also replay the closed clean158 trial, retaining its archived native-helper
evidence and invented prices. New replay account/helper checks remain invented;
do not restart a helper or imply capture-time guards. Verify the original archive
hashes remain unchanged. This is a separate source-bound example, not a unit-test
dependency or an additional native trial.

Keep protected dates/routes, frozen controls,16 unavailable market cells and
orders-off unchanged. Review intended changes, record source-bound evidence,
commit descriptively and push to main after verification.
