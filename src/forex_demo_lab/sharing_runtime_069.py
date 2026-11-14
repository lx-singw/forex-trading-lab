"""Corrected synthetic runtime integration; dependency-injected preparation.

No SDK import or market/order API here. New069 reservation, measured helper
pin, fixed stage diagnostics and cleanup ownership; old066 is immutable.
"""
import json
import os
from pathlib import Path
import stat

from .image_guard_068 import STAGES,HelperChain068
from .private_guard_065 import Identity065
from .sharing_runtime_066 import (Runtime066,PrivateReader066,attach_existing,
    digest,Meter066,LIMITS066)
from .sharing_probe_062 import ProbeRejected
from .mql_sharing_064 import DATE,PHASE as MQL_PHASE

PHASE='69000000000000000000000000000001'
LIMITS069={**LIMITS066,'startup_path_stats':64}


class Meter069(Meter066):
    def __init__(self,clock):super().__init__(clock);self.counts['startup_path_stats']=0
    def consume(self,key,amount=1):
        self.check()
        if key not in LIMITS069 or type(amount) is not int or amount<1 or self.counts[key]+amount>LIMITS069[key]:
            raise ProbeRejected('runtime_budget_rejected')
        self.counts[key]+=amount
    def cleanup(self,key):
        self.counts[key]+=1
        if self.counts[key]>LIMITS069[key]:self.cleanup_exceeded=True


def no_reparse069(path,meter):
    for p in (path,*path.parents):
        meter.consume('startup_path_stats');s=p.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise ProbeRejected('runtime_path_rejected')


class Trace069:
    def __init__(self):self.current='preflight';self.events=[];self.exceeded=False
    def enter(self,name):
        if name not in STAGES or len(self.events)>=32:
            self.exceeded=True;raise ProbeRejected('runtime_stage_budget_rejected')
        self.current=name;self.events.append(dict(stage=name,started=True,completed=False))
        return len(self.events)-1
    def run(self,name,operation,*args):
        i=self.enter(name);value=operation(*args);self.events[i]['completed']=True
        return value
    def cleanup(self,name,operation):
        # Diagnostics never prevent release of an owned handle/SDK connection.
        i=None
        try:i=self.enter(name)
        except Exception:self.exceeded=True
        value=operation()
        if i is not None:self.events[i]['completed']=True
        return value
    def public(self):return [dict(e) for e in self.events]


class Reservation069:
    def __init__(self,path,bindings,meter):
        if type(bindings) is not dict or set(bindings)!={'source','ex5','terminal','editor','preparation','policy','helper_profile'}:
            raise ProbeRejected('runtime_binding_rejected')
        for v in bindings.values():digest(v)
        self.meter=meter;self.arms=[];self.spent=False;self.stopped=False
        meter.consume('reservation_writes')
        try:
            with Path(path).open('xb') as f:
                f.write((json.dumps(dict(version='sharing_reservation_069_v1',phase=PHASE,
                    mql_phase=MQL_PHASE,date=DATE,bindings=bindings,maximum_launches=2,
                    maximum_sdk_connections=1,maximum_log_reads=1,maximum_log_bytes=65536,
                    maximum_receipt_permissions=0,orders_available=False),sort_keys=True)+'\n').encode('ascii'))
                f.flush();os.fsync(f.fileno())
        except Exception:raise ProbeRejected('runtime_reservation_unavailable') from None
    def sdk_attempt(self):
        if self.stopped or self.spent:raise ProbeRejected('runtime_session_unavailable')
        self.spent=True;self.meter.consume('sdk_connections')
    def arm(self,step):
        if self.stopped or len(self.arms)>=2 or step!=('disabled' if not self.arms else 'enabled'):
            self.stopped=True;raise ProbeRejected('runtime_launch_rejected')
        self.meter.consume('script_arms');self.arms.append(step)
    def stop(self):self.stopped=True


def bootstrap(reader,terminal,editor,chain,executable,base_alias,loaded_library,
        helper_pid,python_version,trust,import_sdk,resources,session,meter,trace):
    """Measured/pinned native helper instead of equality with the launcher.

    Actual account guards are mandatory after this metadata-only attach and
    before deployment. Caller owns SDK shutdown as soon as attempt is spent.
    """
    def verify_image(binding):
        if reader.hash_file(binding[0])!=binding[1]:raise ProbeRejected('runtime_binding_rejected')
    trace.run('terminal_image',verify_image,terminal)
    trace.run('editor_image',verify_image,editor)
    if trace.run('signature',trust) is not True:raise ProbeRejected('runtime_trust_rejected')
    def terminal_identity():
        peer=reader.identity(reader.unique_pid())
        if type(peer) is not Identity065 or peer.image!=str(terminal[0]).casefold() or peer.digest!=terminal[1]:
            raise ProbeRejected('runtime_identity_rejected')
        return peer
    peer=trace.run('terminal_process',terminal_identity)
    helper=trace.run('helper_process',reader.identity,helper_pid)
    def check_helper():
        if type(chain) is not HelperChain068 or python_version!='3.13.14':raise ProbeRejected('runtime_helper_rejected')
        chain.check(reader,helper,executable,base_alias,loaded_library())
        if peer.session!=helper.session or peer.logon!=helper.logon:raise ProbeRejected('runtime_identity_rejected')
    trace.run('helper_chain',check_helper)
    private=PrivateReader066(reader,helper)
    resources.sdk=trace.run('sdk_import',import_sdk)
    trace.run('sdk_attach',attach_existing,resources.sdk,session,private,peer,meter)
    return private,peer


class ObservedCompanion069:
    def __init__(self,core,trace):self.core,self.trace=core,trace
    @property
    def stage(self):return self.core.stage
    @stage.setter
    def stage(self,value):self.core.stage=value
    @property
    def probes(self):return self.core.probes
    def prepare(self):return self.trace.run('file_prepare',self.core.prepare)
    def release_seal(self):return self.core.release_seal()
    def controls(self,stage):
        name='independent_controls' if stage=='independent' else 'post_controls'
        return self.trace.run(name,self.core.controls,stage)
    def finish(self):return self.trace.cleanup('file_cleanup',self.core.finish)


class Runtime069(Runtime066):
    def __init__(self,*args,trace):super().__init__(*args);self.trace=trace
    def command(self,command):
        names={'baseline-saved':'saved_log','arm-disabled':'disabled_arm',
            'disabled-done':'file_prepare','arm-enabled':'enabled_arm',
            'probe':'independent_controls','logs-saved':'saved_log'}
        if command not in names:
            self.stopped=True;self.session.stop();raise ProbeRejected('runtime_command_rejected')
        return self.trace.run(names[command],super().command,command)
    def finish(self):
        result=super().finish()
        # The inner core already closes files. Record final audit separately
        # without nesting a parent that might hide the failing cleanup stage.
        try:
            if result['completed']:
                self.trace.run('final_audit',lambda:True)
            elif self.trace.events and self.trace.events[-1]['completed']:
                self.trace.enter('final_audit')
        except ProbeRejected:self.trace.exceeded=True
        if self.trace.exceeded:result['completed']=False;result['stop_reason']='runtime_stage_budget_rejected'
        self.final_result=result
        return result


class Resources069:
    def __init__(self,session,meter,trace):
        self.session,self.meter,self.trace=session,meter,trace
        self.sdk=None;self.base=None;self.files=None;self.runner=None;self.closed=False
    def close(self):
        if self.closed:raise ProbeRejected('runtime_cleanup_already_attempted')
        self.closed=True;outcome=None;base_cleanup=None;file_cleanup=None;shutdown=False;errors=[]
        if self.runner is not None:
            try:
                if not self.runner.closed:outcome=self.runner.finish()
                else:outcome=getattr(self.runner,'final_result',None)
                file_cleanup=outcome.get('cleanup') if outcome else self.runner.cleanup
            except (Exception,KeyboardInterrupt):errors.append('runner_cleanup_unconfirmed')
        elif self.files is not None:
            try:file_cleanup=self.trace.cleanup('file_cleanup',self.files.finish)
            except (Exception,KeyboardInterrupt):errors.append('file_cleanup_unconfirmed')
        if self.base is not None:
            try:base_cleanup=self.trace.cleanup('file_cleanup',self.base.finish)
            except (Exception,KeyboardInterrupt):errors.append('bootstrap_cleanup_unconfirmed')
        for owned,proof in ((self.runner is not None or self.files is not None,file_cleanup),
                            (self.base is not None,base_cleanup)):
            try:
                if owned and (type(proof) is not dict or proof.get('all_handles_closed') is not True or
                    proof.get('allocations_released') is not True or type(proof.get('unconfirmed_handles')) is not int or
                    proof['unconfirmed_handles']!=0):raise ValueError()
            except Exception:errors.append('owned_cleanup_unconfirmed')
        if self.session.spent:
            try:
                self.meter.cleanup('sdk_shutdowns')
                if self.sdk is None:raise ValueError()
                self.trace.cleanup('sdk_cleanup',self.sdk.shutdown);shutdown=True
            except (Exception,KeyboardInterrupt):errors.append('sdk_cleanup_unconfirmed')
        try:self.meter.check()
        except Exception:errors.append('post_cleanup_clock_rejected')
        if self.meter.cleanup_exceeded or self.trace.exceeded:errors.append('cleanup_budget_rejected')
        return dict(outcome=outcome,file_cleanup=file_cleanup,bootstrap_cleanup=base_cleanup,
            sdk_shutdown_called=shutdown,errors=errors)


def close_owned069(resources):
    """Keep a fixed outcome available even if ownership cleanup itself fails."""
    try:return resources.close()
    except (Exception,KeyboardInterrupt):
        return dict(outcome=None,file_cleanup=None,bootstrap_cleanup=None,
            sdk_shutdown_called=False,errors=['resource_cleanup_unconfirmed'])


def deploy_owned069(source,scripts,name,expected,reader,guard,meter):
    import re
    digest(expected)
    if re.fullmatch('ForexDemoLab069-[0-9a-f]{32}',name) is None:raise ProbeRejected('runtime_deployment_rejected')
    source,scripts=Path(source),Path(scripts)
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    no_reparse069(source,meter);no_reparse069(scripts,meter)
    if reader.hash_file(source)!=expected:raise ProbeRejected('runtime_binding_rejected')
    meter.consume('deployment_directories');directory=scripts/name;directory.mkdir(exist_ok=False);no_reparse069(directory,meter)
    deployed=directory/'ForexDemoSharing064.ex5';meter.consume('deployment_writes')
    with source.open('rb') as src,deployed.open('xb') as dst:
        while True:
            meter.check();raw=src.read(65536)
            if not raw:break
            meter.consume('deployment_bytes',len(raw));dst.write(raw)
        dst.flush();os.fsync(dst.fileno())
    no_reparse069(deployed,meter)
    if reader.hash_file(source)!=expected or reader.hash_file(deployed)!=expected:raise ProbeRejected('runtime_binding_rejected')
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    return deployed
