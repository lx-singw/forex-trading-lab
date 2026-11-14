"""Offline readiness probes and sealed regular-file comparison; no native IO.

File availability and frame envelopes cannot prove an open stream's end. The
regular-file branch needs independently verified, continuously held exclusion
of writers/deletion and trusted sandbox/owner/no-reparse evidence. Its injected
proofs are not a Windows or MQL implementation.
"""
from dataclasses import dataclass, field

from .capture_budget_047 import require_guard
from .transport_lifecycle_060 import OfflineLifecycle, Observation, native_error
from .windows_pipe_047 import PipeRejected

MAX_PROBES = 901


def sharing_compatible(existing_access, existing_share, new_access, new_share):
    """Injected Win32 contract model: bit1read/2write/4delete; no OS call."""
    masks = (existing_access,existing_share,new_access,new_share)
    if any(type(x) is not int or not 0 <= x <= 7 for x in masks):
        return False
    return (existing_access & ~new_share)==0 and (new_access & ~existing_share)==0


def readiness_decision(size, error, attempt, elapsed_us):
    """Closed pure decisions:0wait,1read candidate,2error,3extra,4schema,
    5session expired,6probe budget. Read candidate is not boundary proof.
    """
    if (any(type(x) is not int for x in (size,error,attempt,elapsed_us)) or
            size < 0 or error < 0 or error > 2147483647 or attempt < 1 or elapsed_us < 0):
        return 4
    if error != 0: return 2
    if elapsed_us >= 900000000: return 5
    if attempt > MAX_PROBES: return 6
    if size > 84: return 3
    return 1 if size == 84 else 0


@dataclass(frozen=True)
class Availability:
    size: int
    error: int = 0


@dataclass(frozen=True)
class Read:
    data: bytes
    count: int
    error: int = 0


@dataclass(frozen=True)
class Snapshot:
    # Opaque identity remains private; never serialized into diagnostics.
    identity: bytes = field(repr=False)
    kind: str = 'regular'
    size: int = 84
    position: int = 0
    writers_excluded: bool = False
    deletion_excluded: bool = False
    sandbox_verified: bool = False
    owner_verified: bool = False
    reparse_rejected: bool = False


def boundary_snapshot(value, position):
    if (type(value) is not Snapshot or type(value.identity) is not bytes or
            len(value.identity) != 16 or value.kind != 'regular' or
            type(value.size) is not int or value.size != 84 or
            type(value.position) is not int or value.position != position or
            any(type(getattr(value,k)) is not bool or getattr(value,k) is not True
                for k in ('writers_excluded','deletion_excluded','sandbox_verified',
                          'owner_verified','reparse_rejected'))):
        raise PipeRejected('snapshot_boundary_unproven')
    return value


class ReadinessAdapter061:
    """A finite injected observation sequence, with one consumption attempt.

    Pipe: original85-byte diagnostic read; always boundaryFalse, no accepted
    receipt. Regular: exact84 only under held immutable-file proof, then verify
    same handle identity/size/position after read and guard. Caller retains lock
    through the060 receipt/ACK/cleanup lifecycle. Every call must return before
    the deadline can be checked; no blocking-call timeout guarantee.
    """
    def __init__(self, mode, api, policy, clock, guard):
        if mode not in ('pipe','regular') or type(mode) is not str:
            raise PipeRejected('adapter_mode_rejected')
        self.mode, self.api, self.guard = mode, api, guard
        self.timer = OfflineLifecycle(policy, clock, guard)
        self.attempts = 0
        self.consumed = False
        self.failed = False
        self.events = []

    def call(self, stage, function, *args):
        start = self.timer.sample()[1]
        try:
            value = function(*args)
        except Exception:
            raise PipeRejected('adapter_operation_failed_details_redacted') from None
        now = self.timer.sample()[1]
        code = getattr(value, 'error', 0)
        self.events.append(dict(stage=stage,elapsed_us=(now-start)//1000,
                                error_category=native_error(code)))
        return value

    def availability(self, stage):
        value = self.call(stage, self.api.availability)
        if type(value) is not Availability:
            raise PipeRejected('availability_schema_rejected')
        now = self.timer.sample()
        elapsed = (now[1]-self.timer.first[1])//1000
        decision = readiness_decision(value.size,value.error,self.attempts,elapsed)
        reasons = {2:'availability_error',3:'extra_bytes_observed',4:'availability_schema_rejected',
                   5:'session_expired',6:'probe_budget_exhausted'}
        if decision in reasons: raise PipeRejected(reasons[decision])
        return decision

    def observe(self):
        if self.consumed or self.failed: raise PipeRejected('consumption_unavailable')
        try:
            return self._observe()
        except Exception:
            self.failed = True
            raise

    def _observe(self):
        self.attempts += 1
        if self.attempts > MAX_PROBES: raise PipeRejected('probe_budget_exhausted')
        require_guard(self.guard); self.timer.sample()
        if self.availability('availability_before') == 0:
            return Observation('pending')
        # Recheck after full guard latency; a size snapshot can become stale.
        require_guard(self.guard); self.timer.sample()
        if self.availability('availability_after_guard') != 1:
            raise PipeRejected('readiness_changed')
        before = None
        if self.mode == 'regular':
            before = boundary_snapshot(self.call('snapshot_before', self.api.snapshot),0)
        # Burn the consumption attempt BEFORE calling the reader; never retry.
        self.consumed = True
        requested = 85 if self.mode == 'pipe' else 84
        value = self.call('read', self.api.read, requested)
        if (type(value) is not Read or type(value.data) is not bytes or
                type(value.count) is not int or value.count != len(value.data)):
            raise PipeRejected('read_schema_rejected')
        if native_error(value.error) != 0: raise PipeRejected('read_error')
        if value.count != 84: raise PipeRejected('read_length_rejected')
        require_guard(self.guard); self.timer.sample()
        if self.mode == 'pipe':
            return Observation('ready',value.data,False)
        after = boundary_snapshot(self.call('snapshot_after',self.api.snapshot),84)
        if before.identity != after.identity:
            raise PipeRejected('snapshot_identity_changed')
        return Observation('ready',value.data,True)

    def report(self):
        return dict(version='readiness_adapter_061_v1',mode=self.mode,
                    attempts=self.attempts,consumption_attempted=self.consumed,
                    events=list(self.events),native_adapter_ready=False,
                    quote_reads=0,orders=0)
