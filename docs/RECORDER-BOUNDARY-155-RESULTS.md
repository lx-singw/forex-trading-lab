# Recorder155 — invented read-only payload boundary

15 November2026. Implements the first engineering slice from
[154 readiness](ELLIOTT-MT5-SOURCE-154-READINESS.md): associate invented context and
clock/quote/clock payloads with the frozen138 acquisition lifecycle and140
supervision guards.142's health decoder, also used by143, supplies compatible
observations. No Windows helper, MT5, account or native source is launched/read.

This is a Python-only invented boundary. It does not connect143's native port to
MT5, implement a native market adapter, compile/deploy an EA or start collection.
Recorder136, its source/configuration, dates, wire and previous results remain
unchanged. Trading/runtime and all46 frozen-control bindings also remain unchanged.

## Implemented boundary

`recorder_boundary_155.py` accepts only the frozen synthetic140 supervisor and a
sealed memory-source type containing declared reads. It has no source callback,
terminal path, SDK, native process or order option. Enablement and reconnect retry
default off. The CLI is off unless its fixed invented exercise is requested.

The source supplies invented pre/post guard observations for every read and a
separate final observation before commit. Typed DEMO, query success, identity
continuity, connection, Algo-off, non-tester, symbol/currency and clock predicates
are checked through138/140. These are simulated observations, not proof of the
open account. Explicit job-bound helper timestamps are required; missing timestamps
cannot be silently refreshed. Delayed readiness waits without reading the source.

The new payload journal155 joins the existing lifecycle138 and supervisor140
journals. For each context or clock/quote/clock attempt:

1. Check readiness/guards and required context. A triple requires a published
   context from the current segment and lifecycle spacing/capacity eligibility.
2. Persist an attempt before source reads. Check before and after every read.
   An individual failed post-read guard discards that value before payload staging.
3. Validate and persist the complete prepared payload. A later final guard failure
   leaves it uncommitted; the reader cannot publish it as a quote.
4. Recheck final supervision/guards, acknowledge the matching lifecycle event,
   then write the payload commit marker linked to that lifecycle digest. Only
   matching context/quote commit markers enter the reader's published collection.

Context is refreshed on the inherited elapsed-hour boundary and after reconnect or
clean lifecycle rotation. Reconnect is opt-in and retains138's global backoff/
attempt budget; it does not reuse old context. Source-label repeats, reversals and
raw integer flags remain visible rather than repaired or treated as fresh quotes.

The payload is a minimal invented context descriptor and hypothetical integer
price points, not136's full metadata/cost/native-double representation. Cost state
remains unknown. Clock brackets use one invented monotonic domain; source labels
are not certified UTC timestamps. No conversion to136/135 or strategy time is added.

## Storage and independent inspection

Payload frames are canonical, hash-linked, strictly typed and smaller than4096
bytes. The single payload file is capped at1MiB. Its allocation plus the bounded
supervisor journal is reserved outside the lifecycle journal's allowance, keeping
the combined journal allocation within128MiB. Lower test caps never enlarge it.
Writes reserve bytes first, require a full write and flush/fsync acknowledgement,
and poison the payload writer on failure without refund, append or retry. Control
journals retain their own bounded stop/cleanup semantics after payload failure.

The reader independently parses all three journals and checks jobs, lifecycle
references, attempts, slots, contexts, marker brackets and ordering. Partial tails,
pending payloads, incomplete control prefixes and lifecycle commits lacking a
payload acknowledgement stay explicit. Missing/corrupt dependencies reject.

A deliberate failure between lifecycle commit and payload commit yields zero
published payload triples plus one unpublished lifecycle commit. Conversely,
complete commit bytes may be present even when the producer lost its success
return: reader counts describe records present, not proof that the caller received
success or that bytes will survive a machine failure. `durability_ack_proven` is
false. Neither writer nor reader provides resume; a fresh job cannot append to an
old file or claim cross-job identity. Repeated stop calls preserve the original
failure cause and do not write more payload bytes.

Hashes establish consistency, not producer authentication. A test explicitly
demonstrates that self-consistently rewritten values can still parse; they never
become qualified market data. This is not a security sandbox against same-user
Python/file manipulation or proof of true helper/power/account state.

## Verification and examples

**146 targeted checks passed together, zero failures/errors, in16.544seconds:**33
new155 checks and113 existing138/140/142/143/136/145 checks. Recorded sources remain
unchanged during the final run. All inputs are invented, including143's scripted
channel tests. No native process, account query or actual quote read is performed.
Unrelated earlier strategy suites are not rerun or added to this count.

Nine fixed exercises run the public CLI and retain their physical journals:

| Exercise | Expected observation |
| --- | --- |
| Default off | No source/helper/journal activity |
| Clean repeats | Three committed triples; repeated/reversed source labels retained |
| Post-read guard loss | No published quote; queried value discarded |
| Stale final helper status | Prepared payload never published |
| Opt-in reconnect | New segment/context before the next published triple |
| Source failure | Attempt retained and stopped without retry |
| Missing payload acknowledgement | Pending prepared payload and explicit unpublished lifecycle commit |
| Clean rotation | New lifecycle segment requires fresh context |
| Health protocol | Invented142 packets decoded into guarded observations |

Unit checks also cover exact status-age equality, stale/replayed status, REAL/
CONTEST/unknown/mislabeled modes, identity changes, owner/helper/power loss, context
refresh, deadlines, spacing, source type/privacy rejection, open/write/short-write/
flush/fsync-ack/close/capacity failures, no writes after poison, final ACK uncertainty,
truncated journals, rehashed semantic corruption, stopped-state idempotence and
fresh-job restart. The old136 reader rejects155 bytes; study/order gates stay shut.

```sh
PYTHONPATH=src python3 scripts/recorder-boundary-155.py
PYTHONPATH=src python3 scripts/recorder-boundary-155.py --exercise-invented --output NEW-EXERCISE-DIRECTORY
PYTHONPATH=src:tests python3 -m unittest test_recorder_boundary_155 test_acquisition_138 test_supervision_140 test_helper_health_142 test_native_supervision_143 test_context_recorder_136 test_elliott_study_145 -v
```

The [portable evidence](evidence/recorder-boundary-155/README.md) includes final
verification005, its test log, source hashes, invocation, pre-exercise declaration
and compact outcomes. Full journals, source archive and exercise reports remain
under ignored `reports/recorder-boundary-155-verification-005/`. Earlier source-bound
snapshots remain separate and are not included in the final test count.

## Remaining work

Review the native binding/transport feasibility and full raw context/quote format
before any native compilation or runtime exercise.143's actual native port is not
accepted by this pure155 boundary. Fresh wall-clock observations, native IO,
source-specific permission, current actual-DEMO/identity checks and a separate
bounded date/run plan still need proof. Blocked filesystem/API calls, physical
power loss and suspend/resume cannot be preempted or certified by these tests.

No source/provider or new capture dates are assigned.136 remains expired; October
quarantine, consumed2025, reserved/untouched November–December and closed routes
remain. The qualified historical runner, broader Elliott acceptance, viewer/visual
review and native execution reconciliation remain incomplete. All16 actual-market
cells have unavailable/null results; automated orders and real-money execution
stay unavailable. There is no profitability or true tick-completeness result.
