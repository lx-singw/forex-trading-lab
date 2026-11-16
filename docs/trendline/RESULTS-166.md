# Sprint166 — workflow correction and Phase3 causal pivots

16 November 2026 (Africa/Johannesburg). **198 tests pass together:27 new and171
existing**, zero failures/errors, in5.188seconds. Six invented CLI exercises agree
with written expectations. Phase3 software acceptance passes; actual market-source
admission remains open. Baseline9860d22 was pushed before this sprint began.

## Corrected workflow interpretation

The original full roadmap's section0 explicitly says Phases1-9 are software and
Phase10 is first contact with data. Its Phase2 acceptance bullets cover causal
aggregation, missing-child/DST/session semantics, protected loading and B labels.
The160-165 status notes incorrectly added actual source admission as a prerequisite
for building Phase3. Protocol revision4 corrects that ordering before any market
trial. No economic rule, parameter, protected date, source route or grant changes.

Phase2 engineering acceptance is supported by163-165 tests and166's explicit
holiday/maintenance cases. Actual source/use/time/price/spread/coverage qualification
is still unestablished. Continue the authorized software phases with invented
inputs; do not use that acceptance to admit prices, compute actual counts, run a
market study or activate an account. Prior reports/source findings stay preserved.

## Delivered

New trendline/pivots.py and its [CLI](PIVOTS-166-USAGE.md) implement strict delayed
radius3 H4/D1 pivots. The raw journal records occurrence-bar close separately
from confirmation availability and publication ordinal. Equality and dual-extreme
centres are excluded. Later stronger same-kind points update only a diagnostic
alternating view; raw confirmations remain immutable.

Only contiguous scheduled neighbours can confirm. Missing bars reset the window
and segment the display; declared closures preserve adjacency. Late/reordered
backfill is explicitly unsupported and rejects, rather than rewriting history.
Latest identical retries are idempotent; conflicting duplicates, wrong frame/
clock/lineage, source changes and bounds reject before mutation.

The standalone CLI uses unchanged163 loading/aggregation and its validation unlock
boundary, preserves B/geometry labels, supports a prefix cursor and refuses output
overwrite. No market kind or bypass is added. Existing Elliott strategies,
accounting, data/price/preflight code, configs and original80 fixtures are unchanged.

## Verification

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -v
```

27 new checks include every-prefix batch parity on100 bars in each of H4/D1,
handwritten seven/49-bar examples, future suffix and identity invariance, gaps,
declared closures, late backfill, immutable history, alternating supersession,
same-clock ordinals, low-precision context, malformed input, bounds, the public
CLI and source/validation refusal. The171 existing checks are unchanged165/164/
163/145/146 suites. Unrelated broad suites and unchanged120 accounting are not
rerun. This is software evidence, not a win rate or complete strategy test.

| Invented CLI case | Bars | Pivot indices | Confirmation indices |
| --- | ---: | --- | --- |
| H4 long/short golden examples, each | 49 | 17,20,23,26,29 | 20,23,26,29,32 |
| D1 low/high seven-bar examples, each | 7 | 3 | 6 |
| H4 missing scheduled bar22 | 48 | 17,26,29 | 20,29,32 |
| H4 before seventh confirming bar | 6 | none | none |

The first local exercise helper invocation lacked the inherited PYTHONPATH for
its child CLI and failed before producing a pivot export. Its ignored partial
input directory remains. The explicit PYTHONPATH invocation succeeds for all six
examples under reports/trendline-166/examples-002/. No production correction or
expected-output change was required. Logs/large outputs remain ignored; portable
[verification-166.json](verification-166.json) records counts and source hashes.
The identity audit uses Git's existing text filters for a pre-existing mixed-line-
ending reference file and records current working-byte SHA256 bindings. No legacy
line endings or tracked reference content were rewritten.

## Current completion and next sprint

Phase3's software acceptance is complete. Next Phase4 sprint: exact line geometry
and ATR_SMA14, then enumeration/validity/ranking/lifecycle in subsequent increments.
No actual source file or provider request was accessed here. Actual source/run
admission remains required before Phase10 market counts and later evaluation;
all28 new/16 prior market cells, native grants and orders stay unavailable.
