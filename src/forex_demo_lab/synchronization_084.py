"""Source/typed injected transport preparation. No native backend or authority.

Concrete Win32 access/share/creation and descriptor facts are checked here, but
their acquisition is injected. They are not evidence of actual Windows ACLs.
Native blocking calls cannot be interrupted by these after-return time checks.
"""
from dataclasses import dataclass, field
import ast
import hashlib
import json
from pathlib import PureWindowsPath
from typing import Protocol

from .synchronization_083 import (WIRE, MAX_BOOT, Guard083, Meter083,
    window_reason083, control_reason083, integer, digest, require, same_record)
from .sharing_probe_062 import ProbeRejected
from .clock_observer_042 import unique_pairs

PHASE = '84000000000000000000000000000001'
DATE = '2026-10-08'
MAGIC = b'FXDL084S'
KINDS = {'ready': 1, 'release': 2, 'holding': 3, 'closed': 4, 'pending': 5}
MQL_INPUTS = ('mt5/Scripts/ForexDemoSynchronization084.mq5',
    'mt5/Scripts/SynchronizationWire084.mqh', 'mt5/Scripts/Synchronization083.mqh',
    'mt5/Scripts/ClockGuard042.mqh')
CAPS = dict(io=512, opens=160, closes=160, writes=64, reads=128,
    metadata=256, exchanges=64, waits=64, wait_operations=64, cleanup=1)
GUARD_CAP = 256  # Additional concrete metadata IO; not an increased time limit.
READ, WRITE, DELETE, META = 0x80000000, 0x40000000, 0x10000, 0x20080
SHARE_ALL, OPEN_EXISTING, CREATE_NEW, NO_REPARSE = 7, 3, 1, 0x200000
PREFIX = 'FXDL_SYNC084 '
DATA084 = bytes((17*i+29) % 256 for i in range(84))


@dataclass(frozen=True)
class Peer084:
    process_id: int = field(repr=False)
    created: int = field(repr=False)
    session: int = field(repr=False)
    logon: bytes = field(repr=False)
    boot: bytes = field(repr=False)
    def __post_init__(self):
        for v in (self.process_id, self.created, self.session): integer(v)
        require(self.process_id > 0 and self.created > 0)
        for v in (self.logon, self.boot): require(type(v) is bytes and 8 <= len(v) <= 256)


@dataclass(frozen=True)
class Bindings084:
    source_sha256: str
    candidate_artifact_sha256: str
    policy_sha256: str
    episode: bytes = field(repr=False)
    file_identity: tuple = field(repr=False)
    owner_sid: bytes = field(repr=False)
    root: str = field(repr=False)
    peer: Peer084 = field(repr=False)

    def __post_init__(self):
        try:
            for v in (self.source_sha256, self.candidate_artifact_sha256, self.policy_sha256): digest(v)
            require(type(self.episode) is bytes and len(self.episode) == 16 and any(self.episode))
            require(type(self.file_identity) is tuple and len(self.file_identity) == 3)
            for v in self.file_identity: integer(v)
            require(self.file_identity[0] > 0 and self.file_identity[1:] != (0, 0))
            require(type(self.owner_sid) is bytes and 8 <= len(self.owner_sid) <= 256)
            require(type(self.peer) is Peer084)
            require(type(self.root) is str and len(self.root) < 220)
            p = PureWindowsPath(self.root)
            require(p.is_absolute() and len(p.drive) == 2 and p.drive[1] == ':')
            require('..' not in p.parts and p.name == 'ForexDemoSynchronization084-' + PHASE + '-' + self.episode.hex())
        except Exception: raise ProbeRejected('sync084_bindings_rejected') from None


def encode084(kind, seq, b, issued, deadline, start=0, end=0):
    require(type(b) is Bindings084 and kind in KINDS)
    integer(seq, 1, 64)
    for v in (issued, deadline, start, end): integer(v)
    return WIRE.pack(MAGIC, bytes.fromhex(PHASE), bytes.fromhex(b.source_sha256),
        bytes.fromhex(b.candidate_artifact_sha256), b.episode, seq, KINDS[kind], issued, deadline, start, end)


def decode084(raw, kind, seq, b, now, deadline, release=0, request_completed=None, request=False):
    """Never retimestamp, repair, normalize, or relabel peer-produced bytes."""
    try:
        require(type(b) is Bindings084 and kind in KINDS and type(request) is bool)
        integer(seq, 1, 64)
        for v in (now, deadline, release): integer(v)
        require(type(raw) is bytes and len(raw) == 144 and raw[109:112] == b'\0' * 3)
        magic, phase, source, artifact, episode, s, k, issued, expiry, start, end = WIRE.unpack(raw)
        require((magic, phase, source, artifact, episode, s) == (MAGIC, bytes.fromhex(PHASE),
            bytes.fromhex(b.source_sha256), bytes.fromhex(b.candidate_artifact_sha256), b.episode, seq))
        require(k == KINDS[kind] or not request and k == 5 and kind in ('holding', 'closed'))
        require(not request or k in (1,2,3,4))
        require(window_reason083(1 if request or k == 5 else k, issued, expiry, start, end, now, deadline, release) == 0)
        if request_completed is not None:
            integer(request_completed)
            require(request_completed <= issued <= now)
        return Signal084(k, seq, issued, expiry, start, end, raw)
    except Exception: raise ProbeRejected('sync084_frame_rejected') from None


@dataclass(frozen=True)
class Signal084:
    kind: int
    sequence: int
    issued: int
    deadline: int
    hold_start: int
    hold_end: int
    raw: bytes = field(repr=False)


@dataclass(frozen=True)
class Ace084:
    type: int
    flags: int
    mask: int
    sid: bytes = field(repr=False)


@dataclass(frozen=True)
class Security084:
    owner: bytes = field(repr=False)
    control: int
    aces: tuple = field(repr=False)


@dataclass(frozen=True)
class Spec084:
    role: str
    path: str = field(repr=False)
    access: int
    share: int
    creation: int
    flags: int = NO_REPARSE


@dataclass(frozen=True)
class Ancestor084:
    final_path: str = field(repr=False)
    attributes: int
    identity: tuple = field(repr=False)


@dataclass(frozen=True)
class Metadata084:
    identity: tuple = field(repr=False)
    final_path: str = field(repr=False)
    attributes: int
    links: int
    size: int
    position: int
    security: Security084 = field(repr=False)
    ancestors: tuple = field(repr=False, default=())


@dataclass(frozen=True)
class Open084:
    handle: object = field(repr=False)
    error: int


@dataclass(frozen=True)
class Transfer084:
    raw: bytes = field(repr=False)
    request_completed: int
    response_received: int
    pipe_security: Security084 = field(repr=False)
    pipe_client: Peer084 = field(repr=False)
    pipe_type: int
    pipe_read_mode: int
    request_bytes_written: int
    response_buffer_bytes: int
    response_bytes_read: int
    response_error: int
    # No synthetic reader/seal may be owned by the companion during controls.


@dataclass(frozen=True)
class Setup084:
    root_handle: object = field(repr=False)
    root_created_new: bool
    ancestors: tuple = field(repr=False)
    synthetic_bytes: bytes = field(repr=False)


@dataclass(frozen=True)
class Probe084:
    stage: str
    access: str
    start: int
    end: int
    guard_end: int
    error: int
    opened: bool
    closed: bool
    companion_blockers: int


class Backend084(Protocol):
    """Future adapter obligations; this module provides no native implementation.

    open MUST register each returned handle with owner.register before any
    after-acquisition operation can raise. Factory MUST owner.install before IO.
    transfer is one exact message exchange on a private user-only pipe with a
    verified client process; it returns the original peer bytes. request_completed
    is sampled on completing the pipe write, not after the response arrives.
    Metadata handles share READ|WRITE|DELETE. No helper synthetic-file seal.
    """
    model_only: bool
    def bootstrap(self, b: Bindings084, owner: 'Owner084') -> Setup084: ...
    def open(self, spec: Spec084, owner: 'Owner084') -> Open084: ...
    def metadata(self, handle: object) -> Metadata084: ...
    def write(self, handle: object, raw: bytes) -> int: ...
    def read(self, handle: object, count: int) -> bytes: ...
    def close(self, handle: object) -> bool: ...
    def transfer(self, request: bytes) -> Transfer084: ...
    def release(self, raw: bytes) -> int: ...
    def wait(self, milliseconds: int) -> None: ...
    def finish(self) -> bool: ...


class Owner084:
    def __init__(self):
        self.backend = None; self.live = {}; self.finished = False
        self.unconfirmed = 0; self.close_attempts = 0
    def install(self, backend):
        require(self.backend is None and getattr(backend, 'model_only', None) is True)
        self.backend = backend
        return backend
    def register(self, handle, spec):
        require(not self.finished and self.backend is not None and handle is not None and type(spec) is Spec084)
        require(handle not in self.live)
        self.live[handle] = spec
    def close(self, handle):
        require(handle in self.live and self.close_attempts < CAPS['closes'])
        # An uncertain close must not be retried: numeric handles can be reused.
        self.close_attempts += 1
        self.live.pop(handle)
        try: ok = self.backend.close(handle) is True
        except (Exception, KeyboardInterrupt): ok = False
        if not ok: self.unconfirmed += 1
        return ok
    def finish(self):
        require(not self.finished)
        for h in list(self.live):
            try: self.close(h)
            except (Exception, KeyboardInterrupt): self.unconfirmed += 1; self.live.pop(h, None)
        self.finished = True
        try: released = self.backend is None or self.backend.finish() is True
        except (Exception, KeyboardInterrupt): released = False
        return not self.live and self.unconfirmed == 0 and released


def check_security084(sec, owner):
    require(type(sec) is Security084 and type(sec.owner) is bytes and sec.owner == owner)
    integer(sec.control, 0, 65535)
    require(sec.control & 0x1004 == 0x1004 and type(sec.aces) is tuple and len(sec.aces) == 1)
    ace = sec.aces[0]
    require(type(ace) is Ace084 and type(ace.sid) is bytes and ace.sid == owner)
    for v in (ace.type, ace.flags, ace.mask): integer(v)
    require(ace.type == 0 and ace.flags in (0, 3) and ace.mask == 0x1f01ff)


def check_metadata084(m, spec, b, size, position, identity=None):
    try:
        require(type(m) is Metadata084 and type(spec) is Spec084 and type(b) is Bindings084)
        for v in (m.attributes, m.links, m.size): integer(v)
        integer(m.position, -1)
        require(type(m.identity) is tuple and len(m.identity) == 3)
        for v in m.identity: integer(v)
        require(m.identity[0] > 0 and m.identity[1:] != (0, 0))
        require(identity is None or m.identity == identity)
        require(type(m.final_path) is str and m.final_path.casefold() == spec.path.casefold())
        directory = spec.role == 'root'
        require(spec.path == b.root if directory else PureWindowsPath(spec.path).parent == PureWindowsPath(b.root))
        require(m.attributes & 0x400 == 0 and bool(m.attributes & 0x10) == directory and
            m.links == 1 and (m.size, m.position) == (size, position))
        expected = tuple(str(p) for p in PureWindowsPath(spec.path).parents)
        require(type(m.ancestors) is tuple and len(m.ancestors) == len(expected) <= 16)
        for a, path in zip(m.ancestors, expected):
            require(type(a) is Ancestor084 and type(a.final_path) is str and a.final_path.casefold() == path.casefold())
            integer(a.attributes)
            require(a.attributes & 0x400 == 0 and a.attributes & 0x10 != 0)
            require(type(a.identity) is tuple and len(a.identity) == 3)
            for v in a.identity: integer(v)
            require(a.identity[0] > 0 and a.identity[1:] != (0,0))
        check_security084(m.security, b.owner_sid)
        return m.identity
    except Exception: raise ProbeRejected('sync084_metadata_rejected') from None


class Lease084:
    """Held READ/share-READ response handle, rechecked after full trailing guard."""
    def __init__(self, client, h, spec, identity, raw, signal, kind, request_completed):
        self.client, self.h, self.spec, self.identity = client, h, spec, identity
        self.raw, self.signal, self.closed = raw, signal, False
        self.kind, self.request_completed = kind, request_completed
    def snapshot(self):
        try:
            require(not self.closed and self.h in self.client.owner.live)
            self.client.stamp(self.h, self.spec, 144, 144, self.identity)
            # A separate metadata/share-all pathname handle proves same path identity.
            self.client.path_stamp(self.spec.path, 144, self.identity)
            self.client.path_stamp(self.client.b.root + '\\synthetic.bin', 84, self.client.b.file_identity)
            decode084(self.raw, self.kind, self.signal.sequence, self.client.b, self.client.m.check()[2],
                self.client.deadline, self.client.release_time, self.request_completed)
            return self.raw
        except (Exception, KeyboardInterrupt): self.client.stopped = True; raise
    def close(self):
        require(not self.closed)
        self.closed = True
        return self.client.close(self.h)


class Meter084(Meter083):
    def consume(self, key):
        self.check()
        cap = GUARD_CAP if key == 'guards' else 0
        require(key == 'guards' and self.counts[key] < cap)
        self.counts[key] += 1


class Companion084:
    """Once-owned private injected companion. No default native factory.

    The existing083 whole-model clock remains 120s/Oct8 with full guards. Each
    challenge has its own immutable CREATE_NEW signal slot; no overwrite/rename
    or file deletion occurs. Cleanup closes handles even after clocks latch.
    """
    def __init__(self, b, clock, guard, factory):
        require(type(b) is Bindings084)
        self.b, self.clock, self.guard, self.factory = b, clock, guard, factory
        self.owner = Owner084(); self.m = None; self.used = False
        self.counts = dict.fromkeys(CAPS, 0); self.trace = []; self.probes = []
        self.sequence = 0; self.release_time = 0; self.release_spent = False
        self.hold_start = 0; self.hold_end = 0; self.deadline = 0
        self.ready = False; self.leases = []; self.frames = []; self.cleanup_ok = None
        self.stopped = False
        self.root_identity = None
    def bump(self, key):
        require(not self.stopped and key in CAPS and self.counts[key] < CAPS[key])
        self.counts[key] += 1
    def guard_now(self):
        self.m.consume('guards'); start = self.m.check()[2]
        proof = self.guard()
        end = self.m.check()[2]
        self.trace.append(('guard', start, end))
        require(same_record(proof, Guard083()))
        return end
    def call(self, key, fn):
        try:
            self.bump(key); self.bump('io'); self.guard_now()
            start = self.m.check()[2]; result = fn(); end = self.m.check()[2]
            after = self.guard_now(); self.trace.append((key, start, end))
            return result, start, end, after
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise
    def start(self, enabled=False):
        require(type(enabled) is bool and not self.used)
        self.used = True
        if not enabled: return False
        self.m = Meter084(self.clock)
        try:
            self.guard_now()
            backend = self.factory(self.owner)
            require(backend is self.owner.backend and getattr(backend, 'model_only', None) is True)
            self.guard_now()
            setup, _, _, _ = self.call('metadata', lambda: backend.bootstrap(self.b, self.owner))
            require(type(setup) is Setup084 and setup.root_created_new is True and
                type(setup.synthetic_bytes) is bytes and setup.synthetic_bytes == DATA084)
            root_spec = Spec084('root', self.b.root, META, SHARE_ALL, OPEN_EXISTING, NO_REPARSE | 0x2000000)
            require(self.owner.live.get(setup.root_handle) == root_spec)
            self.root_identity = self.stamp(setup.root_handle, root_spec, 0, -1)
            ancestors = tuple(str(p) for p in PureWindowsPath(self.b.root).parents)
            require(type(setup.ancestors) is tuple and len(ancestors) <= 16 and len(setup.ancestors) == len(ancestors))
            for m, path in zip(setup.ancestors, ancestors):
                require(type(m) is Metadata084 and type(m.final_path) is str and m.final_path.casefold() == path.casefold())
                integer(m.attributes)
                require(m.attributes & 0x400 == 0 and m.attributes & 0x10 != 0)
            self.path_stamp(self.b.root + '\\synthetic.bin', 84, self.b.file_identity)
            return True
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            self.finish()
            raise
    def open(self, spec):
        try:
            result, start, end, after = self.call('opens', lambda: self.owner.backend.open(spec, self.owner))
            require(type(result) is Open084 and type(result.error) is int and 0 <= result.error <= 65535)
            if result.handle is not None:
                require(result.error == 0 and same_record(self.owner.live.get(result.handle), spec))
            else: require(result.error != 0)
            return result, start, end, after
        except (Exception, KeyboardInterrupt): self.stopped = True; raise
    def stamp(self, h, spec, size, position, identity=None):
        try:
            raw, _, _, _ = self.call('metadata', lambda: self.owner.backend.metadata(h))
            result = check_metadata084(raw, spec, self.b, size, position, identity)
            if spec.role != 'root': require(raw.ancestors[0].identity == self.root_identity)
            return result
        except (Exception, KeyboardInterrupt): self.stopped = True; raise
    def close(self, h):
        try:
            result, _, _, _ = self.call('closes', lambda: self.owner.close(h))
            require(result is True)
            return result
        except (Exception, KeyboardInterrupt): self.stopped = True; raise
    def path_stamp(self, path, size, identity):
        spec = Spec084('metadata', path, META, SHARE_ALL, OPEN_EXISTING)
        opened, _, _, _ = self.open(spec)
        require(opened.handle is not None)
        try: return self.stamp(opened.handle, spec, size, -1, identity)
        finally:
            if not self.stopped: self.close(opened.handle)
    def control(self, stage, access):
        try:
            require(stage in ('pre', 'independent', 'post') and access in ('write', 'delete'))
            expected = [(s, a) for s in ('pre', 'independent', 'post') for a in ('write', 'delete')]
            require(len(self.probes) < 6 and expected[len(self.probes)] == (stage, access))
            blockers = sum(1 for spec in self.owner.live.values()
                if spec.path == self.b.root + '\\synthetic.bin' and spec.share != SHARE_ALL)
            require(blockers == 0)
            path = self.b.root + '\\synthetic.bin'
            self.path_stamp(path, 84, self.b.file_identity)
            spec = Spec084('control_' + access, path, WRITE if access == 'write' else DELETE, SHARE_ALL, OPEN_EXISTING)
            opened, start, end, after = self.open(spec)
            closed = False
            if stage == 'independent':
                require(opened.error == 32 and opened.handle is None)
                require(control_reason083(start, end, after, self.hold_start) == 0)
            else:
                require(opened.error == 0 and opened.handle is not None)
                self.stamp(opened.handle, spec, 84, -1, self.b.file_identity)
                closed = self.close(opened.handle)
                after = self.m.check()[2]
                if stage == 'post': require(start > self.hold_end + 250)
            self.path_stamp(path, 84, self.b.file_identity)
            final = self.m.check()[2]
            if stage == 'independent': require(control_reason083(start, end, final, self.hold_start) == 0)
            self.probes.append(Probe084(stage, access, start, end, final, opened.error,
                opened.handle is not None, closed, blockers))
            return self.probes[-1]
        except (Exception, KeyboardInterrupt): self.stopped = True; raise
    def exchange(self, kind, deadline):
        lease = None
        try:
            require(kind in ('ready', 'holding', 'closed') and self.sequence < 64)
            require(not self.leases or self.leases[-1].closed)
            require(kind == 'ready' and not self.ready and not self.release_spent or
                kind == 'holding' and self.ready and self.release_time > 0 and self.hold_end == 0 or
                kind == 'closed' and self.hold_start > 0 and self.hold_end == 0)
            if not self.deadline:
                now = self.m.check()[2]
                integer(deadline, 1)
                require(now < deadline <= now + 60000)
                self.deadline = deadline
            require(type(deadline) is int and deadline == self.deadline)
            self.sequence += 1; seq = self.sequence
            def send():
                require(self.m.check()[2] < deadline)
                request = encode084(kind, seq, self.b, self.m.check()[2], deadline)
                return self.owner.backend.transfer(request)
            transfer, request_start, _, _ = self.call('exchanges', send)
            require(type(transfer) is Transfer084 and same_record(transfer.pipe_client, self.b.peer))
            check_security084(transfer.pipe_security, self.b.owner_sid)
            for value in (transfer.pipe_type,transfer.pipe_read_mode,transfer.request_bytes_written,
                transfer.response_buffer_bytes,transfer.response_bytes_read,transfer.response_error): integer(value)
            require((transfer.pipe_type,transfer.pipe_read_mode,transfer.request_bytes_written,
                transfer.response_buffer_bytes,transfer.response_bytes_read,transfer.response_error) == (4,2,144,145,144,0))
            integer(transfer.request_completed); integer(transfer.response_received)
            require(request_start <= transfer.request_completed <= transfer.response_received <= self.m.check()[2])
            signal = decode084(transfer.raw, kind, seq, self.b, self.m.check()[2], deadline,
                self.release_time, transfer.request_completed)
            require(signal.issued <= transfer.response_received)
            path = self.b.root + '\\response-%02d.bin' % seq
            writer_spec = Spec084('signal_writer', path, WRITE, SHARE_ALL, CREATE_NEW)
            writer, _, _, _ = self.open(writer_spec); require(writer.handle is not None)
            ident = self.stamp(writer.handle, writer_spec, 0, 0)
            count, _, _, _ = self.call('writes', lambda: self.owner.backend.write(writer.handle, transfer.raw))
            require(type(count) is int and count == 144)
            self.stamp(writer.handle, writer_spec, 144, 144, ident)
            self.close(writer.handle)
            read_spec = Spec084('signal_reader', path, READ, 1, OPEN_EXISTING)
            reader, _, _, _ = self.open(read_spec); require(reader.handle is not None)
            self.stamp(reader.handle, read_spec, 144, 0, ident)
            raw, _, _, _ = self.call('reads', lambda: self.owner.backend.read(reader.handle, 144))
            require(type(raw) is bytes and raw == transfer.raw)
            self.stamp(reader.handle, read_spec, 144, 144, ident)
            lease = Lease084(self, reader.handle, read_spec, ident, raw, signal, kind, transfer.request_completed)
            self.leases.append(lease)
            require(lease.snapshot() == raw)
            decode084(raw, kind, seq, self.b, self.m.check()[2], deadline, self.release_time, transfer.request_completed)
            if signal.kind != 5:
                if kind == 'ready': self.ready = True
                if kind == 'holding':
                    require(self.hold_start in (0, signal.hold_start))
                    self.hold_start = signal.hold_start
                    require(all(p.guard_end < self.hold_start - 250 for p in self.probes if p.stage == 'pre'))
                if kind == 'closed':
                    require(signal.hold_start == self.hold_start)
                    self.hold_end = signal.hold_end
                self.frames.append((kind, signal, transfer.request_completed, self.m.check()[2]))
            return lease
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise
    def release(self):
        require(self.ready and not self.release_spent and self.sequence < 64 and
            (not self.leases or self.leases[-1].closed))
        self.release_spent = True; self.sequence += 1
        # Clock sampled inside the operation, after its full before guard.
        def send():
            require(self.m.check()[2] < self.deadline)
            self.release_time = self.m.check()[2]
            raw = encode084('release', self.sequence, self.b, self.release_time, self.deadline)
            count = self.owner.backend.release(raw)
            require(type(count) is int and count == 144)
            self.frames.append(('release', decode084(raw, 'release', self.sequence, self.b,
                self.m.check()[2], self.deadline), self.release_time, self.m.check()[2]))
        try:
            self.call('writes', send)
            kind, signal, request, after = self.frames[-1]
            now = self.m.check()[2]
            decode084(signal.raw, 'release', signal.sequence, self.b, now, self.deadline)
            self.frames[-1] = (kind, signal, request, now)
        except (Exception, KeyboardInterrupt): self.stopped = True; raise
    def finish(self):
        require(self.counts['cleanup'] == 0)
        self.counts['cleanup'] = 1
        self.cleanup_ok = self.owner.finish()
        if self.m is not None:
            try: self.m.check()
            except (Exception, KeyboardInterrupt): self.cleanup_ok = False
        self.stopped = True
        return self.cleanup_ok
    def wait_until(self, target):
        integer(target)
        def wait():
            for _ in range(64):
                now = self.m.check()[2]
                if now >= target: return
                self.bump('waits')
                require(self.owner.backend.wait(min(1000, target-now)) is None)
                self.m.check()
            raise ProbeRejected('sync084_wait_rejected')
        self.call('wait_operations', wait)
    def summary(self):
        return dict(version='sync084_interfaces_v1',phase=PHASE,date=DATE,
            dependencies_injected=True, counts=dict(self.counts), release_spent=self.release_spent,
            cleanup_confirmed=self.cleanup_ok, unconfirmed_handles=self.owner.unconfirmed,
            native_protocol_implemented=False,native_mql_verified=False,runtime_authorized=False,
            latency_guaranteed=False,orders_available=False,market_reads=0,orders=0,receipt_permissions=0)


RECORD_KEYS = {'version','phase','reason','requests','responses','opens','reads','closes',
    'hold_start','hold_end','quote_reads','history_reads','orders','receipt_permissions'}
def parse084(text):
    try:
        require(type(text) is str and len(text) <= 2048 and text.startswith(PREFIX))
        r = json.loads(text[len(PREFIX):], object_pairs_hook=unique_pairs)
        require(type(r) is dict and set(r) == RECORD_KEYS and r['version'] == 'synchronization_reader_084_v1' and r['phase'] == PHASE)
        for k in RECORD_KEYS - {'version','phase'}: integer(r[k])
        require(r['reason'] <= 31 and r['requests'] <= 64 and r['responses'] <= r['requests'])
        require(r['opens'] <= 2 and r['reads'] <= 1 and r['closes'] <= r['opens'])
        require(all(r[k] == 0 for k in ('quote_reads','history_reads','orders','receipt_permissions')))
        if r['reason'] == 17:
            require(all(r[k] == 0 for k in RECORD_KEYS - {'version','phase','reason'}))
        if r['reason'] == 0:
            require(r['opens'] == r['closes'] == 2 and r['reads'] == 1 and r['requests'] >= 4)
            require(r['responses'] == r['requests'] - 1 and 0 < r['hold_start'] and
                30000 <= r['hold_end'] - r['hold_start'] <= 31000)
        return r
    except Exception: raise ProbeRejected('sync084_record_rejected') from None


def match084(disabled, enabled, companion):
    """Injected transcripts only. Signal/probe times, not log arrival order."""
    try:
        d, r = (parse084(PREFIX + json.dumps(x)) for x in (disabled, enabled))
        require(d['reason'] == 17 and r['reason'] == 0 and type(companion) is Companion084)
        require(companion.cleanup_ok is True and companion.owner.unconfirmed == 0)
        require((r['hold_start'],r['hold_end']) == (companion.hold_start,companion.hold_end))
        require(r['requests'] == companion.sequence)
        require(len(companion.probes) == 6 and len(companion.frames) == 4)
        require([x[0] for x in companion.frames] == ['ready','release','holding','closed'])
        require(all(l.closed for l in companion.leases))
        last = 0
        for p, (stage, access) in zip(companion.probes, [(s,a) for s in ('pre','independent','post') for a in ('write','delete')]):
            require(type(p) is Probe084 and (p.stage,p.access) == (stage,access))
            for v in (p.start,p.end,p.guard_end,p.error,p.companion_blockers): integer(v)
            require(last <= p.start <= p.end <= p.guard_end and p.companion_blockers == 0)
            last = p.guard_end
            require(type(p.opened) is bool and type(p.closed) is bool)
            if stage == 'independent':
                require(p.error == 32 and not p.opened and not p.closed and
                    control_reason083(p.start,p.end,p.guard_end,r['hold_start']) == 0)
            else:
                require(p.error == 0 and p.opened and p.closed)
                require(p.guard_end < r['hold_start'] - 250 if stage == 'pre' else p.start > r['hold_end'] + 250)
        seq = 0
        for kind, s, request, after in companion.frames:
            require(type(s) is Signal084 and s.sequence > seq)
            seq = s.sequence
            require(decode084(s.raw,kind,s.sequence,companion.b,after,companion.deadline,
                companion.release_time,request if kind != 'release' else None) == s)
        return dict(modeled_match=True,probe_count=6,native_mql_verified=False,
            native_publication_verified=False,runtime_authorized=False,latency_guaranteed=False,
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
            quote_reads=0,history_reads=0,orders=0,receipt_permissions=0)
    except Exception: raise ProbeRejected('sync084_match_rejected') from None


def source_inputs084(root):
    """Static complete local import/include graph; no native import execution."""
    seen = set(MQL_INPUTS)
    pending = ['src/forex_demo_lab/synchronization_084.py','src/forex_demo_lab/__init__.py']
    while pending:
        name = pending.pop()
        if name in seen: continue
        seen.add(name)
        tree = ast.parse((root / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                require(node.level == 1 and node.module is not None)
                candidate = 'src/forex_demo_lab/' + node.module.replace('.', '/') + '.py'
                require((root / candidate).is_file())
                pending.append(candidate)
    return tuple(sorted(seen))


def source_contract084(root):
    inputs = source_inputs084(root)
    hashes = {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in inputs}
    for name in MQL_INPUTS:
        text = (root/name).read_text()
        import re
        for included in re.findall(r'^#include "([^"]+)"', text, flags=re.M):
            require('mt5/Scripts/' + included in inputs)
        require('#import' not in text)
    return dict(version='synchronization_source_084_v1',phase=PHASE,date=DATE,
        input_bindings=hashes,wire_bytes=144,compiled=False,execution_authorized=False,
        native_protocol_implemented=False,orders_available=False,caps=CAPS,guard_cap=GUARD_CAP,
        mql_guard_cap=1024,mql_io_cap=512,freshness_ms=2000,start_ms=10000,
        hold_ms=30000,close_latest_ms=31000,margin_ms=250,episode_ms=60000,whole_ms=120000,
        synthetic_sha256=hashlib.sha256(DATA084).hexdigest(),
        candidate_build_schema=dict(compiler_calls=1,actual_compiler_exit=1,errors=0,warnings=0,
            terminal_build=6244,artifact_min_bytes=1,artifact_max_bytes=1048576,
            required_source_bindings=hashes,normalization_allowed=False,build_authority=False))
