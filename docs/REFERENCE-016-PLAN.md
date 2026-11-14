# Independent reference diagnostics 016 — declared 2026-10-06

Read CONTEXT and PLAN. Preserve stages 008–015 and all failed gates. This is
post-hoc data diagnosis, with no strategy returns, source blending, annual
approval, broker calls or execution. Dukascopy remains stopped after 011.

## Bounded acquisition and schema inspection

Forexite's original archive index lists daily MetaStock ZIPs. Its original
history page describes MetaStock minute bars as CET in winter, CEST in summer;
the ProSuite format instead uses GMT. Do not transfer a format's clock claim
to another format. Retain original HTML, URLs, request outcomes and hashes.
Forex Tester's redistributed GMT data is a different distribution and will
not be downloaded. No 2025 or reserved November–December 2026 data is used.

Download exactly these nine index-listed ZIPs, one ordinary HTTPS request per
file, sequentially, timeout 30 seconds and maximum 5 MiB per response:

- 2022-01-07, 2022-07-08, 2022-11-04;
- 2023-01-06, 2023-07-07, 2023-11-03;
- 2023-03-26, 2023-03-27, 2023-07-14.

Save each outcome exclusively; no overwrite, automatic retries, transport
workarounds, installation or account creation. Stop further archive requests
on HTTP429/403. Missing files remain failures; do not substitute dates. Initial
schema inspection may read header and up to five EURUSD rows only, before
freezing the parser and comparison code. Keep other symbols out of statistics.

## Comparisons fixed before fresh reference statistics

Use reference EURUSD minute OHLC as price/coverage evidence only, never as ticks,
ask quotes, spreads or execution prices. Reject malformed/nonfinite/inconsistent
OHLC, unordered or duplicated EURUSD labels, unexpected dates and ambiguous or
nonexistent CET/CEST times. Preserve original minute labels and row lineage.
The original page does not establish whether labels mark bar start or end;
state this limitation and do not silently optimize a minute shift.

Compare every hour on the six anchor days, including absent hours, with the
bound 015 hourly inventory under its existing candidate UTC mapping. Report
all OHLC differences and reference minute counts. Fixed clock diagnostic uses
UTC hours 06 through 17 inclusive: require all 12 pairs, median absolute close
distance <= 2 pips, at least 10/12 distances <= 2 pips, and the aligned median
strictly smaller than both +/-1-hour control medians (all 12 controls required).
Report failures and ties. All six days are required for a six-day screen pass;
that still cannot certify four annual feeds or independent upstream lineage.
No changes to stage 012's failed activity screen or thresholds follow.

Gap probes: report reference EURUSD minutes at 2023-03-26 UTC23 (using both
local March files) and 2023-07-14 UTC19 and UTC20. Also publish every hour from
those three local files and missing counterparts. Reference presence disproves
a universal closure for that reference feed, not a source-specific closure or
HistData clock hypothesis. Absence alone never proves a market closure.

Freeze plan, new code/tests, timezone bytes, old inventory/provenance hashes
and acquired files before computing these statistics. Recheck both 013 and
015 preflights before reuse and after completion. Validate parser, clock and
missing/control handling with meaningful tests; independently recompute the
saved reference comparison before reporting completion.

## Session evidence and decision

Review primary HistData FAQ/specification and Forexite clock documentation.
Only source-specific historical session/holiday evidence can classify its
closures; generic OTC hours, other brokers' calendars and current terminal
settings cannot certify 2020–2023 HistData coverage. Record unavailable evidence
as unresolved. No new data-quality threshold or annual review is introduced.

Keep performance_evaluation_ready, absolute_utc_certified and
demo_execution_ready false regardless of the selected-window result. Next work
depends on observed evidence, not on forcing the unchanged 009/014 gate to pass.
