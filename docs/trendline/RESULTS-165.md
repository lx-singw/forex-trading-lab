# Sprint165 — prospective source/run qualification checks

16 November 2026 (Africa/Johannesburg). **171 tests pass together:37 new and134
existing**, zero failures/errors, in2.973seconds. The current plan freezes/checks
through the public CLI and retains28 UNAVAILABLE/null market cells. Phase2 actual
source acceptance remains open. Baseline ae3ecbd was pushed before this sprint.

## Implementation

New trendline/study.py adapts unchanged145 chronology, exposure, evidence and
cost checks. It adds the full trendline scope and source/run requirements without
rewriting the previous16-cell preflight, strategies, accounting or native code.
[Usage](STUDY-165-USAGE.md), [source findings](SOURCE-165-FINDINGS.md) and
[verification](verification-165.json) describe scope and limitations.

The canonical config/trendline-study-v1.json assigns no source, dates, file hashes
or geometry. It is a prospective B sensitivity draft, not an executed optional
batch. The older163 config is retained as a coarse-lint example only. No strategy
parameters or economic variants are changed.

New checks retain24-month chronological partitions,253-bar and390-H4 history,
protected/seen dates, prior/undated exposure, complete alternative counts,
28-cell track and paired-analysis budgets, B/Q and geometry/spread restrictions,
scoped price/entry-spread evidence, latency assumptions, uncertainty and
prospective in-partition liquidation. Counts/hashes cannot self-qualify a source.
Endpoints are checked without guessing a source's H1 grid from UTC minutes.

Metadata freezes bind raw plan bytes, content, policy and source hashes; even a
changed whitespace byte or false-vs-zero flag fails a freeze check. Sources are
rechecked before creating output. Evidence hashes are never opened as paths.
No market-price-file, network, credential, account or submission branch is added.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -v
```

37 new tests cover missing/complete claims, all28 cells in each track, immutable
legacy behaviour, calendar/leap-day chronology, warmup/FXR limits, protected and
exposed dates, uncertainty/latency, evidence scopes, budgets, costs, boundary
timestamps, freeze corruption/source races, exclusive paths and the public CLI.
The other134 checks are41 price164,34 data163,28 study145 and31 sessions146.
The unrelated full trading suite and unchanged56-test120 suite were not repeated.

Invented metadata exercises include complete B/Q claims, insufficient FXR history,
exposed/protected validation, exhausted budget and an out-of-partition endpoint.
Every exercise remains unavailable; these are preflight outcomes, not market
trades or strategy results. Current CLI plan/freeze/check output and test logs
remain ignored in reports/trendline-165/. Portable summary/hashes are committed.

## Actual source outcome

The current [Basic pricing](https://twelvedata.com/pricing) lists internal
non-display use, improving the Twelve Data access/use lead. Applicability of the
use/retention terms to this agent-assisted research, historical candle semantics,
entry-spread coverage and actual history still require review. No paid service,
account signup or broker account was created.

One unauthenticated earliest_timestamp metadata URL was inaccessible through the
web tool. No provider HTTP status/body was established, so no authentication
denial is claimed. No retries or alternate transport followed. The specifically
named key was absent in this WSL process environment; other private configuration
was not scanned and no credential value was disclosed. No price request occurred.

Incidental undated provider/search price displays remain documented exposure;
they are not copied into research or assumed to be untouched validation. Old
provider stops, expired136, false156 grant and protected dates/routes persist.

## Remaining dependency

A concrete permitted EURUSD historical export/access with time, price, spread,
coverage and use evidence is still needed to accept Phase2. All28 new and16
earlier market cells stay unavailable. No Phase3 acceptance or collection grant
follows from this metadata software. The intake plan/checker is ready to review
actual source evidence; more invented fixtures cannot replace that evidence.
