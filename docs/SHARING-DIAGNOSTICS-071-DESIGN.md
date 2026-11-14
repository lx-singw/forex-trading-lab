# Sharing diagnostics071 — offline preparation

The sealed070 attempt stopped at independent_controls. It consumed five commands
and two arms, recorded only the two pre controls, and attempted no scheduled
wait or saved log read. Cleanup was confirmed. Original066/069 command handling
replaces several different exceptions with the same fixed reason. The frozen
native outcome therefore cannot prove whether the probe guard, its clock
checks, the ten-second launch window, or the first wait budget failed.

Runtime071 preserves the six-command order, two arms, ten-second gate measured
after the full guard, five/35-second schedule, 36-iteration wait cap, existing
15-second wait tolerance, full uncached guards and all069 resource limits.
It records at most192 fixed diagnostic events and relative boot-clock durations.
Arm-to-ready, arm-to-probe-receipt, arm-to-window-check and probe-guard durations
separate post-arm work, command/UI delay and probe guard time. These measured
intervals describe elapsed time, not proof of the individual cause of delay.
No absolute clock, account, process identity, path or exception string is exported.

Each step has a fixed failure code; the first detected failure survives later
cleanup failures. Completed is false after clock, budget, guard, order, window,
control, cleanup or evidence failure. Extra clock samples consume the same
declared budget. Expiry or exhausted diagnostic/trace budgets never prevent
the one owned close attempt; malformed or missing cleanup proof cannot pass.
An opaque native/SDK call cannot be preempted by after-return checks.

This module has no native entry point, SDK import or market/order capability.
Tests inject the older064 matcher and temporary069 reservations as fixtures;
neither grants permission to reuse the consumed064 sandbox or069 dispatch.
Synthetic success is not native MQL/publication/ACK proof. Keep old source,
raw reservations without fabricated sidecars, dispatches, failures and070 audit.
The controller verifies those hashes and the source archive before diagnosis.

Next is separately declared fresh MQL/source/phase/build integration in
NATIVE-SHARING-072-PLAN.md. Do not weaken account/logon/hash/hold checks or
extend the Oct7 source. No new MT5 test is part of071. Keep033/035 diagnostic
failures, clock/cost/coverage/flags, consumed2025, reserved Nov–Dec2026 and
provider exclusions. Fresh/annual eligibility and orders remain false;
profit is not established.
