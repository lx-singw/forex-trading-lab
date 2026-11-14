from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import itertools
import subprocess
from tempfile import TemporaryDirectory
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from forex_demo_lab.capture_budget_046 import *

UTC=1791312961000

class Clock:
    def __init__(self):self.value=(UTC,1_000_000_000,100_000)
    def __call__(self):return self.value
    def advance(self,ms):self.value=(self.value[0]+ms,self.value[1]+ms*1_000_000,self.value[2]+ms)

class FakeAPI:
    ACCOUNT_TRADE_MODE_DEMO=0
    def __init__(self):
        self.account=SimpleNamespace(trade_mode=0,currency='USD',login=123,server='PRIVATE_SENTINEL')
        self.terminal=SimpleNamespace(connected=True,trade_allowed=False)
        self.symbol=SimpleNamespace(visible=True,currency_base='EUR',currency_profit='USD')
    def account_info(self):return self.account
    def terminal_info(self):return self.terminal
    def symbol_info(self,name):return self.symbol if name=='EURUSD' else None

class CaptureBudget046Tests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'reserved.json';self.clock=Clock()
        self.policy=Policy('a'*32,'b'*64);self.api=FakeAPI();self.rows=[]
        self.guard=private_guard(self.api)
    def journal(self,r):self.rows.append(r);return True
    def start(self,guard=None,journal=None):
        return start_authority(self.path,self.policy,self.clock,guard or self.guard,journal or self.journal)
    def issue(self,a):return a.issue(self.policy.phase,self.policy.digest)
    def client(self,a,enabled=True,quote=lambda:None):
        if not enabled:return 0
        require_guard(self.guard)
        r=self.issue(a)
        require_guard(self.guard)
        utc,_,boot=self.clock()
        if not receipt_valid(r,self.policy,utc,boot):raise PermitRejected('receipt_rejected')
        quote();return 1
    def test_six_manual_launches_allow_only_one(self):
        a=self.start();calls=[];results=[]
        for _ in range(6):
            try:results.append(self.client(a,quote=lambda:calls.append(1)))
            except PermitRejected:results.append(0)
        self.assertEqual(results,[1,0,0,0,0,0]);self.assertEqual(len(calls),1)
    def test_32_simultaneous_requests_issue_exactly_one(self):
        a=self.start();barrier=Barrier(32)
        def request(_):
            barrier.wait(timeout=10)
            try:self.issue(a);return 1
            except PermitRejected:return 0
        with ThreadPoolExecutor(max_workers=32) as pool:results=list(pool.map(request,range(32)))
        self.assertEqual(sum(results),1);self.assertEqual(len(self.rows),1)
    def test_concurrent_startup_cannot_create_two_authorities(self):
        barrier=Barrier(8)
        def startup(_):
            barrier.wait(timeout=10)
            try:self.start();return 1
            except PermitRejected:return 0
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(startup,range(8)))
        self.assertEqual(sum(results),1)
    def test_disabled_has_no_request_or_quote(self):
        a=self.start();self.assertEqual(self.client(a,False,lambda:self.fail('quote')),0)
        self.assertEqual(a.summary()['permissions_consumed'],0);self.assertEqual(self.rows,[])
    def test_closed_helper_has_no_permission(self):
        a=self.start();a.close()
        with self.assertRaises(PermitRejected):self.issue(a)
        self.assertEqual(a.summary(),dict(permissions_consumed=0,closed=True))
    def test_restart_existing_phase_rejected_even_before_any_request(self):
        self.start().close()
        with self.assertRaises(PermitRejected):self.start()
    def test_corrupt_existing_reservation_not_reinitialized(self):
        self.path.write_bytes(b'')
        with self.assertRaises(PermitRejected):self.start()
        self.assertEqual(self.path.read_bytes(),b'')
    def test_missing_reservation_during_request_burns_allowance(self):
        a=self.start();self.path.unlink()
        with self.assertRaisesRegex(PermitRejected,'reservation_missing'):self.issue(a)
        self.assertEqual(a.summary()['permissions_consumed'],1)
    def test_changed_reservation_rejected(self):
        a=self.start();self.path.write_bytes(b'corrupt')
        with self.assertRaises(PermitRejected):self.issue(a)
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_symlink_reservation_never_reused(self):
        target=self.path.with_name('target');target.write_bytes(b'')
        self.path.symlink_to(target)
        with self.assertRaises(PermitRejected):self.start()
        self.assertEqual(target.read_bytes(),b'')
    def test_flush_failure_leaves_phase_consumed(self):
        with patch('forex_demo_lab.capture_budget_046.os.fsync',side_effect=OSError('PRIVATE_SENTINEL')):
            with self.assertRaises(PermitRejected) as error:self.start()
        self.assertNotIn('PRIVATE_SENTINEL',str(error.exception))
        with self.assertRaises(PermitRejected):self.start()
    def test_permission_denial_is_fixed_rejection(self):
        with patch.object(Path,'open',side_effect=PermissionError('PRIVATE_SENTINEL')):
            with self.assertRaises(PermitRejected) as error:self.start()
        self.assertNotIn('PRIVATE_SENTINEL',str(error.exception))
    def test_lost_response_does_not_refund(self):
        a=self.start();self.issue(a) # delivery discarded
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_quote_exception_does_not_refund(self):
        a=self.start()
        def failing_quote():raise OSError('synthetic quote failure')
        with self.assertRaises(OSError):self.client(a,quote=failing_quote)
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_journal_failure_burns_allowance(self):
        a=self.start(journal=lambda r:False)
        with self.assertRaisesRegex(PermitRejected,'journal'):self.issue(a)
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_journal_exception_never_exposes_identity(self):
        def failing(r):raise OSError('PRIVATE_SENTINEL')
        a=self.start(journal=failing)
        with self.assertRaises(PermitRejected) as error:self.issue(a)
        self.assertNotIn('PRIVATE_SENTINEL',str(error.exception))
    def test_wrong_phase_or_policy_consumes_without_permission(self):
        for index,(phase,digest) in enumerate((('c'*32,self.policy.digest),(self.policy.phase,'c'*64))):
            self.path=Path(self.temp.name)/str(index)
            a=self.start()
            with self.assertRaises(PermitRejected):a.issue(phase,digest)
            with self.assertRaises(PermitRejected):self.issue(a)
        self.assertEqual(self.rows,[])
    def test_invalid_policy_and_boolean_ids_rejected(self):
        for phase,digest in ((True,'b'*64),('a'*31,'b'*64),('A'*32,'b'*64),('a'*32,False),('a'*32,'x'*64)):
            with self.subTest(phase=phase,digest=digest),self.assertRaises(PermitRejected):Policy(phase,digest)
    def test_actual_real_and_contest_modes_rejected(self):
        for mode in (1,2,False,'0'):
            self.api.account.trade_mode=mode
            with self.subTest(mode=mode),self.assertRaises(PermitRejected):private_guard(self.api)
    def test_account_connection_algo_and_symbol_failures(self):
        for obj,name,bad in ((self.api.account,'currency','EUR'),(self.api.terminal,'connected',False),
                (self.api.terminal,'trade_allowed',True),(self.api.symbol,'visible',False),
                (self.api.symbol,'currency_base','GBP'),(self.api.symbol,'currency_profit','EUR')):
            old=getattr(obj,name);setattr(obj,name,bad)
            with self.subTest(name=name),self.assertRaises(PermitRejected):private_guard(self.api)
            setattr(obj,name,old)
    def test_identity_change_before_request_rejected(self):
        a=self.start();self.api.account.login+=1
        with self.assertRaises(PermitRejected):self.issue(a)
        self.assertEqual(a.summary()['permissions_consumed'],1)
    def test_identity_change_during_journal_blocks_response(self):
        def change(r):self.api.account.server='CHANGED';return True
        a=self.start(journal=change)
        with self.assertRaises(PermitRejected):self.issue(a)
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_identity_change_after_permission_blocks_client_quote(self):
        a=self.start();r=self.issue(a);self.api.account.login+=1
        self.assertTrue(receipt_valid(r,self.policy,self.clock.value[0],self.clock.value[2]))
        with self.assertRaises(PermitRejected):require_guard(self.guard)
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_non_boolean_guard_fails_closed(self):
        with self.assertRaises(PermitRejected):self.start(guard=lambda:1)
        with self.assertRaises(PermitRejected):self.start()
    def test_expiry_at_exact_boundary_is_rejected(self):
        a=self.start();self.clock.advance(WINDOW_MS)
        with self.assertRaisesRegex(PermitRejected,'session_expired'):self.issue(a)
    def test_clock_reversal_and_discontinuity(self):
        a=self.start();u,m,b=self.clock.value;self.clock.value=(u,m-1,b)
        with self.assertRaisesRegex(PermitRejected,'clock_reversed'):self.issue(a)
    def test_wall_forward_jump_rejected(self):
        a=self.start();u,m,b=self.clock.value;self.clock.value=(u+1001,m,b)
        with self.assertRaisesRegex(PermitRejected,'clock_discontinuity'):self.issue(a)
    def test_date_rollover_is_not_retargeted(self):
        a=self.start();self.clock.value=(UTC+86400000,*self.clock.value[1:])
        with self.assertRaises(PermitRejected):self.issue(a)
    def test_clock_boolean_and_malformed_samples_rejected(self):
        for value in ((UTC,True,1),[UTC,1,1],(UTC,1),(-1,1,1)):
            with self.subTest(value=value),self.assertRaises(PermitRejected):clock_sample(lambda:value)
    def test_late_restarted_or_malformed_receipt_rejected(self):
        a=self.start();r=self.issue(a);u,_,b=self.clock.value
        self.assertTrue(receipt_valid(r,self.policy,u,b))
        self.assertFalse(receipt_valid(r,self.policy,u+2000,b+2000))
        self.assertFalse(receipt_valid(r,self.policy,u,b-1))
        for k,v in (('permission',True),('phase','c'*32),('expires_boot_ms',b+2001),('expires_utc_ms',u-1)):
            wrong=dict(r);wrong[k]=v
            with self.subTest(key=k):self.assertFalse(receipt_valid(wrong,self.policy,u,b))
        self.assertFalse(receipt_valid(dict(r,extra=1),self.policy,u,b))
    def test_summary_journal_reservation_and_response_are_private(self):
        a=self.start();r=self.issue(a)
        public=json.dumps([a.summary(),self.rows,r])+self.path.read_text()
        self.assertNotIn('PRIVATE_SENTINEL',public);self.assertNotIn('login',public);self.assertNotIn('server',public)
    def test_exact_mql_receipt_header_and_500_differential_boundaries(self):
        root=Path(__file__).resolve().parents[1];exe=Path(self.temp.name)/'receipt'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(root/'mt5/Tests/CapturePermit046.cpp'),
            '-o',str(exe)],check=True,capture_output=True,text=True,timeout=30)
        checked=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=5)
        self.assertEqual(json.loads(checked.stdout),dict(receipt_checks=18,passed=True))
        lines=[];expected=[];boot=100000
        for permission,ttl,age,wall_remaining in itertools.product((0,1,2,-1),(0,1,1999,2000,2001),(-1,0,1,1999,2000),(-1,0,1,2000,2001)):
            expiry=UTC+wall_remaining
            lines.append(f'1 1 1 {permission} {boot} {boot+ttl} {expiry} {boot+age} {UTC}')
            r=dict(version=VERSION,phase=self.policy.phase,policy_sha256=self.policy.digest,permission=permission,
                issued_boot_ms=boot,expires_boot_ms=boot+ttl,expires_utc_ms=expiry)
            expected.append(int(receipt_valid(r,self.policy,UTC,boot+age)))
        actual=subprocess.run([str(exe),'--stdin'],input='\n'.join(lines)+'\n',check=True,capture_output=True,text=True,timeout=5)
        self.assertEqual(len(expected),500)
        self.assertEqual([int(x) for x in actual.stdout.splitlines()],expected)

if __name__=='__main__':unittest.main()
