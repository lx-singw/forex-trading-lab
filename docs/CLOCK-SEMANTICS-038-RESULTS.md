# Native clock semantics audit 038 results

Completed 2026-10-06. Every saved033/035 native tick has time_s equal to
floor(time_msc/1000). A disagreement between the seconds and milliseconds fields
is therefore not supported by these originals. Their absolute time basis remains
unqualified. The read-only MQL observer and its shared guard code are prepared;
native compilation is **not verified**, and the observer was not attached or run.

546 tests passed (24 new, no failures/errors/skips). A synthetic C++ harness
compiled the exact shared MQL guard header and passed73 decision checks. The MQL
wrapper's API/output whitelist, query-error handling, disabled default, five
identity guards and one-quote limit were checked statically. These tests do not
execute native terminal APIs or establish that the MQL source compiles.

Before research or compilation,037's1,101 bindings/1,055 archive members/46 external
inputs verified.99 inputs were frozen; an exclusive sealed reservation followed.
The independent checker passed all original field comparisons, clock arithmetic,
documentation budgets and unchanged gates. Zero SDK connections, new quotes,
history downloads, strategy replays, returns or orders. No terminal/chart/timezone/
service/Algo Trading settings changed and no existing EA was overwritten.

| Saved original | Rows checked | Clock fields decoded | Floor-relation failures | Clock reversals |
| --- | ---: | ---: | ---: | ---: |
| 033 | 13,769 | 27,538 | 0 | 0 |
| 035 | 74,929 | 149,858 | 0 | 0 |
| Total | 88,698 | 177,396 | 0 | 0 |

All709,584 native/CSV fields across these responses were independently compared;
the full subsecond residual histograms and extrema remain in the sealed audit.
Overlapping rows count in each preserved response, not as extra unique market
events. Both metadata revisions and prior033/035 failures remain unchanged.
Agreement inside the saved structures proves neither timezone nor upstream
completeness. No fields, labels or flag bits were masked or rewritten.

All120 saved031 raw-minus-local intervals were reconstructed: envelope
10,795.879..10,798.642 seconds. Its distance from a *hypothetical* three-hour lead
is −4.121..−1.358 seconds. The saved037 quote gives10,797.930 seconds, or −2.070
seconds from that hypothesis, inside the031 envelope. Its prior coarse public
reference comparison remains10,795.831..10,799.831 seconds. This is consistent
with a three-hour label convention combined with quote age/reference uncertainty;
that is an inference, not an established offset or historical conversion rule.

The bounded official review used exactly eight declared opens, six finds and zero
searches; seven attributed findings were sealed. Four finds matched, two did not.
No alternate URLs, link traversal, broker contact or provider probes followed.
The clock functions have different sources and important limits:

| Function | Documented source | Consequence for a future observer |
| --- | --- | --- |
| TimeCurrent | Last-known trade-server quote time; outside OnTick, last quote among Market Watch symbols | Can be stale and need not correspond exactly to EURUSD's last tick |
| TimeTradeServer | Client-calculated estimate depending on computer time settings | Cannot serve as an independent server-time reference |
| TimeGMT | Derived from computer local time/DST handling | Does not independently calibrate UTC |
| TimeLocal | Computer local wall clock | Shows local context, not provider timezone |

These descriptions come from [TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent),
[TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver),
[TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt) and
[TimeLocal](https://www.mql5.com/en/docs/dateandtime/timelocal). Tester clocks are
simulated/equated as those pages specify, so tester output cannot establish real
terminal clock semantics; the observer rejects the tester.

[MqlTick](https://www.mql5.com/en/docs/constants/structures/mqltick) describes
last-price-update time and its millisecond field; it does not certify this
provider's historical UTC/session rules. The remaining observed bits128/1024
stay uninterpreted. [AccountInfoInteger](https://www.mql5.com/en/docs/account/accountinfointeger)
demonstrates checking the actual trade mode and distinguishing demo/contest/real.
The observer checks the actual mode; it never treats a server name as proof.
The exact TERMINAL_TRADE_ALLOWED find on the declared
[TerminalInfoInteger page](https://www.mql5.com/en/docs/check/terminalinfointeger)
did not match; linked enumeration pages were not opened under this budget. That
absence does not mean the property is unsupported. The declared Program Running
page was retrieved; its local-time find did not match and no additional runtime
claim is attributed to it.

One reserved compile-driver invocation failed with sanitized outcome
compiler_driver_failure_details_redacted. No owned clock038 build directory or
verified EX5 was produced. The original failure is preserved; there was no second
compile invocation or source repair. The installed MetaEditor executable is
hash-bound, but native compiler execution/success is not confirmed.

Post-result read-only diagnostics found zero PowerShell parser errors in the
compiler script, RemoteSigned policy, an unsigned source on a UNC/WSL path.
A separate harmless script launched with the same -File method returned1 with
UnauthorizedAccess and no success marker. It invoked no compiler/terminal and
changed no settings. This reproduces a launch restriction consistent with the
build failure; the original masked exception does not establish its exact cause.
A nested metadata query also failed; its failed attempt is recorded. Subsequent
read-only source metadata is sealed. No security-policy bypass, signing,
unblocking, installation or execution-policy change was attempted.

The prepared script has capture off by default, rejects non-demo/contest/real
accounts, USD/instrument/identity/Algo/connectivity failures and stale/invalid
samples, and emits only fixed numeric rejection codes or a clock/price whitelist.
It has no order, history, timer, file-write or settings capability. Its date is
fixed2026.10.06 and it must not be silently retargeted. Native API behavior,
runtime guard composition and journal extraction remain untested; the terminal
can write unrelated private journal messages, which must never be exported.

Next: COMPILER-LAUNCH-039-PLAN.md declares a new frozen build-driver repair and
one isolated compilation attempt using locally staged source/invoker files while
preserving Windows policy. This precedes any observer runtime. It is not executed
in038. Current-clock disagreement, provider historical clock/session rules,
metadata repeatability, completeness and executable costs remain unresolved.
Fresh/annual performance eligibility and automated orders remain false;
consumed2025/reservedNov–Dec2026/provider stops remain in force.

Sealed originals: reports/clock-semantics-038-ledger.json, reservation.json,
tests.json, research.json, audit.json, compile-reservation.json, compile.json,
checks.json, launch-diagnostic.json and source-metadata.json, each with SHA256.
Research/metadata composition inputs are retained separately. Post-result review
and final snapshot bind all artifacts and this handoff. The archive contains
sources/reports/small originals; large prior data/ZIPs and installed runtime/
compilers remain external hash-bound dependencies. Remote pages are attributed
summaries, not archived full page copies. Preserve those dependencies.
