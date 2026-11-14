# Separate083 R2 fixture correction and completion policy

Original frozen083 full run:1679 tests,1 failure/0 errors/0 skips. The tamper
fixture used `if cfg.get('wire_change')`, so offset0 did not change magic. The
production decoder already rejects changed magic; source/header remain exactly
unchanged. Preserve original source/ledger/archive/test-start/test-result bytes
and failure. Original083 evidence/check/seal/review were not run. No native action.

New fixture uses explicit key presence and strict integer offset0..143, removing
the old mutation during the base fixture call then flipping exactly one bit in
the boundary frame. Pending replies stay empty. It never changes production
logic. The corrected test class retains42 unaffected prototype tests, replaces
the one faulty tamper test and adds3 direct tests: zero really changes magic,
absent key preserves a valid frame, bool/negative/outside offsets reject.

Freeze separate R2 source/plan/current originals before one fresh full ACTIVE
suite:1682 tests =1636 unchanged baseline +46 corrected protocol/fixture tests.
`active_suite()` in scripts/synchronization-083-r2.py explicitly excludes43
tests from retired test_synchronization_083 and loads the46-test replacement.
The retired test file remains importable only as an immutable fixture/base;
do not use unrestricted default discovery as a completion check. Future full
checks must inherit this reviewed active-suite exclusion. No monkey-patching
old test functions or editing frozen files; original failure remains visible.

Retain the same34 portable C++/pure-MQL header comparisons and thirteen083 model
cases, plus changed_magic at offset0:14 cases,3 expected completions/10 rejections/
1 default-off. New evidence uses the corrected fixture. Verify exact reservation
bindings, all guard spans/counts/caps, strict pre/hold/post windows, once cleanup
and zero native/SDK/market/order/receipt flags. Freeze/test/evidence/check/seal/
review under separate synchronization-083-r2 records; no retry of original run.

All083 source/protocol/window/guard/cap/defaults and083 policy remain unchanged.
Keep082 success, spent081 permissions and all older failures/data/reserved gates.
Models and the1611ms scenario are not native timing bounds or launch authority.
Next fresh MQL/private transport source work is declared separately in
SYNCHRONIZATION-084-R2-PLAN.md; no actual compilation/deployment/runtime here.
