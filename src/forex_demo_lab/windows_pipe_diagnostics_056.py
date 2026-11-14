"""New diagnostic IO derivative of frozen047; no SDK or market functions.

Native bindings, security and identity methods remain inherited without caches.
Only io is replaced. Injected APIs are for offline tests, never account proof.
"""
import ctypes as C
from ctypes import wintypes as W
import time
from .windows_pipe_047 import WindowsPipe, OVERLAPPED, PipeRejected, _PENDING

ERRORS = {5: 'access_denied', 6: 'invalid_handle', 87: 'invalid_parameter',
          109: 'broken_pipe', 232: 'pipe_closing', 233: 'pipe_not_connected',
          234: 'more_data', 535: 'pipe_connected', 995: 'operation_aborted',
          996: 'io_incomplete', 997: 'io_pending'}
REASONS = frozenset(('event_create_rejected','io_operation_rejected','cancellation_not_drained',
    'io_deadline_exceeded','io_wait_rejected','io_completion_rejected','short_write_rejected',
    'read_count_rejected','unexpected_failure'))

def error_category(code):
    if type(code) is not int or not 0 <= code <= 0xffffffff:
        return 'unknown'
    return ERRORS.get(code, 'other')  # Failure + zero is not success.

def duration(start, end, limit_us=3000000):
    if type(start) is not int or type(end) is not int or start < 0 or end < start:
        return None, 'clock_invalid'
    us = (end-start)//1000
    return (us, 'measured') if us <= limit_us else (None, 'over_bound')

class DiagnosticWindowsPipe056(WindowsPipe):
    def __init__(self, *, injected_api=None, now=time.monotonic_ns):
        if injected_api is None:
            super().__init__()
            self._error = C.get_last_error
        else:
            for name in ('event', 'close', 'connect', 'read', 'write', 'result', 'wait', 'cancel'):
                setattr(self, name, getattr(injected_api, name))
            self._error = injected_api.get_error
        self._now = now
        self.last_io = None

    def io(self, handle, kind, data=None, size=0, timeout_ms=2000):
        self.last_io = None
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= 2000:
            raise PipeRejected('io_deadline_rejected')
        if type(kind) is not str or kind not in ('connect', 'read', 'write'):
            raise PipeRejected('io_kind_rejected')
        if kind == 'write' and (type(data) is not bytes or not 1 <= len(data) <= 128):
            raise PipeRejected('io_frame_rejected')
        if kind == 'read' and (type(size) is not int or not 1 <= size <= 128):
            raise PipeRejected('io_frame_rejected')
        events = []
        try: start = self._now()
        except Exception: raise PipeRejected('clock_invalid') from None
        event = None
        overlap = buffer = None
        unresolved = retained = False
        reason = 'ok'
        count = W.DWORD()
        def note(stage, ok, code=None):
            events.append(dict(stage=stage, category='ok' if ok else error_category(code)))
        try:
            event = self.event(None, True, False, None)
            error = self._error() if not event else None
            note('event_create', bool(event), error)
            if not event:
                raise PipeRejected('event_create_rejected')
            overlap = OVERLAPPED(); overlap.hEvent = event
            buffer = C.create_string_buffer(data, len(data)) if kind == 'write' else C.create_string_buffer(max(size, 1))
            if kind == 'connect': ok = self.connect(handle, C.byref(overlap))
            elif kind == 'read': ok = self.read(handle, buffer, size, None, C.byref(overlap))
            else: ok = self.write(handle, buffer, len(data), None, C.byref(overlap))
            error = self._error() if not ok else None  # Before any other Win32 call.
            note('submit', bool(ok), error)
            if kind == 'connect' and (ok or error == 535): return b''
            if not ok and error != 997: raise PipeRejected('io_operation_rejected')
            unresolved = not ok
            if not ok:
                waited = self.wait(event, timeout_ms)
                error = self._error() if waited == 0xffffffff else None
                events.append(dict(stage='wait', category='ok' if waited == 0 else
                                   'timeout' if waited == 258 else error_category(error)))
                if waited != 0:
                    cancelled = self.cancel(handle, C.byref(overlap))
                    error = self._error() if not cancelled else None
                    note('cancel', bool(cancelled), error)
                    drained = self.wait(event, 1000)
                    error = self._error() if drained == 0xffffffff else None
                    events.append(dict(stage='drain_wait', category='ok' if drained == 0 else
                                       'timeout' if drained == 258 else error_category(error)))
                    if drained != 0: raise PipeRejected('cancellation_not_drained')
                    completed = self.result(handle, C.byref(overlap), C.byref(count), False)
                    error = self._error() if not completed else None
                    note('drain_result', bool(completed), error)
                    unresolved = not completed and error not in (109, 232, 233, 234, 995)
                    if unresolved: raise PipeRejected('cancellation_not_drained')
                    # Completion racing cancellation never turns a deadline into success.
                    raise PipeRejected('io_deadline_exceeded' if waited == 258 else 'io_wait_rejected')
            completed = self.result(handle, C.byref(overlap), C.byref(count), False)
            error = self._error() if not completed else None
            note('completion', bool(completed), error)
            unresolved = not completed and error not in (109, 232, 233, 234, 995)
            if not completed: raise PipeRejected('io_completion_rejected')
            if kind == 'write' and count.value != len(data): raise PipeRejected('short_write_rejected')
            if kind == 'read' and count.value > size: raise PipeRejected('read_count_rejected')
            return buffer.raw[:count.value] if kind == 'read' else b''
        except PipeRejected as exc:
            reason = exc.args[0] if len(exc.args)==1 and type(exc.args[0]) is str and exc.args[0] in REASONS else 'unexpected_failure'
            raise PipeRejected(reason) from None
        except Exception:
            reason = 'unexpected_failure'
            raise PipeRejected(reason) from None
        finally:
            if unresolved:
                retained = True
                _PENDING.append((overlap, event, buffer, handle))
            closed = False
            if event and not retained:
                try:
                    closed = bool(self.close(event))
                    error = self._error() if not closed else None
                    note('event_close', closed, error)
                except Exception:
                    events.append(dict(stage='event_close', category='unknown'))
            try: elapsed, timing = duration(start, self._now())
            except Exception: elapsed, timing = None, 'clock_invalid'
            self.last_io = dict(version='windows_io_056_v1', kind=kind, events=events,
                                reason=reason, elapsed_us=elapsed, timing=timing,
                                transferred_bytes=count.value if reason == 'ok' else None,
                                pending_retained=retained, event_closed=closed)
