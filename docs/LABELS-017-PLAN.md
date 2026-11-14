# Minute-label diagnosis 017 — declared 2026-10-06

Read CONTEXT/PLAN and completed reference 016. This is post-hoc diagnosis on
already acquired data. Preserve every old failed gate and frozen file. No new
market downloads, broker calls, source mixing, strategy returns or execution.

Use exactly six existing 016 anchor days: 2022-01-07, 2022-07-08, 2022-11-04,
2023-01-06, 2023-07-07, 2023-11-03. Compare original reference minute labels
in UTC10:01 inclusive through UTC14:59 exclusive: 298 labels per day. This
window has a one-minute buffer inside all existing raw12–18 broker captures.
No date substitution or additional event selection after results.

Three interpretations for a reference label T: end label uses tick interval
[T-60s,T), literal start uses [T,T+60s), future control uses [T+60s,T+120s).
Publish every label and all OHLC/close distances for every interpretation,
including absent reference/tick minutes. Do not fill missing quotes, carry
prices across minutes, count fabricated zero-range bars or sort input ticks.

Two separate tick sources:

- Existing 012 actual-demo broker captures, with their existing hypothesized
  raw-label offset +2h for January/November and +3h for July subtracted. Those
  captures do not independently certify UTC or annual completeness.
- Existing 015 diagnostic candidate tick CSVs for the corresponding six months,
  using their unchanged candidate timestamps and original row identifiers.

Aggregate bid and ask separately, retain quote counts/first/last source rows
and exact-ms ordering. Compare reference OHLC with bid; reference original
bid semantics remain unverified. Neither source may patch or replace the other.

For fair comparisons, also report all three median absolute close distances on
the identical set of labels with reference and all three tick minutes present.
The declared relative end-label screen requires >=240 such common labels,
end-label median <=2 pips, and both alternative medians >=end median+0.25 pip.
All six broker days must pass for an empirical broker-relative inference.
HistData day screens are separate corroboration diagnostics; missing labels,
failed days and coverage counts must be published even if broker screens pass.
No inference establishes an original-provider guarantee, independent upstream
lineage, annual UTC, session calendar, historical spreads/costs or profitability.
Do not revise 016 comparisons or relax its failed screen.

Before fresh statistics freeze new source/tests/plan, six cached capture files
and metadata, six candidate CSV/inventory/provenance/seals, reference lineage
CSV/provenance, used frozen source bytes and old ledgers. Verify original 013,
015 and both 016 preflights. Tests must cover exact interval boundaries,
same-ms quotes, gaps, order/price rejection, fair common-label comparisons,
missing pairs and ambiguous/insufficient evidence. Independently reconstruct
selected minute aggregates and all distances from the bound tick streams.

Primary documentation review may continue; preserve retrieved pages/outcomes.
If no precise original MetaStock label definition is found in reviewed pages,
say so. Separately research publicly accessible complete bid/ask sources for
2023, recording provider schema, clock, coverage and access limitations before
any future acquisition. Dukascopy remains stopped after 011; no access
workaround, paid service, registration or account creation. 2025 stays excluded;
November–December 2026 remains reserved. All readiness flags remain false.
