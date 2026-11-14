# Keep-awake139 results

Completed 2 November 2026. Built a standalone Windows console helper from the
canonical C# sources with the installed Microsoft.NET Framework compiler.
No SDK, service, broker account or scheduled task was installed. Native tests
were brief; no four-hour request or MT5 collection was started.

The helper defaults OFF. Explicit enablement accepts1–14,400 seconds, requires
confirmed mains power and uses a single SystemRequired request. It does not
request display, away or execution modes, modify the power plan or change
locking/security settings. It checks elapsed tick count, cancellation and
power status while calls return, and makes no renewal/retry requests. A
session-local mutex rejects a second helper. Output contains fixed statuses
and acknowledgements; it contains no account, machine or network identifiers.

The native backend follows Microsoft's [PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest),
[PowerSetRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest)
and [PowerClearRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powerclearrequest)
API lifecycle. SystemRequired concerns idle sleep. User-directed sleep/lid
actions can terminate a request; battery/Modern Standby policy adds limits.
The helper rejects unconfirmed mains power and stops on observed power loss.
An acknowledgement is not proof of ongoing sleep suppression.

## Verification

Compiled both helper and test executable with warnings treated as errors.
**30 simulated tests /47 assertions passed.** They cover default-off behavior,
duration limits/exact deadline, cancellation before/after activation, battery
and unknown power, loss during setup/operation, false returns and exceptions
at each power-operation stage, cleanup after clear failure, clock rollback,
oversleep, slow setup, readiness failure and bounded waits. The maximum
four-hour case uses a fake clock, not four elapsed hours of a real request.

Six brief Windows checks passed:

| Native check | Observed result |
| --- | --- |
| Default off | No power creation or power-status query |
| Two-second expiry | Create/set/clear/close acknowledged;2,000ms reported |
| Concurrent owner | Second helper rejected before power acquisition |
| Named cancellation | Clear/close acknowledged;266ms reported in this run |
| Forced exit of exact owned child | Ready event followed set acknowledgement; process exited; no managed cleanup receipt |
| New helper after forced exit | Acquired ownership, expired after1,000ms and acknowledged clear/close |

The active power scheme plus sleep/display configuration hash was identical
before/after. **Zero owned helpers remained.** Raw global power-request output
was not saved. Windows refused that request-list probe without privileges;
we did not elevate. Therefore global request removal was not directly observed,
and actual idle-sleep suppression and Ctrl+C behavior were not tested. The
forced-exit result proves process exit, not that finally executed. Windows
documents [automatic kernel-handle closure at process termination](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process);
the helper never duplicates or inherits its request handle elsewhere.

The initial PowerShell entry script was rejected as unsigned on the UNC
repository path. That attempt is retained. Execution policy was left unchanged;
the final product uses a standalone C# executable. An initial compiler command
also combined its output argument and source array incorrectly; compilation
failed before any helper ran. Corrected argument construction compiled the
same canonical sources. Both attempts remain in the report directory.

## Limits and next step

This is an idle-sleep request, not a guarantee against deliberate sleep,
shutdown, lid closure, power loss, policy overrides or blocked OS calls. The
deadline is checked when calls return; oversleep/call latency can delay cleanup.
No native failure was intentionally induced inside kernel APIs; those error
paths use the simulated backend. Named cancellation does not verify a console
host's Ctrl+C handling. Readiness reports a past Set acknowledgement, not a
continuous availability certificate.

The helper owns its handle. Terminating a launching parent does not necessarily
terminate its child. A future supervisor must connect cancellation and owner
death to the helper lifetime, and stop acquisition on interruptions. The helper
has its own duration limit but is not yet connected to lifecycle138 or MT5.
No helper is running after these tests.

Next build/test that supervision boundary with invented acquisition events:
recording requires a helper readiness acknowledgement; helper failure,
cancellation or owner loss must stop recording and preserve an interruption.
Keep native quote reading and future collection dates unavailable. The136
window remains expired, October quarantined, November–December reserved and
untouched, and automated orders unavailable. No profitability evidence was
generated by this work.

Sources: [helper/core](../src/windows/KeepAwake139.cs),
[console entry](../src/windows/KeepAwake139Program.cs),
[tests](../tests/windows/KeepAwake139Tests.cs),
[native harness](../tests/windows/KeepAwake139NativeChecks.cs),
[contract](KEEP-AWAKE-139-CONTRACT.md), [usage](KEEP-AWAKE-139-USAGE.md).
Evidence: [compiled test results](../reports/keep-awake-139/compiled-pure-tests.json),
[native receipts](../reports/keep-awake-139/native-check.json),
[compiler/artifact binding](../reports/keep-awake-139/compilation.json).
