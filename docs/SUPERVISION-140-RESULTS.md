# Offline supervision140 results

Completed 3 November2026. Connected a strictly synthetic helper port to the
existing138 lifecycle through a new default-off supervisor. The supervisor
has no native helper path/process option and reads no prices. Existing138
and139 source/evidence bindings were preserved and rechecked.

Recording cannot start on a helper-start acknowledgement alone. It requires
matching job-token, liveness, create/set/readiness and mains observations,
with a valid marker at most1s old. Readiness may take up to10s; the exact
timeout rejects a late signal. The overall job budget includes startup,
even though138's own origin begins after readiness. These markers are
invented monotonic observations, not source timestamps or UTC certification.

The supervisor rechecks helper/owner status at context and triple boundaries,
including after modeled reads. Helper exit, lost readiness/power, protocol or
binding failure, stale/reversed/future observations, owner loss, guard faults
and expiry stop recording. Pending triples abort through138's public stop
API. The helper is not restarted; ordinary138 network retry still requires
a valid helper and fresh context in the new segment.

A separate exclusive, bounded, file-synced journal records typed supervisor
transitions and the lifecycle's acknowledged head/counter. The specific
helper/owner cause lives in this journal;138 may record the external stop as
cancellation. Failure to persist supervision still stops138 and attempts
cleanup. Cancellation-request and exit-confirmation acknowledgements remain
separate, and unsuccessful/unknown cleanup is not called complete. A new
supervisor cannot overwrite or append a prior journal.

The independent reader validates frame digests, chronology, transition order,
stop-cause consistency and the linked lifecycle prefix. It distinguishes a
fully present but unacknowledged138 commit after an injected sync failure
from138's acknowledged counter. Present frames, even with valid links, do
not certify fsync acknowledgement, source authenticity or power release.
Partial supervision tails stay explicit and never permit resume.

## Verification

**91 tests passed, including24 new140 tests.** The prior67 tests for138,137,136
and134 were included. New tests exercise start-vs-ready gating, delayed/late
readiness, exact timeout/status-age boundaries, contradictory/foreign/future
reports, reversed markers, owner/helper loss during pending work, before/after
context checks, actual-enum guard decisions using invented observations,
overall duration including startup, failed start, cleanup acknowledgements,
network reconnect, supervisor/lifecycle sync faults, short writes, close
failure, restart collisions, rehashed invalid order/cause/head links, and
deterministic CLI/library output under normal and optimized Python.

The built-in exercise produced:

| Invented scenario | Stop cause | Acknowledged triples | Cleanup confirmed in model |
| --- | --- | ---: | --- |
| Delayed readiness then successful observation | cancelled | 1 | true |
| Helper exit during pending triple | helper_exited | 0 | true |
| Owner loss during pending triple | owner_lost | 0 | true |
| Startup timeout | helper_readiness_timeout | 0 | true |
| Failed helper start | helper_start_failed | 0 | true |
| Network reconnect with fresh context | cancelled | 1 | true |
| Unconfirmed helper exit during cleanup | cancelled | 1 | false |

All seven final journals reconcile to their138 acknowledged prefixes. The
counts are invented acquisition triples, not market ticks, orders or trades.
The cleanup flags are simulated responses, not Windows power API receipts.
No native helper, terminal, account query, quote read or power API call was
performed. Source hashes stayed unchanged during verification;28 prior139
source/evidence bindings were unchanged before updating the four handoffs.

## Limits and next step

This is the offline supervision boundary, not actual Windows supervision.
The139 native readiness event acknowledges a past SetRequest;140 does not
turn that event into an ongoing power-effectiveness certificate or fabricate
a heartbeat from it. Native IPC/observation freshness, helper-exit handling,
actual supervisor process-death containment and blocking-call behavior remain
unimplemented. Owner loss here is a supplied observation: a model cannot
continue executing cleanup after its real process has died.

Next implement a native Windows supervision transport for the existing
helper, with explicit child lifetime ownership and cancellation/readiness
events. Test brief helper-only launches, real owner termination and retained
invented acquisition journals. Keep native quotes, MT5, future collection
dates and reserved prices unavailable during those tests. A separate source/
clock/session/cost qualification path and sufficient observed history are
still needed for strategy evaluation. No profitability claim follows.

October remains quarantined, November–December reserved/untouched and2025
consumed. The136 window stays expired; automated orders remain unavailable.

Reproduce from the WSL repository:

```sh
python3 scripts/supervision-140.py --format markdown
python3 scripts/supervision-140.py --format json
PYTHONPATH=src:tests python3 -m unittest test_supervision_140 test_acquisition_138 test_coverage_137 test_context_recorder_136 test_forward_eligibility_134
```

Sources: [supervisor and reader](../src/forex_demo_lab/supervision_140.py),
[fixture](../src/forex_demo_lab/supervision_fixture_140.py),
[contract](SUPERVISION-140-CONTRACT.md), [tests](../tests/test_supervision_140.py).
Evidence: [test output](../reports/supervision-140/final-tests.txt),
[invented exercise](../reports/supervision-140/invented-demo.json),
[readable exercise](../reports/supervision-140/invented-demo.md),
[verification](../reports/supervision-140/verification.json).
