from pathlib import Path
from types import SimpleNamespace as S
from tempfile import TemporaryDirectory
import unittest
import json
from forex_demo_lab.native_pipe_049 import Readiness049,collect_stopped_record,PREFIX
from forex_demo_lab.fresh_data_031 import ProbeRejected

class FakeMetadata:
    ACCOUNT_TRADE_MODE_DEMO=0
    def __init__(self):
        self.terminal=S(connected=True,trade_allowed=False,path='C:/terminal',data_path='C:/data',build=6244)
        self.account=S(trade_mode=0,currency='USD',login=1,server='synthetic-demo')
        self.symbol=S(visible=True,currency_base='EUR',currency_profit='USD')
    def terminal_info(self):return self.terminal
    def account_info(self):return self.account
    def symbol_info(self,name):
        assert name=='EURUSD';return self.symbol

class Readiness049Tests(unittest.TestCase):
    def setUp(self):
        self.api=FakeMetadata();self.peer=(1,2,'image','hash',3,'synthetic-sid');self.current=self.peer
        self.guard=Readiness049(self.api,lambda:self.current,self.peer,'C:/terminal')
    def test_stable_metadata_passes(self):self.assertTrue(self.guard.check())
    def test_real_and_contest_rejected(self):
        for mode in (1,2):
            self.api.account.trade_mode=mode
            with self.assertRaises(ProbeRejected):self.guard.check()
    def test_account_query_unavailable(self):
        self.api.account=None
        with self.assertRaisesRegex(ProbeRejected,'disconnected'):self.guard.check()
    def test_terminal_query_unavailable(self):
        self.api.terminal=None
        with self.assertRaisesRegex(ProbeRejected,'disconnected'):self.guard.check()
    def test_disconnect_rejected(self):
        self.api.terminal.connected=False
        with self.assertRaisesRegex(ProbeRejected,'disconnected'):self.guard.check()
    def test_algo_enabled_rejected(self):
        self.api.terminal.trade_allowed=True
        with self.assertRaises(ProbeRejected):self.guard.check()
    def test_private_account_change_rejected(self):
        self.api.account.login=2
        with self.assertRaises(ProbeRejected):self.guard.check()
    def test_account_currency_change_rejected(self):
        self.api.account.currency='EUR'
        with self.assertRaises(ProbeRejected):self.guard.check()
    def test_instrument_change_rejected(self):
        self.api.symbol.visible=False
        with self.assertRaises(ProbeRejected):self.guard.check()
    def test_running_build_change_rejected(self):
        self.api.terminal.build=6241
        with self.assertRaises(ValueError):self.guard.check()
    def test_data_root_change_rejected(self):
        self.api.terminal.data_path='C:/other'
        with self.assertRaises(ValueError):self.guard.check()
    def test_process_restart_or_image_change_rejected(self):
        for i in range(len(self.peer)):
            changed=list(self.peer);changed[i]='changed';self.current=tuple(changed)
            with self.assertRaises(ValueError):self.guard.check()
    def test_process_changes_during_metadata_query(self):
        def account():self.current=('changed',);return self.api.account
        self.api.account_info=account
        with self.assertRaises(ValueError):self.guard.check()
    def test_stopped_collection_no_sdk_and_only_once(self):
        with TemporaryDirectory() as d:
            log=Path(d)/'native.log';r=dict(version='pipe_fixture_049_v1',reason_code=17,requests=0,receipt_valid=False,quote_reads=0,orders=0)
            log.write_bytes(('private unrelated line\n'+PREFIX+json.dumps(r)).encode('utf-16-le'))
            out=[];attempted=set()
            self.assertTrue(collect_stopped_record(log,0,'disabled',attempted,out.append))
            self.assertFalse(collect_stopped_record(log,0,'disabled',attempted,out.append))
            self.assertEqual(out[0]['records'],[r]);self.assertNotIn('private',json.dumps(out))
    def test_prior_failed_read_never_repeated(self):
        out=[]
        self.assertFalse(collect_stopped_record(Path('missing'),0,'disabled',{'disabled'},out.append))
        self.assertEqual(out,[])
    def test_malformed_stopped_log_fail_closed(self):
        with TemporaryDirectory() as d:
            log=Path(d)/'native.log';log.write_bytes((PREFIX+'{"login":1}').encode('utf-16-le'));out=[]
            collect_stopped_record(log,0,'enabled',set(),out.append)
            self.assertEqual(out[0]['records'],[]);self.assertIsNotNone(out[0]['stop_reason'])
