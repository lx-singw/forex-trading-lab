"""Freeze reviewed051 preparation and handoff before any SDK attachment."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-051.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=API['verify']();checks=sealed(ROOT/'reports/native-pipe-051-preparation-checks.json')
    assert checks['checker_passed'] and checks['ledger_sha256']==sha(API['LEDGER'])
    text=('# Native fixture051 preparation — 2026-10-07\n\n'
        '742 tests (24 new) passed, including private metadata/process changes, disconnection, strict manual budgets, '
        'and one offline stopped-log collection without reconnecting.87 exact shared MQL wire decoder frames agree '
        'for the new051 phase.5 Windows lifetime cases pass; pending cancellation drained, IO limited to2s.\n\n'
        'The new fixed-Oct7 no-market fixture compiled with signed build6244: one compiler invocation, '
        'zero errors/warnings. It has a separate phase/pipe/reservation, default ExerciseTransport=false, '
        'and no quote/history/order/DLL functions. No SDK attachment, terminal deployment or manual run occurred '
        'during preparation. Actual MT5 framing/peer/repeated-run rejection remains untested.\n\n'
        'The051 default-off branch is exactly the previously observed049 branch apart from declared labels/phase; '
        'its proof is050\'s separate native049 record. No051 disabled run or record is fabricated. '
        'All048/049 original failures and reserved phases are preserved. '
        'No software install/update, login, terminal launch or setting change was made.\n\n'
        'Next execute the frozen051 companion on the existing connected demo with Algo Trading off, guided '
        'enabled→repeat, at most2 launches/1 grant/900s session/2s IO and receipts. '
        'Save old logs before arming and save each completed run through Experts context-menu Open; '
        'explicit acknowledgment is required before collection. '
        'A disconnect closes the SDK/pipe and preserves one bounded sanitized pending record without retry. '
        'Same-logon cooperating-owner assumption remains; no independent MQL server PID authentication.\n\n'
        'All earlier market-data/clock/cost/flags/033/035 failures, consumed2025/reservedNov–Dec2026/provider '
        'stops remain. Fresh/annual eligibility and order availability are false; no price capture or returns.\n')
    with (ROOT/'docs/NATIVE-PIPE-051-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: fixture051 preparation sealed; read NATIVE-PIPE-051-RESULTS.md. '
        '742 tests/24 new/87 shared MQL frames and5 Windows lifetime cases pass. Separate fixed-Oct7 phase '
        'compiled with signed6244: one compiler,0 errors/warnings. Stopped-log preservation added without SDK retry; '
        'actual MT5 transport remains untested, SDK/deployments/quotes/orders0 during preparation. '
        'Next frozen guided051 runtime: existing demo/USD/Algooff, max2 manual launches/1 grant/900s/2s IO, '
        'baseline and post-run log-saving acknowledgments required. Shared049 disabled proof linked via050; '
        'no051 disabled run claimed. '
        '048 reserved phase/failures/disabled audit and all earlier stops/blockers preserved; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-pipe-051-*.json','reports/native-pipe-051-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    bindings.update(checks['output_bindings'])
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-pipe-051-preparation-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        tests_passed=742,native_lifetime_cases=5,wire_differential_frames=87,fixture_compiled=True,
        shared_disabled_proof_phase='049',shared_disabled_source_derivation_passed=True,native051_disabled_run_executed=False,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
