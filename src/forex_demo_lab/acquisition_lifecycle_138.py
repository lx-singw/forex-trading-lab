"""Pure invented-data acquisition decisions. No MT5, clocks, power or orders API."""
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import wraps

from .paired_replay_133 import DENIED
from .segment_journal_138 import Event, Reason, Journal, StorageFailure, TRIPLE_RESERVE, uint

SECOND_US = 1_000_000
HOUR_US = 3_600 * SECOND_US
MAX_JOB_US = 4 * HOUR_US
BACKOFF_US = (5 * SECOND_US, 30 * SECOND_US, 120 * SECOND_US)


class State(str, Enum):
    OFF = 'off'
    PREFLIGHT = 'preflight'
    RECORDING = 'recording'
    INTERRUPTED = 'interrupted'
    STOPPED = 'stopped'


class AccountMode(IntEnum):
    REAL = 0
    DEMO = 1
    CONTEST = 2


@dataclass(frozen=True)
class Checks:
    # Invented observations of actual-type checks, never server-name heuristics.
    actual_mode: AccountMode | None = None
    query_ok: bool = False
    identity_unchanged: bool = False
    connected: bool = False
    algo_enabled: bool = False
    non_tester: bool = False
    eurusd_visible: bool = False
    currency_usd: bool = False
    clock_safe: bool = False

    def fatal_reason(self):
        if any(type(getattr(self, name)) is not bool for name in self.__dataclass_fields__ if name != 'actual_mode'):
            return Reason.QUERY
        if not self.query_ok: return Reason.QUERY
        if type(self.actual_mode) is not AccountMode or self.actual_mode is not AccountMode.DEMO: return Reason.ACCOUNT
        if not self.identity_unchanged: return Reason.IDENTITY
        if self.algo_enabled: return Reason.ALGO
        if not self.non_tester or not self.eurusd_visible or not self.currency_usd: return Reason.SYMBOL
        if not self.clock_safe: return Reason.CLOCK
        return None


@dataclass(frozen=True)
class Policy:
    enabled: bool = False
    retry_enabled: bool = False
    max_elapsed_us: int = MAX_JOB_US

    def __post_init__(self):
        if (type(self.enabled) is not bool or type(self.retry_enabled) is not bool
                or type(self.max_elapsed_us) is not int or not 0 < self.max_elapsed_us <= MAX_JOB_US):
            raise ValueError('lifecycle138_policy')


def fail_closed(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except StorageFailure:
            self.journal.poison()
            self.state, self.reason, self.pending = State.STOPPED, Reason.STORAGE, None
            self.context_at = None
            return False
    return wrapped


class Lifecycle:
    def __init__(self, journal, policy=Policy()):
        if type(journal) is not Journal or type(policy) is not Policy:
            raise ValueError('lifecycle138_configuration')
        self.journal, self.policy = journal, policy
        self.state, self.reason = State.OFF, Reason.NONE
        self.origin = self.last = self.context_at = self.pending = self.last_begin = self.wait_until = None

    def _abort(self, reason):
        if self.pending is not None:
            self.journal.append(Event.ABORT, self.last, sequence=self.pending, reason=reason)
            self.pending = None

    def _stop(self, reason):
        if self.state is State.STOPPED:
            return False
        if self.state is not State.OFF:
            self._abort(reason)
            self.journal.append(Event.STOP, self.last, reason=reason)
            self.journal.close(self.last, reason)
        self.state, self.reason, self.context_at = State.STOPPED, reason, None
        return False

    def _safe(self, now_us, checks):
        try:
            uint(now_us)
        except ValueError:
            return self._stop(Reason.CLOCK)
        if type(checks) is not Checks:
            return self._stop(Reason.QUERY)
        if now_us < self.last:
            return self._stop(Reason.CLOCK)
        self.last = now_us
        # Unsafe identity/account/clock conditions never become reconnect retries.
        reason = checks.fatal_reason()
        if reason is not None:
            return self._stop(reason)
        if now_us - self.origin >= self.policy.max_elapsed_us:
            return self._stop(Reason.DEADLINE)
        return True

    def _wait(self):
        self.wait_until = self.last + BACKOFF_US[self.journal.attempt]
        uint(self.wait_until)
        self.journal.append(Event.WAIT, self.last, wait_until_us=self.wait_until)

    def _interrupt(self, reason):
        self._abort(reason)
        self.journal.append(Event.INTERRUPT, self.last, reason=reason)
        self.state, self.reason, self.context_at = State.INTERRUPTED, reason, None
        if not self.policy.retry_enabled:
            return self._stop(reason)
        if self.journal.attempt == len(BACKOFF_US):
            return self._stop(Reason.RETRIES)
        self._wait()
        return False

    def _connected(self, checks):
        return True if checks.connected else self._interrupt(Reason.DISCONNECTED)

    def _new_segment(self, reason):
        self.journal.close(self.last, reason)
        self.journal.open(self.last)
        self.state, self.context_at = State.PREFLIGHT, None
        self.journal.append(Event.READY, self.last)
        self.state, self.reason = State.RECORDING, Reason.NONE

    @fail_closed
    def start(self, now_us, checks):
        if self.state is not State.OFF or not self.policy.enabled:
            return False
        uint(now_us)
        if now_us + self.policy.max_elapsed_us + max(BACKOFF_US) >= 2**64:
            raise ValueError('lifecycle138_clock_range')
        self.origin = self.last = now_us
        self.journal.open(now_us)
        self.state = State.PREFLIGHT
        if not self._safe(now_us, checks) or not self._connected(checks):
            return False
        self.journal.append(Event.READY, now_us)
        self.state = State.RECORDING
        return True

    @fail_closed
    def record_context(self, start_us, finish_us, before, after, *, succeeded=True):
        if type(succeeded) is not bool:
            raise ValueError('lifecycle138_context_result')
        if self.state is not State.RECORDING:
            return False
        if not self._safe(start_us, before) or not self._connected(before):
            return False
        if self.pending is not None:
            raise ValueError('lifecycle138_pending_triple')
        if not self._safe(finish_us, after) or not self._connected(after):
            return False
        if not succeeded:
            return self._stop(Reason.CONTEXT)
        if not self.journal.room(1024):
            self._new_segment(Reason.ROTATE)
            return False  # Discard the pre-boundary observation; query new context later.
        self.journal.append(Event.CONTEXT, self.last)
        self.context_at = self.last
        return True

    def context_due(self, now_us):
        uint(now_us)
        return self.context_at is None or now_us - self.context_at >= HOUR_US

    @fail_closed
    def begin_triple(self, now_us, before):
        if self.state is not State.RECORDING:
            return False
        if not self._safe(now_us, before) or not self._connected(before):
            return False
        if self.pending is not None:
            raise ValueError('lifecycle138_pending_triple')
        if self.context_due(now_us) or self.last_begin is not None and now_us - self.last_begin < SECOND_US:
            return False
        if not self.journal.room(TRIPLE_RESERVE):
            self._new_segment(Reason.ROTATE)
            return False  # A new context must be captured after the boundary.
        sequence = self.journal.committed + 1
        self.journal.append(Event.BEGIN, now_us, sequence=sequence)
        self.pending, self.last_begin = sequence, now_us
        return True

    @fail_closed
    def finish_triple(self, now_us, after):
        if self.state is not State.RECORDING:
            return False
        if not self._safe(now_us, after) or not self._connected(after):
            return False
        if self.pending is None:
            return False
        self.journal.append(Event.COMMIT, now_us, sequence=self.pending)
        self.pending = None
        return True

    @fail_closed
    def interrupt(self, now_us, checks, *, reason=Reason.SLEEP):
        if type(reason) is not Reason or reason not in (Reason.SLEEP, Reason.DISCONNECTED):
            raise ValueError('lifecycle138_interrupt_reason')
        if self.state not in (State.PREFLIGHT, State.RECORDING):
            return False
        if not self._safe(now_us, checks):
            return False
        return self._interrupt(reason)

    @fail_closed
    def retry(self, now_us, checks):
        if self.state is not State.INTERRUPTED:
            return False
        if not self._safe(now_us, checks):
            return False
        if now_us < self.wait_until:
            return False
        self.journal.append(Event.RETRY, now_us, attempt=self.journal.attempt + 1)
        if checks.connected:
            self._new_segment(Reason.RECONNECT)
            return True
        if self.journal.attempt == len(BACKOFF_US):
            return self._stop(Reason.RETRIES)
        self._wait()
        return False

    @fail_closed
    def stop(self, now_us, checks):
        if self.state in (State.OFF, State.STOPPED):
            return self._stop(Reason.CANCEL)
        if not self._safe(now_us, checks):
            return False
        return self._stop(Reason.CANCEL)

    def snapshot(self):
        return dict(schema='invented_lifecycle138_status_v1', state=self.state.value,
                    reason=self.reason.value, segments=self.journal.segment,
                    acknowledged_committed_sequence=self.journal.committed,
                    pending_triple=self.pending is not None, retry_attempts=self.journal.attempt,
                    wait_until_us=self.wait_until, journal_poisoned=self.journal.poisoned,
                    reserved_bytes=self.journal.reserved_job, invented_only=True,
                    native_acquisition_available=False, keep_awake_API_used=False,
                    market_data_ingestion_available=False, **DENIED)
