# Proposed milestones

## 1. Baseline and risk controls
Implement a documented EURUSD H1 baseline using closed candles only.
Select simple, fixed parameters before evaluation. Proposed initial controls:
at most one position, estimated stop-loss risk at most 0.25% of equity per
trade, a daily loss pause at 1%, a spread filter and no martingale.
These are experiment defaults, not a recommendation for real-money trading.
Specify how daily limits behave across restarts, open losses and broker time.

## 2. Historical validation
Compile with MetaEditor and record compiler output.
Test meaningful account-type guards, sizing bounds, duplicate-order prevention
and loss-limit behavior. Run MT5 Strategy Tester using real ticks where
available. Document actual spread, commissions, swaps, slippage assumptions,
data coverage and execution limitations.
Use a chronological development/holdout split. Freeze parameters before
holdout evaluation. Do not optimize against the holdout.

## 3. Demo forward test
Deploy a reproducible Windows runtime copy from this WSL source tree.
Verify account type and configuration before activation.
Record enough trades and market conditions to assess uncertainty; do not
treat a short winning streak as validation. Stop and investigate failures.

## 4. AI comparison
Only after a working baseline, compare an AI model on the same unseen periods
and costs. Report both gains and failures. Do not assume complexity improves
returns. No live-money deployment is included in these milestones.
