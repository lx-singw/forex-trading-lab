# Research 004 results — 2026-10-01

The six predeclared full bid/ask tick simulations completed. January lost in
both cost scenarios. July's small gain almost disappeared with adverse costs.
These short development samples do not establish a robust profitable edge.
**Demo execution remains unavailable and is not authorized by these results.**

## Observed simulation results

Each run starts independently with $10,000, its own indicator warmup and no
position. The strategy is unchanged: SMA20/50, ATR14 times two stop, 2R target,
estimated risk up to 0.25%, one position, 1% daily entry pause and a 1.5-pip
spread filter. Modeled leverage is 1:10. These are research assumptions.

| Sample / clock | Costs | Trades | Net P&L | Return | Win rate | Maximum tick-sampled drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| January / MT5 UTC+2 | Base | 9 | -$146.38 | -1.4638% | 11.1% | 1.5553% |
| January / MT5 UTC+2 | Adverse | 9 | -$153.19 | -1.5319% | 11.1% | 1.5986% |
| July / empirical New York | Base | 8 | +$11.73 | +0.1173% | 37.5% | 0.8916% |
| July / empirical New York | Adverse | 8 | +$0.44 | +0.0044% | 37.5% | 0.9109% |
| July / documented fixed EST | Base | 8 | +$10.83 | +0.1083% | 37.5% | 0.8917% |
| July / documented fixed EST | Adverse | 8 | +$0.44 | +0.0044% | 37.5% | 0.9109% |

Base costs assume $7 per lot round-trip commission, 0.2 pip adverse slippage,
and daily long/short swaps of -$3/-$1.50 per lot. Adverse costs assume $10,
0.5 pip and -$6/-$3 respectively. Both use UTC daily reset and Wednesday triple
swap. Historical broker charges and rollover rules have not been verified.

The two baseline months contain only 17 trades. Cost and clock variants reuse
the same observations; six reports are not six independent experiments. These
are noncontinuous samples with independent starting capital, so no combined
continuous or annual return is reported. July is a provider source-month sample;
its UTC boundaries differ between clock interpretations.

July's clock variants have identical entry/exit prices and one-hour-shifted
timestamps. At base costs the fixed-EST interpretation adds $0.90 in modeled
swap to the first trade. At adverse costs the non-time trade fields are identical.
This limited sensitivity does not certify the source clock or rollover model.

## Data eligibility and remaining uncertainty

The [protocol](RESEARCH-004-PLAN.md) was declared before new comparisons or
strategy results. The failed 003 candidates and their blocked quality review
remain unchanged. Research 004 uses new, separately identified datasets:

- January: 5,708,283 MT5 ticks captured in 16 bounded chunks, replacing the
  entire earlier candidate without splicing providers. There are 530 observed
  hours. All 525 reference hours inside UTC January are present; 97.90% of
  overlapping hourly bid closes are within one pip, with a maximum difference
  of 2.9 pips. Five reference hours outside UTC January were excluded explicitly.
- July: 1,463,751 HistData ticks and 552 observed hours, represented separately
  under empirical New York and documented fixed-EST clocks. Every quote and
  sequence number matches between versions; only timestamps shift by one hour.
- Each dataset has four large gaps matching a weekend pattern and no unresolved
  gap over one hour under this review. This does not prove complete market
  coverage, especially for shorter missing intervals.

Fresh January 11 and July 11 CPI checks support the empirical clock hypothesis.
At source 08:30 versus 07:30, January has 679 versus 77 ticks and 47.6 versus
2.7 pips of range; July has 649 versus 59 ticks and 47.5 versus 0.7 pips.
Both pass the predeclared activity thresholds against the BLS 08:30 Eastern
schedule ([January release](https://www.bls.gov/news.release/archives/cpi_01112024.htm),
[July release](https://www.bls.gov/news.release/archives/cpi_07112024.htm)).
This is event-alignment evidence, not provider certification. It still conflicts
with HistData's [fixed-EST specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/).
The offsets used apply only to these samples, not to a validated annual DST rule.

The new quality gate permits **bounded provisional development research only**.
It does not validate historical broker conditions, the old annual OHLC results,
or demo execution. The 2025 holdout was previously examined and remains excluded
from optimization. No untouched holdout was evaluated here.

## Verification and reproducibility

The Python suite passed 117 tests, including meaningful tick risk, adverse gap,
restart, ordering and immutable experiment checks. Four research-data tests
cover clock-only transformations, chunk ordering/coverage, source validation
and bounded hourly comparisons; these also passed after the final assertion
was added. No strategy code changed after freezing.

Post-run checks verified all six manifest links, code/data/provenance/review
hashes, the declared protocol, and every file inside the frozen source archive.
For every run, trade gross P&L minus commissions plus swaps equals net P&L;
trade totals match reported P&L, returns and final equity. Counts and aggregate
charges also reconcile. Original experiment 001 report hashes are unchanged.

Local, Git-ignored evidence:

- `reports/research-004-summary.json`: all six metrics, reconciliation, clock
  trade differences and original-report hashes.
- `reports/research-004-*-manifest.json` and corresponding scenario `.json`:
  frozen assumptions, trade records and hourly equity.
- `reports/research-004-freeze.json` and `reports/research-004-source.zip`:
  frozen source and scenario hashes. Archive SHA-256:
  `3cdeec273230b205fa36e9c7ba24e743ea5da8ab9b31f9a4253f5df6276969f1`.
- `reports/research-quality-004.json`, `reports/cpi-clock-004.json`, and
  `reports/clock-sensitivity-004-check.json`: data eligibility and clock evidence.
- `data/research-004-*` and `data/mt5-january-004-chunks`: normalized inputs,
  original broker chunks and provenance.

Observed quotes are not executable fills. The simulator has no queue, latency
or available-depth model. Stops exit using observed bid/ask plus assumed
slippage; gaps can exceed estimated stop risk and daily thresholds. Tick-sampled
drawdown is a simulation measure, not a guaranteed broker loss bound. MT5
Strategy Tester parity and execution-specific runtime safeguards remain pending.

## Next research step

Predeclare a broader, unchanged-baseline evaluation across additional market
conditions, with data-quality criteria and cost/clock sensitivity fixed before
viewing performance. Reserve a genuinely unexamined period before any later
strategy selection. Investigate verified source clocks and historical broker
costs. Do not tune against the consumed 2025 holdout or reinterpret these short
samples as validation.

The ordered workflow has reached a provisional full tick pilot. The conditional
demo-forward stage has not been activated. No orders were sent, EA deployed or
terminal settings changed; guarded capture observed an actual demo account and
Algo Trading off. Real-money execution remains unavailable.
