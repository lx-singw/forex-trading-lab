"""Seal separate051 failure evidence, never repair or resume original054."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-log-055.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=sealed(API['LEDGER']);audit=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/native-log-055-checks.json')
    assert checks['checker_passed'] and checks['audit_sha256']==sha(API['OUTPUT'])
    for n,h in ledger['bindings'].items():assert sha(API['bound'](n))==h,n
    codes=[row['reason_code'] for row in audit['records']]
    text=(f'# Separate051 failure record audit055 — 2026-10-07\n\n'
        f'Audit passed: {audit["audit_passed"]}; native reason codes: {codes}. '
        f'Exactly {audit["content_reads"]} read(s), {audit["read_bytes"]} bytes in frozen range [1520,1950). '
        'Sanitized closed records only; no raw log or account identifier exported.\n\n'
        'Original054 remains failed: native_transport_rejected. Actual MT5 peer and 56-byte request '
        'passed, one permission consumed, Windows rejected the84-byte reply write immediately, response_written=false, pipe and SDK closed and cancellation drained. '
        'Its original stopped read was zero bytes/records; this later audit is separate evidence and cannot '
        'make the original collection successful. Disabled proof passed; no repeat was armed. No phase reset/refund/rerun.\n\n'
        'Reason22 in the frozen native source means FileSeek failed after request flush; reason23 means '
        'the received frame failed validation. Other codes retain their exact source meanings. '
        'The new helper identifies reply_write/io_operation_rejected in94 microseconds. '
        'This is an immediate Win32 operation rejection, not a2s IO timeout. Raw Windows/MQL read error '
        'codes were not recorded, so exact cause remains unknown. Attempted84 bytes are not delivered84 bytes.\n\n'
        '800 software tests, five Windows lifetime cases and one clean native compilation remain preparation '
        'evidence. No new SDK, permission, native run, compiler, quote/history/order or strategy call in055. '
        'Next review the observed native branch and add bounded fixed-reason transport diagnostics and '
        'offline reproduction tests before declaring another native phase. Frozen051 stays untouched. '
        'All earlier failed sessions, raw clock/cost/coverage/flags/033/035 gates, consumed2025, '
        'reservedNov–Dec2026 and provider stops remain; fresh/annual eligibility and orders false.\n')
    with (ROOT/'docs/NATIVE-LOG-055-RESULTS.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: separate native054 failure audit055 sealed; read NATIVE-LOG-055-RESULTS.md. '
        f'Audit {audit["audit_passed"]}, native reasons {codes}, one bounded existing-log range[1520,1950). '
        'Original054 failed native_transport_rejected: MT5 peer/request valid,1 consumed permission, '
        'immediate reply-write failure, closed SDK/pipe, original stopped read empty. Repeat unarmed; no reset/refund/retry. '
        'No new SDK/native/permission/price/order calls in055. Next offline branch diagnosis and fixed-reason '
        'diagnostics/tests before any new declared phase. Old failures and market gates preserved; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['API']['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-log-055-*.json','reports/native-log-055-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-log-055-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        audit_passed=audit['audit_passed'],native_reason_codes=codes,original054_runtime_completed=False,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,audit_passed=audit['audit_passed'],native_reason_codes=codes,
        bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
