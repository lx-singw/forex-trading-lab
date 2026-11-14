"""Assess saved diagnostic inputs for fixed H1 research; never grant admission."""
from dataclasses import asdict
from pathlib import Path
import re

from . import cost_probe_128 as costs
from . import metadata_probe_127 as metadata
from .paired_capture_132 import MAX_BYTES, inspect_bytes
from .paired_replay_133 import DENIED, canonical, digest, replay_manifest, strict_json
from .shadow_engine_113 import scenarios
from .strategy_adapter_114 import CANDIDATES, WARMUP_HOURS
from .model import Config

SCHEMA = 'forward_eligibility134_v1'
HOUR_US = 3_600_000_000
DEVELOPMENT_HOURS = VALIDATION_HOURS = 480
CONTEXT = (
    ('metadata127', re.compile(r'data/metadata-probe-127-native/Run127-([1-9][0-9]*)-([0-9]+)-([1-9][0-9]*)/Metadata127\.txt'), metadata),
    ('costs128', re.compile(r'data/cost-probe-128-native/Run128-([1-9][0-9]*)-([0-9]+)-([1-9][0-9]*)/Costs128\.txt'), costs),
)


def _keys(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('eligibility_fields')


def _read(root, relative, limit):
    if type(relative) is not str or '\\' in relative or relative.startswith('/') or any(p in ('', '.', '..') for p in relative.split('/')):
        raise ValueError('eligibility_path')
    path = root
    for part in relative.split('/'):
        path = path / part
        if path.is_symlink():
            raise ValueError('eligibility_symlink')
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError('eligibility_file')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError('eligibility_size')
    return raw


def _bound(root, entry, limit, pattern):
    _keys(entry, ('path', 'sha256'))
    if (type(entry['path']) is not str or not pattern.fullmatch(entry['path'])
            or type(entry['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])):
        raise ValueError('eligibility_binding')
    raw = _read(root, entry['path'], limit)
    if digest(raw) != entry['sha256']:
        raise ValueError('eligibility_hash')
    return raw


def span_bounds(first, last):
    """Geometry only; complete aligned/qualified bars cannot be inferred here."""
    if type(first) is not int or type(last) is not int or not 0 <= first <= last < 2**64:
        raise ValueError('eligibility_markers')
    span = last - first
    return dict(recorded_marker_span_us=span,
                maximum_fully_contained_one_hour_intervals=span // HOUR_US,
                qualified_aligned_h1_bars=0, UTC_alignment_established=False)


def pilot_plan():
    """Prospective engineering counts; not a power calculation or collection job."""
    return dict(target='fixed_h1_adapter114', candidates=list(CANDIDATES),
                warmup_observed_closed_h1_bars=WARMUP_HOURS,
                development_observed_closed_h1_bars=DEVELOPMENT_HOURS,
                untouched_validation_observed_closed_h1_bars=VALIDATION_HOURS,
                total_observed_closed_h1_bars=WARMUP_HOURS + DEVELOPMENT_HOURS + VALIDATION_HOURS,
                sample_size_sufficiency_established=False,
                interpretation='Engineering pilot target; no market-effect or profitability sufficiency claim.',
                validation_frozen_before_development_results=True,
                development_uses_validation_prices=False,
                pre_partition_prices_for_indicator_warmup_only=True,
                final_partial_hours_count=False, interpolated_hours_count=False,
                missing_hours_count=False, separate_runs_joined=False,
                collection_dates=None, collection_authorized=False,
                October2026='quarantined', November_December2026='reserved_untouched',
                year2025='consumed')


def _context_report(key, entry, raw, parsed):
    header = raw.split(b'\r\n', 1)[0].split(b'\t')
    report = dict(id=key, path=entry['path'], sha256=entry['sha256'], bytes=len(raw),
                  declared_kind=parsed['declared_kind'], capture_status=parsed['capture_status'],
                  stop_code=parsed['stop_code'], queries_recorded=parsed['queries_recorded'],
                  pending_attempt=parsed['pending_attempt'], truncated_tail=parsed['truncated_tail'],
                  nominal_computer_gmt_date=header[3].decode('ascii'),
                  origin_nominal_gmt_seconds=int(header[4]), scope='separate_reported_observation',
                  cross_run_identity_established=False)
    if key == 'metadata127':
        report.update(properties=[r for r in parsed['rows'] if r['type'] in ('I', 'D', 'V')],
                      weekly_sessions=[r for r in parsed['rows'] if r['type'] == 'W'],
                      weekly_template_truncated=parsed['weekly_template_truncated'],
                      weekly_template_is_verified_calendar=False,
                      dollar_swap_or_margin_inferred=False)
    else:
        report.update(commission_state=parsed['commission_state'],
                      commission_query=next((r for r in parsed['rows'] if r['type'] == 'K'), None),
                      commission_rules=parsed['commission_rules'],
                      pending_rule_payload=parsed['pending_rule_payload'],
                      margin_factors=[r for r in parsed['rows'] if r['type'] == 'M'],
                      commission_cost_USD=None, margin_requirement_USD=None, slippage_terms=None,
                      reported_empty_means_zero_total_cost=False)
    return report


def assess(root, raw_manifest):
    manifest = strict_json(raw_manifest, 65_536)
    _keys(manifest, ('schema', 'quote_manifest', 'context'))
    if (manifest['schema'] != SCHEMA + '_manifest' or type(manifest['context']) is not list
            or len(manifest['context']) != len(CONTEXT)):
        raise ValueError('eligibility_manifest')
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('eligibility_root')
    root = root.resolve()
    raw_quotes = _bound(root, manifest['quote_manifest'], 65_536, re.compile(r'config/paired-replay-133\.json'))
    replay = replay_manifest(root, raw_quotes)
    paired_manifest = strict_json(raw_quotes, 65_536)
    run_reports = []
    kinds = {run['audit']['declared_kind'] for run in replay['runs']}
    for entry, run in zip(paired_manifest['runs'], replay['runs'], strict=True):
        raw = _read(root, entry['path'], MAX_BYTES)
        if digest(raw) != entry['sha256']:
            raise ValueError('eligibility_quote_changed')
        parsed = inspect_bytes(raw)
        audit = run['audit']
        first, last = audit['first_replay_offset_us'], audit['last_replay_offset_us']
        bounds = span_bounds(first, last) if first is not None else dict(
            recorded_marker_span_us=None, maximum_fully_contained_one_hour_intervals=0,
            qualified_aligned_h1_bars=0, UTC_alignment_established=False)
        raw_offsets = [r['raw_clocks']['time_trade_server'] - r['raw_clocks']['time_gmt']
                       for r in parsed['rows'] if r['type'] == 'C']
        run_reports.append(dict(id=run['id'], path=entry['path'], sha256=entry['sha256'], bytes=len(raw),
                                declared_kind=parsed['declared_kind'], replay=audit, coverage=bounds,
                                origin_nominal_gmt_seconds=parsed['origin_nominal_gmt_seconds'],
                                raw_server_minus_computer_gmt_seconds_min=min(raw_offsets) if raw_offsets else None,
                                raw_server_minus_computer_gmt_seconds_max=max(raw_offsets) if raw_offsets else None,
                                raw_offset_applied=False, source_age_ms_bounds=None,
                                longest_observed_repeat_span_us=parsed['longest_observed_repeat_span_us'],
                                repeat_span_is_quote_age=False, qualified_warmup_bars_shortfall=WARMUP_HOURS,
                                qualifies_for_strategy_evaluation=False))
    context = []
    for item, (key, pattern, module) in zip(manifest['context'], CONTEXT, strict=True):
        _keys(item, ('id', 'path', 'sha256'))
        if item['id'] != key:
            raise ValueError('eligibility_context_order')
        entry = {k: item[k] for k in ('path', 'sha256')}
        raw = _bound(root, entry, module.MAX_BYTES, pattern)
        parsed = module.inspect_bytes(raw)
        header = raw.split(b'\r\n', 1)[0].split(b'\t')
        match = pattern.fullmatch(item['path'])
        if int(match[1]) != int(header[4]) or int(match[3]) != int(header[5]):
            raise ValueError('eligibility_context_origin')
        kinds.add(parsed['declared_kind'])
        context.append(_context_report(key, entry, raw, parsed))
    if len(kinds) != 1:
        raise ValueError('eligibility_mixed_provenance')
    requirements = [
        ('wire_integrity', 'observed', 'Pinned bytes and frozen readers accept each file separately; this does not authenticate its producer.'),
        ('source_context', 'unverified', 'Keep run/program provenance and demo/source scope; current metadata from another run is not an atomic contract or account-identity join.'),
        ('absolute_time_and_calendar_mapping', 'unverified', 'Record clock synchronization evidence, source time convention, offset/DST rule, uncertainty bounds and resets. Do not subtract an observed raw offset as a UTC correction.'),
        ('quote_age', 'unverified', 'Compare source/receipt bounds only in an established common time domain, including uncertainty and post-marker delay. The frozen adapter permits age 0..2000ms; repeat duration is not quote age.'),
        ('sampling_and_execution', 'unqualified', 'Declare sampled-quote fills, polling outages, no-fill/stale handling and adverse gap/latency scenarios. Latest-quote polling does not prove complete tick delivery or tradable fills.'),
        ('costs_and_contract', 'incomplete', 'Bind applicable commission/fee, spread, financing/rollover, conversion and margin assumptions to the evaluation scope; stress slippage and outages. Empty rules and zero margin fields are not zero total costs.'),
        ('sessions_and_coverage', 'unverified', 'Establish session/holiday/rollover calendar and missing-hour rules. Weekly session templates do not establish holidays or qualified closed H1 bars.'),
        ('warmup', 'insufficient', 'The fixed H1 comparison needs 201 observed closed H1 bars. Each short run has zero qualified aligned bars; do not join runs or interpolate.'),
        ('untouched_validation', 'unavailable', 'Freeze candidates, costs, periods and handling rules before outcomes; allocate the prospective 480 development and 480 untouched validation bars. Counts alone do not establish statistical sufficiency.'),
        ('calendar_partition_policy', 'blocked', 'October2026 remains quarantined, November–December reserved/untouched and2025 consumed. This assessment schedules or authorizes no collection.')]
    return dict(schema=SCHEMA, manifest_sha256=digest(raw_manifest),
                quote_manifest_binding=manifest['quote_manifest'],
                declared_kind=next(iter(kinds)), assessment='not_ready_for_fixed_h1_evaluation',
                runs=run_reports, context=context, native_input_files=len(run_reports) + len(context),
                native_input_bytes=sum(r['bytes'] for r in run_reports + context),
                requirements=[dict(key=k, status=s, evidence_or_action=d) for k, s, d in requirements],
                pilot_plan=pilot_plan(), frozen_model_assumptions=asdict(Config()),
                frozen_cost_scenarios=scenarios(), model_assumptions_applied_to_native_data=False,
                financial_model_changed=False, cross_run_contract_established=False,
                combined_continuous_history_hours=None, qualified_aligned_h1_bars=0,
                strategy_evaluated=False, financial_engine_events=0, profitability_established=False,
                implementation_grants_admission=False, collection_authorized=False, **DENIED)


def markdown(report):
    lines = ['# Forward input eligibility134', '',
             '**Status: not ready for the fixed H1 strategy comparison.**', '',
             '| Separate run | Paired packets | Marker span (seconds) | Maximum fully contained 1h intervals | Qualified H1 bars |',
             '| --- | ---: | ---: | ---: | ---: |']
    for run in report['runs']:
        coverage = run['coverage']; span = coverage['recorded_marker_span_us']
        label = 'unobserved' if span is None else f'{span / 1_000_000:.6f}'
        lines.append(f"| {run['id']} | {run['replay']['packets_committed']} | {label} | {coverage['maximum_fully_contained_one_hour_intervals']} | 0 |")
    lines += ['', 'The span bound is geometry, not a usable-bar count. Runs remain separate.', '',
              '| Requirement | Status | Evidence or next action |', '| --- | --- | --- |']
    lines += [f"| {row['key']} | {row['status']} | {row['evidence_or_action']} |" for row in report['requirements']]
    cost = report['context'][1]
    leverage = next((r['value'] for r in report['context'][0]['properties'] if r['key'] == 'account_leverage'), None)
    lines += ['', f"Earlier metadata reports leverage {leverage}; the unchanged hypothetical model uses {report['frozen_model_assumptions']['leverage']}.",
              f"Earlier commission response: **{cost['commission_state']}**; applicable USD charges remain unknown.",
              'Neither separate observation is applied as this quote run’s account contract.', '',
              'Prospective engineering target: 201 warm-up + 480 development + 480 untouched',
              'validation closed H1 bars = **1,161 observed closed hours**. This is not a',
              'statistical sufficiency claim or a collection schedule. Partial/interpolated',
              'hours and closed-session absences cannot be manufactured into observations.', '',
              'These inputs remain diagnostics. No strategy/P&L, UTC correction, financial-engine',
              'admission, automated orders or real-money execution is produced.', '']
    return '\n'.join(lines)
