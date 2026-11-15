"""Measured, bounded owner/relay orchestration. No MT5 launch or collection grant."""
import hashlib
import json
from pathlib import Path
import time
import uuid

from .helper_health_142 import HealthDecoder, STATUS_KEYS, identifier, packet
from .native_journal_157 import CAP, require
from .recorder_files_157 import folder_check, read_file, write_file, check_files
from .relay_audit_157 import bind_responses
from .recorder_lease_156 import Relay, request

START_KEYS={'schema','token','contained','resumed','helper_pid'}
EXIT_KEYS={'schema','token','challenge','exit_observed','cancel_ack','job_closed','clear_ack','close_ack','forced'}


def now_us():return time.monotonic_ns()//1000


class Runner:
    def __init__(self,folder,job,channel,*,enabled=False,clock=now_us,wait=time.sleep,budget_us=30_000_000):
        require(type(enabled) is bool and identifier(job) and type(budget_us) is int and 1<=budget_us<=30_000_000)
        self.folder=Path(folder);self.job=job;self.channel=channel;self.enabled=enabled;self.clock=clock;self.wait=wait;self.budget=budget_us
        self.used=False;self.active=False;self.origin=None;self.last=None;self.responses=[];self.probes=[];self.relay=Relay(job)
        self.cause='off';self.claimed=False;self.attempted=False;self.start_packet=None;self.writer_complete=False;self.native_sha256=None
        self.cancel=None;self.exit=None;self.owner_exit=False;self.cleanup_complete=False;self.receipt_ack=False

    def tick(self,active=True):
        value=self.clock()
        require(type(value) is int and value>=0 and (self.last is None or value>=self.last))
        self.last=value
        if self.origin is None:self.origin=value
        if active and value-self.origin>=self.budget:raise TimeoutError('relay157_deadline')
        return value

    def poll(self,challenge,record):
        require(self.enabled and self.used and self.attempted)
        record['sent_us']=self.tick();record['packet']=None;record['received_us']=None
        raw=self.channel.request('POLL',challenge)
        record['received_us']=self.tick();require(type(raw) is bytes and len(raw)<=2048)
        value=packet(raw,'native_health142_status_v1',STATUS_KEYS)
        require(value['token']==self.job and value['challenge']==challenge and value['operation']=='POLL'
                and all(type(value[k]) is bool for k in STATUS_KEYS-{'schema','token','challenge','operation','sample_sequence','sample_tick_ms','owner_tick_ms'})
                and all(type(value[k]) is int and 0<=value[k]<2**63 for k in ('sample_sequence','sample_tick_ms','owner_tick_ms')))
        # Never persist a rejected schema/binding or arbitrary untrusted string.
        record['packet']=json.dumps(value,separators=(',',':'));return raw

    def readiness(self):
        require(self.enabled and self.used and self.attempted)
        decoder=HealthDecoder(self.job)
        for _ in range(32):
            challenge=uuid.uuid4().hex;record=dict(challenge=challenge,healthy=False);self.probes.append(record)
            raw=self.poll(challenge,record);value=packet(raw,'native_health142_status_v1',STATUS_KEYS)
            observation=decoder.decode(raw,challenge,record['sent_us'],record['received_us'])
            require(value['running'] and value['mains'])
            if observation is not None and all(value[k] for k in ('sample_valid','create_ack','set_ack','ready_signal','helper_running_marker')):
                require(record['received_us']-observation.observed_us<=1_000_000)
                record['healthy']=True
                # Preserve sample history when moving from readiness to served requests.
                self.relay.decoder=decoder;return
            self.wait(.05);self.tick()
        raise ValueError('relay157_readiness_limit')

    def serve(self,index):
        require(self.active and self.enabled and self.used and type(index) is int and 1<=index<=256 and index==len(self.responses)+1)
        raw=read_file(self.folder/f'Request{index:04d}.txt',512)
        job,ordinal,challenge=request(raw);require(job==self.job and ordinal==index)
        require(not (self.folder/f'Reply{index:04d}.txt').exists() and not (self.folder/f'Reply{index:04d}.txt').is_symlink())
        record=dict(ordinal=index,challenge=challenge,request_sha256=hashlib.sha256(raw).hexdigest(),reply_sha256=None,published=False)
        self.responses.append(record);native=self.poll(challenge,record)
        reply=self.relay.reply(raw,native,record['sent_us'],record['received_us'])
        require(reply.endswith(b'\t255\n'))
        observed=self.relay.decoder.observed
        require(observed is not None and record['received_us']-observed<=1_000_000)
        require(self.tick()-observed<=1_000_000);record['reply_sha256']=hashlib.sha256(reply).hexdigest()
        write_file(self.folder/f'Reply{index:04d}.txt',reply)
        require(self.tick()-observed<=1_000_000);record['published']=True

    def cleanup(self):
        if not self.attempted:return
        # Always attempt EXIT and EOF close even if CANCEL fails. No retry or kill.
        try:
            challenge=uuid.uuid4().hex;raw=self.channel.request('CANCEL',challenge)
            value=packet(raw,'native_health142_status_v1',STATUS_KEYS)
            require(value['token']==self.job and value['challenge']==challenge and value['operation']=='CANCEL'
                    and value['contained'] is True and value['cancel_ack'] is True
                    and all(type(value[k]) is bool for k in STATUS_KEYS-{'schema','token','challenge','operation','sample_sequence','sample_tick_ms','owner_tick_ms'})
                    and all(type(value[k]) is int and 0<=value[k]<2**63 for k in ('sample_sequence','sample_tick_ms','owner_tick_ms')))
            self.cancel=dict(challenge=challenge,packet=raw.decode('ascii'))
        except Exception:pass
        try:
            challenge=uuid.uuid4().hex;raw=self.channel.request('EXIT',challenge)
            value=packet(raw,'native_health142_exit_v1',EXIT_KEYS)
            require(value['token']==self.job and value['challenge']==challenge
                    and all(value[k] is True for k in ('exit_observed','cancel_ack','job_closed','clear_ack','close_ack'))
                    and value['forced'] is False)
            self.exit=dict(challenge=challenge,packet=raw.decode('ascii'))
        except Exception:pass
        try:self.channel.close()
        except Exception:return
        self.owner_exit=self.channel.owner_exit_observed is True
        self.cleanup_complete=self.cancel is not None and self.exit is not None and self.owner_exit

    def run(self):
        require(not self.used);self.used=True
        if not self.enabled:return self.snapshot()
        try:
            self.tick();self.folder=folder_check(self.folder,self.job)
            require(all(not (self.folder/name).exists() and not (self.folder/name).is_symlink() for name in ('Relay157.json','Reply0001.txt')))
            write_file(self.folder/'Owner157.claim',b'FXDL157_NO_RESUME\n');self.claimed=True;self.tick()
            self.attempted=True
            raw=self.channel.start(self.job,max(1,(self.budget-(self.last-self.origin)+999)//1000))
            self.tick();value=packet(raw,'native_health142_start_v1',START_KEYS)
            require(value['token']==self.job and value['contained'] is True and value['resumed'] is True
                    and type(value['helper_pid']) is int and 0<value['helper_pid']<2**31)
            self.start_packet=raw.decode('ascii');self.readiness();self.active=True
            for _ in range(4096):
                self.tick();native=read_file(self.folder/'NativePort156.txt',CAP);self.tick()
                # A partial tail is merely unfinished; never parse/promote a prefix.
                if native.endswith(b'\n') and native.splitlines()[-1].startswith(b'E\t'):
                    result=check_files(self.folder,self.job);self.tick()
                    require(result['requests']==len(self.responses) and all(r['published'] for r in self.responses))
                    bind_responses(self.folder,result,self.responses)
                    self.tick()
                    self.native_sha256=result['native_sha256']
                    self.writer_complete=True;self.cause='complete';break
                index=len(self.responses)+1;require(index<=256)
                try:read_file(self.folder/f'Request{index:04d}.txt',512)
                except FileNotFoundError:self.wait(.01);continue
                self.serve(index);self.wait(.001)
            else:raise ValueError('relay157_iteration_limit')
        except TimeoutError:self.cause='deadline'
        except Exception:self.cause='fault'
        finally:
            self.active=False
            active_end=self.last
            if self.attempted:self.cleanup()
            if self.cause=='complete' and not self.cleanup_complete:self.cause='cleanup'
            if self.claimed:
                try:
                    self.tick(active=False)
                    receipt=dict(schema='relay157_receipt_v1',job=self.job,cause=self.cause,origin_us=self.origin,active_end_us=active_end,
                                 last_us=self.last,budget_us=self.budget,start_packet=self.start_packet,probes=self.probes,responses=self.responses,
                                 cancel=self.cancel,exit=self.exit,cleanup_complete=self.cleanup_complete,writer_complete=self.writer_complete)
                    receipt['owner_exit_observed']=self.owner_exit
                    receipt['native_sha256']=self.native_sha256
                    write_file(self.folder/'Relay157.json',(json.dumps(receipt,separators=(',',':'),allow_nan=False)+'\n').encode('ascii'))
                    self.receipt_ack=True
                except Exception:
                    if self.cause=='complete':self.cause='receipt_write'
        return self.snapshot()

    def snapshot(self):
        return dict(schema='relay157_status_v1',cause=self.cause,requests=len(self.responses),published=sum(r['published'] for r in self.responses),
                    start_attempted=self.attempted,cleanup_complete=self.cleanup_complete,writer_complete=self.writer_complete,
                    receipt_acknowledged=self.receipt_ack,native_runtime_certified=False,market_eligible=False)
