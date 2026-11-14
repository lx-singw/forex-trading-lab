"""Bounded compiler preparation/evidence only. No SDK, deployment or orders."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PureWindowsPath
import re
import stat

from .mql_sharing_072 import PHASE,DATE
from .sharing_integration_072 import SOURCE_INPUTS,source_contract072
from .sharing_runtime_066 import digest
from .native_compiler_042 import native_command

BUILD_PHASE='73000000000000000000000000000001'
ARTIFACT='ForexDemoSharing072.ex5'
LIMITS=dict(hash_reads=64,hash_bytes=2147483648,path_stats=2048,copies=4,copy_bytes=1048576,
    metadata_calls=3,compiler_invocations=1,clock_samples=10000)
STAGES=('preflight','metadata_before','stage','launch_guard','compiler','outputs','metadata_after','final_audit')
CODES=('date_or_clock_rejected','budget_rejected','path_rejected','file_rejected','binding_rejected',
    'stage_rejected','metadata_rejected','compiler_failed','compiler_timeout','evidence_rejected','unexpected_failure')


class BuildRejected(ValueError):
    def __init__(self,code):
        if code not in CODES:code='unexpected_failure'
        self.code=code;super().__init__(code)


def reserve_build073(path,value):
    required={'build_reservation_consumed','ledger_sha256','authorization_sha256','maximum_compiler_invocations','phase','orders_available'}
    if type(value) is not dict or set(value)!=required or value['build_reservation_consumed'] is not True or value['orders_available'] is not False:
        raise BuildRejected('stage_rejected')
    if type(value['maximum_compiler_invocations']) is not int or value['maximum_compiler_invocations']!=1 or value['phase']!=BUILD_PHASE:
        raise BuildRejected('stage_rejected')
    for k in ('ledger_sha256','authorization_sha256'):digest(value[k])
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode('ascii');path=Path(path)
    # A partial marker/sidecar pair still consumes the attempt. Never unlink it.
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    result=hashlib.sha256(raw).hexdigest()
    with path.with_suffix('.sha256').open('x') as f:f.write(result+'\n');f.flush();os.fsync(f.fileno())
    return result


class Budget073:
    def __init__(self,clock):
        self.clock=clock;self.first=self.last=None;self.counts=dict.fromkeys(LIMITS,0);self.check()
    def check(self):
        self.counts['clock_samples']+=1
        if self.counts['clock_samples']>LIMITS['clock_samples']:raise BuildRejected('budget_rejected')
        try:
            now=self.clock()
            if type(now) is not tuple or len(now)!=2 or any(type(x) is not int or x<0 for x in now):raise ValueError()
            if datetime.fromtimestamp(now[0]//1000,timezone.utc).date().isoformat()!=DATE:raise ValueError()
            if self.first is None:self.first=self.last=now
            if any(a<b for a,b in zip(now,self.last)):raise ValueError()
            delta=[a-b for a,b in zip(now,self.first)];self.last=now
            if delta[0]>=900000 or delta[1]>=900000000000 or abs(delta[0]-delta[1]//1000000)>1000:raise ValueError()
            return now
        except Exception:raise BuildRejected('date_or_clock_rejected') from None
    def consume(self,key,amount=1):
        self.check()
        if key not in LIMITS or type(amount) is not int or amount<1 or self.counts[key]+amount>LIMITS[key]:
            raise BuildRejected('budget_rejected')
        self.counts[key]+=amount


def no_reparse073(path,budget):
    for item in (Path(path),*Path(path).parents):
        budget.consume('path_stats');s=item.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise BuildRejected('path_rejected')


def read_bound073(path,budget,cap=1048576,collect=False):
    """Uncached bounded descriptor/path hash. Byte budget reserved before reads."""
    if type(cap) is not int or not 0<cap<=136314880 or type(collect) is not bool:raise BuildRejected('file_rejected')
    path=Path(path);budget.consume('hash_reads');no_reparse073(path,budget)
    budget.consume('path_stats');before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or not 0<before.st_size<=cap:raise BuildRejected('file_rejected')
    stamp=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
    total=0;h=hashlib.sha256();parts=[]
    with path.open('rb') as f:
        if stamp(os.fstat(f.fileno()))!=stamp(before):raise BuildRejected('file_rejected')
        while total<before.st_size:
            n=min(1048576,before.st_size-total);budget.consume('hash_bytes',n);raw=f.read(n)
            if len(raw)!=n:raise BuildRejected('file_rejected')
            h.update(raw);total+=len(raw)
            if collect:parts.append(raw)
        budget.consume('hash_bytes');extra=f.read(1)
        if extra or stamp(os.fstat(f.fileno()))!=stamp(before):raise BuildRejected('file_rejected')
    no_reparse073(path,budget);budget.consume('path_stats')
    if stamp(path.stat())!=stamp(before):raise BuildRejected('file_rejected')
    budget.check();return dict(sha256=h.hexdigest(),size=total,raw=b''.join(parts) if collect else None)


def owned073(directory,root):
    p,r=Path(directory),Path(root)
    if p.parent!=r or re.fullmatch('compiler073-[0-9a-f]{32}',p.name) is None:raise BuildRejected('stage_rejected')
    return p


def stage073(inputs,expected,directory,root,budget):
    if type(inputs) is not dict or set(inputs)!=set(SOURCE_INPUTS) or set(expected)!=set(inputs):raise BuildRejected('stage_rejected')
    directory=owned073(directory,root);no_reparse073(root,budget);directory.mkdir(exist_ok=False)
    no_reparse073(directory,budget)
    for name in sorted(inputs):
        value=read_bound073(inputs[name],budget,collect=True)
        if value['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
        dest=directory/Path(name).name;budget.consume('copies');budget.consume('copy_bytes',value['size'])
        with dest.open('xb') as f:f.write(value['raw']);f.flush();os.fsync(f.fileno())
        if read_bound073(dest,budget)['sha256']!=expected[name]:raise BuildRejected('binding_rejected')
    return directory


def metadata073(value,policy):
    try:
        if type(value) is not dict or set(value)!= {'policy','editor_processes','terminal_build','editor_build','valid_signatures'}:raise ValueError()
        expected=dict(policy=policy,editor_processes=0,terminal_build=6244,editor_build=6244,valid_signatures=True)
        if any(type(value[k]) is not type(v) or value[k]!=v for k,v in expected.items()):raise ValueError()
        return dict(value)
    except Exception:raise BuildRejected('metadata_rejected') from None


def build_record073(contract,exit_code,log_text,artifact,compiler_sha256,terminal_sha256):
    """Actual observed6244 exit1 retained. Zero summaries alone never pass."""
    try:
        canonical=source_contract072(contract['input_bindings'])
        if type(contract) is not dict or set(contract)!=set(canonical):raise ValueError()
        if any(type(contract[k]) is not type(v) or contract[k]!=v for k,v in canonical.items()):raise ValueError()
        if type(exit_code) is not int or exit_code!=1 or type(log_text) is not str or len(log_text)>524288:raise ValueError()
        summaries=re.findall(r'^Result: (\d+) errors, (\d+) warnings, .+$',log_text,re.MULTILINE)
        if summaries!=[('0','0')]:raise ValueError()
        if type(artifact) is not dict or set(artifact)!={'sha256','size','raw'}:raise ValueError()
        if type(artifact['size']) is not int or not 0<artifact['size']<=1048576:raise ValueError()
        for value in (artifact['sha256'],compiler_sha256,terminal_sha256):digest(value)
        return dict(version='sharing_build_073_v1',build_phase=BUILD_PHASE,phase=PHASE,date=DATE,
            input_bindings=contract['input_bindings'],artifact_name=ARTIFACT,artifact_sha256=artifact['sha256'],
            artifact_bytes=artifact['size'],compiler_sha256=compiler_sha256,terminal_sha256=terminal_sha256,
            terminal_build=6244,compiler_invocations=1,compiler_exit_code=exit_code,errors=0,warnings=0,
            compiled=True,runtime_authorized=False,orders_available=False)
    except Exception:raise BuildRejected('evidence_rejected') from None


def compile_once073(launch,editor,directory,budget):
    budget.consume('compiler_invocations')
    # Exact file, shell=False direct executable,60s timeout. Caller consumes its
    # persistent reservation before this method and always audits final state.
    result=launch(native_command(editor,Path(directory)/'ForexDemoSharing072.mq5',Path(directory)/'compile.log'),editor,60)
    budget.check()
    if type(result.returncode) is not int:raise BuildRejected('compiler_failed')
    return result.returncode
