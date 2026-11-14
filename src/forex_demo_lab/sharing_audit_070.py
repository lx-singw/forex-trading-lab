"""Offline audit of one source-bound069 outcome. No native or SDK APIs."""
import hashlib
import json

from .clock_observer_042 import unique_pairs
from .image_guard_068 import STAGES
from .sharing_runtime_069 import PHASE,LIMITS069,digest
from .mql_sharing_064 import DATE,PHASE as MQL_PHASE,PrivateProof,Probe,match_evidence,parse_record,PREFIX
from .sharing_probe_062 import ProbeRejected

ERRORS=('runner_cleanup_unconfirmed','file_cleanup_unconfirmed','bootstrap_cleanup_unconfirmed',
    'owned_cleanup_unconfirmed','sdk_cleanup_unconfirmed','post_cleanup_clock_rejected',
    'cleanup_budget_rejected','resource_cleanup_unconfirmed')
REASONS=('native_final_audit_rejected','native_runtime_failed_details_redacted',
    'native_cleanup_unconfirmed','native_final_clock_rejected','native_session_incomplete')


def same(actual,expected):
    if type(actual) is not type(expected):return False
    if type(expected) is dict:return set(actual)==set(expected) and all(same(actual[k],v) for k,v in expected.items())
    if type(expected) is list:return len(actual)==len(expected) and all(same(a,b) for a,b in zip(actual,expected))
    return actual==expected


def clean(proof):
    return (type(proof) is dict and proof.get('all_handles_closed') is True and
        proof.get('allocations_released') is True and type(proof.get('unconfirmed_handles')) is int and
        proof['unconfirmed_handles']==0)


def reservation(raw,expected_hash,bindings):
    try:
        if type(raw) is not bytes or not 0<len(raw)<=4096 or hashlib.sha256(raw).hexdigest()!=digest(expected_hash):raise ValueError()
        if set(bindings)!={'source','ex5','terminal','editor','preparation','policy','helper_profile'}:raise ValueError()
        for v in bindings.values():digest(v)
        value=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
        expected=dict(version='sharing_reservation_069_v1',phase=PHASE,mql_phase=MQL_PHASE,date=DATE,
            bindings=bindings,maximum_launches=2,maximum_sdk_connections=1,maximum_log_reads=1,
            maximum_log_bytes=65536,maximum_receipt_permissions=0,orders_available=False)
        if not same(value,expected):raise ValueError()
        return value
    except Exception:raise ProbeRejected('native_reservation_audit_rejected') from None


def audit(r,bindings,raw=None):
    try:
        expected_keys={'completed','stop_reason','stopped_stage','stage_trace','phase','date',
            'preparation_sha256','policy_sha256','helper_profile_sha256','reservation_sha256','counts',
            'sdk_shutdown_called','native_signature_checks_passed','native_private_bootstrap_passed',
            'native_sharing_observed','native_mql_verified','native_publication_verified','orders_available',
            'fresh_performance_eligible','annual_eligible','quote_reads','history_reads','orders','receipt_permissions',
            'script_arms','records','probes','cleanup','bootstrap_cleanup','cleanup_errors','deployment_completed',
            'compiled_source_sha256','compiled_artifact_sha256','elapsed_us'}
        if type(r) is not dict or set(r)!=expected_keys:raise ValueError()
        for k in ('source','ex5','terminal','editor','preparation','policy','helper_profile'):digest(bindings[k])
        if r['phase']!=PHASE or r['date']!=DATE:raise ValueError()
        for key,binding in (('preparation_sha256','preparation'),('policy_sha256','policy'),('helper_profile_sha256','helper_profile')):
            if r[key]!=bindings[binding]:raise ValueError()
        for key in ('quote_reads','history_reads','orders','receipt_permissions'):
            if not same(r[key],0):raise ValueError()
        for key in ('native_mql_verified','native_publication_verified','orders_available','fresh_performance_eligible','annual_eligible'):
            if r[key] is not False:raise ValueError()
        for key in ('completed','sdk_shutdown_called','native_signature_checks_passed',
                'native_private_bootstrap_passed','native_sharing_observed','deployment_completed'):
            if type(r[key]) is not bool:raise ValueError()
        if r['native_sharing_observed']!=r['completed']:raise ValueError()
        trace=r['stage_trace']
        if type(trace) is not list or not 1<=len(trace)<=32:raise ValueError()
        for e in trace:
            if (type(e) is not dict or set(e)!={'stage','started','completed'} or e['stage'] not in STAGES or
                e['started'] is not True or type(e['completed']) is not bool):raise ValueError()
        if r['completed']:
            if r['stop_reason'] is not None or r['stopped_stage'] is not None or not all(e['completed'] for e in trace):raise ValueError()
            if set(e['stage'] for e in trace)!=set(STAGES):raise ValueError()
        elif r['stop_reason'] not in REASONS or r['stopped_stage'] not in (*STAGES,None):raise ValueError()
        if type(r['cleanup_errors']) is not list or any(e not in ERRORS for e in r['cleanup_errors']):raise ValueError()
        if not any(same(r['script_arms'],a) for a in ([],['disabled'],['disabled','enabled'])):raise ValueError()
        if type(r['records']) is not list or len(r['records'])>128 or type(r['probes']) is not list or len(r['probes'])>6:raise ValueError()
        for row in r['records']:parse_record(PREFIX+json.dumps(row))
        for p in r['probes']:
            probe=Probe(**p)
            if probe.stage not in ('pre','independent','post') or probe.access not in ('write','delete'):raise ValueError()
            for k,v in vars(probe).items():
                if k in ('stage','access'):continue
                if k in ('start_boot_ms','end_boot_ms','error','blocking_companion_handles'):
                    if type(v) is not int:raise ValueError()
                elif type(v) is not bool:raise ValueError()
        c=r['counts'];within=None
        if c is None:
            if r['completed'] or raw is not None or r['reservation_sha256'] is not None:raise ValueError()
            if r['stopped_stage']!='preflight' or r['elapsed_us'] is not None:raise ValueError()
            if any(r[k] for k in ('sdk_shutdown_called','native_signature_checks_passed',
                'native_private_bootstrap_passed','deployment_completed','script_arms','records','probes','cleanup_errors')):raise ValueError()
            if any(r[k] is not None for k in ('cleanup','bootstrap_cleanup','compiled_source_sha256','compiled_artifact_sha256')):raise ValueError()
        else:
            if type(c) is not dict or set(c)!=set(LIMITS069) or any(type(v) is not int or v<0 for v in c.values()):raise ValueError()
            within=all(v<=LIMITS069[k] for k,v in c.items())
            if type(r['elapsed_us']) is not int or r['elapsed_us']<0:raise ValueError()
            if c['sdk_connections']>1 or c['sdk_shutdowns']>1 or c['script_arms']!=len(r['script_arms']) or c['script_arms']>2:raise ValueError()
            if c['deployment_directories']>1 or c['deployment_writes']>1 or c['log_reads']>1 or c['log_bytes']>65536:raise ValueError()
            if r['records'] and c['log_reads']!=1:raise ValueError()
            if r['sdk_shutdown_called'] and (c['sdk_connections']!=1 or c['sdk_shutdowns']!=1):raise ValueError()
            if c['sdk_connections']==0 and (c['sdk_shutdowns'] or r['sdk_shutdown_called']):raise ValueError()
            if raw is not None:
                reservation(raw,r['reservation_sha256'],bindings)
                if c['reservation_writes']!=1:raise ValueError()
            else:
                if r['reservation_sha256'] is not None or c['sdk_connections'] or c['native_calls'] or r['script_arms']:raise ValueError()
            for key,binding in (('compiled_source_sha256','source'),('compiled_artifact_sha256','ex5')):
                if r[key] is not None and r[key]!=bindings[binding]:raise ValueError()
            if r['completed']:
                if not within or raw is None or r['elapsed_us']>=900000000 or r['cleanup_errors']:raise ValueError()
                if not all(r[k] for k in ('sdk_shutdown_called','native_signature_checks_passed','native_private_bootstrap_passed','deployment_completed')):raise ValueError()
                if (c['sdk_connections'],c['sdk_shutdowns'],c['script_arms'],c['log_reads'])!=(1,1,2,1):raise ValueError()
                if (c['deployment_directories'],c['deployment_writes'],c['trust_queries'])!=(1,1,1):raise ValueError()
                if not all(c[k]>0 for k in ('native_calls','process_opens','identity_tokens','hash_reads','hash_bytes','sdk_queries')):raise ValueError()
                if not clean(r['cleanup']) or not clean(r['bootstrap_cleanup']):raise ValueError()
                if r['compiled_source_sha256']!=bindings['source'] or r['compiled_artifact_sha256']!=bindings['ex5']:raise ValueError()
                match_evidence(r['records'],[Probe(**p) for p in r['probes']],PrivateProof(True,True,True,True,True,True,True,True,DATE))
        return dict(audit_passed=True,runtime_completed=r['completed'],stopped_stage=r['stopped_stage'],
            counts_within_declared_caps=within,reservation_present=raw is not None,
            sdk_attempts=c['sdk_connections'] if c else 0,script_arms=len(r['script_arms']),
            owned_cleanup_confirmed=all(clean(r[k]) for k in ('cleanup','bootstrap_cleanup') if r[k] is not None),
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
    except Exception:raise ProbeRejected('native_outcome_audit_rejected') from None
