"""Fresh no-market diagnostic integration; actual account guards unchanged."""
import copy
import ctypes as C
from ctypes import wintypes as W
import json
import math
import time
from .native_pipe_054 import Session054
from .native_pipe_049 import Readiness049 as Readiness057
from .native_pipe_048 import require_interactive,date_guard
from .clock_observer_042 import unique_pairs
from .windows_pipe_047 import OVERLAPPED, PipeRejected, _PENDING
from .windows_pipe_diagnostics_056 import DiagnosticWindowsPipe056,error_category,duration,ERRORS,REASONS
from .transport_diagnostics_053 import serve,validate_report

PREFIX='FXDL_PIPE057 '
STEPS=('disabled','enabled','repeat')

def validate_runtime_authorization(r,preparation_sha256,plan_sha256):
    expected=dict(version='native_runtime_057_v1',runtime_authorized=True,preparation_sha256=preparation_sha256,
        plan_sha256=plan_sha256,phase='57000000000000000000000000000001',date='2026-10-07',
        maximum_sdk_connections=1,maximum_script_arms=3,maximum_grants=1,maximum_deployments=1,
        maximum_session_seconds=900,maximum_io_ms=2000,maximum_drain_ms=1000)
    if type(r) is not dict or set(r)!=set(expected):raise ValueError('runtime_authorization_rejected')
    for k,v in expected.items():
        if type(r[k]) is not type(v) or r[k]!=v:raise ValueError('runtime_authorization_rejected')
    return r

def parse_record(text):
    if type(text) is not str or len(text)>2048 or not text.startswith(PREFIX):raise ValueError('fixture_prefix_rejected')
    try:
        r=json.loads(text[len(PREFIX):],object_pairs_hook=unique_pairs)
        keys={'version','reason_code','requests','receipt_valid','reply_bytes','decode_reason',
              'read_error_category','read_elapsed_us','read_timing','quote_reads','orders'}
        if type(r) is not dict or set(r)!=keys or r['version']!='pipe_fixture_057_v1':raise ValueError()
        if type(r['receipt_valid']) is not bool or any(type(r[k]) is not int for k in keys-{'version','receipt_valid'}):raise ValueError()
        if r['requests'] not in (0,1) or not 0<=r['reason_code']<=24 or not 0<=r['reply_bytes']<=85 or not -1<=r['decode_reason']<=14:raise ValueError()
        if r['quote_reads']!=0 or r['orders']!=0 or r['receipt_valid']!=(r['reason_code']==0):raise ValueError()
        attempted=r['read_error_category']!=-1
        if r['read_error_category'] not in (-1,0,2,3,4,5,6,7) or r['read_timing'] not in (-1,0,1):raise ValueError()
        if not -1<=r['read_elapsed_us']<=900000000:raise ValueError()
        if not attempted:
            if (r['read_timing'],r['read_elapsed_us'],r['reply_bytes'],r['decode_reason'])!=(-1,-1,0,-1):raise ValueError()
        else:
            if r['requests']!=1 or r['read_timing']==-1 or (r['read_elapsed_us']==-1)!=(r['read_timing']==1):raise ValueError()
        if r['reason_code'] in (0,23,24):
            if not attempted or r['decode_reason']<0 or (r['reply_bytes']!=84)!=(r['decode_reason']==1):raise ValueError()
            if r['reason_code']==23 and r['decode_reason']==0:raise ValueError()
            if r['reason_code'] in (0,24) and r['decode_reason']!=0:raise ValueError()
            diag_ok=r['read_error_category']==0 and r['read_timing']==0 and r['read_elapsed_us']<900000000
            if r['reason_code']==0 and not diag_ok or r['reason_code']==24 and diag_ok:raise ValueError()
        elif r['decode_reason']!=-1:raise ValueError()
        if r['requests']==0 and attempted:raise ValueError()
        return r
    except Exception:raise ValueError('fixture_schema_rejected') from None

def records_from_log(raw):
    if type(raw) is not bytes or len(raw)>1048576 or len(raw)%2:raise ValueError('fixture_log_bound_rejected')
    rows=[]
    for line in raw.decode('utf-16-le',errors='strict').splitlines():
        if PREFIX in line:
            if line.count(PREFIX)!=1:raise ValueError('fixture_log_ambiguous')
            rows.append(parse_record(line[line.index(PREFIX):]))
    return rows

class Session057(Session054):
    def __init__(self,**kwargs):
        super().__init__(**kwargs);self.rejected=False
    def arm(self,step):
        if self.rejected:raise ValueError('fixture_order_or_budget_rejected')
        return super().arm(step)
    def collect(self,rows):
        self.remaining_ms();self.require_saved(self.pending)
        if len(rows)!=1:raise ValueError('exactly_one_fixture_record_required')
        r=parse_record(PREFIX+json.dumps(rows[0]))
        expected={'disabled':(17,0,False,0,-1),'enabled':(0,1,True,84,0),'repeat':(20,0,False,0,-1)}[self.pending]
        self.records.append(r);self.pending=None;self.pending_saved=False
        if tuple(r[k] for k in ('reason_code','requests','receipt_valid','reply_bytes','decode_reason'))!=expected:
            self.rejected=True
            raise ValueError('native_fixture_outcome_rejected')
        return r

class ManualWindowsPipe057(DiagnosticWindowsPipe056):
    def io(self,*args,**kwargs):
        result=super().io(*args,**kwargs)
        if not self.last_io['event_closed'] or self.last_io['pending_retained']:
            raise PipeRejected('close_result_rejected')
        return result

    def connect_until(self,handle,deadline,stop,clock=time.monotonic):
        """Reviewed049 derivative: categories and conservative completion proof."""
        self.last_connect=None
        now=clock()
        if not math.isfinite(now) or not math.isfinite(deadline) or not 0<deadline-now<=900 or stop.is_set():
            raise PipeRejected('manual_connect_deadline_rejected')
        started=self._now();event=None;overlap=None;unresolved=False;closed=False;failure=None
        submit='not_attempted';event_category='unknown';close_category='not_attempted';completion='not_attempted';cancel='not_attempted';drain='not_attempted';wait_category='not_attempted';waits=0
        count=W.DWORD()
        try:
            event=self.event(None,True,False,None)
            error=self._error() if not event else None
            event_category='ok' if event else error_category(error)
            if not event:raise PipeRejected('event_create_rejected')
            overlap=OVERLAPPED();overlap.hEvent=event
            ok=self.connect(handle,C.byref(overlap));error=self._error() if not ok else None
            submit='ok' if ok else error_category(error)
            if ok or error==535:
                if stop.is_set() or clock()>=deadline:raise PipeRejected('manual_connect_deadline_rejected')
                return
            if error!=997:raise PipeRejected('io_operation_rejected')
            unresolved=True;last=now
            while True:
                now=clock()
                expired=not math.isfinite(now) or now<last or now>=deadline or stop.is_set() or waits>=900001
                if expired:
                    ok=self.cancel(handle,C.byref(overlap));error=self._error() if not ok else None
                    cancel='ok' if ok else error_category(error)
                    status=self.wait(event,1000);error=self._error() if status==0xffffffff else None
                    drain='ok' if status==0 else 'timeout' if status==258 else error_category(error)
                    if status!=0:raise PipeRejected('cancellation_not_drained')
                    ok=self.result(handle,C.byref(overlap),C.byref(count),False);error=self._error() if not ok else None
                    completion='ok' if ok else error_category(error)
                    unresolved=not ok and error not in (109,232,233,234,995)
                    if unresolved:raise PipeRejected('cancellation_not_drained')
                    raise PipeRejected('manual_connect_cancelled_or_expired')
                last=now;waits+=1
                status=self.wait(event,max(1,min(100,int((deadline-now)*1000))))
                error=self._error() if status==0xffffffff else None
                wait_category='ok' if status==0 else 'timeout' if status==258 else error_category(error)
                if status==0:
                    ok=self.result(handle,C.byref(overlap),C.byref(count),False);error=self._error() if not ok else None
                    completion='ok' if ok else error_category(error)
                    unresolved=not ok and error not in (109,232,233,234,995)
                    if not ok:raise PipeRejected('io_completion_rejected')
                    if stop.is_set() or clock()>=deadline:raise PipeRejected('manual_connect_deadline_rejected')
                    return
                if status!=258:
                    # Preserve the observed failed-wait category; cancel next iteration.
                    drain=error_category(error);stop.set()
        except Exception as exc:
            allowed=REASONS|{'manual_connect_deadline_rejected','manual_connect_cancelled_or_expired'}
            failure=exc.args[0] if isinstance(exc,PipeRejected) and len(exc.args)==1 and type(exc.args[0]) is str and exc.args[0] in allowed else 'unexpected_failure'
            raise PipeRejected(failure) from None
        finally:
            if unresolved:_PENDING.append((overlap,event,None,handle))
            elif event:
                try:
                    closed=bool(self.close(event));error=self._error() if not closed else None
                    close_category='ok' if closed else error_category(error)
                except Exception:closed=False;close_category='unknown'
            try:elapsed,timing=duration(started,self._now(),901000000)
            except Exception:elapsed,timing=None,'clock_invalid'
            self.last_connect=dict(version='manual_connect_057_v1',submit_category=submit,completion_category=completion,
                cancel_category=cancel,drain_category=drain,wait_category=wait_category,wait_calls=waits,elapsed_us=elapsed,timing=timing,
                event_category=event_category,close_category=close_category,pending_retained=unresolved,event_closed=closed,reason=failure)
            if failure is None and event and not closed:raise PipeRejected('close_result_rejected')

def validate_operation(r):
    if type(r) is not dict:raise ValueError('windows_diagnostic_schema_rejected')
    categories=set(ERRORS.values())|{'ok','other','unknown','timeout','not_attempted'}
    if r.get('version')=='manual_connect_057_v1':
        keys={'version','submit_category','completion_category','cancel_category','drain_category','wait_category','wait_calls',
              'event_category','close_category','elapsed_us','timing','pending_retained','event_closed','reason'}
        if set(r)!=keys:raise ValueError('windows_diagnostic_schema_rejected')
        if any(type(r[k]) is not str or r[k] not in categories for k in ('event_category','close_category','submit_category','completion_category','cancel_category','drain_category','wait_category')):raise ValueError('windows_diagnostic_schema_rejected')
        if type(r['wait_calls']) is not int or not 0<=r['wait_calls']<=900001:raise ValueError('windows_diagnostic_schema_rejected')
        limit=901000000;reasons=REASONS|{'manual_connect_deadline_rejected','manual_connect_cancelled_or_expired','close_result_rejected'}
    elif r.get('version')=='windows_io_056_v1':
        keys={'version','kind','events','reason','elapsed_us','timing','transferred_bytes','pending_retained','event_closed'}
        if set(r)!=keys or type(r['kind']) is not str or r['kind'] not in ('read','write','connect'):raise ValueError('windows_diagnostic_schema_rejected')
        if type(r['events']) is not list or not 1<=len(r['events'])<=8:raise ValueError('windows_diagnostic_schema_rejected')
        stages={'event_create','submit','wait','cancel','drain_wait','drain_result','completion','event_close'}
        for e in r['events']:
            if type(e) is not dict or set(e)!={'stage','category'} or type(e['stage']) is not str or e['stage'] not in stages or type(e['category']) is not str or e['category'] not in categories:raise ValueError('windows_diagnostic_schema_rejected')
        if r['transferred_bytes'] is not None and (type(r['transferred_bytes']) is not int or not 0<=r['transferred_bytes']<=128):raise ValueError('windows_diagnostic_schema_rejected')
        limit=3000000;reasons=REASONS|{'ok'}
    else:raise ValueError('windows_diagnostic_schema_rejected')
    if r['reason'] is not None and (type(r['reason']) is not str or r['reason'] not in reasons):raise ValueError('windows_diagnostic_schema_rejected')
    if type(r['timing']) is not str or r['timing'] not in ('measured','clock_invalid','over_bound'):raise ValueError('windows_diagnostic_schema_rejected')
    if r['timing']=='measured':
        if type(r['elapsed_us']) is not int or not 0<=r['elapsed_us']<=limit:raise ValueError('windows_diagnostic_schema_rejected')
    elif r['elapsed_us'] is not None:raise ValueError('windows_diagnostic_schema_rejected')
    if any(type(r[k]) is not bool for k in ('pending_retained','event_closed')) or r['pending_retained'] and r['event_closed']:raise ValueError('windows_diagnostic_schema_rejected')
    return r

def serve_diagnostic(pipe,handle,peer,authority,policy,guard,deadline,io_stop,pending):
    operations=[]
    class Trace:
        def connect_until(self,*args):
            try:return pipe.connect_until(*args)
            finally:
                if pipe.last_connect is not None:operations.append(copy.deepcopy(validate_operation(pipe.last_connect)))
        def io(self,*args,**kwargs):
            try:return pipe.io(*args,**kwargs)
            finally:
                if pipe.last_io is not None:operations.append(copy.deepcopy(validate_operation(pipe.last_io)))
        def peer(self,*args):return pipe.peer(*args)
        def close(self,*args):return pipe.close(*args)
    base=validate_report(serve(Trace(),handle,peer,authority,policy,guard,deadline,io_stop,pending=pending))
    base['windows_operations']=operations
    return base

def collect_stopped_record(log,offset,step,attempted,save):
    if step is None or step in attempted:return False
    attempted.add(step);rows=[];count=0;reason=None
    try:
        size=log.stat().st_size
        if size<offset or size-offset>1048576:raise ValueError()
        with log.open('rb') as f:f.seek(offset);raw=f.read(1048577)
        count=len(raw);rows=records_from_log(raw)
    except Exception:reason='stopped_log_evidence_unavailable_or_invalid'
    save(dict(step=step,records=rows,read_bytes=count,stop_reason=reason,sdk_connections=0,quote_reads=0,orders_available=False))
    return True
