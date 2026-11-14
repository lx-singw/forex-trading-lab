"""Offline audit of the completed081 metadata observation, never an executor.

Only the complete four-sample branch is accepted. Caller expectations must be
derived from sealed081 inputs, not copied from the reports being audited.
Observed durations are not upper bounds or permission for MQL/market activity.
"""
import hashlib

from .native_timing_081 import validate_authorization081, dispatch_value081, PHASE
from .public_trace_081 import invocation_bytes081, PUBLIC_LIMITS081
from .sharing_adapter_076 import exact076, encoded076
from .sharing_probe_062 import ProbeRejected
from .timing_profile_077 import LIMITS077, DATE, SESSION_MS
from .timing_outcome_079 import START_KEYS, OUTCOME_KEYS, utc_stamp

STAGES = ('preflight', 'terminal_image', 'editor_image', 'signature',
          'terminal_process', 'helper_process', 'helper_chain', 'sdk_import',
          'sdk_attach', 'account_metadata', 'profile_samples', 'file_cleanup',
          'sdk_cleanup')
RAW_MARKERS = ('invocation', 'dispatch', 'component')
PUBLIC_METRICS = ('public_record_reads', 'public_record_bytes', 'public_record_stats',
                  'public_source_reads', 'public_source_bytes', 'public_source_stats', 'steps')
CLEANUP = dict(bootstrap_cleanup=dict(all_handles_closed=True,
    allocations_released=True, synthetic_directory_retained=False,
    unconfirmed_handles=0), errors=[], file_cleanup=None, outcome=None,
    sdk_shutdown_called=True)
ROOT_FALSE = ('annual_eligible', 'fresh_performance_eligible', 'latency_guaranteed',
              'native_launch_ready', 'native_mql_verified',
              'native_publication_verified', 'orders_available')
ROOT_ZERO = ('market_reads', 'orders', 'receipt_permissions', 'script_launches',
             'terminal_deployments', 'terminal_log_content_reads')
AUTH_PINS = ('preparation_sha256', 'policy_sha256', 'helper_profile_sha256',
             'build_record_sha256', 'component_contract_sha256')


def require(condition):
    if not condition:
        raise ValueError()


def integer(value, low=0, high=2**63-1):
    require(type(value) is int and low <= value <= high)
    return value


def digest(value):
    require(type(value) is str and len(value) == 64 and
            all(c in '0123456789abcdef' for c in value))
    return value


def timing_scenarios082(guard_ms):
    """Independent076 arithmetic using an observed maximum as a scenario input."""
    integer(guard_ms, 0, SESSION_MS)
    rows = []
    for name, u, c, n, o, w in (
            ('zero_other_overhead', 0, 0, 0, 0, 0),
            ('retained_wait_overshoot', 0, 0, 0, 0, 15000),
            ('prior_illustrative_overheads', 1000, 100, 1, 500, 15000)):
        launch = 2*guard_ms + u + c + o
        start = guard_ms + u + o
        completion = 16*guard_ms + u + c + 5000 + 6*n + o + w
        rows.append(dict(scenario=name, guard_ms=guard_ms, manual_launch_ms=u,
            command_delay_ms=c, native_call_ms=n, overhead_ms=o,
            wait_overshoot_ms=w, launch_ms=launch, latest_start_ms=start,
            completion_ms=completion, launch_fits=launch <= 10000,
            start_margin_fits=start + 250 < 5000,
            end_margin_fits=completion < 29750))
    return dict(scenarios=rows, repeated_observed_maximum_only=True,
        measured_critical_path=False, worst_case_bound_established=False,
        actual_wait_and_io_measured=False, runtime_authorized=False,
        native_launch_ready=False, latency_guaranteed=False)


def audit_observation082(auth_raw, expected_auth, auth_sha, component_expected_raw,
        markers, sidecars_present, started, outcome, started_sha, launcher_sha,
        public, runtime, checks_sha, review_sha, public_sha,
        expected_public_metrics, sample_hash_bytes, bootstrap_hash_bytes):
    try:
        auth = validate_authorization081(auth_raw, expected_auth, auth_sha)
        for h in (started_sha, launcher_sha, checks_sha, review_sha, public_sha):
            digest(h)
        require(type(component_expected_raw) is bytes and
                0 < len(component_expected_raw) <= 8192)
        require(hashlib.sha256(component_expected_raw).hexdigest() ==
                auth['component_contract_sha256'])
        expected_markers = dict(invocation=invocation_bytes081(),
            dispatch=encoded076(dispatch_value081(auth, auth_sha)),
            component=component_expected_raw)
        require(exact076(markers, expected_markers))
        require(exact076(sidecars_present, dict.fromkeys(RAW_MARKERS, False)))

        require(type(started) is dict and set(started) == START_KEYS)
        require(type(outcome) is dict and set(outcome) == OUTCOME_KEYS)
        require(exact076(started, dict(version='native_timing_invocation_082_v1',
            invocation_consumed=True, maximum_invocations=1,
            started_utc=started['started_utc'], authorization_sha256=auth_sha,
            entry_sha256=auth['entry_sha256'], launcher_sha256=launcher_sha,
            orders_available=False)))
        elapsed = integer(outcome['elapsed_ms'], 0, SESSION_MS)
        require(exact076(outcome, dict(version='native_timing_invocation_outcome_082_v1',
            invocation_consumed=True, native_entry_invocations=1, exit_code=0,
            elapsed_ms=elapsed, ended_utc=outcome['ended_utc'],
            output_characters=146, output_category='fixed_native_summary',
            native_summary=dict(public_completed=True, stop_reason=None,
                orders_available=False, entry_completed=True),
            started_record_sha256=started_sha, orders_available=False)))
        begin = utc_stamp(started['started_utc'], DATE)
        end = utc_stamp(outcome['ended_utc'], DATE)
        require(end >= begin and elapsed <= (end-begin).total_seconds()*1000 + 1)

        require(type(expected_public_metrics) is dict and
                set(expected_public_metrics) == set(PUBLIC_METRICS))
        caps = (PUBLIC_LIMITS081['record_reads'], PUBLIC_LIMITS081['record_bytes'],
            PUBLIC_LIMITS081['record_stats'], PUBLIC_LIMITS081['source_reads'],
            PUBLIC_LIMITS081['source_bytes'], PUBLIC_LIMITS081['source_stats'],
            PUBLIC_LIMITS081['trace_steps'])
        for k, cap in zip(PUBLIC_METRICS, caps):
            integer(expected_public_metrics[k], 1, cap)
        require(exact076(public, dict(version='native_timing_public_081_v1',
            date=DATE, phase=PHASE, account_type_verified=False,
            authority_validated=True, completed=True, dispatch_reserved=True,
            invocation_consumed=True, latency_guaranteed=False,
            native_launch_ready=False, orders_available=False,
            owned_cleanup_applicable=False, owned_native_backend_created=False,
            sdk_connections=0, sdk_queries=0, source_index=None,
            source_pins_verified=True, stop_reason=None, stopped_operation=None,
            stopped_stage=None, **expected_public_metrics)))

        require(type(runtime) is dict)
        counts = runtime['counts']
        require(type(counts) is dict and set(counts) == set(LIMITS077))
        for k, cap in LIMITS077.items():
            integer(counts[k], 0, cap)
        sample_bytes = integer(sample_hash_bytes, 1, LIMITS077['hash_bytes'])
        bootstrap_bytes = integer(bootstrap_hash_bytes, 1, LIMITS077['hash_bytes'])
        fixed = dict(guards=8, profile_samples=4, hash_reads=26+4*25,
            hash_bytes=bootstrap_bytes+4*sample_bytes, sdk_queries=1+8*11,
            sdk_connections=1, sdk_shutdowns=1, reservation_writes=1,
            trust_queries=1)
        for k, v in fixed.items():
            require(counts[k] == v)
        for k in ('clock_samples', 'process_opens', 'identity_tokens',
                  'token_queries', 'process_snapshots', 'process_entries',
                  'native_calls', 'hash_path_stats', 'startup_path_stats'):
            integer(counts[k], 1, LIMITS077[k])
        require(counts['identity_tokens'] == counts['process_opens'])
        require(counts['local_frees'] == counts['identity_tokens'])
        require(counts['token_queries'] == 3*counts['identity_tokens'])
        require(counts['closes'] == counts['process_opens'] +
                counts['identity_tokens'] + counts['process_snapshots'])
        require(exact076(runtime['cleanup'], CLEANUP))
        stages = [dict(stage=n, started=True, completed=True) for n in STAGES]
        require(exact076(runtime['stage_trace'], stages))

        observation = runtime['observation']
        require(type(observation) is dict)
        samples = observation['samples']
        require(type(samples) is list and len(samples) == 4)
        cores = []; composites = []
        for row in samples:
            require(type(row) is dict and type(row['core_guard_ms']) is list and
                    len(row['core_guard_ms']) == 2)
            gs = [integer(g, 0, SESSION_MS) for g in row['core_guard_ms']]
            composite = integer(row['composite_sample_ms'], sum(gs), SESSION_MS)
            require(exact076(row, dict(core_guard_ms=gs, composite_sample_ms=composite,
                hash_reads=25, hash_bytes=sample_bytes, sdk_queries=22)))
            cores.extend(gs); composites.append(composite)
        require(sum(composites) <= elapsed)
        require(exact076(observation, dict(version='timing_profile_observation_077_v1',
            phase='77000000000000000000000000000001', date=DATE,
            build_record_sha256=auth['build_record_sha256'], cleanup=CLEANUP,
            completed=True, counts=counts, latency_guaranteed=False,
            native_launch_ready=False, native_timing_verified=False,
            observations_only=True, observed_composite_max_ms=max(composites),
            observed_core_guard_max_ms=max(cores), orders_available=False,
            preparation_contract_sha256=auth['component_contract_sha256'],
            runtime_authorized=False, samples=samples, samples_completed=4,
            stop_reason=None)))
        expected_runtime = dict(version='native_timing_entry_081_v1', date=DATE,
            phase=PHASE, authorization_sha256=auth_sha, counts=counts,
            cleanup=CLEANUP, entry_completed=True, native_entry_invoked=True,
            observation=observation, observations_only=True,
            public_outcome_sha256=public_sha, checks_sha256=checks_sha,
            completion_review_sha256=review_sha,
            reservation_sha256=auth['component_contract_sha256'],
            signature_checks_passed=True, stage_trace=stages,
            stop_reason=None, stopped_stage=None,
            **{k: auth[k] for k in AUTH_PINS},
            **dict.fromkeys(ROOT_FALSE, False), **dict.fromkeys(ROOT_ZERO, 0))
        require(exact076(runtime, expected_runtime))
        return dict(audit_passed=True, native_metadata_observation_verified=True,
            native_entry_invocations=1, invocation_consumed=True, cli_exit_code=0,
            invocation_elapsed_ms=elapsed, samples_completed=4, guards=8,
            sdk_queries=89, sdk_connections=1, sdk_shutdowns=1,
            hash_reads=126, hash_bytes=counts['hash_bytes'],
            sample_hash_bytes=sample_bytes, bootstrap_hash_bytes=bootstrap_bytes,
            account_type_verified_this_attempt=True, signature_checks_observed=True,
            owned_cleanup_confirmed=True, observed_core_guard_min_ms=min(cores),
            observed_core_guard_max_ms=max(cores),
            observed_composite_max_ms=max(composites), raw_markers_verified=3,
            capture_sample_count_omitted=True,
            authoritative_sample_count_source='sealed_native_runtime',
            public_report_precedes_native_work=True,
            timing_comparison=timing_scenarios082(max(cores)),
            retry_authorized=False, old070_cause_proven=False,
            authorization_sha256=auth_sha,
            **dict.fromkeys(ROOT_FALSE, False), **dict.fromkeys(ROOT_ZERO, 0))
    except Exception:
        raise ProbeRejected('timing_observation_audit_rejected') from None
