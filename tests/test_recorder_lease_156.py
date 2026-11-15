"""Invented file/health exercises and shared MQL/C++ decisions, no MT5 runtime."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.recorder_lease_156 import Relay, request, number
from test_helper_health_142 import wire, TOKEN, CHALLENGE

ROOT=Path(__file__).resolve().parents[1]


def frame(sequence=1,job=TOKEN,challenge=CHALLENGE):
    return f'FXDL_REQUEST156_V1\t{job}\t{sequence}\t{challenge}\n'.encode('ascii')


class Channel:
    def __init__(self,**changes):self.calls=[];self.changes=changes
    def request(self,operation,challenge):
        self.calls.append((operation,challenge));return wire(challenge=challenge,**self.changes)


class RecorderLease156Tests(unittest.TestCase):
    def test_exact_bound_request(self):
        self.assertEqual(request(frame()),(TOKEN,1,CHALLENGE))
        self.assertEqual(request(frame(512)),(TOKEN,512,CHALLENGE))

    def test_noncanonical_frame_types_sizes_numbers_tokens_and_fields(self):
        bad=[b'',frame().decode(),frame()+b'\n',frame().replace(b'\n',b'\r\n'),frame().replace(b'V1',b'V2'),
             frame(0),frame(513),frame('01'),frame(True),frame(job='A'*32),frame(challenge='x'*32),b'x'*513,
             frame()+b'\x80',frame().replace(b'\t1\t',b'\t+1\t')]
        for raw in bad:
            with self.subTest(raw=repr(raw)[:35]),self.assertRaises(ValueError):request(raw)
        for value in ('9223372036854775808','-1',' 1','1\n',True):
            with self.assertRaises(ValueError):number(value)

    def test_reply_preserves_native_ticks_and_health_bits(self):
        raw=Relay(TOKEN).reply(frame(),wire(),2_000_000,2_010_000)
        self.assertEqual(raw,f'FXDL_REPLY156_V1\t{TOKEN}\t1\t{CHALLENGE}\t1\t100\t120\t255\n'.encode())

    def test_wrong_binding_or_duplicate_request_poison_permanently(self):
        for bad in (frame(2),frame(job='c'*32)):
            relay=Relay(TOKEN)
            with self.assertRaises(ValueError):relay.reply(bad,wire(),2_000_000,2_010_000)
            with self.assertRaisesRegex(ValueError,'poisoned'):relay.reply(frame(),wire(),2_000_000,2_010_000)
        relay=Relay(TOKEN);relay.reply(frame(),wire(),2_000_000,2_010_000)
        with self.assertRaises(ValueError):relay.reply(frame(),wire(),2_000_000,2_010_000)

    def test_negative_health_transferred_as_negative_flags(self):
        for changes in ({'mains':False},{'running':False},{'set_ack':False,'ready_signal':False}):
            raw=Relay(TOKEN).reply(frame(),wire(**changes),2_000_000,2_010_000)
            self.assertNotEqual(raw.split(b'\t')[-1],b'255\n')

    def test_unready_malformed_or_stale_protocol_never_becomes_success(self):
        for raw in (wire(sample_valid=False),wire(token='c'*32),wire(challenge='c'*32),wire(contained=False),b'{}'):
            relay=Relay(TOKEN)
            with self.assertRaises(ValueError):relay.reply(frame(),raw,2_000_000,2_010_000)
            self.assertTrue(relay.poisoned)
        with self.assertRaises(ValueError):Relay(TOKEN).reply(frame(),wire(),2_000_000,3_000_001)

    def test_repeated_sample_keeps_native_age_and_rewrite_rejected(self):
        relay=Relay(TOKEN);relay.reply(frame(),wire(),2_000_000,2_010_000)
        raw=relay.reply(frame(2),wire(owner_tick_ms=620),2_500_000,2_510_000)
        self.assertIn(b'\t1\t100\t620\t255\n',raw)
        with self.assertRaises(ValueError):relay.reply(frame(3),wire(sample_tick_ms=101,owner_tick_ms=621),2_501_000,2_511_000)

    def folder(self,root):
        folder=Path(root)/('Job156-'+TOKEN);folder.mkdir();(folder/'Request0001.txt').write_bytes(frame());return folder

    def test_file_service_writes_one_exclusive_reply(self):
        with tempfile.TemporaryDirectory() as root:
            folder=self.folder(root);channel=Channel();relay=Relay(TOKEN)
            reply=relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertEqual((folder/'Reply0001.txt').read_bytes(),reply);self.assertEqual(channel.calls,[('POLL',CHALLENGE)])
            with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertEqual(len(channel.calls),1)

    def test_existing_output_and_wrong_order_never_poll_or_overwrite(self):
        for cause in ('existing','order','wrong_folder','oversize','binding'):
            with tempfile.TemporaryDirectory() as root:
                folder=self.folder(root);channel=Channel();relay=Relay(TOKEN)
                if cause=='existing':(folder/'Reply0001.txt').write_bytes(b'preserved')
                if cause=='order':relay.last=1
                if cause=='wrong_folder':folder=Path(root)
                if cause=='oversize':(folder/'Request0001.txt').write_bytes(b'x'*513)
                if cause=='binding':(folder/'Request0001.txt').write_bytes(frame(2))
                with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
                self.assertTrue(relay.poisoned);self.assertEqual(channel.calls,[])
                if cause=='existing':self.assertEqual((folder/'Reply0001.txt').read_bytes(),b'preserved')

    def test_fsync_ack_failure_retains_uncertain_file_and_prevents_retry(self):
        with tempfile.TemporaryDirectory() as root:
            folder=self.folder(root);relay=Relay(TOKEN);channel=Channel()
            with patch('forex_demo_lab.recorder_lease_156.os.fsync',side_effect=OSError('invented')):
                with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertTrue((folder/'Reply0001.txt').exists());self.assertTrue(relay.poisoned)
            with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertEqual(len(channel.calls),1)

    def test_reply_creation_race_preserves_existing_bytes_and_poison(self):
        with tempfile.TemporaryDirectory() as root:
            folder=self.folder(root);relay=Relay(TOKEN);channel=Channel()
            def collide(operation,challenge):
                (folder/'Reply0001.txt').write_bytes(b'preserved race');return wire()
            with patch.object(channel,'request',side_effect=collide):
                with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertEqual((folder/'Reply0001.txt').read_bytes(),b'preserved race');self.assertTrue(relay.poisoned)

    def test_short_reply_write_keeps_partial_file_and_never_retries(self):
        original=Path.open
        class ShortFile:
            def __init__(self,file):self.file=file
            def __enter__(self):return self
            def __exit__(self,*args):self.file.close()
            def write(self,value):return self.file.write(value[:-1])
        def opened(path,mode='r',*args,**kwargs):
            file=original(path,mode,*args,**kwargs)
            return ShortFile(file) if mode=='xb' else file
        with tempfile.TemporaryDirectory() as root:
            folder=self.folder(root);relay=Relay(TOKEN);channel=Channel()
            with patch.object(Path,'open',opened):
                with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertFalse((folder/'Reply0001.txt').read_bytes().endswith(b'\n'))
            with self.assertRaises(ValueError):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertEqual(len(channel.calls),1);self.assertTrue(relay.poisoned)

    def test_unexpected_channel_failure_is_poisoned_without_private_message(self):
        with tempfile.TemporaryDirectory() as root:
            folder=self.folder(root);relay=Relay(TOKEN);channel=Channel()
            with patch.object(channel,'request',side_effect=RuntimeError('private invented detail')):
                with self.assertRaisesRegex(ValueError,'^lease156_service_failed$'):relay.service(folder,1,channel,2_000_000,2_010_000)
            self.assertTrue(relay.poisoned);self.assertFalse((folder/'Reply0001.txt').exists())

    def test_symlink_folder_request_or_reply_rejected(self):
        for kind in ('folder','request','reply'):
            with tempfile.TemporaryDirectory() as root:
                folder=self.folder(root);channel=Channel()
                if kind=='folder':
                    target=Path(root)/'target';folder.rename(target);folder.symlink_to(target,target_is_directory=True)
                elif kind=='request':
                    (folder/'Request0001.txt').unlink();target=Path(root)/'target';target.write_bytes(frame());(folder/'Request0001.txt').symlink_to(target)
                else:(folder/'Reply0001.txt').symlink_to(Path(root)/'absent')
                with self.assertRaises(ValueError):Relay(TOKEN).service(folder,1,channel,2_000_000,2_010_000)
                self.assertEqual(channel.calls,[])

    def test_source_scope_and_entry_precede_native_apis(self):
        text=(ROOT/'mt5/Scripts/ForexDemoNativePort156.mq5').read_text()
        entry=text.split('void OnStart()')[1]
        self.assertLess(entry.index('if(!CollectEvidence)'),entry.index('if(!RunGranted156())'))
        self.assertLess(entry.index('if(!RunGranted156())'),entry.index('GetMicrosecondCount()'))
        for forbidden in ('OrderSend','OrderSendAsync','CTrade','CopyRates','CopyTicks','#import','ClockReason107(', 'ContextRun136', 'FILE_COMMON|'):
            self.assertNotIn(forbidden,text)
        self.assertIn('s.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE)',text)
        for function in ('Tick156','Clocks156','Integer156','Double156','Currency156','Sessions156','Margin156','Commissions156'):
            body=text.split('bool '+function+'(')[1].split('\nbool ')[0]
            self.assertIn('Begin156(',body);self.assertIn('After156()',body)
        self.assertIn('FXDL_NATIVE_PORT156_V1',text)


class NativePort156Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('g++') is None:raise RuntimeError('g++ required; shared native guard checks must not be skipped')
        cls.temp=tempfile.TemporaryDirectory();cls.binary=Path(cls.temp.name)/'port156'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'tests/native_port_156.cpp'),'-o',str(cls.binary)],check=True,capture_output=True,text=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def check_case(self,name):
        result=subprocess.run([str(self.binary),name],check=True,capture_output=True,text=True)
        self.assertEqual(result.stdout,f'{name} passed\n')


for case in ('authority','account','deadline','storage','query','freshness','replay','health','restart'):
    setattr(NativePort156Tests,'test_'+case,lambda self,name=case:self.check_case(name))


if __name__=='__main__':unittest.main()
