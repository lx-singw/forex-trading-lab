# Daily reference098 — offline importer and chronology verified

Implemented an isolated local JSON importer, immutable observation/policy types,
integrity inspection and an availability selector. The corrected active regression
suite passed2,011 tests:1,975 retained plus36 new. The focused36-test run also passed.
Both runs had zero failures, errors or skips; no new exclusions. No market dataset,
strategy return or trading profit was produced.

The versioned schema declares base/quote direction, positive finite Decimal prices,
observation date, vintage identity, first publication, version availability,
retrieval time, source artifact digest and evidence references. Policies have their
own dates, explicit calendar, timezone and publication/revision/use descriptions.
Embedded source bytes are hashed and matched against the parsed records. This
checks local consistency; it does not authenticate a publisher or certify historical
rights, clock interpretation, coverage or revisions. No evidence URL is fetched.

Synthetic selection admits only the exact fixed098 invented source and policy.
Changing a role label, price, source digest or typed object cannot admit another
source. Its2030 dates, releases, prices and holiday are invented. They are not ECB
or other market observations. Final-vintage inspection has a separate type and
cannot enter the selector, even when a file declares release history or a policy.
Missing history may be inspected, but never becomes historical-data qualification.

At each UTC decision instant, a synthetic value is eligible only when its version
availability is strictly earlier. Input order is irrelevant; identical duplicates
are counted and deduplicated, conflicting or ambiguous vintages reject. A later
revision cannot replace the version selected for an earlier decision. Missing
observations are explicit results; no carry-forward, interpolation or guessed release
schedule. Saving normalizes timestamp offsets and order; reloading preserves the
selected version. Canonical saves omit redundant duplicates, so their original
duplicate count is an import diagnostic rather than retained record history.

| Invented decision | Outcome |
| --- | --- |
| Exactly at first publication | Missing: not yet available |
| One microsecond later | Original v1 |
| Exactly at correction availability | Original v1 |
| One microsecond after correction | Corrected v2 |
| Declared non-publication day | Missing: non-publication day |
| Expected publication day with no record | Missing: no observation |

The saved demonstration has4 invented versions across3 observation dates. Eight
manually specified cases produced4 selected and4 missing results. An independent
checker compared all case identities, reasons and versions against explicit
expectations and checked every selected availability timestamp precedes its
decision. No prices, returns, rankings or trades appear in the demonstration report.

New files:src/forex_demo_lab/daily_reference_098.py,
tests/test_daily_reference_098.py,scripts/daily-reference-098.py and
data/fixtures/daily-reference-098.json. The local script provides `fixture`, `demo`
and `inspect` commands; outputs use exclusive creation. The module has no network,
broker, native-process or execution imports and is not connected to009/020/093
strategy runners. Inspection reads one supplied local bounded UTF-8 JSON bundle.

Verified097 predecessor49 bindings/48 archive members, all498 retained bot/test/
config/script hashes unchanged and each new source hash unchanged across testing.
Full testing used the existing corrected084R2 active-suite selector, retaining the
same43/36 previously retired fixtures and preserving old failed reports. That
regression includes existing Linux g++ portable-header checks; no standalone native
build or MetaTrader compiler/runtime/deployment action occurred. Frozen098 no-compiler
scope was applied to standalone/native/MT5 work while retaining its requested full
regression checks. No settings, logs, accounts or order controls were accessed.

The remaining obstacle is qualifying historical market inputs. Current097 documents
do not establish the target series schema/direction,2020–2023 publication policy,
coverage or historical vintages. The next separate099 proposal assesses primary
Federal Reserve H.10 documentation as another daily-reference research source;
no request was made here and it is not a retry of failed ECB endpoints. It must
establish evidence before any acquisition or new market-selection implementation.

Original003 costs and028/030 strategy rules remain. Old failures/provider stops,
2025 exclusion,Nov–Dec2026 reservation and October quarantine are unchanged.
Native090 stays closed. Zero external requests, market rows/returns, SDK/MT5/MetaTrader-
compiler/deployment/log/order/receipt/grant action. Historical market eligibility, profitability,
runtime and orders remain unavailable. Daily reference rates cannot establish
spread costs, stop fills or broker trading profit. No UI action is needed.
