# Windows helper owner141 contract

3 November2026. Implement native ownership/transport for the pinned139 helper
only. Default OFF, explicit enablement,1–14,400 seconds, exact local executable
path plus expected SHA256. Pin the verified executable against modification
through process creation. No MT5, quotes, account access or new collection dates.

Create an unnamed non-inheritable job with KILL_ON_JOB_CLOSE and a single active
child limit. Specify JOB_LIST at CreateProcess, not a post-launch attach. Start
suspended, verify membership, persist the created boundary, then resume. Refuse
unsupported/failed containment without a fallback detached launch. Inherit only
the designated stdout pipe/NUL handles via HANDLE_LIST; never pass the job
handle into the child. The sole job handle belongs to the owner process, so
owner termination closes it and Windows terminates the contained helper.

Use random named cancellation/readiness events, fixed name formats, bounded
waits and exclusive typed32KiB traces. The trace records helper lifecycle plus
an explicitly invented pending triple; it is not the138 market recorder or an
actual quote payload. Startup consumes the owner duration. Abort the invented
pending marker before ordinary cleanup; cancel the helper, wait briefly, close
the job if needed, and observe exit. Do not imply forced cleanup ran managed
finally or produced ClearRequest acknowledgement. No automatic helper restart.

Test default-off/invalid options and ABI/policy checks first. Native tests:
graceful deadline, cancellation, hash rejection, actual helper death, owner
death while child is suspended and owner death after ready/invented-pending.
Open and retain exact child handles supplied by the created-owner trace;
never terminate unrelated processes by name. Preserve real crash-prefix traces
and independently inspect their digests/order/pending state without resume.
Compare sleep/display configuration before/after and leave no owned process.
An upstream launching shell dying is not itself the owner141 death event.

Global power-request visibility and idle-sleep suppression remain unverified
where unavailable. Readiness acknowledges a past Set call, not uninterrupted
power effectiveness. Native owner141 does not establish the complete140
fresh-status IPC contract, source freshness, UTC or cost qualification. Use
only brief helper tests; November–December stays reserved/untouched and orders
remain unavailable. Keep previous138–140 sources unchanged.
