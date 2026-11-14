from datetime import datetime, timezone
from pathlib import Path
import json
import runpy
import ssl
import tempfile
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch

from forex_demo_lab import clock_reference_037 as c

BASE = int(datetime(2026,10,6,12,tzinfo=timezone.utc).timestamp()*1000)


def row(status=200, date='Tue, 06 Oct 2026 12:00:00 GMT', age=None, after=200):
    return dict(index=0,target=c.TARGETS[0],before=(BASE,0),after=(BASE+after,after*1_000_000),
                status=status,headers={'Date':date,'Age':age,'Cache-Control':'no-cache'},transport_outcome='response')


class Clock:
    def __init__(self): self.ms=BASE; self.ns=0
    def __call__(self):
        self.ms+=10; self.ns+=10_000_000
        return self.ms,self.ns


class API:
    ACCOUNT_TRADE_MODE_DEMO=0
    def __init__(self,clock):
        self.clock=clock; self.calls=0; self.guards=0; self.closed=False; self.mode=0
        self.currency='USD'; self.algo=False; self.connected=True; self.change=False
    def terminal_info(self):
        return N(connected=self.connected,trade_allowed=self.algo)
    def account_info(self):
        self.guards+=1
        return N(trade_mode=self.mode,currency=self.currency,login=999 if self.change and self.guards>1 else 123,
                 server='PRIVATE_SERVER')
    def symbol_info_tick(self,symbol):
        assert symbol=='EURUSD'
        self.calls+=1
        return N(time_msc=self.clock.ms+10_800_000,bid=1.1,ask=1.1001)
    def last_error(self): return (1,'PRIVATE_ERROR')
    def shutdown(self): self.closed=True
    def __getattr__(self,name): raise AssertionError('Forbidden API: '+name)


def scenario(transport=None, api_setup=None, clock=None, service=None):
    clock=clock or Clock(); api=API(clock); connections=[]
    if api_setup: api_setup(api)
    def connect(): connections.append(1); return api
    def success(index,timeout):
        assert 0<timeout<=10
        return {k:v for k,v in row().items() if k in ('status','headers','transport_outcome')}
    result=c.collect(clock,service or (lambda:dict(available=True,running=True,outcome='observed')),
                     transport or success,connect)
    return result,api,connections


class ClockReferenceTests(unittest.TestCase):
    def test_coarse_interval(self):
        r=c.reference(row()); self.assertTrue(r['usable'])
        self.assertEqual(r['offset_interval_ms'],[-200,1000]); self.assertEqual(r['uncertainty_ms'],1200)
    def test_old_date(self):
        self.assertFalse(c.reference(row(date='Tue, 06 Oct 2026 11:59:50 GMT'))['usable'])
    def test_future_date(self):
        self.assertFalse(c.reference(row(date='Tue, 06 Oct 2026 12:00:10 GMT'))['usable'])
    def test_age(self):
        for age in ('1','abc','-1','0.0',''):
            self.assertFalse(c.reference(row(age=age))['usable'])
        self.assertTrue(c.reference(row(age='0'))['usable'])
    def test_redirects_and_errors(self):
        for status in (301,302,403,429,500,True,None):
            self.assertFalse(c.reference(row(status=status))['usable'])
    def test_invalid_dates(self):
        for date in (None,'junk','Tue, 06 Oct 2026 12:00:00 +0300','Tue, 06 Oct 2026 12:00:00 GMT, junk'):
            self.assertFalse(c.reference(row(date=date))['usable'])
    def test_local_reversal(self):
        r=row(); r['after']=(BASE-1,1)
        self.assertEqual(c.reference(r)['reason'],'receipt_clock_reversed')
    def test_monotonic_reversal(self):
        r=row(); r['after']=(BASE+1,-1)
        self.assertEqual(c.reference(r)['reason'],'invalid_monotonic_clock')
    def test_expired_date_zero_calls(self):
        clock=Clock(); clock.ms=BASE+86_400_000
        result,api,connections=scenario(clock=clock)
        self.assertEqual(result['requests'],[]); self.assertEqual(connections,[]); self.assertEqual(api.calls,0)
        clock=Clock()
        def expired_transport(index,timeout):
            clock.ms+=86_400_000; clock.ns+=86_400_000_000_000
            return {k:v for k,v in row().items() if k in ('status','headers','transport_outcome')}
        result,api,connections=scenario(expired_transport,clock=clock)
        self.assertEqual(len(result['requests']),1); self.assertEqual(connections,[]); self.assertEqual(api.calls,0)
    def test_two_host_prerequisite(self):
        def transport(index,timeout):
            r=row(status=200 if index==0 else 403)
            return {k:r[k] for k in ('status','headers','transport_outcome')}
        result,api,connections=scenario(transport)
        self.assertEqual(len(result['requests']),3); self.assertEqual(connections,[])
        self.assertEqual(api.calls,0); self.assertEqual(result['comparison']['outcome'],'insufficient_evidence')
    def test_one_quote_three_requests_and_disagreement(self):
        result,api,connections=scenario()
        self.assertEqual(len(result['requests']),3); self.assertEqual(api.calls,1); self.assertEqual(len(connections),1)
        self.assertTrue(result['quote_guards_passed']); self.assertTrue(api.closed)
        self.assertEqual(result['comparison']['outcome'],'disagreement')
        self.assertFalse(result['orders_available']); self.assertEqual(result['historical_reads'],0)
    def test_actual_account_modes(self):
        for mode in (1,2,True):
            result,api,_=scenario(api_setup=lambda api:setattr(api,'mode',mode))
            self.assertEqual(api.calls,0); self.assertEqual(result['stop_reason'],'actual_account_not_demo')
    def test_account_identity_change(self):
        result,api,_=scenario(api_setup=lambda api:setattr(api,'change',True))
        self.assertIsNone(result['quote']); self.assertEqual(api.calls,0)
    def test_connectivity_currency_algo(self):
        for name,value in (('connected',False),('currency','EUR'),('algo',True)):
            result,api,_=scenario(api_setup=lambda api:setattr(api,name,value))
            self.assertIsNone(result['quote']); self.assertEqual(api.calls,0)
    def test_post_read_identity_rejected(self):
        def setup(api):
            original=api.symbol_info_tick
            def quote(symbol):
                q=original(symbol); api.change=True; return q
            api.symbol_info_tick=quote
        result,api,_=scenario(api_setup=setup)
        self.assertEqual(api.calls,1); self.assertIsNone(result['quote']); self.assertFalse(result['quote_guards_passed'])
    def test_malformed_quote(self):
        for tick in (None,N(time_msc=BASE,bid=2,ask=1),N(time_msc=BASE,bid=float('nan'),ask=2),
                     N(time_msc=BASE+100_000_000,bid=1,ask=2)):
            result,api,_=scenario(api_setup=lambda api:setattr(api,'symbol_info_tick',lambda symbol:tick))
            self.assertEqual(result['actual_quote_reads'],1); self.assertIsNone(result['quote'])
    def test_exception_privacy_and_no_retry(self):
        calls=[]
        def transport(index,timeout): calls.append(index); raise RuntimeError('PRIVATE_SECRET')
        result,api,_=scenario(transport)
        self.assertEqual(calls,[0,1,2]); self.assertNotIn('PRIVATE',json.dumps(result)); self.assertEqual(api.calls,0)
    def test_output_privacy(self):
        result,_,_=scenario()
        text=json.dumps(result)
        for private in ('PRIVATE_SERVER','PRIVATE_ERROR','login','server','password'):
            self.assertNotIn(private,text)
    def test_request_deadline_and_total_budget(self):
        clock=Clock(); calls=[]
        def transport(index,timeout):
            calls.append(index); clock.ms+=31_000; clock.ns+=31_000_000_000
            return {k:v for k,v in row().items() if k in ('status','headers','transport_outcome')}
        result,api,_=scenario(transport,clock=clock)
        self.assertEqual(calls,[0]); self.assertEqual(api.calls,0)
        self.assertEqual(result['stop_reason'],'total_request_budget_exhausted')
        self.assertEqual(result['requests'][0]['assessment']['reason'],'request_deadline_exceeded')
    def test_clock_discontinuity(self):
        r=row(); r['after']=(BASE+6001,1)
        self.assertEqual(c.reference(r)['reason'],'receipt_clock_discontinuity')
    def test_verified_tls_head_headers_and_no_body(self):
        seen=[]
        class Connection:
            def __init__(self,host,timeout,context):
                seen.append((host,timeout,context)); self.closed=False
            def request(self,method,path): seen.append((method,path))
            def getresponse(self):
                return N(status=302,getheaders=lambda:[('Date',row()['headers']['Date']),('Set-Cookie','SECRET')])
            def close(self): seen.append('closed')
        response=c.https_head(0,connection=Connection)
        self.assertEqual(seen[1],('HEAD','/')); self.assertEqual(seen[-1],'closed')
        self.assertEqual(seen[0][2].verify_mode,ssl.CERT_REQUIRED); self.assertTrue(seen[0][2].check_hostname)
        self.assertNotIn('SECRET',json.dumps(response))
        for index in (-1,3,True):
            with self.assertRaises(ValueError): c.https_head(index,connection=Connection)
        class Duplicate(Connection):
            def getresponse(self):
                return N(status=200,getheaders=lambda:[('Date','one'),('Date','two'),('Age','SECRET\n')])
        malformed=c.https_head(1,connection=Duplicate)
        self.assertEqual(malformed['transport_outcome'],'malformed_headers')
        self.assertIsNone(malformed['headers']['Date']); self.assertIsNone(malformed['headers']['Age'])
    def test_child_deadline_no_retry(self):
        root=Path(__file__).resolve().parents[1]; api=runpy.run_path(str(root/'scripts/clock-reference-037.py'))
        import subprocess
        with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('secret',10)) as mock:
            result=api['transport'](1,4.5)
        self.assertEqual(result['transport_outcome'],'timeout'); self.assertEqual(mock.call_count,1)
        self.assertEqual(mock.call_args.kwargs['timeout'],4.5)
    def test_exclusive_output(self):
        root=Path(__file__).resolve().parents[1]; api=runpy.run_path(str(root/'scripts/clock-reference-037.py'))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'original.json'; api['write'](path,dict(a=1)); h=api['sha'](path)
            with self.assertRaises(FileExistsError): api['write'](path,dict(a=2))
            self.assertEqual(api['sha'](path),h); self.assertEqual(api['sealed'](path),dict(a=1))
    def test_comparison_envelope_and_agreement(self):
        q=dict(raw_time_msc=BASE,received_before_utc_ms=BASE,received_after_utc_ms=BASE+200)
        first=row(); second=row(after=400); second['index']=1; second['target']=c.TARGETS[1]
        result=c.compare([first,second],q)
        self.assertEqual(result['reference_offset_envelope_ms'],[-400,1000])
        self.assertEqual(result['raw_minus_reference_ms'],[-1200,400]); self.assertEqual(result['outcome'],'agreement')


if __name__=='__main__': unittest.main()
