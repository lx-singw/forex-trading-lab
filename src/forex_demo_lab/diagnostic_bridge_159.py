"""Offline invented replay binding to frozen138/140; no native source or orders."""
import os
from pathlib import Path
from .acquisition_lifecycle_138 import Checks, Lifecycle, Policy
from .segment_journal_138 import Journal, DiskStore, StorageFailure, uint
from .supervision_140 import Supervisor, SyntheticHelper, Ledger, Observation
from .recorder_boundary_155 import Snapshot
from .paired_replay_133 import canonical, DENIED
from .recorder_files_157 import write_file
from .diagnostic_source_159 import capture, sha

SCHEMA='invented_diagnostic_bridge159_v1'
ZERO='0'*64
MAX_FRAME=8192
MAX_BYTES=16*MAX_FRAME


def require(value):
    if not value:raise ValueError('bridge159_rejected')


class BindingJournal:
    def __init__(self,root,job,source):
        self.path=Path(root)/'Binding159.journal';self.job=job;self.source=source
        self.head=ZERO;self.sequence=self.reserved=0;self.stream=None;self.closed=self.poisoned=False

    def poison(self):
        self.poisoned=True
        if self.stream is not None:
            try:self.stream.close()
            except OSError:pass
        self.stream=None

    def sync(self):self.stream.flush();os.fsync(self.stream.fileno())

    def append(self,event,at,life,context=None):
        if self.closed or self.poisoned:raise StorageFailure('bridge159_closed')
        uint(at)
        ref=self.source['context_sha256'] if event=='context' else self.source['triple_sha256'] if event in ('begin','prepared','commit','abort') else None
        value=dict(schema=SCHEMA,job=self.job,sequence=self.sequence+1,previous=self.head,event=event,at_us=at,
                   source_sha256=sha(canonical(self.source)),source_ref=ref,context_binding=context,
                   life_head=life.journal.head,segment=life.journal.segment,slot=1 if event in ('begin','prepared','commit','abort') else 0)
        raw=canonical(value);head=sha(raw);line=raw+b'\t'+head.encode()+b'\n'
        if len(line)>MAX_FRAME or self.sequence>=16 or self.reserved+len(line)>MAX_BYTES:
            self.poison();raise StorageFailure('bridge159_capacity')
        self.reserved+=len(line)
        try:
            if self.stream is None:self.stream=os.fdopen(os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb',buffering=0)
            if self.stream.write(line)!=len(line):raise OSError('short_write')
            self.sync()
        except OSError:
            self.poison();raise StorageFailure('bridge159_write') from None
        self.sequence+=1;self.head=head;return head

    def close(self):
        try:
            if self.stream is not None:self.stream.close()
            self.stream=None;self.closed=True
        except OSError:
            self.poison();raise StorageFailure('bridge159_close') from None


class Bridge:
    def __init__(self,output,job,*,enabled=False,budget_us=30_000_000):
        import re
        require(type(enabled) is bool and type(job) is str and re.fullmatch('[a-f0-9]{32}',job) is not None)
        require(type(budget_us) is int and 0<budget_us<=30_000_000)
        self.output=Path(output);self.job=job;self.enabled=enabled;self.budget=budget_us
        self.stage='off';self.fault=None;self.source=None;self.source_folder=None;self.source_job=None
        self.supervisor=self.life=self.journal=None;self.context_binding=None;self.committed=0;self.receipt_ack=False

    def _install(self,snapshot):
        require(type(snapshot) is Snapshot)
        require(type(snapshot.health) is Observation and snapshot.health.token is not None and snapshot.health.observed_us is not None)
        self.supervisor.helper.report=snapshot.health

    def _guard(self,snapshot):
        self._install(snapshot)
        return self.supervisor.observe(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive)

    def _append(self,event):
        return self.journal.append(event,self.supervisor.last,self.life,self.context_binding)

    def _source_stable(self):return capture(self.source_folder,self.source_job)==self.source

    def _receipt(self):
        if self.journal is None or not self.supervisor.ledger.path.exists():return
        value=dict(schema='invented_bridge159_receipt_v1',job=self.job,source_sha256=sha(canonical(self.source)),
                   binding_ack_head=self.journal.head,life_ack_head=self.life.journal.head,supervision_ack_head=self.supervisor.ledger.head,
                   binding_commit_acks=self.committed,binding_close_ack=self.journal.closed and not self.journal.poisoned,
                   publishable=self.stage=='ended' and self.fault is None and self.committed==1 and self.journal.closed and not self.journal.poisoned and not self.life.journal.poisoned and self.supervisor.ledger.closed and not self.supervisor.ledger.poisoned and self.supervisor.snapshot()['cleanup_complete'],
                   fault=self.fault,market_eligible=False,caller_acknowledgement_known=False)
        try:write_file(self.output/'Receipt159.json',canonical(value)+b'\n');self.receipt_ack=True
        except (OSError,ValueError):
            if self.fault is None:self.fault='receipt_write'

    def _fail(self,snapshot,reason):
        self.fault=reason;prior=self.stage;self.stage='failed'
        if self.supervisor is not None:
            checks=snapshot.checks if type(snapshot) is Snapshot and type(snapshot.checks) is Checks else Checks()
            if self.supervisor.state not in ('off','stopped'):self.supervisor.stop(self.supervisor.last,checks)
            if self.journal is not None and not self.journal.poisoned and self.journal.sequence:
                try:
                    if prior in ('pending','prepared'):self._append('abort')
                    self._append('end');self.journal.close()
                except StorageFailure:self.journal.poison()
            self._receipt()
        return False

    def start(self,folder,source_job,snapshot):
        if not self.enabled or self.stage!='off':return False
        try:
            require(type(snapshot) is Snapshot);uint(snapshot.at_us)
            source=capture(folder,source_job)
        except (OSError,ValueError):self.stage='failed';self.fault='source_admission';return False
        self.source,self.source_folder,self.source_job=source,Path(folder),source_job
        try:
            require(self.job!=source_job)
            require(not any(p.is_symlink() for p in (self.output,*self.output.absolute().parents)))
            self.output.mkdir(parents=False,exist_ok=False)
            self.life=Lifecycle(Journal(self.job,lambda token:DiskStore(self.output,token),file_limit=65536,job_limit=1024*1024),Policy(enabled=True,max_elapsed_us=self.budget))
            self.supervisor=Supervisor(self.life,SyntheticHelper(),Ledger(self.output,self.job),enabled=True)
            self.journal=BindingJournal(self.output,self.job,self.source)
            write_file(self.output/'Source159.json',canonical(source)+b'\n')
            self.supervisor.last=snapshot.at_us;self._append('open');self._install(snapshot)
            if not self.supervisor.start(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive) or not self._guard(snapshot):return self._fail(snapshot,'start_guard')
            self.stage='ready';return True
        except (OSError,ValueError,StorageFailure):return self._fail(snapshot,'start_storage')

    def context(self,before,after):
        if self.stage!='ready':return False
        try:
            if not self._guard(before) or not self._guard(after):return self._fail(after,'context_guard')
            if not self.supervisor.record_context(after.at_us,after.at_us,after.checks,after.checks,owner_before=after.owner_alive,owner_after=after.owner_alive):return self._fail(after,'context_lifecycle')
            self.context_binding=self._append('context');self.stage='context';return True
        except (ValueError,StorageFailure):return self._fail(after,'context_storage')

    def begin(self,snapshot):
        if self.stage!='context':return False
        try:
            if not self._guard(snapshot) or not self.supervisor.begin_triple(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive):return self._fail(snapshot,'begin_guard')
            self.stage='pending';self._append('begin');return True
        except (ValueError,StorageFailure):return self._fail(snapshot,'begin_storage')

    def prepare(self,snapshot):
        if self.stage!='pending':return False
        try:
            if not self._guard(snapshot):return self._fail(snapshot,'prepare_guard')
            self._append('prepared');self.stage='prepared';return True
        except (ValueError,StorageFailure):return self._fail(snapshot,'prepare_storage')

    def commit(self,snapshot):
        if self.stage!='prepared':return False
        try:
            if not self._source_stable():return self._fail(snapshot,'source_changed')
            if not self._guard(snapshot) or not self.supervisor.finish_triple(snapshot.at_us,snapshot.checks,owner_alive=snapshot.owner_alive):return self._fail(snapshot,'commit_guard')
            self._append('commit');self.committed=1;self.stage='committed';return True
        except (OSError,ValueError,StorageFailure):return self._fail(snapshot,'commit_storage')

    def finish(self,snapshot):
        if self.stage!='committed':return False
        try:
            if not self._source_stable():return self._fail(snapshot,'source_changed')
            if not self._guard(snapshot):return self._fail(snapshot,'finish_guard')
            self.supervisor.stop(snapshot.at_us,snapshot.checks)
            if self.life.journal.poisoned or self.supervisor.ledger.poisoned or not self.supervisor.ledger.closed or not self.supervisor.snapshot()['cleanup_complete']:return self._fail(snapshot,'finish_storage')
            self._append('end');self.journal.close();self.stage='ended';self._receipt()
            return self.fault is None and self.receipt_ack
        except (OSError,ValueError,StorageFailure):return self._fail(snapshot,'finish_storage')

    def abort(self,snapshot):
        if self.stage in ('off','failed','ended'):return False
        return self._fail(snapshot,'explicit_abort')

    def snapshot(self):
        return dict(schema='invented_bridge159_status_v1',stage=self.stage,fault=self.fault,binding_commit_acks=self.committed,
                    caller_receipt_acknowledged=self.receipt_ack,replay_clock_only=True,market_eligible=False,resume_available=False,**DENIED)
