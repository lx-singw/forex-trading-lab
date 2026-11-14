import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

from forex_demo_lab.sharing_diagnostics_071 import Runtime071,Diagnostics071,DiagnosticFailure071,inspect_prior071
from forex_demo_lab.sharing_runtime_069 import Meter069,Trace069,Reservation069,ObservedCompanion069,Resources069,Runtime069
from forex_demo_lab.sharing_runtime_066 import COMMANDS
from forex_demo_lab.sharing_companion_065 import Companion065
from forex_demo_lab.sharing_probe_062 import ProbeRejected
from test_sharing_runtime_066 import ExternalFiles
from test_transport_lifecycle_060 import Clock
from test_mql_sharing_064 import record,text

ROOT=Path(__file__).resolve().parents[1]


class Diagnostics071Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.clock=Clock();self.clock.boot=99000;self.m=Meter069(self.clock);self.trace=Trace069()
        self.s=Reservation069(self.root/'reservation',dict.fromkeys(
            ('source','ex5','terminal','editor','preparation','policy','helper_profile'),'a'*64),self.m)
        self.guard=lambda:True;self.f=ExternalFiles(self.m,self.clock)
        self.c=ObservedCompanion069(Companion065(self.f,self.m,lambda:self.guard()),self.trace)
        self.log=self.root/'log';self.log.write_bytes('old\r\n'.encode('utf-16-le'))
        self.r=Runtime071(self.c,self.s,self.m,lambda:self.guard(),self.log,self.clock.advance,trace=self.trace)
    def prepared(self):
        for cmd in COMMANDS[:3]:self.r.command(cmd)
    def armed(self):
        self.prepared();self.clock.advance(1000);self.r.command('arm-enabled')
    def probed(self):self.armed();self.r.command('probe')
    def saved(self):
        with self.log.open('ab') as f:f.write(('\r\n'.join(text(x) for x in (record(),record(True)))+'\r\n').encode('utf-16-le'))
        self.r.command('logs-saved')
    def reject(self,cmd,step,code):
        with self.assertRaisesRegex(ProbeRejected,'^'+step+':'+code+'$'):self.r.command(cmd)
        self.assertEqual(self.r.diagnostics.first_failure,dict(step=step,code=code))
        out=self.r.finish();self.assertFalse(out['completed']);self.assertFalse(self.f.active)
        self.assertEqual(out['stop_reason'],step+':'+code);return out
    def test_complete_injected_sequence_with_relative_timings(self):
        self.probed();self.saved();out=self.r.finish();self.assertTrue(out['completed'])
        d=out['diagnostics'];self.assertIsNone(d['first_failure']);self.assertTrue(all(e['completed'] for e in d['events']))
        self.assertEqual(d['metrics'],dict(arm_to_ready_ms=0,arm_to_probe_receipt_ms=0,
            arm_to_window_check_ms=0,probe_guard_ms=0,wait5_elapsed_ms=5000,wait35_elapsed_ms=35000))
        self.assertEqual([p.stage for p in self.c.probes],['pre','pre','independent','independent','post','post'])
        self.assertEqual(out['counts']['log_reads'],1);self.assertEqual(self.s.arms,['disabled','enabled'])
        self.assertFalse(out['native_mql_verified']);self.assertFalse(out['orders_available'])
    def test_late_receipt_rejected_before_waits(self):
        self.armed();self.clock.advance(10001)
        out=self.reject('probe','probe_launch_window','window_rejected')
        self.assertEqual(out['diagnostics']['metrics']['arm_to_probe_receipt_ms'],10001)
        self.assertEqual(out['counts']['schedule_waits'],0)
    def test_guard_time_can_cross_unchanged_launch_deadline(self):
        self.armed();self.clock.advance(9000);self.guard=lambda:self.clock.advance(2000) or True
        out=self.reject('probe','probe_launch_window','window_rejected');d=out['diagnostics']['metrics']
        self.assertEqual((d['arm_to_probe_receipt_ms'],d['arm_to_window_check_ms'],d['probe_guard_ms']),(9000,11000,2000))
    def test_probe_guard_false_has_distinct_reason(self):
        self.armed();self.guard=lambda:False;out=self.reject('probe','probe_guard_before','guard_rejected')
        self.assertIsNone(out['diagnostics']['metrics']['arm_to_window_check_ms'])
    def test_probe_guard_private_exception_is_redacted(self):
        self.armed()
        def fail():raise RuntimeError('private SID account password')
        self.guard=fail;out=self.reject('probe','probe_guard_before','guard_rejected')
        for value in ('private','SID','account','password'):self.assertNotIn(value,json.dumps(out))
    def test_clock_discontinuity_before_probe_stops_at_first_check(self):
        self.armed();self.clock.utc+=2001;self.reject('probe','command_order','clock_rejected')
    def test_clock_discontinuity_during_guard_is_separate(self):
        self.armed();self.guard=lambda:setattr(self.clock,'utc',self.clock.utc+2001) or True
        self.reject('probe','probe_guard_before','clock_rejected')
    def test_post_arm_guard_time_is_in_readiness_metric(self):
        self.prepared();self.clock.advance(1000);self.guard=lambda:self.clock.advance(2000) or True
        self.r.command('arm-enabled');self.assertEqual(self.r.diagnostics.metrics['arm_to_ready_ms'],2000)
        self.assertEqual(self.clock.boot-self.r.armed_boot,2000)
    def test_wait_without_progress_has_finite_loop(self):
        self.armed();calls=[];self.r.wait=lambda ms:calls.append(ms)
        self.reject('probe','wait5_loop','wait_rejected');self.assertEqual(len(calls),36)
    def test_wait_overrun_is_distinct_window_failure(self):
        self.armed();self.r.wait=lambda ms:self.clock.advance(21000)
        self.reject('probe','wait5_window','wait_rejected')
    def test_independent_wrong_error_stops_before_second_wait(self):
        self.armed();self.f.error='access_denied'
        out=self.reject('probe','independent_controls','controls_failed');self.assertEqual(out['counts']['schedule_waits'],1)
    def test_post_control_failure_is_distinct(self):
        self.armed();original=self.c.controls
        def controls(stage):
            if stage=='post':raise RuntimeError('private path')
            return original(stage)
        self.c.controls=controls;self.reject('probe','post_controls','controls_failed')
    def test_empty_saved_range_is_not_success(self):
        self.probed();self.reject('logs-saved','saved_range_read','saved_log_failed')
    def test_replaced_saved_range_is_not_success(self):
        self.probed();self.log.rename(self.root/'old');self.log.write_bytes(b'\0'*100)
        self.reject('logs-saved','saved_range_read','saved_log_failed')
    def test_unknown_command_has_no_raw_echo(self):
        out=self.reject('private-secret','command_order','order_rejected');self.assertNotIn('private-secret',json.dumps(out))
    def test_duplicate_arm_cannot_grant_extra_launch(self):
        self.r.command('baseline-saved');self.r.command('arm-disabled')
        self.reject('arm-disabled','command_order','order_rejected');self.assertEqual(self.s.arms,['disabled'])
    def test_first_failure_survives_cleanup_failure(self):
        self.armed();self.clock.advance(10001);original=self.c.finish
        def finish():original();raise RuntimeError('private')
        self.c.finish=finish;out=self.reject('probe','probe_launch_window','window_rejected')
        self.assertEqual(out['diagnostics']['events'][-1]['failure_code'],'cleanup_unconfirmed')
    def test_missing_cleanup_proof_cannot_pass(self):
        self.probed();self.saved();original=self.c.finish
        self.c.finish=lambda:original() and None
        out=self.r.finish();self.assertFalse(out['completed']);self.assertEqual(out['stop_reason'],'cleanup_validate:cleanup_unconfirmed')
    def test_boolean_cleanup_count_cannot_pass(self):
        self.probed();self.saved();original=self.c.finish
        self.c.finish=lambda:{**original(),'unconfirmed_handles':False}
        self.assertEqual(self.r.finish()['stop_reason'],'cleanup_validate:cleanup_unconfirmed')
    def test_expiry_still_closes_owned_files_and_sdk_once(self):
        self.prepared();calls=[];self.s.sdk_attempt();owner=Resources069(self.s,self.m,self.trace)
        owner.runner=self.r;owner.sdk=NS(shutdown=lambda:calls.append('shutdown'))
        self.clock.advance(900000);out=owner.close();self.assertFalse(self.f.active)
        self.assertEqual(calls,['shutdown']);self.assertFalse(out['outcome']['completed'])
        self.assertTrue(out['outcome']['cleanup']['all_handles_closed'])
        with self.assertRaises(ProbeRejected):owner.close()
    def test_diagnostic_exhaustion_still_closes(self):
        self.prepared();d=self.r.diagnostics
        while len(d.events)<192:d.run('command_order','order_rejected',lambda:True)
        out=self.r.finish();self.assertFalse(self.f.active);self.assertFalse(out['completed'])
        self.assertTrue(out['diagnostics']['diagnostics_exhausted']);self.assertEqual(len(d.events),192)
    def test_outer_trace_exhaustion_still_closes(self):
        self.prepared()
        while len(self.trace.events)<32:self.trace.run('preflight',lambda:True)
        self.reject('arm-enabled','diagnostic_budget','budget_rejected')
    def test_bad_evidence_window_has_distinct_final_reason(self):
        self.probed();self.saved();self.r.rows=[]
        out=self.r.finish();self.assertFalse(out['completed']);self.assertEqual(out['stop_reason'],'window_match:audit_failed')
    def test_finish_cannot_repeat_file_cleanup(self):
        self.prepared();self.r.finish();events=list(self.f.events)
        with self.assertRaises(ProbeRejected):self.r.finish()
        self.assertEqual(self.f.events,events)
    def test_wait_budget_failure_is_distinct(self):
        self.armed();self.m.counts['schedule_waits']=2;self.reject('probe','wait5_budget','budget_rejected')
    def test_interruption_is_fixed_and_cleanup_runs(self):
        self.armed()
        def fail():raise KeyboardInterrupt('private')
        self.guard=fail;out=self.reject('probe','probe_guard_before','interrupted');self.assertNotIn('private',json.dumps(out))
    def test_metrics_reject_unknown_names_boolean_and_negative(self):
        for name,value in (('private',1),('probe_guard_ms',True),('probe_guard_ms',-1)):
            with self.assertRaises(DiagnosticFailure071):Diagnostics071(self.m).metric(name,value)
    def test_success_has_no_native_operations_or_absolute_clock_export(self):
        self.probed();self.saved();out=self.r.finish();d=json.dumps(out['diagnostics'])
        self.assertNotIn(str(self.clock.utc),d);self.assertNotIn('private',d)
        for key in ('native_calls','sdk_connections','deployment_writes'):self.assertEqual(out['counts'][key],0)
    def test_old_late_probe_loses_precise_reason(self):
        self.r=Runtime069(self.c,self.s,self.m,lambda:self.guard(),self.log,self.clock.advance,trace=self.trace)
        self.armed();self.clock.advance(10001)
        with self.assertRaisesRegex(ProbeRejected,'^runtime_step_failed_details_redacted$'):self.r.command('probe')
        self.assertEqual(self.m.counts['schedule_waits'],0);self.assertEqual(self.trace.current,'independent_controls')
        self.r.finish();self.assertFalse(self.f.active)
    def test_old_guard_failure_has_same_ambiguous_evidence(self):
        self.r=Runtime069(self.c,self.s,self.m,lambda:self.guard(),self.log,self.clock.advance,trace=self.trace)
        self.armed();self.guard=lambda:False
        with self.assertRaisesRegex(ProbeRejected,'^runtime_step_failed_details_redacted$'):self.r.command('probe')
        self.assertEqual(self.m.counts['schedule_waits'],0);self.assertEqual(self.trace.current,'independent_controls')
        self.r.finish();self.assertFalse(self.f.active)
    def test_prior_report_does_not_claim_root_cause(self):
        out=inspect_prior071(json.loads((ROOT/'reports/native-sharing-069-runtime.json').read_text()))
        self.assertFalse(out['root_cause_proven']);self.assertFalse(out['native_experiment_repeated'])
        self.assertEqual(out['candidate_steps'],['probe_guard_before','probe_launch_window','wait5_budget'])
    def test_unexpected_prior_shape_is_rejected(self):
        prior=json.loads((ROOT/'reports/native-sharing-069-runtime.json').read_text());prior['counts']['schedule_waits']=1
        with self.assertRaisesRegex(ProbeRejected,'^prior_diagnostic_inputs_rejected$'):inspect_prior071(prior)
