"""Invented producer/channel exercise only. Never import a native launcher."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .recorder_runner_157 import Runner
from .relay_audit_157 import inspect_job


def raw(value):return json.dumps(value,separators=(',',':')).encode('ascii')
def bits(value):return struct.pack('>d',value).hex().upper()


def recipe(failed=False):
    """Declared independently of reader constants; data are wholly constructed."""
    clocks=['1700000000']*4+['0','0'];items=[('C','context_before',True,0,clocks,[])]
    integers={'account_leverage':10,'digits':5,'trade_calc_mode':0,'swap_mode':0,'swap_rollover3days':3,'stops_level':0,'freeze_level':0,'execution_mode':2,'order_mode':127,'custom_symbol':0,'subscription_delay':0,'chart_mode':0}
    doubles={'point':.00001,'tick_size':.00001,'contract_size':100000.,'tick_value_profit':1.,'tick_value_loss':1.,'volume_min':.01,'volume_max':100.,'volume_step':.01,'volume_limit':0.,'margin_initial':0.,'margin_maintenance':0.,'swap_long':0.,'swap_short':0.,'swap_sunday':0.,'swap_monday':1.,'swap_tuesday':1.,'swap_wednesday':3.,'swap_thursday':1.,'swap_friday':1.,'swap_saturday':0.}
    for key,value in integers.items():items.append(('I',key,not failed,4401 if failed else 0,[str(0 if failed else value)],[]))
    for key,value in doubles.items():items.append(('D',key,not failed,4401 if failed else 0,[bits(0. if failed else value)],[]))
    items.append(('V','currency_margin',not failed,4401 if failed else 0,['NA' if failed else 'USD'],[]))
    for day in range(7):
        if not failed and day in range(1,6):items.append(('W',f'{day}:0',True,0,['0','86340'],[]))
        index=1 if not failed and day in range(1,6) else 0
        items.append(('W',f'{day}:{index}',False,0,['0','0'],[]))
    extras=[] if failed else [['R','{q}','0','USD','0','0','0','0','0','1'],['L','{q}','0','0','0','0',*[bits(v) for v in (7.,0.,1000.,0.,10000.)],'USD']]
    items.append(('K','commissions',not failed,0,['-1' if failed else '1'],extras))
    for side in ('buy','sell'):items.append(('M',side,not failed,0,[bits(0. if failed else 1.)]*2,[]))
    items.append(('C','context_after',True,0,clocks,[]));items.append(('C','before',True,0,clocks,[]))
    items.append(('T','quote',True,0,['1700000000','1700000000000',bits(1.10),bits(1.10012),bits(0.),'0','6',bits(0.)],[]))
    items.append(('C','after',True,0,clocks,[]));return items


class Clock:
    def __init__(self):self.value=5_000_000;self.producer=None;self.reads=0
    def read(self):self.value+=100;self.reads+=1;return self.value
    def wait(self,seconds):
        self.value+=round(seconds*1_000_000)
        if self.producer is not None:self.producer.step()


class Producer:
    """One invented request at a time; no dependency on native reader/lease code."""
    def __init__(self,folder,job,clock,*,failed=False,hold=False):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=False);self.job=job;self.clock=clock;clock.producer=self
        self.items=recipe(failed);self.index=0;self.ordinal=0;self.phase='before';self.chain='0'*64;self.hold=hold;self.done=False
        self.path=self.folder/'NativePort156.txt';self.path.write_bytes(b'')
        self.append(['H','FXDL_NATIVE_PORT156_V1','non_admitted_prototype',job]);self.append(['B','1']);self.issue()

    def native_time(self):return self.clock.value-4_900_000

    def append(self,fields):
        payload='\t'.join(map(str,fields));self.chain=hashlib.sha256((self.chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()
        with self.path.open('ab') as file:file.write((payload+'\t'+self.chain+'\n').encode('ascii'))

    def issue(self):
        self.ordinal+=1;self.sent=self.native_time();self.challenge=f'{self.ordinal:032x}'
        (self.folder/f'Request{self.ordinal:04d}.txt').write_bytes(f'FXDL_REQUEST156_V1\t{self.job}\t{self.ordinal}\t{self.challenge}\n'.encode())

    def step(self):
        if self.hold or self.done:return
        path=self.folder/f'Reply{self.ordinal:04d}.txt'
        if not path.exists():return
        response=path.read_bytes()
        if not response.endswith(b'\n'):return
        fields=response.decode().strip().split('\t');received=self.native_time()
        self.append(['J',self.ordinal,self.challenge,self.sent,received,*fields[4:]])
        if self.phase=='final':self.append(['E',len(self.items),self.ordinal]);self.done=True;return
        tag,key,ok,error,values,extras=self.items[self.index];q=self.index+1
        if self.phase=='before':
            self.append(['A',q,tag,key]);self.before=received;self.phase='after'
        else:
            self.append([tag,q,key,1700000000,1700000000,1700000000,self.before,self.before,received,int(ok),error,*values])
            for row in extras:self.append([str(v).replace('{q}',str(q)) for v in row])
            if key=='context_after':self.append(['Z','1',q])
            self.index+=1;self.phase='final' if self.index==len(self.items) else 'before'
        self.issue()


class Channel:
    def __init__(self,clock,mode='clean'):
        self.clock=clock;self.mode=mode;self.calls=[];self.owner_exit_observed=False;self.polls=0;self.job=None
    def start(self,job,duration_ms):
        self.job=job;self.calls.append('START')
        if self.mode=='start_failure':raise OSError('invented private detail')
        return raw(dict(schema='native_health142_start_v1',token=job,contained=self.mode!='uncontained',resumed=True,helper_pid=7))
    def request(self,operation,challenge):
        self.calls.append(operation);self.clock.value+=100
        if self.mode=='owner_death' and self.polls>=5:raise OSError('invented owner EOF')
        if operation=='EXIT':
            return raw(dict(schema='native_health142_exit_v1',token=self.job,challenge=challenge,exit_observed=True,cancel_ack=True,
                            job_closed=True,clear_ack=self.mode!='clear_failure',close_ack=True,forced=False))
        if operation=='POLL':self.polls+=1
        owner=self.clock.value//1000+10000
        value=dict(schema='native_health142_status_v1',token=self.job,challenge=challenge,operation=operation,contained=True,running=True,
                   sample_valid=True,sample_sequence=self.polls,sample_tick_ms=owner-20,owner_tick_ms=owner,create_ack=True,set_ack=True,
                   ready_signal=True,mains=True,helper_running_marker=True,cancel_ack=operation=='CANCEL')
        if operation=='POLL':
            if self.mode=='delayed_ready' and self.polls==1:value.update(sample_valid=False,ready_signal=False,set_ack=False)
            if self.mode=='never_ready':value.update(sample_valid=False,ready_signal=False,set_ack=False)
            if self.mode=='power' and self.polls>=4:value['mains']=False
            if self.mode=='stale' and self.polls>=4:value['sample_tick_ms']=owner-2000
            if self.mode=='wrong_challenge' and self.polls>=4:value['challenge']='f'*32
            if self.mode=='protocol' and self.polls>=4:return b'{}'
            if self.mode=='slow' and self.polls>=4:self.clock.value+=1_000_001
        if operation=='CANCEL' and self.mode=='cancel_failure':value['cancel_ack']=False
        return raw(value)
    def close(self):
        self.calls.append('CLOSE')
        if self.mode=='close_failure':raise OSError('invented close failure')
        self.owner_exit_observed=True


def exercise(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);results=[]
    cases=('clean','failed_metadata','delayed_ready','power','stale','wrong_challenge','owner_death','start_failure','clear_failure','held_request')
    (output/'declaration.json').write_bytes(raw(dict(inputs='invented_only',cases=cases,native_launch=False,market_eligible=False))+b'\n')
    for index,case in enumerate(cases,1):
        clock=Clock();job=f'{1000+index:032x}';folder=output/case/('Job156-'+job)
        Producer(folder,job,clock,failed=case=='failed_metadata',hold=case=='held_request')
        channel=Channel(clock,case);runner=Runner(folder,job,channel,enabled=True,clock=clock.read,wait=clock.wait,budget_us=500_000 if case=='held_request' else 30_000_000)
        status=runner.run();checked=None
        try:checked=inspect_job(folder,job)
        except ValueError:pass
        require_complete=case in ('clean','failed_metadata','delayed_ready')
        if (status['cause']=='complete')!=require_complete or (checked is not None)!=require_complete:raise ValueError('fixture157_outcome')
        results.append(dict(case=case,status=status,independent=checked,channel_calls=len(channel.calls)))
    summary=dict(schema='relay157_exercise_v1',inputs='invented_only',cases=results,native_launch=False,market_eligible=False)
    (output/'summary.json').write_bytes(raw(summary)+b'\n');return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exercise-invented',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    if not args.exercise_invented:print(json.dumps(dict(cause='off',native_launch=False,market_eligible=False)));return 0
    if args.output is None:parser.error('--output requires a new exercise directory')
    result=exercise(args.output);print(json.dumps(dict(cases=len(result['cases']),inputs='invented_only',native_launch=False)));return 0
