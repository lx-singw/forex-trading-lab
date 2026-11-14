# Experiment 001: predeclared historical research

Declared 2026-09-30 before fetching or evaluating historical prices.

- Instrument/period: EURUSD H1 bid candles, requested 2024-01-01 00:00 UTC
  through (excluding) 2026-01-01 00:00 UTC from the existing demo terminal.
- Development: 2024. Holdout: 2025, beginning at 2025-01-01 00:00 UTC;
  a market holiday need not contain a candle. Do not tune on holdout.
- Strategy and risk parameters: unchanged `config/baseline.json`, selected before
  market evaluation. Both partitions use independent hypothetical $10,000 capital.
- First-pass execution assumptions: fixed 1.2-pip spread, $7 commission per lot
  round trip, 0.2 pip adverse slippage, baseline swap debits and UTC daily reset.
  All are hypotheses, not verified broker terms. Keep the hypothetical 30:1
  sizing leverage even if the terminal reports a different current leverage.
- Purpose: exercise the market-data workflow and describe this fixed baseline's
  behavior. This OHLC experiment cannot authorize trading or establish robust
  profitability. Tick validation, historical broker terms and runtime guards
  remain separate work.

Preserve input hashes, imported provenance, missing-hour audit and current
symbol properties. Current symbol properties are observations as of collection,
not proof of 2024/2025 settings. If history is missing, report its actual coverage;
do not silently substitute dates or regenerate favorable data. Account identity,
credentials, order history and account balances are not part of this capture.

Record results and any departures from this declaration separately after the
software tests pass. Do not change parameters based on the holdout outcome.

## Time interpretation amendment, before evaluation

The first collection contained 12,422 bars but a live quote timestamp was about
10,798 seconds ahead of the system's UTC clock. The documented API UTC convention
does not match that observation. Raw numeric labels are preserved and must not
be silently accepted as true UTC. No performance results were examined before
this amendment.

For this **provisional** experiment, interpret the raw labels as EET/EEST using
`Europe/Helsinki` (UTC+2 winter, UTC+3 summer with European DST). This is an
explicit assumption supported by an older MetaQuotes staff statement describing
EET with DST, by the current +3-hour observation, and by shortened Friday
sessions in the March/November US/European DST mismatch weeks. These observations
do not independently verify the source's 2024/2025 transition rules. A fixed
three-hour subtraction would be inappropriate for winter dates.

The requested 2024/2025 boundaries were raw source-clock labels; record the
actual converted UTC coverage. The holdout split remains 2025-01-01 UTC. The
simulator's UTC daily reset and baseline costs remain explicit hypotheses.
Any results are exploratory and cannot count as passed historical validation.

References:

- [Official API documentation says UTC](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py)
- [Historical MetaQuotes staff statement: EET with DST](https://www.mql5.com/en/forum/399066/page5)
- [Earlier staff discussion of EET/DST](https://www.mql5.com/en/forum/63796)

Current account properties also show 1:10 leverage and Algo Trading disabled.
Keep the predeclared hypothetical 30:1 reference simulation; do not confuse that
input with the observed account leverage. Historical commissions and swaps are
still unverified. No account balance or identifying data is needed for this work.
