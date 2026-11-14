"""Offline audit of the observed078 early preflight rejection; no native APIs.

This deliberately accepts only the recorded no-dispatch outcome. A future
partial/full SDK report needs its own independently declared audit. Absence
of resources is not a cleanup proof, and process duration is not guard latency.
"""
from datetime import datetime
import hashlib
import re

from .native_timing_078 import validate_authorization078
from .sharing_adapter_076 import exact076
from .sharing_probe_062 import ProbeRejected

INVENTORY = ('dispatch', 'dispatch_sidecar', 'reservation',
             'reservation_sidecar', 'runtime', 'runtime_sidecar')
START_KEYS = {'version', 'invocation_consumed', 'maximum_invocations',
              'started_utc', 'authorization_sha256', 'entry_sha256',
              'launcher_sha256', 'orders_available'}
OUTCOME_KEYS = {'version', 'invocation_consumed', 'native_entry_invocations',
                'exit_code', 'elapsed_ms', 'ended_utc', 'output_characters',
                'output_category', 'native_summary', 'started_record_sha256',
                'orders_available'}


def utc_stamp(value, date):
    if (type(value) is not str or
        re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}Z', value) is None):
        raise ValueError()
    stamp = datetime.fromisoformat(value[:-1] + '+00:00')
    if stamp.date().isoformat() != date:
        raise ValueError()
    return stamp


def audit_preflight079(auth_raw, expected_auth, auth_sha, started, outcome,
                       started_sha, launcher_sha, inventory):
    """Trusted expectations come from sealed078 inputs, never the grant itself."""
    try:
        auth = validate_authorization078(auth_raw, expected_auth, auth_sha)
        for digest in (started_sha, launcher_sha):
            if (type(digest) is not str or len(digest) != 64 or
                any(c not in '0123456789abcdef' for c in digest)):
                raise ValueError()
        if type(started) is not dict or set(started) != START_KEYS:
            raise ValueError()
        if type(outcome) is not dict or set(outcome) != OUTCOME_KEYS:
            raise ValueError()
        expected_start = dict(version='native_timing_invocation_079_v1',
            invocation_consumed=True, maximum_invocations=1,
            started_utc=started['started_utc'], authorization_sha256=auth_sha,
            entry_sha256=auth['entry_sha256'], launcher_sha256=launcher_sha,
            orders_available=False)
        if not exact076(started, expected_start):
            raise ValueError()
        expected_outcome = dict(version='native_timing_invocation_outcome_079_v1',
            invocation_consumed=True, native_entry_invocations=1, exit_code=1,
            elapsed_ms=outcome['elapsed_ms'], ended_utc=outcome['ended_utc'],
            output_characters=len('timing_preflight_rejected_details_redacted'),
            output_category='preflight_rejected', native_summary=None,
            started_record_sha256=started_sha, orders_available=False)
        if not exact076(outcome, expected_outcome):
            raise ValueError()
        elapsed = outcome['elapsed_ms']
        if type(elapsed) is not int or not 0 <= elapsed <= 2**63-1:
            raise ValueError()
        begin = utc_stamp(started['started_utc'], auth['date'])
        end = utc_stamp(outcome['ended_utc'], auth['date'])
        if end < begin or elapsed > (end-begin).total_seconds()*1000 + 1:
            raise ValueError()
        if not exact076(inventory, dict.fromkeys(INVENTORY, False)):
            raise ValueError()
        # Frozen entry reserves dispatch BEFORE native backend construction,
        # SDK import, SDK reservation or initialize. No dispatch + the fixed CLI
        # rejection proves this branch, not a particular public check's cause.
        return dict(audit_passed=True, native_entry_invocations=1,
            invocation_consumed=True, cli_exit_code=1,
            invocation_elapsed_ms=elapsed, stopped_stage='public_preflight',
            stop_reason='timing_preflight_rejected_details_redacted',
            exact_failure_cause_known=False, dispatch_present=False,
            sdk_reservation_present=False, runtime_report_present=False,
            sdk_connections=0, sdk_shutdowns=0, guards=0, sdk_queries=0,
            samples_completed=0, owned_native_backend_created=False,
            owned_cleanup_applicable=False, owned_cleanup_confirmed=None,
            native_timing_verified=False, timing_bounds_comparison_possible=False,
            signature_checks_observed=False, account_type_verified_this_attempt=False,
            elapsed_is_guard_latency=False, retry_authorized=False,
            script_launches=0, terminal_deployments=0,
            terminal_log_content_reads=0, market_reads=0, orders=0,
            receipt_permissions=0, orders_available=False, annual_eligible=False,
            fresh_performance_eligible=False, native_mql_verified=False,
            native_publication_verified=False, native_launch_ready=False,
            latency_guaranteed=False, old070_cause_proven=False,
            authorization_sha256=hashlib.sha256(auth_raw).hexdigest())
    except Exception:
        raise ProbeRejected('timing_outcome_audit_rejected') from None
