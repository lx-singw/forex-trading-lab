"""Finite synthetic sharing orchestration. No market or order capability.

Dependencies are injected here; only the separately gated Windows entry point
may produce native evidence. A saved final log is retrospective proof only.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from .sharing_companion_065 import Meter065, LIMITS
from .sharing_probe_062 import ProbeRejected
from .sharing_session_065 import SavedRange065
from .mql_sharing_064 import DATE, PHASE as MQL_PHASE, PrivateProof, match_evidence
from .private_guard_065 import Identity065

PHASE = '66000000000000000000000000000001'
LIMITS066 = {**LIMITS, 'guards':128, 'process_opens':512, 'identity_tokens':512, 'token_queries':2048,
    'deployment_directories':1, 'deployment_writes':1, 'deployment_bytes':1048576,
    'trust_queries':1, 'sdk_shutdowns':1, 'commands':6, 'schedule_waits':2}


class Meter066(Meter065):
    def __init__(self, clock):
        super().__init__(clock)
        self.counts.update({k:0 for k in LIMITS066 if k not in self.counts})
    def consume(self, key, amount=1):
        self.check()
        if (key not in LIMITS066 or type(amount) is not int or amount<1 or
                self.counts[key]+amount>LIMITS066[key]):
            raise ProbeRejected('runtime_budget_rejected')
        self.counts[key]+=amount
    def cleanup(self,key):
        self.counts[key]+=1
        if self.counts[key]>LIMITS066[key]:self.cleanup_exceeded=True


def digest(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None:
        raise ProbeRejected('runtime_binding_rejected')
    return value


class Reservation066:
    def __init__(self,path,bindings,meter):
        if type(bindings) is not dict or set(bindings)!={'source','ex5','terminal','editor','preparation','policy'}:
            raise ProbeRejected('runtime_binding_rejected')
        for value in bindings.values():digest(value)
        self.meter=meter;self.arms=[];self.spent=False;self.stopped=False
        meter.consume('reservation_writes')
        try:
            with Path(path).open('xb') as f:
                f.write((json.dumps(dict(version='sharing_reservation_066_v1',phase=PHASE,
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


class PrivateReader066:
    """Recheck helper identity on EACH peer identity check, without hash caches."""
    def __init__(self,base,helper):
        if type(helper) is not Identity065:raise ProbeRejected('runtime_identity_rejected')
        self.base,self.helper=base,helper
    def unique_pid(self):return self.base.unique_pid()
    def hash_file(self,path):return self.base.hash_file(path)
    def identity(self,pid):
        helper=self.base.identity(self.helper.pid)
        peer=self.base.identity(pid)
        if (helper!=self.helper or peer.session!=helper.session or peer.logon!=helper.logon):
            raise ProbeRejected('runtime_identity_rejected')
        return peer


def attach_existing(sdk,reservation,reader,peer,meter):
    """One initialize attempt after native process proof; no reconnect.

    SDK attachment may have internal blocking/launch behavior; checks cannot
    preempt or guarantee absence of that behavior. Reject any identity change.
    Caller owns shutdown once the attempt has been consumed, including failure.
    """
    if sdk.__version__!='5.0.6231':raise ProbeRejected('runtime_sdk_rejected')
    if reader.unique_pid()!=peer.pid or reader.identity(peer.pid)!=peer:
        raise ProbeRejected('runtime_identity_rejected')
    reservation.sdk_attempt()
    if sdk.initialize(peer.image,timeout=15000) is not True:
        raise ProbeRejected('runtime_sdk_rejected')
    meter.check()
    if reader.unique_pid()!=peer.pid or reader.identity(peer.pid)!=peer:
        raise ProbeRejected('runtime_identity_rejected')


def no_reparse(path):
    for p in (path,*path.parents):
        if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:
            raise ProbeRejected('runtime_path_rejected')


def deploy_owned(source,scripts,name,expected,reader,guard,meter):
    """Exclusive copy into one declared own folder; never overwrites/removes."""
    digest(expected)
    if re.fullmatch('ForexDemoLab066-[0-9a-f]{32}',name) is None:
        raise ProbeRejected('runtime_deployment_rejected')
    source,scripts=Path(source),Path(scripts)
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    no_reparse(source);no_reparse(scripts)
    if reader.hash_file(source)!=expected:raise ProbeRejected('runtime_binding_rejected')
    meter.consume('deployment_directories');directory=scripts/name
    directory.mkdir(exist_ok=False);no_reparse(directory)
    deployed=directory/'ForexDemoSharing064.ex5'
    meter.consume('deployment_writes')
    with source.open('rb') as src,deployed.open('xb') as dst:
        while True:
            meter.check();raw=src.read(65536)
            if not raw:break
            meter.consume('deployment_bytes',len(raw));dst.write(raw)
        dst.flush();os.fsync(dst.fileno())
    no_reparse(deployed)
    if reader.hash_file(source)!=expected or reader.hash_file(deployed)!=expected:
        raise ProbeRejected('runtime_binding_rejected')
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    return deployed


COMMANDS=('baseline-saved','arm-disabled','disabled-done','arm-enabled','probe','logs-saved')


class Runtime066:
    def __init__(self,companion,reservation,meter,guard,log,wait):
        self.c,self.session,self.meter,self.guard=companion,reservation,meter,guard
        self.log,self.wait=log,wait;self.stage=0;self.range=None;self.rows=[]
        self.armed_boot=None;self.stopped=False;self.cleanup=None;self.closed=False
        self.audit=None;self.reason=None
    def checked(self):
        if self.guard() is not True:raise ProbeRejected('runtime_guard_rejected')
        return self.meter.check()
    def pause(self,milliseconds):
        self.meter.consume('schedule_waits');start=self.checked()[2]
        # At most 36 one-second waits. No log polling or retry of file controls.
        for _ in range(36):
            now=self.meter.check()[2]
            if now-start>=milliseconds:break
            self.wait(min(1000,milliseconds-(now-start)))
        else:raise ProbeRejected('runtime_schedule_rejected')
        end=self.checked()[2]
        if not milliseconds<=end-start<=milliseconds+15000:
            raise ProbeRejected('runtime_schedule_rejected')
    def command(self,command):
        try:
            if self.stopped or self.closed or self.stage>=len(COMMANDS) or command!=COMMANDS[self.stage]:
                raise ProbeRejected('runtime_command_rejected')
            self.meter.consume('commands');self.checked()
            if command=='baseline-saved':self.range=SavedRange065(self.log,self.meter)
            elif command=='arm-disabled':self.session.arm('disabled')
            elif command=='disabled-done':self.c.prepare()
            elif command=='arm-enabled':
                self.c.release_seal();self.session.arm('enabled');self.armed_boot=self.meter.check()[2]
            elif command=='probe':
                if not 0<=self.meter.check()[2]-self.armed_boot<=10000:
                    raise ProbeRejected('runtime_launch_window_rejected')
                self.pause(5000);self.c.controls('independent')
                self.pause(35000);self.c.stage='post';self.c.controls('post')
            elif command=='logs-saved':
                self.rows=self.range.read()
            self.checked();self.stage+=1
            return dict(status=command,maximum_launches=2,quote_reads=0,orders_available=False)
        except Exception:
            self.stopped=True;self.session.stop();self.reason='runtime_step_failed_details_redacted'
            raise ProbeRejected(self.reason) from None
    def finish(self):
        if self.closed:raise ProbeRejected('runtime_cleanup_already_attempted')
        self.closed=True
        try:
            self.cleanup=self.c.finish()
            if (self.cleanup.get('all_handles_closed') is not True or
                self.cleanup.get('allocations_released') is not True or
                type(self.cleanup.get('unconfirmed_handles')) is not int or self.cleanup['unconfirmed_handles']!=0):
                raise ValueError()
            self.checked()
            if self.meter.cleanup_exceeded or self.stopped or self.stage!=6 or self.session.arms!=['disabled','enabled']:
                raise ValueError()
            date=datetime.fromtimestamp(self.meter.check()[0]/1000,timezone.utc).date().isoformat()
            # This matcher remains an injected audit. Native entry point must
            # separately bind actual backend/bootstrap/deployment/log evidence.
            proof=PrivateProof(True,True,True,True,True,True,True,True,date)
            self.audit=match_evidence(self.rows,self.c.probes,proof)
            return dict(completed=True,audit=self.audit,counts=dict(self.meter.counts),
                cleanup=self.cleanup,native_mql_verified=False,native_publication_verified=False,
                quote_reads=0,history_reads=0,orders=0,orders_available=False,
                fresh_performance_eligible=False,annual_eligible=False)
        except Exception:
            self.stopped=True;self.session.stop()
            self.reason=self.reason or 'runtime_final_audit_rejected'
            return dict(completed=False,stop_reason=self.reason,counts=dict(self.meter.counts),
                cleanup=self.cleanup,native_mql_verified=False,native_publication_verified=False,
                quote_reads=0,history_reads=0,orders=0,orders_available=False,
                fresh_performance_eligible=False,annual_eligible=False)
