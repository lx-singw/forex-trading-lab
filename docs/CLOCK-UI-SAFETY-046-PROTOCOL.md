# Capture budget046 design and offline test protocol

Declared before implementing the reusable reference authority/tests. This phase
does not compile/deploy/run MQL, connect an SDK, create a pipe, change MT5 state or
read quotes/history. Previous045 manifest ca66bddacebf572c112b98cfa03322ebdea9b6002dcd70a320fbf00f83504e2a
and all current bindings/archived members must verify before the new freeze.

Select a one-use local permission authority. A newly versioned native observer
must request permission on every enabled invocation, before SymbolInfoTick;
disabled returns before IPC and quotes. Permission never comes from inputs or
saved logs. Atomic issuance happens in one companion process under a lock, not
in independently initialized script globals. A unique exclusive phase reservation
is created/flushed before the authority starts; any existing, empty/corrupt or
symlink reservation rejects restart. No reset/refund/delete/replenish operation.
Missing/changed reservation during a request invalidates the running authority.
State changes to spent BEFORE request validation, guards, journal and response.
Lost response, failed quote, guard failure, cancellation and ambiguous outcomes
burn the allowance. A closed/dead helper cannot issue any further permission.

Fixed reference limits: one permission,900-second maximum session,2-second maximum
receipt validity, actualDEMO/USD/Algooff/connected/exactEURUSD/private stable
identity via existing guards, strict booleans/integers, exact32 lowercase hex phase
and64hex policy digest. Clock samples contain UTCms/monotonicns/system-uptime-ms;
reject backwards or malformed clocks, wrong fixed date or either expiry, including
the boundary. Client must recheck phase, date, uptime expiry and native account/
instrument immediately before its one quote, and original account/date guards
afterward. UTC/uptime agreement checks are bounds, not clock certification.
No account/server identifiers in reservation, journal, request or response.

Required offline tests: six repeated launch requests,32 simultaneous requests,
concurrent phase startup, disabled zero IPC/quotes, real/contest account rejection,
USD/Algo/connection/symbol/private identity failures and changes during grant,
expiry/date rollover/backwards clocks/invalid types, wrong/corrupt phase or policy,
missing/corrupt/permission-denied reservation, helper restart/close, journal errors,
lost response and quote errors without refund, late client permission and account
change before its quote. Check shared MQL pure receipt decisions with a C++ harness;
these are synthetic, not a native terminal proof. Full regression required once.

Native integration is a separate declared047 phase. Candidate transport is local
named pipes supported by MQL FileOpen without DLL enabling: owner/logon-session ACL,
reject remote clients, first-instance-only ownership, exact-size messages, bounded
server cancellation/cleanup. Reject missing/uncertain peer/ACL/protocol. Need native
no-market fixtures to establish framing, timeout and disconnection behavior before
an observation. A terminal-local global CAS alone needs separate initialization,
restart and durable-state protection; it is not chosen as the complete guard.

Limitations: this is cooperative budget enforcement for frozen artifacts, not a
defense against same-user code tampering, reservation deletion/rollback or malicious
clients. Atomic file creation/flush durability depends on filesystem/platform;
power-loss rollback is not claimed impossible. Across-process guards cannot prove
absence of an account switch-and-back between checks; within-invocation private
identity checks remain mandatory. Different terminal/data roots must reject phase
reuse; pipe peer validation remains unimplemented. Old042 remains prohibited for
reruns. No historicalUTC correction, strategy returns or qualification promotion.
