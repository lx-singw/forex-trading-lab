# Strategy diagnosis 027 — complete, 2026-10-06

The main problem is weak entry performance in these development samples, with
costs adding further damage. Of 18 losing scenarios, 16 were already negative
before commission and financing; that gross figure still includes spread and
modeled slippage. Two April C00 cases crossed from slightly positive gross to
negative net after fees. These are descriptive findings from existing results,
not new strategy returns or unseen validation.

All **30 scenarios, 245 trades and 5,072 logged flat-account decisions** were
examined. Every trade matched exactly one prior closed-bar signal record by
entry hour, side and stop distance. No missing/ambiguous matches or decision
reuse. Independent Fraction accounting and separate lookup checked every trade;
245 future-log withholding checks preserved attribution. No quotes were parsed,
no strategy was rerun and no parameters were selected.

| Sample | Candidate | Trades base / adverse | Net USD base / adverse | Mean net R base / adverse |
| --- | --- | ---: | ---: | ---: |
| January | C00 SMA20/50 | 7 / 7 | -99.11 / -104.37 | -0.616 / -0.649 |
| January | C01 SMA50/200 | 1 / 1 | +44.90 / +44.54 | +1.963 / +1.948 |
| January | C02 breakout | 18 / 18 | -158.09 / -163.82 | -0.392 / -0.421 |
| January | C03 range | 11 / 11 | +6.92 / +0.79 | +0.045 / +0.013 |
| January | C04 selector | 9 / 9 | -12.81 / -14.36 | -0.046 / -0.078 |
| April | C00 | 7 / 7 | -0.08 / -3.23 | +0.012 / -0.022 |
| April | C01 | 1 / 1 | -24.22 / -26.11 | -1.097 / -1.183 |
| April | C02 | 11 / 11 | -166.49 / -170.33 | -0.672 / -0.707 |
| April | C03 | 10 / 11 | -168.46 / -197.08 | -0.746 / -0.808 |
| April | C04 | 11 / 11 | -86.24 / -99.84 | -0.343 / -0.380 |
| July | C00 | 7 / 7 | +36.43 / +25.52 | +0.227 / +0.190 |
| July | C01 | 1 / 1 | +46.05 / +42.18 | +1.950 / +1.923 |
| July | C02 | 13 / 13 | -109.32 / -121.49 | -0.373 / -0.412 |
| July | C03 | 8 / 8 | +49.34 / +41.68 | +0.274 / +0.220 |
| July | C04 | 7 / 7 | +51.72 / +37.29 | +0.292 / +0.245 |

R is initial entry-to-stop distance times volume and contract size, excluding
fees. Mean R weights each trade equally; dollar results also reflect differing
trade sizes, so their signs need not always agree. Stops, costs and gaps can
produce losses exceeding R. Every month restarts capital independently; these
rows cannot be compounded into a continuous investment return. Twelve scenarios
are positive and eighteen negative; cost variants/candidates reuse observations.

## What the entries reveal

C02 loses in every window under both costs. At base costs its January/April/July
exit counts are respectively 14/9/10 stops, 4/1/3 targets, and 0/1/0 sample-end
exits. April includes eight consecutive net losses. A 2R target cannot compensate
for this observed frequency of stopped trades. This supports testing stronger
direction confirmation, but does not prove whipsaw, news or an optimal horizon.

C01's apparently attractive January/July results each contain only one trade.
It loses its single April trade. Three base-cost observations are far too few
to establish superiority. Its slower direction can motivate a fixed hypothesis,
not a winner declaration or a learned filter fitted to these outcomes.

C04 is an actual combination, yet neither branch is consistently profitable:

| Sample | Range trades | Range net USD base / adverse | Trend trades | Trend net USD base / adverse |
| --- | ---: | ---: | ---: | ---: |
| January | 4 | -28.23 / -31.81 | 5 | +15.42 / +17.45 |
| April | 5 | -53.33 / -60.90 | 6 | -32.91 / -38.95 |
| July | 2 | +32.62 / +30.62 | 5 | +19.10 / +6.66 |

Across the three independent windows, the 11 range entries have net-dollar sums
of -48.94 base / -62.08 adverse; 16 trend entries sum to +1.60 / -14.84. These
are attribution sums, not returns of a new trend-only strategy: suppressing range
entries changes later position availability. Removing that branch needs a new
declared replay and cannot be credited with hypothetical recovered profits.

C04's base/adverse decision counts are identical: January has 68 range, 39
trend and 46 neutral decisions; April 74/25/42; July 15/23/32. The neutral band
abstains as specified. Decisions are logged only while flat at eligible contiguous
hour starts, not across every market hour; counts are not regime probabilities.
No evidence here establishes that price efficiency reliably identifies regimes.

## Costs, rejection and re-entry

Every base/adverse pair has lower net PnL under adverse assumptions. Fourteen
pairs retain the same entry identities; April C03 has one additional adverse
trade, losing $23.70. Of that pair's $28.62 deterioration, $4.92 comes from
shared entries and $23.70 from the added entry. This demonstrates trade-path
sensitivity, rather than a simple uniform fee deduction.

There are four unfilled logged signals and four reported spread rejections;
the records do not identify each individual rejection cause. No sampled equity
point is marked paused. These observations do not prove that every intratick
risk event or suppressed signal was logged. The 20 rapid entries after a loss
occur across overlapping cost/candidate paths; they are not independent cases
and do not account for all losses. C03's April losses have no such rapid re-entry.

The diagnosis accounts for stop overshoot separately from imposed slippage;
it does not claim these losses could be recovered. No legacy tick-drawdown metric
is interpreted here: later 019/020 work identified a peak-marking defect in the
older engine, while preserving its cash/trade accounting. A future replay must
use separately verified corrected metrics, retaining original reports.

## Verification and next experiment

The 026 snapshot's 632 bindings, 604 archive members and 28 external bindings
verified unchanged before extraction. All 58 original 008 archive members match
their current originals; the original archived module-set digest, specification,
runner, three data/review bindings and 30 report hashes verify. The new ledger
freezes 109 input/source bindings. Appended modules do not weaken the old CLI.
The first final-review attempt caught a missing next-plan filename in the
verification handoff. That local documentation failure is preserved separately;
only the handoff link was repaired, with diagnosis code/results unchanged.
Independent checks cover all 30 scenarios and 15 cost pairs. **342 tests pass,
including 12 new diagnosis tests.** Reports, checks, full table and seals are in
`reports/strategy-diagnosis-027*`; old inputs/results are preserved.

Next is `STRATEGY-EXPERIMENT-028-PLAN.md`: two fixed challengers against unchanged
C00/C02/C04 controls—C04 trend-only ablation, and C02 with existing SMA50/200
direction confirmation. Both address observed weaknesses without optimizing
thresholds. This is a bounded exploratory proposal, not a selected winner.
Annual eligibility remains failed; consumed 2025/reserved Nov–Dec 2026 stay
excluded. No real/contest execution, orders or market-edge claim.
