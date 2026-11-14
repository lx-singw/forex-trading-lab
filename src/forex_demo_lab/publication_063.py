"""Offline publication/ACK protocol, using injected file capabilities only.

No native adapter, IPC, SDK or orders. A successful model result is not a
quote-capture permission. The adapter must retain every acquired handle even
when a call raises after acquisition, and report uncertain cleanup as retained.
"""
from dataclasses import dataclass
import hashlib

from .capture_budget_047 import require_guard
from .transport_lifecycle_060 import (
    ACK_MAGIC, Cleanup, Observation, OfflineLifecycle, issue_frame)
from .windows_pipe_047 import PipeRejected


@dataclass(frozen=True)
class FileProof:
    identity: bytes                 # Private opaque model identity; never exported.
    size: int
    position: int
    regular: bool = False
    owner: bool = False
    sandbox: bool = False
    no_reparse: bool = False
    single_link: bool = False
    write_excluded: bool = False
    delete_excluded: bool = False


def valid_proof(proof, size, position, identity=None, sealed=False):
    return (type(proof) is FileProof and type(proof.identity) is bytes and
            len(proof.identity) == 16 and
            (identity is None or proof.identity == identity) and
            type(proof.size) is int and proof.size == size and
            type(proof.position) is int and proof.position == position and
            all(getattr(proof, k) is True for k in
                ('regular', 'owner', 'sandbox', 'no_reparse', 'single_link')) and
            (not sealed or proof.write_excluded is True and proof.delete_excluded is True))


class Publication063:
    """One attempt, two CREATE_NEW files, no readiness marker or retry loop.

    Producer closes its writer, acquires a read-only seal, verifies identity and
    bytes, THEN permits reader open. Response seal and reader remain held while
    a separate ACK file goes through the same protocol. There is no atomic-rename
    claim: a replacement in the close/open gap is rejected by private identity.
    All deadlines are checks after calls return; they cannot preempt native IO.
    """
    def __init__(self, api, authority, policy, clock, guard):
        self.api, self.authority, self.policy, self.guard = api, authority, policy, guard
        self.timer = OfflineLifecycle(policy, clock, guard)
        self.started = False
        self.stage = 0
        self.published = set()
        self.held = {}
        self.counts = dict(creates=0, writes=0, seals=0, reader_opens=0, reads=0,
                           writer_closes=0, snapshots=0)

    def call(self, operation, *args):
        require_guard(self.guard)
        self.timer.sample()
        value = self.timer.call(operation, *args)
        require_guard(self.guard)
        self.timer.sample()
        return value

    def counted(self, key, limit, operation, *args):
        if self.counts[key] >= limit:
            raise PipeRejected('publication_budget_exhausted')
        self.counts[key] += 1       # Burn attempt before guard/call, never refund.
        return self.call(operation, *args)

    def proof(self, handle, size, position, identity=None, sealed=False):
        p = self.counted('snapshots', 32, self.api.snapshot, handle)
        if not valid_proof(p, size, position, identity, sealed):
            raise PipeRejected('publication_proof_rejected')
        return p.identity

    def read_exact(self, handle, raw, identity):
        self.proof(handle, len(raw), 0, identity, True)
        value = self.counted('reads', 4, self.api.read, handle, len(raw))
        # A zero/short/extra read or successful count with different bytes fails.
        if type(value) is not bytes or value != raw:
            raise PipeRejected('publication_bytes_rejected')
        self.proof(handle, len(raw), len(raw), identity, True)
        return value

    def publish(self, kind, raw):
        if kind in self.published or kind not in ('response', 'ack'):
            raise PipeRejected('publication_unavailable')
        self.published.add(kind)   # Failure, crash or stale file cannot be retried.
        self.stage = 1 if kind == 'response' else 5
        writer = self.counted('creates', 2, self.api.create_new, kind)
        identity = self.proof(writer, 0, 0)
        count = self.counted('writes', 2, self.api.write, writer, raw)
        if type(count) is not int or count != len(raw):
            raise PipeRejected('publication_write_rejected')
        self.proof(writer, len(raw), len(raw), identity)
        if self.counted('writer_closes', 2, self.api.close_writer, writer) is not True:
            raise PipeRejected('publication_close_unconfirmed')
        self.stage += 1
        seal = self.counted('seals', 2, self.api.acquire_seal, kind)
        self.read_exact(seal, raw, identity)
        self.stage += 1
        reader = self.counted('reader_opens', 2, self.api.open_reader, kind)
        self.read_exact(reader, raw, identity)
        self.proof(seal, len(raw), len(raw), identity, True)
        self.held[kind] = (seal, reader, identity, len(raw))
        return raw

    def retain_proofs(self):
        for seal, reader, identity, size in self.held.values():
            self.proof(seal, size, size, identity, True)
            self.proof(reader, size, size, identity, True)

    def observe(self):
        self.stage = 0
        raw = self.call(issue_frame, self.authority, self.policy)
        data = self.publish('response', raw)
        self.response_digest = hashlib.sha256(data).digest()
        return Observation('ready', data, True)

    def wait(self):
        raise PipeRejected('publication_wait_unavailable')

    def ack(self, raw, remaining):
        self.stage = 4
        self.retain_proofs()
        # Validate ACK binding independently, not merely the caller's bytes.
        if type(raw) is not bytes or len(raw) != 40 or raw[:8] != ACK_MAGIC:
            raise PipeRejected('publication_ack_rejected')
        if (type(remaining) is not int or not 0 < remaining <= 2000 or
                raw[8:] != self.response_digest):
            raise PipeRejected('publication_ack_rejected')
        data = self.publish('ack', raw)
        self.retain_proofs()
        self.stage = 8
        return Observation('written', data, True)

    def finish(self):
        # Check both held files before releasing. Cleanup must still run after
        # validation/deadline failure; no identity values or exception text escape.
        proof_ok = False
        try:
            self.retain_proofs()
            proof_ok = True
        finally:
            self.authority.close()
            cleanup = self.api.finish()
        if not proof_ok or type(cleanup) is not Cleanup:
            return Cleanup(False, True)
        return cleanup

    def run(self):
        if self.started:
            raise PipeRejected('publication_unavailable')
        self.started = True
        result = self.timer.run(self)
        result.update(version='offline_publication_063_v1', stage=self.stage,
                      attempts=dict(self.counts), authority=self.authority.summary(),
                      native_publication_verified=False, native_mql_verified=False,
                      orders_available=False, fresh_performance_eligible=False, annual_eligible=False)
        return result
