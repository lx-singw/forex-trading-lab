"""Independent schema, arithmetic, budget and false-gate reconstruction."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/clock-reference-037.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
TARGETS=['https://www.time.gov/','https://www.microsoft.com/','https://www.mql5.com/']
DATE='2026-10-06'


def clock_reason(before,after,previous=None):
    for utc,mono in (before,after):
        if type(utc) is not int or utc<0:return 'invalid_receipt_clock'
        try: date=datetime.fromtimestamp(utc/1000,timezone.utc).date().isoformat()
        except (ValueError,OverflowError,OSError):return 'invalid_receipt_clock'
        if date!=DATE:return 'receipt_outside_declared_date'
        if type(mono) is not int or mono<0:return 'invalid_monotonic_clock'
    if after[0]<before[0] or after[1]<before[1] or previous is not None and (
            before[0]<previous[0] or before[1]<previous[1]):return 'receipt_clock_reversed'
    if abs((after[0]-before[0])*1_000_000-(after[1]-before[1]))>5_000_000_000:
        return 'receipt_clock_discontinuity'
    return None


def independently_assess(row):
    b,a=row['before'],row['after']
    result=dict(usable=False,reason=None,date_utc_ms=None,offset_interval_ms=None,uncertainty_ms=None)
    reason=clock_reason(b,a)
    if reason is None and a[1]-b[1]>10_000_000_000:reason='request_deadline_exceeded'
    if reason is None and row['transport_outcome']!='response':reason=row['transport_outcome']
    status=row['status']
    if reason is None and (type(status) is not int or not 200<=status<300):
        reason='redirect' if type(status) is int and 300<=status<400 else 'http_failure'
    h=row['headers']
    if reason is None and set(h)!={'Date','Age','Cache-Control'}:reason='malformed_headers'
    if reason is None and h['Age'] is not None and (
            not h['Age'].isascii() or not h['Age'].isdigit() or int(h['Age'])!=0):reason='cached_or_invalid_age'
    if reason is None:
        try:
            value=h['Date'];d=parsedate_to_datetime(value)
            assert d.tzinfo is not None and d.utcoffset().total_seconds()==0
            assert d.strftime('%a, %d %b %Y %H:%M:%S GMT')==value
            stamp=int(d.timestamp())*1000;result['date_utc_ms']=stamp
        except Exception:reason='missing_or_invalid_date'
    if reason is None and not b[0]-5000<=result['date_utc_ms']<=a[0]+5000:
        reason='date_outside_fresh_receipt_bounds'
    if reason is None:
        result.update(usable=True,offset_interval_ms=[result['date_utc_ms']-a[0],result['date_utc_ms']+1000-b[0]],
                      uncertainty_ms=a[0]-b[0]+1000)
    else:result['reason']=reason
    return result


def check():
    ledger=API['verify']();capture=sealed(API['OUTPUT']);reservation=sealed(API['RESERVATION'])
    tests=sealed(ROOT/'reports/clock-reference-037-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==522 and tests['new_tests']==24
    assert capture['ledger_sha256']==reservation['ledger_sha256']==sha(API['LEDGER'])
    assert capture['reservation_sha256']==sha(API['RESERVATION'])
    assert ledger['targets']==TARGETS and ledger['declared_date']==reservation['declared_date']==capture['declared_date']==DATE
    assert reservation['maximum_http_requests']==3 and reservation['maximum_quote_reads']==1
    assert set(capture)=={'version','declared_date','requests','windows_time_service','native_connections_attempted',
        'actual_quote_reads','quote','quote_last_error_code','quote_guards_passed','stop_reason','started','completed',
        'fresh_performance_eligible','annual_eligible','orders_available','historical_reads','strategy_replays',
        'raw_labels_normalized','local_clock_certified','comparison','ledger_sha256','reservation_sha256'}
    service=capture['windows_time_service']
    if service is not None:
        assert set(service)=={'available','running','outcome'} and type(service['available']) is bool
        assert service['running'] is None or type(service['running']) is bool
        assert service['outcome'] in ('observed','unavailable','query_failed')
    for flag in ('fresh_performance_eligible','annual_eligible','orders_available','raw_labels_normalized','local_clock_certified'):
        assert capture[flag] is False
    assert capture['historical_reads']==capture['strategy_replays']==0
    assert type(capture['actual_quote_reads']) is int and 0<=capture['actual_quote_reads']<=1
    assert type(capture['native_connections_attempted']) is int and 0<=capture['native_connections_attempted']<=1
    code=capture['quote_last_error_code'];assert code is None or type(code) is int
    requests=capture['requests'];assert len(requests)<=3
    usable=[];elapsed=[];clock_errors=[];previous=capture['started']
    for i,row in enumerate(requests):
        expected={'index','target','before','after','status','headers','transport_outcome','assessment'}
        assert set(row)==expected or row['after'] is None and set(row)==expected-{'assessment'}
        assert row['index']==i and row['target']==TARGETS[i]
        assert row['status'] is None or type(row['status']) is int
        assert row['transport_outcome'] in ('response','timeout','transport_failure','malformed_headers')
        assert set(row['headers'])=={'Date','Age','Cache-Control'}
        for value in row['headers'].values():
            assert value is None or isinstance(value,str) and len(value)<=2048 and all(32<=ord(c)<=126 for c in value)
        if row['after'] is None:
            clock_errors.append('incomplete_request_clock');continue
        derived=independently_assess(row);assert derived==row['assessment']
        reason=clock_reason(row['before'],row['after'],previous)
        if reason:clock_errors.append(reason)
        elapsed.append(row['after'][1]-row['before'][1]);previous=row['after']
        if derived['usable']:usable.append(dict(target=row['target'],**derived))
    span=requests[-1]['after'][1]-requests[0]['before'][1] if requests and requests[-1]['after'] else None
    budget_ok=all(0<=ns<=10_000_000_000 for ns in elapsed) and (span is None or 0<=span<=30_000_000_000)
    if capture['completed'] is not None:
        reason=clock_reason(capture['started'] or capture['completed'],capture['completed'])
        if reason:clock_errors.append(reason)
    if capture['native_connections_attempted']:
        assert len(usable)>=2 and budget_ok and not clock_errors
    q=capture['quote']
    expected=dict(outcome='insufficient_evidence',raw_minus_receipt_ms=None,raw_minus_reference_ms=None,
                  reference_offset_envelope_ms=None)
    if q is not None:
        assert capture['quote_guards_passed'] is True and capture['actual_quote_reads']==1
        assert capture['native_connections_attempted']==1 and capture['stop_reason'] is None
        assert set(q)=={'poll_index','raw_time_msc','bid','ask','received_before_utc_ms','received_after_utc_ms',
            'received_before_monotonic_ns','received_after_monotonic_ns','repeated_snapshot'}
        assert q['poll_index']==0 and q['repeated_snapshot'] is False
        qb=[q['received_before_utc_ms'],q['received_before_monotonic_ns']]
        qa=[q['received_after_utc_ms'],q['received_after_monotonic_ns']]
        assert clock_reason(qb,qa,previous) is None and clock_reason(qa,capture['completed']) is None
        assert type(q['raw_time_msc']) is int and q['raw_time_msc']>0 and abs(q['raw_time_msc']-qa[0])<=86_400_000
        assert all(type(q[k]) in (int,float) and math.isfinite(q[k]) for k in ('bid','ask'))
        assert 0<q['bid']<=q['ask'] and len(usable)>=2
        lo=min(r['offset_interval_ms'][0] for r in usable);hi=max(r['offset_interval_ms'][1] for r in usable)
        qlo=q['raw_time_msc']-qa[0];qhi=q['raw_time_msc']-qb[0];d=[qlo-hi,qhi-lo]
        expected=dict(outcome='agreement' if d[0]<=5000 and d[1]>=-5000 else 'disagreement',
                      raw_minus_receipt_ms=[qlo,qhi],raw_minus_reference_ms=d,reference_offset_envelope_ms=[lo,hi])
    else:assert capture['quote_guards_passed'] is False
    assert capture['comparison']==expected
    # Explicit schema above excludes identities/exception text; production reasons are closed enums.
    allowed={'fewer_than_two_usable_hosts','total_request_budget_exhausted','request_deadline_exceeded',
        'existing_terminal_connection_unavailable','invalid_service_status','invalid_receipt_clock',
        'receipt_outside_declared_date','invalid_monotonic_clock','receipt_clock_reversed','receipt_clock_discontinuity',
        'disconnected','actual_account_not_demo','account_currency_not_usd','algo_trading_enabled',
        'account_changed_or_invalid','quote_unavailable','invalid_quote','raw_label_outside_current_probe_bound',
        'runtime_failure_details_redacted','completion_clock_invalid','ipc_shutdown_failure_details_redacted'}
    assert capture['stop_reason'] is None or capture['stop_reason'] in allowed
    for name in ('reports/fresh-context-033-checks.json','reports/fresh-replication-035-checks.json'):
        assert sealed(ROOT/name)['diagnostic_passed'] is False
    write(ROOT/'reports/clock-reference-037-checks.json',dict(checker_passed=True,
        ledger_sha256=sha(API['LEDGER']),capture_sha256=sha(API['OUTPUT']),reservation_sha256=sha(API['RESERVATION']),
        input_bindings_verified=len(ledger['bindings']),software_tests_passed=522,new_tests=24,
        http_requests=len(requests),usable_references=usable,request_elapsed_ns=elapsed,total_request_span_ns=span,
        observed_request_budgets_passed=budget_ok,clock_errors=clock_errors,
        native_connections_attempted=capture['native_connections_attempted'],actual_quote_reads=capture['actual_quote_reads'],
        windows_time_service=service,comparison=expected,stop_reason=capture['stop_reason'],
        privacy_schema_checked=True,prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,historical_reads=0,strategy_replays=0))
    print(json.dumps(dict(checker_passed=True,http_requests=len(requests),usable_hosts=len(usable),
                         actual_quote_reads=capture['actual_quote_reads'],comparison=expected)))


if __name__=='__main__':check()
