# Bounded Windows keep-awake139 contract

2 November 2026. This helper is separate from collection138 and has no MT5,
account, price, strategy or order integration. Compile a standalone Windows
executable from canonical C# with the installed Microsoft.NET Framework
compiler; no SDK/service install needed. The initial unsigned PowerShell
entry script was rejected on the UNC path. Preserve that attempt and leave
execution policy unchanged; no PowerShell entry script is required by the
standalone executable.

Default disabled. Explicit enablement needs a duration of1–14,400 seconds.
Request only PowerRequestSystemRequired on confirmed mains power; do not keep
the display on, request away/execution mode, change a power plan, suppress
locking or change security settings. Unknown/battery power before acquisition
rejects it; observed loss after acquisition clears/closes and ends the helper.
Sample cancellation/power at most250ms apart while calls return. A monotonic
GetTickCount64 deadline includes setup after entry, and has no renewal/retry.
Blocked OS calls, deliberate sleep, lid closure, shutdown or power loss cannot
be prevented or forcibly preempted by this helper.

Use one handle, one successful SetRequest, a ClearRequest in finally and a
CloseHandle even after create/set exceptions or failed clear. Record each
acknowledgement separately; do not hide cleanup failures. A process-scoped
handle is not duplicated/inherited to other processes. An OS-terminated helper
may not execute finally; process termination closes its kernel handles. Do not
claim that a forced-exit test ran managed cleanup. A single-owner mutex prevents
concurrent helpers in the Windows session, but does not schedule future runs.

Cancellation can use Ctrl+C where supported by the console host, or a named
local event with a random non-identity ID. Validate its fixed name format and
fail before power acquisition if it is unavailable. Test named cancellation;
do not assume PowerShell Ctrl+C behavior has been verified by that test.
Output only fixed statuses, durations and API acknowledgements, not paths,
machine/account details, errors containing arbitrary text or other apps' power
requests. Persist no credentials or account identifiers.

Test the pure runner with a fake clock/backend first: default off, exact
deadline and limits, cancellation before/after acquisition, mains loss/unknown,
API false returns/exceptions, cleanup even when clear fails, clock rollback,
oversleep and bounded waits. Then run only brief real Windows checks: disabled,
short expiry, named cancellation, concurrent-owner rejection and forced exit
of an exact child process created by the test. Compare the active power scheme
and sleep timeout before/after. No elevation or permanent power changes.
If the global power-request list is unavailable, retain that limitation;
successful native API acknowledgements do not prove idle-sleep suppression.

No market data, reserved dates or expired136 collector is read or renewed.
Keep source here and any runtime artifacts in a dedicated owned report/temp
folder. Leave no keep-awake process running at task completion.
