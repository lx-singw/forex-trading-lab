"""Bounded, injected metadata profile and a modeled synchronization protocol.

No SDK import, native entry point, signal transport, MQL launch or order API.
Preparation contracts cannot authorize a native session. A future caller must
own resources before bootstrap and close them even if construction fails.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import Lock

from .clock_observer_042 import unique_pairs
from .image_guard_068 import HelperChain068
from .private_guard_065 import FullGuard065
from .sharing_adapter_076 import (VerifiedBuild076, runtime_bindings076,
    exact076, encoded076)
from .sharing_integration_072 import SOURCE_INPUTS
from .sharing_runtime_066 import PrivateReader066, digest
from .sharing_runtime_069 import Resources069, LIMITS069, close_owned069
from .sharing_probe_062 import ProbeRejected

PHASE = '77000000000000000000000000000001'
SYNC_PHASE = '77000000000000000000000000000002'
DATE = '2026-10-08'
SAMPLES = 4
SESSION_MS = 600000
# Denied buckets remain zero, including all fixture/deployment/log operations.
LIMITS077 = {**dict.fromkeys(LIMITS069, 0),
    'profile_samples': SAMPLES, 'guards': 2*SAMPLES, 'clock_samples': 100000,
    'process_opens': 128, 'identity_tokens': 128, 'token_queries': 512,
    'process_snapshots': 64, 'process_entries': 32768, 'native_calls': 25000,
    'hash_reads': 192, 'hash_bytes': 17179869184, 'hash_path_stats': 4096,
    'sdk_queries': 128, 'closes': 256, 'local_frees': 256,
    'sdk_connections': 1, 'sdk_shutdowns': 1, 'reservation_writes': 1,
    'trust_queries': 1, 'startup_path_stats': 64}
HANDSHAKE_LIMITS077 = {**LIMITS077, 'profile_samples': 0, 'guards': 10,
    'sdk_queries': 160}


class Meter077:
    limits = LIMITS077
    def __init__(self, clock):
        self.clock = clock
        self.counts = dict.fromkeys(self.limits, 0)
        self.first = self.last = None
        self.elapsed_us = 0
        self.cleanup_exceeded = self.stopped = False
        self.check()

    def check(self):
        if self.stopped:
            raise ProbeRejected('profile_meter_stopped')
        self.counts['clock_samples'] += 1
        try:
            if self.counts['clock_samples'] > self.limits['clock_samples']:
                raise ValueError()
            now = self.clock()
            if (type(now) is not tuple or len(now) != 3 or
                any(type(x) is not int or x < 0 for x in now) or
                datetime.fromtimestamp(now[0]//1000, timezone.utc).date().isoformat() != DATE):
                raise ValueError()
            if self.first is None:
                self.first = self.last = now
            if any(a < b for a, b in zip(now, self.last)):
                raise ValueError()
            delta = tuple(a-b for a, b in zip(now, self.first))
            if (max(delta[0], delta[2]) >= SESSION_MS or delta[1] >= SESSION_MS*1000000 or
                abs(delta[0]-delta[1]//1000000) > 1000 or
                abs(delta[2]-delta[1]//1000000) > 1000):
                raise ValueError()
            self.last = now
            self.elapsed_us = delta[1]//1000
            return now
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise ProbeRejected('profile_clock_rejected') from None

    def consume(self, key, amount=1):
        self.check()
        if (key not in self.limits or type(amount) is not int or amount < 1 or
            self.counts[key]+amount > self.limits[key]):
            self.stopped = True
            raise ProbeRejected('profile_budget_rejected')
        self.counts[key] += amount

    def cleanup(self, key):
        # Attempt owned release even after expiry/exhaustion; never refund.
        if key not in ('closes', 'local_frees', 'sdk_shutdowns'):
            self.cleanup_exceeded = True
            return
        self.counts[key] += 1
        if self.counts[key] > self.limits[key]:
            self.cleanup_exceeded = True


class HandshakeMeter077(Meter077):
    limits = HANDSHAKE_LIMITS077


def profile_contract077(build, preparation, policy, profile, chain):
    if type(build) is not VerifiedBuild076 or type(chain) is not HelperChain068:
        raise ProbeRejected('profile_contract_rejected')
    if (type(chain.images) is not tuple or
        any(type(b) is not tuple or len(b) != 2 for b in
            (chain.launcher, chain.config, chain.library, *chain.images))):
        raise ProbeRejected('profile_contract_rejected')
    return dict(version='timing_profile_preparation_077_v1', phase=PHASE, date=DATE,
        bindings=runtime_bindings076(build, preparation, policy, profile),
        build_record_sha256=build.sha256,
        helper_bindings=dict(launcher=chain.launcher[1], config=chain.config[1],
            library=chain.library[1], images=[b[1] for b in chain.images]),
        fixed_samples=SAMPLES, full_guards_per_sample=2, session_ms=SESSION_MS,
        limits=dict(LIMITS077), maximum_sdk_connections=1, maximum_script_launches=0,
        maximum_log_content_reads=0, maximum_market_reads=0, maximum_orders=0,
        maximum_receipt_permissions=0, execution_authorized=False,
        latency_guaranteed=False, orders_available=False)


def validate_policy077(raw, expected, expected_sha):
    try:
        if (type(raw) is not bytes or not 0 < len(raw) <= 8192 or
            hashlib.sha256(raw).hexdigest() != digest(expected_sha)):
            raise ValueError()
        parsed = json.loads(raw.decode('ascii'), object_pairs_hook=unique_pairs)
        if not exact076(parsed, expected) or raw != encoded076(expected):
            raise ValueError()
        if (parsed['phase'] != PHASE or parsed['date'] != DATE or
            parsed['execution_authorized'] is not False or parsed['orders_available'] is not False):
            raise ValueError()
        return parsed
    except Exception:
        raise ProbeRejected('profile_policy_rejected') from None


class Reservation077:
    def __init__(self, path, build, preparation, policy, profile, chain, meter):
        if type(meter) is not Meter077:
            raise ProbeRejected('profile_reservation_rejected')
        contract = profile_contract077(build, preparation, policy, profile, chain)
        raw = encoded076(contract)
        validate_policy077(raw, contract, hashlib.sha256(raw).hexdigest())
        self.raw, self.meter = raw, meter
        self.spent = self.attached = self.started = self.stopped = False
        self.lock = Lock()
        meter.consume('reservation_writes')
        try:
            with Path(path).open('xb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        except Exception:
            self.stopped = True
            raise ProbeRejected('profile_reservation_unavailable') from None

    def sdk_attempt(self):
        with self.lock:
            if self.spent or self.stopped:
                raise ProbeRejected('profile_session_unavailable')
            self.spent = True
            self.meter.consume('sdk_connections')

    def claim(self):
        with self.lock:
            if not self.spent or not self.attached or self.started or self.stopped:
                raise ProbeRejected('profile_session_unavailable')
            self.started = True

    def confirm_attach(self, owner):
        with self.lock:
            try:
                if (type(owner) is not Resources069 or owner.session is not self or owner.meter is not self.meter or
                    owner.closed or owner.sdk is None or not self.spent or self.attached or self.started or self.stopped):
                    raise ValueError()
                events = [e for e in owner.trace.events if e['stage']=='sdk_attach']
                if len(events) != 1 or events[0]['completed'] is not True:
                    raise ValueError()
                self.attached = True
            except Exception:
                self.stopped = True
                raise ProbeRejected('profile_attach_unconfirmed') from None

    def stop(self):
        self.stopped = True


def duration_ms077(start, end):
    # Retain ceil of monotonic nanoseconds; boot-clock quantization cannot hide
    # a positive sub-millisecond cost. The meter independently checks all clocks.
    return (end[1]-start[1]+999999)//1000000


class ProfileGuard077:
    def __init__(self, owner, core, build, preparation, policy, profile, chain,
                 executable, base_alias, loaded_library, source_paths):
        self.owner, self.core, self.build, self.chain = owner, core, build, chain
        self.executable, self.base_alias, self.loaded_library = executable, base_alias, loaded_library
        self.source_paths = dict(source_paths)
        self.contract = encoded076(profile_contract077(build, preparation, policy, profile, chain))
        self.stopped = False
        self.graph()

    def graph(self):
        o, c = self.owner, self.core
        try:
            if (type(o) is not Resources069 or o.closed or o.runner is not None or o.files is not None or
                type(o.meter) is not Meter077 or type(o.session) is not Reservation077 or
                o.session.meter is not o.meter or not o.session.spent or not o.session.attached or o.session.stopped or
                o.session.raw != self.contract or type(c) is not FullGuard065 or
                type(o.sdk.__version__) is not str or o.sdk.__version__ != '5.0.6231' or
                c.meter is not o.meter or c.api._meter is not o.meter or c.api._api is not o.sdk or
                type(c.reader) is not PrivateReader066 or c.reader.base.f is not o.base or
                c.reader.base.meter is not o.meter or o.base.meter is not o.meter or
                self.stopped):
                raise ValueError()
            r = self.build.record()
            if (c.peer.digest != r['terminal_sha256'] or c.build != r['terminal_build'] or
                c.editor[1] != r['compiler_sha256'] or c.artifact[1] != r['artifact_sha256'] or
                set(self.source_paths) != set(SOURCE_INPUTS)):
                raise ValueError()
            if (c.reader.helper.image, c.reader.helper.digest) not in tuple(
                (p.casefold(), h) for p, h in self.chain.images):
                raise ValueError()
        except Exception:
            self.stopped = True
            raise ProbeRejected('profile_ownership_or_binding_rejected') from None

    def sample(self):
        self.graph()
        m = self.owner.meter
        m.consume('profile_samples')
        start = m.check()
        guards = []
        before = dict(m.counts)
        try:
            a = m.check()
            if self.core() is not True:
                raise ValueError()
            b = m.check(); guards.append(duration_ms077(a, b))
            reader = self.core.reader
            # Rehash every helper input/image, source and header, without a cache.
            self.chain.check(reader, reader.helper, self.executable, self.base_alias, self.loaded_library())
            for path, expected in self.chain.images:
                if reader.hash_file(path) != expected:
                    raise ValueError()
            for name, expected in self.build.record()['input_bindings'].items():
                if reader.hash_file(self.source_paths[name]) != expected:
                    raise ValueError()
            a = m.check()
            if self.core() is not True:
                raise ValueError()
            b = m.check(); guards.append(duration_ms077(a, b))
            self.graph(); end = m.check()
            return dict(core_guard_ms=guards, composite_sample_ms=duration_ms077(start, end),
                hash_reads=m.counts['hash_reads']-before['hash_reads'],
                hash_bytes=m.counts['hash_bytes']-before['hash_bytes'],
                sdk_queries=m.counts['sdk_queries']-before['sdk_queries'])
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise ProbeRejected('profile_sample_rejected') from None


def profile_once077(owner, guard):
    if type(owner) is not Resources069:
        raise ProbeRejected('profile_ownership_or_binding_rejected')
    rows, reason = [], None
    try:
        if type(guard) is not ProfileGuard077 or guard.owner is not owner:
            raise ValueError()
        guard.graph(); owner.session.claim()
        for _ in range(SAMPLES):
            rows.append(guard.sample())
    except (Exception, KeyboardInterrupt):
        reason = 'profile_stopped_details_redacted'
    finally:
        owner.session.stop()
        cleanup = close_owned069(owner)
    guards = [ms for row in rows for ms in row['core_guard_ms']]
    return dict(version='timing_profile_observation_077_v1', phase=PHASE, date=DATE,
        preparation_contract_sha256=hashlib.sha256(owner.session.raw).hexdigest()
            if type(owner.session) is Reservation077 else None,
        build_record_sha256=guard.build.sha256 if type(guard) is ProfileGuard077 else None,
        completed=len(rows) == SAMPLES and reason is None and not cleanup['errors'],
        stop_reason=reason, samples=rows, samples_completed=len(rows),
        observed_core_guard_max_ms=max(guards) if guards else None,
        observed_composite_max_ms=max((r['composite_sample_ms'] for r in rows), default=None),
        counts=dict(owner.meter.counts), cleanup=cleanup,
        observations_only=True, latency_guaranteed=False, native_timing_verified=False,
        native_launch_ready=False, runtime_authorized=False, orders_available=False)


@dataclass(frozen=True)
class Signal077:
    kind: str
    phase: str
    build_sha256: str
    identity: tuple = field(repr=False)
    origin_boot_ms: int
    deadline_boot_ms: int
    start_boot_ms: int
    end_boot_ms: int


class Handshake077:
    """Finite model only; no transport, hold handle, publication or native ACK.

    A restart cannot recreate this episode because the marker is exclusive.
    Later source/decoder must prove authenticity/private ACL and clock domain.
    """
    def __init__(self, path, build, identity, meter, guard):
        if (type(build) is not VerifiedBuild076 or type(meter) is not HandshakeMeter077 or
            type(identity) is not tuple or len(identity) != 3 or
            any(type(x) is not int or x < 0 for x in identity) or identity[0] == 0 or
            identity[1:] == (0, 0) or not callable(guard)):
            raise ProbeRejected('handshake_binding_rejected')
        self.build, self.identity, self.meter, self.guard = build, identity, meter, guard
        self.state = 'new'; self.stopped = False; self.events = []
        self.release_boot = self.hold_boot = None
        now = meter.check(); self.origin = now[2]; self.deadline = self.origin+60000
        self.last_signal_end = self.origin
        raw = encoded076(dict(version='handshake_model_reservation_077_v1', phase=SYNC_PHASE,
            date=DATE, build_sha256=build.sha256,
            identity_sha256=hashlib.sha256(encoded076(identity)).hexdigest(),
            origin_boot_ms=self.origin, deadline_boot_ms=self.deadline,
            maximum_releases=1, execution_authorized=False, orders_available=False))
        try:
            meter.consume('reservation_writes')
            with Path(path).open('xb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        except Exception:
            self.stopped = True
            raise ProbeRejected('handshake_reservation_unavailable') from None

    def accept(self, signal):
        try:
            if self.stopped or self.state == 'complete' or type(signal) is not Signal077:
                raise ValueError()
            expected = {'new':'ready', 'ready':'release', 'released':'holding',
                        'holding':'write', 'write':'delete'}[self.state]
            if (type(signal.kind) is not str or signal.kind != expected or
                type(signal.phase) is not str or signal.phase != SYNC_PHASE or
                type(signal.build_sha256) is not str or signal.build_sha256 != self.build.sha256 or
                not exact076(signal.identity, self.identity) or
                any(type(x) is not int or x < 0 for x in (signal.origin_boot_ms,
                    signal.deadline_boot_ms, signal.start_boot_ms, signal.end_boot_ms)) or
                (signal.origin_boot_ms, signal.deadline_boot_ms) != (self.origin, self.deadline) or
                not self.last_signal_end <= signal.start_boot_ms <= signal.end_boot_ms):
                raise ValueError()
            before = self.meter.check()[2]
            if before >= self.deadline or signal.end_boot_ms > before:
                raise ValueError()
            # Full guards remain around every modeled signal operation. There
            # is no cached proof allowing a guard-free critical window.
            if self.guard() is not True:
                raise ValueError()
            after = self.meter.check()[2]
            if after >= self.deadline or after-signal.end_boot_ms > 2000:
                raise ValueError()
            if expected in ('ready', 'release', 'holding') and signal.start_boot_ms != signal.end_boot_ms:
                raise ValueError()
            if expected == 'holding':
                if not self.release_boot <= signal.start_boot_ms <= self.release_boot+10000:
                    raise ValueError()
                self.hold_boot = signal.start_boot_ms
            if expected in ('write', 'delete'):
                if not (self.hold_boot+250 < signal.start_boot_ms <= signal.end_boot_ms < self.hold_boot+29750):
                    raise ValueError()
            # Spend release BEFORE the trailing guard, even if it later fails.
            if expected == 'release':
                self.release_boot = after
            self.state = {'ready':'ready', 'release':'released', 'holding':'holding',
                          'write':'write', 'delete':'complete'}[expected]
            if self.guard() is not True:
                raise ValueError()
            end = self.meter.check()[2]
            if (end >= self.deadline or end-signal.end_boot_ms > 2000 or
                expected == 'release' and end+40250 >= self.deadline or
                expected in ('write', 'delete') and end >= self.hold_boot+29750):
                raise ValueError()
            self.last_signal_end = signal.end_boot_ms
            self.events.append(expected)
            return True
        except (Exception, KeyboardInterrupt):
            self.stopped = True
            raise ProbeRejected('handshake_signal_rejected') from None

    def report(self):
        return dict(version='handshake_model_077_v1', phase=SYNC_PHASE,
            modeled_completed=self.state == 'complete' and not self.stopped,
            stopped=self.stopped, events=list(self.events), maximum_releases=1,
            launch_gate_ms=10000, hold_ms=30000, margin_ms=250,
            native_protocol_implemented=False, native_launch_ready=False,
            native_mql_verified=False, runtime_authorized=False, orders_available=False)
