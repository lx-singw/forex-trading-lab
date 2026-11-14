"""Fresh072 offline integration. No SDK import, dispatch, compilation or orders.

Native backend construction is only available to a future separately gated
caller; importing this module performs no Windows operations.
"""
from datetime import datetime,timezone
import json
import os
from pathlib import Path,PureWindowsPath

from .mql_sharing_072 import PHASE,DATE,SANDBOX,DATA,PrivateProof,match_evidence,records_from_log
from .sharing_probe_062 import ProbeRejected,Stamp,validate_stamp
from .sharing_runtime_069 import Meter069,Reservation069,Trace069,LIMITS069,ObservedCompanion069
from .sharing_runtime_066 import COMMANDS,digest
from .sharing_diagnostics_071 import Runtime071,Diagnostics071,DiagnosticFailure071
from .sharing_companion_065 import Companion065
from .sharing_session_065 import SavedRange065
from .private_guard_065 import FullGuard065
from .native_files_065 import NativeFiles065

SOURCE_INPUTS=('mt5/Scripts/ForexDemoSharing072.mq5','mt5/Scripts/SharingHold072.mqh',
    'mt5/Scripts/ClockGuard042.mqh','mt5/Scripts/CaptureReadiness060.mqh')
BINDING_KEYS={'source','hold','ex5','terminal','editor','preparation','policy','helper_profile'}


def source_contract072(bindings):
    if type(bindings) is not dict or set(bindings)!=set(SOURCE_INPUTS):raise ProbeRejected('fresh_source_contract_rejected')
    for value in bindings.values():digest(value)
    return dict(version='sharing_source_contract_072_v1',phase=PHASE,date=DATE,
        input_bindings=dict(bindings),artifact_name='ForexDemoSharing072.ex5',terminal_build=6244,
        maximum_compiler_invocations=1,maximum_native_sessions=0,compiled=False,orders_available=False)


def validate_build072(record,contract,compiler_sha256,terminal_sha256):
    """Strict future build evidence contract; never creates execution permission."""
    try:
        canonical=source_contract072(contract['input_bindings'])
        if type(contract) is not dict or set(contract)!=set(canonical):raise ValueError()
        for k,v in canonical.items():
            if type(contract[k]) is not type(v) or contract[k]!=v:raise ValueError()
        for value in (compiler_sha256,terminal_sha256):digest(value)
        required={'version','phase','date','input_bindings','artifact_name','artifact_sha256',
            'compiler_sha256','terminal_sha256','terminal_build','compiler_invocations','exit_code','errors','warnings'}
        if type(record) is not dict or set(record)!=required:raise ValueError()
        expected=dict(version='sharing_build_072_v1',phase=PHASE,date=DATE,input_bindings=contract['input_bindings'],
            artifact_name=contract['artifact_name'],compiler_sha256=compiler_sha256,terminal_sha256=terminal_sha256,
            terminal_build=6244,compiler_invocations=1,exit_code=0,errors=0,warnings=0)
        for k,v in expected.items():
            if type(record[k]) is not type(v) or record[k]!=v:raise ValueError()
        digest(record['artifact_sha256'])
        return dict(build_contract_matched=True,artifact_sha256=record['artifact_sha256'],
            phase=PHASE,orders_available=False,native_mql_verified=False)
    except Exception:raise ProbeRejected('fresh_build_contract_rejected') from None


class Meter072(Meter069):
    def check(self):
        # Older Meter065 calls the immutable Oct7 clock_sample047. Use a fresh
        # Oct8 sampler without changing its shape, skew, expiry or sample caps.
        self.counts['clock_samples']+=1
        if self.counts['clock_samples']>LIMITS069['clock_samples']:raise ProbeRejected('clock_budget_exhausted')
        try:
            now=self.clock()
            if type(now) is not tuple or len(now)!=3 or any(type(x) is not int or x<0 for x in now):raise ValueError()
            if datetime.fromtimestamp(now[0]//1000,timezone.utc).date().isoformat()!=DATE:
                raise ProbeRejected('fresh_date_rejected')
        except ProbeRejected:raise
        except Exception:raise ProbeRejected('fresh_clock_rejected') from None
        if self.first is None:self.first=self.last=now
        if any(a<b for a,b in zip(now,self.last)):raise ProbeRejected('clock_reversed')
        d=tuple(a-b for a,b in zip(now,self.first));self.last=now;self.elapsed_us=d[1]//1000
        if max(d[0],d[2])>=900000 or d[1]>=900000000000:raise ProbeRejected('session_expired')
        if abs(d[0]-d[1]//1000000)>1000 or abs(d[2]-d[1]//1000000)>1000:
            raise ProbeRejected('clock_discontinuity')
        return now


class Reservation072(Reservation069):
    def __init__(self,path,bindings,meter):
        if type(meter) is not Meter072 or type(bindings) is not dict or set(bindings)!=BINDING_KEYS:
            raise ProbeRejected('fresh_reservation_binding_rejected')
        for value in bindings.values():digest(value)
        self.meter=meter;self.arms=[];self.spent=False;self.stopped=False
        meter.consume('reservation_writes')
        value=dict(version='sharing_reservation_072_v1',phase=PHASE,mql_phase=PHASE,date=DATE,
            bindings=dict(bindings),maximum_launches=2,maximum_sdk_connections=1,maximum_log_reads=1,
            maximum_log_bytes=65536,maximum_receipt_permissions=0,orders_available=False)
        try:
            with Path(path).open('xb') as f:
                f.write((json.dumps(value,sort_keys=True)+'\n').encode('ascii'));f.flush();os.fsync(f.fileno())
        except Exception:raise ProbeRejected('fresh_reservation_unavailable') from None


class SavedRange072(SavedRange065):
    def read(self):
        if self.used:raise ProbeRejected('saved_log_unavailable')
        self.used=True;self.meter.consume('log_reads')
        try:
            self._check_path();before=self.path.stat();end=before.st_size;n=end-self.offset
            if (before.st_dev,before.st_ino)!=self.identity or not 0<n<=65536 or n%2:raise ValueError()
            self.meter.consume('log_bytes',n)
            with self.path.open('rb') as stream:
                current=os.fstat(stream.fileno())
                if (current.st_dev,current.st_ino,current.st_size)!=(before.st_dev,before.st_ino,end):raise ValueError()
                stream.seek(self.offset);raw=stream.read(n)
            self._check_path();after=self.path.stat();self.meter.check()
            if (after.st_dev,after.st_ino,after.st_size)!=(before.st_dev,before.st_ino,end) or len(raw)!=n:raise ValueError()
            rows=records_from_log(raw)
            if not rows:raise ValueError()
            return rows
        except Exception:raise ProbeRejected('saved_log_rejected') from None


def terminal_paths072(data_root):
    parent=PureWindowsPath(data_root)/'MQL5'/'Files';root=parent/SANDBOX
    return parent,root,root/'synthetic.bin'


class NativeFiles072(NativeFiles065):
    def __init__(self,meter,parent,scope):
        if type(meter) is not Meter072 or scope!='terminal':raise ProbeRejected('fresh_native_scope_rejected')
        # Parent/ABI/API binding checks only; base constructor performs no file IO.
        super().__init__(meter,parent,scope)
        self.root=self.parent/SANDBOX;self.fixture=self.root/'synthetic.bin'
        if len(str(self.fixture))>=248:raise ProbeRejected('local_path_rejected')


class FullGuard072(FullGuard065):
    def __init__(self,*args):
        if not args or type(args[-1]) is not Meter072:raise ProbeRejected('fresh_guard_meter_rejected')
        super().__init__(*args)
    def bind_files(self,files):
        parent,root,fixture=terminal_paths072(self.data_root)
        if (type(files) is not NativeFiles072 or files.scope!='terminal' or
            any(str(a).casefold()!=str(b).casefold() for a,b in
                ((files.parent,parent),(files.root,root),(files.fixture,fixture)))):
            raise ProbeRejected('fresh_file_binding_rejected')
        return super().bind_files(files)


class Companion072(Companion065):
    def prepare(self):
        if self.used:raise ProbeRejected('session_unavailable')
        self.used=True;self.stage='preparing'
        if getattr(self.api,'scope',None)=='terminal':
            if type(self.guard) is not FullGuard072:raise ProbeRejected('private_guard_rejected')
            self.guard.bind_files(self.api)
        self.call(self.api.setup)
        d=self.opened('directory');s=self.call(self.api.stamp,d,True)
        if (type(s) is not Stamp or s.directory is not True or s.security_verified is not True or
            s.path_verified is not True or s.reparse is not False):raise ProbeRejected('private_directory_binding_rejected')
        w=self.opened('writer');self.identity=validate_stamp(self.call(self.api.stamp,w),0,0)
        n=self.call(self.api.write,w,DATA)
        if type(n) is not int or n!=84:raise ProbeRejected('synthetic_write_rejected')
        self.stamped(w,84);self.close(w)
        self.metadata=self.opened('metadata');self.stamped(self.metadata,-1);self.controls('pre')
        self.seal=self.opened('seal');self.stamped(self.seal,0)
        raw,n=self.call(self.api.read,self.seal,84)
        if type(raw) is not bytes or type(n) is not int or n!=84 or raw!=DATA:raise ProbeRejected('synthetic_read_rejected')
        self.stamped(self.seal,84);self.stage='sealed'


class Diagnostics072(Diagnostics071):
    def public(self):return {**super().public(),'version':'sharing_diagnostics_072_v1','phase':PHASE}


class Runtime072(Runtime071):
    def __init__(self,*args,trace):
        if len(args)!=6 or type(args[1]) is not Reservation072 or type(args[2]) is not Meter072:
            raise ProbeRejected('fresh_runtime_dependencies_rejected')
        companion,session,meter,guard=args[:4]
        if (type(companion) is not ObservedCompanion069 or type(companion.core) is not Companion072 or
            companion.trace is not trace or session.meter is not meter or companion.core.meter is not meter):
            raise ProbeRejected('fresh_runtime_dependencies_rejected')
        if getattr(companion.core.api,'scope',None)=='terminal' and (
            type(guard) is not FullGuard072 or companion.core.guard is not guard or guard.meter is not meter):
            raise ProbeRejected('fresh_runtime_dependencies_rejected')
        super().__init__(*args,trace=trace);self.diagnostics=Diagnostics072(self.meter)
    def _body(self,command):
        self._step('command_order','order_rejected',lambda:self._order(command))
        if command=='probe':
            now=self._step('probe_received','clock_rejected',self.meter.check)
            self.diagnostics.metric('arm_to_probe_receipt_ms',now[2]-self.armed_boot)
        self._step('command_budget','budget_rejected',lambda:self.meter.consume('commands'))
        self._guard('probe_guard_before' if command=='probe' else 'command_guard_before')
        if command=='baseline-saved':
            self.range=self._step('baseline_anchor','saved_log_failed',lambda:SavedRange072(self.log,self.meter))
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
            self._step('final_trace','budget_rejected',lambda:self.trace.run('final_audit',lambda:True));completed=True
        except (Exception,KeyboardInterrupt) as error:
            self.stopped=True;self.session.stop()
            if not isinstance(error,DiagnosticFailure071):self.diagnostics.failure('diagnostic_budget','unexpected_failure')
            failure=self.diagnostics.first_failure;self.reason=failure['step']+':'+failure['code']
        self.final_result=dict(completed=completed,stop_reason=None if completed else self.reason,phase=PHASE,date=DATE,
            audit=self.audit,counts=dict(self.meter.counts),cleanup=self.cleanup,diagnostics=self.diagnostics.public(),
            native_mql_verified=False,native_publication_verified=False,quote_reads=0,history_reads=0,
            orders=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
        return self.final_result
