# Sprint 202 · Prior exposure and trial history

18 November 2026. The user reported **no known exposure** to EURUSD
prices, charts, strategy tests or rule-setting examples from 2018–2019.
The lab’s tracked-record search also found no dated price inspection or
strategy run for that span. These findings support retaining 2018–2019
as a candidate validation period. The observation dates of earlier incidental
price displays still require review before the period can be certified as
unseen. [Tracked-record review](RESULTS-201.md)

## Recorded lab evidence

| Scope | Recorded activity | Effect on study review |
| --- | --- | --- |
| 2015–2019 Exness annual files | The selector showed file links and the lab checked response headers. The user’s statement covers the 2018–2019 validation candidate. | Delivery and prior-knowledge evidence for the proposal. CSV coverage and full exposure history remain unresolved. [Archive inventory](RESULTS-200.md) |
| 2020–2023 HistData source labels | The lab processed 48 monthly tick archives in an earlier diagnostic, with provisional clock interpretations. | Recorded price exposure in the labeled years. Candidate UTC boundaries need independent confirmation. [Normalization results](../NORMALIZATION-015-RESULTS.md) |
| March and July 2023 Exness source labels | The lab audited both monthly archives and later compared specific disputed hours. | Recorded price exposure separate from strategy evaluation. [Archive audit](../EXNESS-024-RESULTS.md) · [Coverage comparison](../EXNESS-COMPARISON-025-RESULTS.md) |
| 2024 and 2025 | Earlier EURUSD strategy simulations used 2024 for development and viewed the 2025 holdout. One later comparison ran five strategies under two cost profiles over three 2024 windows. | 2024 remains development-only. The 2025 validation exclusion follows the consumed-holdout rule. [Experiment 001](../EXPERIMENT-001-RESULTS.md) · [Comparison 008](../COMPARISON-008-RESULTS.md) |
| Undated documentation displays | The 161 and 165 source reviews recorded incidental EURUSD ticker or example prices with unknown observation dates. A later clearly dated example concerned a different variant in excluded 2025. | Keep the undated observations visible and their complete count unknown. The two reports may refer to overlapping displays. [Source reconnaissance](SOURCE-CANDIDATES-161.md) · [Source review](SOURCE-165-FINDINGS.md) · [Later example](RESULTS-197.md) |

The recorded TRL_V1 market-cell count is zero. Strategy variants and cost
profiles exercised in the invented fixtures are software verification. The
earlier lab’s historical tests belong in the exposure review, while the
trendline cell budget applies to actual TRL_V1 market runs. The complete
attempted-alternatives history remains unverified. [Phase 10 counter](RESULTS-194.md) · [Frozen trial rules](PROTOCOL.md)

## Preflight outcome

The canonical plan still leaves `history.complete` false and the undated
exposure and tried-alternatives counts null. A copy with the earlier proposed
dates has no chronological date block under the frozen restrictions. In a
separate conditional check, supplying a nonzero undated count produces
`undated_price_exposure_requires_validation_review`. This shows the effect
of the recorded uncertainty without assigning it a count or date in the
canonical plan.

All 65 targeted preflight tests passed. A fresh metadata freeze and check
bound the canonical plan and reported all 28 cells `UNAVAILABLE` with null
returns. Phase 10 likewise reports `UNAVAILABLE` with null actual counts.
Local metadata checks are under the ignored `reports/trendline-source-202/`
directory.

The Phase 10 development count still needs an admitted source with the
exact archive’s feed and timestamps, dated session exceptions, applicable
use terms and verified warmup and development coverage. The 2018–2019
exposure review governs a later validation decision. [Source qualification](RESULTS-201.md) · [Draft source inquiry](RESULTS-199.md)
