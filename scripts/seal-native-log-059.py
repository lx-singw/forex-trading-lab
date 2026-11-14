"""Seal separate059 record; original058 trial remains failed."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-059.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']
def seal():
    l=sealed(API['LEDGER']);r=sealed(API['OUTPUT']);c=sealed(ROOT/'reports/native-log-059-checks.json')
    assert c['checker_passed'] and c['audit_sha256']==sha(API['OUTPUT'])
    for n,h in l['bindings'].items():assert sha(API['bound'](n))==h,n
    row=r['records'][0]
    text=(f'# Separate057 native read audit059 — 2026-10-07\n\n'
        f'Audit passed; exactlyone frozen [2508,3066) read,558 bytes. Native sanitized record: '
        f'reason{row["reason_code"]}, requests{row["requests"]}, reply_bytes{row["reply_bytes"]}, '
        f'decode_reason{row["decode_reason"]}, read_error_category{row["read_error_category"]}, '
        f'read_elapsed_us{row["read_elapsed_us"]}, read_timing{row["read_timing"]}. '
        'No raw log/account identifiers exported.\n\n'
        'Original058 trial remains failed: one permission consumed, disabled primary passed, '
        'enabled primary/stopped collection empty, repeat unarmed, SDK/pipe closed, cancellation drained. '
        'Windows reply-write submit category was pipe_closing; attempted84 bytes, completed bytes unknown, '
        'no successful write. Its adapter failed in107us, whole diagnostic write stage192us. '
        'This is an immediate rejection, not its2s pending IO deadline. '
        'The late saved native record cannot repair that original collection.\n\n'
        'Frozen native source closes its pipe after FileReadArray returns, before post-read guards/decoder. '
        'Read category5 means general MQL file-read error;0 means no recorded MQL error;6/7 remain '
        'other/unknown. Decoder1 means wrong length, checked before receipt expiry. '
        'These measurements narrow the read/connection-lifetime branch, but do not prove why the native '
        'read returned that count or establish a repair. Helper pre-write work after connection took '
        '2788977us; receipt starts after final issue guards. Do not label the failure expired receipt.\n\n'
        'Zero new SDK/native/permission/compiler/deployment/quote/history/order/strategy calls in059. '
        '874 preparation tests and signed6244 clean compilation remain software/build evidence. '
        'Do not rerun057. Next offline native read-primitive/lifecycle design and injected delayed/partial/extra '
        'frame tests before any fresh trial. No unbounded flush, weaker guards, mutable hash cache, '
        '84-byte count change without suffix proof or deployment of modeled ACK. '
        'All earlier failures/market gates/consumed2025/reservedNov–Dec2026/provider stops remain; '
        'fresh/annual eligibility and orders false.\n')
    with (ROOT/'docs/NATIVE-LOG-059-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: separate native057 read audit059 sealed; read NATIVE-LOG-059-RESULTS.md. '
        f'558-byte single frozen log range; native reply{row["reply_bytes"]}/decode{row["decode_reason"]}/'
        f'read error category{row["read_error_category"]}/duration{row["read_elapsed_us"]}us. '
        'Original058 failed: immediate Windows pipe_closing on reply write,1 consumed permission, '
        'disabled proof passed, repeat unarmed, SDK/pipe closed. Late record cannot repair original empty collection. '
        'Zero new SDK/native/quote/order calls. Next060 offline read/lifecycle investigation, not executed. '
        'All old failures/market gates/reserved data retained; fresh/annual eligibility/orders false. '
        'Earlier entries are historical.\n\n')
    b=dict(l['bindings'])
    for n in API['API']['HANDOFF']:
        p=ROOT/n;s=p.read_text();i=s.index('\n')+1;p.write_text(s[:i]+'\n'+handoff+s[i:]);b[n]=sha(p)
    for pattern in ('scripts/*059.py','docs/*059*.md','reports/native-log-059-*.json','reports/native-log-059-*.sha256','docs/NATIVE-TRANSPORT-060-PLAN.md'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in b.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external}
    final=ROOT/'reports/native-log-059-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(final.with_suffix('.zip')) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        external_bindings_verified=len(external),native_record=row,original_runtime_completed=False,
        root_cause_proven=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))
if __name__=='__main__':seal()
