# Baseline v1: offline simulation and demo observer

Parameters selected on 2026-09-30 before obtaining or evaluating market data.
This is a transparent reference strategy, not a profitability claim.

## Signals

EURUSD H1 bid candles. At the following bar's open, compare SMA20 minus SMA50
on the last two completed candles. A crossing from <=0 to >0 buys; >=0 to <0
sells. Warmup requires 51 completed candles. The current candle's close, high
and low never influence its entry signal or sizing. No entry on a time gap
longer than one hour; do not replay a Friday signal on Monday.

Stop distance is twice the arithmetic mean of the last 14 true ranges (including
the preceding close). This is simple-average ATR, **not Wilder's smoothed ATR**.
Target distance is twice stop distance. Existing positions keep their original
stop and target; opposite signals do not reverse them. A bar starting with an
existing position cannot reenter after that position exits. Trades are closed
at the end of each evaluation partition, with exit costs.

## Sizing and prices

Only EURUSD with USD accounting is supported. The baseline assumes 100,000 EUR
per lot, 0.01 minimum/step, at most 1 lot, and hypothetical 30:1 leverage. These
are research inputs, not verified account facts. Lots are rounded down, never
up to a broker minimum. Skip if the risk budget cannot fund the minimum.

The risk budget is current equity times 0.0025. For each lot, estimated loss is
`(stop_distance + exit_slippage) * contract_size + round_turn_commission`.
Entry is already adjusted for adverse entry slippage. A simplified initial
margin cap, including entry commission, also bounds volume. No stop-out,
liquidation, variable margin or exchange conversion is implemented.

Long entry is ask plus slippage; short entry is bid minus slippage. Long stops
trigger on bid, short stops on ask. The per-bar spread is constant across that
bar, including exit evaluation. Stop fills receive adverse slippage; a gap
beyond a stop fills at the opening exit quote plus adverse slippage, not at the
stop. A target is modeled as a limit filled exactly at target without favorable
gap improvement; real target fills are not assured. When both stop and target
touch within a candle, use the stop. No tick order is inferred from OHLC.

Default hypothetical costs: $7 round trip per lot, 0.2 pip adverse slippage on
each market/stop fill, and daily swap debits $3/long lot or $1.50/short lot.
Wednesday's rollover is tripled; Saturday and Sunday are not charged. Rollover
is applied at the next broker midnight; all skipped dates are accounted for.
This is an explicit approximation; holidays, broker-specific rollover times,
variable swaps and spread widening require actual data and further work.

## Daily limits and restarts

The first observed day's reference is starting capital. Later days use the
previous observed close equity, before rollover charges and opening gaps. This
preserves overnight losses even across missing days. Calendar boundaries use
the configured IANA `broker_timezone` (default UTC is only a hypothesis). Input
bars and broker rollover must align to whole hours for this H1 model.

Latch the pause if equity is at or below 99% of the reference: check at open,
after exits, at the close, and at a held position's adverse intrabar extreme.
If no stop touched but a target touched, conservatively assume the adverse
extreme could have come first. A latched pause persists through recovery and
blocks new entries until the next observed broker date. Stops/targets continue
operating; a pause neither forcibly liquidates a position nor caps losses.

`Simulator.checkpoint()` serializes the full simulation state, including open
position, indicator history, daily reference, pause, last candle and results.
`Simulator.restore(text, config)` rejects a corrupt checksum or changed config.
An identical replay of the latest candle is a no-op; a conflicting duplicate or
older candle is an error. Persist the returned string if using this API across
processes. The CLI replays deterministically from source data instead of keeping
mutable state. Checksums detect accidental corruption, not malicious edits.
This is simulated restart handling, **not** broker order reconciliation.

## Evaluation

`freeze` records immutable-by-convention parameters, source/code hashes, data
coverage, assumptions and an explicit holdout boundary. Files cannot be silently
overwritten. Both partitions start with the same capital and no open position;
holdout indicators may warm up on prior development candles. Costs and signals
for development cannot read holdout values. Reading the complete file for schema
validation and hashing does not use future prices for decisions.

Reports include net P&L/return, trade count, win rate, average win/loss, exposure,
costs, close-sampled drawdown, trades and equity. Trade `opened` and `closed`
timestamps label their H1 candle starts, not exact intrabar fill times. Missing
hours include weekends and outages; they are counted, not imputed. Exposure is
the fraction of evaluated bars with a position, not a precise time fraction.
Close drawdown can miss intrabar losses. Synthetic fixtures are labeled as
software checks. No historical profitability has been established. Hashes cannot
prevent deliberate repeated holdout inspection: do not tune on the holdout.

The first provisional market-history experiment is now recorded in
`docs/EXPERIMENT-001-RESULTS.md`; it does not establish reliable profitability.
`freeze` requires a matching import provenance file for market data. Split
boundaries can fall on an hourly market-closure timestamp, with observations
assigned strictly before/after the cutoff. API source-clock interpretation and
cost assumptions remain visible in the frozen manifest and resulting reports.

## MT5 boundary

The observer mirrors default signal formulas only. Python config changes do not
update MQL5 constants. The observer suppresses output on excessive spread,
existing positions/pending orders, missing history and nonconsecutive bars.
Attachment/restart skips the already closed candle. It logs no account identity.
Compilation does not establish runtime behavior or Python/MQL signal parity.

Before any execution component is built: validate market history and costs;
test real/contest rejection and demo acceptance in an appropriate isolated
harness; recheck the actual account type immediately before every submission;
reconcile positions, pending orders and prior requests across crashes; verify
broker sizing, stop constraints, slippage, rejection and daily limits. Order
placement must remain off by default, and real-money execution must stay absent.

MQL5 references used for implementation:

- [Account type enum and ACCOUNT_TRADE_MODE](https://www.mql5.com/en/book/automation/account/account_real_demo_contest)
- [AccountInfoInteger](https://www.mql5.com/en/docs/account/accountinfointeger)
- [CopyRates: closed-bar shift and physical array order](https://www.mql5.com/en/docs/series/copyrates)
- [MetaEditor compilation and diagnostics](https://www.metatrader5.com/en/metaeditor/help/development/compile)
