"""Offline recorder quality observations; no feed admission or trade interface."""
import hashlib
import json
from pathlib import Path
import re

from . import forward_capture_111 as forward
from . import timing_probe_130 as timing

SCHEMA = 'forward_quality131_manifest_v1'
IDS = ('forward111', 'timing130')
MAX_EVENTS, RECEIPT_GAP_US, MAX_MANIFEST = 128, 2000000, 65536
MAX_TOTAL = forward.MAX_BYTES + timing.MAX_BYTES
SPECS = {
    'forward111': (r'data/forward-capture-112/(Run111-[1-9][0-9]*-[0-9]+-[1-9][0-9]*)/(Segment111-[0-9]{3}\.txt)', forward.MAX_FILE, 64),
    'timing130': (r'data/timing-probe-130-native/(Run130-[1-9][0-9]*-[0-9]+-[1-9][0-9]*)/(Timing130\.txt)', timing.MAX_BYTES, 1),
}


def _range(values):
    return {'min': min(values), 'max': max(values), 'distinct': len(set(values))} if values else None


def _quality(kind, parsed):
    paired = kind == 'timing130'
    observations = [r for r in parsed['rows'] if r['type'] == 'T'] if paired else parsed['observations']
    rows = [dict(sequence=r['sequence'], source_millis=r['source_millis'], source_seconds=r['source_seconds'],
                 receipt_monotonic_us=r['receipt_monotonic_us'],
                 receipt_seconds=r['receipt_nominal_gmt_seconds'] if paired else r['receipt_gmt_seconds'],
                 native_bits=r['native_bits'], volume=r['volume'], flags=r['raw_flags'] if paired else r['flags'])
            for r in observations]
    events = []; event_count = 0

    def event(code, sequence, detail):
        nonlocal event_count
        event_count += 1
        if len(events) < MAX_EVENTS:
            events.append({'code': code, 'sequence': sequence, **detail})

    def snapshot(row):
        return (row['source_seconds'], row['source_millis'],
                tuple(row['native_bits'][k] for k in ('bid', 'ask', 'last', 'volume_real')), row['volume'], row['flags'])

    advances = reversals = repeated = equal_changed = below_highwater = gaps = longest = 0
    repeat_start = None; highwater = None; prior = None; intervals = []
    for row in rows:
        if highwater is not None and row['source_millis'] < highwater:
            below_highwater += 1
        highwater = max(highwater or row['source_millis'], row['source_millis'])
        if prior is not None:
            delta = row['source_millis'] - prior['source_millis']
            advances += delta > 0; reversals += delta < 0
            interval = row['receipt_monotonic_us'][0] - prior['receipt_monotonic_us'][0]
            intervals.append(interval)
            if delta < 0:
                event('source_label_reversal', row['sequence'], {'raw_change_ms': delta})
            if interval > RECEIPT_GAP_US:
                gaps += 1
                event('receipt_poll_gap', row['sequence'], {'receipt_gap_us': interval})
            if snapshot(prior) == snapshot(row):
                repeated += 1
                if repeat_start is None:
                    repeat_start = prior['receipt_monotonic_us'][0]
                span = row['receipt_monotonic_us'][0] - repeat_start
                longest = max(longest, span)
                event('identical_snapshot', row['sequence'], {'observed_repeat_span_us': span})
            else:
                repeat_start = None
                if delta == 0:
                    equal_changed += 1
                    event('same_timestamp_changed_snapshot', row['sequence'], {})
        prior = row
    if paired:
        clocks = [r for r in parsed['rows'] if r['type'] == 'C']
        clock_series = {
            'time_current_minus_gmt_seconds': [r['raw_clocks']['time_current']-r['raw_clocks']['time_gmt'] for r in clocks],
            'time_trade_server_minus_gmt_seconds': [r['raw_clocks']['time_trade_server']-r['raw_clocks']['time_gmt'] for r in clocks],
            'time_local_minus_gmt_seconds': [r['raw_clocks']['time_local']-r['raw_clocks']['time_gmt'] for r in clocks],
        }
        offsets = {key: {'range': _range(values), 'adjacent_changes': sum(a != b for a, b in zip(values, values[1:]))}
                   for key, values in clock_series.items()}
        raw_changes = parsed['raw_clock_changes']
        clock_report = dict(status='recorded' if clocks else 'not_observed', clock_groups=len(clocks), completed_pairs=parsed['completed_polls'],
                            quotes_without_completed_pair=len(rows)-parsed['completed_polls'],
                            raw_offset_observations=offsets, raw_clock_changes=raw_changes,
                            paired_raw_arithmetic=parsed['paired_raw_arithmetic'],
                            all_read_groups_atomic=False)
    else:
        clock_report = dict(status='not_recorded', clock_groups=0, completed_pairs=None,
                            quotes_without_completed_pair=None, raw_offset_observations=None,
                            raw_clock_changes=None, paired_raw_arithmetic=None, all_read_groups_atomic=False)
    findings = []

    def finding(code, severity, count=None):
        findings.append({'code': code, 'severity': severity, 'count': count})

    if parsed['capture_status'] != 'complete':
        finding('elapsed_limit_stop' if parsed['stop_code'] == 13 else
                'stopped_prefix' if parsed['capture_status'] == 'stopped' else 'incomplete_capture', 'notice')
    pending = bool(parsed['pending_attempt']) if paired else parsed['pending_attempt'] is not None
    truncated = parsed['truncated_tail'] if paired else parsed['truncated_final_segment']
    if pending: finding('pending_attempt', 'warning')
    if truncated: finding('partial_final_frame', 'warning')
    if not rows: finding('no_recorded_quotes', 'warning', 0)
    if repeated: finding('identical_snapshots_observed', 'notice', repeated)
    if equal_changed: finding('same_timestamp_changed_snapshots_observed', 'notice', equal_changed)
    if reversals: finding('source_label_reversals_observed', 'warning', reversals)
    if gaps: finding('receipt_poll_gaps_over_two_seconds', 'warning', gaps)
    if paired:
        count = sum(v['reversals'] for v in clock_report['raw_clock_changes'].values())
        if count: finding('raw_clock_numeric_reversals_observed', 'warning', count)
        count = sum(v['adjacent_changes'] for v in clock_report['raw_offset_observations'].values())
        if count: finding('raw_clock_offset_changes_observed', 'notice', count)
        if clock_report['quotes_without_completed_pair']:
            finding('quote_without_completed_clock_pair', 'warning', clock_report['quotes_without_completed_pair'])
    else:
        finding('paired_clocks_not_recorded', 'warning')
    missing = 0 if paired else parsed['missing']
    invalid = 0 if paired else parsed['invalid']
    if missing: finding('missing_quote_outcomes', 'warning', missing)
    if invalid: finding('invalid_quote_outcomes', 'warning', invalid)
    finding('source_age_unverified', 'warning')
    finding('complete_delivery_unverified', 'warning')
    finding('execution_quality_unverified', 'warning')
    origin_s = parsed['origin_nominal_gmt_seconds'] if paired else parsed['origin_gmt_seconds']
    origin_us = parsed['origin_monotonic_us']
    return dict(schema='forward_quality131_source_v1', format=kind, declared_kind=parsed['declared_kind'],
                structure_validated=True, capture_status=parsed['capture_status'], stop_code=parsed['stop_code'],
                attempts=parsed['queries_attempted'] if paired else parsed['attempts'],
                diagnostic_groups_recorded=parsed['queries_recorded'] if paired else None,
                quote_outcomes_recorded=len(rows), missing_quote_outcomes=missing, invalid_quote_outcomes=invalid,
                pending_attempt=pending, truncated_tail=truncated,
                origin_nominal_gmt_seconds=origin_s, origin_monotonic_us=origin_us,
                quote_statistics=dict(adjacent_comparisons=max(0, len(rows)-1), distinct_source_millis=len({r['source_millis'] for r in rows}),
                    source_label_advances=advances, source_label_adjacent_reversals=reversals,
                    source_labels_below_prior_highwater=below_highwater, adjacent_identical_snapshots=repeated,
                    same_timestamp_changed_snapshots=equal_changed, receipt_poll_gaps_over_two_seconds=gaps,
                    receipt_start_interval_us=_range(intervals),
                    longest_observed_repeat_span_us=longest if len(rows) >= 2 else None,
                    repeat_span_is_quote_age=False,
                    raw_source_minus_nominal_receipt_ms=_range([r['source_millis']-r['receipt_seconds'][1]*1000 for r in rows])),
                receipt_window=None if not rows else dict(first_quote_sequence=rows[0]['sequence'],
                    last_quote_sequence=rows[-1]['sequence'],
                    first_nominal_seconds=rows[0]['receipt_seconds'][0], last_nominal_seconds=rows[-1]['receipt_seconds'][2],
                    recorded_span_us=rows[-1]['receipt_monotonic_us'][2]-rows[0]['receipt_monotonic_us'][0],
                    last_guard_elapsed_from_origin_us=rows[-1]['receipt_monotonic_us'][2]-origin_us),
                paired_clocks=clock_report, findings=findings, events=events, event_count=event_count,
                event_details_truncated=event_count > len(events), event_detail_limit=MAX_EVENTS,
                fixed_receipt_gap_notice_threshold_us=RECEIPT_GAP_US,
                producer_authenticated=False, source_utc_certified=False, receipt_utc_certified=False, source_age=None,
                executable_freshness_certified=False, complete_tick_delivery=False, historical_timezone_rule_established=False,
                market_data_qualified=False, paper_evaluation_available=False, orders_available=False,
                real_money_execution_available=False, strategy_evaluated=False, profitability_established=False)


def inspect_forward_segments(segments):
    """Read a closed111 run through its retained wire reader, then report quality."""
    return _quality('forward111', forward.inspect_segments(segments))


def inspect_timing_bytes(data):
    """Read a closed130 export through its retained wire reader, then report quality."""
    return _quality('timing130', timing.inspect_bytes(data))


def _keys(obj, expected):
    if type(obj) is not dict or set(obj) != set(expected):
        raise ValueError('quality_fields')


def _read(path, maximum, allow_empty=False):
    if path.is_symlink() or not path.is_file():
        raise ValueError('quality_file')
    with path.open('rb') as stream:
        data = stream.read(maximum+1)
    if (not data and not allow_empty) or len(data) > maximum:
        raise ValueError('quality_size')
    return data


def load_manifest(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('quality_duplicate_key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('quality_nonfinite_constant')
    try:
        return json.loads(_read(Path(path), MAX_MANIFEST).decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('quality_manifest_json') from None


def build_report(manifest, root):
    _keys(manifest, ('schema', 'sources'))
    if manifest['schema'] != SCHEMA or type(manifest['sources']) is not list or len(manifest['sources']) != 2:
        raise ValueError('quality_manifest')
    root = Path(root)
    if root.is_symlink():
        raise ValueError('quality_root_symlink')
    root = root.resolve()
    sources = []; seen = set(); kinds = set(); total = 0
    for position, source in enumerate(manifest['sources']):
        _keys(source, ('id', 'files'))
        key = source['id']
        if key != IDS[position]:
            raise ValueError('quality_source_order')
        pattern, bound, count_bound = SPECS[key]
        if type(source['files']) is not list or not 1 <= len(source['files']) <= count_bound:
            raise ValueError('quality_file_count')
        bindings = []; loaded = []; run = None
        for index, entry in enumerate(source['files'], 1):
            _keys(entry, ('path', 'sha256'))
            relative, digest = entry['path'], entry['sha256']
            if type(relative) is not str or type(digest) is not str or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('quality_binding')
            match = re.fullmatch(pattern, relative)
            if match is None or relative in seen:
                raise ValueError('quality_path')
            folder, filename = match.groups()
            if run is not None and run != folder or key == 'forward111' and filename != f'Segment111-{index:03d}.txt':
                raise ValueError('quality_run_order')
            run = folder; candidate = root
            for part in relative.split('/'):
                candidate = candidate / part
                if candidate.is_symlink():
                    raise ValueError('quality_symlink')
            data = _read(candidate, bound, allow_empty=key == 'forward111')
            total += len(data)
            if total > MAX_TOTAL:
                raise ValueError('quality_total_size')
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('quality_hash_mismatch')
            seen.add(relative); bindings.append({'path': relative, 'sha256': digest, 'bytes': len(data)})
            loaded.append((filename, data))
        report = inspect_forward_segments(loaded) if key == 'forward111' else inspect_timing_bytes(loaded[0][1])
        if (str(report['origin_nominal_gmt_seconds']), str(report['origin_monotonic_us'])) != (run.split('-')[1], run.split('-')[3]):
            raise ValueError('quality_run_origin')
        kinds.add(report['declared_kind'])
        sources.append({'id': key, 'files': bindings, 'quality': report})
    if len(kinds) != 1:
        raise ValueError('quality_mixed_declarations')
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return dict(schema='forward_quality131_report_v1', manifest_semantic_sha256=hashlib.sha256(canonical).hexdigest(),
                input_files=len(seen), input_bytes=total, sources=sources, input_integrity_verified=True,
                cross_run_contract_authenticated=False, continuous_history_across_sources=False,
                source_offsets_transferred_between_runs=False, producer_authenticated=False,
                source_utc_certified=False, receipt_utc_certified=False, source_age=None,
                market_data_qualified=False, paper_evaluation_available=False, orders_available=False,
                real_money_execution_available=False, strategy_evaluated=False, profitability_established=False)


def render_markdown(report):
    lines = ['# Forward recorder quality report131', '',
             'Each source remains a separate run. Clock comparisons and repeat spans do not certify quote age or executable freshness.', '',
             '| Source | Capture | Quotes | Adjacent repeats | Longest observed repeat (us) | Paired clocks |', '|---|---|---:|---:|---:|---|']
    for source in report['sources']:
        q = source['quality']; stats = q['quote_statistics']; clocks = q['paired_clocks']
        span = stats['longest_observed_repeat_span_us']
        lines.append(f"| {source['id']} | {q['capture_status']} / code {q['stop_code']} | {q['quote_outcomes_recorded']} | {stats['adjacent_identical_snapshots']} | {span if span is not None else 'unknown'} | {clocks['status']} |")
    for source in report['sources']:
        q = source['quality']; stats = q['quote_statistics']; clocks = q['paired_clocks']
        lines += ['', f"## {source['id']}", '',
                  f"Source-label advances / adjacent reversals / below prior high-water: {stats['source_label_advances']} / {stats['source_label_adjacent_reversals']} / {stats['source_labels_below_prior_highwater']}.",
                  f"Receipt poll gaps over 2,000,000us: {stats['receipt_poll_gaps_over_two_seconds']}. This threshold describes sampling gaps, not quote age.",
                  f"Completed clock pairs: {clocks['completed_pairs'] if clocks['completed_pairs'] is not None else 'not recorded'}; quotes without completed pair: {clocks['quotes_without_completed_pair'] if clocks['quotes_without_completed_pair'] is not None else 'unknown'}."]
        if clocks['raw_offset_observations'] is not None:
            lines += ['', '| Raw clock comparison | Range in seconds | Adjacent changes |', '|---|---|---:|']
            for key, value in clocks['raw_offset_observations'].items():
                r = value['range']
                lines.append(f"| {key} | {str(r['min'])+' to '+str(r['max']) if r is not None else 'unknown'} | {value['adjacent_changes']} |")
        lines += ['', '| Finding | Severity | Count |', '|---|---|---:|']
        for finding in q['findings']:
            lines.append(f"| {finding['code']} | {finding['severity']} | {finding['count'] if finding['count'] is not None else ''} |")
        lines += ['', f"Event details stored: {len(q['events'])} of {q['event_count']}; truncated: {q['event_details_truncated']} (limit {MAX_EVENTS}). Full counters include all events.",
                  '', '| Pinned raw file | Bytes | SHA256 |', '|---|---:|---|']
        for entry in source['files']:
            lines.append(f"| {entry['path']} | {entry['bytes']} | {entry['sha256']} |")
    return '\n'.join(lines + ['', 'Source/receipt UTC, quote age, complete tick delivery and execution quality remain unverified.',
                              'No source offsets are transferred between runs. No strategy evaluation or orders; market/paper/real-money admission stays false.', ''])
