"""Invented-only helper/lifecycle supervision. Never launches a helper or terminal."""
from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import os
from pathlib import Path
import re

from .acquisition_lifecycle_138 import Checks, Lifecycle, State
from .segment_journal_138 import Reason, StorageFailure, inspect_segments, uint
from .paired_replay_133 import DENIED, canonical, strict_json

SCHEMA = 'invented_supervision140_v1'
ZERO = '0' * 64
MAX_FRAME, MAX_FRAMES = 2048, 32
READY_TIMEOUT_US, MAX_STATUS_AGE_US = 10_000_000, 1_000_000


class Event(str, Enum):
    START = 'start_requested'
    ACK = 'helper_start_ack'
    READY = 'helper_ready'
    ACTIVE = 'lifecycle_started'
    STOP = 'stop_requested'
    STOPPED = 'stopped'


class Cause(str, Enum):
    NONE = 'none'
    DISABLED = 'lifecycle_disabled'
    GUARD = 'guard_failed'
    OWNER = 'owner_lost'
    CLOCK = 'unsafe_clock'
    DEADLINE = 'job_deadline'
    START = 'helper_start_failed'
    TIMEOUT = 'helper_readiness_timeout'
    PROTOCOL = 'helper_protocol_failed'
    BINDING = 'helper_binding_failed'
    STALE = 'helper_status_stale'
    EXIT = 'helper_exited'
    LOST = 'helper_readiness_lost'
    POWER = 'helper_power_lost'
    LIFECYCLE = 'lifecycle_stopped'
    STORAGE = 'supervision_storage_failed'
    CANCEL = 'cancelled'


@dataclass(frozen=True)
class Observation:
    token: str | None = None
    observed_us: int | None = None
    running: bool = True
    create_ack: bool = False
    set_ack: bool = False
    ready_signal: bool = False
    mains: bool = True


class SyntheticHelper:
    """In-memory test port only. No binary path, subprocess or native API option."""
    def __init__(self):
        self.report = Observation()
        self.start_ack = self.cancel_ack = self.exit_ack = True
        self.throw_at = None
        self.token = None
        self.duration_ms = None
        self.calls = dict(start=0, poll=0, cancel=0, confirm_exit=0)
        self.exited = False

    def _call(self, operation):
        self.calls[operation] += 1
        if self.throw_at == operation:
            raise OSError('invented_helper_fault')

    def start(self, token, duration_ms):
        self._call('start'); self.token, self.duration_ms = token, duration_ms
        return self.start_ack

    def poll(self, now_us):
        self._call('poll')
        if type(self.report) is not Observation:
            return self.report
        return replace(self.report, token=self.token if self.report.token is None else self.report.token,
                       observed_us=now_us if self.report.observed_us is None else self.report.observed_us)

    def cancel(self):
        self._call('cancel'); return self.cancel_ack

    def confirm_exit(self):
        self._call('confirm_exit'); self.exited = self.exit_ack is True
        return self.exit_ack


class Ledger:
    """Exclusive, bounded, file-synced typed transition journal; no append/resume."""
    def __init__(self, root, job):
        root = Path(root).absolute()
        if (not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents))
                or type(job) is not str or not re.fullmatch('[a-f0-9]{32}', job)):
            raise ValueError('supervision140_root_or_job')
        self.path, self.job = root / ('Supervisor140-' + job + '.journal'), job
        self.stream = None
        self.poisoned = self.closed = False
        self.head, self.sequence, self.reserved = ZERO, 0, 0

    def poison(self):
        self.poisoned = True
        if self.stream is not None:
            try: self.stream.close()
            except OSError: pass
            self.stream = None

    def _sync(self):
        self.stream.flush(); os.fsync(self.stream.fileno())

    def append(self, event, cause, now_us, life, helper_seen_at, cancel_ack=None, exit_ack=None):
        if self.poisoned or self.closed: raise StorageFailure('supervision140_closed')
        if type(event) is not Event or type(cause) is not Cause: raise ValueError('supervision140_enum')
        uint(now_us)
        payload = canonical(dict(schema=SCHEMA, job=self.job, sequence=self.sequence + 1,
            previous=self.head, event=event.value, cause=cause.value, at_us=now_us,
            life_head=life.journal.head, life_committed=life.journal.committed,
            life_pending=life.pending is not None, life_poisoned=life.journal.poisoned,
            helper_seen_at=helper_seen_at, cancel_ack=cancel_ack, exit_ack=exit_ack))
        checksum = hashlib.sha256(payload).hexdigest()
        line = payload + b'\t' + checksum.encode('ascii') + b'\n'
        limit = MAX_FRAMES if event in (Event.STOP, Event.STOPPED) else MAX_FRAMES - 2
        if len(line) > MAX_FRAME or self.sequence >= limit or self.reserved + len(line) > MAX_FRAME * MAX_FRAMES:
            self.poison(); raise StorageFailure('supervision140_budget')
        self.reserved += len(line)
        try:
            if self.stream is None: self.stream = self.path.open('xb')
            if self.stream.write(line) != len(line): raise OSError('short_write')
            self._sync()
        except OSError:
            self.poison(); raise StorageFailure('supervision140_write') from None
        self.head, self.sequence = checksum, self.sequence + 1

    def close(self):
        try:
            if self.stream is not None: self.stream.close()
            self.stream = None; self.closed = True
        except OSError:
            self.poison(); raise StorageFailure('supervision140_close') from None


class Supervisor:
    def __init__(self, life, helper, ledger, *, enabled=False):
        if (type(life) is not Lifecycle or type(helper) is not SyntheticHelper or type(ledger) is not Ledger
                or type(enabled) is not bool or life.state is not State.OFF or life.journal.job_id != ledger.job
                or life.journal.segment != 0 or life.journal.poisoned or life.journal.head != ZERO
                or ledger.sequence != 0 or ledger.closed or ledger.poisoned):
            raise ValueError('supervision140_configuration')
        self.life, self.helper, self.ledger, self.enabled = life, helper, ledger, enabled
        self.state, self.cause = 'off', Cause.NONE
        self.last = self.origin = self.end = self.ready_until = self.helper_seen_at = None
        self.start_attempted = self.cleanup_attempted = False
        self.cancel_ack = self.exit_ack = None

    def _record(self, event, cause=Cause.NONE):
        self.ledger.append(event, cause, self.last, self.life, self.helper_seen_at, self.cancel_ack, self.exit_ack)

    def _halt(self, cause, checks):
        if self.state == 'stopped': return False
        self.cause = cause
        try: self._record(Event.STOP, cause)
        except StorageFailure: self.cause = Cause.STORAGE
        # Stop recording even if the independent supervision journal has failed.
        self.life.stop(self.last, checks if type(checks) is Checks else Checks())
        if self.start_attempted and not self.cleanup_attempted:
            self.cleanup_attempted = True
            try: self.cancel_ack = self.helper.cancel() is True
            except Exception: self.cancel_ack = False
            try: self.exit_ack = self.helper.confirm_exit() is True
            except Exception: self.exit_ack = False
        self.state = 'stopped'
        if not self.ledger.poisoned:
            try: self._record(Event.STOPPED, self.cause); self.ledger.close()
            except StorageFailure: self.cause = Cause.STORAGE
        return False

    def _record_or_stop(self, event, checks):
        try: self._record(event); return True
        except StorageFailure: return self._halt(Cause.STORAGE, checks)

    def _preflight(self, now_us, checks, owner_alive):
        try: uint(now_us)
        except ValueError: return self._halt(Cause.CLOCK, checks)
        if self.last is not None and now_us < self.last: return self._halt(Cause.CLOCK, checks)
        self.last = now_us
        if type(owner_alive) is not bool or not owner_alive: return self._halt(Cause.OWNER, checks)
        if type(checks) is not Checks or checks.fatal_reason() is not None: return self._halt(Cause.GUARD, checks)
        if self.end is not None and now_us >= self.end: return self._halt(Cause.DEADLINE, checks)
        return True

    def start(self, now_us, checks, *, owner_alive=True):
        if self.state != 'off' or not self.enabled: return False
        uint(now_us)
        if now_us + self.life.policy.max_elapsed_us + READY_TIMEOUT_US >= 2**64:
            raise ValueError('supervision140_clock_range')
        self.origin = self.last = now_us
        self.end = now_us + self.life.policy.max_elapsed_us
        self.ready_until = now_us + READY_TIMEOUT_US
        self.state = 'waiting_ready'
        if not self._record_or_stop(Event.START, checks): return False
        if not self._preflight(now_us, checks, owner_alive): return False
        if not self.life.policy.enabled: return self._halt(Cause.DISABLED, checks)
        if not checks.connected: return self._halt(Cause.GUARD, checks)
        self.start_attempted = True
        try: acknowledged = self.helper.start(self.ledger.job, (self.life.policy.max_elapsed_us + 999) // 1000)
        except Exception: acknowledged = False
        if acknowledged is not True: return self._halt(Cause.START, checks)
        return self._record_or_stop(Event.ACK, checks)

    def observe(self, now_us, checks, *, owner_alive=True):
        if self.state in ('off', 'stopped'): return False
        if not self._preflight(now_us, checks, owner_alive): return False
        if self.state == 'waiting_ready' and now_us >= self.ready_until:
            return self._halt(Cause.TIMEOUT, checks)
        try: report = self.helper.poll(now_us)
        except Exception: return self._halt(Cause.PROTOCOL, checks)
        if (type(report) is not Observation or any(type(getattr(report, k)) is not bool
                for k in ('running', 'create_ack', 'set_ack', 'ready_signal', 'mains'))):
            return self._halt(Cause.PROTOCOL, checks)
        if report.token != self.ledger.job: return self._halt(Cause.BINDING, checks)
        if (type(report.observed_us) is not int or not 0 <= report.observed_us <= now_us
                or self.helper_seen_at is not None and report.observed_us < self.helper_seen_at):
            return self._halt(Cause.PROTOCOL, checks)
        if now_us - report.observed_us > MAX_STATUS_AGE_US: return self._halt(Cause.STALE, checks)
        self.helper_seen_at = report.observed_us
        if not report.running: return self._halt(Cause.EXIT, checks)
        if not report.mains: return self._halt(Cause.POWER, checks)
        if report.ready_signal and not (report.create_ack and report.set_ack):
            return self._halt(Cause.PROTOCOL, checks)
        ready = report.ready_signal and report.create_ack and report.set_ack
        if self.state == 'waiting_ready':
            if not ready: return False
            if not self._record_or_stop(Event.READY, checks): return False
            if not self.life.start(now_us, checks): return self._halt(Cause.LIFECYCLE, checks)
            self.state = 'active'
            if not self._record_or_stop(Event.ACTIVE, checks): return False
        elif not ready:
            return self._halt(Cause.LOST, checks)
        if self.life.state is State.RECORDING and not checks.connected:
            self.life.interrupt(now_us, checks, reason=Reason.DISCONNECTED)
        if self.life.state is State.STOPPED: return self._halt(Cause.LIFECYCLE, checks)
        return True

    def _after(self, value, checks):
        if self.life.state is State.STOPPED: return self._halt(Cause.LIFECYCLE, checks)
        return value

    def record_context(self, start_us, finish_us, before, after, *, owner_before=True, owner_after=True, succeeded=True):
        if not self.observe(start_us, before, owner_alive=owner_before): return False
        if not self.observe(finish_us, after, owner_alive=owner_after): return False
        return self._after(self.life.record_context(start_us, finish_us, before, after, succeeded=succeeded), after)

    def begin_triple(self, now_us, checks, *, owner_alive=True):
        if not self.observe(now_us, checks, owner_alive=owner_alive): return False
        return self._after(self.life.begin_triple(now_us, checks), checks)

    def finish_triple(self, now_us, checks, *, owner_alive=True):
        if not self.observe(now_us, checks, owner_alive=owner_alive): return False
        return self._after(self.life.finish_triple(now_us, checks), checks)

    def retry(self, now_us, checks, *, owner_alive=True):
        if not self.observe(now_us, checks, owner_alive=owner_alive): return False
        return self._after(self.life.retry(now_us, checks), checks)

    def stop(self, now_us, checks):
        if self.state in ('off', 'stopped'): return False
        if not self._preflight(now_us, checks, True): return False
        return self._halt(Cause.CANCEL, checks)

    def snapshot(self):
        return dict(schema=SCHEMA + '_status', state=self.state, cause=self.cause.value,
                    life=self.life.snapshot(), helper_calls=dict(self.helper.calls),
                    helper_cleanup_attempted=self.cleanup_attempted, cancel_ack=self.cancel_ack, exit_ack=self.exit_ack,
                    cleanup_complete=not self.start_attempted or self.cancel_ack is True and self.exit_ack is True,
                    supervision_journal_poisoned=self.ledger.poisoned, invented_only=True,
                    native_helper_launch_available=False, actual_owner_death_tested=False,
                    power_request_release_proven=False, collection_dates=None, **DENIED)


def inspect_ledger(raw, lifecycle_segments=None):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_FRAME * MAX_FRAMES:
        raise ValueError('supervision140_size')
    lines = raw.split(b'\n'); tail = lines.pop()
    if not lines or len(lines) > MAX_FRAMES or len(tail) >= MAX_FRAME:
        raise ValueError('supervision140_frames')
    head, previous_event, job, last_time, committed = ZERO, None, None, 0, 0
    record = None
    stop_cause = None
    seen_at = None
    allowed = {None: {Event.START}, Event.START: {Event.ACK, Event.STOP},
               Event.ACK: {Event.READY, Event.STOP}, Event.READY: {Event.ACTIVE, Event.STOP},
               Event.ACTIVE: {Event.STOP}, Event.STOP: {Event.STOPPED}, Event.STOPPED: set()}
    for sequence, line in enumerate(lines, 1):
        if not 0 < len(line) < MAX_FRAME: raise ValueError('supervision140_frame_size')
        try: payload, sha = line.rsplit(b'\t', 1)
        except ValueError: raise ValueError('supervision140_frame') from None
        if hashlib.sha256(payload).hexdigest().encode() != sha: raise ValueError('supervision140_checksum')
        f = strict_json(payload, MAX_FRAME)
        keys = {'schema', 'job', 'sequence', 'previous', 'event', 'cause', 'at_us', 'life_head', 'life_committed',
                'life_pending', 'life_poisoned', 'helper_seen_at', 'cancel_ack', 'exit_ack'}
        if type(f) is not dict or set(f) != keys or canonical(f) != payload: raise ValueError('supervision140_fields')
        try: event, cause = Event(f['event']), Cause(f['cause'])
        except (ValueError, TypeError): raise ValueError('supervision140_event') from None
        for k in ('sequence', 'at_us', 'life_committed'): uint(f[k])
        if (f['schema'] != SCHEMA or type(f['job']) is not str or not re.fullmatch('[0-9a-f]{32}', f['job'])
                or job is not None and f['job'] != job or f['sequence'] != sequence or f['previous'] != head
                or f['at_us'] < last_time or f['life_committed'] < committed or event not in allowed[previous_event]
                or type(f['life_head']) is not str or not re.fullmatch('[0-9a-f]{64}', f['life_head'])
                or any(type(f[k]) is not bool for k in ('life_pending', 'life_poisoned'))
                or any(f[k] is not None and type(f[k]) is not bool for k in ('cancel_ack', 'exit_ack'))
                or f['helper_seen_at'] is not None and (type(f['helper_seen_at']) is not int or not 0 <= f['helper_seen_at'] <= f['at_us'])
                or event not in (Event.STOP, Event.STOPPED) and cause is not Cause.NONE
                or event in (Event.STOP, Event.STOPPED) and cause is Cause.NONE):
            raise ValueError('supervision140_transition')
        if (event is Event.START and (f['life_head'] != ZERO or f['life_committed'] != 0 or f['life_pending']
                                     or f['life_poisoned'] or f['helper_seen_at'] is not None)
                or event in (Event.READY, Event.ACTIVE) and f['helper_seen_at'] is None
                or f['helper_seen_at'] is not None and seen_at is not None and f['helper_seen_at'] < seen_at
                or event is not Event.STOPPED and (f['cancel_ack'] is not None or f['exit_ack'] is not None)
                or event is Event.STOPPED and (cause is not stop_cause or (f['cancel_ack'] is None) != (f['exit_ack'] is None))):
            raise ValueError('supervision140_ordering')
        if event is Event.STOP: stop_cause = cause
        if f['helper_seen_at'] is not None: seen_at = f['helper_seen_at']
        record, job, head, previous_event, last_time, committed = f, f['job'], sha.decode(), event, f['at_us'], f['life_committed']
    if tail and previous_event is Event.STOPPED: raise ValueError('supervision140_tail_after_stop')
    binding = None
    if lifecycle_segments is not None:
        if type(lifecycle_segments) is not list: raise ValueError('supervision140_binding')
        if not lifecycle_segments:
            binding = record['life_head'] == ZERO and committed == 0
        else:
            inspect_segments(lifecycle_segments)
            prefixes = {ZERO: 0}; last_head = ZERO
            for segment in lifecycle_segments:
                for line in segment.split(b'\n')[:-1]:
                    payload, sha = line.rsplit(b'\t', 1); f = strict_json(payload, MAX_FRAME)
                    if f['job'] != job: raise ValueError('supervision140_job_binding')
                    last_head = sha.decode(); prefixes[last_head] = f['committed_sequence']
            binding = prefixes.get(record['life_head']) == committed and (record['life_poisoned'] or record['life_head'] == last_head)
        if not binding: raise ValueError('supervision140_head_binding')
    return dict(schema=SCHEMA + '_inspection', frames=len(lines), stopped_record_present=previous_event is Event.STOPPED,
                cause=record['cause'], last_lifecycle_acknowledged_sequence=committed,
                trailing_partial_bytes=len(tail), lifecycle_acknowledged_prefix_bound=binding,
                cancel_ack=record['cancel_ack'], exit_ack=record['exit_ack'], resume_available=False,
                durability_ack_proven=False, native_supervision_certified=False, **DENIED)
