# Data and tick workflow 003 — 2026-09-30

Historical status for the 003 candidates, which remain blocked. The later
[research 004](RESEARCH-004-RESULTS.md) uses separate datasets and an explicitly
provisional research gate; its six completed simulations do not clear these
original candidates or authorize execution.

**Performance evaluation remains blocked by data quality.** The two downloaded
archives and their normalized copies are diagnostic evidence. The new tick
strategy engine and gated workflow pass software tests, but no new historical
strategy return has been generated and no demo execution is authorized.

## Ordered workflow status

1. Cross-source price comparisons completed; absolute summer timestamp meaning
   is still disputed by event-time evidence.
2. Separate January and July development candidates were built and audited.
   January has five missing weekday hours; July's documented clock conversion
   is questionable. Both remain quarantined from performance evaluation.
3. Full-strategy tick replay is implemented and tested. The actual dataset
   freeze was rejected by its data-quality gate, before any result was produced.
4. Demo forward execution remains unavailable. No order code, terminal setting
   change or EA deployment was introduced.

## Cross-source clock evidence

Original archives were downloaded through HistData's public free web form.
The provider's [format specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/)
states a fixed EST clock without DST and identifies bid/ask tick fields. The
reader therefore initially applied a fixed five-hour shift to UTC. Rows were
validated in order, preserving same-millisecond events and rejecting malformed,
crossed, nonfinite, out-of-month or reordered rows. No gaps were filled.

All five MT5 offset candidates were compared under the
[predeclared protocol and amendments](INDEPENDENT-DATA-003.md):

| Sample | Mean absolute bid-close difference at +2 | At +3 |
|---|---:|---:|
| January 4–5 tick reconstruction, 14 hours | 0.1714 pip | 3.5286 pips |
| July 2–3 tick reconstruction, 13 hours | 0.1231 pip | 5.3000 pips |
| January 9 preserved H1, 12 hours | 0.1250 pip | 7.6000 pips |
| July 9 preserved H1, 12 hours | 0.0917 pip | 3.8833 pips |

The fresh dates were selected before their prices were compared. MT5 was closed
at that point, so preserved H1 candles were used, explicitly distinguished from
fresh ticks. The initial +3 summer hypothesis failed. A predeclared fixed-offset
amendment passed relative price-alignment checks and permitted building the
separate diagnostic candidates. **That preliminary pass is superseded by the
subsequent absolute-clock and gap review.** Relative alignment cannot identify
which source's UTC interpretation is correct.

## Event-time contradiction

The official BLS releases occurred at 08:30 Eastern on
[January 5](https://www.bls.gov/news.release/archives/empsit_01052024.htm) and
[July 5](https://www.bls.gov/news.release/archives/empsit_07052024.htm), corresponding
to 13:30 UTC in January and 12:30 UTC in July. The archive's strongest activity
within the inspected 07:00–09:30 source-clock interval occurs at 08:30 on both
dates: 661 January ticks and 663 July ticks, with respective one-minute bid
ranges of 41.9 and 41.0 pips. July's 07:30 source minute has just 23 ticks and a
0.6-pip range.

After MT5 became available again, a guarded demo read around July 5 showed the
corresponding large move at source label 15:30: 195 ticks and a 37.6-pip range.
This favors MT5 +3 in summer and daylight-adjusted New York labels in HistData,
rather than fixed EST. That is an inference from event alignment, not proof of
the meaning of every historical timestamp. No silent timezone correction was
made. The documented-rule normalization remains preserved and quarantined.

Dukascopy's public history endpoints returned HTTP 429 and an FXCM 2024 sample
request returned HTTP 403. Requests stopped at those responses; no paid access,
credential creation or provider contact was used.

## Coverage and missing weekday hours

| Candidate | Tick rows | Observed hours | Gaps longer than an hour |
|---|---:|---:|---:|
| January 2024 | 2,176,113 | 530 | 7, including 3 weekday gaps |
| July 2024 | 1,463,751 | 552 | 4, spanning weekends |

The January weekday gaps cover five hourly slots under the documented clock:
January 15 19:00 UTC; January 16 17:00 UTC; and January 16 21:00–23:00 UTC.
Read-only MT5 demo captures contain respectively 1,514, 19,195, 2,388, 5,592
and 1,175 ticks in the corresponding source hours. They are not established
market closures. No broker ticks were spliced into HistData.

Current limiting report: `reports/data-quality-003.json`, supplemented by
`reports/additional-data-003.json` for broker gap and event evidence. It
supersedes `reports/data-stage-003-amended.json`; the original failed seasonal
check `reports/data-stage-003.json` is also preserved.

## Tick strategy implementation and checks

`TickSimulator` builds H1 bid candles as ticks arrive. Signals see only completed
hours; entries use the next observed opening bid/ask with the spread filter and
assumed slippage. It uses existing risk sizing, commission, swap and daily-loss
rules with an explicitly assumed UTC day. Long exits use bid, short exits use
ask. Stops fill at the next observed quote plus adverse slippage; targets get
their limit price. Gaps can exceed estimated risk. Intrahour equity observes the
daily pause, and tick-sampled drawdown is tracked separately from hourly closes.

**113 tests passed.** New meaningful cases cover first-quote entry/spread rules,
same-millisecond stop/target order, adverse gaps, short ask exits, loss pauses
after recovery, chronological signal isolation, position/size bounds, rollover,
final liquidation, duplicate rejection and equivalent mid-position restart.
Workflow tests verify that failed quality reviews, changed datasets/reviews and
immutable outputs prevent inappropriate evaluation. Existing OHLC tests remain.

The full engine has only been exercised on software fixtures. Queueing, latency,
available liquidity, broker margin liquidation and real fills are not modeled.
Historical commissions/swaps remain assumptions. No new strategy performance
report exists. The 2025 holdout remains consumed and was not revisited.

## Reproduction and next action

Download and comparison scripts: `download-histdata.py`, `compare-histdata.py`,
`check-data-stage.py`, `normalize-histdata.py` in `scripts/`. Original ZIPs live
under `data/histdata-eurusd-2024{01,07}-original/`; diagnostic candidates live
under `data/histdata-development-003-{january,july}/`, with hashes and coverage.

The following command must stop with the current review and must not create a
manifest:

```bash
python3 scripts/run-tick-experiment.py freeze \
  --dataset data/histdata-development-003-july \
  --quality reports/data-quality-003.json \
  --config config/tick-pilot-003.json \
  --manifest reports/new-tick-pilot-manifest.json
```

Next: resolve the source-clock contradiction with additional timestamped
evidence and obtain a continuous, separately sourced development sample. Any
changed clock convention or repaired dataset requires a new artifact and quality
review. Freeze it before running the baseline and predeclared adverse-cost case.
Do not promote diagnostic outcomes into demo authorization.
