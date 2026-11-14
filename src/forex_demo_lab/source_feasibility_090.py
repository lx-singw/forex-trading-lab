"""Offline count accounting only. No native reader, date renewal or admission.

The original065 numeric predicates are called directly. Injected file sizes,
path depths and successful process calls are assumptions, not native evidence.
"""
from dataclasses import dataclass, replace
from types import MappingProxyType

from .sharing_companion_065 import LIMITS, Meter065
from .sharing_probe_062 import ProbeRejected

SOURCE = 'src/forex_demo_lab/source_feasibility_090.py'
REVIEW_DATE = '2026-10-09'
CAPS = MappingProxyType(dict(LIMITS))
CHUNK = 1048576
FILE_CAP = 134217728


def positive(value):
    if type(value) is not int or value < 1:
        raise ProbeRejected('source090_invalid_count')
    return value


def feasibility090(sources=41, roles=9, guards=38, passes=2, boot_queries=75):
    for value in (sources, roles, guards, passes, boot_queries): positive(value)
    source_reads = sources * guards * passes
    explicit_reads = (sources + roles) * guards * passes + 4 * boot_queries
    # FullGuard087.identity is called twice, hashing terminal AND helper each time.
    identity_reads = 4 * guards
    return dict(source_reads=source_reads, explicit_reads=explicit_reads,
        identity_image_reads=identity_reads, reader_reads=explicit_reads + identity_reads,
        hash_read_cap=CAPS['hash_reads'], source_only_fits=source_reads <= CAPS['hash_reads'],
        contract_fits=explicit_reads + identity_reads <= CAPS['hash_reads'],
        native_experiment_can_proceed=False, runtime_authorized=False, orders_available=False,
        counted_current_090_source=False, native_cost_proven=False)


def representation090(kind):
    # Archives/manifests do not attest separately mutable execution/source paths.
    if kind != 'individual_fresh_before_after':
        raise ProbeRejected('source090_representation_rejected')
    return feasibility090()


def projection090(proofs, guards=38, entries=2):
    """Arithmetic projection, never a runnable episode with enlarged caps.

    Each (profile, multiplicity) is an individually acquired file, including
    identity/boot repeats. Actual Windows paths and private image sizes are open.
    """
    positive(guards); positive(entries)
    counts = dict.fromkeys(CAPS, 0); counts['clock_samples'] = 1
    for profile, reads in proofs:
        positive(reads)
        if (type(profile) is not Profile090 or type(profile.size) is not int or
                not 1 <= profile.size <= FILE_CAP or type(profile.path_nodes) is not int or
                not 1 <= profile.path_nodes <= 256):
            raise ProbeRejected('source090_profile_rejected')
        chunks = (profile.size + CHUNK - 1) // CHUNK
        counts['hash_reads'] += reads
        counts['hash_bytes'] += reads * profile.size
        counts['hash_path_stats'] += reads * (profile.path_nodes + 2)
        counts['clock_samples'] += reads * (profile.path_nodes + 5 + 2 * chunks)
    identities = 4 * guards; snapshots = 2 * guards
    counts.update(process_opens=identities, identity_tokens=identities,
        process_snapshots=snapshots, process_entries=snapshots * entries,
        native_calls=8 * identities + (entries + 2) * snapshots,
        token_queries=3 * identities, closes=2 * identities + snapshots,
        local_frees=identities)
    counts['clock_samples'] += 21 * identities + snapshots * (5 + 3 * entries)
    return dict(projected_counts=counts, exceeded=[k for k in CAPS if counts[k] > CAPS[k]],
        profile_scope='public_canonical_sizes_depths_and_synthetic_private_images',
        arithmetic_projection_only=True, native_cost_proven=False, runtime_authorized=False,
        orders_available=False, sdk_raw_api_and_runner_costs_included=False)


class Counts090:
    """Exact065 consume/cleanup predicates, COUNT ONLY: no old date bypass.

    No native clock is sampled and the legacy900s meter is never instantiated.
    Current083 timing predicates remain in the coupled historical fixture.
    """
    model_only = True
    def __init__(self):
        self.counts = dict.fromkeys(CAPS, 0)
        self.cleanup_exceeded = False
        self.stopped = False
        self.first_exhausted = None
        self.check()
    def check(self):
        if self.stopped: raise ProbeRejected('source090_count_model_stopped')
        self.counts['clock_samples'] += 1
        if self.counts['clock_samples'] > CAPS['clock_samples']:
            self.stopped = True; self.first_exhausted = 'clock_samples'
            raise ProbeRejected('clock_budget_exhausted')
    def consume(self, key, amount=1):
        try:
            # No cap argument or altered copy of the predicate.
            return Meter065.consume(self, key, amount)
        except Exception:
            self.stopped = True
            if self.first_exhausted is None: self.first_exhausted = key
            raise
    def cleanup(self, key):
        Meter065.cleanup(self, key)


@dataclass(frozen=True)
class Profile090:
    size: int
    path_nodes: int


def hash_cost090(meter, profile):
    """NativeIdentity065.hash_file control flow, with declared bytes/depth.

    Includes file+all-parent lstats, two stats, each1MiB read/byte charge,
    EOF check and final check. No content/path safety claim from these counts.
    """
    meter.consume('hash_reads')
    if type(profile) is not Profile090 or type(profile.path_nodes) is not int or not 1 <= profile.path_nodes <= 256:
        raise ProbeRejected('source090_profile_rejected')
    for _ in range(profile.path_nodes): meter.consume('hash_path_stats')
    meter.consume('hash_path_stats')
    if type(profile.size) is not int or not 1 <= profile.size <= FILE_CAP:
        raise ProbeRejected('source090_profile_rejected')
    remaining = profile.size
    while remaining:
        meter.check(); amount = min(CHUNK, remaining)
        meter.consume('hash_bytes', amount); remaining -= amount
    meter.check()  # EOF read
    meter.consume('hash_path_stats')
    meter.check()


class ReaderAccounting090:
    """Attach count hooks to an existing injected reader, preserving its graph.

    Digest values and process identities are still fixture values. This is not
    NativeIdentity065 or a Windows filesystem/process implementation.
    """
    model_only = True
    def __init__(self, reader, profiles, entries=2):
        if getattr(reader, 'model_only', None) is not True or type(entries) is not int or not 1 <= entries <= 512:
            raise ProbeRejected('source090_reader_rejected')
        if type(profiles) is not dict or set(profiles) != set(reader.hashes):
            raise ProbeRejected('source090_profile_rejected')
        self.reader = reader; self.profiles = MappingProxyType(dict(profiles)); self.entries = entries
        self.meter = Counts090(); self.hashes = 0; self.identity_hashes = 0
        self.owned = []; self.close_attempts = 0; self.free_attempts = 0
        self.original_hash = reader.hash_file
        self.original_identity = reader.identity
        self.original_unique = reader.unique_pid
        reader.hash_file = self.hash_file; reader.identity = self.identity; reader.unique_pid = self.unique_pid
    def native(self, token_query=False, register=None):
        if token_query: self.meter.consume('token_queries')
        self.meter.consume('native_calls')
        if register is not None: self.owned.append(register)
        self.meter.check()
    def close(self, role):
        self.owned.remove(role); self.meter.cleanup('closes'); self.close_attempts += 1
    def hash_file(self, path):
        hash_cost090(self.meter, self.profiles[path])
        self.hashes += 1
        return self.original_hash(path)
    def unique_pid(self):
        self.meter.consume('process_snapshots')
        try:
            self.native(register='snapshot'); self.native()  # snapshot, first
            for _ in range(self.entries):
                self.meter.consume('process_entries'); self.native()  # next, including EOF
            return self.original_unique()
        finally:
            if 'snapshot' in self.owned: self.close('snapshot')
    def identity(self, pid):
        self.meter.consume('process_opens')
        try:
            self.native(register='process')
            for _ in range(3): self.native()  # image, times, session
            self.meter.consume('identity_tokens'); self.native(register='token')
            self.native(token_query=True); self.native(token_query=True)
            self.native(token_query=True)  # bounded logon SID conversion
            self.meter.cleanup('local_frees'); self.free_attempts += 1
            value = self.original_identity(pid)
            digest = self.hash_file(value.image); self.identity_hashes += 1
            return replace(value, digest=digest)
        finally:
            for role in ('token', 'process'):
                if role in self.owned: self.close(role)


def native_entry090(*args, **kwargs):
    raise ProbeRejected('source090_native_contract_infeasible')
