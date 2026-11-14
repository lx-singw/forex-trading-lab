# Private recorder109 — timing correction

The observed107 run, preserved in108, stopped at116 snapshots after nearly60seconds.
Its median read spacing was521.441ms. The original loop's fixed20ms sleeps permit
cumulative overshoot above its500ms target.

A separate109 recorder now selects its pause from the remaining interval. It leaves
25ms before the target for polling, with stop/date/clock/deadline checks on each
iteration. Maximum sleep remains20ms; minimum read spacing,120-snapshot limit,
60-second elapsed budget and256KiB file bound are unchanged. The final polling
window uses some CPU; it does not guarantee operating-system deadlines.

The actual account/identity/quote guards and shared107 export format/inspector are
unchanged. Attempts still persist before reads; a failed after-read guard discards
the quote. Collection defaults off, and no order, DLL, pipe, SDK/login, network feed,
symbol selection or trading-switch capability was added. All original107 source,
deployment and its stopped export remain preserved.

## Verification

**46 focused tests passed**, zero failures/errors/skips:37 existing recorder tests
and9 new scheduling tests. The shared account guard harness passed48 checks.
The actual shared schedule function passed15 boundary checks and5 invented timing
scenarios: first read, minimum spacing, reversal, deadline equality/excess and
unsigned extreme values; ordinary timing, coarse wait, adaptive wait, a long stall
and excessive native sleep delay.

In an invented model with1.5ms sleep overshoot and one437ms delay, the old coarse wait
fails to reach120 within60seconds while the adaptive wait completes120. Every
modeled read remains at least500ms apart. A3-second stall and a500ms sleep-delay
scenario still stop at the budget. These are synthetic checks of decisions, not
measurements or a forecast of native timing.

Only the waiting block and public script/status/file labels changed. A meaningful
source-comparison test verifies the remainder against107. Four new files bring
retained canonical sources from514 to518; all514 old source hashes are unchanged.
The older2,095-test active-suite result is retained; no new full-suite claim.

Existing MetaEditor compiled109 in a new isolated owned stage with **0 errors,
0 warnings**, producing a nonempty18,578-byte EX5. Process exit1 is recorded;
completion, diagnostic counts and the new artifact establish compile success.
The current compiler binary hash differs from107 and is recorded in the build
report; the agent did not install an update.

Four matching files (script, two headers, EX5) were deployed exclusively to
**Scripts/ForexDemoLab109-39828a784c0c**. No107/unrelated files or settings were
overwritten. No script was executed by the agent, no SDK connection or orders used,
and no support contact made. Native timing improvement remains unproved until the
manual launch and closed export inspection in
[PRIVATE-RECORDER-109-USAGE.md](PRIVATE-RECORDER-109-USAGE.md).

The captured107 clock labels still differ by roughly3hours; no timezone conversion
or quote-age claim is introduced.80 of116 quotes had equal bid/ask. This short demo
sample does not establish execution costs, complete tick coverage or profit.
Historical gaps, existing costs/strategy rules, native090/H.10 closures, provider
stops and reserved validation periods remain unchanged. Private engineering scope
and no-contact direction continue; use rights, UTC and producer authentication are
not certified. Market/paper/order admission and real-money execution remain false.

API semantics: [Sleep suspends the script for a requested millisecond interval](https://www.mql5.com/en/docs/common/sleep);
[GetMicrosecondCount measures elapsed microseconds since MQL program start](https://www.mql5.com/en/docs/common/getmicrosecondcount).
Neither statement establishes a hard scheduling guarantee for this implementation.
