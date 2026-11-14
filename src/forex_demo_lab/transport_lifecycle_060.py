"""Injected offline lifecycle. No native adapter, SDK, pipe or order operations.

`pending` and `boundary` are capabilities of the injected model, NOT inferred
from FileReadArray returning zero, FileSize, or FileReadInteger's value.
"""
from dataclasses import dataclass
import hashlib

from .capture_budget_047 import clock_sample, require_guard, WINDOW_MS
from .capture_wire_047 import decode_response, encode_response
from .windows_pipe_047 import PipeRejected

# Preserve previous categories; assign separate closed categories to the rest
# of the documented MQL file-error range. Never retroactively classify057.
MQL_ERRORS = {5007: 2, 5010: 3, 5011: 4, 5015: 5}
MQL_ERRORS.update({code: 10 + code - 5001 for code in range(5001, 5028)
                   if code not in MQL_ERRORS})


def native_error(code):
    if type(code) is not int or not 0 <= code <= 2147483647:
        return 7
    return 0 if code == 0 else MQL_ERRORS.get(code, 6)


@dataclass(frozen=True)
class Observation:
    status: str
    data: bytes = b''
    boundary: bool = False
    error: int = 0


@dataclass(frozen=True)
class Cleanup:
    closed: bool
    pending_retained: bool = False


ACK_MAGIC = b'FXDL060A'


class OfflineLifecycle:
    """One request, explicit pending readiness, exact response, bounded ACK.

    Injected calls must return to permit deadline checks. The model does not
    interrupt blocking calls. Native boundary/readiness proof is still missing.
    """
    def __init__(self, policy, clock, guard):
        self.policy, self.clock, self.guard = policy, clock, guard
        self.first = self.last = clock_sample(clock)
        self.used = False
        self.receipt = None
        self.ack_deadline_ns = None

    def sample(self):
        now = clock_sample(self.clock)
        if any(a < b for a, b in zip(now, self.last)):
            raise PipeRejected('clock_reversed')
        delta = tuple(a-b for a, b in zip(now, self.first))
        if delta[0] >= WINDOW_MS or delta[1] >= WINDOW_MS*1000000 or delta[2] >= WINDOW_MS:
            raise PipeRejected('session_expired')
        if abs(delta[0]-delta[1]//1000000) > 1000 or abs(delta[2]-delta[1]//1000000) > 1000:
            raise PipeRejected('clock_discontinuity')
        self.last = now
        if self.ack_deadline_ns is not None and now[1] >= self.ack_deadline_ns:
            raise PipeRejected('receipt_expired')
        if self.receipt is not None:
            r = self.receipt
            if not r['issued_boot_ms'] <= now[2] < r['expires_boot_ms'] or now[0] >= r['expires_utc_ms']:
                raise PipeRejected('receipt_expired')
        return now

    def call(self, function, *args):
        self.sample()
        try:
            value = function(*args)
        except Exception:
            raise PipeRejected('operation_failed_details_redacted') from None
        self.sample()
        return value

    @staticmethod
    def checked(value):
        if (type(value) is not Observation or type(value.status) is not str or
                type(value.data) is not bytes or type(value.boundary) is not bool):
            raise PipeRejected('observation_rejected')
        if native_error(value.error) != 0:
            raise PipeRejected('read_error')
        return value

    def run(self, channel):
        if self.used:
            raise PipeRejected('request_unavailable')
        self.used = True
        result = dict(version='offline_lifecycle_060_v1', completed=False,
                      reason=None, polls=0, reply_bytes=0, ack_written=False,
                      closed=False, pending_retained=False, native_ready=False,
                      quote_reads=0, orders=0)
        try:
            require_guard(self.guard)
            self.sample()  # Guard work may have advanced clocks.
            # Bounded count as well as session clock: no spin on frozen clocks.
            for _ in range(900001):
                value = self.checked(self.call(channel.observe))
                result['polls'] += 1
                if value.status == 'pending':
                    if value.data or value.boundary:
                        raise PipeRejected('pending_observation_rejected')
                    self.call(channel.wait)
                    continue
                if value.status != 'ready':
                    raise PipeRejected('peer_disconnected')
                # Zero returned by an actual read is failure, never readiness.
                if len(value.data) != 84:
                    raise PipeRejected('frame_length_rejected')
                if not value.boundary:
                    raise PipeRejected('frame_boundary_unproven')
                result['reply_bytes'] = 84
                require_guard(self.guard)
                now = self.sample()
                self.receipt = decode_response(value.data, self.policy, now[0], now[2])
                self.sample()
                remaining = min(self.receipt['expires_boot_ms']-now[2],
                                self.receipt['expires_utc_ms']-now[0])
                self.ack_deadline_ns = now[1] + remaining*1000000
                ack = ACK_MAGIC + hashlib.sha256(value.data).digest()
                outcome = self.checked(self.call(channel.ack, ack, remaining))
                if outcome.status != 'written' or outcome.data != ack or not outcome.boundary:
                    raise PipeRejected('ack_unconfirmed')
                require_guard(self.guard)
                self.sample()  # Reject an expired/reversed clock after ACK/guard.
                result['ack_written'] = True
                result['completed'] = True
                break
            else:
                raise PipeRejected('poll_budget_exhausted')
        except Exception as exc:
            allowed = {'clock_reversed','session_expired','clock_discontinuity',
                       'receipt_expired','operation_failed_details_redacted',
                       'observation_rejected','read_error','pending_observation_rejected',
                       'peer_disconnected','frame_length_rejected','frame_boundary_unproven',
                       'ack_unconfirmed','poll_budget_exhausted'}
            result['reason'] = str(exc) if str(exc) in allowed else 'validation_failed_details_redacted'
            result['completed'] = False
        finally:
            try:
                cleanup = channel.finish()
                if (type(cleanup) is not Cleanup or type(cleanup.closed) is not bool or
                        type(cleanup.pending_retained) is not bool):
                    raise ValueError()
                result['closed'], result['pending_retained'] = cleanup.closed, cleanup.pending_retained
                if not cleanup.closed or cleanup.pending_retained:
                    result['completed'] = False
                    result['reason'] = 'cleanup_unconfirmed'
                elif result['completed']:
                    self.sample()  # Cleanup can also block; never hide expiry.
            except Exception:
                result['completed'] = False
                result['reason'] = 'cleanup_failed_details_redacted'
        return result


def issue_frame(authority, policy):
    """Use unchanged047 one-use issuer in a temporary offline reservation only."""
    return encode_response(authority.issue(policy.phase, policy.digest))
