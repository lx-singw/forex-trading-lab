"""Injected, bounded diagnostics. No SDK, native initialization or market APIs."""
import struct
import time
from .capture_budget_047 import PermitRejected, Policy
from .capture_wire_047 import decode_request, encode_response
from .windows_pipe_047 import PipeRejected

STAGES=('connect','peer','guard','request_read','request_decode','issue','encode','reply_write',
        'authority_close','pipe_close')
REASONS=frozenset(('ok','unexpected_failure','clock_reversed','session_deadline_exceeded',
    'clock_invalid','cleanup_pending_retained','guard_return_rejected','write_result_rejected',
    'close_result_rejected','summary_rejected','manual_connect_deadline_rejected',
    'manual_connect_cancelled_or_expired','peer_binding_rejected','io_deadline_rejected',
    'event_create_rejected','io_operation_rejected','io_completion_rejected','io_deadline_exceeded',
    'cancellation_not_drained','short_write_rejected','request_length_rejected',
    'request_binding_rejected','response_schema_rejected','permission_unavailable',
    'reservation_missing_or_changed','clock_invalid_or_date_expired','session_expired',
    'clock_discontinuity','private_account_or_instrument_guard_rejected','consumption_journal_rejected',
    'disconnected','actual_account_not_demo','account_currency_not_usd','algo_trading_enabled',
    'account_changed_or_invalid','symbol_not_supported_or_visible','terminal_metadata_changed',
    'terminal_process_binding_rejected'))
LIMIT_NS=900_000_000_000

class DiagnosticRejected(ValueError):pass

def reason_for(exc):
    if isinstance(exc,(PermitRejected,PipeRejected,DiagnosticRejected)) or type(exc) is ValueError:
        token=str(exc)
        if token in REASONS and token!='ok':return token
    return 'unexpected_failure'

def validate_report(r):
    keys={'version','events','stop_reason','cleanup_reason','permissions_consumed',
          'reply_written','closed','pending_retained','quote_reads','orders'}
    if type(r) is not dict or set(r)!=keys or r['version']!='transport_diagnostics_053_v1':
        raise ValueError('diagnostic_schema_rejected')
    for k in ('reply_written','closed','pending_retained'):
        if type(r[k]) is not bool:raise ValueError('diagnostic_schema_rejected')
    for k in ('quote_reads','orders'):
        if type(r[k]) is not int:raise ValueError('diagnostic_schema_rejected')
    if not (type(r['permissions_consumed']) is int and r['permissions_consumed'] in (0,1) or
            r['permissions_consumed'] is None and r['cleanup_reason']=='summary_rejected'):
        raise ValueError('diagnostic_schema_rejected')
    if r['quote_reads']!=0 or r['orders']!=0:
        raise ValueError('diagnostic_schema_rejected')
    if any(r[k] is not None and (type(r[k]) is not str or r[k] not in REASONS-{'ok'}) for k in ('stop_reason','cleanup_reason')):
        raise ValueError('diagnostic_schema_rejected')
    events=r['events']
    if type(events) is not list or not 2<=len(events)<=10:raise ValueError('diagnostic_schema_rejected')
    if [x.get('stage') for x in events[-2:] if type(x) is dict]!=['authority_close','pipe_close']:
        raise ValueError('diagnostic_schema_rejected')
    last=-1
    for e in events:
        if type(e) is not dict or set(e)!={'stage','reason','byte_count','elapsed_us'}:
            raise ValueError('diagnostic_schema_rejected')
        if type(e['stage']) is not str or type(e['reason']) is not str or e['stage'] not in STAGES or STAGES.index(e['stage'])<=last or e['reason'] not in REASONS:
            raise ValueError('diagnostic_schema_rejected')
        last=STAGES.index(e['stage'])
        if type(e['byte_count']) is not int or not 0<=e['byte_count']<=85:
            raise ValueError('diagnostic_schema_rejected')
        if type(e['elapsed_us']) is not int or not 0<=e['elapsed_us']<=900_000_000:
            raise ValueError('diagnostic_schema_rejected')
        if e['stage'] not in ('request_read','encode','reply_write') and e['byte_count']:
            raise ValueError('diagnostic_schema_rejected')
    if r['closed'] and r['pending_retained']:raise ValueError('diagnostic_schema_rejected')
    operations=events[:-2]
    if [e['stage'] for e in operations]!=list(STAGES[:len(operations)]):raise ValueError('diagnostic_schema_rejected')
    bad=[e for e in operations if e['reason']!='ok']
    if len(bad)>1 or bad and bad[0]!=operations[-1] or r['stop_reason']!=(bad[0]['reason'] if bad else None):
        raise ValueError('diagnostic_schema_rejected')
    if r['reply_written']!=(len(operations)==8 and not bad) or r['closed']!=(events[-1]['reason']=='ok'):
        raise ValueError('diagnostic_schema_rejected')
    return r

def serve(pipe,handle,expected,authority,policy,guard,deadline,stop,*,pending=lambda h:False,clock=time.monotonic_ns):
    """One request only; retain uncompleted native IO rather than closing its handle."""
    events=[];failure=None;cleanup=None;reply_written=False;closed=False;retained=False;spent=0
    started=None;last=0
    def sample():
        nonlocal last,started
        now=clock()
        if type(now) is not int or now<0:raise DiagnosticRejected('clock_invalid')
        if started is None:started=now
        if now<last:raise DiagnosticRejected('clock_reversed')
        last=now
        if now-started>=LIMIT_NS:raise DiagnosticRejected('session_deadline_exceeded')
        return now
    def action(stage,fn,count=0):
        nonlocal last
        before=last;why='ok';value=None;n=count
        try:
            before=sample();value=fn();sample()
            if stage in ('request_read','encode'):
                if type(value) is not bytes or len(value)>85:raise DiagnosticRejected('request_length_rejected' if stage=='request_read' else 'response_schema_rejected')
                n=len(value)
            if stage=='guard' and value is not True:raise DiagnosticRejected('guard_return_rejected')
            if stage=='reply_write' and (type(value) is not bytes or value!=b''):raise DiagnosticRejected('write_result_rejected')
        except Exception as exc:
            why=reason_for(exc);raise DiagnosticRejected(why) from None
        finally:
            if why!='ok':
                # Measure failed IO too, without replacing its first fixed reason.
                try:
                    now=clock()
                    if type(now) is int and now>=last:last=now
                except Exception:pass
            events.append(dict(stage=stage,reason=why,byte_count=n,
                elapsed_us=min(900_000_000,max(0,last-before)//1000)))
        return value
    try:
        action('connect',lambda:pipe.connect_until(handle,deadline,stop))
        action('peer',lambda:pipe.peer(handle,'client',expected))
        action('guard',guard)
        raw=action('request_read',lambda:pipe.io(handle,'read',size=57))
        def decode():
            try:return decode_request(raw,policy)
            except PermitRejected:
                # Preserve the old core's burn on a malformed client request.
                try:authority.issue('invalid','invalid')
                except PermitRejected:pass
                raise
        phase,digest=action('request_decode',decode)
        receipt=action('issue',lambda:authority.issue(phase,digest))
        reply=action('encode',lambda:encode_response(receipt))
        action('reply_write',lambda:pipe.io(handle,'write',data=reply),len(reply));reply_written=True
    except Exception as exc:failure=reason_for(exc)
    finally:
        stop.set()
        # Cleanup must run even when the diagnostic clock itself has failed.
        for stage,fn in (('authority_close',authority.close),('pipe_close',None)):
            why='ok'
            try:
                if stage=='authority_close':fn()
                else:
                    retained=True
                    if pending(handle) is not False:raise DiagnosticRejected('cleanup_pending_retained')
                    retained=False;value=pipe.close(handle)
                    if not (value is True or type(value) is int and value==1):raise DiagnosticRejected('close_result_rejected')
                    closed=True
            except Exception as exc:
                why=reason_for(exc)
                if cleanup is None:cleanup=why
            events.append(dict(stage=stage,reason=why,byte_count=0,elapsed_us=0))
        try:
            value=authority.summary()['permissions_consumed']
            if type(value) is not int or value not in (0,1):raise ValueError()
            spent=value
        except Exception:
            spent=None;cleanup='summary_rejected'
    return validate_report(dict(version='transport_diagnostics_053_v1',events=events,stop_reason=failure,
        cleanup_reason=cleanup,permissions_consumed=spent,reply_written=reply_written,closed=closed,
        pending_retained=retained,quote_reads=0,orders=0))

def decode_reason(raw,policy,utc,boot,date_ok=True):
    """Same decisions as the actual pure MQL header, with fixed rejection categories."""
    if type(raw) is not bytes or len(raw)!=84:return 1
    if type(policy) is not Policy:return 2
    if type(utc) is not int or type(boot) is not int or type(date_ok) is not bool:
        raise ValueError('diagnostic_clock_schema_rejected')
    magic,phase,digest,permission,issued,expires,expiry=struct.unpack('<8s16s32sIQQQ',raw)
    if magic!=b'FXDL047R':return 3
    if phase.hex()!=policy.phase:return 4
    if digest.hex()!=policy.digest:return 5
    if permission!=1:return 6
    if issued>9007199254740991 or expires>9007199254740991 or expiry>32535215999999:return 7
    if date_ok is not True:return 8
    if boot<issued:return 9
    if boot>=expires:return 10
    if boot>9007199254740991 or utc<=0 or utc>32535215999999 or expiry<=0:return 11
    if expires-issued>2000:return 12
    if expiry<=utc:return 13
    if expiry-utc>2000:return 14
    return 0

def native_record(raw,policy,utc,boot,date_ok=True):
    """Offline model of the future native closed record, never reads a pipe."""
    if type(raw) is not bytes or len(raw)>85:raise ValueError('native_diagnostic_schema_rejected')
    code=decode_reason(raw,policy,utc,boot,date_ok)
    return validate_native_record(dict(version='native_diagnostics_053_v1',reason_code=0 if code==0 else 23,
        requests=1,receipt_valid=code==0,reply_bytes=len(raw),decode_reason=code,quote_reads=0,orders=0))

def validate_native_record(r):
    keys={'version','reason_code','requests','receipt_valid','reply_bytes','decode_reason','quote_reads','orders'}
    if type(r) is not dict or set(r)!=keys or r['version']!='native_diagnostics_053_v1':
        raise ValueError('native_diagnostic_schema_rejected')
    for k in keys-{'version','receipt_valid'}:
        if type(r[k]) is not int:raise ValueError('native_diagnostic_schema_rejected')
    if type(r['receipt_valid']) is not bool or r['requests']!=1 or r['quote_reads']!=0 or r['orders']!=0:
        raise ValueError('native_diagnostic_schema_rejected')
    if not 0<=r['reply_bytes']<=85 or not 0<=r['decode_reason']<=14:
        raise ValueError('native_diagnostic_schema_rejected')
    if (r['reply_bytes']!=84)!=(r['decode_reason']==1) or r['receipt_valid']!=(r['decode_reason']==0):
        raise ValueError('native_diagnostic_schema_rejected')
    if r['reason_code']!=(0 if r['receipt_valid'] else 23):raise ValueError('native_diagnostic_schema_rejected')
    return r
