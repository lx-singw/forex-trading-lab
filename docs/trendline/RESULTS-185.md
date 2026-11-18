# Sprint 185 · Invented Level Q quote replay

18 November 2026. The quote adapter builds geometry from each
synchronized bid/ask midpoint. Scheduled H1, H4 and D1 slots publish
after finalization. Signal selection, sizing, E1 protection and E2
targets reuse the existing models. Bid and ask observations drive
fills, marks, slippage, commissions and financing.
[Protocol](PROTOCOL.md)

- Order comes from source time, receipt time and unique quote sequence.
  A source timestamp must be strictly after setup receipt. Freshness
  includes an age of exactly 2 seconds. The effective entry spread cap
  includes 1.5 pips. Quote observations at the same timestamp can
  execute in the supplied sequence.
- The first eligible quote settles the attempt. The ratio cap, initial
  stop, sizing and daily pause can cause a skip. A wide executable
  quote can still close a held position. Capacity stays occupied for
  the quote that closes it.
- E1 updates take effect for quotes whose source follows the
  publication. An overlapping H4 close can schedule an exit, and
  whole-bar trailing starts with a fully post-entry H4. E2 keeps its
  opening stop and target.
- Liquidation uses the first eligible source quote from the declared
  cutoff with receipt inside the partition. Missing closing evidence
  preserves the last mark and open commission liability. A fresh
  closing mark can carry across an expressly declared closure for a
  UTC day reference.

## Invented results

| Scenario | Observed result |
| --- | --- |
| Synchronized geometry | Quote midpoints give an H1 high of 1.2. A quote received after finalization leaves that publication intact. |
| Freshness, spread and sequence | The quote at age 2 seconds and spread 1.5 pips opens a LONG. A repeated observation is skipped. A later, wider quote at the same source millisecond closes at 1.10148. After costs the net loss is USD 37.02. |
| First eligible rejection | A first quote that has already crossed the stop consumes the attempt. A later favorable quote produces no new position. |
| Prospective E1 | A later-received quote sourced before the H4 stop update uses the old level. The next source quote closes against the tightened stop. |
| FXR E2 | The first target reach fills at 1.1068. A subsequent stop-side quote arrives after that close. |
| Adverse SHORT across a closure | The modeled ask closes the position at 1.09967. Wednesday and weekend multipliers are 3, 1, 1, 0 and 0. Financing is USD 1.2375 and net loss is USD 4.7575. |
| Capacity, pause and liquidation | The exit observation blocks re-entry. A later attempt skips after a realized pause. The first eligible source quote from the liquidation cutoff can close a hold. A missing close leaves the last mark and liability. |
| Restart | The held-prefix checkpoint resumes to byte-identical output. A changed tape fails its checkpoint binding before output creation. |

## Replay

```sh
PYTHONPATH=src python3 scripts/trendline-quotes-185.py TAPE.json NEW_DIRECTORY --tick-size 0.0001
```

Use the declared fixture tick and select `--profile` and
`--cost-profile` for the intended run. A tape declares schema
`TRL_Q_TAPE_185_V1`, kind `invented_trendline_quotes`, symbol
`EURUSD`, level `Q`, geometry basis `mid_sync`, partition, calendar,
liquidation cutoff and the ordered `quotes` list. The calendar uses the
existing invented session schema. Each quote supplies integer
`source_at`, `received_at`, `sequence` and exact decimal strings
`bid` and `ask`. Set `liquidation_at` in epoch milliseconds inside the
partition. For invented validation fixtures, use
`quotes.validation_unlock(document)` to prepare the matching JSON
receipt and pass it with `--unlock-receipt`.

The CLI writes `quote-ledger.json` and `checkpoint.json`. Its default
cursor is the partition end. Use `--as-of` for a receipt prefix.
`--restore-checkpoint` reconstructs and checks that prefix before
replaying further on the same bound tape and settings.
Earlier source-bound Level B checkpoints require their matching checkout
or a replay of their original inputs.

The tape is an invented observation sequence. The adapter derives
software evidence about that sequence. Actual provider coverage, clock
qualification, broker costs and market admission remain open.

## Verification

All 177 targeted tests passed. The ten quote tests took 118.694 seconds.
The retained 70 accounting and fill tests took 188.172 seconds, the 71
entry and replay checks took 346.058 seconds, and the 26 FXR, DLY and
setup acceptance checks took 700.587 seconds. The completed verification
includes the shared Level B open-liability path after its refactor fix.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_quotes_185 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_account_parity_184 test_trendline_ledger_183 test_trendline_risk_182 test_trendline_exits_181 test_trendline_fills_164 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_entries_174 test_trendline_bounce_177 test_trendline_brk2_176 test_trendline_breaks_173 test_trendline_data_163 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_fxr_175 test_trendline_dly_178 test_trendline_setup_acceptance_179 test_trendline_levels_180 -q
```
