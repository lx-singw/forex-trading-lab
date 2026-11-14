"""Read-only metadata diagnostic inspection; never admits prices or orders."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026.10.14"
MAX_BYTES, MAX_QUERIES, MAX_US = 65536, 128, 60000000
INTEGER_KEYS = ("account_leverage", "digits", "trade_calc_mode", "swap_mode", "swap_rollover3days",
                "stops_level", "freeze_level", "execution_mode", "order_mode", "custom_symbol", "subscription_delay", "chart_mode")
DOUBLE_KEYS = ("point", "tick_size", "contract_size", "tick_value_profit", "tick_value_loss",
               "volume_min", "volume_max", "volume_step", "volume_limit", "margin_initial",
               "margin_maintenance", "swap_long", "swap_short", "swap_sunday", "swap_monday",
               "swap_tuesday", "swap_wednesday", "swap_thursday", "swap_friday", "swap_saturday")
STRING_KEYS = ("currency_margin",)
ZERO = "0" * 64


def integer(s, maximum=2**63-1, signed=False):
    pattern = r"-?(0|[1-9][0-9]*)" if signed else r"0|[1-9][0-9]*"
    if type(s) is not str or not re.fullmatch(pattern, s) or s == "-0" or abs(int(s)) > maximum:
        raise ValueError("probe_integer")
    return int(s)


def native(s):
    if type(s) is not str or not re.fullmatch(r"[0-9A-F]{16}", s):
        raise ValueError("probe_native_bits")
    value = struct.unpack('>d', bytes.fromhex(s))[0]
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("probe_nonfinite")
    return str(d)


def inspect_bytes(data):
    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("probe_size")
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError:
        raise ValueError("probe_encoding") from None
    chunks = text.split('\r\n');tail = chunks.pop()
    if len(chunks)>260 or any(len(l)>2048 for l in chunks+[tail]):
        raise ValueError("probe_frame_bounds")
    if any('\r' in l or '\n' in l or any((ord(c)<32 and c!='\t') or ord(c)==127 for c in l) for l in chunks+([tail.removesuffix('\r')] if tail else [])):
        raise ValueError("probe_framing")
    chain=ZERO;pending=None;terminal=None;kind=None;count=0;rows=[];origin=None;last=None
    fixed=[('C','clock_before'),('T','tick_before')]+[('I',k) for k in INTEGER_KEYS]+[('D',k) for k in DOUBLE_KEYS]+[('V',k) for k in STRING_KEYS]
    phase=0;day=index=0
    def expected():
        if phase<len(fixed):return fixed[phase]
        if day<7:return ('W',str(day)+':'+str(index))
        if phase==len(fixed):return ('T','tick_after')
        if phase==len(fixed)+1:return ('C','clock_after')
        return None
    def clock(seconds,micros):
        nonlocal last
        if (seconds<last[0] or micros<last[1] or micros-origin[1]>MAX_US
                or abs((seconds-origin[0])-(micros-origin[1])//1000000)>2):
            raise ValueError("probe_clock")
        try:nominal_date=datetime.fromtimestamp(seconds,timezone.utc).strftime('%Y.%m.%d')
        except (ValueError,OverflowError,OSError):raise ValueError("probe_clock_range") from None
        if nominal_date!=DATE:
            raise ValueError("probe_date")
        last=(seconds,micros)
    for line_no,line in enumerate(chunks):
        if not line:raise ValueError("probe_empty_frame")
        try:payload,digest=line.rsplit('\t',1)
        except ValueError:raise ValueError("probe_checksum") from None
        if not re.fullmatch('[0-9A-F]{64}',digest) or hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()!=digest:
            raise ValueError("probe_checksum")
        chain=digest;f=payload.split('\t');tag=f[0]
        if line_no==0:
            if len(f)!=6 or f[:2]!=['H','FXDL127_V1'] or f[2] not in ('market_declared','invented_fixture') or f[3]!=DATE:
                raise ValueError("probe_header")
            origin=(integer(f[4]),integer(f[5],2**64-1));last=origin;kind=f[2]
            if min(origin)<=0:raise ValueError("probe_origin")
            clock(*origin);continue
        if terminal is not None:raise ValueError("probe_after_terminal")
        if tag=='A':
            if len(f)!=4 or pending is not None or count>=MAX_QUERIES or expected()!=(f[2],f[3]):
                raise ValueError("probe_attempt")
            seq=integer(f[1],MAX_QUERIES)
            if seq!=count+1:raise ValueError("probe_sequence")
            count=seq;pending=(seq,f[2],f[3]);continue
        if tag in ('I','D','V','W','T','C'):
            if len(f)<11:raise ValueError("probe_outcome_fields")
            if pending is None or (integer(f[1],MAX_QUERIES),tag,f[2])!=pending:
                raise ValueError("probe_unmatched_outcome")
            bs,ats,gs,bu,au,gu=[integer(x,2**64-1) for x in f[3:9]]
            if not bs<=ats<=gs or not bu<=au<=gu:raise ValueError("probe_receipt_order")
            for pair in ((bs,bu),(ats,au),(gs,gu)):clock(*pair)
            success=integer(f[9],1);error=integer(f[10],2**31-1)
            if success and error:raise ValueError("probe_query_error")
            row={'sequence':count,'type':tag,'key':f[2],'receipt_nominal_gmt_seconds':[bs,ats,gs],
                 'receipt_monotonic_us':[bu,au,gu],'query_succeeded':bool(success),'error_code':error}
            values=f[11:]
            if tag in ('I','D','V'):
                if len(values)!=1:raise ValueError("probe_property_fields")
                if tag=='I':value=integer(values[0],signed=True)
                elif tag=='D':value=native(values[0]);row['native_bits']=values[0]
                else:
                    if not re.fullmatch('[A-Z]{3}|NA',values[0]):raise ValueError("probe_currency")
                    value=values[0]
                if not success and values[0]!=('0000000000000000' if tag=='D' else 'NA' if tag=='V' else '0'):
                    raise ValueError("probe_failed_value")
                row['value']=value if success else None
            elif tag=='W':
                if len(values)!=2:raise ValueError("probe_session_fields")
                row['raw_from_seconds'],row['raw_to_seconds']=[integer(v) for v in values]
                if not success and values!=['0','0']:raise ValueError("probe_failed_value")
            elif tag=='T':
                if len(values)!=8 or not success:raise ValueError("probe_tick_fields")
                seconds,millis=integer(values[0],32535215999),integer(values[1],32535215999999)
                bid,ask,last_price,real_volume=[Decimal(native(values[k])) for k in (2,3,4,7)]
                if seconds<=0 or millis//1000!=seconds or bid<=0 or ask<bid or min(last_price,real_volume)<0:
                    raise ValueError("probe_tick")
                row.update(source_seconds=seconds,source_millis=millis,bid_decimal=str(bid),ask_decimal=str(ask),
                           volume=integer(values[5],2**64-1),raw_flags=integer(values[6],2**32-1),
                           raw_source_minus_nominal_receipt_ms=millis-ats*1000,source_age=None)
                row['native_bits']={k:values[j] for k,j in (('bid',2),('ask',3),('last',4),('volume_real',7))}
            else:
                if len(values)!=6 or not success:raise ValueError("probe_clock_fields")
                row['raw_clocks']=dict(zip(('time_current','time_trade_server','time_gmt','time_local','gmt_offset','daylight_savings'),
                                          [integer(v,signed=True) for v in values]))
            rows.append(row);pending=None
            if tag=='W':
                if not success or index==8:day+=1;index=0
                else:index+=1
            else:phase+=1
            continue
        if tag in ('E','S'):
            if len(f)!=(4 if tag=='E' else 3):raise ValueError("probe_footer")
            if tag=='E':
                if pending is not None or expected() is not None or integer(f[1],MAX_QUERIES)!=count:
                    raise ValueError("probe_premature_end")
                clock(integer(f[2]),integer(f[3],2**64-1));terminal='complete'
            else:
                code=integer(f[1],20)
                if not 2<=code<=20 or integer(f[2],MAX_QUERIES)!=count:raise ValueError("probe_stop")
                terminal='stopped';row_stop=code
            continue
        raise ValueError("probe_record")
    if kind is None:raise ValueError("probe_header")
    if tail and terminal:raise ValueError("probe_tail_after_terminal")
    weekly=[r for r in rows if r['type']=='W']
    return {'schema':'metadata_probe127_inspection_v1','declared_kind':kind,'capture_status':terminal or 'incomplete',
            'stop_code':row_stop if terminal=='stopped' else None,'queries_attempted':count,'queries_recorded':len(rows),
            'pending_attempt':pending is not None,'truncated_tail':bool(tail),'rows':rows,'chain_head':chain,
            'export_sha256':hashlib.sha256(data).hexdigest(),'weekly_template_truncated':any(r['key'].endswith(':8') and r['query_succeeded'] for r in weekly),
            'weekly_template_is_historical_calendar':False,'source_utc_certified':False,'receipt_utc_certified':False,
            'source_age':None,'commission_terms':None,'slippage_terms':None,
            'market_data_qualified':False,'paper_evaluation_available':False,'orders_available':False,
            'real_money_execution_available':False,'producer_authenticated':False}


def inspect_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>MAX_BYTES:raise ValueError("probe_file")
    with p.open('rb') as stream:data=stream.read(MAX_BYTES+1)
    return inspect_bytes(data)
