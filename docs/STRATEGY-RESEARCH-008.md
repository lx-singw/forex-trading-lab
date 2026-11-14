# Strategy research and engine direction — 2026-10-01

## User objective and measurable interpretation

The user wants research into strong known strategies, alternatives, combinations
and trial-and-error development of a robust demo-only engine. This supersedes
the former priority of repeatedly investigating October timestamps. Preserve
the original baseline as a control; allow separately versioned new strategies.
October's failed gates remain intact and its data remain quarantined.

No researched strategy establishes an every-trade or every-period profit
guarantee. The engineering objective is positive after-cost expectancy supported
by chronological validation, controlled drawdowns, stable behavior under cost
stress, and an explicit ability to abstain. Losing periods are compatible with
that objective; concealed losses or selecting a lucky backtest are not.

## Evidence reviewed

This is a comparison of established research families, not an exhaustive search
or a ranking of today's live returns. Publication findings concern their own
instruments, horizons, datasets and cost models; none validates our EURUSD H1 bot.

| Family | Primary evidence and practical implication | Priority here |
| --- | --- | --- |
| Time-series momentum / trend | [Hurst, Ooi and Pedersen, 2017](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing) examine diversified historical trend following over a long sample. This supports testing the family, not assuming a single hourly crossover inherits the result. | First research family; test slower signals and breakout implementations. |
| Cross-sectional currency momentum | [Menkhoff et al., BIS Working Paper 366, 2011](https://www.bis.org/publications/working-paper-366-currency-momentum-strategies) document currency momentum, transaction-cost effects and practical limits to exploiting it. This ranks currencies against one another, unlike our single-pair crossover. | Later: requires several synchronized currency datasets and tested instrument/accounting support. |
| Carry | [BIS, Drivers of carry and currency momentum, 2011](https://www.bis.org/publications/drivers-carry-and-currency-momentum) discusses distinct drivers and downside risks. Collecting interest differentials is not a loss-free source of return. | Defer until historical financing/forward or rollover inputs are verified; do not substitute invented positive swaps. |
| Value plus momentum | [Asness, Moskowitz and Pedersen, 2013](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere) find value/momentum premia and negative correlations between the two across studied markets. This motivates investigating complementary exposures; it does not establish that combining arbitrary indicators improves results. | Later macro/value extension with appropriate data and horizon. |
| Mean reversion / range trading | [Eichenbaum, Johannsen and Rebelo, Federal Reserve, 2017](https://www.federalreserve.gov/econres/feds/monetary-policy-and-the-predictability-of-nominal-exchange-rates.htm) find real-exchange-rate predictability at horizons beyond two years. That is not evidence for an hourly z-score strategy. | An explicitly experimental H1 challenger, with lower evidence priority. |

My research judgment is to start with transparent trend and breakout candidates,
then test a range challenger and a fixed selector. Published evidence for a broad
family must remain separate from evidence for our exact implementation.

Repeated searches can manufacture impressive historical results. [Bailey et al.,
The Probability of Backtest Overfitting](https://carmamaths.org/resources/jon/backtest2.pdf)
examines this selection problem. Accordingly, every candidate, rejected variant,
cost scenario and later parameter change must be recorded. Trial-and-error is
authorized; unrecorded trial-and-error followed by reporting only the winner is not.

## New diagnosis of existing trades

`scripts/diagnose-baseline.py` reads the frozen reports and verifies their manifest
links and accounting. It does not rerun or change any strategy. Results are in
ignored `reports/baseline-diagnosis-008.json`, including every base/adverse trade.

| Base-cost sample | Stops / targets / sample-end exits | Net P&L | P&L before commission and swap | Fill beyond nominal stop, total dollars |
| --- | --- | ---: | ---: | ---: |
| January | 8 / 1 / 0 | -$146.38 | -$139.09 | $1.82 |
| April | 6 / 2 / 1 | -$51.01 | -$42.55 | $9.27 |
| July | 5 / 3 / 0 | +$11.73 | +$21.54 | $1.78 |

Across these baseline samples: 19 stopped trades, six targets and one profitable
sample-end exit, giving seven winners and 19 losers. These are only 26 trades;
cost variants reuse observations. Each month has separate initial capital, so
the table is not a continuous investment record.

Gross P&L above still includes spread and modeled slippage. Overshoot dollars
include assumed exit slippage; they are accounting attribution, not money that
an alternative execution system could necessarily recover. April's maximum
observed-quote overshoot, excluding the imposed exit slippage, is 4.34 pips.
January's small overshoot total and negative gross P&L indicate that this sample's
loss is not mainly a large-gap or commission story. We have not causally proved
late entries, range whipsaws, news sensitivity or an optimal stop distance.

Four meaningful new tests cover long/short stop attribution, separation of
modeled slippage from quote overshoot, non-stop exits and invalid accounting/time
records. The original engine, reports and declared gates are preserved.

## First bounded comparison batch

Specification: `config/research-candidates-008.json`. This frozen file is a
declarative specification, not an executable runtime configuration. Its status
field preserves that distinction. The rules are now implemented separately in
`src/forex_demo_lab/strategies.py` and `research_simulation.py`, with an offline
runner in `scripts/compare-strategies-008.py`. They were fixed before returns.
The first batch has five candidates, including the unchanged control; no search
over hundreds of parameter combinations. All use the same existing risk/cost
model, including at most one aggregate position, estimated 0.25% risk, 1% daily
entry pause and no loss-recovery scaling. Conflicting signals cannot stack risk.

- C00: unchanged SMA20/50 control.
- C01: slower SMA50/200 crossover; tests signal horizon without an indicator stack.
- C02: 20-bar close-confirmed channel breakout.
- C03: 20-bar standardized-price re-entry from a two-standard-deviation excursion.
- C04: fixed selector between C02 and C03 using a trailing price-efficiency ratio;
  an intermediate range gives no trade. This is a testable hypothesis, not a
  reliable market-regime detector or a probability forecast.

The common ATR stop and 2R target stay fixed in this batch to isolate entry logic.
Trailing exits, other horizons, news filters, weighted votes and learned selectors
would be new recorded experiments, not hidden changes to a losing run. A strategy
combination must be tested against its individual components and the control.

## Engine and experiment workflow

1. Implement a common pure signal interface accepting completed history only,
   returning direction, stop distance and an auditable reason. Test no-future-data
   behavior, warmup, zero volatility, repeated bars and selector boundaries.
2. Route decisions through the existing risk/sizing/tick simulation layer. Keep
   research separate from broker execution; no new order APIs or live toggle.
3. Add an immutable trial ledger: candidate/config/code/data hashes, dataset
   exposure, fold dates, every failure and every result. Preserve a no-trade
   control and report net expectancy, drawdown, trade count, payoff and costs.
4. Run all five on the currently eligible January/April/July samples as exploratory
   development comparisons only. Those months are already seen and cannot prove
   generalization. Exclude blocked October and the consumed 2025 holdout.
5. Obtain longer contiguous, separately reviewed history. Proposed acquisition
   target is 2020–2023, subject to availability/quality; no data were acquired or
   claimed validated here. Freeze actual chronological training/test windows
   and selection criteria before evaluating them. Choose rules/weights only
   from earlier data and carry them unchanged into each later test window.
6. Stress costs and observed gaps, inspect performance concentration and quantify
   uncertainty with methods appropriate to serial dependence. Do not assign
   reliable confidence from three short months. Simpler candidates that hold up
   deserve priority over complex historical winners.
7. Preserve reserved November–December 2026 validation. Before its eventual use,
   lock the final selection and numeric acceptance criteria; two months alone
   may provide too little evidence. Observation-only parity and runtime guard
   tests can proceed independently. Demo orders still require separate execution
   safeguards and sufficient historical evidence. Real money remains unavailable.

Status now: literature review, frozen-trade diagnosis, five pure signal modules,
shared-risk integration and all 30 frozen comparison scenarios are complete.
See `COMPARISON-008-RESULTS.md` for every candidate/cost outcome and limitations.
158 tests passed and the final audit reconciled all reports. Twelve scenarios
gained, eighteen lost; none of the five candidates gained in every window.
The selector did not consistently improve on both components. Walk-forward
selection, independent validation and reliable profitability remain uncompleted.
History 009 has since acquired all 48 months of 2020–2023, reviewed 110.1 million
rows and implemented the fixed training-only selector. Its data gate failed on
clock reversals and coverage; no new returns were computed. See
`HISTORY-009-RESULTS.md`. Next is resolving those deficiencies before a frozen
chronological replay, not post-result tuning of 008. No orders or deployment.
