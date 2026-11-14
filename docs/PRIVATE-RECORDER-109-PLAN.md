# Private recorder109 — sampling wait correction

The observed107 export stopped at116 snapshots/60seconds, with median521.441ms
read spacing. Preserve that export and original107 implementation. Build a separate
109 script using unchanged107 protocol/inspector and shared107 account/clock/price
guards. Keep current private demo/no-contact scope, default collection off, exact
EURUSD,120 snapshots,500ms minimum spacing,60seconds and256KiB bounds. No trades,
SDK/login, DLL, pipe, symbol selection, network feed or terminal settings changes.

Replace only the coarse waiting block. A pure shared schedule function subtracts
checked monotonic values, rejects reversal/deadline, sleeps at most20ms while
leaving25ms margin, and polls the final window with stop/date/clock checks. This
uses some CPU to reduce quantization; it is not a hard-real-time guarantee.
Never catch up through too-close reads, raise the time budget or fabricate samples.
Other guard positions, persisted attempts and discard-after-failure behavior stay.

Use a portable C++ harness to exercise the actual schedule function, including
deadline/overflow/reversal boundaries and end-to-end invented oversleep/stall
scenarios. Run focused107 inspector/guard tests plus109 tests; preserve the older
full-suite result without claiming a new full run. Technical reads may use only
official MQL Sleep/GetMicrosecondCount documentation; no market/support requests.

Compile in a new isolated owned Windows stage with existing MetaEditor. Require
finished build, zero errors/warnings and nonempty new EX5. Deploy source, both
headers and EX5 only into a new owned Scripts folder; preserve107 deployment.
Do not run the script or alter settings. Native UI is unavailable, so final native
timing behavior still needs one manual launch and closed export inspection.
