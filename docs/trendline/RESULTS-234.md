# Sprint 234 · EV decision and Exness follow-up

27 November 2026. Complete the EV public-evidence check for the frozen
Level B delayed-entry trial. The review required a dated EURUSD session
calendar, permission for the study's use of the exact archive, and evidence
to place completed H4 decisions and paired H1 openings on a common clock.
EV remains unqualified. Exness public EURUSD tick history is the next
candidate. [Frozen trial](RESULTS-230.md) · [EV timing sensitivity](RESULTS-233.md)

## EV evidence and decision

| Requirement | What the public evidence establishes | What remains open |
| --- | --- | --- |
| Friday H4 completion | EV labels its precomputed resamples with bar opening times. Dukascopy's JForex API describes separate bar and tick callbacks. Its platform settings document skipping ticks under load or queueing them for later processing. [EV catalogue](https://evtradelabs.com/data) · [JForex callbacks](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IStrategy.html) · [JForex queue policy](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/system/IPreferences.Platform.PreferencesSettings.html) | A receipt trace or publication specification tied to EV's exact bars and the Friday-to-Sunday boundary. Even a JForex historical replay would establish timing for its configured replay. EV publishes resamples built by its own pipeline. [JForex tester tick modes](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/system/ITesterClient.DataLoadingMethod.html) · [EV methodology](https://evtradelabs.com/about) |
| Sunday opening bid and ask | The retained H1 and M5 comparison establishes agreement between the two products, with two late first M5 labels at development Sunday reopenings. [Timestamp audit](RESULTS-231.md) | Formation from a single first quote and availability of that pair at the selected scheduled H1 open on the decision clock. |
| Holiday closures | Dukascopy's December 2019 and December 2020 notices direct users to the trading-breaks calendar. Its December 2020 leverage notice covers different events. The earlier reconstructed holiday scenario fits all 60 missing ordinary H1 slots. [2019 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-dbl201708/) · [2020 notice](https://www.dukascopy.com/swiss/english/about/ournews/market-closures-on-christmas-and-new-year-2020) · [Leverage notice](https://www.dukascopy.com/europe/english/about/ournews/weekend-leverage-at-christmas-and-new-year/) · [Holiday scenario](RESULTS-232.md) | The effective UTC closure and reopening edges for the exact dates and feed. |
| Research use | EV's data catalogue states that its downloadable files are free with attribution. EV's general licence clause concerns purchased software. Dukascopy's website terms allow personal non-commercial downloads subject to their restrictions and separately restrict derivative use and distribution of website materials. [EV data licence](https://evtradelabs.com/data) · [EV general terms](https://evtradelabs.com/terms) · [Dukascopy website terms](https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/) | Which upstream terms apply to EV's specific redistribution and the planned offline research use. The review found no public upstream grant tied to these resamples. |

Close the public-evidence pass for EV. Reopen the candidate when evidence
addresses the unmet requirements. The delayed-entry rule remains frozen.
Phase 10 remains `UNAVAILABLE` with null actual counts. The 60-opportunity
threshold per strategy and cost profile still applies to a qualified
development count. [Phase 10 preflight](RESULTS-215.md) · [Frozen trial](RESULTS-230.md)

## Start with the retained Exness evidence

Exness explicitly offers its public tick history for backtesting. Its
public download describes paired bid and ask ticks and calls the archive
indicative. The Personal Area documentation identifies several account-type
feeds and says their timing can differ. The connection between those
feeds and the exact public unsuffixed EURUSD archives remains open.
Previous checks verified delivery metadata for all three candidate years
and audited the January and July 2022 samples.
[Public archive](https://www.exness.com/tick-history/) · [Backtesting guidance](https://www.exness.com/order-execution/) · [Personal Area feed description](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history) · [Retained archive inventory](RESULTS-196.md) · [January and July diagnostics](RESULTS-213.md)

Use the nine retained January and July weekend edges to check what
Exness's source labels add. Apply the Sprint 220 ordinary-hours scenario
and use the same assumed two-second delay as the EV sensitivity check.
With release at Friday's H4 close, the frozen trial selects the clipped
Sunday opening at :05 in all nine samples. With release anchored to the
first archived Sunday source label, it selects the next whole hour in all
nine, 55 minutes later. That selection precedes the next H4 expiry and
liquidation. In the second case the modeled decision precedes the selected
opening by 3,029.912 to 3,280.460 seconds. In the first case every selected
:05 slot lacks a pair with an exact boundary source timestamp. These are
schedule and source-label observations. Eligibility of the later pair
and actual strategy receipt remain unverified.
[Calendar scenario](RESULTS-220.md) · [Weekend source labels and strict-opening ceiling](RESULTS-222.md)

The next Exness review should start with the exact public archive's feed,
timestamp meaning and dated quote schedule, including holidays and
quote-only intervals. Use the 2022 dated ordinary hours and the two
retained sample receipts as cross-checks. Review retention and derivation
terms and establish how the proposed H4 availability model and selected
opening pair can be supported. The current schedule help describes UTC+0
server time and date filtering. The prior public widget check exposed
only October–November 2026. Its schedule help supplies no effective
rules for the proposed historical archive. Preserve Exness as a separate
source and use its own price, spread and calendar evidence.
[Dated schedule evidence](RESULTS-197.md) · [Current schedule help](https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours) · [Archive use review](RESULTS-199.md)

## Verification

The independent calculation checked the four retained report digests,
matched the nine source labels to their calendar slots, and verified
opening selection and expiry. It used the Sprint 220 calendar and
Sprint 222 ceiling reports and the Sprint 203 and 204 source summaries.
All 52 targeted tests passed.
The command below regenerates the canonical metadata status at a fresh
path. Its output matches Sprint 233 byte for byte.

```sh
PYTHONPATH=src python3 tools/signal_count.py status config/trendline-study-v1.json new-status.json
```

The sprint used public documentation and retained metadata. Search
results incidentally displayed archival EURUSD examples, including
January 2020 and November 2025 material, and legacy platform examples.
The study and its counts did not use those prices. No price archive was
downloaded. [Exposure policy](RESULTS-202.md)
