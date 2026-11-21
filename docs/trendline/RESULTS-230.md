# Sprint 230 · Level B delayed-entry trial

22 November 2026. Following approval to test the variant, freeze the
development-only entry rule `TRL_H1_AFTER_DECISION_230_V1`. Use it as a
separate timing trial across the five initial strategy profiles and both
existing cost profiles. Use the first scheduled H1 open strictly after
the H4 decision is available. The decision time is the H4 publication
time supplied by the reviewed receipt or availability model.
[Qualification decision](RESULTS-229.md) · [Frozen strategy specifications](PROTOCOL.md)

## Trial rule

- Expire at the next scheduled H4 close. The selected H1 open must
  precede both expiry and the partition liquidation opening.
- Select the slot from the schedule before looking up prices. A missing,
  late or ineligible opening leaves the entry unavailable. Keep the
  selection fixed even when a later hour has usable data.
- Keep the setup, safety geometry, stop and target inputs from the
  original decision. Re-evaluate entry prices, spread, slippage and the
  existing price filters using the selected opening.
- Report a separate feasibility count against the existing threshold of
  60 eligible opportunities per strategy and cost profile. Keep this
  as a declared development trial and record it in trial history before
  any later study admission. `TRL_BRK3_DLY` is the separately declared
  missing-safety-line profile.
  [Entry and count semantics](PROTOCOL.md#c4-entry-and-data-level-semantics) · [Development counter](RESULTS-194.md)

## Counter and input

The Level B count uses `--delayed-entry` to select the trial. Reports
carry the explicit entry rule and schema
`TRL_PHASE10_DELAYED_ENTRY_COUNT_230_V1`. A reviewed historical
manifest for the variant must carry
`"entry_rule": "TRL_H1_AFTER_DECISION_230_V1"` and have its exact bytes
admitted. The loader rejects a manifest for the wrong entry rule before
opening price data. Source use, dates, receipt or availability model,
calendar, coverage and opening prices still require qualification.

```sh
PYTHONPATH=src python3 tools/signal_count.py bars DESCRIPTOR HOURS REPORT --tick-size TICK --delayed-entry
PYTHONPATH=src python3 tools/signal_count.py historical-input MANIFEST REPORT --delayed-entry
PYTHONPATH=src python3 tools/signal_count.py historical-count MANIFEST REPORT --delayed-entry
```

The `bars` command accepts fabricated development inputs. Use a fresh
report path for each command. The two historical commands require a
reviewed manifest. [Historical inputs and coverage](RESULTS-221.md)

## Timing comparison

Recompute the Sprint 226 calendar-only scenario from retained EV 2024
coverage metadata. In the clock cases the decision comes two seconds
after the modeled close. In the quote-dependent cases it comes two
seconds after the first scheduled opening, the earliest modeled quote
release. Require all expected H1 children and the selected opening's
row. Enforce next-H4 expiry and exclude the last scheduled H1 slot for
liquidation. Use a strict time comparison for the variant.

| Close model | Release model | Original potential slots | Delayed-entry potential slots |
| --- | --- | ---: | ---: |
| UTC bucket end | Clock | 52 | 1,577 |
| UTC bucket end | First possible quote | 0 | 1,577 |
| Ordinary session end | Clock | 52 | 1,577 |
| Ordinary session end | First possible quote | 0 | 1,577 |

These are coverage-adjusted scheduling ceilings for the 2024 scenario.
They establish potential time to act under the test assumptions.
Opening prices, setup and spread filters, and historical eligibility
remain open. The exact figures depend on the assumed decision time.
[Coverage metadata](RESULTS-224.md) · [Original timing scenarios](RESULTS-226.md)

## Verification and status

All 101 targeted tests passed. The fabricated historical bundle counted
one eligible BRK3 entry under each cost profile using a paired quote at
the later opening. Coverage also included a decision that arrives on an
hourly boundary, missing opening evidence, liquidation, expiry and
rejection of a mismatched manifest before price access. Independent
Python and JavaScript calculations agreed on the four timing cases.

The canonical Phase 10 status matches Sprint 229 byte for byte. Actual
counts remain unavailable pending a qualified EURUSD input for the
delayed-entry trial.
