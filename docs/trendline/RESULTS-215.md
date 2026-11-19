# Sprint 215 · Development count preflight

19 November 2026. The historical development count has two current
dependencies. It needs an independently qualified EURUSD source with
reviewed timing and opening semantics, and it needs a counter input path
that admits that historical source. The existing counter accepts invented
inputs. An unassigned validation period can remain open during a
development-only count. [Signal counting rule](PROTOCOL.md#c6-signal-counting) · [Chronological source review](RESULTS-199.md)

## Preflight change

The `status` command now reports `TRL_PHASE10_STATUS_215_V1` with the
existing `development_preflight_issues` field scoped to the count and a
`later_study_preflight_issues` field carrying the remaining study checks.
Source permissions, input and calendar lineage, development and warmup
coverage, declared spread, price and availability evidence, and independent
qualification remain count requirements. Cost-profile contradictions still
require review. The existing price kernel applies the frozen base and
adverse entry cost assumptions to the count. [Frozen cost decisions](PROTOCOL.md)

Phase 11 retains validation readiness, broker commission and financing,
contract and margin evidence, paired exits, the 28-cell budget, controls,
historical trial history and inference requirements. Level B can support
Phase 10 with qualified input. A later Level Q study must meet its recorded
receipt requirements. The count also needs a valid endpoint when provided.
Level B uses its documented last scheduled H1 default if the endpoint is
unassigned. Level Q retains its explicit cutoff check. [Counter contract](RESULTS-194.md)

Consumed, quarantined and protected dates still block development and
warmup access. The preflight also flags a development or development
warmup interval that intersects a declared validation interval. Adjacent
half-open intervals remain valid. The full study still checks chronology,
validation exposure and acceptance of all study cells. [Date and exposure rules](PROTOCOL.md#data-costs-and-study-admission)

## Evidence and verification

The canonical metadata report lists 21 Phase 10 issues and 20 later study
issues. A separate metadata example supplies the proposed 2021–2022
development dates and 2020 warmup from Sprint 199. It leaves validation
unassigned and exposes the outstanding source, coverage, opening-model
and historical reader requirements. Both reports have `UNAVAILABLE` and
null actual counts. The plan hashes and original study issues reconciled
independently. All 59 targeted status, timing, study, count and coverage tests
passed. The reports used metadata only. [Candidate dates](RESULTS-199.md)

```sh
PYTHONPATH=src python3 tools/signal_count.py status config/trendline-study-v1.json new-status.json
```

The updated status is metadata only. The next implementation dependency is
a historical reader that verifies the admitted source and development scope
before opening the corresponding prices. A receipt from this preflight
supplies no admission authority.
