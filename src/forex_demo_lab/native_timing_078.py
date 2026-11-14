"""Source-bound metadata entry orchestration. No SDK import or market API.

The native078 dispatcher is fresh; its component reservation uses the immutable
077 proposal schema with new078 preparation/policy bindings. Neither proposal
nor a modeled result is authority. Only exact separate authorization is accepted.
"""
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
from threading import Lock

from .clock_observer_042 import unique_pairs
from .sharing_adapter_076 import VerifiedBuild076,encoded076,exact076
from .sharing_integration_072 import SOURCE_INPUTS
from .sharing_runtime_066 import digest
from .sharing_runtime_069 import Resources069,Trace069,bootstrap,close_owned069,no_reparse069
from .private_guard_065 import Metadata065,FullGuard065
from .image_guard_068 import HelperChain068
from .sharing_probe_062 import ProbeRejected
from .timing_profile_077 import (Meter077,Reservation077,ProfileGuard077,profile_once077,
    profile_contract077,LIMITS077,DATE,SAMPLES)

PHASE='78000000000000000000000000000001'


class Trace078(Trace069):
    def enter(self,name):
        if name!='profile_samples': return super().enter(name)
        if len(self.events)>=32:
            self.exceeded=True;raise ProbeRejected('runtime_stage_budget_rejected')
        self.current=name;self.events.append(dict(stage=name,started=True,completed=False))
        return len(self.events)-1


def authorization078(preparation,policy,profile,ledger,entry,build,component):
    for h in (preparation,policy,profile,ledger,entry,build,component): digest(h)
    return dict(version='native_timing_authorization_078_v1',phase=PHASE,date=DATE,
        preparation_sha256=preparation,policy_sha256=policy,helper_profile_sha256=profile,
        ledger_sha256=ledger,entry_sha256=entry,build_record_sha256=build,
        component_contract_sha256=component,maximum_native_sessions=1,
        maximum_sdk_connections=1,fixed_samples=SAMPLES,full_guards=8,
        limits=dict(LIMITS077),maximum_script_launches=0,maximum_deployments=0,
        maximum_terminal_log_reads=0,maximum_market_reads=0,maximum_orders=0,
        maximum_receipt_permissions=0,execution_authorized=True,
        sharing_launch_authorized=False,latency_guaranteed=False,orders_available=False)


def validate_authorization078(raw,expected,expected_sha):
    try:
        if type(raw) is not bytes or not 0<len(raw)<=8192 or hashlib.sha256(raw).hexdigest()!=digest(expected_sha):
            raise ValueError()
        value=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
        if not exact076(value,expected) or raw!=encoded076(expected): raise ValueError()
        if value['phase']!=PHASE or value['execution_authorized'] is not True or value['orders_available'] is not False:
            raise ValueError()
        return value
    except Exception: raise ProbeRejected('timing_authorization_rejected') from None


def dispatch_value078(auth,auth_sha):
    digest(auth_sha)
    return dict(version='native_timing_dispatch_078_v1',phase=PHASE,date=DATE,
        authorization_sha256=auth_sha,preparation_sha256=auth['preparation_sha256'],
        policy_sha256=auth['policy_sha256'],component_contract_sha256=auth['component_contract_sha256'],
        dispatch_consumed=True,maximum_native_sessions=1,maximum_sdk_connections=1,orders_available=False)


@dataclass(frozen=True)
class Dispatch078:
    raw:bytes=field(repr=False)
    used:bool=field(default=False,init=False)
    lock:object=field(default_factory=Lock,init=False,repr=False,compare=False)
    def claim(self,expected):
        with self.lock:
            if self.used or type(self.raw) is not bytes or self.raw!=encoded076(expected):
                raise ProbeRejected('timing_dispatch_rejected')
            object.__setattr__(self,'used',True)


def reserve_dispatch078(path,auth,auth_sha):
    raw=encoded076(dispatch_value078(auth,auth_sha))
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return Dispatch078(raw)


@dataclass(frozen=True)
class Spec078:
    build:VerifiedBuild076
    preparation:str
    policy:str
    profile:str
    chain:HelperChain068=field(repr=False)
    terminal:tuple=field(repr=False)
    editor:tuple=field(repr=False)
    artifact:tuple=field(repr=False)
    source_paths:tuple=field(repr=False)
    sdk_bindings:tuple=field(repr=False)
    def __post_init__(self):
        try:
            if type(self.build) is not VerifiedBuild076 or type(self.chain) is not HelperChain068: raise ValueError()
            for h in (self.preparation,self.policy,self.profile): digest(h)
            r=self.build.record()
            for pair,expected in ((self.terminal,r['terminal_sha256']),(self.editor,r['compiler_sha256']),
                (self.artifact,r['artifact_sha256'])):
                if type(pair) is not tuple or len(pair)!=2 or not str(pair[0]) or pair[1]!=expected: raise ValueError()
            if (type(self.source_paths) is not tuple or len(self.source_paths)!=4 or
                any(type(x) is not tuple or len(x)!=2 or not str(x[1]) for x in self.source_paths) or
                set(n for n,p in self.source_paths)!=set(SOURCE_INPUTS) or
                type(self.sdk_bindings) is not tuple or len(self.sdk_bindings)!=5): raise ValueError()
            for pair in self.sdk_bindings:
                if type(pair) is not tuple or len(pair)!=2 or not str(pair[0]): raise ValueError()
                digest(pair[1])
            profile_contract077(self.build,self.preparation,self.policy,self.profile,self.chain)
        except Exception: raise ProbeRejected('timing_spec_rejected') from None
    @property
    def component_raw(self):
        return encoded076(profile_contract077(self.build,self.preparation,self.policy,self.profile,self.chain))
    @property
    def component_sha256(self): return hashlib.sha256(self.component_raw).hexdigest()


@dataclass(frozen=True)
class Hooks078:
    clock:object=field(repr=False)
    backend:object=field(repr=False)
    reader:object=field(repr=False)
    trust:object=field(repr=False)
    import_sdk:object=field(repr=False)
    loaded_library:object=field(repr=False)
    helper_pid:int=field(repr=False)
    executable:str=field(repr=False)
    base_alias:str=field(repr=False)
    python_version:str


def run_entry078(spec,hooks,authorization_raw,expected_authorization,authorization_sha,
                 dispatch,reservation_path):
    # Validate all raw grants and spend dispatch before any backend/SDK action.
    if type(spec) is not Spec078 or type(hooks) is not Hooks078 or type(dispatch) is not Dispatch078:
        raise ProbeRejected('timing_entry_rejected')
    auth=validate_authorization078(authorization_raw,expected_authorization,authorization_sha)
    if (auth['preparation_sha256']!=spec.preparation or auth['policy_sha256']!=spec.policy or
        auth['helper_profile_sha256']!=spec.profile or auth['build_record_sha256']!=spec.build.sha256 or
        auth['component_contract_sha256']!=spec.component_sha256): raise ProbeRejected('timing_entry_binding_rejected')
    dispatch.claim(dispatch_value078(auth,authorization_sha))
    trace=Trace078();meter=session=owner=observation=cleanup=None
    reason=failed=None;trusted=False
    try:
        meter=Meter077(hooks.clock)
        session=Reservation077(reservation_path,spec.build,spec.preparation,spec.policy,spec.profile,spec.chain,meter)
        owner=Resources069(session,meter,trace) # Own BEFORE construction/bootstrap.
        def construct():
            owner.base=hooks.backend(meter)
            reader=hooks.reader(owner.base)
            if reader.f is not owner.base or reader.meter is not meter: raise ValueError()
            # These immutable installed SDK/shell inputs are never market/log content.
            for path,expected in spec.sdk_bindings:
                if reader.hash_file(path)!=expected: raise ValueError()
            for name,path in spec.source_paths:
                if reader.hash_file(path)!=spec.build.record()['input_bindings'][name]: raise ValueError()
            if reader.hash_file(spec.artifact[0])!=spec.artifact[1]: raise ValueError()
            return reader
        reader=trace.run('preflight',construct)
        def trust():
            nonlocal trusted
            trusted=hooks.trust(meter) is True
            if not trusted: raise ValueError()
            # Hash SDK/shell inputs again after signature subprocess and before import.
            for path,expected in spec.sdk_bindings:
                if reader.hash_file(path)!=expected: raise ValueError()
            return True
        private,peer=bootstrap(reader,spec.terminal,spec.editor,spec.chain,hooks.executable,
            hooks.base_alias,lambda:hooks.loaded_library(owner.base),hooks.helper_pid,hooks.python_version,
            trust,hooks.import_sdk,owner,session,meter,trace)
        session.confirm_attach(owner)
        def metadata():
            info=Metadata065(owner.sdk,meter).terminal_info()
            if info is None or type(info.build) is not int or info.build!=6244 or type(info.data_path) is not str:
                raise ValueError()
            no_reparse069(Path(info.data_path),meter)
            return FullGuard065(owner.sdk,private,peer,info.data_path,6244,spec.editor,spec.artifact,meter)
        core=trace.run('account_metadata',metadata)
        def sample_inputs():
            # Called between the two full account/identity guards in EVERY
            # composite sample, so SDK/config changes cannot go unnoticed.
            for path,expected in spec.sdk_bindings:
                if private.hash_file(path)!=expected: raise ValueError()
            return hooks.loaded_library(owner.base)
        guard=ProfileGuard077(owner,core,spec.build,spec.preparation,spec.policy,spec.profile,
            spec.chain,hooks.executable,hooks.base_alias,sample_inputs,dict(spec.source_paths))
        index=trace.enter('profile_samples')
        observation=profile_once077(owner,guard)
        trace.events[index]['completed']=observation['completed']
        cleanup=observation['cleanup']
        if not observation['completed']: reason='timing_profile_incomplete';failed='profile_samples'
    except (Exception,KeyboardInterrupt):
        reason='timing_entry_failed_details_redacted';failed=trace.current
    finally:
        if session is not None: session.stop()
        if owner is not None and not owner.closed: cleanup=close_owned069(owner)
        if cleanup is not None and cleanup['errors']:
            reason=reason or 'timing_cleanup_unconfirmed';failed=failed or trace.current
    complete=reason is None and trusted and observation is not None and observation['completed']
    return dict(version='native_timing_entry_078_v1',phase=PHASE,date=DATE,entry_completed=complete,
        stop_reason=reason,stopped_stage=failed,stage_trace=trace.public(),
        authorization_sha256=authorization_sha,preparation_sha256=spec.preparation,policy_sha256=spec.policy,
        helper_profile_sha256=spec.profile,build_record_sha256=spec.build.sha256,
        component_contract_sha256=spec.component_sha256,
        reservation_sha256=hashlib.sha256(session.raw).hexdigest() if session else None,
        counts=dict(meter.counts) if meter else None,observation=observation,cleanup=cleanup,
        signature_checks_passed=trusted,observations_only=True,latency_guaranteed=False,
        native_launch_ready=False,native_mql_verified=False,native_publication_verified=False,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False,
        script_launches=0,terminal_deployments=0,terminal_log_content_reads=0,
        market_reads=0,orders=0,receipt_permissions=0)
