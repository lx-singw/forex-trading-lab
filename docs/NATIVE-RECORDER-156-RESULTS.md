# Native recorder156: closed-entry port and compilation

15 November2026. A distinct native MQL read binding is implemented and compiled.
It is **not deployed, run, connected to an account or admitted as market data**.
This advances disabled-adapter preparation under the approved [144 plan](ELLIOTT-EXPANSION-144-PLAN.md).
It does not complete historical study or native operational readiness.

## Delivered boundary

`mt5/Scripts/ForexDemoNativePort156.mq5` uses native read APIs and terminal-local
challenge/reply files. It does not use the closed090 DLL/pipe route, Python MT5
SDK, FILE_COMMON, network access, order APIs or history APIs. Canonical136 and its
26–30 October expiry are unchanged. Selected read/serialization functions are
derived from136 into this separate source; its date authority is not copied.
Unchanged107 contributes the actual-account decision and quote validator;
unchanged128 bounds commission payloads.107's dated clock function is not called.

Entry has two independent stops: `CollectEvidence=false` by default and
`RunGranted156()` returning false unconditionally. Even setting the input true
cannot open a job or read account/price information in this build. No date,
provider, account, source permission or collection window is assigned. A future
admitted run needs a separately reviewed, frozen build and bounded run plan;
changing an input or folder is not a grant.

The dormant native path checks the actual `ACCOUNT_TRADE_MODE_DEMO` constant,
connection, non-tester mode, Algo Trading off, USD account, visible EURUSD and
private account continuity. Login/server stay in memory; exported rows and status
contain no account identifiers. Native enums are used by name: the invented138
account-mode encoding must not be substituted. Guards and helper leases bracket
every source query. A failed after-read check discards its local result.

The prototype permits one context and one clock/quote/clock triple, bounded by
30 seconds,128 source-query groups,512 lease requests,4096 bytes per written
frame and a combined1MiB reserved budget. The budget includes request writes,
512 reserved bytes for each reply and the output journal. Unused reservations
are never refunded. Guard API reads are additional to source-query groups.
The worst declared context has104 source groups including the final triple.
Blocking APIs/IO cannot be preempted by these elapsed-time checks.

## Raw payload and transport

The context contains33 scalar fields: leverage,11 integer symbol properties,
20 double properties and margin currency. It also records weekly session API
responses (seven days, at most nine indices each), commission rules (at most
eight rules,16 tiers each,128 tiers total), buy/sell margin factors and bounding
clock samples. Failed/empty API results remain explicit; they do not establish
historical closures or zero trading costs.

Quote records retain native seconds/milliseconds, bid/ask/last, volume, flags and
real volume. Doubles preserve their native64-bit representation. Clock records
retain all six clock fields used by136 and before/after/guard markers. No UTC
offset, historical cost or executable-price qualification is invented.

Files live under the explicit job folder
`MQL5/Files/ForexDemoLab156/Job156-<32 lowercase hex characters>/`:

| File | Purpose |
| --- | --- |
| `Request0001.txt`, etc. | One bounded job/ordinal/challenge request |
| `Reply0001.txt`, etc. | Matching raw helper sequence/ticks and eight health bits |
| `NativePort156.txt` | Digest-linked diagnostic frames with `FXDL_NATIVE_PORT156_V1` header |

Each reply is at most512 bytes. ASCII syntax, canonical integers, job, ordinal,
challenge, sequence and clock direction are checked. Native age plus the entire
MQL request/reply round trip counts against a one-second freshness limit;
equality is allowed. A repeated sample retains its original MQL observation
marker. Its timestamp cannot be renewed by polling. No Windows/WSL/MQL epoch
equivalence is assumed.

`recorder_lease_156.py` supplies a strict codec and a one-request file service
compatible with143's channel interface. It does **not** launch a helper, discover
a terminal or implement an owned worker loop. Its exercised receipt markers are
caller-supplied invented values. Actual measured-clock/owned-channel integration
is outstanding. The service writes replies exclusively, checks short writes,
requests fsync and permanently poisons itself after a fault. Existing/partial
files are retained; there is no retry, overwrite, append or resume.

This is a separate diagnostic wire format. It is not an accepted source for the
invented155 boundary or145 market study. There is no completed native semantic
journal reader,138/140 commit integration or native dataset admission here.
An `E` frame only marks the writer's completion; it grants no market eligibility.

## Verification

The isolated MetaEditor build used version5.0.0.6320 and produced **0 errors,
0 warnings**. Canonical/staged hashes match; compiler and EX5 hashes are retained
in [portable evidence](evidence/native-recorder-156/README.md). The build directory
is outside terminal folders. No script/EA was deployed, terminal launched or
terminal setting changed. An unsigned UNC-script policy initially prevented
starting the wrapper. A process-scoped PowerShell invocation then ran the compiler;
no persistent execution-policy setting was changed.

The shared native decisions compile under g++17 with `-Wall -Wextra -Werror`.
Tests exercise the actual named demo constant, rejection of contest/real/unknown
modes, identity/connection/Algo/tester faults, deadline and capacity boundaries,
pending queries, stale/changed/replayed helper samples, missing health bits and
fresh restart state. Python tests exercise request binding, bounded decoding,
exclusive creation/races, links, partial writes, uncertain fsync acknowledgement,
private-error suppression and permanent fault state. Source checks verify entry
ordering, query bracketing and absence of order/history/import routes.

**170 targeted checks pass:24 new and146 existing, zero failures/errors/skips.**
The final targeted test count and source bindings are recorded in
[verification summary](evidence/native-recorder-156/verification-summary.json).
These checks use invented inputs. They are not an MT5 runtime, physical power,
current account, feed, timing or durable-storage test. Related136/138/140/142/143/
145/155 regressions run together; unrelated trading suites are not claimed.
All20 prior155 file bindings and46 frozen-control bindings remain unchanged.
Final verification003 follows the folder/close revision;001 is retained separately.
Verification002 stopped before tests because its basename resolver omitted the
config directory. Its preflight failure is retained;003 adds config resolution
without changing a canonical source or the expected tests.

```sh
PYTHONPATH=src:tests python3 -m unittest test_recorder_lease_156 test_recorder_boundary_155 test_acquisition_138 test_supervision_140 test_helper_health_142 test_native_supervision_143 test_context_recorder_136 test_elliott_study_145 -v
```

The compile wrapper is `scripts/compile-native-port-156.ps1`. It copies only its
five declared sources into unique non-terminal staging and preserves compiler
diagnostics under ignored reports. It never installs the EX5 into MT5.

## Limits and next work

MQL sandbox placement and hash chains do not authenticate a producer or prevent
same-user tampering. Job/challenge tokens bind messages; they are not credentials
or cryptographic peer authentication. MQL's existence check plus read/write open
has not established atomic create-new behaviour. Native partial-file, sharing,
flush, blocked-call, suspension, account-switch and physical power behaviour need
runtime evidence. Python link checks do not certify Windows reparse/ACL safety.
FileFlush is not proof of crash durability. Multiple native account reads are not
an atomic account snapshot. No operational guarantee follows from compilation.

Next implement a bounded owner/relay runner with measured receipt times and an
independent native-journal checker, starting with invented IO/process faults.
Only after source/date/run qualification should a separately scoped native read
exercise be considered. Preserve this closed156 build; do not renew136, bypass
closed routes or silently choose current acquisition dates.

October remains quarantined,2025 consumed, November–December2026 reserved and
untouched,2024 seen development evidence and2020–23 unqualified. Qualified
historical admission/runner, broader Elliott acceptance, viewer/visual review
and native reconciliation remain open. All16 actual-market comparison cells
remain unavailable/null; automated orders and real-money execution remain
unavailable. No profitability, win-rate or income conclusion is drawn.

## Primary API references

The feasibility review uses official MQL documentation: sandbox/file modes
([FileOpen](https://www.mql5.com/en/docs/files/fileopen)), buffered writes
([FileFlush](https://www.mql5.com/en/docs/files/fileflush)), MQL program-relative
timing ([GetMicrosecondCount](https://www.mql5.com/en/docs/common/getmicrosecondcount))
and actual account enums
([account properties](https://www.mql5.com/en/docs/constants/environment_state/accountinformation)).
The local-file challenge protocol is our design inference from those APIs; the
documentation does not verify this implementation's runtime behaviour.
