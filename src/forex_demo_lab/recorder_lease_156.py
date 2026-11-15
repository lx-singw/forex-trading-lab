"""Terminal-local challenge/reply lease codec. No helper launch or MT5 access.

An already-owned channel can implement143's request interface in a future bounded
runner. This module has no launch/discovery/polling CLI or collection permission.
"""
from pathlib import Path
import os
import re

from .helper_health_142 import HealthDecoder, STATUS_KEYS, packet

MAX_BYTES=512
IDENTIFIER=re.compile('[a-f0-9]{32}')


def number(value):
    if type(value) is not str or not re.fullmatch('0|[1-9][0-9]{0,18}',value):raise ValueError('lease156_integer')
    n=int(value)
    if n>=2**63:raise ValueError('lease156_integer')
    return n


def request(raw):
    if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES or not raw.endswith(b'\n') or b'\r' in raw:
        raise ValueError('lease156_frame')
    try:fields=raw[:-1].decode('ascii').split('\t')
    except UnicodeError:raise ValueError('lease156_ascii') from None
    if (len(fields)!=4 or fields[0]!='FXDL_REQUEST156_V1' or not IDENTIFIER.fullmatch(fields[1])
            or not IDENTIFIER.fullmatch(fields[3]) or not 1<=number(fields[2])<=512):raise ValueError('lease156_request')
    return fields[1],number(fields[2]),fields[3]


class Relay:
    """One run's ordered requests. An IO/protocol fault poisons it permanently."""
    def __init__(self,job):
        if type(job) is not str or not IDENTIFIER.fullmatch(job):raise ValueError('lease156_job')
        self.job=job;self.decoder=HealthDecoder(job);self.last=0;self.poisoned=False

    def reply(self,raw,native_packet,sent_us,received_us):
        if self.poisoned:raise ValueError('lease156_poisoned')
        try:
            job,sequence,challenge=request(raw)
            if job!=self.job or sequence!=self.last+1:raise ValueError('lease156_order')
            report=self.decoder.decode(native_packet,challenge,sent_us,received_us)
            value=packet(native_packet,'native_health142_status_v1',STATUS_KEYS)
            if report is None:raise ValueError('lease156_not_ready')
            names=('contained','running','sample_valid','create_ack','set_ack','ready_signal','mains','helper_running_marker')
            flags=sum((1<<i) for i,key in enumerate(names) if value[key])
            # Raw native ticks are preserved. MQL adds its own full response transit.
            result=('FXDL_REPLY156_V1\t'+job+'\t'+str(sequence)+'\t'+challenge+'\t'+str(value['sample_sequence'])+'\t'
                    +str(value['sample_tick_ms'])+'\t'+str(value['owner_tick_ms'])+'\t'+str(flags)+'\n').encode('ascii')
            if len(result)>MAX_BYTES:raise ValueError('lease156_reply_bound')
            self.last=sequence
            return result
        except (ValueError,TypeError,KeyError):
            self.poisoned=True;raise ValueError('lease156_rejected') from None

    def service(self,folder,sequence,channel,sent_us,received_us):
        """One explicit owned request, not directory discovery or a worker loop.

        Caller supplies receipt markers for an invented exercise; actual wall-clock
        and owned-channel integration need a separately reviewed runtime runner.
        """
        if self.poisoned:raise ValueError('lease156_poisoned')
        try:
            folder=Path(folder)
            if (folder.name!='Job156-'+self.job or not folder.is_dir()
                    or any(p.is_symlink() for p in (folder,*folder.parents))
                    or type(sequence) is not int or not 1<=sequence<=512):raise ValueError('lease156_folder')
            req=folder/f'Request{sequence:04d}.txt';out=folder/f'Reply{sequence:04d}.txt'
            if req.is_symlink() or not req.is_file() or out.exists() or out.is_symlink():raise ValueError('lease156_files')
            with req.open('rb') as file:raw=file.read(MAX_BYTES+1)
            job,index,challenge=request(raw)
            if job!=self.job or index!=sequence or sequence!=self.last+1:raise ValueError('lease156_request_binding')
            reply=self.reply(raw,channel.request('POLL',challenge),sent_us,received_us)
            with out.open('xb',buffering=0) as file:
                if file.write(reply)!=len(reply):raise OSError('short_write')
                os.fsync(file.fileno())
            return reply
        except Exception:
            self.poisoned=True;raise ValueError('lease156_service_failed') from None
