# Sprint 193 · Disabled native contract and Phase 9 acceptance

18 November 2026. The Tori native contract compiles with MetaEditor.
Its script entry point is a no-op and its order availability function
returns false. The native snapshot reader uses `ACCOUNT_TRADE_MODE`
and compares it with `ACCOUNT_TRADE_MODE_DEMO`. Identity fields used
for continuity are held in memory. The offline C++ harness exercises
the same contract with invented observations and an isolated fixture
journal.

## Observed fault outcomes

| Case | Observed result |
| --- | --- |
| Entry, tightening, cancellation and emergency closure | The account is checked at preparation and again after intent readback. REAL, CONTEST, unknown modes, identity changes, failed queries and disconnection all block the simulated action. |
| Admission and intent readback | Only a qualified Level Q request within its approved size can stage an entry. A loss pause blocks new entries. Missing persistence, a different saved size, and a copied offer all fail the single-use dispatch check. |
| Restart and ambiguous acknowledgement | Separate processes reopen the same fixture journal after intent persistence and after a simulated send with no acknowledgement. Both retain the reservation until fresh owned evidence resolves the matching intent. Old, incomplete and mismatched evidence cannot release it. |
| Owned partial fills | A four-unit fill with six units pending stays within the ten-unit reservation. Protection covers every filled unit and the pending remainder carries its stop. A completed cancellation can leave the protected hold in place. Tightening applies strictly in the protective direction for LONG and SHORT. |
| Protection failure | Missing or incomplete stop coverage latches a halt. The simulated path reconciles cancellation of the remainder before allowing emergency closure of the held units. An ambiguous emergency acknowledgement blocks a repeat, and the halt survives a flat restart. |

The journal stores the intent revision, side, volume and stop in exact
integer units. Observed position and remainder quantities update as
inventory arrives. The unresolved intent keeps its original payload
until an observation resolves it. The fixture exercises process restart
with a single writer. MT5 transport, durable terminal integration,
ownership reconciliation with actual records and deployment are Phase 12.

## Verification

All 46 targeted tests passed. Six new C++ fault scenarios ran through
the Python test runner, alongside 40 retained research and study-gate
checks. The isolated MetaEditor compile finished with zero errors and
zero warnings.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_native_193 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_verification_192 test_trendline_study_165 -q
```

Phase 9 software acceptance is complete on invented evidence. Phase 10
starts with development-only signal counts and requires admitted
historical data for its feasibility gate.
[Verification matrix](VERIFICATION.md)
