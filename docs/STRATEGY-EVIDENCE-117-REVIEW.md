# Strategy evidence117 — literature review and research decision

Completed 2026-10-13 local. Nine original papers were reviewed at the access levels
listed below. This is a bounded review, not an exhaustive search or a replication.
It extends [the008 review](STRATEGY-RESEARCH-008.md) with conflicting evidence,
implementation costs and a concrete separation between published portfolios and
our single-pair rules. No new market returns were calculated.

Our decision is to prototype a slower daily trend hypothesis, a daily version of
the existing price reentry rule, their fixed equal-weight signal combination, and
cash. These are research candidates, not selected profitable strategies. Carry,
cross-sectional momentum and fundamental currency value are unavailable with our
current qualified inputs. A paper's positive result does not repair our data.

## What the original research supports and what it does not

| Primary source and access | Finding relevant to this project | Transfer limitation |
| --- | --- | --- |
| Moskowitz, Ooi and Pedersen (2012), [Time series momentum](https://doi.org/10.1016/j.jfineco.2011.11.003). Indexed publisher abstract/introduction and author bibliography; author PDF timed out. | Reports return persistence over one to twelve months across 58 liquid futures/forwards and a diversified strategy. | A daily EURUSD spot-price sign with ATR stops is not their excess-return portfolio, monthly construction or risk scaling. |
| Kim, Tse and Wald (2016), [Time Series Momentum and Volatility Scaling](https://www.sciencedirect.com/science/article/pii/S1386418116301379). Indexed publisher introduction; [institutional bibliography](https://profiles.umsl.edu/en/publications/time-series-momentum-and-volatility-scaling/) confirms metadata; direct full text unavailable. | Finds that volatility scaling explains much of the apparent advantage over buy-and-hold in the investigated setting. | Better risk allocation must not be mistaken for an independently predictive signal. We have not reproduced this comparison. |
| Huang, Li, Wang and Zhou (2020), [Time series momentum: Is it there?](https://smusg.elsevierpure.com/en/publications/time-series-momentum-is-it-there/). Author institution's abstract; publisher full text unavailable. | Reports weak assetwise predictability and similar strategy performance from a historical-mean rule without that predictability. | Challenges one interpretation of momentum evidence; does not establish that every trend rule or market lacks an edge. |
| Menkhoff, Sarno, Schmeling and Schrimpf (2011 working paper; 2012 journal), [Currency Momentum Strategies](https://www.bis.org/publications/working-paper-366-currency-momentum-strategies). BIS abstract and publication metadata. | Reports cross-sectional currency momentum, partly explained by transaction costs, with limits to practical exploitation. | Ranking many currencies and using currency excess returns cannot be reproduced by one EURUSD spot feed. |
| Brunnermeier, Nagel and Pedersen (2008; revised 2013), [Carry Trades and Currency Crashes](https://www.nber.org/papers/w14473). Indexed NBER abstract; direct page denied. | Connects carry's negative skew and crash risk to funding constraints and crowded unwinds. | Positive interest differentials do not make a low-risk guaranteed return. Forward pricing and actual financing matter. |
| Asness, Moskowitz and Pedersen (2013), [Value and Momentum Everywhere](https://doi.org/10.1111/jofi.12021). Publisher abstract and selected sections of [author-hosted published PDF](https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf), especially introduction and V.A. | Finds complementary value and momentum across eight markets. The paper focuses on gross returns and discusses implementation costs. | Its cross-sectional value/momentum construction is distinct from time-series trend and our 20-bar price z-score. Its correlation result does not validate our mixture. |
| Eichenbaum, Johannsen and Rebelo (2017 revised), [Monetary Policy and the Predictability of Nominal Exchange Rates](https://www.federalreserve.gov/econres/feds/monetary-policy-and-the-predictability-of-nominal-exchange-rates.htm). Official abstract. | Reports real-exchange-rate prediction of nominal changes beyond two years, dependent on the monetary regime. | This is not evidence for hourly or 20-day price reversion; causal inflation vintages and a different horizon are needed. |
| Neely, Weller and Ulrich, [The Adaptive Markets Hypothesis: Evidence from the Foreign Exchange Market](https://fraser.stlouisfed.org/files/docs/publications/frbsl_wp/2006-046.pdf). Selected abstract, introduction and cost sections of March2007 working version 2006-046B; journal publication2009. | A later out-of-sample test finds deterioration in previously profitable technical rules; findings differ across rules. | Old success can decay. Historical cost models and particular rules do not certify contemporary retail execution or refute every possible rule. |
| Bailey, Borwein, López de Prado and Zhu, [The Probability of Backtest Overfitting](https://carmamaths.org/resources/jon/backtest2.pdf). Selected sections of November27,2014 working version. | Repeated strategy search and reused holdouts can create misleading success; a single holdout does not account for the search history. | We have not computed PBO. Chronology remains mandatory; freezing a small batch does not erase our earlier experiments. |

The strongest actionable inference here is to compare transparent, economically
different hypotheses at a slower frequency, with explicit costs and a recorded
search history. This is our engineering judgment. None of these papers proves
that the four proposed rules will profit, that 50/50 is an optimal weight, or that
an AI-designed engine can work every time. We have not established that daily
turnover will be lower after our stops and reentries; that must be measured.

## Fit to our data and engine

| Hypothesis | Required evidence and implementation | Exposure and failure modes | Current disposition |
| --- | --- | --- | --- |
| Time-series price trend | Completed daily sessions from qualified bid/ask quotes; at least253 prior closes; execution and financing evidence. | Trend reversals, whipsaw, persistent wrong direction, gaps and holding costs. | T12_D specification only; no qualified evaluation input. |
| Cross-sectional currency momentum | An independently defined multi-currency universe, aligned excess returns, forward/financing data, contemporaneous availability and realistic portfolio costs. | Concentration, changing relationships, expensive turnover and crowded reversals. | Unavailable; no proxy from EURUSD alone. |
| Carry | Tradable interest differentials or forward quotes, historical side-specific financing, rolls and portfolio exposures. | Negative skew, funding stress, large devaluations and gap losses. | Unavailable; swap debit placeholders cannot create carry evidence. |
| Fundamental value / PPP | Causal CPI vintages, original publication times, nominal exchange rates, regimes and a sufficiently long sample. | Multi-year divergence, revisions, policy changes and financing drag. | Unavailable; the closed H.10 route is not reopened. |
| Price mean reversion | Qualified completed daily price sessions; fixed price z-score; realistic entry/exit costs. | Strong trends can keep moving away; small gains may be overwhelmed by costs or tail losses. | MR20_D is a distinct experimental price rule, not fundamental value. |
| Fixed trend/reentry mixture | Both causal signals on the same data, one account, one risk budget; components measured alongside the mixture. | Correlated losses, signal cancellation, reduced exposure masquerading as improvement. | MIX50_D specification only; diversification benefit unproven. |
| Cash | Same evaluation dates and account currency; explicitly zero interest in this experiment. | Misses opportunities; no claim about actual deposit yield or inflation. | Required control, not a proof of a trading edge. |

The native107/109/111 captures still have uncertified source UTC/age and feed/cost
limitations. Legacy2020–2023 history still has unresolved coverage/provenance.
Reused2024 development results cannot become new validation;2025 is consumed and
excluded. October2026 stays quarantined. Reserved November–December2026 stays
untouched and alone would not meet this trial's minimum duration. Fresh qualified
data could support future work, but117 collected none.

## What our previous losses tell us

[Comparison008](COMPARISON-008-RESULTS.md) reports12 gains and18 losses across30
development scenarios; every candidate lost in at least one window. Several
breakout outcomes were negative before costs. Costs aggravated weakness rather
than providing its only explanation. The slow SMA candidate had too few trades
to establish anything reliable.

[Experiment028](STRATEGY-EXPERIMENT-028-RESULTS.md) found that trend-only and
agreement filters did not remove all losing months. Its window totals came from
separate accounts and are not a continuous portfolio return. [Experiment030](EXIT-EXPERIMENT-030-RESULTS.md)
found protective exits improved5 of12 comparisons and worsened7; some protected
exits still lost after costs and some original target winners were clipped. Those
thresholds were examined on reused development data. None is untouched evidence.

[Stress116](COMBINATION-STRESS-116-RESULTS.md) verifies software behavior on invented
prices. Its largest constructed single-trade loss was$1543.09 against a$25 entry
estimate. That demonstrates a gap limitation, not a real-market loss forecast.
Adding votes, tightening exits or achieving more passing tests cannot establish
an economic edge. No existing rule was changed or selected in117.

## Concrete next step

[The117 protocol](STRATEGY-EVIDENCE-117-PROTOCOL.md) and
[the declarative candidate ledger](../config/research-candidates-117.json) freeze
four hypotheses and16 planned evaluation cells. Data IDs, dates and executable
implementation are explicitly unassigned. This is a rule freeze, not a ready
market run or a completed statistical validation protocol.

[Daily prototype118](DAILY-STRATEGY-118-PLAN.md) is prepared next: implement only
pure completed-session feature decisions and test them with invented bars. A
later separate source/data/cost/run freeze is required before new returns. No
contact, provider retries, terminal actions, orders or manual user step are needed
for that prototype.
