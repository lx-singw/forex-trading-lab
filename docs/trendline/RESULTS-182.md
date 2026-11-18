# Sprint 182 · Reservation and lot sizing

18 November 2026. The invented Level B replay can admit priced entries
to one independent strategy run with one reservation or held position.
The earliest scheduled opening owns the attempt once its risk snapshot
clears the equity and pause checks. The opening row or expiry settles
the reservation. A held position continues to occupy capacity until its
closing evidence arrives. A gap exit on an opening therefore blocks
another entry at that opening. [Protocol](PROTOCOL.md)

Sizing uses 0.25 percent of positive executable equity. The per-lot
estimate uses the slippage-adjusted entry, initial stop, modeled exit
slippage and round-turn commission. Free margin after estimated entry
commission, headroom to the 99 percent UTC-day reference floor, and the
inherited 1-lot cap can each reduce the size. The result is floored to
the inherited 0.01-lot step. Results below 0.01 lots skip with
`BELOW_MIN_LOT`. Margin is recorded as an exact numerator and denominator
because leverage can produce repeating decimals.

## Invented results

| Scenario | Observed result |
| --- | --- |
| G22 LONG and SHORT | A USD 25 risk budget limits size to 0.10 lots. USD 50 of free margin limits it to 0.05 and USD 10 of daily headroom limits it to 0.04. A per-lot loss of USD 2,501 floors to zero. |
| Cost and margin boundaries | Both sides size to 0.11 lots on the small-price fixture. Estimated stop loss per lot is USD 213 under base and USD 222 under adverse costs. The exact margin plus entry commission for 0.01 lots permits that size. A smaller margin balance skips. |
| Gap and range ordering | A gap that closes the first position blocks the entry attempted at that opening. A prior range exit permits the next entry when its row arrives by that opening. A one-millisecond delay blocks it. |
| Missing evidence | A price path with missing exit evidence keeps the slot occupied. An unfilled reservation expires at its original deadline. A missing risk snapshot leaves the attempt unavailable. |
| Daily risk snapshots | A pause triggered at the 99 percent floor survives a same-day recovery. A nonpositive equity snapshot skips. An entry at liquidation skips. |
| Normal CLI and restart | The invented G35 replay reserves at the opening, sizes 0.01 lots, estimates USD 1,800.23 of stop loss and releases on receipt of a later gap row. The restored prefix produces byte-identical risk output. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-breaks-173.py SOURCE.json HOURS.json NEW_DIRECTORY --tick-size 0.1 --risk-snapshots SNAPSHOTS.json
```

Use the declared fixture tick. The snapshot file binds the declaration hash
and the strategy and cost profile of the run. Take the `source_sha256` from
`entries.json` or `exits.json` for that source. This example shows the file
shape. Supply an opening from the actual invented source calendar.

```json
{
  "kind": "invented_b_risk_snapshots",
  "source_sha256": "<source declaration SHA-256>",
  "profile": "TRL_BRK3_E1",
  "cost_profile": "base",
  "snapshots": [
    {
      "opening_at": 947296800000,
      "equity_usd": "10000",
      "free_margin_usd": "10000",
      "day_reference_usd": "10000",
      "entry_paused": false
    }
  ]
}
```

Snapshots are ordered by unique scheduled opening time in epoch
milliseconds and describe account state immediately before that
opening. Reference equity stays fixed within a UTC day. An observed
floor breach or supplied pause stays latched in subsequent snapshots
that day. Missing snapshots make otherwise available entries abstain.
`risk.json` records reservation times, admission, sizing and capacity
release. The setup checkpoint and supplied prefixes reconstruct these
decisions on restart. Earlier source-bound checkpoints require their
matching checkout or a replay of the original inputs.

Equity, free margin and the day reference are inputs for this sprint.
Phase 7 still needs a cash and mark ledger, modeled
commission and financing debits, daily boundary reconciliation, realized
loss-excess reporting and independent accounting parity. Gap losses can
exceed the sizing estimate.

## Verification

All 153 targeted tests passed. Eight new risk tests took 36.933 seconds.
The 12 retained exit and E2 target tests took 348.886 seconds, the 112
entry, fill and data checks took 358.016 seconds, and the 21 FXR, DLY
and setup acceptance tests took 506.332 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_risk_182 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_exits_181 test_trendline_levels_180 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_entries_174 test_trendline_breaks_173 test_trendline_fills_164 test_trendline_data_163 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 -q
```
