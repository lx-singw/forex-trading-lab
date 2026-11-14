"""New native proof plus diagnostic integration. No market methods."""
import json
from .native_pipe_048 import Session048,require_interactive,date_guard
from .native_pipe_049 import Readiness049 as Readiness054,ManualWindowsPipe049 as ManualWindowsPipe054
from .clock_observer_042 import unique_pairs
from .transport_diagnostics_053 import serve,validate_report

PREFIX='FXDL_PIPE054 '
STEPS=('disabled','enabled','repeat')

def parse_record(text):
    if type(text) is not str or len(text)>2048 or not text.startswith(PREFIX):raise ValueError('fixture_prefix_rejected')
    try:
        r=json.loads(text[len(PREFIX):],object_pairs_hook=unique_pairs)
        keys={'version','reason_code','requests','receipt_valid','reply_bytes','decode_reason','quote_reads','orders'}
        if type(r) is not dict or set(r)!=keys or r['version']!='pipe_fixture_054_v1':raise ValueError()
        if type(r['receipt_valid']) is not bool or any(type(r[k]) is not int for k in keys-{'version','receipt_valid'}):raise ValueError()
        if r['requests'] not in (0,1) or not 0<=r['reason_code']<=23 or not 0<=r['reply_bytes']<=85 or not -1<=r['decode_reason']<=14:raise ValueError()
        if r['quote_reads']!=0 or r['orders']!=0 or r['receipt_valid']!=(r['reason_code']==0):raise ValueError()
        if r['reason_code'] in (0,23):
            if r['requests']!=1 or r['decode_reason']<0:raise ValueError()
            if (r['reply_bytes']!=84)!=(r['decode_reason']==1) or r['receipt_valid']!=(r['decode_reason']==0):raise ValueError()
        elif r['decode_reason']!=-1 or r['requests']==0 and r['reply_bytes']!=0:raise ValueError()
        return r
    except Exception:raise ValueError('fixture_schema_rejected') from None

def records_from_log(raw):
    if type(raw) is not bytes or len(raw)>1048576 or len(raw)%2:raise ValueError('fixture_log_bound_rejected')
    out=[]
    for line in raw.decode('utf-16-le',errors='strict').splitlines():
        if PREFIX in line:
            if line.count(PREFIX)!=1:raise ValueError('fixture_log_ambiguous')
            out.append(parse_record(line[line.index(PREFIX):]))
    return out

class Session054(Session048):
    def __init__(self,**kw):
        super().__init__(**kw);self.baseline_saved=False;self.pending_saved=False
    def save_baseline(self):
        self.remaining_ms()
        if self.baseline_saved or self.arms:raise ValueError('log_save_order_rejected')
        self.baseline_saved=True
    def arm(self,step):
        self.remaining_ms()
        if not self.baseline_saved or self.pending is not None or len(self.arms)>=3 or step!=STEPS[len(self.arms)] or len(self.arms)!=len(self.records):
            raise ValueError('fixture_order_or_budget_rejected')
        self.arms.append(step);self.pending=step;self.pending_saved=False
    def save_pending(self,step):
        self.remaining_ms()
        if step!=self.pending or self.pending_saved:raise ValueError('log_save_order_rejected')
        self.pending_saved=True
    def require_saved(self,step):
        if step!=self.pending or not self.pending_saved:raise ValueError('log_save_ack_required')
    def collect(self,rows):
        self.remaining_ms();self.require_saved(self.pending)
        if len(rows)!=1:raise ValueError('exactly_one_fixture_record_required')
        r=parse_record(PREFIX+json.dumps(rows[0]))
        expected={'disabled':(17,0,False,0,-1),'enabled':(0,1,True,84,0),'repeat':(20,0,False,0,-1)}[self.pending]
        self.records.append(r);self.pending=None;self.pending_saved=False
        if tuple(r[k] for k in ('reason_code','requests','receipt_valid','reply_bytes','decode_reason'))!=expected:
            raise ValueError('native_fixture_outcome_rejected')
        return r

def serve_diagnostic(pipe,handle,peer,authority,policy,guard,deadline,io_stop,pending):
    return validate_report(serve(pipe,handle,peer,authority,policy,guard,deadline,io_stop,pending=pending))

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
