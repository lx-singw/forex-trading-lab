"""Bounded manual fixture lifetime and sanitized evidence. No market APIs."""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import json
import math
import time
from threading import Lock
from .windows_pipe_047 import WindowsPipe, OVERLAPPED, PipeRejected, _PENDING
from .clock_observer_042 import unique_pairs
from .clock_observer_042 import runtime_guard

DATE = '2026-10-07'
PREFIX = 'FXDL_PIPE049 '
STEPS = ('disabled', 'enabled', 'repeat')

class Readiness049:
    """Private stable metadata/process guard; no initialization or market methods."""
    def __init__(self, api, peer_reader, expected_peer, terminal_directory):
        self.api, self.peer_reader, self.expected_peer = api, peer_reader, expected_peer
        self.terminal_directory = str(terminal_directory).casefold()
        self.identity = runtime_guard(api)
        info = api.terminal_info()
        if info is None or type(info.data_path) is not str or not info.data_path:
            raise ValueError('terminal_metadata_changed')
        self.data_root = info.data_path
        self.check()

    def check(self):
        if self.peer_reader()!=self.expected_peer:
            raise ValueError('terminal_process_binding_rejected')
        runtime_guard(self.api,self.identity)
        info=self.api.terminal_info()
        if (info is None or type(info.path) is not str or info.path.casefold()!=self.terminal_directory
            or type(info.data_path) is not str or info.data_path.casefold()!=self.data_root.casefold()
            or type(info.build) is not int or info.build!=6244):
            raise ValueError('terminal_metadata_changed')
        # Detect changes during metadata queries, before any permission can follow.
        if self.peer_reader()!=self.expected_peer:
            raise ValueError('terminal_process_binding_rejected')
        return True

def collect_stopped_record(log,offset,step,attempted,save):
    """One offline read after stop, never a second attempt or SDK reconnection."""
    if step is None or step in attempted:return False
    attempted.add(step)
    rows=[];count=0;reason=None
    try:
        size=log.stat().st_size
        if size<offset or size-offset>1048576:raise ValueError('native_log_truncated_or_budget_exceeded')
        with log.open('rb') as f:f.seek(offset);raw=f.read(1048577)
        count=len(raw);rows=records_from_log(raw)
    except Exception:
        reason='stopped_log_evidence_unavailable_or_invalid'
    save(dict(step=step,records=rows,read_bytes=count,stop_reason=reason,
        sdk_connections=0,quote_reads=0,orders_available=False))
    return True

def require_interactive(stream):
    if stream.isatty() is not True:
        raise ValueError('interactive_stdin_required')

class Session049:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + 900
        self.last = self.started
        self._clock_lock = Lock()
        self.arms, self.records, self.pending = [], [], None

    def remaining_ms(self):
        with self._clock_lock:
            now = self.clock()
            if not math.isfinite(now) or now < self.last or now >= self.deadline:
                raise ValueError('session_deadline_or_clock_reversal')
            self.last = now
            return min(900000, int((self.deadline-now)*1000))

    def arm(self, step):
        self.remaining_ms()
        if self.pending is not None or len(self.arms) >= 3 or step != STEPS[len(self.arms)] or len(self.records) != len(self.arms):
            raise ValueError('fixture_order_or_budget_rejected')
        self.arms.append(step)
        self.pending = step

    def collect(self, records):
        self.remaining_ms()
        if self.pending is None or len(records) != 1:
            raise ValueError('exactly_one_fixture_record_required')
        record = parse_record(PREFIX+json.dumps(records[0]))
        expected = {'disabled': (17,0,False), 'enabled': (0,1,True), 'repeat': (20,0,False)}[self.pending]
        # Retain a valid unexpected native outcome before rejecting it.
        self.records.append(record)
        self.pending = None
        if (record['reason_code'],record['requests'],record['receipt_valid']) != expected:
            raise ValueError('native_fixture_outcome_rejected')
        return record

def parse_record(text):
    if type(text) is not str or len(text)>2049 or not text.startswith(PREFIX):
        raise ValueError('fixture_prefix_rejected')
    try:
        r=json.loads(text[len(PREFIX):],object_pairs_hook=unique_pairs)
        keys={'version','reason_code','requests','receipt_valid','quote_reads','orders'}
        if type(r) is not dict or set(r)!=keys or r['version']!='pipe_fixture_049_v1':raise ValueError()
        if any(type(r[k]) is not int for k in ('reason_code','requests','quote_reads','orders')):raise ValueError()
        if type(r['receipt_valid']) is not bool or not 0<=r['reason_code']<=23 or r['requests'] not in (0,1):raise ValueError()
        if r['quote_reads']!=0 or r['orders']!=0:raise ValueError()
        if r['receipt_valid'] != (r['reason_code']==0) or r['receipt_valid'] and r['requests']!=1:raise ValueError()
        return r
    except Exception:raise ValueError('fixture_schema_rejected') from None

def records_from_log(raw):
    if type(raw) is not bytes or len(raw)>1049576 or len(raw)%2:raise ValueError('fixture_log_bound_rejected')
    text=raw.decode('utf-16-le',errors='strict');records=[]
    for line in text.splitlines():
        if PREFIX in line:
            if line.count(PREFIX)!=1:raise ValueError('fixture_log_ambiguous')
            records.append(parse_record(line[line.index(PREFIX):]))
    return records

def date_guard(utc_ms):
    if type(utc_ms) is not int or datetime.fromtimestamp(utc_ms/1000,timezone.utc).date().isoformat()!=DATE:
        raise ValueError('declared_date_expired')

class ManualWindowsPipe049(WindowsPipe):
    def connect_until(self, handle, deadline, stop, clock=time.monotonic):
        """Own OVERLAPPED until completion, including observed cancellation."""
        now=clock()
        if not math.isfinite(deadline) or not 0<deadline-now<=900 or stop.is_set():
            raise PipeRejected('manual_connect_deadline_rejected')
        event=self.event(None,True,False,None)
        if not event:raise PipeRejected('event_create_rejected')
        overlap=OVERLAPPED();overlap.hEvent=event;count=W.DWORD();retain=False
        try:
            ok=self.connect(handle,C.byref(overlap));error=C.get_last_error()
            if ok or error==535:
                if stop.is_set() or clock()>=deadline:raise PipeRejected('manual_connect_deadline_rejected')
                return
            if error!=997:raise PipeRejected('io_operation_rejected')
            last=now
            while True:
                now=clock()
                if stop.is_set() or now>=deadline or now<last:
                    self.cancel(handle,C.byref(overlap))
                    if self.wait(event,1000)!=0:
                        retain=True;_PENDING.append((overlap,event,None,handle))
                        raise PipeRejected('cancellation_not_drained')
                    self.result(handle,C.byref(overlap),C.byref(count),False)
                    raise PipeRejected('manual_connect_cancelled_or_expired')
                last=now
                status=self.wait(event,max(1,min(100,int((deadline-now)*1000))))
                if status==0:
                    if not self.result(handle,C.byref(overlap),C.byref(count),False):raise PipeRejected('io_completion_rejected')
                    if stop.is_set() or clock()>=deadline:raise PipeRejected('manual_connect_deadline_rejected')
                    return
                if status!=258:
                    # A failed wait also needs cancellation and completion proof.
                    stop.set()
        finally:
            if not retain:self.close(event)
