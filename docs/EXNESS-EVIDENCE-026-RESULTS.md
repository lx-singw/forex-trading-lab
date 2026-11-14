# Historical evidence review 026 — complete, 2026-10-06

The bounded review does **not** clear the annual data gate. No new quotes,
strategy returns, account connections or orders. The 025 comparison remains
intact; source presence does not establish historical clock or execution rules.

| Requirement | Evidence and applicability | Decision |
| --- | --- | --- |
| HistData historical clock | Current [FAQ](https://www.histdata.com/f-a-q/) and [tick specification](https://www.histdata.com/f-a-q/data-files-detailed-specification/) state fixed EST without DST. No dated target-file exception found. | Conditional Athens mapping remains in conflict; do not approve it from price agreement. |
| Exness clock and account variant | [Tick-history article](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history) was updated September 30, 2026. Its current origin descriptions do not certify exact 2023 EURUSD variant/server. [Current hours](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours) state UTC+0. | Neither current policy nor observed Z syntax independently certifies all historical timestamps. |
| Historical sessions and outages | The hours article was updated September 29, 2026 and shows 2026 holidays. [Forexite export guidance](https://www.forexite.com/free_forex_quotes/forex_history.html) distinguishes CET/CEST from GMT formats, without the required source-specific incident evidence. | March/July 2023 empty intervals remain unclassified. |
| Upstreams and use conditions | [Public quotation policy](https://mini.forexite.com/en/public_quotes.html) and [legal index](https://www.exness.co.za/legal-documents/) do not establish the required historical contributor relationships or archive-specific permissions. | Different providers and public downloads are insufficient proof. Unverified questions remain explicit. |
| Historical executable costs | [Current forex page](https://www.exness.co.za/forex/) describes changing spreads/swaps and possible slippage. No exact historical account-specific fees retrieved. | Keep declared costs and adverse-cost requirements; do not substitute current marketing. |

Six declared queries, twelve primary opens (ten successful, two failed), eight
finds and zero snapshot opens. Public tick-history page timed out; the translated
2020 HistData post returned an internal error. Both failures are retained without
retry. No useful dated official snapshot resolved in the returned bounded results;
this does not establish that none exist. Current examples outside the target years
were not collected as quotes or used for optimization. Source dates, URLs,
limitations and counts are in `reports/evidence-026-notes.json`.

Feasibility: no four-year quote expansion or annual replay by assumption. The
unresolved source-clock conflict, session coverage, exact feed attribution,
upstream evidence and historical costs still block defensible annual evaluation.
Current documentation cannot supply missing retrospective evidence.

Next: the separately declared `STRATEGY-DIAGNOSIS-027-PLAN.md` returns to the
user's strategy objective. Audit entry conditions, regime decisions, abstention
and risk/cost failure mechanisms across **all 30 frozen 2024 development
scenarios**. This can explain losses and inform a later bounded strategy proposal;
it cannot establish an unseen profitable edge. No new strategy selection or
performance runs in 026. Consumed 2025 and reserved Nov–Dec 2026 remain excluded.

Verification: preflight verified all 616 previous bindings, 589 archived members
and 27 external bindings. Final review checks declarations, records, failures and
handoff consistency, then seals a new snapshot. No application code changed or
test suite rerun; the latest recorded software suite is 330 passing tests from
025. Integrity checks establish preservation and documentation consistency,
not independent verification of a provider's claims. Orders remain unavailable.
