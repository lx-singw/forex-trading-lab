# Sprint 190 · Retrospective view and ledger exports

18 November 2026. **Receipt replay** opens at the partition start.
**Retrospective** shows the full saved H4 chart and the account state
at the labelled saved cutoff. Runs with more than 120 H4 candles also
offer 120-candle windows. Selecting a retrospective fill or contact
opens its original receipt evidence alongside the saved chart. Return
to **Receipt replay** to resume the same receipt, selected evidence,
and chart layers.

## Export bundle

The existing viewer command exports the bundle from a saved Level B
ledger run or a saved Level Q quote run and its matching tape.
[Export command and source settings](RESULTS-188.md#export)

| File | Contents |
| --- | --- |
| `replay.html` | Offline receipt replay and retrospective chart |
| `report.html` | Saved cutoff, closing balances, any open liability, closed trades, entry gates and setup reasons |
| `ledger.json` | Structured setup, contact, admission, account, protection and ending records with their original evidence |
| `ledger.csv` | Columns for the same rows with exact decimal amounts, outcome codes, clocks and identifiers |
| `manifest.json` | Input report hashes, scope, saved cutoff and SHA-256 of each exported file |

The report and both ledgers identify the data level, geometry basis,
profile, partition and cost profile. Join CSV and JSON by `row_id`.
`receipt_at_ms` is when evidence arrived. `effective_at_ms`,
`decision_at_ms` and the quote source and sequence carry their own values
where recorded. `receipt_order` is the row's position in the viewer's
receipt group. The quote sequence carries the source ordering for linked
quotes with the same receipt. The CSV leaves unavailable columns blank.

## Verification

The Level Q example preserves its `−$37.02` closed trade, `$9,962.98`
ending cash and distinct effective and receipt timestamps. A shorter
saved prefix reports the held position, its last mark and unpaid
commission. The Level B bounce report includes the crossed-stop skip.
The CSV and JSON rows reconcile by identifier and the manifest hashes
match their files. A simulated write failure permits an identical retry.

All 49 targeted tests passed. Chrome at 1440 × 1000 and 390 × 844
verified the saved-cutoff label, receipt restoration, fill inspection,
the readable report and its ledger links. A separate Level B run
showed all 132 saved candles in the retrospective view and confirmed
that the last window contained 12 candles.

Phase 8 continues with manual annotation comparison and visual
acceptance. This sprint uses invented replay evidence.
