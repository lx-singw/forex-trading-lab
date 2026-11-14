"""Read-only inspection of one linked111 run; no broker or trading interface."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from pathlib import Path

from .private_recorder_107 import number, native_price, SHA, ZERO

DATE='2026.10.12'
MAX_BYTES=4194304
MAX_FILE=262144
MAX_FILES=64
MAX_ATTEMPTS=7200
MAX_US=3600000000

def inspect_segments(segments):
    """Validate an ordered list of (Segment111-NNN.txt, bytes) pairs.

    Complete earlier frames survive a partial final frame/file. A malformed or
    hash-inconsistent complete frame rejects. Never resume or authenticate data.
    """
    if type(segments) is not list or not 1<=len(segments)<=MAX_FILES:
        raise ValueError('segment_count')
    total=0
    for index,item in enumerate(segments,1):
        if type(item) is not tuple or len(item)!=2 or item[0]!=f'Segment111-{index:03d}.txt' or type(item[1]) is not bytes:
            raise ValueError('segment_order_or_type')
        if len(item[1])>MAX_FILE:raise ValueError('segment_size')
        total+=len(item[1])
    if total>MAX_BYTES:raise ValueError('run_size')
    chain=ZERO
    origin_s=origin_us=kind=None
    attempts=observed=segment_attempts=0
    pending=None
    last_s=last_us=last_read_us=None
    terminal=stop_code=required_stop=None
    rotated=False
    truncated=False
    rows=[]
    repeated=changed=backwards=gaps=missing=invalid=0
    previous_tick=None
    highwater=0
    file_hashes=[]

    def clock(seconds,micros):
        if seconds<origin_s or micros<origin_us or seconds<last_s or micros<last_us:
            raise ValueError('clock_reversal')
        if micros-origin_us>MAX_US:raise ValueError('deadline_exceeded')
        if abs((seconds-origin_s)-(micros-origin_us)//1000000)>2:raise ValueError('clock_jump')
        try:date=datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y.%m.%d')
        except (ValueError,OverflowError,OSError):raise ValueError('clock_range') from None
        if date!=DATE:raise ValueError('date_mismatch')

    for index,(name,data) in enumerate(segments,1):
        if terminal is not None:raise ValueError('segment_after_terminal')
        if index>1 and not rotated:raise ValueError('segment_after_incomplete')
        file_hashes.append({'segment':index,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        if not data:
            if index==1:raise ValueError('header_missing')
            if index<len(segments):raise ValueError('partial_before_final_segment')
            truncated=True;break
        try:text=data.decode('ascii')
        except UnicodeDecodeError:raise ValueError('export_encoding') from None
        if any((ord(c)<32 and c not in '\t\r\n') or ord(c)==127 for c in text):raise ValueError('export_control')
        chunks=text.split('\r\n');tail=chunks.pop()
        if len(chunks)>243 or any(len(c)>2048 for c in chunks) or len(tail)>2048:
            raise ValueError('frame_bounds')
        if any('\r' in c or '\n' in c for c in chunks) or '\n' in tail or '\r' in tail.removesuffix('\r'):
            raise ValueError('physical_framing')
        if (tail or not chunks) and index<len(segments):raise ValueError('partial_before_final_segment')
        if not chunks:
            if index==1:raise ValueError('header_missing')
            truncated=True;break
        rotated=False
        for position,line in enumerate(chunks):
            if not line:raise ValueError('empty_frame')
            try:payload,digest=line.rsplit('\t',1)
            except ValueError:raise ValueError('checksum_missing') from None
            before_chain=chain
            if not SHA.fullmatch(digest) or hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()!=digest:
                raise ValueError('checksum_mismatch')
            chain=digest
            fields=payload.split('\t');record=fields[0]
            if position==0:
                if len(fields)!=13 or fields[:2]!=['H','FXDL111_V1'] or fields[2] not in ('market_declared','invented_fixture') or fields[3]!=DATE:
                    raise ValueError('invalid_header')
                values=[number(v) for v in fields[4:12]]
                seg,os,ou,a,o,read,ws,us=values
                if seg!=index or fields[12]!=before_chain:raise ValueError('header_link')
                if index==1:
                    if not os or not ou or (a,o,read,ws,us)!=(0,0,0,os,ou):raise ValueError('initial_state')
                    origin_s,origin_us,kind=os,ou,fields[2]
                    last_s,last_us,last_read_us=os,ou,0
                elif (os,ou,a,o,read,ws,us,fields[2])!=(origin_s,origin_us,attempts,observed,last_read_us,last_s,last_us,kind):
                    raise ValueError('header_state')
                clock(ws,us);segment_attempts=0
                continue
            if terminal is not None or rotated:raise ValueError('data_after_file_terminal')
            if required_stop is not None and record!='S':raise ValueError('required_stop')
            if record=='A':
                if len(fields)!=2 or pending is not None or segment_attempts>=120 or attempts>=MAX_ATTEMPTS:
                    raise ValueError('invalid_attempt')
                seq=number(fields[1],MAX_ATTEMPTS)
                if seq!=attempts+1:raise ValueError('attempt_sequence')
                attempts=pending=seq;segment_attempts+=1
            elif record in ('Q','N'):
                if len(fields)!=(16 if record=='Q' else 9) or pending is None:raise ValueError('unmatched_outcome')
                seq,bs,ats,gs,bu,au,gu=[number(v) for v in fields[1:8]]
                if seq!=pending or not bs<=ats<=gs or not bu<=au<=gu:raise ValueError('receipt_order')
                for seconds,micros in ((bs,bu),(ats,au),(gs,gu)):clock(seconds,micros)
                if last_read_us:
                    if bu-last_read_us<500000:raise ValueError('sampling_interval')
                    if bu-last_read_us>2000000:gaps+=1
                last_read_us,last_s,last_us=bu,gs,gu
                if record=='N':
                    code=number(fields[8],20)
                    if code not in (15,16):raise ValueError('missing_reason')
                    required_stop=code;missing+=code==15;invalid+=code==16
                else:
                    seconds=number(fields[8],32535215999);millis=number(fields[9],32535215999999)
                    bid,ask,last,volume_real=[native_price(fields[i]) for i in (10,11,12,15)]
                    volume=number(fields[13]);flags=number(fields[14],2**32-1)
                    if not seconds or not millis or millis//1000!=seconds or bid<=0 or ask<bid or last<0 or volume_real<0:
                        raise ValueError('invalid_quote')
                    tick=tuple(fields[8:16])
                    repeated+=tick==previous_tick
                    changed+=previous_tick is not None and tick[1]==previous_tick[1] and tick!=previous_tick
                    backwards+=millis<highwater;highwater=max(highwater,millis);previous_tick=tick
                    observed+=1
                    rows.append({'sequence':seq,'segment':index,'receipt_gmt_seconds':[bs,ats,gs],
                        'receipt_monotonic_us':[bu,au,gu],'source_seconds':seconds,'source_millis':millis,
                        'native_bits':dict(zip(('bid','ask','last','volume_real'),(fields[10],fields[11],fields[12],fields[15]))),
                        'bid_decimal':str(Decimal(str(bid))),'ask_decimal':str(Decimal(str(ask))),
                        'volume':volume,'flags':flags})
                pending=None
            elif record in ('R','E'):
                if len(fields)!=5 or pending is not None or required_stop is not None:raise ValueError('invalid_footer')
                a,o,ws,us=[number(v) for v in fields[1:]]
                if (a,o)!=(attempts,observed):raise ValueError('footer_counts')
                clock(ws,us)
                if record=='R':
                    if segment_attempts!=120 or attempts!=observed or attempts>=MAX_ATTEMPTS or index>=MAX_FILES:
                        raise ValueError('invalid_rotation')
                    rotated=True
                else:
                    if attempts!=MAX_ATTEMPTS or observed!=MAX_ATTEMPTS:raise ValueError('incomplete_end')
                    terminal='complete'
                last_s,last_us=ws,us
            elif record=='S':
                if len(fields)!=4 or (number(fields[2],MAX_ATTEMPTS),number(fields[3],MAX_ATTEMPTS))!=(attempts,observed):
                    raise ValueError('invalid_stop')
                stop_code=number(fields[1],20)
                if stop_code<2 or (required_stop is not None and stop_code!=required_stop):raise ValueError('stop_reason')
                terminal='stopped'
            else:raise ValueError('unknown_record')
        if tail:
            if terminal is not None or rotated:raise ValueError('partial_after_terminal')
            truncated=True
    if origin_s is None:raise ValueError('header_missing')
    return {'schema':'forward_capture_111_inspection_v1','capture_status':terminal or 'incomplete',
        'declared_kind':kind,'synthetic':True if kind=='invented_fixture' else None,'attempts':attempts,'observed':observed,
        'segments':len(segments),'total_bytes':total,'file_hashes':file_hashes,'chain_head':chain,
        'origin_gmt_seconds':origin_s,'origin_monotonic_us':origin_us,'stop_code':stop_code,
        'limit_stop':stop_code==13,'pending_attempt':pending,'truncated_final_segment':truncated,
        'rotation_without_next_header':rotated and terminal is None,
        'missing':missing,'invalid':invalid,'repeated_snapshots':repeated,'equal_time_changed':changed,
        'source_backwards':backwards,'receipt_gaps':gaps,'sampling':'poll_latest','symbol':'EURUSD',
        'producer_authentication':'unverified','receipt_clock':'pc_gmt_unverified','source_clock':'raw_unverified',
        'source_age_known':False,'complete_tick_delivery':False,'use_rights_certified':False,
        'resume_available':False,'market_data_qualified':False,'paper_evaluation_available':False,
        'orders_available':False,'real_money_execution_available':False,'observations':rows}

def inspect_run(path):
    root=Path(path)
    if root.is_symlink():raise ValueError('run_symlink')
    files=[]
    for p in root.iterdir():
        if len(files)>=MAX_FILES or p.is_symlink() or not p.is_file():raise ValueError('run_files')
        files.append(p)
    files.sort(key=lambda p:p.name)
    segments=[];total=0
    for index,p in enumerate(files,1):
        if p.name!=f'Segment111-{index:03d}.txt':raise ValueError('run_filenames')
        with p.open('rb') as f:data=f.read(MAX_FILE+1)
        total+=len(data)
        if len(data)>MAX_FILE or total>MAX_BYTES:raise ValueError('run_size')
        segments.append((p.name,data))
    return inspect_segments(segments)

def summary(result):return {k:v for k,v in result.items() if k!='observations'}
