"""Offline framing/acknowledgment candidates; no permission issuer or IO loop."""
import hashlib
from .capture_wire_047 import decode_response
from .capture_budget_047 import require_guard
from .windows_pipe_diagnostics_056 import duration
from .windows_pipe_047 import PipeRejected

MQL_ERRORS = {5007: 2, 5010: 3, 5011: 4, 5015: 5}

def native_error(code):
    if type(code) is not int or not 0 <= code <= 2147483647: return 7
    if code == 0: return 0
    return MQL_ERRORS.get(code, 6)

def native_read_report(count, error, start_us, end_us):
    if type(count) is not int or not 0 <= count <= 85: raise PipeRejected('read_count_rejected')
    if type(start_us) is not int or type(end_us) is not int:
        elapsed, timing = None, 'clock_invalid'
    else: elapsed, timing = duration(start_us*1000, end_us*1000, 900000000)
    return dict(version='native_read_056_v1', reply_bytes=count,
                error_category=native_error(error), elapsed_us=elapsed, timing=timing)

def frame_candidate(raw, requested, error=0):
    """No partial accumulation/retry. Returns a frame only on exact success.

    A returned84 from an exact84 read cannot reveal an unread suffix. This
    ambiguity must be resolved by a future native framing protocol, not hidden.
    """
    if type(raw) is not bytes or requested not in (84, 85): raise PipeRejected('frame_input_rejected')
    if len(raw) != 84 or native_error(error) != 0: raise PipeRejected('frame_rejected')
    return raw

def modeled_read(read, requested, now_us):
    """One injected read, no native IPC or retry; duration is measurement only."""
    if type(requested) is not int or requested not in (84,85): raise PipeRejected('frame_input_rejected')
    start=now_us()
    try: raw,error=read(requested)
    except Exception: raise PipeRejected('read_failed_details_redacted') from None
    end=now_us()
    if type(raw) is not bytes: raise PipeRejected('frame_input_rejected')
    report=native_read_report(len(raw),error,start,end)
    report['frame_accepted']=len(raw)==84 and native_error(error)==0
    return report

ACK_MAGIC = b'FXDL056A'

def consumption_ack(frame, policy, utc_ms, boot_ms, guard):
    """Local modeling only. Guard and frozen receipt validation precede ACK."""
    require_guard(guard)
    decode_response(frame, policy, utc_ms, boot_ms)
    return ACK_MAGIC + hashlib.sha256(frame).digest()

def validate_ack(raw, frame, policy, utc_ms, boot_ms, guard, started_ns, now_ns):
    if (type(started_ns) is not int or type(now_ns) is not int or
            not 0 <= now_ns-started_ns < 2000000000):
        raise PipeRejected('ack_deadline_rejected')
    expected = consumption_ack(frame, policy, utc_ms, boot_ms, guard)
    if type(raw) is not bytes or raw != expected: raise PipeRejected('ack_binding_rejected')
    return True
