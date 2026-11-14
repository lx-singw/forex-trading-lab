"""Two no-market native runs with explicit log-save acknowledgments."""
import json
from .native_pipe_048 import Session048, require_interactive, date_guard
from .native_pipe_049 import Readiness049 as Readiness051, ManualWindowsPipe049 as ManualWindowsPipe051
from .clock_observer_042 import unique_pairs

PREFIX='FXDL_PIPE051 '
STEPS=('enabled','repeat')

def parse_record(text):
    if type(text) is not str or len(text)>2048 or not text.startswith(PREFIX):raise ValueError('fixture_prefix_rejected')
    try:
        r=json.loads(text[len(PREFIX):],object_pairs_hook=unique_pairs)
        if type(r) is not dict or set(r)!={'version','reason_code','requests','receipt_valid','quote_reads','orders'}:raise ValueError()
        if r['version']!='pipe_fixture_051_v1' or type(r['receipt_valid']) is not bool:raise ValueError()
        if any(type(r[k]) is not int for k in ('reason_code','requests','quote_reads','orders')):raise ValueError()
        if not 0<=r['reason_code']<=23 or r['requests'] not in (0,1) or r['quote_reads']!=0 or r['orders']!=0:raise ValueError()
        if r['receipt_valid']!=(r['reason_code']==0) or r['receipt_valid'] and r['requests']!=1:raise ValueError()
        return r
    except Exception:raise ValueError('fixture_schema_rejected') from None

def records_from_log(raw):
    if type(raw) is not bytes or len(raw)>1048576 or len(raw)%2:raise ValueError('fixture_log_bound_rejected')
    records=[]
    for line in raw.decode('utf-16-le',errors='strict').splitlines():
        if PREFIX in line:
            if line.count(PREFIX)!=1:raise ValueError('fixture_log_ambiguous')
            records.append(parse_record(line[line.index(PREFIX):]))
    return records

class Session051(Session048):
    def __init__(self,disabled_proof_valid,**kwargs):
        if disabled_proof_valid is not True:raise ValueError('shared_disabled_proof_required')
        super().__init__(**kwargs)
        self.baseline_saved=False;self.pending_saved=False
    def save_baseline(self):
        self.remaining_ms()
        if self.baseline_saved or self.arms or self.pending is not None:raise ValueError('log_save_order_rejected')
        self.baseline_saved=True
    def arm(self,step):
        self.remaining_ms()
        if (not self.baseline_saved or self.pending is not None or len(self.arms)>=2
            or step!=STEPS[len(self.arms)] or len(self.records)!=len(self.arms)):
            raise ValueError('fixture_order_or_budget_rejected')
        self.arms.append(step);self.pending=step;self.pending_saved=False
    def save_pending(self,step):
        self.remaining_ms()
        if self.pending!=step or self.pending_saved:raise ValueError('log_save_order_rejected')
        self.pending_saved=True
    def require_saved(self,step):
        if self.pending!=step or not self.pending_saved:raise ValueError('log_save_ack_required')
    def collect(self,records):
        self.remaining_ms();self.require_saved(self.pending)
        if len(records)!=1:raise ValueError('exactly_one_fixture_record_required')
        record=parse_record(PREFIX+json.dumps(records[0]))
        expected={'enabled':(0,1,True),'repeat':(20,0,False)}[self.pending]
        self.records.append(record);self.pending=None;self.pending_saved=False
        if (record['reason_code'],record['requests'],record['receipt_valid'])!=expected:raise ValueError('native_fixture_outcome_rejected')
        return record

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
