"""Pure audit of retained084 R2 evidence. Does not execute or repair models."""
from .synchronization_084 import CAPS

COMPLETE={'normal','small_guard'}
CASES=COMPLETE|{'observed_guard','stale','changed_magic','changed_identity','pipe_acl',
    'wrong_error','launch_late','blocked_return','cleanup_failure','interrupted','changed_account','default_off'}
ZERO=('native_invocations','sdk_connections','mt5_runtime_invocations',
    'native_metatrader_compiler_invocations','terminal_deployments','terminal_log_content_reads',
    'market_reads','orders','receipt_permissions')
FALSE=('native_protocol_implemented','native_mql_verified','native_publication_verified',
    'native_launch_ready','latency_guaranteed','runtime_authorized','orders_available',
    'fresh_performance_eligible','annual_eligible','old070_cause_proven')


def need(value):
    if not value: raise ValueError('sync084_audit_rejected')


def number(value,low=0,high=9007199254740991):
    need(type(value) is int and low<=value<=high)


def validate_row084_r3(name,row):
    need(name in CASES and type(row) is dict)
    for key in ZERO: need(type(row[key]) is int and row[key]==0)
    for key in FALSE: need(row[key] is False)
    need(row['dependencies_injected'] is True and row['private_identifiers_exported'] is False)
    for key in ('full_guards','elapsed_ms','publication_count','model_release_calls','factories',
        'model_finish_calls','backend_model_handles_remaining','model_close_attempts'):number(row[key])
    need(row['backend_model_handles_remaining']==0 and row['model_release_calls']<=1)
    need(type(row['modeled_completed']) is bool and row['modeled_completed']==(name in COMPLETE))
    s=row['summary'];need(type(s) is dict and s['dependencies_injected'] is True)
    need(type(s['counts']) is dict and set(s['counts'])==set(CAPS))
    for key,cap in CAPS.items():number(s['counts'][key],0,cap)
    number(s['unconfirmed_handles'])
    need(type(s['release_spent']) is bool)
    need(type(row['guard_spans']) is list and row['full_guards']<=256 and row['guard_cap']==256)
    last=0
    for span in row['guard_spans']:
        need(type(span) is dict and set(span)=={'start','end'})
        number(span['start']);number(span['end'])
        need(last<=span['start']<=span['end']<120000)
        last=span['end']
    gap=row['full_guards']-len(row['guard_spans'])
    if name=='default_off':
        need(gap==0 and row['elapsed_ms']==0 and row['first_failure'] is None)
        need(s['cleanup_confirmed'] is None and not s['release_spent'])
        need(all(row[k]==0 for k in ('full_guards','factories','model_finish_calls','publication_count')))
        need(all(v==0 for v in s['counts'].values()))
        return {'default_off':True,'started_guards':0,'valid_guard_spans':0}
    need(row['model_finish_calls']==1 and s['counts']['cleanup']==1)
    need(type(s['cleanup_confirmed']) is bool)
    if name=='observed_guard':
        # Retained model entered its75th guard; post-guard clock sampling rejected
        #120827ms, so that guard has no valid completed span. Never invent it.
        need(gap==1 and row['full_guards']==75 and len(row['guard_spans'])==74)
        need(row['elapsed_ms']==120827 and row['first_failure']=='rejected')
        need(all(x['end']-x['start']==1611 for x in row['guard_spans']))
        need(last==119216 and not s['release_spent'] and row['model_release_calls']==0)
        need(s['cleanup_confirmed'] is False and s['unconfirmed_handles']==0)
        return dict(default_off=False,started_guards=75,valid_guard_spans=74,
            whole_deadline_exceeded=True,release_attempted=False,
            missing_span_invented=False,exact_native_cause_proven=False)
    need(gap==0)
    if name in COMPLETE:
        need(row['first_failure'] is None and s['cleanup_confirmed'] is True and s['unconfirmed_handles']==0)
        need(row['elapsed_ms']<120000 and row['model_release_calls']==1 and row['publication_count']==3)
        need(row['all_lease_closes_attempted'] is True and row['match']['modeled_match'] is True)
        need(type(row['probes']) is list and len(row['probes'])==6)
        for p,(stage,access) in zip(row['probes'],[(s,a) for s in ('pre','independent','post') for a in ('write','delete')]):
            need((p['stage'],p['access'])==(stage,access))
            for key in ('start','end','guard_end','error','companion_blockers'):number(p[key])
            need(p['start']<=p['end']<=p['guard_end'] and p['companion_blockers']==0)
            need(p['error']==(32 if stage=='independent' else 0))
            need(p['opened'] is (stage!='independent') and p['closed'] is (stage!='independent'))
        need(type(row['frames']) is list and len(row['frames'])==4)
        need([f['kind'] for f in row['frames']]==['ready','release','holding','closed'])
        previous=0
        for f in row['frames']:
            for key in ('sequence','issued_offset_ms','request_completed_offset_ms','validated_offset_ms'):number(f[key])
            need(previous<f['sequence']<=64);previous=f['sequence']
            need(f['request_completed_offset_ms']<=f['issued_offset_ms']<=f['validated_offset_ms']<=f['issued_offset_ms']+2000)
            h=f['original_frame_sha256'];need(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h))
    else: need(row['first_failure'] in ('rejected','interrupted'))
    if name=='cleanup_failure':need(s['cleanup_confirmed'] is False and s['unconfirmed_handles']>0)
    return dict(default_off=False,started_guards=row['full_guards'],valid_guard_spans=len(row['guard_spans']),
        modeled_completed=row['modeled_completed'])


def audit084_r3(evidence):
    need(type(evidence) is dict and type(evidence['cases']) is dict and set(evidence['cases'])==CASES)
    return {name:validate_row084_r3(name,row) for name,row in evidence['cases'].items()}
