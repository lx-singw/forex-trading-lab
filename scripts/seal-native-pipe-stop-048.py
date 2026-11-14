"""Archive failed048 with additive offline checks; original native pins stay failed."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];OFFLINE=runpy.run_path(str(ROOT/'scripts/offline-native-pipe-stop-048.py'))
API=OFFLINE['API'];sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=OFFLINE['verify_offline']();r=sealed(ROOT/'reports/native-pipe-048-runtime.json')
    audit=sealed(ROOT/'reports/native-pipe-048-disabled-stop-records.json')
    checks=sealed(ROOT/'reports/native-pipe-048-stop-audit-checks.json')
    assert checks['checker_passed'] and checks['audit_sha256']==sha(ROOT/'reports/native-pipe-048-disabled-stop-records.json')
    assert checks['runtime_sha256']==sha(ROOT/'reports/native-pipe-048-runtime.json')
    assert r['completed'] is False and r['stop_reason']=='disconnected' and r['permissions_consumed']==0
    text=(f'# Native no-market fixture048 results — 2026-10-07\n\n'
        '682 software tests and5 Windows lifetime cases passed before the manual session. '
        'The exact compiled047 EX5 was exclusively deployed, with initial actual-demo/USD/Algo-off '
        'and private identity/process/instrument guards passing.\n\n'
        'The session stopped while checking guards for collect-disabled: disconnected, which also covers '
        'unavailable SDK terminal/account metadata.452.525s elapsed; one SDK attachment, one disabled arm, '
        'zero collected records, zero consumed permissions. The SDK was shut down. '
        'No enabled server/request/receipt or repeat run was armed. Native transport remains untested.\n\n'
        f'An additive existing-log audit found {len(audit["records"])} sanitized records; '
        f'disabled proof passed: {audit["disabled_proof_passed"]}. '
        'Its result is separate from the original empty runtime collection and never changes the failed outcome. '
        'No quote/history/order requests occurred.\n\n'
        'Post-stop original preflight and checker also failed: installed metaeditor64.exe and terminal64.exe '
        'changed from signed MetaQuotes6241 to signed6244.1452 other frozen inputs match. '
        'Both exact revisions are hash-accounted; no update was performed by this work. '
        'The change/disconnect cause and timing are unestablished. The user now reports a connected interface.\n\n'
        'The first additive audit stopped before reservation/log read; its three source files are archived. '
        'The revised offline audit checks every original input with exactly two recorded executable exceptions, '
        'executes neither changed executable, and makes no SDK connection. '
        'The original runtime and checker remain failed. Original048 reservations remain permanently reserved.\n\n'
        'Old047 stops,045 six captures and044 timeout are preserved. Same-logon cooperating pipe owner remains '
        'an assumption; MQL has no independent server-PID authentication. Clock/coverage/cost/flags and033/035 '
        'failures remain unresolved, consumed2025/reservedNov–Dec2026 and stopped providers unchanged. '
        'Fresh/annual eligibility and orders remain false.\n\n'
        'Next: docs/NATIVE-PIPE-049-PLAN.md, prepare/test/freeze fresh no-market readiness and a new dated phase '
        'against the observed signed6244 binaries. Not executed. Do not rerun048/047 or the old042 observer.\n')
    with (ROOT/'docs/NATIVE-PIPE-048-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: native fixture048 stopped and sealed; read NATIVE-PIPE-048-RESULTS.md. '
        '682 tests/5 Windows lifetime cases passed; initial demo/USD/Algo-off guards and exclusive deployment passed. '
        f'One disabled arm; SDK collect guard stopped disconnected; original collection empty, permissions0. '
        f'Additive disabled log proof {audit["disabled_proof_passed"]}/{len(audit["records"])} records, original outcome unchanged. '
        'No enabled/repeat transport test, quotes/history/orders. Both signed installed MT5 files changed6241→6244; '
        'original preflight/checker failures and audit-r1 stop preserved,1452 other inputs unchanged. Cause unknown; '
        'user reports connected now. No session reset/reconnect. Next NATIVE-PIPE-049-PLAN.md fresh readiness/new dated '
        'phase preparation, not executed. Old047 stops/045 six captures/044 timeout and market-data blockers retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    # These are archival old pins, accounted against current signed revisions only.
    for n in API['OLD']['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'docs/NATIVE-PIPE-049-PLAN.md','reports/native-pipe-048-*.json','reports/native-pipe-048-*.sha256','reports/native-pipe-048-*.zip'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    bindings.update(r['deployment']['artifact_binding'])
    observed={n:dict(frozen_sha256=before,observed_sha256=after) for n,(before,after) in OFFLINE['CHANGES'].items()}
    for n,h in bindings.items():
        if n in observed:assert h==observed[n]['frozen_sha256'] and sha(API['bound'](n))==observed[n]['observed_sha256']
        else:assert sha(API['bound'](n))==h,n
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
        installed_dependency_mismatches=observed,current_installed_digests={n:v['observed_sha256'] for n,v in observed.items()},
        historical_installed_bytes_available=False,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_accounted_for=len(external),
        unchanged_external_bindings_verified=len(external)-2,mismatched_external_bindings_accounted_for=2,
        runtime_completed=False,original_checker_passed=False,additive_evidence_checker_passed=True,
        disabled_proof_passed=audit['disabled_proof_passed'],native_mt5_transport_verified=False,
        next_plan='docs/NATIVE-PIPE-049-PLAN.md',next_plan_executed=False,
        quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,runtime_completed=False,disabled_proof_passed=audit['disabled_proof_passed'],
        bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
