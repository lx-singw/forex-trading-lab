# Prospective source/run preflight — sprint165

The canonical current declaration is config/trendline-study-v1.json. The smaller
config/trendline-data-163.json remains a retained coarse-lint example, not a second
active study declaration. Strategy parameters remain in the frozen protocol;
this plan describes data, costs, scopes, prior exposures and proposed run endpoints.

```sh
PYTHONPATH=src python3 scripts/trendline-study-165.py draft NEW-PLAN.json
PYTHONPATH=src python3 scripts/trendline-study-165.py freeze config/trendline-study-v1.json NEW-FREEZE.json
PYTHONPATH=src python3 scripts/trendline-study-165.py check config/trendline-study-v1.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
```

Drafts, freezes and output directories are exclusive. No price/evidence-file path
or credential is accepted by this CLI. It reads the two named metadata files and
known implementation/protocol sources only. Evidence references are SHA256 claims,
not filenames to open. File sizes, duplicate JSON, symlink paths, unknown fields,
nonfinite values and source/flag/policy changes reject.

The freeze binds exact plan-file bytes, canonical content, immutable policy and
source hashes. Changes during assessment reject before the output directory is
created. These are ordinary local consistency checks, not authenticated approval
or proof against a hostile process. A frozen declaration never admits market data.

## Checked requirements

The adapter reuses unchanged145 date, chronology, exposure, joint-freeze, evidence
scope and cost checks. It replaces the earlier16-cell budget with the trendline
28-cell scope without modifying the old module or its study. Inputs/outputs are
copied; no legacy source or candidate is silently relabelled.

- Development and validation each span at least24 calendar months, are ordered
  and disjoint; warmup must end at the corresponding funded start.
- Warmup declarations retain253 complete bars per required timeframe and require
  at least390 H4 bars for the included FXR angle window. Parent counts cannot
  exceed child counts. These are declarations, not authenticated observations.
- Consumed2025, quarantined October2026 and reserved November-December2026 remain
  blocked even for warmup. Seen2024 cannot become untouched funded validation.
- Prior price/return/rule/example exposure is checked. Undated price exposure
  requires validation review; a missing exposure/alternative count is not zero.
  A declared joint pre-return freeze is not independent certification.
- Prior cells count against each28-cell track; the paired exit analysis retains
  its one-analysis initial budget. All attempted alternatives still need a
  complete reviewed history. Supplied counters are not an authoritative registry.
- B/Q geometry, spread and latency labels must agree. B cannot satisfy qualified
  broker/demo gates; midpoint-only data cannot supply executable sides. A nonzero
  B finalization delay remains visible rather than being changed to obtain entries.
- Ten evidence categories declare hashes, scopes and timeframes, including bar
  price and entry-spread semantics. Coverage holes are not filled by a hash.
  Unknown fees remain unknown; hypothetical costs cannot pass the qualified track.
- Both proposed liquidation timestamps must be within their own half-open funded
  scopes. Actual source-specific H1 grid and endpoint quote coverage still need
  review; UTC-minute alignment is not guessed without a calendar.
- Input/calendar/uncertainty hashes and timing assumptions remain explicit.
  Closed native/SDK routes and unassigned capture grants are not renewed.

Every result retains all28 strategy/profile/partition cells as UNAVAILABLE with
null returns. Even complete declarations require independent qualification,
unchanged-control compatibility, finished strategy acceptance and an implemented
market reader. There is no enabled market branch, strategy/account replay or
native account/order query. This tool diagnoses readiness; it cannot fabricate
the provider evidence identified in SOURCE-165-FINDINGS.md.
