# Broker-free snapshot collector104

This is an invented adapter/journal model with a market-shaped schema. It has
no broker connection, SDK/native adapter, order API or strategy execution. Its
metadata always says invented and `synthetic=true`; raw source clocks and data
eligibility remain unverified.103 qualification flags are never loaded as runtime
permission.102 and all old collectors remain unchanged.

From the repository in WSL, choose a new directory with an existing parent:

```sh
python3 scripts/snapshot-collector-104.py demo /tmp/my-snapshot-model
python3 scripts/snapshot-collector-104.py inspect /tmp/my-snapshot-model/observations.sqlite
python3 scripts/snapshot-collector-104.py inspect /tmp/my-snapshot-model/stopped.sqlite
python3 scripts/snapshot-collector-104.py inspect /tmp/my-snapshot-model/pending.sqlite
```

Creation refuses existing files/directories. The demonstration creates three
SQLite journals: an eight-read example with an explicit restart and two recorded
model decisions, a stopped account-change example, and an unfinished attempt.
The latter two reject acquisition after reopening. No prices come from a provider.

The collector accepts exactly the stored `ReplaySource` and `ReplayClock` model
classes, rather than SDK objects or callbacks. Private guard identity stays in
memory and is absent from records. `connect_broker()` always raises
`broker_entry_disabled`. Python source/object tampering is outside this model's
trust assumptions; type checks are not hostile-code isolation or native admission.

An attempt is committed before any modeled read. Guard failures before the read
make zero quote calls. Read-boundary UTC/monotonic clocks surround the acquisition;
an after guard and guard-completion clock precede the outcome commit. After guard
or clock failure discards the quote, retaining fixed codes and a persistent stop.
An outcome write failure rolls back the outcome and leaves the prior attempt
pending. Resume can inspect that state, but cannot start another collector.
There is no automatic reconnect, retry, pending-attempt completion or latch reset.

Raw seconds/milliseconds, native float hexadecimal encodings, declared Decimal
text conversion and original allowlisted flags are separate from receipt clocks.
Every attempted poll is retained, including missing/invalid results and repeated
snapshots. Equal-time changed observations remain distinct. Unknown bits are
preserved. Gaps/reversing raw labels are diagnostics, with no interpolation,
assumed timezone subtraction, unique provider tick ID or complete-stream claim.
Repeated-snapshot duration is not quote age or executable liquidity.

Restart creates a new monotonic segment and a restart-gap marker. The committed
event sequence, total attempt budget, raw source high-water mark and wall-clock
ordering survive. Cross-segment monotonic subtraction is forbidden. Private
identity continuity across process restart is not proven or serialized. Model
decisions expose only earlier guarded, committed observation sequences; later
recovered invented history is visible only to a later decision. This is a causal
visibility exercise, without signals, fills or P&L.

Default bounds:120 total attempts per journal,1,024 events,60,000ms per session,
2,000ms gap diagnostics and500ms wall/monotonic jump tolerance. These are frozen
invented test parameters, not market-calibrated quality rules or renewed legacy
runtime allowances. The policy/file caps and full-history replay keep this finite;
throughput, rotation and recovery from actual power loss remain unproven. A late
read return is rejected; the collector cannot guarantee aborting an in-flight
native call. No such native call is implemented here.

SQLite commits each event/head atomically and verifies schema, canonical metadata,
history decisions and hash chain on resume/append. Hashes prove local consistency
under this model, not source identity, actual account state, trusted clocks or
authenticity of an older valid snapshot. The tests and CLI run in WSL; there is
no Windows MT5 integration claim. Source permission, safe attachment and fresh
runtime/account/clock evidence still gate any future connection. Automated
orders remain off and real-money execution unavailable.
