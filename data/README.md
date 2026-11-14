# Local data

Place exported market data here. Record source, timezone and coverage. Datasets are ignored by Git.

The offline simulator accepts UTF-8 CSV (optional BOM) with exactly this header:

```csv
time,open,high,low,close,spread_pips
2024-01-01T00:00:00Z,1.10000,1.10100,1.09900,1.10050,1.2
```

Rows must be completed EURUSD H1 **bid** candles, sorted and unique, with
timezone-aware opening timestamps and valid finite OHLC. One pip is 0.0001.
`spread_pips` is the spread available at entry, modeled constant throughout that
candle; using an end-of-bar statistic as an entry spread may introduce leakage.
Do not confuse MT5 points with pips: 10 points per pip for a five-digit EURUSD
quote. Do not pad missing candles or silently reorder/drop bad rows.

Raw MT5 exports are not this normalized format. Convert broker-local timestamps
using verified historical UTC/DST offsets, remove the currently forming candle,
and document the conversion. The `import-mt5` command now handles native and
read-only collector exports; see `docs/HISTORICAL-DATA.md` for commands and
the timestamp discrepancy discovered on this terminal. Normalized market-data
bundles contain `bars.csv` and `provenance.json`; freezing requires both.
Record public source, symbol definition, bid/ask convention, spread measurement,
coverage/gaps, timezone rules, extraction date and whether data are synthetic.
Do not include terminal/account identifiers or credentials. Verified swap,
commission, margin, volume and rollover rules belong in an experiment's config
and cost notes before freezing, never guessed from the account balance.

`recovery-010` contains separate original February–July 2023 MT5 tick captures
in 91 bounded chunks, plus a sample and explicit mismatch follow-ups. All
labels remain raw broker labels; UTC serialization does not certify their
timezone. See `docs/RECOVERY-010-RESULTS.md`. The full tick capture includes an
incomplete July 14 hour; no simulator-ready replacement or blended source has
been published. Preserve original `history-009-raw` archives and failed audits.

`clock-012` contains eleven separate raw-label demo broker anchor captures.
`correction-013-gaps` contains four March broker hours and diagnostic
reconstructions (9,130 ticks). These are not HistData patches or eligible
simulator input. Correction 013 publishes only diagnostic JSON with exact replay
lineage and a scoped calendar hypothesis. Canonical archives, other quotes and
gaps remain intact. Annual clock and July coverage remain unresolved. See
`docs/CORRECTION-013-RESULTS.md`.

`walk-forward-014-synthetic` contains four annual files with 3,456 invented
ticks and deliberately sparse quarters. These exercise the chronological
runner and are not forex history. Their synthetic role cannot be accepted via
the market path. The annual market bundle/provenance/review contract is in
`docs/WALK-FORWARD-014-RESULTS.md`; no eligible market bundle has been published.

`normalization-015/YYYYMM` contains all 48 monthly diagnostic bundles. Each
retained quote carries its original row number and naive source label plus
candidate milliseconds, bid, ask and volume. The four proved second October
replays are collapsed only in this derived representation; originals remain
intact. Gzip CSV, inventory, provenance and seal are hash-bound. No missing
hour is filled and no broker source inserted. Files have a distinct diagnostic
kind/header and cannot enter the 014 annual reader. UTC/session approval is
still false. See `docs/NORMALIZATION-015-RESULTS.md` for findings and resume limits.

`reference-016` contains nine original Forexite daily MetaStock ZIPs for fixed
2022/2023 dates, request outcomes, primary-source HTML and boundary inspection
evidence. The separate diagnostic minute CSV preserves literal source row,
date/time and OHLC plus provisional CET/CEST-derived timestamps. All 11,153
saved rows were independently checked against originals. These are minute
bars with unverified start/end and original bid semantics; no ask quotes,
spread or execution path is synthesized. They cannot enter the annual tick
runner, fill 015 gaps or approve annual history. Both frozen 016 versions and
the failed first attempt remain intact. See `docs/REFERENCE-016-RESULTS.md`.

`source-access-017` contains primary-provider documentation and a separately
declared metadata-only FXCM HEAD failure. The first request returned 403 and
further archive requests stopped; no market quote body was downloaded. TrueFX's
public page requires login. Minute-label 017 uses only cached 012/015/016 data;
all reports are diagnostic, with no new simulator input or timestamp changes.
See `docs/LABELS-017-RESULTS.md` for fixed screens and acquisition prerequisites.
