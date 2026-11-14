from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from forex_demo_lab import metadata_probe_127 as probe

ROOT=Path(__file__).resolve().parents[1]
SECOND=int(datetime(2026,10,14,12,tzinfo=timezone.utc).timestamp())
def bits(value):return struct.pack('>d',float(value)).hex().upper()
def encode(payloads):
    chain=probe.ZERO;rows=[]
    for payload in payloads:
        chain=hashlib.sha256((chain+'\t'+payload+'\n').encode('ascii')).hexdigest().upper()
        rows.append(payload+'\t'+chain+'\r\n')
    return ''.join(rows).encode('ascii')
def fixture_payloads(kind='invented_fixture',sessions=1,failed=()):
    rows=[f'H\tFXDL127_V1\t{kind}\t2026.10.14\t{SECOND}\t1000'];seq=0
    def add(tag,key,values,ok=True,error=0):
        nonlocal seq
        seq+=1;bu=1000+seq*1000
        rows.append(f'A\t{seq}\t{tag}\t{key}')
        rows.append('\t'.join(map(str,[tag,seq,key,SECOND,SECOND,SECOND,bu,bu+10,bu+20,int(ok),error,*values])))
    def tick(key):
        add('T',key,[SECOND+10800,(SECOND+10800)*1000+123,bits(1.1),bits(1.1001),bits(0),0,1026,bits(0)])
    def clocks(key):add('C',key,[SECOND+10800,SECOND+10800,SECOND,SECOND+7200,-7200,0])
    clocks('clock_before');tick('tick_before')
    for key in probe.INTEGER_KEYS:add('I',key,[0 if key in failed else 30],key not in failed,4303 if key in failed else 0)
    for key in probe.DOUBLE_KEYS:add('D',key,[bits(0 if key in failed else -.5 if key.startswith('swap_') else .01)],key not in failed,4303 if key in failed else 0)
    for key in probe.STRING_KEYS:add('V',key,['NA' if key in failed else 'EUR'],key not in failed,4303 if key in failed else 0)
    for day in range(7):
        for index in range(min(9,sessions+1)):
            ok=index<sessions
            add('W',str(day)+':'+str(index),[0,86400 if ok else 0],ok)
    tick('tick_after');clocks('clock_after')
    rows.append(f'E\t{seq}\t{SECOND}\t{1000+seq*1000+30}')
    return rows


class Metadata127Tests(unittest.TestCase):
    def test_complete_fixture_and_all_admission_false(self):
        r=probe.inspect_bytes(encode(fixture_payloads()))
        self.assertEqual(r['capture_status'],'complete')
        self.assertEqual(r['queries_attempted'],len(r['rows']))
        for flag in ('source_utc_certified','receipt_utc_certified','market_data_qualified','paper_evaluation_available','orders_available','real_money_execution_available','producer_authenticated','weekly_template_is_historical_calendar'):
            self.assertIs(r[flag],False)
        self.assertIsNone(r['source_age']);self.assertIsNone(r['commission_terms']);self.assertIsNone(r['slippage_terms'])

    def test_market_declared_is_not_authenticated_or_admitted(self):
        r=probe.inspect_bytes(encode(fixture_payloads('market_declared')))
        self.assertEqual(r['declared_kind'],'market_declared')
        self.assertFalse(r['producer_authenticated']);self.assertFalse(r['market_data_qualified'])

    def test_raw_offset_not_source_age_and_unknown_flags_retained(self):
        r=probe.inspect_bytes(encode(fixture_payloads()))
        ticks=[x for x in r['rows'] if x['type']=='T']
        self.assertEqual(ticks[0]['raw_source_minus_nominal_receipt_ms'],10800123)
        self.assertEqual(ticks[0]['raw_flags'],1026)
        self.assertIsNone(ticks[0]['source_age'])
        self.assertEqual(ticks[0]['source_millis'],ticks[1]['source_millis'])

    def test_negative_swap_exact_bits_and_failed_property_not_zero(self):
        r=probe.inspect_bytes(encode(fixture_payloads(failed=('point','account_leverage','currency_margin'))))
        by={x['key']:x for x in r['rows']}
        self.assertEqual(by['swap_long']['value'],'-0.5')
        self.assertEqual(by['swap_long']['native_bits'],bits(-.5))
        for key in ('point','account_leverage','currency_margin'):
            self.assertFalse(by[key]['query_succeeded']);self.assertIsNone(by[key]['value'])

    def test_zero_or_missing_weekly_sessions_not_historical_closures(self):
        r=probe.inspect_bytes(encode(fixture_payloads(sessions=0)))
        weekly=[x for x in r['rows'] if x['type']=='W']
        self.assertEqual(len(weekly),7)
        self.assertTrue(all(not x['query_succeeded'] for x in weekly))
        self.assertFalse(r['weekly_template_is_historical_calendar'])

    def test_session_cap_explicitly_truncated(self):
        r=probe.inspect_bytes(encode(fixture_payloads(sessions=9)))
        self.assertTrue(r['weekly_template_truncated'])
        self.assertEqual(len([x for x in r['rows'] if x['type']=='W']),63)

    def test_every_stopped_prefix_keeps_pending_attempt_without_value(self):
        original=fixture_payloads()
        for i,line in enumerate(original):
            if line.startswith('A\t'):
                seq=int(line.split('\t')[1])
                r=probe.inspect_bytes(encode(original[:i+1]+[f'S\t9\t{seq}']))
                self.assertEqual(r['capture_status'],'stopped')
                self.assertTrue(r['pending_attempt']);self.assertEqual(r['queries_recorded'],seq-1)

    def test_partial_tail_and_missing_footer_stay_incomplete(self):
        payloads=fixture_payloads()
        for raw in (encode(payloads[:-1]),encode(payloads[:-1])+b'E\t',encode(payloads[:2])):
            r=probe.inspect_bytes(raw);self.assertEqual(r['capture_status'],'incomplete')
        self.assertTrue(probe.inspect_bytes(encode(payloads[:2]))['pending_attempt'])

    def test_premature_footer_and_data_after_terminal_reject(self):
        payloads=fixture_payloads()
        for p in (payloads[:1]+[f'E\t0\t{SECOND}\t1000'],payloads+[payloads[1]],payloads[:-1]+['S\t1\t0']):
            with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_forged_checksum_and_rehashed_sequence_reject(self):
        raw=encode(fixture_payloads())
        with self.assertRaisesRegex(ValueError,'probe_checksum'):probe.inspect_bytes(raw.replace(b'tick_before',b'tock_before',1))
        p=fixture_payloads();p[1]=p[1].replace('A\t1','A\t2')
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_reordered_properties_and_skipped_session_indices_reject(self):
        p=fixture_payloads();p[5],p[7]=p[7],p[5]
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads()
        i=next(i for i,x in enumerate(p) if x.startswith('A\t') and x.endswith('W\t0:0'))
        p[i]=p[i].replace('0:0','0:1')
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_nonfinite_bits_crossed_quotes_and_nondecimal_flags_reject(self):
        for old,new in ((bits(1.1),'7FF8000000000000'),(bits(1.1001),bits(.9)),('\t1026\t','\tTrue\t')):
            p=fixture_payloads();i=next(i for i,x in enumerate(p) if x.startswith('T\t'))
            p[i]=p[i].replace(old,new)
            with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_failed_nonzero_value_and_success_with_error_reject(self):
        p=fixture_payloads(failed=('point',))
        i=next(i for i,x in enumerate(p) if x.startswith('D\t') and '\tpoint\t' in x)
        p[i]=p[i][:-16]+bits(1)
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads();i=next(i for i,x in enumerate(p) if x.startswith('I\t'))
        f=p[i].split('\t');f[10]='4303';p[i]='\t'.join(f)
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_receipt_clock_reversal_jump_expiry_and_deadline_reject(self):
        for index,value in ((3,str(SECOND-1)),(5,str(SECOND+3)),(6,'999'),(8,'60001001')):
            p=fixture_payloads();f=p[2].split('\t');f[index]=value;p[2]='\t'.join(f)
            with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads();p[0]=p[0].replace('2026.10.14','2026.10.12')
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_short_outcomes_invalid_unicode_control_and_size_reject(self):
        p=fixture_payloads();p[2]='C'
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        for data in (b'',b'X'*(probe.MAX_BYTES+1),b'\xff',b'H\x7f'):
            with self.assertRaises(ValueError):probe.inspect_bytes(data)

    def test_missing_duplicate_frames_and_wrong_kind_reject(self):
        p=fixture_payloads();p.pop(2)
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads();p.insert(3,p[2])
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads();p[0]=p[0].replace('invented_fixture','qualified')
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_currency_injection_and_extra_tick_fields_reject(self):
        p=fixture_payloads();i=next(i for i,x in enumerate(p) if x.startswith('V\t'));p[i]=p[i].removesuffix('EUR')+'private_identifier'
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))
        p=fixture_payloads();i=next(i for i,x in enumerate(p) if x.startswith('T\t'));p[i]+='\t123'
        with self.assertRaises(ValueError):probe.inspect_bytes(encode(p))

    def test_config_and_native_query_names_match_and_no_order_history_api(self):
        spec=json.loads((ROOT/'config/metadata-probe-127.json').read_bytes())
        self.assertEqual(spec['integer_keys'],list(probe.INTEGER_KEYS));self.assertEqual(spec['double_keys'],list(probe.DOUBLE_KEYS));self.assertEqual(spec['string_keys'],list(probe.STRING_KEYS))
        source=(ROOT/'mt5/Scripts/ForexDemoMetadataProbe127.mq5').read_text()
        self.assertIn('input bool CollectEvidence = false;',source)
        self.assertNotIn('ClockReason107(',source)
        for token in ('OrderSend(', 'OrderCheck(', 'SymbolSelect(', 'WebRequest(', 'CopyTicks', 'CopyRates', '#import', 'FILE_COMMON'):
            self.assertNotIn(token,source)
        for key in (*probe.INTEGER_KEYS,*probe.DOUBLE_KEYS,*probe.STRING_KEYS):self.assertIn('"'+key+'"',source)

    def test_cli_closed_file_read_only_and_generic_rejection(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'Metadata127.txt';path.write_bytes(encode(fixture_payloads()));before=path.read_bytes()
            args=[sys.executable,str(ROOT/'scripts/metadata-probe-127.py'),str(path)]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            self.assertFalse(json.loads(result.stdout)['orders_available']);self.assertEqual(path.read_bytes(),before)
            path.write_bytes(b'invalid');result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['reason'],'invalid_or_unreadable_metadata_export')


if __name__=='__main__':unittest.main()
