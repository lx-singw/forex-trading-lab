"""Invented-only read-only payload boundary for frozen138/140 supervision.

Health observations may be decoded using142's protocol used by143. There is no
native helper/source adapter, account query, terminal launch or order interface.
"""
from dataclasses import dataclass, replace
import hashlib
import os
from pathlib import Path
import re

from .acquisition_lifecycle_138 import Checks, State
from .helper_health_142 import HealthDecoder
from .paired_replay_133 import DENIED, canonical, strict_json
from .segment_journal_138 import StorageFailure, uint, inspect_segments, MAX_JOB
from .supervision_140 import Supervisor, Observation, inspect_ledger, MAX_FRAME as SUP_FRAME, MAX_FRAMES as SUP_FRAMES

SCHEMA = 'invented_readonly_recorder155_v1'
MAX_FRAME = 4096
MAX_BYTES = 1024*1024
HASH = re.compile('[a-f0-9]{64}')
KINDS = ('context','triple','none')
EVENTS = ('begin','prepared','commit','abort','end')


def fields(value, names):
    if type(value) is not dict or set(value) != set(names):raise ValueError('recorder155_fields')


def payload(kind, value):
    if kind == 'context':
        fields(value, ('epoch','digits','contract_units','cost_state'))
        for key in ('epoch','digits','contract_units'):uint(value[key])
        if not 1 <= value['epoch'] or not 0 <= value['digits'] <= 8 or not 1 <= value['contract_units'] <= 10000000 or value['cost_state'] != 'unknown':
            raise ValueError('recorder155_context')
    elif kind == 'triple':
        fields(value, ('before_us','after_us','quote','context_ref'))
        uint(value['before_us']);uint(value['after_us'])
        if value['after_us'] < value['before_us'] or type(value['context_ref']) is not str or not HASH.fullmatch(value['context_ref']):raise ValueError('recorder155_clock_or_context')
        quote(value['quote'])
    else:raise ValueError('recorder155_payload_kind')
    return value


def quote(value):
    fields(value, ('source_label','bid_points','ask_points','flags'))
    for key in value:uint(value[key])
    if not 0 < value['bid_points'] <= value['ask_points'] <= 1000000000 or value['flags'] >= 2**32:
        raise ValueError('recorder155_quote')
    return value


@dataclass(frozen=True)
class Snapshot:
    at_us: int
    checks: Checks
    health: Observation
    owner_alive: bool = True


@dataclass(frozen=True)
class Read:
    kind: str
    before: Snapshot
    after: Snapshot
    value: object


class InventedSource:
    """Predeclared memory values only; no callbacks, paths or native source hook."""
    def __init__(self, reads):
        if (type(reads) is not list or len(reads) > 4096 or any(type(r) is not Read
                or r.kind not in ('context','clock_before','quote','clock_after')
                or type(r.before) is not Snapshot or type(r.after) is not Snapshot for r in reads)):
            raise ValueError('recorder155_invented_reads')
        self.reads = tuple(reads)
        self.cursor = self.queries = 0
        self.fail_query = None

    def peek(self, kind):
        if self.cursor >= len(self.reads) or self.reads[self.cursor].kind != kind:raise ValueError('recorder155_read_order')
        return self.reads[self.cursor]

    def read(self, kind):
        item = self.peek(kind)
        self.queries += 1
        if self.queries == self.fail_query:raise OSError('invented155_source_failure')
        self.cursor += 1
        return item


def decoded_snapshot(decoder, raw, challenge, sent_us, received_us, checks, owner_alive=True):
    if type(decoder) is not HealthDecoder:raise ValueError('recorder155_decoder')
    return Snapshot(received_us, checks, decoder.decode(raw,challenge,sent_us,received_us),owner_alive)


class PayloadJournal:
    """One exclusive bounded file; reserve before IO, poison on any IO failure."""
    def __init__(self, root, job, byte_limit=MAX_BYTES):
        root = Path(root).absolute()
        if (not root.is_dir() or any(p.is_symlink() for p in (root,*root.parents))
                or type(job) is not str or not re.fullmatch('[a-f0-9]{32}',job)
                or type(byte_limit) is not int or not MAX_FRAME*4 <= byte_limit <= MAX_BYTES):
            raise ValueError('recorder155_journal_configuration')
        self.path = root/('Recorder155-'+job+'.journal')
        if self.path.exists() or self.path.is_symlink():raise StorageFailure('recorder155_collision')
        self.job,self.limit = job,byte_limit
        self.stream = None
        self.sequence = self.reserved = 0
        self.head = '0'*64
        self.poisoned = self.closed = False

    def poison(self):
        self.poisoned = True
        if self.stream is not None:
            try:self.stream.close()
            except OSError:pass
            self.stream = None

    def sync(self):
        self.stream.flush();os.fsync(self.stream.fileno())

    def append(self, event, kind, attempt, segment, slot, at_us, life_head, value=None):
        if self.poisoned or self.closed:raise StorageFailure('recorder155_closed')
        if event not in EVENTS or kind not in KINDS or type(life_head) is not str or not HASH.fullmatch(life_head):raise ValueError('recorder155_enum')
        for number in (attempt,segment,slot,at_us):uint(number)
        if event == 'prepared':payload(kind,value)
        elif value is not None:raise ValueError('recorder155_unexpected_payload')
        frame = dict(schema=SCHEMA,job=self.job,sequence=self.sequence+1,previous=self.head,event=event,
                     kind=kind,attempt=attempt,segment=segment,slot=slot,at_us=at_us,life_head=life_head,payload=value)
        raw = canonical(frame);head = hashlib.sha256(raw).hexdigest()
        line = raw+b'\t'+head.encode()+b'\n'
        if len(line) >= MAX_FRAME or self.reserved+len(line) > self.limit:
            self.poison();raise StorageFailure('recorder155_capacity')
        self.reserved += len(line)
        try:
            if self.stream is None:self.stream = self.path.open('xb',buffering=0)
            if self.stream.write(line) != len(line):raise OSError('short_write')
            self.sync()
        except OSError:
            self.poison();raise StorageFailure('recorder155_write') from None
        self.sequence += 1;self.head = head
        return head

    def close(self):
        try:
            if self.stream is not None:self.stream.close()
            self.stream = None;self.closed = True
        except OSError:
            self.poison();raise StorageFailure('recorder155_close') from None


class Recorder:
    def __init__(self, supervisor, journal, *, enabled=False):
        if (type(supervisor) is not Supervisor or type(journal) is not PayloadJournal or type(enabled) is not bool
                or supervisor.state != 'off' or supervisor.ledger.job != journal.job or journal.sequence
                or journal.closed or journal.poisoned
                or supervisor.life.journal.job_limit+journal.limit+SUP_FRAME*SUP_FRAMES > MAX_JOB):raise ValueError('recorder155_configuration')
        self.supervisor,self.journal,self.enabled = supervisor,journal,enabled
        self.pending = self.context_ref = None
        self.attempt = self.published = 0
        self.fault = None

    def start(self, snapshot):
        if not self.enabled or self.journal.closed or self.journal.poisoned:return False
        self._install(snapshot)
        return self.supervisor.start(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive)

    def _install(self, snapshot):
        if type(snapshot) is not Snapshot:raise ValueError('recorder155_snapshot')
        if (type(snapshot.health) is not Observation or type(snapshot.health.observed_us) is not int
                or snapshot.health.observed_us < 0 or snapshot.health.token != self.journal.job):
            raise ValueError('recorder155_bound_health_required')
        self.supervisor.helper.report = snapshot.health

    def _guard(self, snapshot):
        self._install(snapshot)
        return (self.supervisor.observe(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive)
                and self.supervisor.life.state is State.RECORDING)

    def _append(self, event, snapshot, value=None):
        kind,segment,slot = self.pending if self.pending is not None else ('none',self.supervisor.life.journal.segment,0)
        return self.journal.append(event,kind,self.attempt,segment,slot,snapshot.at_us,self.supervisor.life.journal.head,value)

    def _fail(self, snapshot, cause):
        self.fault = cause
        life = self.supervisor.life
        interrupted = life.state is State.INTERRUPTED and self.supervisor.state == 'active' and cause == 'guard_or_helper'
        if not interrupted:self.supervisor.stop(snapshot.at_us,snapshot.checks)
        snapshot = replace(snapshot,at_us=self.supervisor.last)
        try:
            if self.pending is not None and not self.journal.poisoned:self._append('abort',snapshot)
            self.pending = self.context_ref = None
            if not interrupted and not self.journal.poisoned:
                self._append('end',snapshot);self.journal.close()
        except StorageFailure:self.journal.poison()
        return False

    def _read(self, source, kind):
        item = source.peek(kind)
        if not self._guard(item.before):return None,item.before
        source.read(kind)
        if not self._guard(item.after):return None,item.after
        return item,item.after

    def _operation(self, source, final, kind):
        if not self.enabled or self.supervisor.state in ('off','stopped') or self.journal.closed or self.journal.poisoned:return False
        if type(source) is not InventedSource or type(final) is not Snapshot:raise ValueError('recorder155_source')
        marker = final
        try:
            first = source.peek('context' if kind == 'context' else 'clock_before').before
            marker = first
            if not self._guard(first):
                if self.supervisor.state == 'waiting_ready':return False
                return self._fail(first,'guard_or_helper')
            life = self.supervisor.life
            if kind == 'triple':
                if self.context_ref is None or self.context_ref[:2] != (life.journal.segment,life.context_at):return False
                if not self.supervisor.begin_triple(first.at_us,first.checks,owner_alive=first.owner_alive):return False
            elif not life.context_due(first.at_us):return False
            self.attempt += 1
            self.pending = (kind,life.journal.segment,life.pending or 0)
            self._append('begin',first)
            values = []
            reads = []
            for query in (('context',) if kind == 'context' else ('clock_before','quote','clock_after')):
                marker = source.peek(query).before
                item,marker = self._read(source,query)
                if item is None:return self._fail(marker,'guard_or_helper')
                values.append(item.value);reads.append(item)
            if kind == 'triple':
                for read in (reads[0],reads[-1]):
                    uint(read.value)
                    if not read.before.at_us <= read.value <= read.after.at_us:raise ValueError('recorder155_marker_outside_read')
            value = values[0] if kind == 'context' else dict(before_us=values[0],quote=values[1],after_us=values[2],context_ref=self.context_ref[2])
            payload(kind,value)
            self._append('prepared',marker,value)
            marker = final
            if not self._guard(final):return self._fail(final,'guard_or_helper')
            ok = (self.supervisor.record_context(final.at_us,final.at_us,final.checks,final.checks,owner_before=final.owner_alive,owner_after=final.owner_alive)
                  if kind == 'context' else self.supervisor.finish_triple(final.at_us,final.checks,owner_alive=final.owner_alive))
            if not ok:return self._fail(final,'guard_or_helper')
            acknowledgement = self._append('commit',final)
            if kind == 'context':self.context_ref = (life.journal.segment,life.context_at,acknowledgement)
            else:self.published += 1
            self.pending = None
            return True
        except StorageFailure:
            self.journal.poison();return self._fail(marker,'storage_error')
        except (OSError,ValueError):return self._fail(marker,'source_or_payload_error')

    def context(self, source, final):return self._operation(source,final,'context')

    def poll(self, source, final):return self._operation(source,final,'triple')

    def retry(self, snapshot):
        if not self.enabled or self.journal.poisoned or self.journal.closed:return False
        self._install(snapshot)
        result = self.supervisor.retry(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive)
        if result:self.context_ref = None;self.fault = None
        return result

    def stop(self, snapshot):
        if not self.enabled or self.journal.closed or self.supervisor.state in ('off','stopped'):return False
        if type(snapshot) is not Snapshot:raise ValueError('recorder155_snapshot')
        return self._fail(snapshot,'explicit_stop')

    def snapshot(self):
        return dict(schema=SCHEMA+'_status',enabled=self.enabled,published_triples=self.published,
                    pending_payload=self.pending is not None,payload_poisoned=self.journal.poisoned,fault=self.fault,
                    supervisor=self.supervisor.snapshot(),invented_only=True,native_source_available=False,
                    native_helper_launched=False,actual_account_queried=False,actual_quotes_read=False,
                    collection_dates=None,resume_available=False,**DENIED)


def inspect(raw, segments, supervisor_raw):
    """Independent three-journal join. Only matching payload ACKs publish quotes."""
    if type(raw) is not bytes or len(raw) > MAX_BYTES:raise ValueError('recorder155_input')
    life = inspect_segments(segments) if segments else None
    supervision = inspect_ledger(supervisor_raw,segments)
    refs = {'0'*64:dict(segment=0,committed_sequence=0,event=None,at_us=0)}
    first_supervision = strict_json(supervisor_raw.split(b'\n',1)[0].rsplit(b'\t',1)[0],MAX_FRAME)
    job = first_supervision['job']
    for segment in segments:
        for line in segment.split(b'\n')[:-1]:
            body,head = line.rsplit(b'\t',1);row = strict_json(body,MAX_FRAME)
            refs[head.decode()] = row;job = row['job']
    lines = raw.split(b'\n');tail = lines.pop()
    if len(tail) >= MAX_FRAME:raise ValueError('recorder155_tail')
    head = '0'*64;pending = None;attempt = 0;last = 0;ended = False
    contexts = {};quotes = [];used = set();previous_source = None;repeats = reversals = 0
    for sequence,line in enumerate(lines,1):
        if not 0 < len(line) < MAX_FRAME or ended:raise ValueError('recorder155_frame')
        try:body,checksum = line.rsplit(b'\t',1)
        except ValueError:raise ValueError('recorder155_frame') from None
        row = strict_json(body,MAX_FRAME)
        fields(row,('schema','job','sequence','previous','event','kind','attempt','segment','slot','at_us','life_head','payload'))
        if canonical(row) != body or hashlib.sha256(body).hexdigest().encode() != checksum:raise ValueError('recorder155_digest')
        for key in ('sequence','attempt','segment','slot','at_us'):uint(row[key])
        if (row['schema'] != SCHEMA or row['job'] != job or row['sequence'] != sequence or row['previous'] != head
                or row['event'] not in EVENTS or row['kind'] not in KINDS or row['at_us'] < last
                or type(row['life_head']) is not str or row['life_head'] not in refs):raise ValueError('recorder155_binding')
        ref = refs[row['life_head']]
        if ref['at_us'] > row['at_us']:raise ValueError('recorder155_future_lifecycle')
        event = row['event']
        if event == 'begin':
            if pending is not None or row['attempt'] != attempt+1 or row['kind'] == 'none' or row['segment'] != ref['segment']:
                raise ValueError('recorder155_begin')
            if row['kind'] == 'triple' and (ref['event'] != 'triple_begin' or ref['sequence'] != row['slot']):raise ValueError('recorder155_begin_ref')
            if row['kind'] == 'context' and row['slot'] != 0:raise ValueError('recorder155_context_slot')
            pending = dict(begin=row,prepared=None);attempt += 1
        elif event == 'end':
            if (pending is not None or row['kind'] != 'none' or row['slot'] or row['attempt'] != attempt
                    or row['segment'] != ref['segment'] or row['life_head'] != (life['head_sha256'] if life else '0'*64)
                    or life and len(quotes) != life['committed_sequence_present']):
                raise ValueError('recorder155_end')
            if not supervision['stopped_record_present']:raise ValueError('recorder155_unstopped_end')
            ended = True
        else:
            if pending is None or any(row[k] != pending['begin'][k] for k in ('attempt','kind','segment','slot')):raise ValueError('recorder155_attempt')
            if event == 'prepared':
                if pending['prepared'] is not None or row['life_head'] != pending['begin']['life_head']:raise ValueError('recorder155_prepare')
                payload(row['kind'],row['payload']);pending['prepared'] = row
                if row['kind'] == 'triple' and (row['payload']['before_us'] < pending['begin']['at_us'] or row['payload']['after_us'] > row['at_us']):
                    raise ValueError('recorder155_marker_bracket')
            elif event == 'commit':
                if pending['prepared'] is None or row['life_head'] in used or ref['segment'] != row['segment'] or ref['at_us'] != row['at_us']:
                    raise ValueError('recorder155_commit')
                value = pending['prepared']['payload']
                if row['kind'] == 'context':
                    if ref['event'] != 'context':raise ValueError('recorder155_context_ref')
                    contexts[checksum.decode()] = row['segment']
                else:
                    if (ref['event'] != 'triple_commit' or ref['committed_sequence'] != row['slot'] or row['slot'] != len(quotes)+1
                            or contexts.get(value['context_ref']) != row['segment']):raise ValueError('recorder155_quote_ref')
                    label = value['quote']['source_label']
                    repeats += int(previous_source == label)
                    reversals += int(previous_source is not None and label < previous_source)
                    previous_source = label;quotes.append(value)
                used.add(row['life_head']);pending = None
            elif event == 'abort':pending = None
        if event != 'prepared' and row['payload'] is not None:raise ValueError('recorder155_unexpected_payload')
        head = checksum.decode();last = row['at_us']
    if tail and ended:raise ValueError('recorder155_tail_after_end')
    total = 0 if life is None else life['committed_sequence_present']
    return dict(schema=SCHEMA+'_inspection',frames=len(lines),ended=ended,published_triples=len(quotes),
                pending_payload=pending is not None,unpublished_lifecycle_commits=total-len(quotes),
                lifecycle_pending=False if life is None else life['pending_triple'],
                lifecycle_final_close_present=False if life is None else life['final_close_present'],
                trailing_partial_bytes=len(tail),context_count=len(contexts),adjacent_source_repeats=repeats,
                source_reversals=reversals,quotes=quotes,resume_available=False,durability_ack_proven=False,
                invented_only=True,**DENIED)
