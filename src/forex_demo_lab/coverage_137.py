"""Retrospective coverage diagnostics for closed136 exports; no admission."""
from pathlib import Path
import re

from .context_recorder_136 import MAX_BYTES, inspect_bytes
from .paired_replay_133 import DENIED, digest, strict_json
from .strategy_adapter_114 import WARMUP_HOURS

SCHEMA = 'coverage137_v1'
HOUR_US = 3_600_000_000
GAP_US = 2_000_000
DETAIL_LIMIT = 128
PATH = re.compile(r'data/context-recorder-136-native/Run136-([1-9][0-9]*)-([0-9]+)-([1-9][0-9]*)/Context136\.txt')


def _snapshot(quote):
    return (quote['source_millis'], tuple(sorted(quote['native_bits'].items())),
            quote['volume'], quote['raw_flags'])


def _diagnose(parsed):
    by_sequence = {row['sequence']: row for row in parsed['rows']}
    pairs = parsed['paired_polls']
    quotes = [by_sequence[pair['quote_sequence']] for pair in pairs]
    markers = [pair['after_guard_offset_us'] for pair in pairs]
    repeats = reversals = same_time_changed = gap_count = 0
    largest_gap = None
    segments, groups = [], []
    segment_start = repeat_start = 0

    def segment(first, last):
        span = markers[last] - markers[first]
        segments.append(dict(first_poll=first + 1, last_poll=last + 1,
                             quote_observations=last - first + 1,
                             first_after_guard_offset_us=markers[first],
                             last_after_guard_offset_us=markers[last], span_us=span,
                             geometric_h1_upper_bound=span // HOUR_US))

    def group(first, last):
        if last == first:
            return
        groups.append(dict(first_poll=first + 1, last_poll=last + 1,
                           quote_observations=last - first + 1,
                           quote_before_span_us=(quotes[last]['receipt_monotonic_us'][0]
                                                 - quotes[first]['receipt_monotonic_us'][0]),
                           contains_sampling_gap=any(
                               quotes[i]['receipt_monotonic_us'][0] - quotes[i - 1]['receipt_monotonic_us'][0] > GAP_US
                               for i in range(first + 1, last + 1))))

    for i in range(1, len(quotes)):
        a, b = quotes[i - 1:i + 1]
        gap = b['receipt_monotonic_us'][0] - a['receipt_monotonic_us'][0]
        largest_gap = gap if largest_gap is None else max(largest_gap, gap)
        repeated = _snapshot(a) == _snapshot(b)
        reversed_time = b['source_millis'] < a['source_millis']
        changed = b['source_millis'] == a['source_millis'] and not repeated
        repeats += repeated
        reversals += reversed_time
        same_time_changed += changed
        gap_count += gap > GAP_US
        if not repeated:
            group(repeat_start, i - 1)
            repeat_start = i
        # Break geometry at observed sampling gaps and source-label anomalies.
        if gap > GAP_US or reversed_time or changed:
            segment(segment_start, i - 1)
            segment_start = i
    if quotes:
        segment(segment_start, len(quotes) - 1)
        group(repeat_start, len(quotes) - 1)
    span = markers[-1] - markers[0] if markers else None
    trailing = groups[-1] if groups and groups[-1]['last_poll'] == len(quotes) else None
    return dict(
        paired_quote_observations=len(quotes),
        unpaired_quote_observations=sum(row['type'] == 'T' for row in parsed['rows']) - len(quotes),
        distinct_recorded_snapshots=len({_snapshot(q) for q in quotes}),
        distinct_snapshots_are_market_tick_count=False,
        marker_span_us=span, geometric_h1_upper_bound=span // HOUR_US if span is not None else 0,
        adjacent_repeated_snapshots=repeats, source_reversals=reversals,
        same_source_time_changed_payload=same_time_changed,
        quote_before_gaps_over2s=gap_count, maximum_quote_before_gap_us=largest_gap,
        identical_snapshot_group_count=len(groups), identical_snapshot_groups=groups[:DETAIL_LIMIT],
        identical_group_details_truncated=len(groups) > DETAIL_LIMIT,
        longest_identical_quote_before_span_us=max((g['quote_before_span_us'] for g in groups), default=None),
        trailing_identical_group=trailing, repeat_span_is_source_age=False,
        segment_count=len(segments), segments=segments[:DETAIL_LIMIT],
        segment_details_truncated=len(segments) > DETAIL_LIMIT,
        longest_segment_span_us=max((s['span_us'] for s in segments), default=None),
        maximum_h1_intervals_in_one_segment=max((s['geometric_h1_upper_bound'] for s in segments), default=0),
        # These are sample-marker blocks, never market sessions or qualified bars.
        UTC_alignment_established=False, active_session_established=False,
        qualified_aligned_h1_bars=0, qualified_warmup_shortfall=WARMUP_HOURS)


def assess_bytes(raw):
    parsed = inspect_bytes(raw)
    return dict(schema=SCHEMA + '_run', input_sha256=digest(raw), input_bytes=len(raw),
                declared_kind=parsed['declared_kind'], capture_status=parsed['capture_status'],
                stop_code=parsed['stop_code'], origin_nominal_gmt_seconds=parsed['origin_nominal_gmt_seconds'],
                origin_monotonic_us=parsed['origin_monotonic_us'],
                pending_attempt=parsed['pending_attempt'], incomplete_context=parsed['incomplete_context'],
                truncated_tail=parsed['truncated_tail'], quarantined_poll_rows=parsed['quarantined_poll_rows'],
                context_count=len(parsed['contexts']),
                complete_context_count=sum(c['complete'] for c in parsed['contexts']),
                commission_states=[c['commission_state'] for c in parsed['contexts']],
                context_is_atomic_contract=False, applicable_total_costs_USD=None,
                coverage=_diagnose(parsed), retrospective_diagnostics_only=True,
                causal_admission_available=False, repeat_cause_established=False,
                source_offset_bounds=None, receipt_UTC_uncertainty_bounds=None,
                delivery_delay_bounds=None, strategy_evaluated=False, **DENIED)


def assess(root, raw_manifest):
    manifest = strict_json(raw_manifest, 65_536)
    if (type(manifest) is not dict or set(manifest) != {'schema', 'runs'}
            or manifest['schema'] != SCHEMA + '_manifest' or type(manifest['runs']) is not list
            or not 1 <= len(manifest['runs']) <= 8):
        raise ValueError('coverage137_manifest')
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('coverage137_root')
    root = root.resolve()
    reports, seen_ids, seen_paths, seen_hashes = [], set(), set(), set()
    for entry in manifest['runs']:
        if type(entry) is not dict or set(entry) != {'id', 'path', 'sha256'}:
            raise ValueError('coverage137_entry')
        name, relative, sha = entry['id'], entry['path'], entry['sha256']
        if (type(name) is not str or not re.fullmatch('[a-z][a-z0-9_]{0,31}', name)
                or type(relative) is not str or not (match := PATH.fullmatch(relative))
                or type(sha) is not str or not re.fullmatch('[0-9a-f]{64}', sha)
                or name in seen_ids or relative in seen_paths or sha in seen_hashes):
            raise ValueError('coverage137_binding')
        seen_ids.add(name); seen_paths.add(relative); seen_hashes.add(sha)
        path = root
        for part in relative.split('/'):
            path = path / part
            if path.is_symlink():
                raise ValueError('coverage137_symlink')
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError('coverage137_file')
        with path.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if not 0 < len(raw) <= MAX_BYTES or digest(raw) != sha:
            raise ValueError('coverage137_hash')
        report = assess_bytes(raw)
        if (int(match[1]) != report['origin_nominal_gmt_seconds']
                or int(match[3]) != report['origin_monotonic_us']):
            raise ValueError('coverage137_origin')
        reports.append(dict(id=name, path=relative, **report))
    if len({r['declared_kind'] for r in reports}) != 1:
        raise ValueError('coverage137_mixed_provenance')
    return dict(schema=SCHEMA, manifest_sha256=digest(raw_manifest), runs=reports,
                thresholds=dict(quote_before_gap_us=GAP_US, detail_limit=DETAIL_LIMIT),
                assessment='diagnostic_only_not_ready_for_fixed_h1_evaluation',
                runs_joined=False, combined_continuous_history_hours=None,
                qualified_aligned_h1_bars=0, warmup_observed_closed_h1_required=WARMUP_HOURS,
                geometry_is_qualified_coverage=False, retrospective_diagnostics_only=True,
                October2026='quarantined', November_December2026='reserved_untouched', year2025='consumed',
                collection_authorized=False, strategy_evaluated=False, financial_engine_events=0,
                profitability_established=False, **DENIED)


def markdown(report):
    lines = ['# Coverage137 assessment', '', 'Diagnostic sample coverage; no qualified strategy input.', '',
             '| Separate run | Paired quotes | Marker span (s) | Max H1 intervals by span | Longest segment (s) | Gaps >2s | Longest identical span (s) | Qualified H1 |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    def seconds(value): return 'unobserved' if value is None else f'{value / 1_000_000:.6f}'
    for run in report['runs']:
        c = run['coverage']
        lines.append(f"| {run['id']} | {c['paired_quote_observations']} | {seconds(c['marker_span_us'])} | "
                     f"{c['geometric_h1_upper_bound']} | {seconds(c['longest_segment_span_us'])} | "
                     f"{c['quote_before_gaps_over2s']} | {seconds(c['longest_identical_quote_before_span_us'])} | 0 |")
    lines += ['', 'Segments break at quote-request gaps over2s and source-label reversals or same-time payload changes.',
              'They may contain repeated quotes; they are not active sessions, complete tick delivery or qualified bars.',
              'Span bounds use first/last completed paired after-guard markers; no partial pair supplies an endpoint.',
              'The fixed H1 adapter requires201 qualified observed closed H1 warm-up bars before evaluation.',
              'Do not join runs, infer UTC offsets/quote age, assume zero costs or manufacture missing bars.',
              'November–December remains reserved and untouched. No strategy return or collection is authorized.', '']
    return '\n'.join(lines)
