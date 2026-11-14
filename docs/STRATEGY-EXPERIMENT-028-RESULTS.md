# Strategy experiment 028 — development replay complete, 2026-10-06

The two fixed challengers improve several outcomes, but both still lose in
April. Eight of their twelve scenario cases are positive. These are new offline
replays of already-seen 2024 development, not unseen validation or a reliable
income estimate. No strategy is selected or promoted; orders remain unavailable.

C05 keeps only C04's existing ER20 >=0.35 breakout branch. C06 requires C02's
breakout direction to agree with preceding SMA50 versus SMA200. Thresholds,
periods, 201-bar warmup, costs, ATR stop, 2R target, position sizing and loss
controls were fixed before returns. All 30 declared scenarios completed once.

| Window | Candidate | Trades base / adverse | Net USD base / adverse | Corrected tick drawdown % base / adverse |
| --- | --- | ---: | ---: | ---: |
| January | C00 control | 7 / 7 | -99.11 / -104.37 | 1.5480 / 1.5909 |
| January | C02 control | 18 / 18 | -158.09 / -163.82 | 1.8132 / 1.8750 |
| January | C04 control | 9 / 9 | -12.81 / -14.36 | 1.2117 / 1.1985 |
| January | C05 trend-only | 5 / 5 | +18.49 / +17.45 | 0.6348 / 0.5888 |
| January | C06 confirmed breakout | 10 / 10 | +39.86 / +30.33 | 0.8013 / 0.8131 |
| April | C00 | 7 / 7 | -0.08 / -3.23 | 0.8749 / 0.8795 |
| April | C02 | 11 / 11 | -166.49 / -170.33 | 2.0358 / 2.0845 |
| April | C04 | 11 / 11 | -86.24 / -99.84 | 1.7501 / 1.7919 |
| April | C05 | 8 / 8 | -13.01 / -20.98 | 1.1300 / 1.1422 |
| April | C06 | 7 / 7 | -100.27 / -100.69 | 1.3215 / 1.3402 |
| July | C00 | 7 / 7 | +36.43 / +25.52 | 0.8894 / 0.9086 |
| July | C02 | 13 / 13 | -109.32 / -121.49 | 1.5027 / 1.5677 |
| July | C04 | 7 / 7 | +51.72 / +37.29 | 0.8227 / 0.8384 |
| July | C05 | 5 / 5 | +15.23 / +6.66 | 0.7008 / 0.7081 |
| July | C06 | 8 / 8 | +11.49 / +2.14 | 0.5820 / 0.5955 |

Every window starts with simulated $10,000 and excludes the first 201 observed
hours as warmup. Evaluation starts January12 07:00, April11 13:00 and July11
13:00 UTC under the existing provisional data interpretation. These are partial
months, not three continuous monthly investment returns. Cost variants and
candidates reuse observations; their results are not independent trials. The
full table includes expectancy, win rate, exposure, gross PnL, commission and
financing in `reports/strategy-experiment-028-table.csv`.

## What changed

C05 turns January positive and substantially reduces April's loss relative to
C04, while giving up much of July's gain. It makes 18 trades per cost setting
across the three independent windows. Its diagnostic net-dollar sum is +$20.71
base and only +$3.13 adverse; this is not a continuous return or an expected
profit. That thin adverse result and April loss do not establish a stable edge.

C06 improves on C02 in every window/cost case, turning January and July positive.
It has 25 trades per cost setting. April's approximately $100 loss outweighs
the two positive windows: diagnostic net sums are -$48.93 base / -$68.21 adverse.
Slow direction agreement is a promising research hypothesis here, not a complete
solution. Every active candidate loses after costs in April; the arithmetic CASH
reference is zero. Retrospective knowledge of this cannot supply a forward
rule that knows when to abstain.

Entry-path comparisons show why these are actual replays, not deletion of old
losing trades. At each cost setting C05 retains 5/6/5 C04 entries in January/
April/July, drops 4/5/2, and adds two new April entries. C06 retains 9/6/6 C02
entries, drops 9/5/7, and adds 1/1/2 new entries. Capital and lot rounding can
also differ on shared entries. All twelve challenger/control comparisons are
recorded in the final review. No rejected variant or losing window is hidden.

## Verification and limits

Preflight verified all 700 prior bindings, 667 archived members and 33 external
bindings, including every original 008 archive member and exact data/reviews.
The ledger freezes 135 bindings before market replay. **356 tests pass**, including
14 new tests for the challenger rules, chronology, risk limits, spread guards,
gap losses, restart/duplicate behavior, legacy rejection and corrected marking.
The independent checker passed 12 synthetic long/short target/stop/end cases.

All **18 control replays** exactly match original trades, decisions and non-
drawdown cash/cost/state metrics. Corrected drawdown remains separately labelled;
the substantive control change is July C02 adverse, from about 1.568662% to
1.567681%. Tiny differences in two other cases are floating-point rounding.
Original 008 reports and annual runner/gates remain unchanged. Stops remain
subject to gaps and slippage; the nominal stop is not a guaranteed loss cap.

Independent full-tick cash, financing, feature and equity reconstruction passes
for all 30 accounts: **266 trades, 8,732,543 source ticks, 174,650,870 equity
marks and 2,628 new-challenger closed-bar feature records** checked. Each sample
had one replay pass and one separate verification pass over the same frozen
cached ticks; the market data were not downloaded again. Source sequence lineage
avoids guessing execution order from tied timestamps. No replay/check failures.
No source-clock/session or historical execution-cost uncertainty is cured by
this software check. Annual eligibility remains failed, 2025 remains consumed
and excluded, and Nov–Dec2026 remains reserved and unexamined.

Next: `TRADE-PATH-029-PLAN.md` declares an all-trade excursion diagnosis using
exact source sequence lineage. Determine whether failed entries never advance
or advance then reverse before proposing any exit change. No automatic trailing
stop, target tuning or deployment follows from the present results.
