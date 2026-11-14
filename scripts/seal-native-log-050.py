"""Seal separate delayed-record evidence; preserve049 runtime failure."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-log-050.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=sealed(API['LEDGER']);audit=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/native-log-050-checks.json')
    assert checks['checker_passed'] and checks['audit_sha256']==sha(API['OUTPUT'])
    for n,h in ledger['bindings'].items():assert sha(API['bound'](n))==h,n
    text=(f'# Delayed native log050 evidence — 2026-10-07\n\n'
        f'Separate disabled049 proof passed: {audit["disabled_proof_passed"]}; '
        f'{len(audit["records"])} sanitized native record(s) in exactly{audit["read_bytes"]} bytes. '
        'One frozen read of existing range[364,726); no SDK connection, script rerun, permission, quote/history/order calls.\n\n'
        'Original049 runtime remains failed: exactly_one_fixture_record_required, zero appended bytes/records '
        'at its original collection, one disabled arm, zero grants, SDK shut down. The later metadata observation '
        'found726 bytes and the separate050 audit examined only those362 bytes. The user confirmed the exact049 '
        'script and OK. This is later evidence, not a successful original collection or a resumed session.\n\n'
        'If the expected record is present, the script ran while the result was unavailable to the earlier file '
        'collection. Delayed logging/file visibility is inferred; exact automatic buffering/flush timing is unknown. '
        'MT5 help documents that Experts context-menu Open saves current journal entries to disk: '
        'https://www.metatrader5.com/en/terminal/help/start_advanced/journal. '
        'Future guided tests must explicitly save the log before collection. '
        'No claim of a specific automatic flush interval or historical clock correction.\n\n'
        '718 tests/5 Windows fixtures/one clean049 compilation remain preparation evidence; '
        'actual MT5 permission/framing and repeat rejection remain untested. '
        '049/048 reserved phases and original failures,048 additive audit,047 stops/045 captures/044 timeout preserved. '
        'All market-data/clock/cost/flags/033/035 blockers and consumed2025/reservedNov–Dec2026/provider stops remain; '
        'fresh/annual eligibility/orders false.\n\n'
        'Next NATIVE-PIPE-051-PLAN.md: fresh no-market phase, exact shared-default-off derivation if proof valid, '
        'then at most two enabled/repeat launches with explicit Experts Open log-saving steps. Not executed.\n')
    with (ROOT/'docs/NATIVE-LOG-050-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: separate delayed-log audit050 sealed; read NATIVE-LOG-050-RESULTS.md. '
        f'Disabled049 proof {audit["disabled_proof_passed"]}, {len(audit["records"])} sanitized records/{audit["read_bytes"]} bytes '
        'in one frozen existing-log read. Original049 missing-record/zero-byte/empty collection and closed SDK remain failed; '
        'no phase reset/rerun/grant/SDK/quotes/orders. File grew after original read; logging/visibility delay inferred, '
        'exact timing unknown. Official MT5 Experts Open saves current entries; add this before future collections. '
        'Next NATIVE-PIPE-051-PLAN.md fresh no-market phase/shared-default-off proof and at most2 enabled/repeat launches '
        'with explicit log saving, not executed. All old failures/reservations and market-data blockers retained; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['API']['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'docs/NATIVE-PIPE-051-PLAN.md','reports/native-log-050-*.json','reports/native-log-050-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-log-050-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        disabled049_proof_passed=audit['disabled_proof_passed'],original049_runtime_completed=False,
        native_mt5_transport_verified=False,next_plan='docs/NATIVE-PIPE-051-PLAN.md',next_plan_executed=False,
        sdk_connections=0,quote_reads=0,orders_available=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,disabled049_proof_passed=audit['disabled_proof_passed'],
        bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
