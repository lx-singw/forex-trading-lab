# Sprint 178 · Disabled DLY replay

18 November 2026. The declared `TRL_BRK3_DLY_E1` profile now supports
invented replay with explicit opt-in. The selected BRK3 break consumes
its group at the trigger. If safety is already valid, the existing E1
path uses that close. If safety is missing, DLY records a wait with its
original action ray, close, group and deadline.

The tenth scheduled H4 close ends the wait before safety selection.
Earlier observations invalidate a wait on a coverage gap, an incomplete
search, a close across the original ray, or travel strictly greater than
one current ATR. The first qualifying safety line supplies the decision
bar's value, ATR and rounded stop. The entry report uses that bar's next
scheduled H1 opening and retains the original trigger identity. Simultaneous
opposing decisions abstain. [Sprint 178 protocol note](PROTOCOL.md)

## Invented checks

| Case | Expected outcome |
| --- | --- |
| G25 signed guards | A close back across the original action ray fails. A move of exactly one ATR passes. A larger move fails for both directions. |
| Safety appears after the break | A mirrored G35 adaptation consumes at H4 index 48 and first qualifies protection at index 52. The current safety values are 103.2 and 96.8. The respective modeled E1 prices are 104.40014 and 95.59998. |
| Safety on a failed or chase-limited bar | The wait ends before safety can authorize entry. |
| Safety on the tenth bar | The wait expires. An as-of cutoff at the deadline also shows expiry with the same decision history. |
| Missing H4 inside the wait | The first received bar beyond the gap invalidates the wait. |
| Multiple pending setups agree on timing but oppose in direction | Both abstain when they become ready together. |
| Opt-in and restart | The CLI rejects the profile without its flag. Restore requires explicit opt-in and reconstructs the wait from the original bar prefix. Resumed setup, entry and checkpoint files match uninterrupted output. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --profile TRL_BRK3_DLY_E1 --enable-dly
```

Use the tick declared for the invented fixture. Keep the same profile and
flag when passing `--restore-checkpoint`. The setup report includes
`dly_transitions` and the state of unresolved waits at the cutoff.
Earlier checkpoints require their matching source checkout or replay
from the original input.

DLY remains outside the initial study grid. Phase 6 still needs its final
setup acceptance review. The report provides invented setup and entry
prices for the later account simulation.

## Verification

All 397 targeted tests passed. The 9 DLY tests took 97.090 seconds,
the 33 acceptance and lifecycle tests took 365.886 seconds, the 6 FXR
tests took 247.109 seconds, and the 349 other retained checks took
417.663 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_dly_178 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_acceptance_171 test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_context_172 test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```
