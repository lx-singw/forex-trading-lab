"""Freeze reviewed057 preparation and handoff before any SDK attachment."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-057.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=API['verify']();checks=sealed(ROOT/'reports/native-pipe-057-preparation-checks.json')
    assert checks['checker_passed'] and checks['ledger_sha256']==sha(API['LEDGER'])
    text=('# Diagnostic fixture057 preparation — 2026-10-07\n\n'
        '874 tests (32 new),87 shared native decoder frames and6 Windows synthetic lifetime cases pass. '
        'The new fixed-date fixture compiled once with the reviewed signed6244 editor:0 errors/warnings. '
        'It retains the85-byte read and records bounded native read error/timing before cleanup. '
        'Read errors/invalid timing prevent a successful result even if wire decoding passes.\n\n'
        'The new companion preserves guards/identity hashing and records Windows connect/read/write '
        'categories, attempted/completed bytes, failed event cleanup and retained pending operations. '
        'Synthetic delayed guards, disconnection/error/schema/privacy/deadline/cancellation cases pass. '
        'Old054/051 failures and one consumed permission each remain. No actual error/root cause or '
        'successful MT5 transport is established by these preparation tests.\n\n'
        'Zero SDK connections, deployments, native script launches, permissions, market/history/order '
        'calls or terminal-log content reads. The runtime source is gated by a separate authorization '
        'that has not been created. No terminal settings or unrelated files changed.\n\n'
        'Next NATIVE-PIPE-058-PLAN.md: freeze a separately authorized057 runtime trial after full '
        'preparation closure review and current readiness. Keep Algo Trading off and do not run old '
        'fixtures. The native read call has no caller timeout; its duration is measured, not guaranteed. '
        'Helper deadlines cannot preempt a blocking native script. The84-byte candidate and modeled '
        'ACK remain unused; successful helper write alone is not proof of peer consumption.\n\n'
        'All clock/cost/coverage/flags/033/035 gates, consumed2025, reservedNov–Dec2026/provider stops '
        'remain. Fresh/annual eligibility and orders false. See NATIVE-PIPE-057-PROTOCOL.md.\n')
    with (ROOT/'docs/NATIVE-PIPE-057-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: diagnostic057 preparation sealed; read NATIVE-PIPE-057-RESULTS.md. '
        '874 tests/32 new/87 shared decoder frames/6 Windows lifetime cases pass; one signed6244 '
        'compile0 errors/warnings. Original85-byte read plus immediate native error/timing; Windows '
        'IO categories/pending retention/event cleanup integrated. Actual MT5 repair/root cause unknown. '
        'SDK/deployment/native runs/permissions/market/orders0; separate runtime authorization absent. '
        'Next058 bounded057 runtime plan, not executed; native read timeout limitation remains. '
        'Old failures/market blockers/reserved data retained; fresh/annual eligibility/orders false. '
        'Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-pipe-057-*.json','reports/native-pipe-057-*.sha256','reports/native-pipe-057-initial-source.zip','docs/NATIVE-PIPE-058-PLAN.md'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    bindings.update(checks['output_bindings'])
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-pipe-057-preparation-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        tests_passed=874,native_lifetime_cases=6,wire_differential_frames=87,fixture_compiled=True,
        native_disabled_proof_required=True,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
