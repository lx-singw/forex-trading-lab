# Sprint 183 · Invented USD ledger

18 November 2026. Each independent Level B account starts from the
frozen USD 10,000. The ledger uses reconciled cash when flat to supply
the 0.25 percent sizing rule. It charges half the modeled commission at
each fill. Closed trades report gross P&L, both commissions, financing,
net P&L and any realized loss beyond the sized stop estimate.
[Protocol](PROTOCOL.md)

The held mark uses bid for LONG and ask for SHORT. Equity at or below 99
percent of the day reference latches the daily pause. A completed H1
range that the position survives can trigger it through the adverse mark.
The next UTC day anchors to reconciled executable equity before its
financing debit. A surviving position incurs the declared
weekday swaps, including three units on Wednesday and zero on Saturday
and Sunday.

## Invented results

| Scenario | Observed result |
| --- | --- |
| Wednesday hold and Monday gap | The base LONG was 0.11 lots. Gross loss was USD 39.16, commission USD 0.77 and financing USD 1.65. Net loss was USD 41.58, which exceeded the original USD 23.43 estimate by USD 18.15. Same-opening re-entry was blocked. |
| Daily loss pause and subsequent sizing | A USD 171.93 net gap loss paused the following same-day entry. The next valid day anchored to cash of USD 9,828.07 and sized against a USD 24.570175 budget. |
| Floating loss and recovery | A survived H1 adverse mark breached the day floor. Equity recovered by the close while the pause remained latched. |
| Missing liquidation opening | The adverse SHORT retained the last ask of 1.09982, USD 4.29 of floating loss and USD 0.55 of unpaid exit commission. Its state was `OPEN_AT_BOUNDARY` and it contributed no closed trade. |
| Midnight without an exact mark | An unresolved intrahour exit held capacity and left financing unsettled. A position proven to survive midnight could be financed while its daily reference remained unavailable. An unresolved reservation deferred the flat-account reference until receipt of its settlement. |
| Scaled G35 CLI and restart | A 0.12-lot LONG opened at 1.10454 and exited the gap at 1.10198. Net loss was USD 31.56, including USD 0.84 of commission. Cash was USD 9,968.44. Restoring the checkpoint and replaying the supplied prefix reproduced the ledger bytes. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.0001 --ledger
```

Use the fixture's declared tick. Select `--cost-profile adverse` for the
inherited adverse spread floor, slippage, commission and swaps. The
`--ledger` flag uses replay-derived capital. The separate
`--risk-snapshots` flag supplies invented capital for the sizing harness.

`ledger.json` records fills, marks, financing and day references with
their effective and receipt times, plus admitted positions, realized
trades and open liabilities. The effective time of a range exit is its
interval end for bookkeeping. The trade retains the interval as evidence.
Cash becomes reusable only on receipt of a closing observation. At a
missing observation the ledger keeps the last mark and its age, maintains
capacity occupancy, and books financing through reconciled exposure.
Prior source-bound setup checkpoints require their matching checkout or
a replay of the original inputs.

Level B liquidity, fills, commissions and swaps are modeled assumptions.
The pause can act on the available marks and on adverse prices in
survived ranges. Finer intrahour ordering, broker costs, the Level Q
adapter and full parity against retained ledgers remain unverified.

## Verification

All 161 targeted tests passed. The eight new ledger tests and eight
retained risk tests took 55.294 seconds. The 12 exit and E2 target tests
took 297.967 seconds, the 112 entry, fill and data checks took 313.565
seconds and the 21 FXR, DLY and setup acceptance tests took 460.116 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_ledger_183 test_trendline_risk_182 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_exits_181 test_trendline_levels_180 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_fills_164 test_trendline_data_163 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 -q
```
