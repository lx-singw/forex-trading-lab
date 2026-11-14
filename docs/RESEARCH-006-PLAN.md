# Research 006 — fresh late-October clock checks

Declared 2026-10-01 before inspecting the October 30/31 event statistics or new
broker comparisons. The October archive was already parsed in 005; these are
fresh diagnostics, not unseen market data. Preserve 005's failed UTC+2 check
and blocked gate unchanged. Its post-hoc UTC+3 match motivates a new hypothesis,
not a retroactive pass. No October strategy returns have been computed.

## Predeclared evidence and decision

1. Use the official BEA October 30 GDP and October 31 personal-income releases,
   both scheduled at 08:30 EDT (12:30 UTC):
   https://www.bea.gov/news/2024/gross-domestic-product-third-quarter-2024-advance-estimate
   https://www.bea.gov/news/2024/personal-income-and-outlays-september-2024
   Other releases can coincide; activity cannot be attributed to one release.
2. From the unchanged HistData October archive, compare source 08:30 with 07:30
   on each date. Require positive control activity, at least three times its
   bid-price range and twice its tick count at 08:30 on both days. This supports
   empirical New York UTC-4 after the presumed European clock-change weekend.
3. Capture MT5 raw-label 12:00–18:00 on October 30 and 31 through the guarded
   read-only demo collector. Assert those exact capture bounds. Require broker
   raw-label 15:30 activity to meet the same range/count thresholds against
   14:30 on both dates, consistent with UTC+3. Record 16:30 as diagnostic context,
   with no eligibility threshold. Do not change terminal settings or send orders.
4. Compare all six hourly bid closes per window with the unchanged empirical
   New York HistData version under broker UTC+3. Each window requires all six
   hours, at least 95% within one pip and none beyond five pips. Record UTC+2
   as the predeclared alternative, but only UTC+3 can pass this hypothesis.
   Every event and UTC+3 price check must pass. A failure ends this study without
   returns; no relaxed thresholds, alternate dates or additional fitted offsets.
5. Recheck original October hashes and both 005 clock versions' coverage gates
   (500 hours minimum, six-hour source-month edge tolerance, no unresolved gap
   over one hour). If all pass, create separate 006 dataset versions with byte-
   identical quote files and new provenance referencing this evidence. Do not
   edit the 005 datasets or quality report. This is scoped provisional research
   eligibility, not certification of a year-wide broker/source timezone rule.
6. Freeze all four October clock/cost scenarios and source archive before any
   strategy returns. Use precisely the unchanged 003 base/adverse configs and
   existing engine, independent $10,000 starts, 1:10 modeled leverage, UTC resets
   and hypothetical costs. Evaluate and report all four, reconciling trade P&L,
   costs, final equity, counts and hashes. Clock variants reuse observations.

This study does not claim market completeness, validate broker fills, establish
profitability or authorize demo execution. Preserve 001–005 artifacts, exclude
the consumed 2025 holdout from optimization, and leave reserved November–December
2026 validation untouched. No strategy tuning or real-money mode is included.
