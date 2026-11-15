"""Controlled startup/adapter checks. No Windows process launch in this suite."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forex_demo_lab.recorder_fixture_157 import Clock, Producer, Channel as InventedChannel
from forex_demo_lab.recorder_runner_157 import Runner as Runner157
from forex_demo_lab.recorder_startup_158 import Runner
from forex_demo_lab.relay_audit_157 import inspect_job as inspect157
from forex_demo_lab.relay_audit_158 import inspect_job
from forex_demo_lab.native_trial_158 import run, main, validate_build, Channel, quiet, same_power
from forex_demo_lab.native_supervision_143 import WindowsChannel

JOB='a'*32
ROOT=Path(__file__).resolve().parents[1]


def setup(root,mode):
    folder=Path(root)/('Job156-'+JOB);clock=Clock();Producer(folder,JOB,clock);channel=InventedChannel(clock)
    original=channel.request
    def request(operation,challenge):
        raw=original(operation,challenge)
        if operation!='POLL':return raw
        value=json.loads(raw)
        if mode=='absent' and channel.polls==1 or mode=='never':
            value.update(sample_valid=False,mains=False,create_ack=False,set_ack=False,ready_signal=False,helper_running_marker=False)
        if mode=='power':value.update(mains=False)
        if mode=='lost' and channel.polls>=3:value.update(sample_valid=False)
        if mode=='exit':value.update(running=False)
        return json.dumps(value).encode()
    channel.request=request;return folder,clock,channel


class Startup158Tests(unittest.TestCase):
    def test_absence_is_not_a_power_observation_but_is_never_ready(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,channel=setup(root,'absent');runner=Runner(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait)
            self.assertEqual(runner.run()['cause'],'complete');self.assertEqual(len(runner.probes),2);self.assertFalse(runner.probes[0]['healthy'])
            self.assertTrue(inspect_job(folder,JOB)['relay_receipt_consistent'])
            with self.assertRaises(ValueError):inspect157(folder,JOB)

    def test_frozen157_reproduces_initial_absence_failure(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,channel=setup(root,'absent');runner=Runner157(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait)
            self.assertEqual(runner.run()['cause'],'fault');self.assertEqual(runner.responses,[])

    def test_sampled_power_failure_exit_and_sample_loss_remain_fatal(self):
        for mode in ('power','exit','lost'):
            with tempfile.TemporaryDirectory() as root:
                folder,clock,channel=setup(root,mode);runner=Runner(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait)
                self.assertEqual(runner.run()['cause'],'fault');self.assertFalse(runner.writer_complete)
                with self.assertRaises(ValueError):inspect_job(folder,JOB)

    def test_no_sample_exhausts_probe_budget_without_serving(self):
        with tempfile.TemporaryDirectory() as root:
            folder,clock,channel=setup(root,'never');runner=Runner(folder,JOB,channel,enabled=True,clock=clock.read,wait=clock.wait)
            self.assertEqual(runner.run()['cause'],'fault');self.assertEqual(len(runner.probes),32);self.assertEqual(runner.responses,[])

    def test_default_off_and_methods_have_no_channel_effect(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();channel=InventedChannel(clock);runner=Runner(Path(root)/'absent',JOB,channel)
            self.assertEqual(runner.run()['cause'],'off');self.assertEqual(channel.calls,[])
            with self.assertRaises(ValueError):runner.readiness()

    def test_158_auditor_is_exactly_the_declared_narrow_derivation(self):
        old=(ROOT/'src/forex_demo_lab/relay_audit_157.py').read_text()
        expected=old.replace('Independent final receipt/file reconciliation. Self-consistency is not trust.','Separate158 receipt check: an absent sample is not a power observation.')
        expected=expected.replace("value=status(record['packet'],job,challenge);require(value['running'] and value['mains'])","value=status(record['packet'],job,challenge);require(value['running'])\n            if value['sample_valid']:require(value['mains'])")
        self.assertEqual((ROOT/'src/forex_demo_lab/relay_audit_158.py').read_text(),expected)


class NativeTrial158Tests(unittest.TestCase):
    def test_default_off_never_reads_build_or_starts_process(self):
        with patch('forex_demo_lab.native_trial_158.validate_build',side_effect=AssertionError('build')),patch('forex_demo_lab.native_trial_158.snapshot',side_effect=AssertionError('snapshot')):
            self.assertFalse(run(None,None)['enabled'])
            with contextlib.redirect_stdout(io.StringIO()) as output:self.assertEqual(main([]),0)
            self.assertFalse(json.loads(output.getvalue())['enabled'])

    def test_wrong_schema_and_unpinned_binary_are_rejected_before_launch(self):
        for value in ({},{'schema':'other'},{'schema':'health142_build_v1','owner_sha256':'0'*64}):
            with self.assertRaises(ValueError):validate_build(value)

    def test_fault_adapter_only_modifies_healthy_packets_and_preserves_native_source(self):
        for mode in ('held','contradictory'):
            channel=Channel({},mode);clock=Clock();source=InventedChannel(clock);source.start(JOB,1000)
            with patch.object(WindowsChannel,'request',side_effect=source.request),patch('forex_demo_lab.native_trial_158.time.sleep'):
                for index in range(6):raw=channel.request('POLL',f'{index:032x}')
            value=json.loads(raw);self.assertTrue(channel.injected)
            if mode=='held':self.assertEqual(value['sample_sequence'],5)
            else:self.assertTrue(value['ready_signal']);self.assertFalse(value['create_ack'])

    def test_actual_failure_is_not_masked_by_fault_adapter(self):
        channel=Channel({},'held');clock=Clock();source=InventedChannel(clock,'power');source.start(JOB,1000)
        with patch.object(WindowsChannel,'request',side_effect=source.request):
            for index in range(4):raw=channel.request('POLL',f'{index:032x}')
        self.assertFalse(json.loads(raw)['mains']);self.assertEqual(channel.injected,[])

    def test_eof_closes_only_the_supplied_channel_input(self):
        class Input:
            def __init__(self):self.closed=False
            def close(self):self.closed=True
        class Process:stdin=Input()
        channel=Channel({},'eof');channel.process=Process();clock=Clock();source=InventedChannel(clock);source.start(JOB,1000)
        with patch.object(WindowsChannel,'request',side_effect=source.request):
            for index in range(5):channel.request('POLL',f'{index:032x}')
        self.assertTrue(channel.process.stdin.closed);self.assertEqual(channel.injected[-1]['kind'],'actual_owner_input_eof')

    def test_host_comparison_requires_both_zero_processes_and_unchanged_settings(self):
        a=dict(active='a',sleep='b',display='c',owner_count=0,helper_count=0);self.assertTrue(quiet(a));self.assertTrue(same_power(a,dict(a)))
        self.assertFalse(quiet(dict(a,helper_count=1)));self.assertFalse(same_power(a,dict(a,sleep='changed')))


if __name__=='__main__':unittest.main()
