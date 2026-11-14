# Diagnostic reconstruction 002 — 2026-09-30

The separate reconstruction contains **28 bid/ask candles from 101,859 ticks**.
A second July capture returned the same 27,856 ordered events and the same
compressed tick-file hash. This establishes repeatability of that read, not
independent market accuracy. Original experiment files remain unchanged.

## Findings

- July: 13 reconstructed candles, including the 11 absent from the original H1
  history. The first source hour contains 2,526 ticks versus the original H1
  candle's reported tick volume of 321; these counts need not use identical
  definitions and are not used to choose an endpoint.
- The suspect July 2 12:00 candle's four prices match 21 chronological prefixes
  ending between source labels 12:07:38.667 and 12:15:36.628. This is consistent
  with a truncated candle but does not prove truncation or its underlying cause.
  The full-hour close still differs by -9.4 pips and low by -6.3 pips.
- First development trade window: 14 reconstructed candles.
- March Friday window: one reconstructed candle; the following empty hour is
  recorded as unclassified and is not filled or labeled a confirmed closure.

The output records both bid and ask OHLC, opening-quote spread, first-tick delay,
last-tick gap and largest internal tick gap. Spreads use the first observed
quote, never the hour's later minimum. No entry, fill, sizing or performance
calculation is implied.

## Verification

**87 Python tests passed.** New tests exercise chunk-manifest consistency,
invalid quotes, partial/failed reads, empty hours, repeated/corrupt data,
same-millisecond ordering, conditional prefix diagnostics and immutable outputs.

A separate SQLite implementation checked every exported numeric column against
the captured ticks for all 28 candles. Its regression test deliberately changes
a closing price and refreshes the file hash: the checker still detects the wrong
aggregate. This is an independent calculation on the same feed, not validation
against another provider. Source and output hashes accompany both calculations.

The diagnostic CSV deliberately has a different header from simulator inputs;
the existing reader rejects it. Provenance declares
`not_validated_for_backtesting`, unverified historical timezone, incomplete
market validation and no independent feed validation. There is no silent patch
to the frozen dataset or automatic path into performance evaluation.

Original performance-report SHA-256 values were checked unchanged:

- Development: `f75ac99a6ed295d0f0078c73dcd7ec0c85d698766022392392d14e3cfa8d1cfb`
- Holdout: `c38ce8ea45cfba0cd13d67e7ff4293760fbee4a3076341e260f3a03180b6152b`

## Independent-feed attempt and remaining limits

One unauthenticated public Dukascopy hourly-file request for
`EURUSD/2024/06/02/09h_ticks.bi5` returned HTTP 429. Requests stopped after that
response; no comparison data were obtained. Dukascopy's current
[export documentation](https://www.dukascopy.com/wiki/en/development/data-export/)
describes a separate AWS requester-pays workflow. No paid service, AWS credentials,
broker account or new package was used.

The market-data cause, historical UTC/DST mapping and historical broker costs
remain unresolved. A trustworthy annual dataset and a complete tick strategy
simulation are still pending. Do not reinterpret the old annual returns as
validated or reuse the consumed 2025 holdout for optimization. Trading remains
unavailable; the repeat capture only read the existing demo terminal.

## Reproduce

From the repository root in WSL:

```bash
python3 scripts/reconstruct-ticks.py \
  --capture data/tick-audit-001-july-gap \
  --repeat-capture data/tick-audit-002-july-repeat \
  --raw-bars data/mt5-2024-2025-capture-v2/rates.csv \
  --output data/new-july-reconstruction
python3 scripts/check-reconstruction.py \
  --capture data/tick-audit-001-july-gap \
  --reconstruction data/new-july-reconstruction \
  --output reports/new-july-reconstruction-check.json
```

`--repeat-capture` and `--raw-bars` are optional diagnostics. Captures must cover
at most 48 hours with contiguous successful/empty request windows, consistent
counts and valid quotes. Missing hours remain explicit. Existing outputs are
never overwritten. See [capture commands](TICK-AUDIT-WORKFLOW.md) for read-only
collection with actual demo-account guards.

Local ignored artifacts: `data/tick-audit-002-july-repeat/`,
`data/tick-reconstruction-002-{july,first-trade,dst-friday}/` and the three
`reports/tick-reconstruction-002-*-check.json` files. Each reconstruction has
`diagnostic-bars.csv` and `provenance.json`.
