# Windows helper ownership141 results

Completed 5 November 2026. The default-off Windows owner now contains the
pinned139 keep-awake helper from process creation. In brief native tests,
terminating the owner terminated its exact helper both while suspended and
after readiness. This establishes process ownership on this Windows host;
it does not establish market-data readiness or strategy profitability.

## Implementation

[Owner source](../src/windows/HelperOwner141.cs) creates one unnamed job with
KILL_ON_JOB_CLOSE and an active-process limit of one. Only the owner holds its
job handle. The child receives job membership inside CreateProcess through
JOB_LIST, starts suspended, and is checked for membership before resuming.
Only the selected output pipe and NUL input handles are inherited. These
mechanisms follow Microsoft's [job lifetime documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [process-creation attribute documentation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).
JOB_LIST requires Windows 10 / Server 2016 or newer; this build targets x64.
Containment failure has no detached-launch fallback.

Enablement requires an exact local helper path, expected SHA256, a new trace
path and an explicit duration of 1–14,400 seconds. The executable stays open
against replacement through launch. Startup consumes the duration. Existing139
readiness/cancellation events are used; no helper restart is attempted.
Ordinary shutdown cancels, waits, then closes the job if necessary and checks
exit. Forced exit is never reported as an acknowledged managed cleanup.

Exclusive, digest-linked traces contain typed lifecycle events and one
explicitly invented pending triple. They contain no quote, account identifier
or trading-engine event. Writes are flushed to disk before stdout notification.
A failed write or sync poisons the trace: subsequent writes are rejected.
The [independent Python reader](../src/forex_demo_lab/helper_owner_141.py)
checks bounds, fields, hashes, sequence, transitions and state, retains partial
tail information, and never grants crash append/resume. Hashes detect changes;
they do not authenticate the producer.

## Verification

99 Python tests passed: eight new reader tests plus the 91-test140 regression
set. The C# suite passed 14 pure cases and eight native scenarios, compiled
with warnings as errors using the installed .NET Framework compiler.

| Native scenario | Observed result |
| --- | --- |
| Default off | No child or trace created |
| Wrong helper hash | Rejected before child or trace creation |
| Two-second deadline | Ready, invented pending marker aborted, helper exit and clear/close acknowledged |
| Named cancellation | Helper exit and clear/close acknowledged |
| Exact helper terminated after readiness | Owner detected loss; failure code, no invented clear acknowledgement |
| Owner terminated before child resume | Suspended helper exited within the five-second test wait |
| Owner terminated after invented pending marker | Helper exited within the five-second test wait |
| Suspended gate timeout | No resume; job closed and child exit observed |

There were zero owned processes left. Active power scheme and sleep/display
configuration hashes matched before and after. No MT5 start, account query,
quote read, order, permanent power-plan write or execution-policy change was
performed. The native tests briefly requested SystemRequired through139.

Twelve closed journals from the initial and final runs were copied while each
source was exclusively open, with original/copy/after-copy hash agreement.
All twelve independently parsed to the expected state. The owner-death files
end at `child_created_suspended` (two frames) and `invented_triple_begin`
(five frames). The latter retains an unfinished invented marker; it is never
promoted into a completed observation. Other cases with a trace end at
`owner_stopped`. The native harness separately observed process exits; a trace
prefix alone cannot prove exit, its cause, or power-request cleanup.

Three pure cases specifically test sync failure, partial-write failure and
invalid event rejection. The first compile attempt after adding those tests
found a C# local-name collision; it was corrected before the final native run.
The earlier passed run and failed compile binding were preserved. Final
native source hashes were unchanged through independent inspection. All 20
prior140 source/evidence bindings matched before handoff updates.

Evidence:

- [Final native results](../reports/helper-owner-141/native-check-003.json),
  [build hashes](../reports/helper-owner-141/compilation-003.json) and
  [C# tests](../tests/windows/HelperOwner141Tests.cs).
- [Python tests](../reports/helper-owner-141/python-tests.txt) and
  [reader tests](../tests/test_helper_owner_141.py).
- [Journal copy checks](../reports/helper-owner-141/journal-copies.json),
  [independent readings](../reports/helper-owner-141/independent-inspections.json)
  and [verification](../reports/helper-owner-141/verification.json).

From the WSL repository, reproduce the offline tests without native launches:

```sh
PYTHONPATH=src:tests python3 -m unittest test_helper_owner_141 test_supervision_140 test_acquisition_138 test_coverage_137 test_context_recorder_136 test_forward_eligibility_134
```

For a preserved closed trace, call `inspect_bytes(path.read_bytes())` from
`forex_demo_lab.helper_owner_141`; use only these bounded lifecycle journals.
No market-data file is needed. The native test entry point takes the compiled
owner path, pinned helper path, expected helper hash and a new local journal
directory, in that order. Running it performs the eight brief native tests;
the build manifest records the actual executables and their hashes.

## Remaining work

This owner is a transport and process-lifetime component. It does not yet feed
authenticated, fresh ongoing status into140 or compose140 with native quote
acquisition. Readiness acknowledges a past successful request, not continuous
power effectiveness. Next connect typed native status/exit observations to the
offline supervisor and test missing, stale and contradictory status with
invented acquisition events before considering collection.

Global request removal and actual idle-sleep suppression were not verified.
Ctrl+C, arbitrary blocked filesystem/API calls, suspend/resume and all Windows
versions were not tested here. Killing an upstream shell is not the same as
killing owner141. Local same-user interference is not an authenticated security
boundary. Forced owner death cannot produce its managed cleanup receipt.

Native quotes, source freshness, UTC/session/cost qualification and sufficient
qualified history remain unresolved. There are no new strategy results. The136
window remains expired; October stays quarantined, November–December reserved
and untouched,2025 consumed, and automated orders unavailable. No new collection
dates or financial-engine permissions were introduced.
