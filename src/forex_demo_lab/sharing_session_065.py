"""One-use private reservation and one bounded saved-log read. No SDK attach.
Interactive runtime orchestration/compiled-artifact verification is not here.
"""
import json
import os
from pathlib import Path
import re
from .sharing_companion_065 import PHASE
from .mql_sharing_064 import PHASE as MQL_PHASE, DATE, records_from_log
from .sharing_probe_062 import ProbeRejected


class LaunchSession065:
    def __init__(self,path,bindings,meter):
        self.meter=meter;self.arms=[];self.stopped=False;self.sdk_spent=False
        if type(bindings) is not dict or set(bindings)!={'source','ex5','terminal','editor'}:
            raise ProbeRejected('session_binding_rejected')
        if any(type(v) is not str or re.fullmatch('[0-9a-f]{64}',v) is None for v in bindings.values()):
            raise ProbeRejected('session_binding_rejected')
        meter.consume('reservation_writes')
        data=dict(version='launch_reservation_065_v1',phase=PHASE,mql_phase=MQL_PHASE,
            date=DATE,bindings=bindings,maximum_sdk_connections=1,maximum_launches=2,
            maximum_receipt_permissions=0,orders_available=False)
        try:
            with Path(path).open('xb') as stream:
                stream.write((json.dumps(data,sort_keys=True)+'\n').encode('ascii'))
                stream.flush();os.fsync(stream.fileno())
        except Exception:raise ProbeRejected('reservation_unavailable') from None
    def sdk_attempt(self):
        if self.stopped or self.sdk_spent:raise ProbeRejected('session_unavailable')
        self.sdk_spent=True;self.meter.consume('sdk_connections')
    def arm(self,step):
        try:
            if self.stopped or self.arms==['disabled','enabled'] or step!=('disabled' if not self.arms else 'enabled'):
                raise ValueError()
            self.meter.consume('script_arms');self.arms.append(step)
        except Exception:
            self.stopped=True;raise ProbeRejected('launch_order_or_budget_rejected') from None
    def stop(self):self.stopped=True


class SavedRange065:
    def __init__(self,path,meter):
        self.meter=meter;self.used=False
        try:
            self.path=Path(path);self._check_path();s=self.path.stat()
            if s.st_size%2:raise ValueError()
            self.identity=(s.st_dev,s.st_ino);self.offset=s.st_size
        except Exception:raise ProbeRejected('saved_log_rejected') from None
    def _check_path(self):
        for p in (self.path,*self.path.parents):
            if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:
                raise ProbeRejected('saved_log_rejected')
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
