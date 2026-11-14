"""Exact source-bound compilation preparation; model-only one-use stage.

No actual MetaEditor launcher/authority, SDK connection, deployment or orders.
The reader remains immutable086 source. A later build needs separate authority.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from itertools import islice
from pathlib import Path
import re
from threading import Lock

from .sharing_build_073 import BuildRejected, read_bound073, no_reparse073, metadata073
from .sharing_adapter_076 import exact076, encoded076
from .clock_observer_042 import unique_pairs
from .synchronization_086 import source_contract086, MQL_INPUTS, PHASE as SOURCE_PHASE
from .synchronization_083 import digest, require

PHASE = '87000000000000000000000000000001'
DATE = '2026-10-08'
ARTIFACT = 'ForexDemoSynchronization086.ex5'
SOURCE = MQL_INPUTS[0]
LIMITS = dict(hash_reads=256, hash_bytes=2147483648, path_stats=8192,
    copies=6, copy_bytes=1048576, metadata_calls=3, compiler_invocations=1, clock_samples=10000)


def build_contract087(root):
    source = source_contract086(root)
    return dict(version='synchronization_build_preparation_087_v1', build_phase=PHASE,
        source_phase=SOURCE_PHASE, date=DATE, source_contract=source,
        compile_inputs={n:source['input_bindings'][n] for n in MQL_INPUTS},
        compiler_invocations=1, actual_compiler_exit=1, errors=0, warnings=0,
        terminal_build=6244, editor_build=6244, artifact_name=ARTIFACT,
        artifact_min_bytes=1, artifact_max_bytes=1048576, compiler_timeout_seconds=60,
        normalization_allowed=False, build_authority=False, runtime_authorized=False, orders_available=False)


def validate_contract087(contract):
    try:
        require(type(contract) is dict)
        source=contract['source_contract']; hashes=source['input_bindings']
        require(exact076(source,source_contract086(Path(__file__).resolve().parents[2])))
        require(type(hashes) is dict and len(hashes)==37)
        for n,h in hashes.items(): require(type(n) is str and n and '..' not in Path(n).parts); digest(h)
        expected=dict(version='synchronization_build_preparation_087_v1', build_phase=PHASE,
            source_phase=SOURCE_PHASE, date=DATE, source_contract=source,
            compile_inputs={n:hashes[n] for n in MQL_INPUTS}, compiler_invocations=1,
            actual_compiler_exit=1, errors=0, warnings=0, terminal_build=6244, editor_build=6244,
            artifact_name=ARTIFACT, artifact_min_bytes=1, artifact_max_bytes=1048576,
            compiler_timeout_seconds=60, normalization_allowed=False, build_authority=False,
            runtime_authorized=False, orders_available=False)
        require(exact076(contract,expected))
        require(source['phase']==SOURCE_PHASE and source['date']==DATE and source['compiled'] is False)
        require(source['native_runtime_authorized'] is False and source['orders_available'] is False)
        return contract
    except Exception: raise BuildRejected('binding_rejected') from None


class Budget087:
    def __init__(self, clock):
        self.clock=clock; self.first=self.last=None; self.counts=dict.fromkeys(LIMITS,0); self.stopped=False
        self.check()
    def check(self):
        try:
            require(not self.stopped); self.counts['clock_samples']+=1
            require(self.counts['clock_samples']<=LIMITS['clock_samples'])
            now=self.clock(); require(type(now) is tuple and len(now)==2)
            require(all(type(x) is int and x>=0 for x in now))
            require(datetime.fromtimestamp(now[0]//1000,timezone.utc).date().isoformat()==DATE)
            if self.first is None:self.first=self.last=now
            require(all(a>=b for a,b in zip(now,self.last)))
            delta=[a-b for a,b in zip(now,self.first)]
            require(delta[0]<900000 and delta[1]<900000000000 and abs(delta[0]-delta[1]//1000000)<=1000)
            self.last=now;return now
        except Exception:
            self.stopped=True;raise BuildRejected('date_or_clock_rejected') from None
    def consume(self, key, amount=1):
        self.check()
        if key not in LIMITS or type(amount) is not int or amount<1 or self.counts[key]+amount>LIMITS[key]:
            self.stopped=True;raise BuildRejected('budget_rejected')
        self.counts[key]+=amount


def build_record087(contract, exit_code, log_text, artifact, compiler_sha, terminal_sha):
    try:
        validate_contract087(contract)
        require(type(exit_code) is int and exit_code==1)
        require(type(log_text) is str and 0<len(log_text)<=524288)
        require(re.findall(r'^Result: ([0-9]+) errors, ([0-9]+) warnings, .+$',log_text,re.MULTILINE)==[('0','0')])
        require(re.search(r'^.*:\s*(?:error|warning)\b',log_text,re.MULTILINE|re.IGNORECASE) is None)
        require(type(artifact) is dict and set(artifact)=={'sha256','size','raw'})
        require(type(artifact['size']) is int and 1<=artifact['size']<=1048576)
        for h in (artifact['sha256'],compiler_sha,terminal_sha):digest(h)
        return dict(version='synchronization_build_087_v1', build_phase=PHASE, source_phase=SOURCE_PHASE,
            date=DATE, source_contract_sha256=hashlib.sha256(encoded076(contract['source_contract'])).hexdigest(),
            input_bindings=dict(contract['source_contract']['input_bindings']),
            compile_inputs=dict(contract['compile_inputs']), artifact_name=ARTIFACT,
            artifact_sha256=artifact['sha256'], artifact_bytes=artifact['size'],
            compiler_sha256=compiler_sha, terminal_sha256=terminal_sha, terminal_build=6244,
            editor_build=6244, compiler_invocations=1, compiler_exit_code=1, errors=0, warnings=0,
            compiled=True, runtime_authorized=False, orders_available=False)
    except Exception:raise BuildRejected('evidence_rejected') from None


@dataclass(frozen=True)
class Build087:
    raw: bytes = field(repr=False)
    def record(self):return json.loads(self.raw,object_pairs_hook=unique_pairs)
    @property
    def sha256(self):return hashlib.sha256(self.raw).hexdigest()


def verify_build087(raw, contract, log_text, artifact, compiler_sha, terminal_sha):
    try:
        require(type(raw) is bytes and 0<len(raw)<=32768)
        value=json.loads(raw.decode('ascii'),object_pairs_hook=unique_pairs)
        expected=build_record087(contract,value['compiler_exit_code'],log_text,artifact,compiler_sha,terminal_sha)
        require(exact076(value,expected) and raw==encoded076(expected))
        return Build087(raw)
    except Exception:raise BuildRejected('evidence_rejected') from None


class Stage087:
    """Model-only callbacks; persisted attempt precedes all staging/launch work.

    Each new directory is exclusive and never overwritten/deleted. A failed or
    interrupted build remains spent. Metadata-after is still attempted on failure.
    """
    def __init__(self, root, contract, pins, backend, clock):
        require(getattr(backend,'model_only',None) is True)
        validate_contract087(contract)
        require(type(pins) is dict and set(pins)=={'compiler','terminal','policy'})
        for k in ('compiler','terminal'):digest(pins[k])
        require(type(pins['policy']) is str and bool(pins['policy']))
        self.root=Path(root);self.contract=json.loads(encoded076(contract));self.pins=dict(pins);self.backend=backend;self.clock=clock
        self.fixed_contract=encoded076(self.contract);self.fixed_pins=dict(self.pins)
        self.used=False;self.lock=Lock()
    def run(self, marker, directory, source_paths, enabled=False):
        require(type(enabled) is bool)
        with self.lock:
            require(not self.used);self.used=True
        if not enabled:return dict(modeled_completed=False,default_off=True,compiler_invocations=0,stage_trace=[])
        require(encoded076(self.contract)==self.fixed_contract and self.pins==self.fixed_pins)
        marker,directory=Path(marker),Path(directory)
        require(marker.parent==directory.parent and directory.name.startswith('compiler087-') and
            re.fullmatch('compiler087-[0-9a-f]{32}',directory.name) is not None)
        require(type(source_paths) is dict and set(source_paths)==set(self.contract['source_contract']['input_bindings']))
        # Exclusive durable marker: even a partial write consumes the attempt.
        raw=encoded076(dict(version='build087_attempt_v1',phase=PHASE,consumed=True,
            contract_sha256=hashlib.sha256(encoded076(self.contract)).hexdigest(),orders_available=False))
        with marker.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        b=Budget087(self.clock);trace=[];reason=None;record=None;before=after=None
        def enter(s):trace.append(s);b.check()
        def sources():
            for n,h in self.contract['source_contract']['input_bindings'].items():
                if read_bound073(source_paths[n],b)['sha256']!=h:raise BuildRejected('binding_rejected')
        def images():
            require(encoded076(self.contract)==self.fixed_contract and self.pins==self.fixed_pins)
            observed=self.backend.images()
            require(exact076(observed,{k:self.pins[k] for k in ('compiler','terminal')}))
        def metadata(cleanup=False):
            if cleanup:
                if b.counts['metadata_calls']>=3:raise BuildRejected('budget_rejected')
                b.counts['metadata_calls']+=1
            else:b.consume('metadata_calls')
            return metadata073(self.backend.metadata(),self.pins['policy'])
        try:
            enter('preflight');sources();images();before=metadata()
            enter('stage');no_reparse073(directory.parent,b);directory.mkdir(exist_ok=False);no_reparse073(directory,b)
            for n,h in self.contract['compile_inputs'].items():
                v=read_bound073(source_paths[n],b,collect=True);require(v['sha256']==h)
                b.consume('copies');b.consume('copy_bytes',v['size'])
                with (directory/Path(n).name).open('xb') as f:f.write(v['raw']);f.flush();os.fsync(f.fileno())
            enter('launch_guard');sources();images();metadata()
            for n,h in self.contract['compile_inputs'].items():require(read_bound073(directory/Path(n).name,b)['sha256']==h)
            enter('compiler');b.consume('compiler_invocations')
            exit_code=self.backend.compile(directory,SOURCE,60);b.check()
            enter('outputs')
            names={Path(n).name for n in MQL_INPUTS}|{ARTIFACT,'compile.log'}
            actual=list(islice(directory.iterdir(),9));require(len(actual)==8 and {p.name for p in actual}==names)
            values={p.name:read_bound073(p,b,collect=p.name=='compile.log') for p in actual}
            for n,h in self.contract['compile_inputs'].items():require(values[Path(n).name]['sha256']==h)
            log=values['compile.log']['raw'].decode('utf-16',errors='strict')
            value=build_record087(self.contract,exit_code,log,values[ARTIFACT],self.pins['compiler'],self.pins['terminal'])
            record=verify_build087(encoded076(value),self.contract,log,values[ARTIFACT],self.pins['compiler'],self.pins['terminal'])
        except BuildRejected as e:reason=e.code
        except (Exception,KeyboardInterrupt):reason='unexpected_failure'
        finally:
            trace.append('metadata_after')
            try:after=metadata(True)
            except (Exception,KeyboardInterrupt):reason=reason or 'metadata_rejected'
        if reason is None:
            try:enter('final_audit');sources();images();require(exact076(before,after) and record is not None)
            except (Exception,KeyboardInterrupt):reason='binding_rejected'
        return dict(modeled_completed=reason is None,default_off=False,stop_reason=reason,
            compiler_invocations=b.counts['compiler_invocations'],stage_trace=trace,counts=dict(b.counts),
            build_record=record.record() if record else None,metadata_after_attempted=True,
            dependencies_injected=True,native_compiler_invocations=0,runtime_authorized=False,orders_available=False)
