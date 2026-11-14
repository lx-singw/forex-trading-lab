"""Seal offline diagnostic preparation; original native051 remains failed."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/transport-diagnostics-053.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=API['verify']();checks=sealed(ROOT/'reports/transport-diagnostics-053-checks.json')
    assert checks['checker_passed'] and checks['ledger_sha256']==sha(API['LEDGER'])
    assert checks['tests_sha256']==sha(ROOT/'reports/transport-diagnostics-053-r2-tests.json')
    text=('# Offline connection diagnostics053 — 2026-10-07\n\n'
        '774 tests passed (32 new) after correcting a diagnostic clock variable binding. '
        'The first full run failed26 tests; its source, ledger and failed result remain in the r1 snapshot. '
        'Revision2 was frozen separately and one full rerun passed. '
        'The new injected server records ten fixed connection/cleanup stages, '
        'strict reasons, bounded byte counts and timings. Unknown exceptions are redacted, private account '
        'metadata/raw messages never emitted. Tests cover peer/disconnection/read/decode/issue/encoding/write '
        'failures, one-use consumption despite failure, receipt/IO deadlines, clock reversal, closures, '
        'pending memory/handle retention and report privacy. The fake duplex consumes the complete reply.\n\n'
        '99 differential cases compare the actual new pure MQL diagnostic header with Python. '
        'Diagnostic code0 matches the unchanged Decode047 acceptance in every case. '
        'Reply length, magic/phase/policy/permission, range/date, boot-clock/restart, windows and UTC expiry '
        'can be distinguished in a future closed native record. Existing guards and2s limits remain. '
        'The C++ shim is a temporary Linux unit-test executable; no MetaEditor compilation/EX5/deployment.\n\n'
        'Original051 remains failed, one permission consumed, response unconfirmed, MT5 reason23. '
        '053 cannot recover the missing original exception or establish its root cause. '
        'The new layer is prepared offline and is not integrated into a deployed MT5 fixture. '
        'No SDK, terminal/native fixture, price/history/order calls, log reread, source051 edit or phase reuse.\n\n'
        'Next declare a fresh fixed-date native experiment using these diagnostics before compiling, '
        'deploying or manually running anything. Keep actual DEMO/USD/Algooff guards, one-use allowance, '
        '900s session,2s IO/receipt, explicit log saving and cancellation completion. '
        'No unbounded flush or weakened validation as a speculative fix. '
        'All earlier failed sessions, clock/cost/coverage/flags/033/035 gates, consumed2025, '
        'reservedNov–Dec2026/provider stops remain. Fresh/annual eligibility and orders false.\n')
    with (ROOT/'docs/NATIVE-TRANSPORT-053-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: offline transport diagnostics053 sealed; read NATIVE-TRANSPORT-053-RESULTS.md. '
        'Revision2:774 tests/32 new pass after diagnostic variable fix; first26-error result/source preserved. '
        '99 actual pure MQL/Python diagnostic cases agree with frozen047 acceptance. '
        'Ten fixed connection/cleanup stages, byte counts/timing, privacy and pending-handle retention tested '
        'with injected peers; no actual MT5 repair claimed.051 failure/one consumed permission/052 reason23 '
        'and all old evidence preserved. Zero SDK/native MT5/compiler/deployment/market/order calls. '
        'Next new fixed-date experiment requires fresh phase and tested diagnostic integration before use; '
        'no repeated051 run. Market blockers and reserved data remain; fresh/annual eligibility/orders false. '
        'Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/transport-diagnostics-053-*.json','reports/transport-diagnostics-053-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/transport-diagnostics-053-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        tests_passed=774,new_tests=32,differential_cases=99,root_cause_proven=False,actual_mt5_repair_verified=False,
        original051_runtime_completed=False,native_metatrader_compiler_invocations=0,terminal_deployments=0,
        sdk_connections=0,market_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
