# Diagnostic correction 013 results — 2026-10-01

Each October archive contains an entire source hour replayed verbatim. A
separately frozen correction checks every record field before collapsing only
the declared second copy in a diagnostic stream. Canonical archives and both
copies remain intact. Original row ranges give explicit correspondence to the
retained rows. All other events, same-ms quotes and gaps remain preserved.

| October archive | Exact replay rows collapsed in diagnostic stream |
| --- | ---: |
| 2020 | 3,800 |
| 2021 | 1,695 |
| 2022 | 4,625 |
| 2023 | 2,559 |
| Total | 12,679 |

Eight complete March/October reviews consumed 23,711,389 source rows and produced
23,698,710 diagnostic events, all monotonic. Only JSON diagnostics were published;
there is no eligible simulator CSV. Changed replay content, incomplete blocks,
unexpected reversals, invalid quotes or ambiguous clock times cause rejection
before report publication. Prices are not altered or fabricated.

The candidate applies European winter/summer dates to source labels plus seven
hours, using frozen Europe/Athens rules as a representative calendar. This is a
post-hoc scoped hypothesis, not provider-location or full-year UTC certification.
EU transitions occur at 01:00 UTC on the last Sundays of March and October, before
the late-Sunday archive defects. See the
[primary EU calendar rule](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32000L0084).

Of 48 requested boundary hours, 40 have candidate and broker reference closes.
**39/40 agree within one pip; maximum difference 1.3 pips**, at 2022-03-27
21:00 candidate UTC. All differences and adjacent-hour alternatives remain in
monthly reports. Four March hours lack HistData quotes despite a broker bar;
four autumn hours lack both sources and remain unclassified. This supports the
transition diagnosis but does not approve annual clocks. The earlier statement
that all 40 were within one pip was too broad.

A separately declared gap probe captured four missing March broker hours:

| Raw broker interval start | Original ticks |
| --- | ---: |
| 2020-03-30 02:00 | 3,968 |
| 2021-03-29 02:00 | 1,511 |
| 2022-03-28 02:00 | 1,533 |
| 2023-03-27 02:00 | 2,118 |
| Total | 9,130 |

All four bid OHLC reconstructions exactly match the frozen broker H1 reference
under the unchanged 0.05-pip screen. Independent SQL agrees with all exported
aggregates. Captures checked actual demo type; recorded Algo Trading flags were
off. Quotes remain separate raw-label broker data, with no insertion into
HistData. Same-feed agreement verifies aggregation, not independent completeness
or absolute UTC.

**209 tests passed**, including eight correction tests for replay lineage and
content, incomplete blocks, retained ordinary duplicates, calendar ambiguity,
source scope and preserved March gaps. Independent arithmetic checked eight
calendar endpoints. All eight monthly report hashes, row accounting, four gap
screens and 100 prior recovery report bindings were checked. Frozen 012/013
code, plans and original evidence remain unchanged.

Evidence:

- `reports/correction-013-ledger.json`: declared source/correction bindings.
- `reports/correction-013-review.json`: all eight monthly reports.
- `reports/correction-013-gap-probes.json`: four separate captures.
- `reports/correction-013-checks.json`: independent final checks.
- `reports/correction-013-final-source-02.json`: completed source snapshot.

Performance remains blocked. The unchanged eleven clock screens did not all
pass (HistData 7/11, broker 2/11, both 1/11). July 14 still has a truncated broker
tick hour and an hour missing in both candidate feeds. Other February–July
coverage flags and unverified historical costs remain. No new returns were
computed; a robust profitable edge has not been established. Orders remain
unavailable.

Next: declare source-lineage and coverage rules for separately reviewed
normalization, retain unresolved periods explicitly, and implement the frozen 009
chronological runner with eligibility checks. Software implementation can
proceed; actual performance must wait for the data gate. Keep the five strategies,
training-only selection and cash fallback fixed. Consumed 2025 is excluded from
tuning; November–December 2026 remains reserved.
