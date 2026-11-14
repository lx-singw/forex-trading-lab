# Research 007 — explicit October interval mapping

Declared 2026-10-01 before inspecting the new event/window statistics. Earlier
005/006 failures remain unchanged. Test one scoped hypothesis: October quotes
before the October 26–27 weekend use HistData UTC-4 / broker UTC+3; quotes after
that weekend use HistData UTC-5 / broker UTC+2. This is not a named timezone or
a certified annual DST rule. The exact change instant within a quote-free
weekend is unobservable; only the mapping of observed quotes can be checked.

## Fixed checks

1. Fresh event statistics: October 24 claims at 08:30 Eastern / 12:30 UTC
   (https://oui.doleta.gov/press/2024/102424.pdf) and October 29 JOLTS at 10:00
   Eastern / 14:00 UTC
   (https://www.bls.gov/news.release/archives/jolts_10292024.htm).
   Earlier studies parsed the archive and captured October 29 but did not
   inspect these event-minute statistics. Use HistData event/control labels
   08:30/07:30 on Oct 24 and 09:00/10:00 on Oct 29; broker labels 15:30/14:30
   and 16:00/17:00 respectively. Require positive control range/count and at
   least 3x its range and 2x its count at the event in each feed, on both dates.
   An inconclusive/failed check blocks performance; no alternate dates or fits.
2. New guarded broker captures: October 24, 25 and 28 raw 12:00–18:00. Reuse
   original October 29 raw 12:00–18:00 for its fresh event statistics. Compare
   all six hourly closes on each of October 24/25/28 against the proposed
   interval-mapped HistData quotes. Require all hours, >=95% within one pip,
   maximum <=5 pips in each window. Assert exact declared capture bounds.
3. Capture the broker weekend in contiguous raw-label windows Oct 25 18:00 to
   Oct 27 18:00, then to Oct 28 06:00. Require no broker quotes from Oct 26
   06:00 through Oct 27 18:00 and observed quotes on both sides. Require no
   HistData quotes from source Oct 26 00:00 through Oct 27 12:00 and observed
   quotes on both sides. These checks bracket an operational boundary, not
   an exact clock-change time or certified market closure.
4. Conversion uses source-label Oct 27 00:00 as a representative cutoff inside
   those quote-free intervals. For HistData apply +4h before, +5h at/after;
   for broker apply -3h before, -2h at/after. Reject quotes inside the declared
   quiet intervals, out-of-October labels, missing sides, sequence changes or
   nonmonotonic output. Preserve all prices and event ordering. Test both sides
   of the cutoff, same-millisecond events, ambiguous/quiet-interval quotes and
   unchanged outputs for alternative cutoffs within the observed empty interval.
5. Only if every event/window/boundary check passes, build a separate 007
   HistData dataset from the unchanged source archive with explicit interval
   provenance. Recheck >=500 hours, month edges within six hours, no unresolved
   gaps >1h, and unchanged quote/sequence/count coverage. The previous constant-
   clock 005 datasets and failed gates remain unchanged and ineligible.
6. If eligible, freeze base/adverse scenarios before returns with unchanged
   003 configs and strategy engine. Independent $10,000 starts, modeled 1:10
   leverage, UTC resets and hypothetical costs. Archive source and publish both
   reports with complete accounting/hash reconciliation. No constant-clock
   performance comparison is authorized by this study.

Eligibility is provisional development research only. Do not infer profitability
or activate demo execution. No orders, terminal changes, paid services, 2025
holdout optimization or access to reserved November–December 2026 validation.
