"""Finite, sanitized public preflight steps and one-use entry marker; no SDK."""
import hashlib
import json
import os
from pathlib import Path

from .public_preflight_080 import (PublicInputs080,PublicInputRejected080,
    verify_sidecar080,unique_pairs080,DATE080,SIDECAR_CAP080)

PHASE081='81000000000000000000000000000001'
PUBLIC_LIMITS081=dict(record_reads=16,record_bytes=2097152,record_stats=128,
    source_reads=64,source_bytes=16777216,source_stats=1024,
    boundary_ms=30000,sidecar_bytes=SIDECAR_CAP080,trace_steps=128)
STAGES081=('platform','invocation','ledger','checks','final','review','helper_profile',
    'authorization','preparation','spec','source_schema','source','launcher','dispatch')
OPERATIONS081=('validate','reserve','record_bytes','sidecar_bytes','sidecar_digest',
    'json_schema','raw_authority','source_bytes','source_digest')
REASONS081=('file_rejected','digest_rejected','schema_rejected','budget_rejected',
    'clock_rejected','binding_rejected','authorization_rejected','path_rejected',
    'invocation_unavailable','unsupported_platform','expired_date','interrupted',
    'trace_budget_rejected','file_missing','file_access_rejected','unexpected_failure_redacted')


class PublicFailure081(Exception):
    def __init__(self,reason):
        if reason not in REASONS081:raise ValueError('invalid_public_failure_category')
        self.reason=reason
        super().__init__(reason)


def invocation_value081():
    return dict(version='native_timing_invocation_081_v1',phase=PHASE081,date=DATE080,
        invocation_consumed=True,maximum_native_entry_invocations=1,orders_available=False)


def invocation_bytes081():
    return (json.dumps(invocation_value081(),sort_keys=True,separators=(',',':'))+'\n').encode('ascii')


def reserve_invocation081(path):
    raw=invocation_bytes081()
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return raw


def category081(error):
    if isinstance(error,KeyboardInterrupt):return 'interrupted'
    if type(error) is PublicFailure081:return error.reason
    if isinstance(error,FileExistsError):return 'invocation_unavailable'
    if isinstance(error,FileNotFoundError):return 'file_missing'
    if isinstance(error,PermissionError):return 'file_access_rejected'
    if type(error) is PublicInputRejected080:
        mapping={'timing_public_file_rejected':'file_rejected',
            'timing_public_digest_rejected':'digest_rejected',
            'timing_public_schema_rejected':'schema_rejected',
            'timing_public_budget_rejected':'budget_rejected',
            'timing_public_clock_rejected':'clock_rejected'}
        return mapping.get(str(error),'unexpected_failure_redacted')
    return 'unexpected_failure_redacted'


class PublicTrace081:
    def __init__(self,public):
        if type(public) is not PublicInputs080:raise TypeError('public_reader_type_rejected')
        self.public=public;self.stage='platform';self.operation='validate';self.index=None
        self.steps=0;self.stopped=False;self.captured=False;self.authority_validated=False
        self.source_pins_verified=False;self.dispatch_reserved=False
    def step(self,stage,operation,index=None):
        if (self.stopped or stage not in STAGES081 or operation not in OPERATIONS081 or
            index is not None and (type(index) is not int or not 0<=index<64)):
            raise PublicFailure081('schema_rejected')
        self.stage=stage;self.operation=operation;self.index=index;self.steps+=1
        if self.steps>PUBLIC_LIMITS081['trace_steps']:
            self.stopped=True;raise PublicFailure081('trace_budget_rejected')
    def record(self,label,path):
        self.step(label,'record_bytes');raw=self.public.raw(path)
        self.step(label,'sidecar_bytes');side=self.public.raw(Path(path).with_suffix('.sha256'),SIDECAR_CAP080)
        self.step(label,'sidecar_digest');verify_sidecar080(side,raw)
        self.step(label,'json_schema')
        try:value=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs080)
        except Exception:raise PublicFailure081('schema_rejected') from None
        return value,hashlib.sha256(raw).hexdigest()
    def authority(self,path):
        self.step('authorization','raw_authority');raw=self.public.raw(path,8192)
        self.step('authorization','sidecar_bytes');side=self.public.raw(Path(path).with_suffix('.sha256'),SIDECAR_CAP080)
        self.step('authorization','sidecar_digest');verify_sidecar080(side,raw)
        return raw,hashlib.sha256(raw).hexdigest()
    def source(self,path,expected,index=None,launcher=False):
        stage='launcher' if launcher else 'source'
        self.step(stage,'source_bytes',index)
        raw=self.public.raw(path,1048576 if launcher else 262144,source=True)
        self.step(stage,'source_digest',index)
        if hashlib.sha256(raw).hexdigest()!=expected:raise PublicFailure081('binding_rejected')
    def outcome(self,completed,error=None):
        if self.captured:raise PublicFailure081('binding_rejected')
        if type(completed) is not bool or completed!=(error is None):
            raise TypeError('invalid_public_outcome')
        if completed and (self.stopped or not self.authority_validated or
                          not self.source_pins_verified or not self.dispatch_reserved):
            raise PublicFailure081('binding_rejected')
        self.stopped=True;self.captured=True
        p=self.public
        return dict(version='native_timing_public_081_v1',phase=PHASE081,date=DATE080,
            completed=completed,stopped_stage=None if completed else self.stage,
            stopped_operation=None if completed else self.operation,
            source_index=None if completed else self.index,
            stop_reason=None if completed else category081(error),steps=self.steps,
            authority_validated=self.authority_validated,source_pins_verified=self.source_pins_verified,
            dispatch_reserved=self.dispatch_reserved,invocation_consumed=True,
            public_record_reads=p.reads,public_record_bytes=p.bytes,public_record_stats=p.stats,
            public_source_reads=p.source_reads,public_source_bytes=p.source_bytes,public_source_stats=p.source_stats,
            owned_native_backend_created=False,sdk_connections=0,sdk_queries=0,
            account_type_verified=False,owned_cleanup_applicable=False,orders_available=False,
            latency_guaranteed=False,native_launch_ready=False)
