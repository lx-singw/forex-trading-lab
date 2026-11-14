# Invented acquisition138 contract

2 November 2026. Implement only the pure lifecycle and a bounded journal of
invented acquisition events. No prices, actual account identifiers, source
timestamps, terminal reads, power API, future collection dates or native
acquisition adapter. Disk IO is exercised in dedicated temporary test folders.

The lifecycle begins OFF; enablement and retries both default false. Invented
guard inputs carry the actual account enum (REAL0, DEMO1, CONTEST2), query
success, ephemeral identity continuity, connection, Algo-off, non-tester,
EURUSD/USD and safe-clock results. They are simulated inputs, not evidence of
a queried account. Unknown/real/contest/changed identity/Algo-on/unsafe checks
stop the job even when disconnected. Actual native checks will be required
before any future native read; this layer grants no admission.

The job budget is at most four monotonic hours including waits. At the exact
deadline stop. Reconnection is opt-in with at most three attempts across the
entire job, waiting5,30 and120 seconds after each interruption/failed attempt.
A successful connection does not reset the attempt count. No catch-up polls;
actual triple starts are at least1s apart. Context is required at every segment
start and on elapsed-hour boundaries, never halfway through a pending triple.
Guard failure after a read aborts the pending triple without committing it.

Every interruption is explicit. The old segment can contain operational
wait/retry/stop events after interruption but cannot receive further triples.
Successful reconnect closes it, opens a hash-linked new segment and requires
new context. Clean capacity rotation likewise occurs before a triple begins.
Unsafe clocks stop the job; any later clock segment requires a new explicitly
started job and preflight. This resolves the general design's clock-boundary
language without retrying an unsafe clock inside the current job.

Journal frames contain only fixed-schema enum events, monotonic markers,
sequence counters and random non-identity job IDs. There are no free-text
payloads. Use exclusive new job directories and files, full-write checks and
flush/fsync acknowledgement. Bytes reserve before IO and never refund after
failure. Normal frames leave16KiB for bounded control/close events; complete
triple space reserves before beginning. Limits:32MiB/file,128MiB/job,64 segments,
and1024 bytes/frame. Smaller test limits cannot exceed these limits. A failed
write/flush/close/open poisons the journal, stops the lifecycle and permits no
further writes, retry or rotation. This cannot preempt a blocked OS call.

The independent reader validates canonical frames, digests, linked segments,
monotonic sequence/time and event-state ordering. A partial final frame and
uncommitted triple remain explicit. Missing/invalid middle boundaries reject
the chain. Present valid bytes are not proof of fsync acknowledgement or
producer identity. Even an intact stopped journal has no append/resume API;
restart always creates a fresh random job and never claims cross-job identity.

Test exact budget/backoff/spacing boundaries; real/contest/unknown account and
identity changes; pre/post guard faults; sleep and clock rollback; context
refresh; rotation; partial/short writes, flush/fsync and close failures;
capacity limits and failed new-segment creation; corrupt/rehashed semantics,
missing boundaries, independent restarts and retained crash prefixes. No
expired136 dates or saved/native market files are changed. November–December
remains reserved/untouched. Orders and real-money execution stay unavailable.
