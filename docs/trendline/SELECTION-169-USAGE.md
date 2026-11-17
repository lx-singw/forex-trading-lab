# Selection and explicit lifecycle journal

Sprint169,17 November2026. Invented Level B software only. This increment reduces
[168's validated candidates](LINES-168-USAGE.md) and supplies lifecycle storage
commands. Automatic bar-by-bar lifecycle and setup detection remain unfinished.

From the WSL repository root:

```sh
PYTHONPATH=src python3 scripts/trendline-lines-169.py /path/source.json /path/hours.json /path/new-output-directory --profile TRL_BRK3_E1 --role full --journal
```

The explicit163 source/hour files, `--as-of`, invented-validation
`--unlock-receipt`, profile choices and penetration roles are unchanged.
Market kinds and output overwrite are refused. `selection.json` contains the full
168 debug dump plus reduction/ranking. Optional `journal.json` records CANDIDATE
registration and VALID transitions for current survivors. This is one snapshot,
not a historical lifecycle replay. `--journal` requires `--role full`; an action-
break exception cannot certify a newly registered line as unpoked through now.

## Deduplication and ranking

Only fully profile-valid geometries enter reduction. Within the same profile,
frame, kind and exact ordered touch set, prefer an existing validated pair joining
the earliest/latest touches. Otherwise minimize the exact sum of touch distances,
then canonical geometry id. An invalid earliest/latest pair is never fabricated
or revived. Strict subsets are dropped only within the same eligibility profile;
BRK2's exactly-two-touch category survives another profile's three-touch geometry.

Ranking follows more touches, longer age, more recent last touch and ascending
first-touch id. Canonical geometry id settles display ties only. The economic key
excludes that geometry id; ties are reported explicitly and no trade is selected.
Reduction is independent of input order; identical duplicates are idempotent and
conflicting copies of one geometry are refused. One evaluation frontier is
required within each profile/frame. All diagnostics retain profile/frame scope,
including when the same canonical geometry appears in two profiles.

`selection.select(source, bars, ...)` returns a frozen `SelectedSnapshot` with
immutable typed selected lines; `.record()` returns a fresh JSON-compatible copy.
`reduce_lines()` also accepts declared typed component fixtures. Those metadata
are not proof of candle discovery, authentic prices or source permission.
Exact-touch-set aliases are recorded before strict-subset removal; a subset's
replacement is not automatically an opportunity-group alias.

## Journal command boundary

```python
from forex_demo_lab.trendline.selection import select
from forex_demo_lab.trendline.lifecycle import Journal

snapshot = select(source, completed_bars, role="full")
book = Journal(source)
for line in snapshot.selected:
    line_id = book.register(snapshot, line.geometry_id)
    book.validate(snapshot, line_id)
checkpoint = book.checkpoint()
restored = Journal.restore(source, checkpoint)
```

The journal is bound to one invented source declaration, profile, timeframe and
code/protocol version. Every accepted command appends a hash-linked event and
updates a staged frontier only after all checks pass. Exact command retries are
no-ops even after later state changes or restart. Reports/checkpoints are fresh
copies, and earlier events are never rewritten.

Registration creates CANDIDATE; `validate` requires the same touch-set instance to
survive current full-check selection. `poke` requires an actual strict penetration
by the supplied snapshot's completed bar. Candidate or valid geometry can be
terminally poked; no late confirmation restores it. `retire` requires either more
than500 bars since first validation, or a selected same-profile/kind strict-touch-
superset replacement. Exactly500 bars is insufficient. POKED, RETIRED and
TRIGGERED instances cannot be reset. A new confirmed touch set produces a new
instance/group; geometries sharing an identical touch set share their group.

`trigger_many(snapshot, line_ids)` is an **explicit declared-trigger interface**
for later setup integration. It does not detect or certify a break/bounce, apply
tick margins, select an entry or approve an order. It requires pre-existing VALID
instances from an earlier bar and open groups. It atomically consumes all supplied
simultaneous groups before any later caller filtering. Same-formation-bar triggers
and reconsumption are refused. No skip/no-fill/refilter command can reopen a group.

`merge_groups` records an explicit same-kind alias decision. It unions consumed
state, so merging an open group with a consumed one leaves the result consumed.
It never splits or resets groups. The journal does not infer which groups should
merge; that policy and automatic new-pivot replacement integration are next.

Line/group ids depend on causal geometry/touches, profile, frame and symbol rather
than whole-file hash. Full-file source binding remains separate on the journal
and checkpoint: changing the manifest prevents resuming that checkpoint but does
not rename an otherwise identical earlier line when a future suffix is appended.

Checkpoint restore replays every command, checks legal transitions, chain order,
state digest and source/code bindings, and refuses duplicates/reordering/tampering.
It is bounded at10,000 events and16,000,000 encoded bytes; no silent truncation.
Integrity hashes are not source authentication, data permission or a grant. There
is no checkpoint migration across changed code/source. Only the standard library
is used; no credentials, accounts, native trading or order API is involved.

## Remaining Phase4 work

Automatic per-bar candidate revisions, penetration/retirement order, cap/gap
handling and alias/replacement decisions still need integration and generated-path
acceptance. Trigger detection, missed-break handling, bounce contact and economic
tie abstention belong to later setup integration. Profile validity and journal
VALID do not themselves establish entry readiness. All outputs keep entry/orders
unavailable; actual-source admission remains open before market evaluation.
