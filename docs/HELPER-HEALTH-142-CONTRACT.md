# Helper health142 contract

5 November 2026. Helper-only diagnostics; no terminal, account query, price
input, order API or collection dates. Both Windows entry points default OFF.
The existing139 runner and141 process-containment source remain unchanged.

The new142 helper wraps139's power backend and publishes a small volatile
status slot after power checks and create/set/readiness/cleanup transitions.
The owner creates the random job-scoped mapping before launching the helper.
It uses141's atomic job assignment and suspended creation, with only designated
pipe/NUL handles inherited. The verified helper executable remains open against
replacement through launch. The139 singleton mutex is shared with older helpers.

The x64 slot holds an aligned version, native monotonic tick and fixed flags.
The writer marks the version odd while updating and even when complete, with
memory barriers; the reader accepts only a matching even version across the
read. Sequence advances identify new helper samples; repeatedly reading the
same version is not a new sample. Readiness represents acknowledged create/set
and the readiness event, not proof that the machine cannot sleep.

Microsoft documents [aligned64-bit access on64-bit Windows](https://learn.microsoft.com/en-us/windows/win32/sync/interlocked-variable-access)
and [memory-barrier ordering](https://learn.microsoft.com/en-us/dotnet/api/system.threading.thread.memorybarrier?view=netframework-4.8.1).
This implementation is restricted to x64. No portability claim follows from
this host's tests. The random mapping/event names and challenges correlate a
job; they do not authenticate it against malicious same-user interference.

The owner accepts bounded ASCII LF-terminated commands `POLL`, `CANCEL` and
`EXIT`, each with a fresh32-hex challenge. Replies echo the job and challenge.
Status contains the helper's sample sequence/tick, owner's native tick, exact
process liveness and fixed acknowledgement flags. Exit receipts distinguish
process exit, job closure, cancellation and optional139 clear/close receipts.
Input EOF and the native duration cap initiate cleanup. A failed/unsupported
job setup never falls back to detached launch. Owner death closes its sole
job handle, containing the helper's lifetime.

The Python142 decoder rejects unknown fields, wrong types, mismatched jobs or
challenges, slow/reversed receipt clocks, future native samples, sample
regressions, rewritten samples and contradictory readiness. Startup without a
sample is not ready. Source age comes from Windows tick differences; the whole
request round trip is charged conservatively in the receiving clock domain.
Duplicate samples retain their first conservative receipt marker. No Windows
tick is relabeled as UTC or directly compared with the WSL monotonic epoch.

Native source: [helper/owner](../src/windows/HelperHealth142.cs).
Decoder: [Python](../src/forex_demo_lab/helper_health_142.py).
Tests: [packets](../tests/test_helper_health_142.py),
[slot](../tests/windows/HelperHealth142Tests.cs),
[native ownership](../tests/windows/HelperHealth142NativeChecks.cs).
See [integration results](NATIVE-SUPERVISION-143-RESULTS.md).
