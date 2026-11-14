# Forward recorder quality report131

This offline adapter gives the saved forward111 recorder and paired-clock130
format a common quality report. It reparses raw bytes through the retained wire
readers. No native program, terminal setting or dated runtime is changed.

Run from the canonical repository in WSL:

```sh
python3 scripts/forward-quality-131.py
python3 scripts/forward-quality-131.py --format markdown
```

The default [manifest](../config/forward-quality-131.json) pins 60 forward111
segments and one timing130 file. Optional manifest and root arguments support
offline fixtures with the same bounded, explicitly named formats:

```sh
python3 scripts/forward-quality-131.py /absolute/path/manifest.json --root /absolute/path/root
```

The CLI writes JSON or Markdown to stdout. It does not modify inputs or launch
MT5. Invalid/unreadable files produce a generic JSON error and exit1 without
echoing file contents, arbitrary exception strings or paths.

## Reusable integration points

The module forex_demo_lab.forward_quality_131 exposes:

- inspect_forward_segments(segments): ordered (filename, bytes) pairs from one
  closed111 run, using the retained segment reader.
- inspect_timing_bytes(data): one closed130 export, using its retained reader.
- build_report(manifest, root): separately validated, hash-pinned inputs from
  both formats. Mixed invented/market declarations and mixed run segments fail.
- render_markdown(report): a readable rendering of the validated report.

The adapters inspect raw exports, not alleged inspection JSON. They retain the
old readers' date/size/sequence/receipt/integrity checks. Source origin seconds
and origin microseconds must agree with the run-folder label. The manifest
rejects duplicate fields, unexpected keys, traversal, symlink components,
duplicate files, wrong source order, hashes, segment ordering and size/count
overruns. These local integrity checks do not authenticate the producer.

## What the report means

Both formats receive the same quote counters: advances, adjacent timestamp
reversals, labels below a prior high-water mark, identical full native snapshots,
same-time changed snapshots, quote-read spacing and longest observed repeat
span. Comparing native bits preserves distinctions such as negative zero and
unknown flag changes. Counters never cross run boundaries.

The fixed receipt-gap notice threshold is strictly greater than 2,000,000us,
inherited from111's engineering threshold. It describes gaps between recorded
quote-read starts; no missing market ticks or stale-price age is inferred.
These intervals differ from130's first-clock poll-start intervals because quote
reads follow their first clock groups and intervening guards.

Only130 contains paired raw clock readings. Full pairs keep their original
arithmetic; a final quote without clock-after is reported separately. Numeric
raw-clock reversals and changes in clock differences are findings, without an
automatic UTC correction. The111 pilot remains paired_clocks.status=
not_recorded; no130 offset is transferred into it. A130 prefix with no clock
groups is not_observed, distinct from zero observed offset.

Quote-event details are capped at128, with event_details_truncated and full
event_count. Aggregate counters cover every quote. Prefix events use only
earlier observations; a later snapshot does not rewrite an earlier event.

Notice findings describe bounded stops, repetition, same-time changes and raw
offset changes. Warning findings expose reversals, sampling gaps, missing or
invalid outcomes, partial/pending data and unresolved age/delivery/execution
evidence. They are not automated trading rules. A wire-valid stopped prefix
does not become a complete capture or a qualified feed.

Source/receipt UTC, source age, executable freshness, complete delivery,
historical timezone rules and profitability remain unverified. Market/paper/
order/real-money availability stays false. Read [results](FORWARD-QUALITY-131-RESULTS.md)
and [the generated report](../reports/forward-quality-131-report.md).

No MT5 action is required. Existing111 and130 runtime envelopes are expired on
16 October2026 and must not be renewed by editing their dates. A longer recorder
with paired timing fields is separate future work after this integration.
