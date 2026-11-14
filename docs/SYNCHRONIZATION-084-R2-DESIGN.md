# Separate084 R2 fixture correction and offline policy — 2026-10-08

Original084 source/interface/MQL/codec/build schema/design/policy remain frozen.
Its declared1718-test run failed exactly one test: owned_cleanup_after_date_expiry
expected overall finish success after expiry. Before freezing, implementation
had deliberately made post-cleanup clock validity mandatory. It attempts all
owned closes and still rejects the expired run. The fixture expectation was
wrong; changing production validity would weaken the clock limit. Preserve the
original test source, ledger/initial archive and failure report; no original
evidence/check/seal/review action was run, and none may now be invented or retried.

R2 changes only the fixture expectation in a new inherited test class. It checks
False overall validity, empty model handles, zero uncertain closes and exactly
one finish. Two additional checks cover cleanup returning beyond120s without
repeat closes and an excessive60s episode deadline rejected before transport.
The original36 tests are retained as evidence and replaced by38 active checks.
The prior08343 faulty tests remain retired with46 corrected tests active. Future
full suites inherit active_suite() from scripts/synchronization-084-r2.py.

Declare one fresh frozen full regression:1720 active tests/38 corrected checks;
same14 fixed injected cases/2 completions/11 rejections/1 default-off;18 portable
frame decisions/one exact encoder comparison plus34 retained windows. All actual
source bytes, modeled cases, caps and native exclusions are unchanged. Freeze
this correction source/test/controller/next plan and the original1718-test
failure SHA before the new actions. Failure after freeze needs another separate
correction; no rewriting, rerun, marker deletion or allowance refund.

Follow SYNCHRONIZATION-084-DESIGN.md and SYNCHRONIZATION-084-POLICY.md for the
source/ownership/private boundary/build contract. The concrete1611ms scenario
must reject stale publication before release;083 abstract timing success does
not carry over. Retain all full guards and2s/10s/30–31s/250ms/60s/120s limits.
Native backend/ACL/pipe boundary/MQL scheduling/blocking/compilation/deployment/
SDK/log/market/orders/receipt authority remain absent. No UI action is needed.

082 metadata success, spent081/raw markers,075 reference, old failures and all
033/035/data clock/cost/coverage/consumed2025/reserved Nov–Dec2026/provider gates
remain unchanged. No native readiness/bounds/profit/070 cause/eligibility/order
claim follows. No real/contest/live mode, martingale, paid service or new account.
