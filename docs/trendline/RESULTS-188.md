# Sprint 188 · Level Q quotes and trade links

18 November 2026. The local viewer reads a saved invented Level Q ledger,
its checkpoint and the bound EURUSD quote tape. It checks the saved
midpoint publications against the tape and reconstructs their line
journals with the bound setup engine. Account events and modeled fill
prices come from the saved ledger.

## Inspect a receipt

Choose **Quote observations** to step through quote receipts. Each quote
shows its source time, receipt, sequence, bid and ask, and quality result.
Executable observations also show the modeled spread and whether it meets
the entry cap. Quotes received at the same millisecond share a cursor
position. Their inspector entries preserve their sequence.

Choose **Fills** or **Entry gates**, or select a visible fill marker. The
inspector links to the action and safety line revisions at the original
setup receipt. It shows touch indices, age, span and exact price slope.
**Go to setup receipt** returns the chart to that point. Fill inspectors
show the modeled price and, for Level Q, the quote that triggered it. A
skip linked to an eligible quote appears at that quote's receipt. An
expired opportunity appears when its deadline is known.

For Level Q, a protection record shows the H4 decision time and the
receipt of the first executable quote sourced after it. If no quote
applied the change, the ending liability shows the stop reported at the
saved cursor. Level B fills and gates also support setup links.

## Export

```sh
PYTHONPATH=src python3 scripts/trendline-quotes-185.py TAPE.json SAVED_RUN --tick-size 0.0001
PYTHONPATH=src python3 scripts/trendline-viewer-187.py TAPE.json SAVED_RUN NEW_VIEW_DIRECTORY
```

Use the tick declared for the fixture. Both commands accept the matching
`--unlock-receipt` for invented validation tapes. Open the exported
`replay.html`. The manifest identifies `Q` and `mid_sync` and records
the tape, ledger, checkpoint and HTML hashes. The same viewer command
accepts the Level B descriptor and saved `--ledger` directory.
[Level B usage](RESULTS-187.md)

## Verification

The invented break example has 788 receipt groups. Its entry quote is
2,000 ms old, the entry follows a stale and a spread-blocked quote, and a
later wide quote closes the held position. The viewer shows final cash
of `$9,962.98` and a net trade result of `−$37.02`. A separate example
reveals a crossed-stop skip only when the first eligible quote arrives.
The delayed-protection case preserves the earlier receipt prefix and
links the later change to the actual applicable quote.

Six new viewer tests, seven retained Level B viewer tests and 37 quote,
accounting and Elliott viewer tests passed. The fixed-target case keeps
its `1.1068` target and links the exit to the first target-reaching quote.
Chrome checks at 1440 × 1000 and 390 × 844 exercised quote and fill
stepping, selection of a chart marker, original setup links and the
settled account. An invented validation export requires its matching
unlock and records the unlock file hash when supplied.

Phase 8 continues with provisional pivots, bounce contacts, fuller
no-trade inspection, retrospective browsing, ledger exports and manual
annotations. This increment is software evidence from invented inputs.
