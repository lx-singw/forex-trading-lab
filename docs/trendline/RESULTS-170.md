# Sprint170 — automatic per-bar lifecycle integration

17 November2026 (Africa/Johannesburg). **327 unique checks pass:24 new and303
retained**, verified across the new suite, focused correction run and regression
run described below. Seven invented CLI exports and two API lifecycle exercises
match expectations. Baselinef523660 was pushed before this sprint began. Phase4
remains in progress pending its complete acceptance matrix/boundary review.

## Delivered

New `trendline/engine.py` and [replay CLI](REPLAY-170-USAGE.md) integrate incremental
bar/pivot/indicator observations, full/action line inspection, local selection and
the lifecycle journal. Every publication stages the inspector and journal together
before publishing immutable frames and per-line revisions. Invalid inputs,
conflicting retries, source/code changes and software bounds cannot partially
publish a bar. Identical latest retries are no-ops.

The engine admits explicitly supplied pre-existing triggers before current pokes;
then handles age retirement, new registrations, aliases and strict-subset
retirement. A poke beats age retirement. New geometry/touch revisions cannot
backdate same-bar triggers. No setup predicate, economic trade selection or order
submission is implemented. The declared-trigger interface remains labelled as
such, with entry readiness/trigger detection/orders false.

Protocol revision5 records the deterministic alias policy before automatic engine
fixtures: use registered group history from before the bar. Fresh touch sets get
fresh groups unless exactly covered by the union of prior same-profile/frame/kind
strict-subset groups; that alias case preserves consumed union. A mere subset
replacement does not merge groups. No numerical parameter, strategy activation,
protected period, source grant or market trial changes.

Search incompleteness blocks registration/eligibility/trigger admission while
observable pokes and age retirement still record. Missing interval coverage blocks
old instances without inventing a wick. Known closures preserve adjacency. The
historical VALID state is distinct from current eligibility; temporary caps can
clear without resetting first validation/group identity. Terminal instances never
reopen. Candidate/pair rejection diagnostics, selection explanations and immutable
revision chains remain available per frame.

Four existing trendline adapters evolve deliberately:167 geometry gains forked
frontiers;168 inspection gains a shared incremental Inspector;169 selection can
consume that inspector;169 journal gains staged copies/read-only queries and
fact-recording during capped search. Frozen declaration guards compare canonical
JSON bytes directly, retaining separately bound source SHA256. Existing batch
interfaces and numerical rules are retained. Elliott/account sources, source
configs, original80 fixtures and prior evidence are unchanged.

## Verification and corrections

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_engine_170 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_engine_170.Engine170Tests.test_cli_prefix_checkpoint_resume_matches_uninterrupted_and_refuses_overwrite test_trendline_engine_170.Engine170Tests.test_d1_and_bounce_profiles_have_no_action_break_exception test_trendline_engine_170.Engine170Tests.test_cli_validation_and_market_kinds_cannot_bypass_loader -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_selection_169 test_trendline_lines_168 test_trendline_geometry_167 test_trendline_pivots_166 test_trendline_study_165 test_trendline_fills_164 test_trendline_data_163 test_elliott_study_145 test_elliott_sessions_146 -q
```

The initial24-scenario run took491.050seconds:22 passed and two failed. The CLI
passed163's `(document, raw_sha)` reader result directly to restore; it now unpacks
the document. The D1 fixture placed its first pivot before ATR warmup; its touch
indices move past warmup while the frozen rule remains unchanged. The corrected
two checks and loader refusal pass in a focused three-test run,35.549seconds.
The303 retained tests pass separately in153.515seconds, zero failures/errors.
The Engine algorithm was unchanged after the initial new-suite run; only the
CLI document unpacking and D1 fixture inputs changed. No unresolved failures or
claim of a single combined327-test run remains.

New evidence includes mirrored G35 formation47/poke48; declared consumption before
poke and restart; same-formation-bar rejection; incremental/batch equality at
handwritten boundaries; fork isolation; new-pivot groups/subset retirement; the
exact-union alias policy; cap recovery and observable pokes during caps; unknown
gaps versus declared closures;500/501 retirement and poke priority across a
552-bar path/counterfactual; overdue clock advancement; duplicate/conflicting
retries; atomic source/trace/command failures; immutable revisions; future/file-
binding identity; checkpoint edit/reorder/duplicate/code refusal; D1/BNC full-bar
semantics; CLI prefix continuation, overwrite and market/validation refusal.
The long run includes full prefix restoration/counterfactuals; elapsed times are
local verification observations, not throughput acceptance. Synthetic cap pressure
and group-union metadata are labelled component tests, not market observations.
Unchanged broad/120 accounting suites are not rerun.

| Invented CLI case | Bar publications | Final admitted lifecycle states |
| --- | ---: | --- |
| H4 LONG G35 | 49 | POKED |
| H4 SHORT G35 | 49 | POKED |
| H4 LONG prefix through47 | 48 | VALID |
| H4 continuation of that checkpoint | 49 | POKED; byte-identical to uninterrupted |
| H4 missing scheduled bar40 | 48 | no admitted line |
| H4 new-pivot superset | 62 | old RETIRED, new VALID in a fresh group |
| D1 BRK3 diagnostic | 50 | VALID |

API exercises also demonstrate an explicitly supplied G35 trigger consumed before
poke and a gap after first formation that keeps historical VALID but blocks current
eligibility. Both checkpoint/restart reports match. The supplied trigger is not
evidence of detected setups, trades, fills, returns or economic selection.
Inputs, checkpoints and reports remain ignored under
`reports/trendline-170/examples-001/`. Portable counts, hashes and the filtered
Git identity audit are in [verification-170.json](verification-170.json).

## Remaining work

Next finish the full Phase4 golden/generated-path acceptance matrix and a separate
primary-agent boundary review, including wider invented candle-path alias/ranking/replacement cases.
The group-union policy has declared component coverage; this is not a claim that
every intended candle/property case is complete. Phase5's D1 gate and Phase6's
actual setup predicates, missed-break/bounce logic and economic tie abstention
remain later work. Current replay serializes diagnostic history and has explicit
command/trace/checkpoint bounds; no long-study performance qualification is claimed.
Actual-source admission stays open before market counts/studies. All28 new/16
prior cells, protected dates/routes, frozen legacy code, native grants and orders-off
persist. No actual market/provider/account/native access or full Phase4 completion.
