# Automatic invented lifecycle replay

Sprint170,17 November2026, engineering version TRL_ENGINE_170_V1 and protocol
revision5. Explicit invented Level B files only. This integrates bar observations,
line selection and immutable lifecycle history; it does not detect setups or
select entries, calculate returns or place orders.

From the WSL repository root:

```sh
PYTHONPATH=src python3 scripts/trendline-replay-170.py /path/source.json /path/hours.json /path/new-output-directory --profile TRL_BRK3_E1
```

The163 source/hour contract, protected-validation `--unlock-receipt` and bounded
`--as-of INTEGER_MS` cursor are unchanged. All five H4 strategies and the D1_BRK3
diagnostic are retained. Market kinds are refused. The new output directory must
not exist; `replay.json` contains the debug/history report and `checkpoint.json`
contains a restart record. No CLI order or declared-trigger option exists.

To continue an invented prefix:

```sh
PYTHONPATH=src python3 scripts/trendline-replay-170.py /path/source.json /path/hours.json /path/new-output-directory --restore-checkpoint /path/previous/checkpoint.json
```

The checkpoint must match source, profile, code/protocol, cursor and the supplied
bar prefix. Restore replays commands and verifies the resulting state digest;
duplicate/no-op, reordered, changed or mismatched commands reject. The CLI compares
the restored publications with the aggregated input prefix before continuing.
There is no migration of older169 checkpoints across this code/protocol change.
Hashes protect integrity/reproducibility, not source authenticity or permission.

## Per-publication ordering

`Engine(source, profile, timeframe)` owns a forkable incremental inspector and
staged lifecycle journal. `observe(completed_bar)` confirms pivots, computes exact
indicators and evaluates the same168 line rules without rebuilding the indicator
prefix. It then:

1. Records any explicitly supplied, admitted pre-existing declared triggers.
2. Poke-checks every nonterminal admitted geometry against the completed extreme.
3. Retires untriggered instances more than500 bars past first validation.
4. Registers/validates new full-check selected instances and resolves group aliases.
5. Retires selected strict-subset replacements and publishes immutable revisions.

A poke wins over age retirement. A terminal instance never reopens. Raw candidate
and pair rejection diagnostics remain in every publication frame, including before
first eligibility. Current line revisions report age, value, slope metrics, group
consumption and explicit eligibility reasons. Journal CANDIDATE/VALID/terminal
events and per-bar line revisions are separate immutable histories.

## Group interpretation and eligibility

[Protocol revision5](PROTOCOL.md) freezes the automatic alias policy before engine
fixtures. Exact-touch aliases already share a group. A new touch set gets a fresh
group unless it is exactly the union of prior registered same-profile/frame/kind
strict-subset groups. Only that exact-union case automatically merges groups and
unions consumed state. Use history from before the current publication, including
terminal groups; registration order within a bar cannot decide novelty. A new
touch not represented by those prior groups creates a genuinely new opportunity,
even when its confirmation preceded first eligibility. A strict-subset retirement
alone does not merge groups.

Search incompleteness blocks current eligibility, registration and trigger
admission. It does not suppress observable pokes or age retirement of stored
instances. A cap can clear on a later snapshot without resetting the original
validity date/group. Missing scheduled candles break line coverage and block old
instances; no invented wick or fill is inferred. Known closures preserve adjacency.
Overdue unobserved completed bars also block eligibility. Clock advancement alone
does not fabricate bar observations or lifecycle retirement.

Historical lifecycle VALID and current eligibility are distinct. A stored VALID
instance can currently be blocked by missing coverage, the search cap, changed
profile eligibility/selection or a consumed group. `eligible_line_ids` is a
structural/protection diagnostic, not an entry permission. `action_line_ids` lists
pre-existing instances passing current action checks; new same-bar revisions
cannot backdate a break. Clock-only frames emit no action candidates.

The Python-only `observe(bar, declared_triggers=[line_ids])` boundary retains169's
explicit declared-trigger interface. It requires pre-existing admitted instances,
matching current touches, complete interval coverage and open groups. All supplied
groups consume before poke handling; failure rejects the entire publication.
It does not detect/certify a break, bounce, tick margin, missed break, safety line,
economic tie resolution, fill or trade. Actual setup predicates remain Phase6.

## Atomicity, identity and bounds

Indicator, pivot, selection and journal frontiers stage together. Invalid/reordered
bars, conflicting retries, invalid trigger ids, source/code changes and software
bounds reject before publishing any state. Identical latest retries are no-ops;
adding a trigger after a bar was already committed is a conflicting retry.
Reports/checkpoints return copies; published frames/revisions never change.

Causal frame, geometry, instance and group identities exclude whole-file source
binding. The report/checkpoint separately binds all source bytes and code. Appending
or changing a future suffix cannot rename an already published causal prefix.
Checkpoint continuation still requires the identical frozen source declaration.

Existing observation/event bounds remain. Additional engineering bounds are30,000
replay commands,32,000,000 encoded trace bytes and32,000,000 checkpoint bytes.
Exceeding a bound errors explicitly without truncation or partial bar publication;
it is not a successful study/qualification result. No long-replay performance or
market-source acceptance is claimed.

Remaining Phase4 work is the full golden/generated-path acceptance matrix and a
separate primary-agent boundary review, including wider alias/ranking/lifecycle paths. The
eight-outcome D1 gate and actual setup machines remain later phases. Actual-source
admission, market counts/studies, native grants and orders remain unavailable.
