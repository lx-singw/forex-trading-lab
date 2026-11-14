"""Freeze reviewed054 preparation and handoff before any SDK attachment."""
import hashlib
import json
from pathlib import Path
import runpy
import zipfile
ROOT=Path(__file__).resolve().parents[1];API=runpy.run_path(str(ROOT/'scripts/native-pipe-054.py'))
sha,sealed,write=API['sha'],API['sealed'],API['write']

def seal():
    ledger=API['verify']();checks=sealed(ROOT/'reports/native-pipe-054-preparation-checks.json')
    assert checks['checker_passed'] and checks['ledger_sha256']==sha(API['LEDGER'])
    text=('# Native fixture054 preparation — 2026-10-07\n\n'
        '800 tests (26 new) passed, including private metadata/process changes, disconnection, strict manual budgets, '
        'and one offline stopped-log collection without reconnecting.87 exact shared MQL wire decoder frames agree '
        'for the new054 phase.5 Windows lifetime cases pass; pending cancellation drained, IO limited to2s.\n\n'
        'The new fixed-Oct7 no-market fixture compiled with signed build6244: one compiler invocation, '
        'zero errors/warnings. It has a separate phase/pipe/reservation, default ExerciseTransport=false, '
        'and no quote/history/order/DLL functions. No SDK attachment, terminal deployment or manual run occurred '
        'during preparation. Actual MT5 framing/peer/repeated-run rejection remains untested.\n\n'
        'The new diagnostic integration requires a fresh native disabled proof before enabling. '
        'All old failures, including051/052 and053 R1, and reserved phases remain preserved. '
        'No software install/update, login, terminal launch or setting change was made.\n\n'
        'Next execute the frozen054 companion on the existing connected demo with Algo Trading off, guided '
        'disabled→enabled→repeat, at most3 launches/1 grant/900s session/2s IO and receipts. '
        'Save old logs before arming and save each completed run through Experts context-menu Open; '
        'explicit acknowledgment is required before collection. '
        'A disconnect closes the SDK/pipe and preserves one bounded sanitized pending record without retry. '
        'Same-logon cooperating-owner assumption remains; no independent MQL server PID authentication.\n\n'
        'All earlier market-data/clock/cost/flags/033/035 failures, consumed2025/reservedNov–Dec2026/provider '
        'stops remain. Fresh/annual eligibility and order availability are false; no price capture or returns.\n')
    with (ROOT/'docs/NATIVE-PIPE-054-RESULTS.md').open('x') as f:f.write(text)
    handoff=('Latest — 2026-10-07: fixture054 preparation sealed; read NATIVE-PIPE-054-RESULTS.md. '
        '800 tests/26 new/87 shared MQL frames and5 Windows lifetime cases pass. Separate fixed-Oct7 phase '
        'compiled with signed6244: one compiler,0 errors/warnings. Stopped-log preservation added without SDK retry; '
        'actual MT5 transport remains untested, SDK/deployments/quotes/orders0 during preparation. '
        'Next frozen guided054 runtime: existing demo/USD/Algooff, max3 manual launches/1 grant/900s/2s IO, '
        'baseline and all three post-run log-saving acknowledgments required. New native disabled proof required. '
        '048 reserved phase/failures/disabled audit and all earlier stops/blockers preserved; '
        'fresh/annual eligibility/orders false. Earlier entries are historical.\n\n')
    bindings=dict(ledger['bindings'])
    for n in API['HANDOFF']:
        p=ROOT/n;old=p.read_text();i=old.index('\n')+1;p.write_text(old[:i]+'\n'+handoff+old[i:]);bindings[n]=sha(p)
    for pattern in (*API['PATTERNS'],'reports/native-pipe-054-*.json','reports/native-pipe-054-*.sha256'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    bindings.update(checks['output_bindings'])
    for n,h in bindings.items():assert sha(API['bound'](n))==h,n
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    final=ROOT/'reports/native-pipe-054-preparation-final-source.json';archive=final.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(internal) and len(z.infolist())==len(internal)
        for n,h in internal.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(final,dict(source_and_evidence_bindings=bindings,archive_external_bindings=external,
        archive_sha256=sha(archive),archive_members_verified=len(internal),external_bindings_verified=len(external),
        tests_passed=800,native_lifetime_cases=5,wire_differential_frames=87,fixture_compiled=True,
        native_disabled_proof_required=True,
        native_mt5_transport_verified=False,sdk_connections=0,quote_reads=0,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(sealed=True,bindings=len(bindings),members=len(internal),sha256=sha(final))))

if __name__=='__main__':seal()
