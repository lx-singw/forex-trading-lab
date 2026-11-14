# Acquisition138 implementation and results

Completed 2 November 2026. Implemented the invented-data acquisition lifecycle,
bounded segment journal, independent journal reader and repeatable command-line
exercise. No native collector, power helper, future dates, market input option
or execution integration was added.

The lifecycle starts OFF. Enablement and reconnection both default false.
Invented guards model actual account enum checks and continuity; real, contest,
unknown or changed account state, Algo Trading on and unsafe clocks stop the
job even when it is disconnected. These inputs do not prove that an actual
account was queried. Native integration will need its own real API checks.

Disconnection/sleep interrupts and aborts any pending quote triple. Opt-in test
recovery has at most three attempts across the entire job, with5/30/120-second
backoffs. It creates a new hash-linked segment and requires new context before
another triple. Hourly context refresh uses elapsed markers. Job duration
includes waits and stops at the exact budget; polling cannot catch up faster
than1s between starts. Account/clock/storage faults never trigger reconnection.

The event journal creates exclusive new directories and files. It stores
fixed-schema enum events, markers and counters, with no quote values, account
identifiers, credentials or arbitrary messages. Frames are digest linked;
files/jobs/segment counts have fixed caps. Complete triple capacity and control
closure space are reserved before recording. Full-write and file-level fsync
acknowledgements precede progress changes. Short writes, flush/fsync failures,
close/open failures and exhausted capacity poison the journal without retry.

A stopped/crashed job cannot be reopened to append. The reader preserves a
valid prefix's pending triple or partial final frame, rejects missing middle
boundaries and corrupt/rehashed state transitions, and never grants resume.
A new job cannot claim the old job's account continuity. A complete commit
frame can be present after an invented sync failure even though the running
lifecycle did not acknowledge it; the reader explicitly does not certify
durability acknowledgement. No orders consume either representation.

## Verification

**67 tests passed, including24 new138 tests.** The unchanged137,136 and134
tests were included. New tests exercise actual-enum guard decisions before and
after invented reads, interrupted pending triples, exact retry/deadline/spacing
boundaries, elapsed context refresh, clock rollback/invalid markers, before-
triple rotation, discarded pre-boundary context, file/job caps, exclusive
creation, symlink refusal, partial/short writes, sync/close/open failures,
crash prefixes, separate restarts, corrupt semantics and24 generated transition
paths checked against the independent reader. CLI/library JSON agrees under
normal and optimized Python. No genuine account or market data is used.

One initial test incorrectly stopped its driver at ordinary rotation before
refreshing context; it had not yet reached the byte cap it was meant to test.
The driver was corrected, the failure retained, and the final suite passed.

The deterministic built-in exercise produced:

| Invented scenario | Final state | Segments | Acknowledged triples | Retry attempts |
| --- | --- | ---: | ---: | ---: |
| Clean rotation, deliberately small files | stopped | 20 | 40 | 0 |
| Sleep/reconnect with a rejected pending triple | stopped | 2 | 2 | 1 |
| Retry exhaustion | stopped | 1 | 0 | 3 |
| Independent restart after retained crash prefix | stopped | 1 new job | 0 | 0 |

These are software outcomes, not quote counts from a feed, trades or profit.
The small file limit deliberately forces frequent rotation in the exercise;
it is not the proposed native collection cadence.

## Remaining work

File IO and injected failures were tested in WSL temporary directories. Actual
process termination, power loss, directory-metadata durability, blocked OS
calls and Windows/MT5 flush semantics have not been validated. File fsync is
not a guarantee against every loss or storage failure. Native account checks,
source/receipt clocks, session evidence, cost qualification and quote payloads
remain outside138. The expired136 source and saved October captures were not
renewed or changed; November–December stays reserved/untouched.

Next implement and separately test a bounded, temporary Windows keep-awake
helper, including release on cancellation, failure and process exit. It must
not modify permanent power plans or start MT5/data collection. A later native
adapter will still require explicit dates, partition rules and its own tests.
Automated orders and real-money execution remain unavailable.

To run the invented exercise from the WSL repository:

```sh
python3 scripts/acquisition-138.py --format markdown
python3 scripts/acquisition-138.py --format json
PYTHONPATH=src:tests python3 -m unittest test_acquisition_138 test_coverage_137 test_context_recorder_136 test_forward_eligibility_134
```

Sources: [lifecycle](../src/forex_demo_lab/acquisition_lifecycle_138.py),
[journal and reader](../src/forex_demo_lab/segment_journal_138.py),
[contract](ACQUISITION-138-CONTRACT.md).
Evidence: [test output](../reports/acquisition-138/final-tests.txt),
[invented exercise](../reports/acquisition-138/invented-demo.json),
[verification](../reports/acquisition-138/verification.json),
[retained initial test failure](../reports/acquisition-138/initial-test-failure.json).
