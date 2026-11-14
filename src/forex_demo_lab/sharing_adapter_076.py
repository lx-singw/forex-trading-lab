"""Source-bound adapter preparation. No SDK import or native entry point.

Timing bounds are assumptions for admission, never measured native permission.
The caller owns Resources069 before construction and closes it on every exit.
"""
from dataclasses import dataclass,field
import hashlib
import json
import os
from pathlib import Path
import re
from threading import Lock

from .clock_observer_042 import unique_pairs
from .sharing_build_075 import build_record075
from .sharing_integration_072 import (SOURCE_INPUTS,BINDING_KEYS,source_contract072,
    Meter072,Reservation072,Runtime072,ObservedCompanion069,Companion072,PHASE as SOURCE_PHASE,DATE)
from .sharing_runtime_069 import Resources069,no_reparse069,close_owned069
from .sharing_runtime_066 import digest
from .sharing_probe_062 import ProbeRejected

PHASE='76000000000000000000000000000001'


def exact076(value,expected):
    if type(value) is not type(expected):return False
    if type(expected) is dict:
        return set(value)==set(expected) and all(exact076(value[k],v) for k,v in expected.items())
    if type(expected) in (list,tuple):
        return len(value)==len(expected) and all(exact076(a,b) for a,b in zip(value,expected))
    return value==expected


def encoded076(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')


@dataclass(frozen=True)
class VerifiedBuild076:
    raw:bytes=field(repr=False)
    def __post_init__(self):
        try:
            if type(self.raw) is not bytes or not 0<len(self.raw)<=4096:raise ValueError()
            r=json.loads(self.raw.decode('ascii'),object_pairs_hook=unique_pairs)
            expected=build_record075(source_contract072(r['input_bindings']),r['compiler_exit_code'],
                'Result: 0 errors, 0 warnings, retained summary\n',
                dict(sha256=r['artifact_sha256'],size=r['artifact_bytes'],raw=None),
                r['compiler_sha256'],r['terminal_sha256'])
            if not exact076(r,expected) or self.raw!=encoded076(expected):raise ValueError()
        except Exception:raise ProbeRejected('adapter_build_rejected') from None
    def record(self):return json.loads(self.raw)
    @property
    def sha256(self):return hashlib.sha256(self.raw).hexdigest()


def validate_build076(record,contract,log_text,artifact,compiler_sha256,terminal_sha256):
    """Validate actual075 exit1/log/artifact against independently pinned inputs."""
    try:
        expected=build_record075(contract,record['compiler_exit_code'],log_text,artifact,
            compiler_sha256,terminal_sha256)
        if not exact076(record,expected):raise ValueError()
        return VerifiedBuild076(encoded076(expected))
    except Exception:raise ProbeRejected('adapter_build_rejected') from None


def runtime_bindings076(build,preparation,policy,profile):
    if type(build) is not VerifiedBuild076:raise ProbeRejected('adapter_build_rejected')
    r=build.record()
    return dict(source=r['input_bindings'][SOURCE_INPUTS[0]],hold=r['input_bindings'][SOURCE_INPUTS[1]],
        ex5=r['artifact_sha256'],terminal=r['terminal_sha256'],editor=r['compiler_sha256'],
        preparation=digest(preparation),policy=digest(policy),helper_profile=digest(profile))


@dataclass(frozen=True)
class TimingBounds076:
    guard_ms:int
    manual_launch_ms:int
    command_delay_ms:int
    native_call_ms:int
    overhead_ms:int=0
    wait_overshoot_ms:int=15000
    def __post_init__(self):
        if any(type(x) is not int or not 0<=x<=10000 for x in
            (self.guard_ms,self.manual_launch_ms,self.command_delay_ms,self.native_call_ms,self.overhead_ms)):
            raise ProbeRejected('adapter_timing_rejected')
        if type(self.wait_overshoot_ms) is not int or not 0<=self.wait_overshoot_ms<=15000:
            raise ProbeRejected('adapter_timing_rejected')
    def report(self):
        g,u,c,n=self.guard_ms,self.manual_launch_ms,self.command_delay_ms,self.native_call_ms
        # One post-arm guard, one probe guard; then two wait guards and12
        # independent-control guards (six metadata/open calls, before+after).
        launch=2*g+u+c+self.overhead_ms
        latest_start=g+u+self.overhead_ms
        complete=16*g+u+c+5000+6*n+self.overhead_ms+self.wait_overshoot_ms
        gate=launch<=10000
        start=latest_start+250<5000
        end=complete<30000-250
        return dict(version='sharing_timing_076_v1',bounds=vars(self).copy(),
            launch_gate_upper_ms=launch,latest_mql_start_ms=latest_start,
            independent_start_lower_ms=5000,independent_completion_upper_ms=complete,
            launch_gate_fits=gate,start_margin_fits=start,end_margin_fits=end,
            modeled_admission=gate and start and end,assumed_bounds_only=True,
            requires_native_timing_evidence=True,runtime_authorized=False,
            native_mql_verified=False,orders_available=False)
    def require(self):
        if not self.report()['modeled_admission']:raise ProbeRejected('adapter_schedule_infeasible')


def dispatch_value076(build,preparation,policy,profile,timing):
    if type(timing) is not TimingBounds076:raise ProbeRejected('adapter_timing_rejected')
    timing.require();bindings=runtime_bindings076(build,preparation,policy,profile)
    return dict(version='sharing_dispatch_076_v1',phase=PHASE,source_phase=SOURCE_PHASE,date=DATE,
        bindings=bindings,build_record_sha256=build.sha256,timing=timing.report(),
        dispatch_consumed=True,maximum_sessions=1,execution_authorized=False,orders_available=False)


@dataclass(frozen=True)
class Dispatch076:
    raw:bytes=field(repr=False)
    used:bool=field(default=False,init=False)
    lock:object=field(default_factory=Lock,init=False,repr=False,compare=False)
    def __post_init__(self):
        if type(self.raw) is not bytes or not 0<len(self.raw)<=4096:raise ProbeRejected('adapter_dispatch_rejected')
    @property
    def sha256(self):return hashlib.sha256(self.raw).hexdigest()
    def claim(self,expected):
        with self.lock:
            if self.used or self.raw!=encoded076(expected):raise ProbeRejected('adapter_dispatch_rejected')
            object.__setattr__(self,'used',True)


def reserve_dispatch076(path,build,preparation,policy,profile,timing):
    raw=encoded076(dispatch_value076(build,preparation,policy,profile,timing))
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return Dispatch076(raw)


def reservation_bytes076(raw,expected_sha,bindings):
    try:
        if type(raw) is not bytes or not 0<len(raw)<=4096 or hashlib.sha256(raw).hexdigest()!=digest(expected_sha):raise ValueError()
        if type(bindings) is not dict or set(bindings)!=BINDING_KEYS:raise ValueError()
        for h in bindings.values():digest(h)
        r=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
        expected=dict(version='sharing_reservation_072_v1',phase=SOURCE_PHASE,mql_phase=SOURCE_PHASE,date=DATE,
            bindings=bindings,maximum_launches=2,maximum_sdk_connections=1,maximum_log_reads=1,
            maximum_log_bytes=65536,maximum_receipt_permissions=0,orders_available=False)
        if not exact076(r,expected):raise ValueError()
        return r
    except Exception:raise ProbeRejected('adapter_reservation_rejected') from None


class Adapter076:
    def __init__(self,build,preparation,policy,profile,timing,dispatch,bindings,reservation_raw,reservation_sha,
                 companion,session,meter,guard,log,wait,owner,trace):
        if (type(owner) is not Resources069 or owner.session is not session or owner.meter is not meter or
            owner.trace is not trace or owner.closed or owner.runner is not None or
            type(companion) is not ObservedCompanion069 or type(companion.core) is not Companion072 or
            owner.files is not companion.core.api or
            type(session) is not Reservation072 or type(meter) is not Meter072 or session.meter is not meter):
            raise ProbeRejected('adapter_ownership_rejected')
        if not exact076(bindings,runtime_bindings076(build,preparation,policy,profile)):
            raise ProbeRejected('adapter_bindings_rejected')
        reservation_bytes076(reservation_raw,reservation_sha,bindings)
        if type(timing) is not TimingBounds076:raise ProbeRejected('adapter_timing_rejected')
        timing.require()
        if type(dispatch) is not Dispatch076:raise ProbeRejected('adapter_dispatch_rejected')
        dispatch.claim(dispatch_value076(build,preparation,policy,profile,timing))
        self.runtime=Runtime072(companion,session,meter,guard,log,wait,trace=trace)
        self.owner,self.build,self.timing,self.dispatch=owner,build,timing,dispatch
        self.closed=False;self.reason=None
        owner.runner=self.runtime
    def command(self,command):
        if self.closed or self.reason:raise ProbeRejected('adapter_session_unavailable')
        before=len(self.runtime.diagnostics.events)
        result=self.runtime.command(command)
        for e in self.runtime.diagnostics.events[before:]:
            if e['step'].endswith('_guard_before') or e['step'].endswith('_guard_after'):
                if e['duration_ms'] is None or e['duration_ms']>self.timing.guard_ms:
                    self.reason='adapter_guard_bound_exceeded';self.runtime.stopped=True
                    self.runtime.session.stop();raise ProbeRejected(self.reason)
        if command=='probe':
            waited=self.runtime.diagnostics.metrics['wait5_elapsed_ms']
            if waited is None or waited>5000+self.timing.guard_ms+self.timing.wait_overshoot_ms+self.timing.overhead_ms:
                self.reason='adapter_wait_bound_exceeded';self.runtime.stopped=True
                self.runtime.session.stop();raise ProbeRejected(self.reason)
        return result
    def finish(self):
        if self.closed:raise ProbeRejected('adapter_cleanup_already_attempted')
        self.closed=True;out=close_owned069(self.owner)
        completed=bool(out['outcome'] and out['outcome']['completed'] and not out['errors'] and not self.reason)
        return dict(version='sharing_adapter_076_v1',phase=PHASE,source_phase=SOURCE_PHASE,
            modeled_completed=completed,build_record_sha256=self.build.sha256,
            adapter_stop_reason=self.reason,ownership=out,timing=self.timing.report(),
            runtime_authorized=False,native_mql_verified=False,native_publication_verified=False,
            orders_available=False,fresh_performance_eligible=False,annual_eligible=False)


def deploy_owned076(source,scripts,name,build,reader,guard,meter):
    """Future gated caller only; preparation tests use temporary synthetic files."""
    if type(build) is not VerifiedBuild076:raise ProbeRejected('adapter_build_rejected')
    record=build.record();expected=record['artifact_sha256']
    if re.fullmatch('ForexDemoLab076-[0-9a-f]{32}',name) is None:raise ProbeRejected('adapter_deployment_rejected')
    source,scripts=Path(source),Path(scripts)
    if source.name!=record['artifact_name']:raise ProbeRejected('adapter_deployment_rejected')
    if hasattr(guard,'data_root') and scripts!=Path(guard.data_root)/'MQL5'/'Scripts':
        raise ProbeRejected('adapter_deployment_rejected')
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    no_reparse069(source,meter);no_reparse069(scripts,meter)
    if reader.hash_file(source)!=expected:raise ProbeRejected('runtime_binding_rejected')
    if source.stat().st_size!=record['artifact_bytes']:raise ProbeRejected('runtime_binding_rejected')
    meter.consume('deployment_directories');directory=scripts/name;directory.mkdir(exist_ok=False)
    no_reparse069(directory,meter)
    deployed=directory/'ForexDemoSharing072.ex5';meter.consume('deployment_writes')
    with source.open('rb') as src,deployed.open('xb') as dst:
        while True:
            meter.check();raw=src.read(65536)
            if not raw:break
            meter.consume('deployment_bytes',len(raw));dst.write(raw)
        dst.flush();os.fsync(dst.fileno())
    no_reparse069(deployed,meter)
    if reader.hash_file(source)!=expected or reader.hash_file(deployed)!=expected:
        raise ProbeRejected('runtime_binding_rejected')
    if guard() is not True:raise ProbeRejected('runtime_guard_rejected')
    return deployed
