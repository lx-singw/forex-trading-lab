# Synchronization084 source and private interfaces — 2026-10-08

This is source and injected-interface preparation, with no native authority.
The two fresh MQL files implement a default-off synthetic reader and an exact
144-byte little-endian codec. The phase is84000000000000000000000000000001;
the date remains Oct8. Frozen083/R2 sources, original failing fixture evidence,
082 metadata observations, spent081 markers and075 reference artifact remain
unchanged. The old072 artifact cannot implement this source.

The wire layout keeps the083 challenge/ready/release/holding/closed semantics.
Bytes24–55 bind the complete source contract; bytes56–87 bind the future actual
candidate EX5 SHA256, rather than the historical075 reference. The episode and
sequence are exact, padding is zero, counters have finite caps, and all clocks
retain the2s freshness/10s start/30–31s close/250ms margins/60s episode/120s whole
limits. Requests carry zero hold times and have their own validation path.
Pending closed replies use kind5 and zero hold times; they are fresh responses,
not fabricated holding or closing evidence. The private episode and identities
remain ephemeral and are absent from reports.

MQL uses one local named pipe through FileOpen without DLL imports, and one
read-only synthetic file handle with FILE_SHARE_READ. It queries the actual
DEMO account type, USD, connected state, Algo Trading off, unchanged account,
terminal build6244/paths and supported EURUSD metadata under uncached guards.
No quotes/history/orders/credentials are read or written. It guards file IO,
property reads and pipe flush/seek operations before and after. Every acquired
handle receives one cleanup close even after rejection. Ready is accepted once,
release once, sequences are monotonic, and the synthetic bytes are a new fixed
84-byte pattern `(17*i+29)%256`. Response timestamps are sampled after request
receipt and after the actual synthetic open/close operations. The companion
cannot retimestamp or repair a response.

The official [FileOpen reference](https://www.mql5.com/en/docs/files/fileopen)
describes local named pipes and the flush/seek boundary between reads and writes.
The [FileReadArray reference](https://www.mql5.com/en/docs/files/filereadarray)
defines binary uchar array reads. These API descriptions do not establish our
native message mode, scheduling, error semantics or runtime compatibility.
MQL pipe reads/flushes can block: checking a clock after return cannot preempt
them. This reader closes on a timely closed challenge after30s; an absent or
late challenge can prolong the physical hold. A reported success requires the
actual close within31s. There is no guaranteed maximum hold or native deadline.

Python defines concrete access/share/creation specifications and a typed future
backend interface. It refuses native backends in this phase. Its owner exists
before factory entry, requires installation before acquisition, registers each
handle before any later exception, and closes once after interruption, expiry
or failure. Uncertain closes are counted and never retried or refunded. A native
implementation must retain any uncertain resources rather than treating them
as released. Bootstrap must create a new private root/fixture/pipe, never adopt
an existing root; write/read the exact84 bytes and verify their identity. The
future pipe must be local, user-only protected DACL, first-instance, reject remote
clients and bind the actual client PID/creation/session/logon/boot identity.

File metadata uses raw owner/protected-DACL/one allow ACE facts, exact access mask,
canonical final path, regular-file attributes, link count1, size/position and
volume/file-index/creation identity. Every metadata result also supplies the
current complete ancestor chain; reparses and changed private-root identity
reject after bootstrap too. These are injected facts, not observed Windows ACLs.
The companion publishes each original peer response to a separate CREATE_NEW
slot, closes the writer, checks its same identity through a READ/share-READ
held handle, and checks both signal and synthetic path identities through
metadata/share-READ|WRITE|DELETE handles. No synthetic-file seal is held during
the independent controls. Both write and delete must independently return actual
error32, between full guards inside the strict hold margins. Pre/post opens must
succeed; no control mutates the file. The matcher binds six ordered probes,
four original frames and exact reader counters/hold times; success remains
modeled_match only.

Concrete publication adds guards beyond the083 abstract model. The offline
guard cap is explicitly256 (MQL1024); all IO/open/close/metadata/read/write/poll/
wait/clock caps are declared in the source contract. Time limits are unchanged.
Fifty-millisecond guard scenarios are tested. Applying082's observed1611ms
value to every guard in this concrete path must reject stale publication before
release. The083 abstract24515ms critical result does not carry over. This is a
design constraint, not a newly measured native latency or an upper bound.

The complete local Python import graph and all MQL includes are hashed before
the frozen regression/evidence actions. Candidate build schema preserves the
actual compiler exit1 with zero errors/warnings, one compiler call, build6244,
exact source bindings and an independently hashed1–1048576-byte EX5. A source
contract is not a build or deployment grant. No compilation/deployment/SDK/log/
market/receipt/order action exists in this controller. A34-test development
check passed before the final ancestry/identity refinements; it is not the frozen
full-suite evidence. The final declared suite inherits083 R2 active_suite(),
retaining the original43 faulty tests as evidence and running their46 replacements.

Native sharing/publication/ACK, old070 failure cause and profitable edge remain
unproven.033/035, data clocks/cost/coverage, consumed2025, reserved Nov–Dec2026
and provider exclusions remain binding. No live toggle, real/contest account,
martingale, paid service, broker account, income or win-rate promise is added.
