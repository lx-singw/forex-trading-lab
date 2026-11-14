"""Offline diagnostic runner. No native entry point, SDK import or orders.

Keeps the066 schedule/window/guards; separates their previously swallowed
failures. Reused064 matcher/data are injected fixtures, not a native permission.
"""
from datetime import datetime,timezone

from .sharing_runtime_066 import COMMANDS
from .sharing_runtime_069 import Runtime069
from .sharing_session_065 import SavedRange065
from .sharing_probe_062 import ProbeRejected
from .mql_sharing_064 import PrivateProof,match_evidence

PHASE='71000000000000000000000000000001'
STEPS=('diagnostic_budget','command_order','command_budget','command_guard_before','command_guard_after',
    'baseline_anchor','disabled_arm','file_prepare','seal_release','enabled_arm','armed_clock','ready_clock',
    'probe_received','probe_guard_before','probe_launch_window',
    'wait5_budget','wait5_guard_before','wait5_loop','wait5_guard_after','wait5_window',
    'independent_controls','wait35_budget','wait35_guard_before','wait35_loop','wait35_guard_after','wait35_window',
    'post_stage','post_controls','saved_range_read','file_cleanup','cleanup_validate','final_guard',
    'state_validate','window_match','final_trace')
CODES=('order_rejected','budget_rejected','guard_rejected','clock_rejected','window_rejected',
    'wait_rejected','file_prepare_failed','seal_release_failed','arm_failed','controls_failed',
    'saved_log_failed','cleanup_unconfirmed','audit_failed','interrupted','unexpected_failure')
METRICS=('arm_to_ready_ms','arm_to_probe_receipt_ms','arm_to_window_check_ms','probe_guard_ms',
    'wait5_elapsed_ms','wait35_elapsed_ms')
GUARDS=('command_guard_before','command_guard_after','probe_guard_before','wait5_guard_before',
    'wait5_guard_after','wait35_guard_before','wait35_guard_after','final_guard')


class DiagnosticFailure071(ProbeRejected):
    def __init__(self,step,code):
        if step not in STEPS or code not in CODES:raise ProbeRejected('diagnostic_schema_rejected')
        self.step,self.code=step,code;super().__init__(step+':'+code)


class Diagnostics071:
    def __init__(self,meter):
        self.meter=meter;self.events=[];self.metrics=dict.fromkeys(METRICS,None)
        self.first_failure=None;self.exceeded=False
    def failure(self,step,code):
        failure=DiagnosticFailure071(step,code)
        if self.first_failure is None:self.first_failure=dict(step=step,code=code)
        return failure
    def enter(self,step):
        if step not in STEPS:raise self.failure('diagnostic_budget','budget_rejected')
        if len(self.events)>=192:
            self.exceeded=True;raise self.failure('diagnostic_budget','budget_rejected')
        event=dict(step=step,completed=False,duration_ms=None,failure_code=None)
        self.events.append(event);return event
    def metric(self,name,value):
        if name not in METRICS or type(value) is not int or value<0:
            raise self.failure('diagnostic_budget','unexpected_failure')
        self.metrics[name]=value
    def run(self,step,code,operation):
        event=self.enter(step);start=None
        try:start=self.meter.check()
        except (Exception,KeyboardInterrupt):
            event['failure_code']='clock_rejected';raise self.failure(step,'clock_rejected') from None
        try:value=operation()
        except (Exception,KeyboardInterrupt) as error:
            reason='interrupted' if isinstance(error,KeyboardInterrupt) else code
            try:
                end=self.meter.check();event['duration_ms']=end[2]-start[2]
            except (Exception,KeyboardInterrupt):reason='clock_rejected'
            event['failure_code']=reason;raise self.failure(step,reason) from None
        try:
            end=self.meter.check();event['duration_ms']=end[2]-start[2]
        except (Exception,KeyboardInterrupt):
            event['failure_code']='clock_rejected';raise self.failure(step,'clock_rejected') from None
        event['completed']=True;return value
    def cleanup(self,operation):
        # Neither expiry nor diagnostic exhaustion prevents the owned close.
        event=None;start=None;clock_ok=True
        try:event=self.enter('file_cleanup')
        except DiagnosticFailure071:pass
        try:start=self.meter.check()
        except (Exception,KeyboardInterrupt):clock_ok=False
        try:value=operation()
        except (Exception,KeyboardInterrupt):
            if event is not None:event['failure_code']='cleanup_unconfirmed'
            raise self.failure('file_cleanup','cleanup_unconfirmed') from None
        try:
            end=self.meter.check()
            if event is not None and start is not None:event['duration_ms']=end[2]-start[2]
        except (Exception,KeyboardInterrupt):clock_ok=False
        if event is not None:
            event['completed']=clock_ok
            if not clock_ok:event['failure_code']='clock_rejected'
        if not clock_ok:self.failure('file_cleanup','clock_rejected')
        return value
    def public(self):
        return dict(version='sharing_diagnostics_071_v1',phase=PHASE,events=[dict(e) for e in self.events],
            metrics=dict(self.metrics),first_failure=dict(self.first_failure) if self.first_failure else None,
            diagnostics_exhausted=self.exceeded,
            measured_guard_ms=sum(e['duration_ms'] or 0 for e in self.events if e['step'] in GUARDS))


class Runtime071(Runtime069):
    def __init__(self,*args,trace):
        super().__init__(*args,trace=trace);self.diagnostics=Diagnostics071(self.meter)
    def _step(self,step,code,operation):return self.diagnostics.run(step,code,operation)
    def _guard(self,step):
        def check():
            if self.guard() is not True:raise ValueError()
            return self.meter.check()
        return self._step(step,'guard_rejected',check)
    def _order(self,command):
        if self.stopped or self.closed or self.stage>=6 or command!=COMMANDS[self.stage]:raise ValueError()
    def _pause(self,milliseconds):
        prefix='wait5' if milliseconds==5000 else 'wait35'
        self._step(prefix+'_budget','budget_rejected',lambda:self.meter.consume('schedule_waits'))
        start=self._guard(prefix+'_guard_before')[2]
        def loop():
            for _ in range(36):
                now=self.meter.check()[2]
                if now-start>=milliseconds:break
                self.wait(min(1000,milliseconds-(now-start)))
            else:raise ValueError()
        self._step(prefix+'_loop','wait_rejected',loop)
        end=self._guard(prefix+'_guard_after')[2]
        self.diagnostics.metric(prefix+'_elapsed_ms',end-start)
        def window():
            if not milliseconds<=end-start<=milliseconds+15000:raise ValueError()
        self._step(prefix+'_window','wait_rejected',window)
    def _body(self,command):
        self._step('command_order','order_rejected',lambda:self._order(command))
        if command=='probe':
            now=self._step('probe_received','clock_rejected',self.meter.check)
            self.diagnostics.metric('arm_to_probe_receipt_ms',now[2]-self.armed_boot)
        self._step('command_budget','budget_rejected',lambda:self.meter.consume('commands'))
        self._guard('probe_guard_before' if command=='probe' else 'command_guard_before')
        if command=='baseline-saved':
            self.range=self._step('baseline_anchor','saved_log_failed',lambda:SavedRange065(self.log,self.meter))
        elif command=='arm-disabled':self._step('disabled_arm','arm_failed',lambda:self.session.arm('disabled'))
        elif command=='disabled-done':self._step('file_prepare','file_prepare_failed',self.c.prepare)
        elif command=='arm-enabled':
            self._step('seal_release','seal_release_failed',self.c.release_seal)
            self._step('enabled_arm','arm_failed',lambda:self.session.arm('enabled'))
            self.armed_boot=self._step('armed_clock','clock_rejected',self.meter.check)[2]
        elif command=='probe':
            def window():
                now=self.meter.check()[2];delta=now-self.armed_boot
                self.diagnostics.metric('arm_to_window_check_ms',delta)
                guards=[e for e in self.diagnostics.events if e['step']=='probe_guard_before']
                self.diagnostics.metric('probe_guard_ms',guards[-1]['duration_ms'])
                if not 0<=delta<=10000:raise ValueError()
            self._step('probe_launch_window','window_rejected',window)
            self._pause(5000)
            self._step('independent_controls','controls_failed',lambda:self.c.controls('independent'))
            self._pause(35000)
            self._step('post_stage','controls_failed',lambda:setattr(self.c,'stage','post'))
            self._step('post_controls','controls_failed',lambda:self.c.controls('post'))
        elif command=='logs-saved':self.rows=self._step('saved_range_read','saved_log_failed',self.range.read)
        self._guard('command_guard_after')
        if command=='arm-enabled':
            now=self._step('ready_clock','clock_rejected',self.meter.check)
            self.diagnostics.metric('arm_to_ready_ms',now[2]-self.armed_boot)
        self.stage+=1
        return dict(status=command,maximum_launches=2,quote_reads=0,orders_available=False)
    def command(self,command):
        names={'baseline-saved':'saved_log','arm-disabled':'disabled_arm','disabled-done':'file_prepare',
            'arm-enabled':'enabled_arm','probe':'independent_controls','logs-saved':'saved_log'}
        try:
            if command not in names:return self._body(command)
            return self.trace.run(names[command],self._body,command)
        except (Exception,KeyboardInterrupt) as error:
            self.stopped=True;self.session.stop()
            if not isinstance(error,DiagnosticFailure071):
                self.diagnostics.failure('diagnostic_budget','budget_rejected' if self.trace.exceeded else 'unexpected_failure')
            failure=self.diagnostics.first_failure
            self.reason=failure['step']+':'+failure['code']
            raise ProbeRejected(self.reason) from None
    def finish(self):
        if self.closed:raise ProbeRejected('runtime_cleanup_already_attempted')
        self.closed=True;completed=False
        try:
            self.cleanup=self.diagnostics.cleanup(self.c.finish)
            def clean():
                if (type(self.cleanup) is not dict or self.cleanup.get('all_handles_closed') is not True or
                    self.cleanup.get('allocations_released') is not True or
                    type(self.cleanup.get('unconfirmed_handles')) is not int or self.cleanup['unconfirmed_handles']!=0):raise ValueError()
            self._step('cleanup_validate','cleanup_unconfirmed',clean)
            now=self._guard('final_guard')
            def state():
                if (self.meter.cleanup_exceeded or self.trace.exceeded or self.diagnostics.exceeded or
                    self.diagnostics.first_failure is not None or self.stopped or self.stage!=6 or
                    self.session.arms!=['disabled','enabled']):raise ValueError()
            self._step('state_validate','audit_failed',state)
            date=datetime.fromtimestamp(now[0]/1000,timezone.utc).date().isoformat()
            self.audit=self._step('window_match','audit_failed',lambda:match_evidence(self.rows,self.c.probes,
                PrivateProof(True,True,True,True,True,True,True,True,date)))
            self._step('final_trace','budget_rejected',lambda:self.trace.run('final_audit',lambda:True))
            completed=True
        except (Exception,KeyboardInterrupt) as error:
            self.stopped=True;self.session.stop()
            if not isinstance(error,DiagnosticFailure071):self.diagnostics.failure('diagnostic_budget','unexpected_failure')
            failure=self.diagnostics.first_failure;self.reason=failure['step']+':'+failure['code']
        self.final_result=dict(completed=completed,stop_reason=None if completed else self.reason,
            audit=self.audit,counts=dict(self.meter.counts),cleanup=self.cleanup,diagnostics=self.diagnostics.public(),
            native_mql_verified=False,native_publication_verified=False,quote_reads=0,history_reads=0,
            orders=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
        return self.final_result


def inspect_prior071(r):
    """Summarize already-audited070 evidence without inventing a root cause."""
    try:
        c=r['counts'];trace=r['stage_trace']
        if (r['completed'] is not False or r['stopped_stage']!='independent_controls' or
            r['stop_reason']!='native_runtime_failed_details_redacted' or c['commands']!=5 or
            c['schedule_waits']!=0 or c['log_reads']!=0 or r['records'] or
            [p['stage'] for p in r['probes']]!=['pre','pre'] or
            len([e for e in trace if e['stage']=='independent_controls'])!=1 or
            r['script_arms']!=['disabled','enabled']):raise ValueError()
        return dict(observed_stop='before_first_wait_or_independent_control',exact_failed_substep_known=False,
            candidate_steps=['probe_guard_before','probe_launch_window','wait5_budget'],
            launch_deadline_ms=10000,deadline_measured_after_full_guard=True,
            recorded_arm_time_available=False,recorded_command_receipt_time_available=False,
            recorded_guard_duration_available=False,root_cause_proven=False,
            native_bootstrap_passed=r['native_private_bootstrap_passed'],
            guarded_hash_bytes=c['hash_bytes'],guards=c['guards'],elapsed_us=r['elapsed_us'],
            native_experiment_repeated=False,orders_available=False)
    except Exception:raise ProbeRejected('prior_diagnostic_inputs_rejected') from None
