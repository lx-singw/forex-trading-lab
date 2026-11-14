"""Seal complete or failed native051 outcome without resetting its phase."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-051.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=API['verify']();r=sealed(ROOT/'reports/native-pipe-051-runtime.json')
    checks=sealed(ROOT/'reports/native-pipe-051-runtime-checks.json')
    assert checks['checker_passed'] and checks['runtime_sha256']==sha(ROOT/'reports/native-pipe-051-runtime.json')
    text=(f'# Native fixture051 outcome — 2026-10-07\n\n'
        f'Completed: {r["completed"]}; stop: {r["stop_reason"]}. '
        f'One bounded existing-terminal session: {r["native_connections_attempted"]} SDK attachment(s), '
        f'{len(r["script_arms"])} manual arms, {r["permissions_consumed"]} permissions consumed. '
        f'Original native records: {checks["native_records"]}; separately preserved stopped records: {checks["stopped_records"]}. '
        'No quote/history/order/strategy calls.\n\n'
        '742 software tests/24 new/87 shared decoder frames/5 Windows lifetime cases and one compiler with0 errors/warnings '
        'passed before SDK attachment. Actual MT5 transport is verified only if both strict native outcomes passed. '
        'Shared049 default-off proof is separately linked through050; no051 disabled run is claimed. '
        'One new phase is permanently reserved and never reset/refunded. '
        'Cooperating same-logon pipe owner remains an assumption; no independent MQL server PID authentication.\n\n'
        '048 original disconnect/checker failures, its reserved phase and additive disabled proof remain intact. '
        'All earlier047 stops/045 six captures/044 timeout and clock/coverage/cost/flags/033/035 failures remain. '
        'Consumed2025/reservedNov–Dec2026/provider stops are unchanged; fresh/annual eligibility/orders false. '
        'A further fixed-date quote-budget plan requires successful fixture evidence; no price activation follows here.\n')
    with (ROOT/'docs/NATIVE-PIPE-051-OUTCOME.md').open('x') as f:f.write(text)
    handoff=(f'Latest — 2026-10-07: native fixture051 outcome sealed; read NATIVE-PIPE-051-OUTCOME.md. '
        f'Completed {r["completed"]}, stop {r["stop_reason"]}; {len(r["script_arms"])} arms/{r["permissions_consumed"]} permissions, '
        f'{checks["native_records"]} primary/{checks["stopped_records"]} separate stopped records; zero quotes/history/orders. '
        'Preparation742 tests/24 new/87 shared MQL frames/5 Windows cases/one clean compiler retained. '
        'Actual MT5 framing/peer proof only if native completion passes; same-logon owner assumption remains. '
        'No phase reset, reconnect or price activation. All old stops/market blockers and reserved-data exclusions retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    prep=ROOT/'reports/native-pipe-051-preparation-final-source.json';bindings=dict(sealed(prep)['source_and_evidence_bindings'])
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-pipe-051-*.json','reports/native-pipe-051-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    bindings['reports/native-pipe-051-preparation-final-source.zip']=sha(prep.with_suffix('.zip'))
    if r['deployment']:bindings.update(r['deployment']['artifact_binding'])
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-pipe-051-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        runtime_completed=r['completed'],native_mt5_transport_verified=r['completed'],quote_reads=0,
        orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,runtime_completed=r['completed'],bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
