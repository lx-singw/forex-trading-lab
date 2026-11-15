"""Independent bounded reader for156 diagnostic bytes; never market admission."""
import hashlib
import math
import re
import struct

CAP=1_048_576
IDENT=re.compile(r'[0-9a-f]{32}')
HEX=re.compile(r'[0-9A-F]{16}')


def require(condition):
    if not condition:raise ValueError('native157_rejected')


def integer(text,low=0,high=2**63-1):
    require(type(text) is str and re.fullmatch(r'0|[1-9][0-9]*|-[1-9][0-9]*',text) is not None)
    require(len(text)<=20)
    value=int(text);require(low<=value<=high);return value


def floating(text):
    require(HEX.fullmatch(text) is not None)
    value=struct.unpack('>d',bytes.fromhex(text))[0];require(math.isfinite(value));return value


def currency(text,empty=False):require((empty and text=='EMPTY') or re.fullmatch('[A-Z]{3}',text) is not None)


def transport(raw,kind,fields):
    require(type(raw) is bytes and 0<len(raw)<=512 and raw.endswith(b'\n'))
    require(all(c==9 or c==10 and i==len(raw)-1 or 32<=c<=126 for i,c in enumerate(raw)))
    parts=raw[:-1].decode('ascii').split('\t')
    require(len(parts)==fields and parts[0]==kind and IDENT.fullmatch(parts[1]) is not None
            and IDENT.fullmatch(parts[3]) is not None)
    integer(parts[2],1,512);return parts


class Reader:
    def __init__(self,raw):
        require(type(raw) is bytes and 0<len(raw)<=CAP and raw.endswith(b'\n'))
        self.rows=[];chain='0'*64
        for line in raw.splitlines(keepends=True):
            require(len(line)<=4096 and line.endswith(b'\n') and all(c in (9,10) or 32<=c<=126 for c in line))
            text=line[:-1].decode('ascii');require('\t' in text)
            payload,digest=text.rsplit('\t',1)
            expected=hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()
            require(digest==expected);chain=digest;self.rows.append(payload.split('\t'))
            require(len(self.rows)<=4096)
        self.pos=0;self.q=0;self.leases=[];self.last_observed=None;self.challenges=set();self.raw_size=len(raw)
        self.failed_fields=0;self.wall_reversals=0

    def row(self,tag,n=None):
        require(self.pos<len(self.rows));row=self.rows[self.pos];self.pos+=1
        require(row[0]==tag and (n is None or len(row)==n));return row

    def lease(self):
        r=self.row('J',9);ordinal=integer(r[1],1,512)
        require(ordinal==len(self.leases)+1 and IDENT.fullmatch(r[2]) is not None and r[2] not in self.challenges)
        sent,received,seq,tick,owner,flags=[integer(v) for v in r[3:]]
        require(seq>0 and tick<=owner and flags==255 and sent<=received and received-sent<=1_000_000)
        age=(owner-tick)*1000;observed=sent-age;require(age<=1_000_000 and observed>=0)
        if self.leases:
            previous=self.leases[-1]
            require(sent>=previous['received'] and seq>=previous['sequence'] and tick>=previous['tick'] and owner>=previous['owner'])
            if seq==previous['sequence']:
                require(tick==previous['tick']);observed=self.last_observed
            else:require(observed>=self.last_observed)
        require(received-observed<=1_000_000)
        value=dict(ordinal=ordinal,challenge=r[2],sent=sent,received=received,sequence=seq,tick=tick,owner=owner,flags=flags,observed=observed)
        self.leases.append(value);self.challenges.add(r[2]);self.last_observed=observed;return value

    def query(self,tag,key,count):
        before=self.lease();self.q+=1;require(self.q<=128)
        require(self.row('A',4)==['A',str(self.q),tag,key])
        after=self.lease();r=self.row(tag,11+count)
        require(r[1:3]==[str(self.q),key])
        wall=[integer(v,-2**63) for v in r[3:6]]
        self.wall_reversals+=int(wall!=sorted(wall))
        bu,au,gu=[integer(v) for v in r[6:9]]
        require(before['received']<=bu<=au<=after['sent'] and after['received']<=gu)
        require(bu-before['observed']<=1_000_000 and gu-after['observed']<=1_000_000)
        ok=integer(r[9],0,1);error=integer(r[10],0,2**31-1);require(not ok or error==0)
        self.failed_fields+=int(not ok);values=r[11:]
        if tag in ('C','T'):require(ok==1)
        if tag=='C':
            for v in values:integer(v,-2**63)
        elif tag=='I':
            integer(values[0],-2**63);require(ok or values==['0'])
        elif tag=='D':
            floating(values[0]);require(ok or values==['0000000000000000'])
        elif tag=='V':
            require(bool(ok)==(error==0))
            if ok:currency(values[0])
            else:require(values==['NA'])
        elif tag=='W':
            for v in values:integer(v,-2**63)
            require(ok or values==['0','0'])
        elif tag=='M':
            for v in values:require(floating(v)>=0)
            require(ok or values==['0000000000000000']*2)
        elif tag=='T':
            seconds=integer(values[0],1,32535215999);millis=integer(values[1],1,32535215999999)
            bid,ask,last=[floating(v) for v in values[2:5]]
            integer(values[5],0,2**64-1);integer(values[6],0,2**32-1)
            require(millis//1000==seconds and bid>0 and ask>=bid and last>=0 and floating(values[7])>=0)
        elif tag=='K':require(bool(ok)==(integer(values[0],-1,2**31-1)>=0 and error==0))
        if tag=='I' and key=='account_leverage':require(bool(ok)==(error==0))
        return bool(ok),values

    def inspect(self):
        h=self.row('H',4);require(h[1:3]==['FXDL_NATIVE_PORT156_V1','non_admitted_prototype'] and IDENT.fullmatch(h[3]) is not None)
        job=h[3];require(self.row('B',2)==['B','1']);self.query('C','context_before',6)
        for key in ('account_leverage','digits','trade_calc_mode','swap_mode','swap_rollover3days','stops_level','freeze_level','execution_mode','order_mode','custom_symbol','subscription_delay','chart_mode'):
            self.query('I',key,1)
        for key in ('point','tick_size','contract_size','tick_value_profit','tick_value_loss','volume_min','volume_max','volume_step','volume_limit','margin_initial','margin_maintenance','swap_long','swap_short','swap_sunday','swap_monday','swap_tuesday','swap_wednesday','swap_thursday','swap_friday','swap_saturday'):
            self.query('D',key,1)
        self.query('V','currency_margin',1)
        for day in range(7):
            for index in range(9):
                ok,_=self.query('W',f'{day}:{index}',2)
                if not ok:break
        ok,values=self.query('K','commissions',1);rules=integer(values[0],-1,2**31-1)
        require(not ok or 0<=rules<=8);require(ok or rules==-1 or rules>=0)
        total=0
        if ok:
            for index in range(rules):
                row=self.row('R',10);require(row[1:3]==[str(self.q),str(index)]);currency(row[3],True)
                for v in row[4:9]:integer(v,-2**31,2**31-1)
                tiers=integer(row[9],0,16);total+=tiers;require(total<=128)
                for tier in range(tiers):
                    row=self.row('L',12);require(row[1:4]==[str(self.q),str(index),str(tier)])
                    for v in row[4:6]:integer(v,-2**31,2**31-1)
                    for v in row[6:11]:floating(v)
                    currency(row[11],True)
        self.query('M','buy',2);self.query('M','sell',2);self.query('C','context_after',6)
        require(self.row('Z',3)==['Z','1',str(self.q)])
        self.query('C','before',6);self.query('T','quote',8);self.query('C','after',6);self.lease()
        require(self.row('E',3)==['E',str(self.q),str(len(self.leases))] and self.pos==len(self.rows))
        require(self.leases[-1]['received']-self.leases[0]['sent']<30_000_000)
        reserved=self.raw_size+sum(len(f'FXDL_REQUEST156_V1\t{job}\t{p["ordinal"]}\t{p["challenge"]}\n')+512 for p in self.leases)
        require(reserved<=CAP)
        return dict(schema='native157_diagnostic_v1',job=job,queries=self.q,requests=len(self.leases),failed_fields=self.failed_fields,
                    wall_marker_reversals=self.wall_reversals,known_reserved_bytes=reserved,writer_complete=True,
                    native_origin_exported=False,native_runtime_certified=False,market_eligible=False,leases=self.leases)


def inspect_native(raw):
    try:return Reader(raw).inspect()
    except (ValueError,IndexError,UnicodeError,OverflowError,TypeError):raise ValueError('native157_rejected') from None
