"""Seal048 outcome without editing any original runtime or047 evidence."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-048.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def finalize():
    ledger=API['verify']();r=sealed(ROOT/'reports/native-pipe-048-runtime.json')
    checks=sealed(ROOT/'reports/native-pipe-048-checks.json');assert checks['checker_passed']
    assert checks['runtime_sha256']==sha(ROOT/'reports/native-pipe-048-runtime.json')
    text=(f'# Native no-market fixture048 results — 2026-10-07\n\n'
        f'682 software tests and5 Windows lifetime cases pass. Exact047 EX5 reused; no new compilation. '
        f'Native session completed: {r["completed"]}. Stop reason: {r["stop_reason"]}. '
        f'SDK attachments: {r["native_connections_attempted"]}; script arms: {len(r["script_arms"])}; '
        f'permissions consumed: {r["permissions_consumed"]}.\n\n'
        'Original filtered native records are retained in reports/native-pipe-048-*-records.json. '
        'All authorized code has no quote/history/order capability. SDK quote reads and native quote/order counters are zero. '
        'Successful fixture evidence, if present, tests the actual MT5 peer and native pipe framing only. '
        'No absolute/historical clock certification, profitable strategy or market-data qualification follows.\n\n'
        'The pipe uses a cooperating same-logon owner. MQL does not independently authenticate the server PID; '
        'do not claim protection against a malicious same-logon owner. First-instance/local-only/DACL restrictions '
        'are configured, not externally penetration-tested. One exclusive phase/journal is never reset or refunded.\n\n'
        'Old047 revisions/stops,045 six quote captures and044 timeout remain intact. '
        'Clock/coverage/cost/flags and033/035 diagnostic failures remain unresolved. '
        'Consumed2025/reservedNov–Dec2026 and stopped providers remain unchanged. '
        'Fresh/annual eligibility and order availability remain false. '
        'Any later price capture requires a separately dated frozen plan and quote-budget enforcement; '
        'this phase does not authorize it.\n')
    result=ROOT/'docs/NATIVE-PIPE-048-RESULTS.md'
    with result.open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: no-market fixture048 sealed; read NATIVE-PIPE-048-RESULTS.md. '
        f'682 tests/5 Windows lifetime cases pass; native MT5 fixture completed {r["completed"]}, stop {r["stop_reason"]}; '
        f'{len(r["script_arms"])} arms/{r["permissions_consumed"]} permissions, zero quotes/history/orders. '
        '900s manual wait/2s IO, cancellation and exclusive phase preserved. Cooperating pipe owner assumption remains; '
        'MQL independent server-PID authentication unavailable. Old047 stops/045 six captures/044 timeout preserved. '
        'No market/clock/strategy qualification or price-capture activation; fresh/annual eligibility/orders false. '
        'Next separately dated price-budget plan only if native fixture passes; otherwise diagnose preserved failure without rerun. '
        'Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['OLD']['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-pipe-048-*.json','reports/native-pipe-048-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    if r['deployment']:bindings.update(r['deployment']['artifact_binding'])
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-pipe-048-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        completed=r['completed'],quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,completed=r['completed'],bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':finalize()
