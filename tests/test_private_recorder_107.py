from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

from forex_demo_lab.private_recorder_107 import inspect_bytes, inspect_file, summary, MAX_BYTES

ROOT=Path(__file__).resolve().parents[1]
START=int(datetime(2026,10,12,12,tzinfo=timezone.utc).timestamp())

def bits(value): return struct.pack('>d',value).hex().upper()
def header(kind='invented_fixture'): return f'H\tFXDL107_V1\t{kind}\t2026.10.12\t120\t60000000\t500000\t{START}\t1000'
def quote(i=1, source=None, bid=1.1, ask=1.1002):
    us=1000+(i-1)*500000;s=START+(i-1)//2
    raw=source if source is not None else (START+10800)*1000
    return f'Q\t{i}\t{s}\t{s}\t{s}\t{us}\t{us+10}\t{us+20}\t{raw//1000}\t{raw}\t{bits(bid)}\t{bits(ask)}\t{bits(0.0)}\t0\t1154\t{bits(0.0)}'
def finish(): return f'E\t120\t120\t{START+59}\t59501100\t363'
def complete(kind='invented_fixture'):
    result=[header(kind)]
    for i in range(1,121): result += [f'A\t{i}',quote(i)]
    return result+[finish()]
def encode(rows, ending=b'\r\n'):
    previous='0'*64;out=b''
    for row in rows:
        checksum=hashlib.sha256((previous+'\t'+row+'\n').encode('ascii')).hexdigest().upper()
        out += (row+'\t'+checksum).encode('ascii')+ending;previous=checksum
    return out

class PrivateRecorder107Tests(unittest.TestCase):
    def test_shared_native_guard_decisions(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'guards'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/PrivateGuard107.cpp'),'-o',str(exe)],capture_output=True,check=True,timeout=30)
            r=subprocess.run([str(exe)],capture_output=True,check=True,timeout=5,text=True)
            self.assertEqual(json.loads(r.stdout),{'guard_checks':48,'passed':True})
    def test_complete_invented_capture(self):
        r=inspect_bytes(encode(complete()))
        self.assertEqual((r['capture_status'],r['attempts'],r['observed']),('complete',120,120))
        self.assertTrue(r['synthetic'])
        self.assertFalse(r['market_data_qualified'])
    def test_market_declaration_is_not_authentication(self):
        r=inspect_bytes(encode(complete('market_declared')))
        self.assertIsNone(r['synthetic'])
        self.assertEqual(r['producer_authentication'],'unverified')
        for key in ('market_data_qualified','paper_evaluation_available','orders_available','use_rights_certified','provider_tick_identity','complete_tick_delivery','resume_available'):
            self.assertFalse(r[key])
    def test_repeat_snapshots_retained(self):
        r=inspect_bytes(encode(complete()))
        self.assertEqual(r['repeated_snapshots'],119)
        self.assertEqual(len(r['observations']),120)
    def test_equal_time_changed_flags_retained(self):
        rows=complete();rows[4]=rows[4].replace('\t1154\t','\t1158\t')
        r=inspect_bytes(encode(rows));self.assertEqual(r['equal_time_changed'],2)
        self.assertEqual(r['observations'][1]['flags'],1158)
    def test_raw_source_reversal_is_a_diagnostic(self):
        rows=[header(),'A\t1',quote(1),'A\t2',quote(2,source=(START+10800)*1000-1000),'S\t18\t2']
        r=inspect_bytes(encode(rows));self.assertEqual(r['source_backwards'],1)
        self.assertEqual(r['observed'],2);self.assertFalse(r['source_age_known'])
    def test_native_bits_preserved_with_decimal_conversion(self):
        r=inspect_bytes(encode(complete()))['observations'][0]
        self.assertEqual(r['native_bits']['bid'],bits(1.1));self.assertEqual(r['bid_decimal'],'1.1')
        self.assertEqual(r['ask_decimal'],'1.1002')
    def test_hash_tampering_rejected(self):
        data=encode(complete()).replace(b'1154',b'1158',1)
        with self.assertRaisesRegex(ValueError,'checksum'):inspect_bytes(data)
    def test_reordered_records_rejected_even_with_new_checksums(self):
        rows=complete();rows[1],rows[3]=rows[3],rows[1]
        with self.assertRaises(ValueError):inspect_bytes(encode(rows))
    def test_pending_attempt_visible_without_restart(self):
        r=inspect_bytes(encode([header(),'A\t1']))
        self.assertEqual(r['capture_status'],'incomplete');self.assertEqual(r['pending_attempt'],1)
        self.assertFalse(r['resume_available'])
    def test_truncated_outcome_preserves_prior_rows(self):
        r=inspect_bytes(encode([header(),'A\t1'])+b'Q\t1\tpartial')
        self.assertTrue(r['truncated_tail']);self.assertEqual(r['pending_attempt'],1);self.assertEqual(r['observed'],0)
    def test_stop_after_guard_failure_contains_no_second_quote(self):
        r=inspect_bytes(encode([header(),'A\t1',quote(1),'A\t2','S\t9\t2']))
        self.assertEqual((r['capture_status'],r['observed'],r['stop_code'],r['pending_attempt']),('stopped',1,9,2))
    def test_missing_outcome(self):
        q=quote().split('\t');n='\t'.join(['N']+q[1:8]+['15'])
        r=inspect_bytes(encode([header(),'A\t1',n,'S\t15\t1']))
        self.assertEqual((r['missing'],r['observed']),(1,0))
    def test_invalid_outcome(self):
        q=quote().split('\t');n='\t'.join(['N']+q[1:8]+['16'])
        r=inspect_bytes(encode([header(),'A\t1',n,'S\t16\t1']))
        self.assertEqual((r['invalid'],r['observed']),(1,0))
    def test_failed_read_cannot_continue_with_another_attempt(self):
        n='\t'.join(['N']+quote().split('\t')[1:8]+['15'])
        with self.assertRaisesRegex(ValueError,'missing_terminal_stop'):
            inspect_bytes(encode([header(),'A\t1',n,'A\t2']))
    def test_failed_read_stop_reason_must_match(self):
        n='\t'.join(['N']+quote().split('\t')[1:8]+['16'])
        for code in (9,14,15):
            with self.subTest(code=code),self.assertRaisesRegex(ValueError,'stop_reason_mismatch'):
                inspect_bytes(encode([header(),'A\t1',n,f'S\t{code}\t1']))
    def test_failed_read_without_footer_remains_incomplete(self):
        n='\t'.join(['N']+quote().split('\t')[1:8]+['15'])
        r=inspect_bytes(encode([header(),'A\t1',n]))
        self.assertEqual((r['capture_status'],r['missing'],r['pending_attempt']),('incomplete',1,None))
    def test_completion_requires_all_counts(self):
        for footer in ('E\t119\t120\t'+str(START+59)+'\t59501100\t363',finish().replace('\t363','\t362'),finish().replace('\t120\t120','\t120\t119')):
            with self.subTest(footer=footer),self.assertRaises(ValueError):inspect_bytes(encode(complete()[:-1]+[footer]))
    def test_footer_cannot_approve_pending_attempt(self):
        with self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1',finish()]))
    def test_data_after_footer_or_stop_rejected(self):
        for rows in (complete()+['A\t121'],[header(),'S\t18\t0','A\t1']):
            with self.subTest(rows=len(rows)),self.assertRaises(ValueError):inspect_bytes(encode(rows))
    def test_partial_data_after_terminal_rejected(self):
        with self.assertRaises(ValueError):inspect_bytes(encode(complete())+b'partial')
    def test_no_empty_or_oversize_input(self):
        for data in (b'',b'x'*(MAX_BYTES+1)):
            with self.subTest(size=len(data)),self.assertRaises(ValueError):inspect_bytes(data)
    def test_line_and_record_bounds(self):
        for data in (b'x'*2049,encode([header()]+['A\t1']*243)):
            with self.assertRaises(ValueError):inspect_bytes(data)
    def test_encoding_and_control_rejected(self):
        for data in (encode(complete())+b'\xff',encode(complete())+b'\x00',encode(complete()).replace(b'\r\n',b'\r\r\n',1)):
            with self.assertRaises(ValueError):inspect_bytes(data)
    def test_unknown_or_private_columns_rejected(self):
        for row in (quote()+'\tprivate-identity','PRIVATE\tvalue'):
            with self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1',row]))
    def test_header_scope_and_budget_cannot_be_relabelled(self):
        for h in (header().replace('invented_fixture','live'),header().replace('60000000','60000001'),header().replace('2026.10.12','2026.10.13')):
            with self.assertRaises(ValueError):inspect_bytes(encode([h]))
    def test_invalid_integer_formats(self):
        for seq in ('01','-1','True','1.0',str(2**64)):
            with self.subTest(seq=seq),self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t'+seq]))
    def test_nonfinite_crossed_and_nonpositive_quotes(self):
        for b,a in ((float('nan'),1.1),(1.0,float('inf')),(0.0,1.1),(1.2,1.1)):
            with self.subTest(b=b,a=a),self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1',quote(bid=b,ask=a)]))
    def test_source_seconds_millis_disagreement(self):
        fields=quote().split('\t');fields[8]=str(int(fields[8])+1)
        with self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1','\t'.join(fields)]))
    def test_unsigned_flags_and_volume_bounds(self):
        for idx,val in ((13,str(2**64)),(14,str(2**32)),(15,bits(-1.0)),(12,bits(-1.0))):
            fields=quote().split('\t');fields[idx]=val
            with self.subTest(idx=idx),self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1','\t'.join(fields)]))
    def test_receipt_reversal_and_wall_jump_rejected(self):
        for idx,val in ((3,str(START-1)),(6,'999'),(4,str(START+3))):
            fields=quote().split('\t');fields[idx]=val
            with self.subTest(idx=idx),self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1','\t'.join(fields)]))
    def test_deadline_and_date_rejected(self):
        fields=quote().split('\t');fields[7]='60001001'
        with self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1','\t'.join(fields)]))
        with self.assertRaises(ValueError):inspect_bytes(encode([header().replace(str(START),str(START+86400))]))
    def test_sampling_interval_cannot_be_shortened(self):
        fields=quote(2).split('\t');fields[5:8]=['2000','2010','2020']
        with self.assertRaises(ValueError):inspect_bytes(encode([header(),'A\t1',quote(1),'A\t2','\t'.join(fields)]))
    def test_gap_diagnostic(self):
        fields=quote(2).split('\t');fields[2:5]=[str(START+3)]*3;fields[5:8]=['3001000','3001010','3001020']
        r=inspect_bytes(encode([header(),'A\t1',quote(1),'A\t2','\t'.join(fields),'S\t18\t2']))
        self.assertEqual(r['receipt_gaps'],1)
    def test_file_inspection_read_only_and_summary_omits_prices(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.txt';data=encode(complete());p.write_bytes(data)
            r=inspect_file(p);self.assertEqual(p.read_bytes(),data)
            self.assertNotIn('observations',summary(r));self.assertNotIn('bid_decimal',json.dumps(summary(r)))
    def test_lf_encoding_checksums_match_crlf(self):
        self.assertEqual(inspect_bytes(encode(complete(),b'\n'))['chain_head'],inspect_bytes(encode(complete()))['chain_head'])
    def test_native_source_default_off_no_order_network_or_attachment(self):
        source=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder107.mq5').read_text()
        self.assertIn('input bool RecordDiagnosticSnapshots = false;',source)
        self.assertNotRegex(source,r'\b(OrderSend|OrderSendAsync|OrderCheck|WebRequest|SymbolSelect|CopyTicks|CTrade|OnTick|OnTimer)\b|#import')
        self.assertIn('FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI',source)
        self.assertNotIn('FILE_COMMON',source)
        self.assertIn('existing_size!=0 || size_error!=0',source)
        self.assertEqual(len(re.findall(r'\bSymbolInfoTick\s*\(',source)),1)
        after=source.index('reason=ReadGuard107(true,login,server);',source.index('bool ok=SymbolInfoTick'))
        discard=source.index('if(reason!=0) { Stop107(handle,reason); return; }',after)
        self.assertLess(discard,source.index('string payload="Q'))
        for line in source.splitlines():
            if 'PrintFormat(' in line or 'Append107(handle,' in line:
                self.assertNotRegex(line,r'\blogin\b|\bserver\b|AccountInfo')

if __name__=='__main__':unittest.main()
