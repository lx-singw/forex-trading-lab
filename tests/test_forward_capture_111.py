from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from forex_demo_lab.forward_capture_111 import inspect_segments,inspect_run,summary,MAX_BYTES,MAX_FILE

ROOT=Path(__file__).resolve().parents[1]
START=int(datetime(2026,10,12,12,tzinfo=timezone.utc).timestamp())
def bits(v):return struct.pack('>d',v).hex().upper()
def quote(i):
    us=1000+(i-1)*500000;s=START+(i-1)//2;source=(START+10800)*1000
    return f'Q\t{i}\t{s}\t{s}\t{s}\t{us}\t{us+10}\t{us+20}\t{source//1000}\t{source}\t{bits(1.1)}\t{bits(1.1002)}\t{bits(0.0)}\t0\t1154\t{bits(0.0)}'
def payloads(count=240,terminal='S',kind='invented_fixture'):
    result=[];done=0;last_read=0;wall=START;guard=1000
    while True:
        rows=[f'H\tFXDL111_V1\t{kind}\t2026.10.12\t{len(result)+1}\t{START}\t1000\t{done}\t{done}\t{last_read}\t{wall}\t{guard}\tLINK']
        n=min(120,count-done)
        for i in range(done+1,done+n+1):rows += [f'A\t{i}',quote(i)]
        done+=n
        if n:
            last_read=1000+(done-1)*500000;wall=START+(done-1)//2;guard=last_read+40
        if done==count and terminal=='S':rows += [f'S\t18\t{done}\t{done}']
        else:rows += [f'{"E" if done==7200 else "R"}\t{done}\t{done}\t{wall}\t{guard}']
        result.append(rows)
        if done==count:return result
def encode(groups):
    chain='0'*64;result=[]
    for index,group in enumerate(groups,1):
        data=b''
        for row in group:
            if row.startswith('H\t') and row.endswith('\tLINK'):row=row[:-4]+chain
            digest=hashlib.sha256((chain+'\t'+row+'\n').encode('ascii')).hexdigest().upper()
            data+=(row+'\t'+digest+'\r\n').encode('ascii');chain=digest
        result.append((f'Segment111-{index:03d}.txt',data))
    return result

class ForwardCapture111Tests(unittest.TestCase):
    def test_actual_shared_core_and_guard_integration(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'run'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(ROOT/'mt5/Tests/PrivateRun111.cpp'),'-o',str(exe)],capture_output=True,check=True,timeout=30)
            r=json.loads(subprocess.run([str(exe)],capture_output=True,check=True,text=True,timeout=5).stdout)
            self.assertTrue(r['passed']);self.assertGreater(r['core_checks'],43000)
            self.assertEqual((r['ideal_attempts'],r['ideal_observed'],r['ideal_segments']),(7200,7200,60))
            self.assertEqual(r['account_fault_scenarios'],12);self.assertEqual(r['native_calls'],0)
    def test_complete_invented_hour_with_sixty_linked_segments(self):
        r=inspect_segments(encode(payloads(7200,terminal='E')))
        self.assertEqual((r['capture_status'],r['attempts'],r['observed'],r['segments']),('complete',7200,7200,60))
        self.assertTrue(r['synthetic']);self.assertFalse(r['resume_available'])
    def test_rotation_preserves_repeats_and_global_sequence(self):
        r=inspect_segments(encode(payloads()))
        self.assertEqual(r['repeated_snapshots'],239)
        self.assertEqual(r['observations'][120]['sequence'],121)
        self.assertEqual(r['observations'][120]['segment'],2)
    def test_market_declaration_never_promotes_admission(self):
        r=inspect_segments(encode(payloads(1,kind='market_declared')))
        self.assertIsNone(r['synthetic']);self.assertEqual(r['producer_authentication'],'unverified')
        for key in ('source_age_known','complete_tick_delivery','use_rights_certified','resume_available','market_data_qualified','paper_evaluation_available','orders_available','real_money_execution_available'):
            self.assertFalse(r[key])
    def test_early_completion_rejected(self):
        g=payloads(1);g[0][-1]=f'E\t1\t1\t{START}\t1040'
        with self.assertRaisesRegex(ValueError,'incomplete_end'):inspect_segments(encode(g))
    def test_rotation_requires_all120_resolved(self):
        g=payloads(1);g[0][-1]=f'R\t1\t1\t{START}\t1040'
        with self.assertRaisesRegex(ValueError,'invalid_rotation'):inspect_segments(encode(g))
    def test_files_cannot_be_skipped_reordered_or_duplicated(self):
        data=encode(payloads())
        for bad in (data[::-1],[data[0],data[0]],[data[1]]):
            with self.assertRaisesRegex(ValueError,'segment_order'):inspect_segments(bad)
    def test_header_counter_reset_rejected(self):
        g=payloads();h=g[1][0].split('\t');h[7:9]=['0','0'];g[1][0]='\t'.join(h)
        with self.assertRaisesRegex(ValueError,'header_state'):inspect_segments(encode(g))
    def test_header_origin_reset_rejected(self):
        g=payloads();h=g[1][0].split('\t');h[6]='60001000';g[1][0]='\t'.join(h)
        with self.assertRaisesRegex(ValueError,'header_state'):inspect_segments(encode(g))
    def test_header_kind_mixing_rejected(self):
        g=payloads();g[1][0]=g[1][0].replace('invented_fixture','market_declared')
        with self.assertRaisesRegex(ValueError,'header_state'):inspect_segments(encode(g))
    def test_header_chain_link_rejected_even_when_rehashed(self):
        g=payloads();g[1][0]=g[1][0].replace('LINK','0'*64)
        with self.assertRaisesRegex(ValueError,'header_link'):inspect_segments(encode(g))
    def test_changed_payload_with_old_hash_rejected(self):
        data=encode(payloads(1));name,raw=data[0]
        with self.assertRaisesRegex(ValueError,'checksum'):inspect_segments([(name,raw.replace(b'1154',b'1158'))])
    def test_cross_segment_minimum_interval(self):
        g=payloads(121);f=g[1][2].split('\t');f[5:8]=[str(int(v)-1) for v in f[5:8]];g[1][2]='\t'.join(f)
        with self.assertRaisesRegex(ValueError,'sampling_interval'):inspect_segments(encode(g))
    def test_cross_segment_receipt_gap_is_visible(self):
        g=payloads(121);f=g[1][2].split('\t')
        f[2:5]=[str(int(v)+3) for v in f[2:5]];f[5:8]=[str(int(v)+3000000) for v in f[5:8]];g[1][2]='\t'.join(f)
        self.assertEqual(inspect_segments(encode(g))['receipt_gaps'],1)
    def test_global_deadline_cannot_reset_at_rotation(self):
        g=payloads(121);f=g[1][2].split('\t')
        f[2:5]=[str(START+3600)]*3;f[5:8]=['3600001001','3600001011','3600001021'];g[1][2]='\t'.join(f)
        with self.assertRaisesRegex(ValueError,'deadline_exceeded'):inspect_segments(encode(g))
    def test_pending_attempt_and_partial_outcome_preserved(self):
        g=payloads(1);g[0]=g[0][:2]
        data=encode(g);r=inspect_segments([(data[0][0],data[0][1]+b'Q\t1\tpartial')])
        self.assertEqual((r['capture_status'],r['pending_attempt'],r['observed']),('incomplete',1,0))
        self.assertTrue(r['truncated_final_segment']);self.assertFalse(r['resume_available'])
    def test_stop_after_after_guard_failure_discards_pending_quote(self):
        g=payloads(1);g[0]=g[0][:2]+['S\t9\t1\t0']
        r=inspect_segments(encode(g));self.assertEqual((r['capture_status'],r['pending_attempt'],r['observed']),('stopped',1,0))
    def test_missing_invalid_outcomes_require_matching_stop(self):
        for code in (15,16):
            g=payloads(1);g[0][2]='\t'.join(['N']+g[0][2].split('\t')[1:8]+[str(code)]);g[0][-1]=f'S\t{code}\t1\t0'
            r=inspect_segments(encode(g));self.assertEqual(r['missing']+r['invalid'],1)
            self.assertEqual(r['stop_code'],code)
    def test_failed_outcome_cannot_restart_or_mislabel_stop(self):
        for last in ('A\t2','S\t14\t1\t0','S\t9\t1\t0'):
            g=payloads(1);g[0][2]='\t'.join(['N']+g[0][2].split('\t')[1:8]+['15']);g[0][-1]=last
            with self.assertRaises(ValueError):inspect_segments(encode(g))
    def test_empty_last_segment_is_incomplete_and_hashed(self):
        data=encode(payloads(120,terminal=None))+[('Segment111-002.txt',b'')]
        r=inspect_segments(data);self.assertEqual(r['capture_status'],'incomplete')
        self.assertTrue(r['truncated_final_segment']);self.assertEqual(r['file_hashes'][-1]['sha256'],hashlib.sha256(b'').hexdigest())
    def test_empty_middle_segment_not_silently_ignored(self):
        data=encode(payloads(120,terminal=None))+[('Segment111-002.txt',b''),('Segment111-003.txt',b'partial')]
        with self.assertRaisesRegex(ValueError,'partial_before_final'):inspect_segments(data)
    def test_partial_header_after_rotation_is_incomplete(self):
        data=encode(payloads(120,terminal=None))+[('Segment111-002.txt',b'H\tFXDL111_')]
        r=inspect_segments(data);self.assertTrue(r['truncated_final_segment']);self.assertEqual(r['observed'],120)
    def test_rotation_without_next_header_is_not_completion(self):
        r=inspect_segments(encode(payloads(120,terminal=None)))
        self.assertEqual(r['capture_status'],'incomplete');self.assertTrue(r['rotation_without_next_header'])
    def test_terminal_disallows_more_records_files_or_tail(self):
        g=payloads(1)
        for bad in (encode([g[0]+['A\t2']]),encode(g)+[('Segment111-002.txt',b'H')],[(encode(g)[0][0],encode(g)[0][1]+b'tail')]):
            with self.assertRaises(ValueError):inspect_segments(bad)
    def test_unfinished_segment_cannot_lead_to_next_file(self):
        g=payloads(1);g[0]=g[0][:-1]
        with self.assertRaisesRegex(ValueError,'segment_after_incomplete'):inspect_segments(encode(g)+[('Segment111-002.txt',b'H')])
    def test_global_and_per_file_allocation_caps(self):
        for data in ([],[(f'Segment111-{i:03d}.txt',b'x') for i in range(1,66)],
            [('Segment111-001.txt',b'x'*(MAX_FILE+1))],[(f'Segment111-{i:03d}.txt',b'x'*MAX_FILE) for i in range(1,18)]):
            with self.assertRaises(ValueError):inspect_segments(data)
    def test_frame_encoding_control_and_size_bounds(self):
        data=encode(payloads(1));name,raw=data[0]
        for bad in (raw+b'\xff',raw+b'\x00',raw+b'\x7f',raw+b'x'*2049,raw.replace(b'\r\n',b'\n'),raw+b'\rX'):
            with self.assertRaises(ValueError):inspect_segments([(name,bad)])
    def test_private_or_unknown_columns_rejected(self):
        for row in (quote(1)+'\tprivate-account','PRIVATE\tvalue'):
            g=payloads(1);g[0][2]=row
            with self.assertRaises(ValueError):inspect_segments(encode(g))
    def test_native_bits_and_unknown_flags_are_preserved(self):
        g=payloads(1);q=g[0][2].split('\t');q[14]=str(2**32-1);g[0][2]='\t'.join(q)
        r=inspect_segments(encode(g))['observations'][0]
        self.assertEqual(r['native_bits']['bid'],bits(1.1));self.assertEqual(r['bid_decimal'],'1.1')
        self.assertEqual(r['flags'],2**32-1)
    def test_invalid_prices_flags_volume_and_source_coherence(self):
        for idx,val in ((10,bits(float('nan'))),(11,bits(1.0)),(12,bits(-1.0)),(13,str(2**64)),(14,str(2**32)),(15,bits(-1.0)),(8,str(START+1))):
            g=payloads(1);q=g[0][2].split('\t');q[idx]=val;g[0][2]='\t'.join(q)
            with self.subTest(idx=idx),self.assertRaises(ValueError):inspect_segments(encode(g))
    def test_source_reversal_and_same_time_changed_flags_visible(self):
        g=payloads(3);q=g[0][4].split('\t');q[14]='1158';g[0][4]='\t'.join(q)
        r=inspect_segments(encode(g));self.assertEqual(r['equal_time_changed'],2)
        g=payloads(2);q=g[0][4].split('\t');q[9]=str(int(q[9])-1000);q[8]=str(int(q[9])//1000);g[0][4]='\t'.join(q)
        r=inspect_segments(encode(g));self.assertEqual(r['source_backwards'],1);self.assertFalse(r['source_age_known'])
    def test_clock_date_drift_and_reversal_rejected(self):
        for idx,val in ((3,str(START-1)),(5,'999'),(4,str(START+3))):
            g=payloads(1);q=g[0][2].split('\t');q[idx]=val;g[0][2]='\t'.join(q)
            with self.assertRaises(ValueError):inspect_segments(encode(g))
        g=payloads(1);g[0][0]=g[0][0].replace('2026.10.12','2026.10.13')
        with self.assertRaises(ValueError):inspect_segments(encode(g))
    def test_stop_footer_counts_and_integer_formats_rejected(self):
        for stop in ('S\t18\t1\t0','S\t1\t1\t1','S\t21\t1\t1','S\t18\t01\t1'):
            g=payloads(1);g[0][-1]=stop
            with self.assertRaises(ValueError):inspect_segments(encode(g))
    def test_read_only_directory_inspection_and_summary(self):
        with tempfile.TemporaryDirectory() as d:
            data=encode(payloads());root=Path(d)
            for name,raw in data:(root/name).write_bytes(raw)
            r=inspect_run(root);self.assertEqual(r['observed'],240)
            for name,raw in data:self.assertEqual((root/name).read_bytes(),raw)
            self.assertNotIn('observations',summary(r));self.assertNotIn('bid_decimal',json.dumps(summary(r)))
    def test_directory_symlinks_and_unexpected_files_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'unexpected.txt').write_bytes(b'x')
            with self.assertRaises(ValueError):inspect_run(root)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'fixture').write_bytes(b'x');(root/'Segment111-001.txt').symlink_to(root/'fixture')
            with self.assertRaises(ValueError):inspect_run(root)
    def test_native_default_off_and_read_only_capability(self):
        s=(ROOT/'mt5/Scripts/ForexDemoForwardCapture111.mq5').read_text()
        self.assertIn('input bool CollectOneHour = false;',s)
        self.assertNotRegex(s,r'\b(OrderSend|OrderSendAsync|CTrade|WebRequest|SymbolSelect|initialize|login)\s*\(')
        self.assertNotIn('#import',s);self.assertNotIn('FILE_COMMON',s)
        self.assertIn('FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI',s)
        self.assertNotIn('Init111(',s[s.index('   while(true) {'):])
    def test_native_order_of_attempt_write_guard_read_discard_and_outcome(self):
        s=(ROOT/'mt5/Scripts/ForexDemoForwardCapture111.mq5').read_text()
        a=s.index('"A\\t%d"');tick=s.index('SymbolInfoTick(');out=s.index('string payload=')
        self.assertLess(a,tick);self.assertLess(tick,out)
        self.assertIn('ReadGuard111(true,login,server)',s[a:tick])
        self.assertIn('if(reason!=0) { Stop111(handle,reason);return; }',s[tick:out])
        self.assertLess(s.index('Reserve111(run111'),s.index('FileWriteString(handle,line)'))
    def test_existing_guard_implementation_reused_and_identity_not_logged(self):
        old=(ROOT/'mt5/Scripts/ForexDemoPrivateRecorder109.mq5').read_text()
        new=(ROOT/'mt5/Scripts/ForexDemoForwardCapture111.mq5').read_text()
        old_guard=old[old.index('int ReadGuard107'):old.index('int Clock107')]
        new_guard=new[new.index('int ReadGuard111'):new.index('void Status111')]
        self.assertEqual(old_guard.replace('ReadGuard107','ReadGuard111').replace('guards107','guards111').strip(),new_guard.strip())
        status=new[new.index('void Status111'):new.index('int Now111')]
        self.assertNotIn('login',status);self.assertNotIn('server',status)
        self.assertIn('FileIsExist(path,0)',new);self.assertIn('if(exists ||',new)

if __name__=='__main__':unittest.main()
