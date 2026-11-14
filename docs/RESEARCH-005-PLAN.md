# Research 005 — broader unchanged-baseline evaluation

Declared 2026-10-01 before downloading the new tick months or viewing their
strategy returns. Use April and October 2024: these complete the first month
of each calendar quarter alongside January/July 004. Selection is by calendar,
not observed performance. The old 2024 annual OHLC result was already viewed;
these are additional development samples, never an untouched holdout.

## Fixed protocol

1. Download the free EURUSD HistData April and October tick archives using the
   existing bounded downloader. Preserve originals and hashes; stop on access
   failures without automatic retries or alternative paid services.
2. Strictly parse all quotes, retaining ordering and duplicates. Construct two
   separate versions for each month: documented fixed EST and empirical New York
   UTC-4 (one hour earlier). No interpolation or mixing providers. New York has
   no clock transition within either selected source month.
3. Check April 10 and October 10 CPI release activity at source 07:30 and 08:30.
   Require 08:30 to have at least three times the price range and twice the
   tick count of 07:30. The official BLS releases identify 08:30 Eastern:
   https://www.bls.gov/news.release/archives/cpi_04102024.htm and
   https://www.bls.gov/news.release/archives/cpi_10102024.htm.
   This is empirical evidence, not clock certification.
4. Independently capture MT5 ticks for raw-label 12:00–18:00 on April 9,
   October 9 and October 29. Test month/date-specific broker UTC+3 for the first
   two and UTC+2 for October 29 against empirical New York HistData hourly bid
   closes. These are hypotheses declared before comparisons. Require every
   hour in each window (six per window), at least 95% of closes within one pip,
   and none beyond five pips. A failed window blocks that month's evaluation.
   Guarded collection must observe actual demo type; no orders or settings changes.
5. Both clock versions must have at least 500 observed hours, no unresolved
   intertick gap exceeding one hour, and first/last quotes within six hours of
   the source-month boundaries. Weekend-pattern gaps are recorded, not proof
   of completeness. Failures block the affected month; no threshold relaxation,
   feed splice or alternate month selection after inspection. Report all failures.
6. Only eligible months may be frozen/evaluated. Before any returns, freeze all
   eligible month/clock/cost manifests and archive their source. Use precisely
   the existing tick-pilot-003 base/adverse configs and unchanged strategy engine.
   Each sample starts from $10,000 with its own warmup, modeled 1:10 leverage,
   UTC daily reset and hypothetical broker costs. No optimization. Publish every
   eligible scenario, trade count, net P&L, return and tick-sampled drawdown;
   reconcile trades, charges, equity and all frozen hashes.

The gate permits only bounded provisional development research. Passing it
does not verify broker execution, source completeness, timezone documentation
or profitability. Preserve all 001–004 evidence. Never total the separate
monthly starts into a continuous annual return or treat sensitivities as
independent trials. No demo execution is activated by this study.

## Reserved validation period

Reserve November–December 2026 as future, unexamined validation data relative
to this declaration. Do not collect or evaluate that period in this workflow.
A later protocol must lock the final strategy, costs, data eligibility and
acceptance criteria before those returns are examined. This reservation does
not schedule collection or trading and is not evidence of successful validation.
The consumed 2025 holdout remains excluded from optimization.
