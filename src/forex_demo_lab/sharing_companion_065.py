"""Bounded companion core. Injected tests and separate Windows compatibility.
No SDK import, initialization, market, receipt or order capability.
"""
from .capture_budget_047 import clock_sample, require_guard
from .mql_sharing_064 import DATA, Probe
from .sharing_probe_062 import ProbeRejected, Open, Stamp, validate_stamp

PHASE = '65000000000000000000000000000001'
ROLE_SPECS = {
    'directory': (0x20080,3,3,0x02200000),
    'writer': (0xC0000000,3,1,0x00200080),
    'metadata': (0x20080,7,3,0x00200080),
    'seal': (0x80000000,1,3,0x00200080),
    'reader': (0x80000000,1,3,0x00200080),
    'control_write': (0x40020080,7,3,0x00200080),
    'control_delete': (0x30080,7,3,0x00200080),
}
LIMITS = dict(opens=16,directories=1,writes=1,reads=1,stamps=64,native_calls=300000,
    closes=1600,local_frees=2048,guards=192,process_opens=384,identity_tokens=384,
    process_snapshots=384,process_entries=196608,hash_reads=768,hash_bytes=103079215104,
    sdk_queries=2048,clock_samples=610000,sdk_connections=1,script_arms=2,
    log_reads=1,log_bytes=65536,reservation_writes=1,security_queries=512,
    file_properties=256,parent_queries=512,token_queries=1024,hash_path_stats=16384)


class Meter065:
    def __init__(self,clock):
        self.clock=clock;self.first=self.last=None
        self.counts=dict.fromkeys(LIMITS,0);self.cleanup_exceeded=False;self.elapsed_us=0
        self.check()
    def check(self):
        self.counts['clock_samples']+=1
        if self.counts['clock_samples']>LIMITS['clock_samples']:raise ProbeRejected('clock_budget_exhausted')
        now=clock_sample(self.clock)
        if self.first is None:self.first=self.last=now
        if any(a<b for a,b in zip(now,self.last)):raise ProbeRejected('clock_reversed')
        d=tuple(a-b for a,b in zip(now,self.first));self.last=now;self.elapsed_us=d[1]//1000
        if max(d[0],d[2])>=900000 or d[1]>=900000000000:raise ProbeRejected('session_expired')
        if abs(d[0]-d[1]//1000000)>1000 or abs(d[2]-d[1]//1000000)>1000:
            raise ProbeRejected('clock_discontinuity')
        return now
    def consume(self,key,amount=1):
        self.check()
        if key not in LIMITS or type(amount) is not int or amount<1:raise ProbeRejected('operation_budget_exhausted')
        if self.counts[key]+amount>LIMITS[key]:raise ProbeRejected('operation_budget_exhausted')
        self.counts[key]+=amount
    def cleanup(self,key):
        # Expiry never prevents one close/free attempt. Exceeding the declared
        # cap still invalidates the result; do not hide cleanup IO.
        self.counts[key]+=1
        if self.counts[key]>LIMITS[key]:self.cleanup_exceeded=True


class Companion065:
    def __init__(self,api,meter,guard,compatibility=False):
        self.api,self.meter,self.guard=api,meter,guard
        self.used=False;self.identity=None;self.metadata=None;self.seal=None
        self.probes=[];self.span=None;self.stage='new';self.compatibility=compatibility
    def call(self,fn,*args):
        require_guard(self.guard);self.meter.check()
        start=self.meter.check()[2]
        try:value=fn(*args)
        except Exception:raise ProbeRejected('companion_operation_failed_details_redacted') from None
        end=self.meter.check()[2];self.span=(start,end)
        require_guard(self.guard);self.meter.check()
        return value
    def opened(self,role,category='none'):
        r=self.call(self.api.open,role)
        if (type(r) is not Open or r.category!=category or
                (r.handle is None)!=(category!='none')):
            raise ProbeRejected('sharing_control_rejected')
        return r.handle
    def stamped(self,h,position):
        identity=validate_stamp(self.call(self.api.stamp,h),84,position)
        if self.identity is not None and identity!=self.identity:raise ProbeRejected('file_identity_changed')
        return identity
    def close(self,h):
        if self.call(self.api.close,h) is not True:raise ProbeRejected('handle_close_unconfirmed')
    def prepare(self):
        if self.used:raise ProbeRejected('session_unavailable')
        self.used=True;self.stage='preparing'
        if getattr(self.api,'scope',None)=='terminal':
            from .private_guard_065 import FullGuard065
            if type(self.guard) is not FullGuard065:raise ProbeRejected('private_guard_rejected')
            self.guard.bind_files(self.api)
        self.call(self.api.setup)
        d=self.opened('directory');s=self.call(self.api.stamp,d,True)
        if (type(s) is not Stamp or s.directory is not True or s.security_verified is not True or
                s.path_verified is not True or s.reparse is not False):raise ProbeRejected('private_directory_binding_rejected')
        w=self.opened('writer');self.identity=validate_stamp(self.call(self.api.stamp,w),0,0)
        n=self.call(self.api.write,w,DATA)
        if type(n) is not int or n!=84:raise ProbeRejected('synthetic_write_rejected')
        self.stamped(w,84);self.close(w)
        self.metadata=self.opened('metadata');self.stamped(self.metadata,-1)
        self.controls('pre')
        self.seal=self.opened('seal');self.stamped(self.seal,0)
        raw,n=self.call(self.api.read,self.seal,84)
        if type(raw) is not bytes or type(n) is not int or n!=84 or raw!=DATA:
            raise ProbeRejected('synthetic_read_rejected')
        self.stamped(self.seal,84);self.stage='sealed'
    def release_seal(self):
        if self.stage!='sealed' or self.seal is None:raise ProbeRejected('session_order_rejected')
        self.close(self.seal);self.seal=None;self.stage='independent'
        self.stamped(self.metadata,-1)
    def controls(self,stage):
        if stage not in ('pre','independent','post'):raise ProbeRejected('session_order_rejected')
        if stage=='independent' and (self.seal is not None or self.stage!='independent'):
            raise ProbeRejected('helper_seal_masks_observation')
        if len(self.probes)!={'pre':0,'independent':2,'post':4}[stage]:
            raise ProbeRejected('session_order_rejected')
        blockers=self.api.blocking_readers()
        if stage=='independent' and blockers!=(1 if self.compatibility else 0):
            raise ProbeRejected('helper_seal_masks_observation')
        for access in ('write','delete'):
            self.stamped(self.metadata,-1)
            h=self.opened('control_'+access,'sharing_violation' if stage=='independent' else 'none')
            start,end=self.span
            if h is not None:
                self.stamped(h,-1);self.close(h)
            self.stamped(self.metadata,-1)
            self.probes.append(Probe(stage,access,start,end,32 if stage=='independent' else 0,
                h is not None,h is not None,blockers,True,True,True,True))
    def finish(self):
        return self.api.finish()


def run_compatibility(api,meter):
    """Native runner adds actual Windows binding; pure tests stay injected.
    Simulated MQL-like Win32 reader is explicit, never native MQL evidence.
    """
    c=Companion065(api,meter,lambda:meter.check() is not None,compatibility=True)
    result=dict(version='metadata_compatibility_065_v1',passed=False,reason=None,
        native_mql_verified=False,native_publication_verified=False,sdk_connections=0,
        mt5_invocations=0,receipt_permissions=0,quote_reads=0,history_reads=0,orders=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False)
    try:
        c.prepare()
        # A second generic-read/share-read handle must coexist with metadata.
        peer=c.opened('reader');c.stamped(peer,0)
        c.release_seal();c.controls('independent')
        c.close(peer);c.stage='post';c.controls('post')
        result['passed']=True
    except Exception as e:
        allowed={'session_expired','clock_reversed','clock_discontinuity','clock_budget_exhausted',
            'operation_budget_exhausted','companion_operation_failed_details_redacted','sharing_control_rejected',
            'file_identity_changed','handle_close_unconfirmed','private_directory_binding_rejected',
            'private_file_binding_rejected','synthetic_write_rejected','synthetic_read_rejected',
            'session_unavailable','session_order_rejected','helper_seal_masks_observation'}
        result['reason']=str(e) if str(e) in allowed else 'compatibility_failed_details_redacted'
    finally:
        try:
            cleanup=c.finish();result['cleanup']=cleanup
            if (type(cleanup) is not dict or cleanup.get('all_handles_closed') is not True or
                    cleanup.get('allocations_released') is not True or
                    type(cleanup.get('unconfirmed_handles')) is not int or cleanup['unconfirmed_handles']!=0):
                result['passed']=False;result['reason']='cleanup_unconfirmed'
        except Exception:
            result['passed']=False;result['cleanup']=None;result['reason']='cleanup_failed_details_redacted'
        try:meter.check()
        except Exception:result['passed']=False;result['reason']='post_cleanup_clock_rejected'
        if meter.cleanup_exceeded:result['passed']=False;result['reason']='cleanup_budget_exceeded'
        result['counts']=dict(meter.counts)
        result['elapsed_us']=meter.elapsed_us
        result['controls']=[dict(stage=p.stage,access=p.access,error=p.error,opened=p.opened,closed=p.closed,
                                 blocking_companion_handles=p.blocking_companion_handles)
                            for p in c.probes]
    return result
