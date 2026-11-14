# Bounded no-market MQL fixture048 — next, not executed

Use047's compiled no-market fixture only after its preparation/checks seal verifies.
It contains no SymbolInfoTick/history/order API. Date is fixed2026-10-07; stop on
expiry. Any new dated artifact requires its own reviewed/frozen derivation, not
automatic retargeting. Old042 remains prohibited.

First implement/test/freeze a new companion lifetime adapter.047's2-second
ConnectNamedPipe wait is appropriate for programmatic fixtures but too short for
manual UI steps. Allow a bounded pending connection within a900-second companion
session; after connection retain2-second IO/receipt bounds, drain cancellation,
reject date/account/instrument/peer changes before granting. Do not poll quotes.
Require interactive stdin before reservation or SDK connection, one already-running
terminal session, actualDEMO/USD/Algooff/connected/exactvisibleEURUSD/private stable
identity. Bind exact terminal image/process creation/logon/session/data-root and
compiled EX5. The actual MT5 peer has not been tested by047's Python fixtures.

Deploy exclusively into a new owned Scripts subfolder; never overwrite unrelated
EAs, grants or settings. Do not launch/login/switch accounts or enable Algo/DLLs.
Use an exclusive canonical phase reservation and consumption journal; never reset
or replenish on helper death, cancellation, lost reply or fixture error. The
server must own the unique local endpoint first and verify the actual MT5 client.
MQL's independent server-PID authentication remains unavailable without DLL imports;
report the cooperating-owner assumption rather than claiming adversarial protection.

At most three manually armed fixture invocations: (1) ExerciseTransport=false,
reason17/requests0; (2) true, one new authenticated-server grant, valid receipt;
(3) true once again after the server closes, expected missing-pipe rejection and
no second grant. All native quote/order counters must remain0. Each step requires
the preceding exact filtered native log proof and companion guards. Read only
bounded appended FXDL_PIPE047 closed-schema records; no account IDs/whole logs.
Stop on extra/malformed/missing records, expiry, timeout or unexpected permissions.

Verify native MQL FileWriteArray/Flush/Seek/ReadArray behavior including the85-byte
read bound for an84-byte reply; Windows client tests do not certify MT5 framing.
Treat native error/partial/extra data uncertainty as rejection. Preserve any
unexpected successful repeated grant or native error; no rerun to erase failure.
No real quote observer may be activated until this fixture evidence passes and a
separate dated capture plan freezes actual quote budget enforcement.

Preserve all047 revisions/stops and old six045 captures/044 timeout. Clock/coverage/
cost/flags/033/035 failures and consumed2025/reservedNov-Dec2026/provider stops remain;
fresh/annual eligibility/orders false. No strategies, returns or timestamp correction.
