"""Invented filesystem/owner protocol only; no process or MT5 launch."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.native_journal_157 import CAP, Reader, inspect_native
from forex_demo_lab.recorder_files_157 import read_file, write_file, check_files
from forex_demo_lab.recorder_fixture_157 import Clock, Producer, Channel, main
from forex_demo_lab.recorder_runner_157 import Runner
from forex_demo_lab.relay_audit_157 import inspect_job

JOB='a'*32
ROOT=Path(__file__).resolve().parents[1]


def setup(root,mode='clean',failed=False,hold=False,budget=30_000_000):
    clock=Clock();folder=Path(root)/('Job156-'+JOB);producer=Producer(folder,JOB,clock,failed=failed,hold=hold)
    channel=Channel(clock,mode);runner=Runner(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait,budget_us=budget)
    return folder,clock,producer,channel,runner


def rows(raw):return [line.rsplit('\t',1)[0].split('\t') for line in raw.decode('ascii').splitlines()]


def encoded(records):
    chain='0'*64;result=[]
    for record in records:
        payload='\t'.join(map(str,record));chain=hashlib.sha256((chain+'\t'+payload+'\n').encode()).hexdigest().upper()
        result.append(payload+'\t'+chain+'\n')
    return ''.join(result).encode()


class Reader157Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();folder,_,_,_,runner=setup(cls.temp.name)
        assert runner.run()['cause']=='complete';cls.valid=(folder/'NativePort156.txt').read_bytes();cls.records=rows(cls.valid)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def reject(self,records):
        with self.assertRaisesRegex(ValueError,'^native157_rejected$'):inspect_native(encoded(records))

    def test_full_native_payload_and_cost_rules(self):
        value=inspect_native(self.valid)
        self.assertEqual((value['queries'],value['requests'],value['failed_fields']),(53,107,7))
        self.assertFalse(value['market_eligible']);self.assertFalse(value['native_origin_exported']);self.assertLess(value['known_reserved_bytes'],CAP)

    def test_hash_truncation_ascii_crlf_and_size_failures(self):
        for bad in (b'',self.valid[:-1],self.valid.replace(b'\n',b'\r\n'),self.valid+b'x',b'x'*(CAP+1),self.valid.replace(b'USD',b'USX',1),self.valid.replace(b'USD',b'\x80SD',1)):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):inspect_native(bad)

    def test_rehashed_missing_reordered_extra_and_unknown_frames(self):
        for tag in ('A','J','B','Z','K','R','L','E'):
            data=copy.deepcopy(self.records);index=next(i for i,r in enumerate(data) if r[0]==tag);del data[index];self.reject(data)
        data=copy.deepcopy(self.records);data[4],data[5]=data[5],data[4];self.reject(data)
        self.reject(self.records+[['E','53','107']]);self.reject(self.records+[['UNKNOWN']])

    def test_rehashed_keys_counts_and_scalar_syntax(self):
        changes=[('I',2,'wrong_key'),('I',1,'02'),('I',9,'2'),('I',10,'-1'),('D',11,'7FF0000000000000'),('D',11,'3ff0000000000000'),('V',11,'usd'),('W',2,'0:9'),('K',11,'9'),('R',9,'17'),('L',11,'USDD')]
        for tag,index,value in changes:
            data=copy.deepcopy(self.records);record=next(r for r in data if r[0]==tag);record[index]=value
            with self.subTest(tag=tag,index=index):self.reject(data)

    def test_failed_api_cannot_trust_nonzero_payload_or_successful_error(self):
        for tag,field,value in (('I',9,'0'),('D',10,'4401'),('V',9,'0'),('K',9,'0')):
            data=copy.deepcopy(self.records);record=next(r for r in data if r[0]==tag);record[field]=value;self.reject(data)

    def test_lease_replay_age_flags_and_bracket_corruption(self):
        for index,value in ((1,'0'),(3,'0'),(4,'99999999'),(5,'0'),(6,'99999999'),(8,'254')):
            data=copy.deepcopy(self.records);next(r for r in data if r[0]=='J')[index]=value;self.reject(data)
        data=copy.deepcopy(self.records);leases=[r for r in data if r[0]=='J'];leases[1][2]=leases[0][2];self.reject(data)
        data=copy.deepcopy(self.records);record=next(r for r in data if r[0]=='T');record[6]=str(int(record[7])+1);self.reject(data)

    def test_native_quote_float_and_timestamp_rules(self):
        for index,value in ((11,'0'),(12,'1700000000001'),(13,'0000000000000000'),(14,'3FF0000000000000'),(15,'FFF0000000000000'),(16,str(2**64)),(17,str(2**32)),(18,'BFF0000000000000')):
            # Changing millis within the same second is valid; use another second.
            if index==12:value='1700000001000'
            data=copy.deepcopy(self.records);next(r for r in data if r[0]=='T')[index]=value;self.reject(data)

    def test_repeated_sample_never_renews_age_and_regressions_reject(self):
        records=[['J',1,'1'*32,2000000,2010000,1,100,120,255],['J',2,'2'*32,2500000,2510000,1,100,620,255],
                 ['J',3,'3'*32,2970000,2980000,1,100,1070,255],['J',4,'4'*32,2970001,2980001,1,100,1070,255]]
        reader=Reader(encoded(records));reader.lease();reader.lease();reader.lease();self.assertEqual(reader.last_observed,1980000)
        with self.assertRaises(ValueError):reader.lease()
        for field in (5,6,7):
            data=copy.deepcopy(self.records);leases=[r for r in data if r[0]=='J'];leases[1][field]=str(int(leases[0][field])-1)
            self.reject(data)

    def test_raw_wall_clock_reversal_is_retained_without_utc_claim(self):
        data=copy.deepcopy(self.records);next(r for r in data if r[0]=='T')[4]='1699999999'
        value=inspect_native(encoded(data));self.assertEqual(value['wall_marker_reversals'],1);self.assertFalse(value['market_eligible'])

    def test_failed_empty_metadata_is_unknown_not_zero_cost(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root,failed=True);self.assertEqual(runner.run()['cause'],'complete')
            value=inspect_job(folder,JOB);self.assertEqual((value['queries'],value['requests'],value['failed_fields']),(48,97,43))
            self.assertFalse(value['market_eligible'])

    def test_maximum_sessions_rules_and_tiers_fit_the_declared_profile(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,producer,_,runner=setup(root);items=[];sessions=False
            for tag,key,ok,error,values,extras in producer.items:
                if tag=='W':
                    if not sessions:
                        items.extend(('W',f'{day}:{index}',True,0,['0','86340'],[]) for day in range(7) for index in range(9));sessions=True
                    continue
                if tag=='K':
                    rules=[]
                    for i in range(8):
                        r=copy.deepcopy(extras[0]);r[2]=str(i);r[3]='EMPTY';r[9]='16';rules.append(r)
                        for j in range(16):
                            tier=copy.deepcopy(extras[1]);tier[2]=str(i);tier[3]=str(j);rules.append(tier)
                    values=['8'];extras=rules
                items.append((tag,key,ok,error,values,extras))
            producer.items=items;self.assertEqual(runner.run()['cause'],'complete')
            result=inspect_job(folder,JOB);self.assertEqual((result['queries'],result['requests']),(104,209))
            self.assertLess(result['known_reserved_bytes'],CAP)


class Runner157Tests(unittest.TestCase):
    def test_default_off_has_no_clock_file_or_channel_effect(self):
        class Forbidden:
            def __getattr__(self,key):raise AssertionError('unexpected channel activity')
        runner=Runner('/does/not/exist',JOB,Forbidden(),clock=lambda: (_ for _ in ()).throw(AssertionError('clock')))
        self.assertEqual(runner.run()['cause'],'off')
        with self.assertRaises(ValueError):runner.serve(1)
        with self.assertRaises(ValueError):runner.readiness()
        runner.cleanup()

    def test_clean_measured_run_cross_checks_every_reply_and_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,producer,channel,runner=setup(root);value=runner.run()
            self.assertEqual(value['cause'],'complete');self.assertTrue(producer.done);self.assertTrue(value['receipt_acknowledged'])
            self.assertEqual(channel.calls[-3:],['CANCEL','EXIT','CLOSE']);self.assertTrue(value['cleanup_complete'])
            self.assertEqual(value['published'],107);self.assertGreater(clock.reads,107*4)
            audited=inspect_job(folder,JOB);self.assertTrue(audited['relay_receipt_consistent']);self.assertFalse(audited['caller_acknowledgement_known'])

    def test_startup_waits_for_ready_and_never_ready_is_bounded(self):
        for mode,expected in (('delayed_ready','complete'),('never_ready','fault')):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,channel,runner=setup(root,mode);self.assertEqual(runner.run()['cause'],expected)
                self.assertLessEqual(len(runner.probes),32);self.assertEqual(channel.calls[-1],'CLOSE')
                if mode=='delayed_ready':self.assertTrue(inspect_job(folder,JOB)['relay_receipt_consistent'])

    def test_start_failure_uncontained_owner_and_loss_always_cleanup(self):
        for mode in ('start_failure','uncontained','owner_death'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,channel,runner=setup(root,mode);status=runner.run()
                self.assertEqual(status['cause'],'fault');self.assertTrue(status['start_attempted']);self.assertEqual(channel.calls[-3:],['CANCEL','EXIT','CLOSE'])
                with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_power_stale_wrong_challenge_protocol_and_slow_responses_stop(self):
        for mode in ('power','stale','wrong_challenge','protocol','slow'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,producer,_,runner=setup(root,mode);value=runner.run()
                self.assertEqual(value['cause'],'fault');self.assertFalse(producer.done);self.assertFalse(value['writer_complete'])
                self.assertFalse(runner.responses[-1]['published'])
                with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_rejected_status_strings_never_enter_receipts(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,channel,runner=setup(root);original=channel.request
            def untrusted(operation,challenge):
                raw=original(operation,challenge)
                if operation=='POLL' and channel.polls>=2:
                    value=json.loads(raw);value['untrusted_private_field']='INVENTED_PRIVATE_DETAIL';return json.dumps(value).encode()
                return raw
            channel.request=untrusted;self.assertEqual(runner.run()['cause'],'fault')
            self.assertIsNone(runner.responses[-1]['packet'])
            self.assertNotIn('INVENTED_PRIVATE_DETAIL',(folder/'Relay157.json').read_text())

    def test_cleanup_acks_are_separate_from_complete_native_writer(self):
        for mode in ('clear_failure','cancel_failure','close_failure'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,_,runner=setup(root,mode);value=runner.run()
                self.assertEqual(value['cause'],'cleanup');self.assertTrue(value['writer_complete']);self.assertFalse(value['cleanup_complete'])
                self.assertTrue(inspect_native((folder/'NativePort156.txt').read_bytes())['writer_complete'])
                with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_held_request_deadline_reversal_and_request_capacity(self):
        with tempfile.TemporaryDirectory() as root:
            _,_,_,channel,runner=setup(root,hold=True,budget=100_000)
            self.assertEqual(runner.run()['cause'],'deadline');self.assertEqual(channel.calls[-1],'CLOSE')
        with tempfile.TemporaryDirectory() as root:
            _,clock,_,channel,runner=setup(root)
            original=channel.start
            def reverse(*args):
                result=original(*args);clock.value-=10_000;return result
            channel.start=reverse;self.assertEqual(runner.run()['cause'],'fault');self.assertEqual(channel.calls[-1],'CLOSE')
        runner=Runner('/absent',JOB,Channel(Clock()),enabled=True)
        with self.assertRaises(ValueError):runner.serve(257)
        self.assertEqual(runner.channel.calls,[])
        times=iter((10,109,110));runner=Runner('/absent',JOB,Channel(Clock()),enabled=True,clock=lambda:next(times),budget_us=100)
        self.assertEqual(runner.tick(),10);self.assertEqual(runner.tick(),109)
        with self.assertRaises(TimeoutError):runner.tick()

    def test_restart_claim_and_existing_reply_prevent_owner_start(self):
        for existing in ('Owner157.claim','Reply0001.txt','Relay157.json'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,channel,runner=setup(root);path=folder/existing;path.write_bytes(b'preserve')
                self.assertEqual(runner.run()['cause'],'fault');self.assertEqual(path.read_bytes(),b'preserve');self.assertEqual(channel.calls,[])
        with tempfile.TemporaryDirectory() as root:
            folder,clock,_,channel,runner=setup(root);runner.run()
            second=Runner(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait);before=len(channel.calls)
            self.assertEqual(second.run()['cause'],'fault');self.assertEqual(len(channel.calls),before)

    def test_faulted_job_is_retained_and_fresh_nonce_starts_from_query_one(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root,'power');self.assertEqual(runner.run()['cause'],'fault')
            before={p.name:p.read_bytes() for p in folder.iterdir()}
            clock=Clock();job='b'*32;other=Path(root)/('Job156-'+job);Producer(other,job,clock)
            status=Runner(other,job,Channel(clock),enabled=True,clock=clock.read,wait=clock.wait).run()
            self.assertEqual(status['cause'],'complete');self.assertEqual(inspect_job(other,job)['queries'],53)
            self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir()})

    def test_frozen_clock_still_has_a_finite_wait_budget(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,_,channel,_=setup(root,hold=True)
            runner=Runner(folder,JOB,channel,enabled=True,clock=lambda:clock.value,wait=lambda _:None)
            # No elapsed time progress, request two never appears; iteration cap stops it.
            self.assertEqual(runner.run()['cause'],'fault');self.assertEqual(len(runner.responses),1)
            self.assertEqual(channel.calls[-1],'CLOSE')

    def test_invalid_configuration_is_rejected_before_effects(self):
        for values in ({'enabled':1},{'budget_us':True},{'budget_us':0},{'budget_us':30_000_001},{'job':'invalid'}):
            args=dict(folder='/absent',job=JOB,channel=Channel(Clock()));args.update(values)
            with self.assertRaises(ValueError):Runner(**args)

    def test_partial_oversized_symlink_and_fifo_requests_never_poll(self):
        for mode in ('partial','oversize','link','fifo'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,channel,runner=setup(root);path=folder/'Request0001.txt'
                if mode=='partial':path.write_bytes(path.read_bytes()[:-1])
                if mode=='oversize':path.write_bytes(b'x'*513)
                if mode=='link':path.unlink();path.symlink_to(folder/'NativePort156.txt')
                if mode=='fifo':path.unlink();os.mkfifo(path)
                value=runner.run();self.assertEqual(value['cause'],'fault');self.assertEqual(channel.calls.count('POLL'),1)

    def test_reply_storage_delay_fails_freshness_after_write(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,_,_,runner=setup(root);original=write_file
            def delayed(path,value):
                original(path,value)
                if path.name=='Reply0001.txt':clock.value+=1_000_001
            with patch('forex_demo_lab.recorder_runner_157.write_file',side_effect=delayed):value=runner.run()
            self.assertEqual(value['cause'],'fault');self.assertFalse(runner.responses[0]['published']);self.assertTrue((folder/'Reply0001.txt').exists())

    def test_partial_write_fsync_and_receipt_ack_uncertainty(self):
        for mode in ('short','fsync','receipt'):
            with tempfile.TemporaryDirectory() as root:
                folder,_,_,_,runner=setup(root);original=write_file
                def fault(path,value):
                    selected=path.name==('Relay157.json' if mode=='receipt' else 'Reply0001.txt')
                    if selected:
                        if mode=='short':path.write_bytes(value[:-1]);raise OSError('invented short write')
                        original(path,value);raise OSError('invented missing fsync acknowledgement')
                    original(path,value)
                with patch('forex_demo_lab.recorder_runner_157.write_file',side_effect=fault):value=runner.run()
                self.assertEqual(value['cause'],'receipt_write' if mode=='receipt' else 'fault')
                if mode=='receipt':
                    self.assertFalse(value['receipt_acknowledged']);self.assertTrue(inspect_job(folder,JOB)['relay_receipt_consistent'])
                    self.assertFalse(inspect_job(folder,JOB)['caller_acknowledgement_known'])
                else:
                    self.assertFalse(runner.responses[0]['published'])
                    with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_default_clock_is_measured_inside_each_exchange(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,_,channel,_=setup(root)
            with patch('forex_demo_lab.recorder_runner_157.time.monotonic_ns',side_effect=lambda:clock.read()*1000) as measured:
                value=Runner(folder,JOB,channel,enabled=True,wait=clock.wait).run()
            self.assertEqual(value['cause'],'complete');self.assertGreater(measured.call_count,400)


class Audit157Tests(unittest.TestCase):
    def test_receipt_corruption_types_duplicates_times_and_cleanup_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root);runner.run();path=folder/'Relay157.json';original=json.loads(path.read_bytes())
            for mode in ('unknown','bool_time','negative_span','wrong_job','published','packet','clock','cleanup','late','start'):
                value=copy.deepcopy(original)
                if mode=='unknown':value['extra']='not allowed'
                if mode=='bool_time':value['origin_us']=True
                if mode=='negative_span':value['active_end_us']=0
                if mode=='wrong_job':value['job']='b'*32
                if mode=='published':value['responses'][0]['published']=False
                if mode=='packet':value['responses'][0]['packet']='{}'
                if mode=='clock':value['responses'][0]['received_us']=value['responses'][0]['sent_us']-1
                if mode=='cleanup':value['owner_exit_observed']=False
                if mode=='late':value['active_end_us']=value['origin_us']+value['budget_us']
                if mode=='start':value['start_packet']='[]'
                path.write_text(json.dumps(value))
                with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'^relay157_rejected$'):inspect_job(folder,JOB)
            path.write_text('{"schema":1,"schema":2}')
            with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_self_consistently_rehashed_native_and_reply_edits_conflict_with_receipts(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root);runner.run()
            path=folder/'NativePort156.txt';data=rows(path.read_bytes())
            # A larger sample sequence still parses the native grammar if all later samples advance.
            for row in data:
                if row[0]=='J':row[5]=str(int(row[5])+1000)
            path.write_bytes(encoded(data))
            for i in range(1,108):
                reply=folder/f'Reply{i:04d}.txt';fields=reply.read_text().strip().split('\t');fields[4]=str(int(fields[4])+1000);reply.write_text('\t'.join(fields)+'\n')
            self.assertTrue(check_files(folder,JOB)['writer_complete'])
            with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_native_footer_without_receipt_or_matching_transport_is_insufficient(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root);runner.run();(folder/'Relay157.json').unlink()
            self.assertTrue(check_files(folder,JOB)['writer_complete'])
            with self.assertRaises(ValueError):inspect_job(folder,JOB)
            (folder/'Reply0001.txt').unlink()
            with self.assertRaises(OSError):check_files(folder,JOB)

    def test_exclusive_regular_file_io_rejects_overwrite_links_and_fifo(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'data';write_file(path,b'preserved')
            with self.assertRaises(FileExistsError):write_file(path,b'replace')
            link=Path(root)/'link';link.symlink_to(path)
            with self.assertRaises(OSError):read_file(link,512)
            fifo=Path(root)/'fifo';os.mkfifo(fifo)
            with self.assertRaises(ValueError):read_file(fifo,512)
            with self.assertRaises(ValueError):read_file(path,1)
            self.assertEqual(path.read_bytes(),b'preserved')

    def test_actual_file_writer_checks_short_write_and_fsync_ack(self):
        original=os.fdopen
        class ShortFile:
            def __init__(self,file):self.file=file
            def __enter__(self):return self
            def __exit__(self,*args):self.file.close()
            def write(self,value):return self.file.write(value[:-1])
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'short'
            with patch('forex_demo_lab.recorder_files_157.os.fdopen',side_effect=lambda *a,**k:ShortFile(original(*a,**k))):
                with self.assertRaises(ValueError):write_file(path,b'invented')
            self.assertEqual(path.read_bytes(),b'invente')
            path=Path(root)/'uncertain'
            with patch('forex_demo_lab.recorder_files_157.os.fsync',side_effect=OSError('invented')):
                with self.assertRaises(OSError):write_file(path,b'invented')
            self.assertEqual(path.read_bytes(),b'invented')

    def test_cli_default_off_and_invented_exercise_only(self):
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/'absent'
            with contextlib.redirect_stdout(io.StringIO()) as stream:main(['--output',str(out)])
            self.assertEqual(json.loads(stream.getvalue())['cause'],'off');self.assertFalse(out.exists())
            with contextlib.redirect_stdout(io.StringIO()) as stream:main(['--exercise-invented','--output',str(out)])
            self.assertEqual(json.loads(stream.getvalue())['cases'],10)
            with self.assertRaises(FileExistsError):main(['--exercise-invented','--output',str(out)])

    def test_public_cli_is_a_separate_default_off_process(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/recorder-relay-157.py')],check=True,capture_output=True,text=True)
        self.assertEqual(json.loads(result.stdout),dict(cause='off',native_launch=False,market_eligible=False))

    def test_independent_checker_cli_reports_counts_and_rejects_missing_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            folder,_,_,_,runner=setup(root);self.assertEqual(runner.run()['cause'],'complete')
            command=[sys.executable,str(ROOT/'scripts/check-native-journal-157.py'),'--folder',str(folder),'--job',JOB]
            result=subprocess.run(command,check=True,capture_output=True,text=True)
            value=json.loads(result.stdout);self.assertEqual(value['requests'],107);self.assertFalse(value['market_eligible'])
            (folder/'Relay157.json').unlink();result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stdout),dict(error='relay157_rejected',market_eligible=False))


if __name__=='__main__':unittest.main()
