# Exness public inventory review 022 — 2026-10-06

The public EURUSD selector advertises all twelve months for each of 2020–2023.
The provider page directly links its archive host, `ticks.ex2archive.com`.
These are concrete inventory leads, not verified quote files or annual approval.
No ZIP, archive HEAD/GET or explicit API request was made.

The [frozen plan](SOURCE-INVENTORY-022-PLAN.md) preceded inspection. Browser use
covered two navigations, 25 inventory selector interactions, one date-calendar
opening, cookie-banner dismissal and one suffix-FAQ expansion. Six web searches,
nine primary page/context opens and three finds stayed within bounds. Queries,
source notes, asynchronous placeholders and exact observations are preserved in
`reports/source-inventory-022-notes.json`.

| EURUSD year | Month choices actually displayed | Actual January link observed |
| --- | --- | --- |
| 2020 | January–December, plus All months | Exness_EURUSD_2020_01.zip |
| 2021 | January–December, plus All months | Exness_EURUSD_2021_01.zip |
| 2022 | January–December, plus All months | Exness_EURUSD_2022_01.zip |
| 2023 | January–December, plus All months | Exness_EURUSD_2023_01.zip |

The [provider-operated public page](https://www.exness.co.za/tick-history/)
loaded without login. Each year's month list was opened separately. Selecting
January produced the four recorded links; 2020 All months also produced an
annual ZIP link. Earlier years therefore support both advertised annual and
monthly options. We observed 48 month choices, not 48 checked files. Six exact
file links were captured; availability, sizes and contents are untested.

Two diagnostic links were observed after selecting 2023 and each month:

- https://ticks.ex2archive.com/ticks/EURUSD/2023/03/Exness_EURUSD_2023_03.zip
- https://ticks.ex2archive.com/ticks/EURUSD/2023/07/Exness_EURUSD_2023_07.zip

March addresses transition/empty-hour questions; July addresses sparse history
and the July 14 broker truncation. These months come from existing data-quality
questions, not return-based selection. Initial placeholder anchors were not
counted until actual ZIP hrefs appeared. No download control was activated.

Seven EURUSD variants were visible. Exact `EURUSD` was inspected; no blending
with EURUSDm, cent, raw or zero variants. Public suffix guidance generally maps
no suffix to Pro (with Zero exceptions), m to Standard and c to Standard Cent.
That guidance does not establish historical cost equivalence. A link from the
official page establishes provider attribution of the archive host, not legal
domain ownership or independent underlying liquidity.

[Tick-history documentation](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history)
specifies provider/symbol/timestamp/bid/ask CSV columns and different MT4 server
families for account categories. It says archive server selection is unavailable
and latency can differ. Its Personal Area login instructions coexist with our
observed anonymous public selector; anonymous file access remains untested.

[Current session documentation](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours)
states UTC+0 servers, seasonal rollover, mostly US DST and variable maintenance.
Its static holiday list is 2026. The embedded public schedule loaded with the
current week in local GMT+02:00; its date popup exposed a previous-month control.
No historical range was submitted. No 2020–2023 holiday/outage calendar or old
tick clock was certified. Do not classify old quote gaps from generic hours.

The [South Africa legal list](https://www.exness.co.za/legal-documents/)
provided disclosure, privacy/risk and other documents, without a tick-specific
archive license in the inspected list. Provider pages offer indicative,
informational downloads. Full data reuse/redistribution permissions remain
unverified; this review preserves brief factual notes, not copies of articles.
The [current forex page](https://www.exness.co.za/forex/) cannot establish old
costs or sessions. Bounded search failure is not proof that evidence is absent.

Existing 020 migration verify passes. Previous 021 source/report/input/archive
bindings and new plan/budget/link consistency are verified in
`reports/source-inventory-022-review.json`; seals and final snapshot are
`reports/source-inventory-022-*`. Only editable handoff documents change; frozen
engines, reports and datasets remain intact. No code changed or suite rerun;
latest recorded software result remains 299 passing tests.

Next: separately declare one ordinary, no-retry HEAD per observed March/July
URL, with timeouts and provider-wide stop on 403/429. If access permits, declare
a bounded diagnostic acquisition preserving original ZIPs, strictly parsing
bid/ask/UTC labels and auditing complete months independently before targeted
comparisons. No four-year download by assumption, interpolation, source blending
or market returns. Clock continuity, session gaps, upstream independence,
historical execution costs and profitability remain unverified. Annual gates,
demo execution and order placement remain unavailable. No accounts, credentials,
payments, provider contact or stopped FXCM/Dukascopy endpoint retries occurred.
