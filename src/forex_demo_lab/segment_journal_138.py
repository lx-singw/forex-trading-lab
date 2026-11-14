"""Bounded journal for invented acquisition events. No quote or account payloads."""
from enum import Enum
import hashlib
import os
from pathlib import Path
import re

from .paired_replay_133 import DENIED, canonical, strict_json

MAX_FRAME = 1024
CONTROL_RESERVE = 16 * MAX_FRAME
TRIPLE_RESERVE = 2 * MAX_FRAME
MAX_FILE = 32 * 1024 * 1024
MAX_JOB = 128 * 1024 * 1024
MAX_SEGMENTS = 64
ZERO = '0' * 64
SCHEMA = 'invented_acquisition138_v1'


class Event(str, Enum):
    OPEN = 'open'
    READY = 'ready'
    CONTEXT = 'context'
    BEGIN = 'triple_begin'
    COMMIT = 'triple_commit'
    ABORT = 'triple_abort'
    INTERRUPT = 'interrupted'
    WAIT = 'wait'
    RETRY = 'retry'
    STOP = 'stopped'
    CLOSE = 'closed'


class Reason(str, Enum):
    NONE = 'none'
    DISCONNECTED = 'disconnected'
    SLEEP = 'sleep'
    QUERY = 'guard_query_failed'
    ACCOUNT = 'not_actual_demo'
    IDENTITY = 'identity_changed'
    ALGO = 'algo_enabled'
    SYMBOL = 'symbol_or_currency'
    CLOCK = 'unsafe_clock'
    DEADLINE = 'job_deadline'
    STORAGE = 'storage_failed'
    RETRIES = 'retry_budget'
    CANCEL = 'cancelled'
    ROTATE = 'clean_rotation'
    RECONNECT = 'reconnect_boundary'
    CONTEXT = 'context_failed'


class StorageFailure(Exception):
    """A poisoned journal can never write, rotate or retry again."""


def uint(value):
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError('journal138_integer')
    return value


class DiskStore:
    """Exclusive new directory/files. Never reopens an existing job to append."""
    def __init__(self, root, job_id):
        root = Path(root).absolute()
        for parent in (root, *root.parents):
            if parent.is_symlink():
                raise StorageFailure('storage138_root')
        if not root.is_dir() or not re.fullmatch('[0-9a-f]{32}', job_id):
            raise StorageFailure('storage138_root')
        self.folder = root / ('InventedJob138-' + job_id)
        try:
            self.folder.mkdir()
        except OSError:
            raise StorageFailure('storage138_collision') from None

    def open(self, segment):
        try:
            return (self.folder / f'Segment{segment:04d}.journal').open('xb')
        except OSError:
            raise StorageFailure('storage138_open') from None

    @staticmethod
    def sync(stream):
        stream.flush()
        os.fsync(stream.fileno())


class Journal:
    """Write acknowledgements update counters only after full write and fsync."""
    def __init__(self, job_id, store_factory, file_limit=MAX_FILE, job_limit=MAX_JOB):
        if (type(job_id) is not str or not re.fullmatch('[0-9a-f]{32}', job_id)
                or type(file_limit) is not int or not CONTROL_RESERVE + 4 * MAX_FRAME <= file_limit <= MAX_FILE
                or type(job_limit) is not int or not file_limit <= job_limit <= MAX_JOB):
            raise ValueError('journal138_configuration')
        self.job_id, self.factory = job_id, store_factory
        self.file_limit, self.job_limit = file_limit, job_limit
        self.store = self.stream = None
        self.head, self.frame, self.segment = ZERO, 0, 0
        self.reserved_job = self.reserved_file = 0
        self.committed = self.attempt = 0
        self.poisoned = False

    def poison(self):
        self.poisoned = True
        if self.stream is not None:
            try:
                self.stream.close()
            except OSError:
                pass
            self.stream = None

    def open(self, at_us):
        if self.poisoned or self.stream is not None or self.segment >= MAX_SEGMENTS:
            raise StorageFailure('storage138_state')
        try:
            if self.store is None:
                self.store = self.factory(self.job_id)
            self.stream = self.store.open(self.segment + 1)
            self.segment += 1
            self.reserved_file = 0
            self.append(Event.OPEN, at_us)
        except (OSError, StorageFailure):
            self.poison(); raise StorageFailure('storage138_open') from None

    def room(self, amount):
        uint(amount)
        return (not self.poisoned and self.stream is not None
                and self.reserved_file + amount + CONTROL_RESERVE <= self.file_limit
                and self.reserved_job + amount + CONTROL_RESERVE <= self.job_limit)

    def append(self, event, at_us, *, reason=Reason.NONE, sequence=0, wait_until_us=0, attempt=None):
        if self.poisoned or self.stream is None:
            raise StorageFailure('storage138_state')
        if type(event) is not Event or type(reason) is not Reason:
            raise ValueError('journal138_enum')
        uint(at_us); uint(sequence); uint(wait_until_us)
        next_attempt = self.attempt if attempt is None else uint(attempt)
        if next_attempt > 3:
            raise ValueError('journal138_attempt')
        committed = sequence if event is Event.COMMIT else self.committed
        payload = canonical(dict(schema=SCHEMA, job=self.job_id, segment=self.segment,
                                 frame=self.frame + 1, previous=self.head, event=event.value,
                                 at_us=at_us, sequence=sequence, committed_sequence=committed,
                                 reason=reason.value, wait_until_us=wait_until_us, attempt=next_attempt))
        checksum = hashlib.sha256(payload).hexdigest()
        line = payload + b'\t' + checksum.encode('ascii') + b'\n'
        control = event in (Event.ABORT, Event.INTERRUPT, Event.WAIT, Event.RETRY, Event.STOP, Event.CLOSE)
        if (len(line) > MAX_FRAME or not control and not self.room(len(line))
                or self.reserved_file + len(line) > self.file_limit
                or self.reserved_job + len(line) > self.job_limit):
            self.poison(); raise StorageFailure('storage138_budget')
        # Reserve before IO. A failed/short write never refunds or retries bytes.
        self.reserved_file += len(line); self.reserved_job += len(line)
        try:
            if self.stream.write(line) != len(line):
                raise OSError('short_write')
            self.store.sync(self.stream)
        except OSError:
            self.poison(); raise StorageFailure('storage138_write') from None
        self.head, self.frame, self.committed, self.attempt = checksum, self.frame + 1, committed, next_attempt

    def close(self, at_us, reason):
        self.append(Event.CLOSE, at_us, reason=reason)
        try:
            self.stream.close()
            self.stream = None
        except OSError:
            self.poison(); raise StorageFailure('storage138_close') from None


def inspect_segments(segments):
    """Inspect closed invented journals. Even a valid prefix is never resumable."""
    if (type(segments) is not list or not 1 <= len(segments) <= MAX_SEGMENTS
            or any(type(raw) is not bytes or not 0 < len(raw) <= MAX_FILE for raw in segments)
            or sum(map(len, segments)) > MAX_JOB):
        raise ValueError('journal138_inputs')
    head, job, frames, committed, pending = ZERO, None, 0, 0, None
    state, prior_close, last_time, attempt, deadline = None, None, 0, 0, None
    context = False
    stop_reason = None
    tail_bytes = 0
    for index, raw in enumerate(segments, 1):
        if index > 1 and prior_close not in (Reason.ROTATE, Reason.RECONNECT):
            raise ValueError('journal138_segment_boundary')
        lines = raw.split(b'\n'); tail = lines.pop()
        if tail and (index != len(segments) or len(tail) >= MAX_FRAME):
            raise ValueError('journal138_partial_segment')
        tail_bytes = len(tail)
        prior_close = None
        for line_index, line in enumerate(lines):
            if not 0 < len(line) < MAX_FRAME:
                raise ValueError('journal138_frame_size')
            try:
                payload, checksum = line.rsplit(b'\t', 1)
            except ValueError:
                raise ValueError('journal138_frame') from None
            if hashlib.sha256(payload).hexdigest().encode('ascii') != checksum:
                raise ValueError('journal138_digest')
            f = strict_json(payload, MAX_FRAME)
            fields = {'schema', 'job', 'segment', 'frame', 'previous', 'event', 'at_us', 'sequence',
                      'committed_sequence', 'reason', 'wait_until_us', 'attempt'}
            if type(f) is not dict or set(f) != fields or canonical(f) != payload:
                raise ValueError('journal138_fields')
            try:
                event, reason = Event(f['event']), Reason(f['reason'])
                for key in ('segment', 'frame', 'at_us', 'sequence', 'committed_sequence', 'wait_until_us', 'attempt'):
                    uint(f[key])
            except (ValueError, TypeError):
                raise ValueError('journal138_values') from None
            if (f['schema'] != SCHEMA or type(f['job']) is not str or not re.fullmatch('[0-9a-f]{32}', f['job'])
                    or job is not None and f['job'] != job or f['previous'] != head
                    or f['segment'] != index or f['frame'] != frames + 1 or f['at_us'] < last_time
                    or f['attempt'] != attempt + int(event is Event.RETRY) or f['attempt'] > 3
                    or line_index == 0 and event is not Event.OPEN
                    or line_index > 0 and (event is Event.OPEN or prior_close is not None)):
                raise ValueError('journal138_chain')
            if event in (Event.OPEN, Event.READY, Event.CONTEXT, Event.BEGIN, Event.COMMIT, Event.WAIT, Event.RETRY) and reason is not Reason.NONE:
                raise ValueError('journal138_reason')
            if event is Event.OPEN:
                state, context, stop_reason = 'preflight', False, None
            elif event is Event.READY:
                if state != 'preflight': raise ValueError('journal138_ready')
                state = 'recording'
            elif event is Event.CONTEXT:
                if state != 'recording' or pending is not None: raise ValueError('journal138_context')
                context = True
            elif event is Event.BEGIN:
                if state != 'recording' or not context or pending is not None or f['sequence'] != committed + 1:
                    raise ValueError('journal138_begin')
                pending = f['sequence']
            elif event in (Event.COMMIT, Event.ABORT):
                if state != 'recording' or pending is None or f['sequence'] != pending:
                    raise ValueError('journal138_pending')
                if event is Event.COMMIT: committed = pending
                pending = None
            elif event is Event.INTERRUPT:
                if state not in ('preflight', 'recording') or pending is not None or reason not in (Reason.DISCONNECTED, Reason.SLEEP):
                    raise ValueError('journal138_interrupt')
                state, context, deadline = 'interrupted', False, None
            elif event is Event.WAIT:
                if state != 'interrupted' or deadline is not None or attempt >= 3 or f['wait_until_us'] != f['at_us'] + (5, 30, 120)[attempt] * 1_000_000:
                    raise ValueError('journal138_wait')
                deadline = f['wait_until_us']
            elif event is Event.RETRY:
                if state != 'interrupted' or deadline is None or f['at_us'] < deadline:
                    raise ValueError('journal138_retry')
                deadline = None
            elif event is Event.STOP:
                if pending is not None or state == 'stopped' or reason in (Reason.NONE, Reason.ROTATE, Reason.RECONNECT):
                    raise ValueError('journal138_stop')
                state, stop_reason = 'stopped', reason
            elif event is Event.CLOSE:
                if pending is not None or not (state == 'stopped' and reason is stop_reason or state == 'recording' and reason is Reason.ROTATE
                                               or state == 'interrupted' and reason is Reason.RECONNECT and deadline is None):
                    raise ValueError('journal138_close')
                prior_close = reason
            if (f['committed_sequence'] != committed
                    or event not in (Event.BEGIN, Event.COMMIT, Event.ABORT) and f['sequence'] != 0
                    or event is not Event.WAIT and f['wait_until_us'] != 0):
                raise ValueError('journal138_progress')
            job, head, frames, last_time, attempt = f['job'], checksum.decode('ascii'), frames + 1, f['at_us'], f['attempt']
        if not lines:
            raise ValueError('journal138_empty_segment')
        if tail and prior_close is not None:
            raise ValueError('journal138_tail_after_close')
    return dict(schema=SCHEMA + '_inspection', valid_frames=frames, segment_count=len(segments),
                committed_sequence_present=committed, pending_triple=pending is not None,
                trailing_partial_bytes=tail_bytes, final_close_present=prior_close is not None,
                stopped_record_present=state == 'stopped', retry_attempts=attempt,
                head_sha256=head, durability_ack_proven=False,
                resume_available=False, cross_job_identity_established=False, invented_only=True, **DENIED)
