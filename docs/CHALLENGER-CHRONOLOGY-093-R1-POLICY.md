#093 R1 — correct test orchestration, retain failed discovery

The frozen093 launcher mistakenly used unrestricted unittest discovery. Its
first full run executed2,054 cases and failed two already-retired fixtures:
test_synchronization_083.Sync083Tests.test_source_build_phase_episode_sequence_and_padding_changes_rejected
(offset0), and test_synchronization_084.Sync084Tests.test_owned_cleanup_after_date_expiry.
That run, traceback log, source, ledger and spent marker remain immutable.
It is not a successful regression. Do not call or repair the frozen launcher.

The established synchronization-084-r2.py active_suite(), retained by090, already
excludes43 original083 and36 original084 fixtures. SYNCHRONIZATION-084-R3-RESULTS.md
explicitly requires future suites to inherit it. These exclusions predate093:
they are not a new removal of failed tests. The2,054 broad-discovery cases minus
those79 retired cases leave1,975 active cases:1,942 retained plus33 new093 cases.
Confirm all counts, old source hashes and unchanged093 code before proceeding.

Freeze a separate R1 correction ledger and this policy before one corrected
active full regression. Use exactly that inherited active_suite(), with no new
exclusions, skips, candidate changes, thresholds or source edits. Preserve the
first failure and bind the corrective launcher, source/protocol ancestry, test
selection/counts, started marker, log and outcome. The original093 policy permits
a further regression for a separately recorded repair; this is that repair.

The093 bot sources,31/33-test development records, one40-scenario demonstration,
two CASH choices and its one independent audit remain unchanged. No new fixture,
scenario or independent accounting rerun. Correction scope is test orchestration
and honest closure only. Do not invoke the original seal, which requires the
failed unrestricted result to pass. R1 writes the previously uncreated results,
final source/archive/review and four handoffs with the corrected result and the
failed run both documented. No claimed all-discovery success.

Market eligibility, orders/runtime, historical price decoding, external requests
and native/terminal actions remain unavailable. All old failures, source-clock/
coverage/lineage/cost/repeatability/provider/date/data exclusions remain.
