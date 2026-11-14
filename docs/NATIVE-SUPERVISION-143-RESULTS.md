# Native helper supervision142–143 results

Completed 5 November 2026. Two stages are complete:142 adds continuing native
helper health reports;143 connects them to the existing140 transition engine.
The Windows helper is real. Every account guard, context and acquisition
triple supplied in these exercises is invented. No MT5, account query, price
read, strategy evaluation or order occurred.

## Changes

The [142 protocol](HELPER-HEALTH-142-CONTRACT.md) reports the helper's own
sequence, monotonic timestamp, mains observation and acknowledged request
state. The owner also checks the actual child process. A one-time readiness
event cannot substitute for continuing samples. The helper and owner default
OFF and reuse the unchanged139 runner and141 containment implementation.

[143 transport](../src/forex_demo_lab/native_supervision_143.py) hash-checks
the selected binaries and launches the Windows owner through WSL interop,
without a shell. A bounded background worker exchanges job/challenge-matched
requests and retains causal receipt markers. Supervisor polling consumes the
cache without blocking on a native status read. Startup, round-trip and cleanup
waits are bounded; status faults initiate native cleanup. Duplicate samples do
not advance freshness. An input-pipe EOF also requests native shutdown.

The new143 supervisor supplies its own strictly checked initialization and
inherits140's transition methods unchanged. It supplies actual native status
through its port while138 still accepts only invented acquisition events.
Its snapshot explicitly separates native helper activity from invented
acquisition. Clear/close acknowledgements are required before its cleanup
status can be complete; forced exit cannot fabricate those acknowledgements.
Existing139–141 source files were preserved, as were all46 prior141 bindings
before the four handoff files were backed up and updated.

The reused138/140 journals retain their invented-event schemas. Actual native
transport packets and receipt times are preserved separately; the old journal
reader continues to report native supervision certification as false.

This143 prototype is limited to30-second jobs and512 bounded evidence packets.
The test entry point defaults OFF and has no quote or collection mode. The
underlying142 helper's1–14,400-second range does not authorize a new market
capture. No dates, broker settings or previously expired capture were changed.

## Results

121 Python tests passed, including22 new142/143 tests. Twelve C# shared-memory
checks passed without power requests. Four brief native Windows scenarios and
three real native-helper/supervisor exercises passed.

| Exercise | Observed result |
| --- | --- |
| Native sample progression | Helper sequence advanced; owner observed recent native samples |
| Exact helper terminated | Owner reported process loss; exit observed, no clear/close acknowledgement invented |
| Windows owner terminated | Its helper exited within the five-second wait; no managed cleanup receipt |
| Owner input pipe closed | Owner cancelled helper and acknowledged clear/close, exit and job closure |
| Healthy stream through supervisor | One explicitly invented triple acknowledged; ordinary cancellation and cleanup |
| New status samples held by test channel | Pending invented triple aborted on stale status; zero commits |
| Contradictory status injected by test channel | Pending invented triple aborted on protocol failure; zero commits |

The held/contradictory cases inject transport faults while the real helper
continues running; they are not observations of an actual mains failure or
frozen Windows process. Pure packet tests also cover binding, type, sequence,
clock, readiness and exact-exit failures. Default-off paths and actual-mode
REAL/CONTEST values in invented guards block launch.

No owned processes remained. Active power scheme and sleep/display hashes
matched before/after each native verification batch. Temporary SystemRequired
requests were used only during the brief helper tests. No permanent power-plan
write or execution-policy change was made. The global request list and actual
idle-sleep suppression were not verified.

The final three retained exercises were independently read offline: all native
request challenges matched their replies; recorded send/receipt times replayed
through142's decoder; supervision markers matched accepted health observations;
both journal chains reconciled; pending states were closed; commit counts and
stop causes matched expectations. The contradictory packet was independently
rejected. These checks do not turn the journals into market evidence.

Early development evidence is retained: a stale fixture initially supplied a
backward timestamp, a C# overload needed an explicit type, the WSL detection
probe used an unavailable proc entry, and the native C# client initially sent
CRLF instead of the required LF. Those were corrected before the final checks.
The passed Python exercise was repeated after adding receipt-time audit data;
the unchanged Windows owner/helper did not need rebuilding for that addition.

## Evidence and reproduction

- [Final Python checks](../reports/native-supervision-143/python-tests-final.txt)
  and [unit tests](../tests/test_native_supervision_143.py).
- [Windows build](../reports/helper-health-142/compilation-003.json),
  [slot checks](../reports/helper-health-142/slot-tests-003.json),
  [final process checks](../reports/native-supervision-143/windows-native-checks-002.json)
  and [corrected native-client build](../reports/native-supervision-143/nativechecks-compilation-002.json).
- [Three final exercises](../reports/native-supervision-143/native-run-002/results.json),
  [independent inspection](../reports/native-supervision-143/independent-inspection.json)
  and [verification](../reports/native-supervision-143/verification.json).

From the WSL repository, offline checks require no native launches:

```sh
PYTHONPATH=src:tests python3 -m unittest test_helper_health_142 test_native_supervision_143 test_helper_owner_141 test_supervision_140 test_acquisition_138 test_coverage_137 test_context_recorder_136 test_forward_eligibility_134
python3 scripts/native-supervision-143.py
```

The last command reports OFF. To explicitly repeat only the brief native
helper exercise, use the existing hash-bound build and a new output directory:

```sh
python3 scripts/native-supervision-143.py --enable-native-helper-tests --build reports/helper-health-142/compilation-003.json --output reports/native-supervision-143/native-run-NEW
```

The temporary Windows executables must still exist. There is no dependency
install, policy bypass, account setup or native market input in this command.

## Limits and next step

Health samples establish responsiveness and acknowledged request history,
not continuous power effectiveness. The native mapping and random challenges
provide correlation, not authentication against same-user tampering. Only the
helper is contained by the native owner's job; killing a WSL launching process
is not itself proof of Windows owner death. EOF handling was tested separately.
Arbitrary permanently blocked filesystem/API calls, physical mains loss,
suspend/resume, hard machine failure and every Windows/WSL version were not
tested. No restart appends to or promotes an unfinished journal.

Next integrate these guards with the existing read-only recorder boundary,
starting with invented quote inputs and failure injection. A real capture still
requires a new bounded collection plan and source/time/session/cost admission.
No new collection window is authorized by these helper results. The136 window
stays expired, October quarantined, November–December reserved and untouched,
and2025 consumed. Automated orders and real-money execution remain unavailable.
There are no new profit or strategy-performance results.
