"""Offline original-byte diagnosis, corrected reader tests/models and closure."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PureWindowsPath
import runpy
import sys
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/native-timing-079.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE=API['HANDOFF'],API['ARCHIVE']
PREFIX='public-preflight-080';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/native-timing-079-final-source.json'
REVIEW=ROOT/'reports/native-timing-079-completion-review.json'
DESIGN=ROOT/'docs/PUBLIC-PREFLIGHT-080-DESIGN.md'
PLAN=ROOT/'docs/NATIVE-TIMING-081-PLAN.md'
EXPECTED=28
OWN=('scripts/public-preflight-080.py','src/forex_demo_lab/public_preflight_080.py',
    'src/forex_demo_lab/public_model_080.py','tests/test_public_preflight_080.py',
    'docs/PUBLIC-PREFLIGHT-080-DESIGN.md','docs/NATIVE-TIMING-081-PLAN.md')
ZERO=dict(native_invocations=0,sdk_connections=0,mt5_runtime_invocations=0,
    native_metatrader_compiler_invocations=0,terminal_deployments=0,
    terminal_log_content_reads=0,market_reads=0,orders=0,receipt_permissions=0)
FALSE=dict(native_timing_verified=False,native_launch_ready=False,
    native_mql_verified=False,native_publication_verified=False,
    fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
    latency_guaranteed=False,original079_first_failure_proven=False,old070_cause_proven=False)


def pair_unique(pairs):
    result={}
    for key,value in pairs:
        assert key not in result
        result[key]=value
    return result


def inventory():
    # Original bytes + independent grammar/arithmetic; do not call a loader.
    labels=('ledger','checks','final','review','helper_profile','authorization')
    names=('reports/native-timing-078-ledger.json','reports/native-timing-078-checks.json',
        'reports/native-timing-078-final-source.json','reports/native-timing-078-completion-review.json',
        'reports/helper-profile-068.json','reports/native-timing-078-authorization.json')
    winroot=PureWindowsPath('//wsl.localhost/Ubuntu/home/lx_singw/projects/forex-demo-lab')
    rows=[]
    for label,n in zip(labels,names):
        path=ROOT/n;raw=path.read_bytes();side=path.with_suffix('.sha256').read_bytes()
        value=json.loads(raw.decode('ascii'),object_pairs_hook=pair_unique)
        assert type(value) is dict
        digest=hashlib.sha256(raw).hexdigest().encode('ascii')
        lf=side==digest+b'\n';crlf=side==digest+b'\r\n'
        assert lf or crlf
        parents=len((winroot/n).parents)
        rows.append(dict(label=label,content_bytes=len(raw),sidecar_bytes=len(side),
            content_sha256=sha(path),sidecar_sha256=sha(path.with_suffix('.sha256')),
            newline='lf' if lf else 'crlf',exact_digest_matches=True,
            json_ascii_unique_keys=True,windows_parents=parents,
            modeled_pair_stats=2*(parents+4),legacy_cap_accepts=len(side)<=65,
            corrected_cap_accepts=len(side)<=66))
    l=sealed(ROOT/'reports/native-timing-078-ledger.json');p=l['helper_chain']
    sources=l['runtime_sources'];launcher=p['launcher'];image=p['images'][0]
    assert len(sources)==29 and len(set(sources))==29
    assert all(sha(ROOT/n)==l['runtime_bindings'][n] for n in sources)
    assert sha(bound(launcher))==l['runtime_bindings'][launcher]
    assert sha(bound(image))==l['runtime_bindings'][image]
    launcher_win=PureWindowsPath('C:/')/launcher[7:]
    image_win=PureWindowsPath('C:/')/image[7:]
    source_bytes=sum((ROOT/n).stat().st_size for n in sources)
    source_stats=sum(len((winroot/n).parents)+4 for n in sources)
    return dict(rows=rows,public_reads=2*len(rows),
        public_bytes=sum(r['content_bytes']+r['sidecar_bytes'] for r in rows),
        public_stats=sum(r['modeled_pair_stats'] for r in rows),
        source_files=len(sources),source_reads=len(sources)+1,
        source_bytes_with_launcher=source_bytes+bound(launcher).stat().st_size,
        source_stats_with_launcher=source_stats+len(launcher_win.parents)+4,
        source_bytes_with_helper_image=source_bytes+bound(image).stat().st_size,
        source_stats_with_helper_image=source_stats+len(image_win.parents)+4,
        launcher_digest_differs_from_helper_image=sha(bound(launcher))!=sha(bound(image)),
        modeled_non_reparse_metadata=True,windows_metadata_measured=False,
        actual_sys_executable_measured=False,**ZERO,**FALSE)


def freeze():
    API['verify']();p=sealed(PRIOR);review=sealed(REVIEW)
    assert sha(PRIOR)=='049f811f009b3a6a100c6fd42adc77287e982f98b9a77d37239db7e4295a927f'
    assert review['review_passed'] and review['frozen_input_coverage_complete']
    assert review['final_source_sha256']==sha(PRIOR)
    assert (review['bindings_verified'],review['archive_members_verified'])==(2477,2287)
    assert review['new_audit_tests_passed']==24 and review['tests_retained']==1492
    assert not review['next_plan_executed'] and review['next_plan_sha256']==sha(ROOT/'docs/NATIVE-TIMING-080-PLAN.md')
    assert ARCHIVE(PRIOR,p)==2287
    b=dict(p['source_and_evidence_bindings'])
    for n,h in b.items():assert sha(bound(n))==h,n
    for n in HANDOFF:b.pop(n)
    for path in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256')):
        b[path.relative_to(ROOT).as_posix()]=sha(path)
    selected={n:sha(ROOT/n) for n in OWN};b.update(selected)
    write(LEDGER,dict(bindings=b,prior_source_sha256=sha(PRIOR),design_sha256=sha(DESIGN),
        next_plan_sha256=sha(PLAN),expected_new_tests=EXPECTED,maximum_new_test_runs=1,
        retained_preparation_tests=1492,retained079_audit_tests=24,
        maximum_native_invocations=0,maximum_windows_diagnostic_invocations=0,
        declared_profile_date='2026-10-08',inventory=inventory(),**ZERO,**FALSE))
    path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(selected):z.write(ROOT/n,n)
    write(ROOT/f'reports/{PREFIX}-initial-source.json',dict(bindings=selected,
        archive_sha256=sha(path),ledger_sha256=sha(LEDGER)))
    print(json.dumps(dict(frozen=True,bindings=len(b),new_tests=EXPECTED,native_invocations=0)))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['prior_source_sha256']==sha(PRIOR) and l['design_sha256']==sha(DESIGN)
    assert l['next_plan_sha256']==sha(PLAN) and l['inventory']==inventory()
    assert API['observed']()['sdk_connections']==0
    return l


def test():
    verify();sys.path.insert(0,str(ROOT/'src'))
    write(ROOT/f'reports/{PREFIX}-tests-started.json',dict(test_run_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    start=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_public_preflight_080.py')
    r=unittest.TextTestRunner(verbosity=1).run(suite)
    passed=r.wasSuccessful() and r.testsRun==EXPECTED and not r.skipped
    write(ROOT/f'reports/{PREFIX}-tests.json',dict(passed=passed,tests_run=r.testsRun,
        failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        elapsed_seconds=time.monotonic()-start,ledger_sha256=sha(LEDGER),
        retained_suites_rerun=False,**ZERO,**FALSE))
    if not passed:raise SystemExit(1)


def evidence():
    verify();sys.path.insert(0,str(ROOT/'src'))
    from forex_demo_lab.public_model_080 import model_case080,unchanged_methods080
    old=ROOT/'scripts/runtime-native-timing-078.py';new=ROOT/'src/forex_demo_lab/public_preflight_080.py'
    methods=unchanged_methods080(old.read_text(),new.read_text())
    rows=dict(legacy_crlf=model_case080(ROOT,legacy=True),
        corrected_crlf=model_case080(ROOT),wrong_helper_image=model_case080(ROOT,launcher='helper_image'))
    write(ROOT/f'reports/{PREFIX}-evidence.json',dict(ledger_sha256=sha(LEDGER),
        cases=rows,unchanged_integrity_methods=list(methods),
        deterministic_sidecar_blocker_reproduced=True,**ZERO,**FALSE))
    print(json.dumps(dict(modeled_cases=3,modeled_completions=sum(r['completed'] for r in rows.values()),native_invocations=0)))


def check():
    l=verify();i=inventory();t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    e=sealed(ROOT/f'reports/{PREFIX}-evidence.json')
    assert t['passed'] and t['tests_run']==EXPECTED and (t['failures'],t['errors'],t['skipped'])==(0,0,0)
    assert t['ledger_sha256']==e['ledger_sha256']==sha(LEDGER) and not t['retained_suites_rerun']
    rows=i['rows'];assert [r['newline'] for r in rows]==['lf']*4+['crlf','lf']
    assert rows[4]['sidecar_bytes']==66 and not rows[4]['legacy_cap_accepts'] and rows[4]['corrected_cap_accepts']
    assert rows[4]['content_bytes']==2133 and rows[4]['content_sha256']=='71ef653954fdaee55ae39eebcd30250800567b4144bac359306b1f45a9a38124'
    assert i['launcher_digest_differs_from_helper_image']
    assert e['unchanged_integrity_methods']==['__init__','check','properties','raw']
    assert set(e['cases'])=={'legacy_crlf','corrected_crlf','wrong_helper_image'}
    old=e['cases']['legacy_crlf'];new=e['cases']['corrected_crlf'];wrong=e['cases']['wrong_helper_image']
    assert not old['completed'] and old['stopped_label']=='helper_profile' and old['stop_reason']=='timing_public_file_rejected'
    assert (old['public_reads'],old['public_bytes'],old['public_stats'])==(10,sum(r['content_bytes']+r['sidecar_bytes'] for r in rows[:4])+rows[4]['content_bytes'],97)
    assert old['source_reads']==old['source_bytes']==old['source_stats']==0
    assert new['completed'] and new['stopped_label'] is None and new['stop_reason'] is None
    for r in (new,wrong):
        assert r['public_records_complete'] and r['source_bindings_complete']
        assert (r['public_reads'],r['public_bytes'],r['public_stats'])==(i['public_reads'],i['public_bytes'],i['public_stats'])
        assert r['source_reads']==i['source_reads']==30
    assert (new['source_bytes'],new['source_stats'])==(i['source_bytes_with_launcher'],i['source_stats_with_launcher'])
    assert not wrong['completed'] and wrong['stopped_label']=='launcher' and wrong['stop_reason']=='timing_launcher_rejected'
    assert (wrong['source_bytes'],wrong['source_stats'])==(i['source_bytes_with_helper_image'],i['source_stats_with_helper_image'])
    for r in e['cases'].values():
        assert r['dependencies_injected'] and not r['windows_metadata_measured'] and r['sdk_connections']==0 and not r['orders_available']
        assert r['public_reads']<=16 and r['public_bytes']<=2097152 and r['public_stats']<=128
        assert r['source_reads']<=64 and r['source_bytes']<=16777216 and r['source_stats']<=1024
    for r in (t,e,i):
        for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    initial=sealed(ROOT/f'reports/{PREFIX}-initial-source.json');path=ROOT/f'reports/{PREFIX}-initial-source.zip'
    assert sha(path)==initial['archive_sha256'] and initial['ledger_sha256']==sha(LEDGER)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None and set(z.namelist())==set(initial['bindings'])
        for n,h in initial['bindings'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checker_passed=True,ledger_sha256=sha(LEDGER),
        tests_sha256=sha(ROOT/f'reports/{PREFIX}-tests.json'),evidence_sha256=sha(ROOT/f'reports/{PREFIX}-evidence.json'),
        new_tests_passed=EXPECTED,modeled_cases_verified=3,unchanged_integrity_methods_verified=4,
        deterministic_sidecar_blocker_proven=True,public_stats_verified=i['public_stats'],
        source_stats_verified=i['source_stats_with_launcher'],**ZERO,**FALSE))
    print(json.dumps(dict(checker_passed=True,deterministic_sidecar_blocker_proven=True,original079_first_failure_proven=False,native_invocations=0)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');i=inventory()
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    result=ROOT/'docs/PUBLIC-PREFLIGHT-080-RESULTS.md'
    text=('# Public preflight080 results\n\n'
        'A deterministic blocker is identified and reproduced using the original bytes: '
        'helper-profile-068.sha256 contains the correct64-byte lowercase SHA256 plus '
        'Windows CRLF, totaling66 bytes. Frozen078 caps it at65 and requires LF, so '
        'it cannot accept this existing checksum. The original079 first failed substep '
        'was not recorded and remains unknown; this is not a new native trace.\n\n'
        'New PublicInputs080 admits exactly digest+LF or digest+CRLF with a declared66-byte '
        'sidecar cap. Other whitespace/BOM/bareCR/missing newline/uppercase/wrong digest '
        'and duplicate/non-ASCII JSON reject. No bytes or old checksum/source/authority '
        'were rewritten. Four other integrity methods match078 AST exactly modulo DATE '
        'and exception symbol names; all aggregate/read/stat/source/clock/date/file guards remain.\n\n'
        f'{EXPECTED} new offline tests pass, zero failures/errors/skips. Three explicit Windows/UNC '
        'path models: old reader rejects helper-profile; corrected reader completes six '
        'public records,29 bound sources and pinned launcher; substituting the distinct '
        'helper image for the launcher rejects. Independent original-file arithmetic checks '
        f'12 public reads/{i["public_bytes"]}bytes/{i["public_stats"]}stats and30 source/launcher '
        f'reads/{i["source_bytes_with_launcher"]}bytes/{i["source_stats_with_launcher"]}stats. '
        '1492 preparation and24 prior audit tests retained, not rerun. Models use declared '
        'non-reparse metadata/local descriptors; actual Windows metadata/sys.executable, '
        'MT5 account and native timing are not measured.\n\n'
        'Zero new native/helper/SDK/MT5/compiler/deploy/terminal-log/market/orders/receipt actions. '
        'No Windows diagnostic is needed to identify this blocker. Next NATIVE-TIMING-081-PLAN.md '
        'prepares a fresh metadata entry/phase/date/exact authority, uses cap66 for every '
        'sidecar including raw authorization and records fixed public failure substeps. '
        'Preparation/review must precede any separately authorized one-use measurement; '
        'never invoke078 or reuse its retired grant. Native timing/sharing/publication/ACK, '
        '070 cause and profit remain unproven;07610s/30s/250ms,033/035/data/cost/clock/coverage '
        'failures, consumed2025/reserved Nov–Dec2026/provider stops/raw old markers preserved. '
        'Eligibility/orders false.\n')
    with result.open('x') as f:f.write(text)
    latest=('Latest — 2026-10-08: public preflight080 correction sealed; read PUBLIC-PREFLIGHT-080-RESULTS.md. '
        'Original correct helper-profile checksum is66 bytes/SHA256+CRLF; frozen078 cap65/LF-only '
        'deterministically rejects it. Actual first079 failure remains unknown. New exact LF/CRLF '
        f'cap66 reader prepared; four other integrity methods AST-equal;{EXPECTED} new tests pass. '
        'Three Windows/UNC models: old rejects/profile, new completes six records+29sources+launcher, '
        'wrong helper image rejects; independent bytes/stats/hashes checked. 1492 preparation/24 audit '
        'tests retained, not rerun. No actual Windows metadata/sys.executable/native timing; zero new '
        'native/helper/SDK/MT5/compiler/deploy/log/market/orders/grants. Old source/sidecar/079/spent '
        'grant unchanged. Next081 fresh metadata entry/phase/date/authority preparation unexecuted; '
        'fixed public substeps and cap66 authorization sidecar required before any new measurement. '
        'No078 retry/reuse; sharing/publication/ACK/profit/070 cause and eligibility/orders remain false; '
        'timing/data/reserved gates retained. Earlier entries historical.\n\n')
    b=dict(l['bindings'])
    for n in HANDOFF:
        path=ROOT/n;s=path.read_text();idx=s.index('\n')+1
        path.write_text(s[:idx]+'\n'+latest+s[idx:]);b[n]=sha(path)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256',f'reports/{PREFIX}-initial-source.zip'):
        for path in ROOT.glob(pattern):b[path.relative_to(ROOT).as_posix()]=sha(path)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        new_tests_passed=EXPECTED,retained_preparation_tests=1492,retained079_audit_tests=24,
        retained_suites_rerun=False,modeled_cases_verified=3,unchanged_integrity_methods_verified=4,
        deterministic_sidecar_blocker_proven=True,next_plan_executed=False,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();final=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(final)
    b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(final,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');t=sealed(ROOT/f'reports/{PREFIX}-tests.json')
    assert c['checker_passed'] and c['ledger_sha256']==sha(LEDGER)
    assert c['tests_sha256']==sha(ROOT/f'reports/{PREFIX}-tests.json') and c['evidence_sha256']==sha(ROOT/f'reports/{PREFIX}-evidence.json')
    assert r['new_tests_passed']==t['tests_run']==EXPECTED and t['passed']
    assert not r['retained_suites_rerun'] and not r['next_plan_executed']
    assert r['deterministic_sidecar_blocker_proven'] and b[PLAN.relative_to(ROOT).as_posix()]==sha(PLAN)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,
        final_source_sha256=sha(final),bindings_verified=len(b),archive_members_verified=members,
        frozen_input_coverage_complete=True,frozen_inputs_verified=len(l['bindings']),
        new_tests_passed=EXPECTED,retained_preparation_tests=1492,retained079_audit_tests=24,
        retained_suites_rerun=False,modeled_cases_verified=3,unchanged_integrity_methods_verified=4,
        deterministic_sidecar_blocker_proven=True,next_plan_sha256=sha(PLAN),next_plan_executed=False,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,new_tests=EXPECTED,deterministic_sidecar_blocker_proven=True,native_invocations=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','test','evidence','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),test=test,
        evidence=evidence,check=check,seal=seal,review=review)[p.parse_args().action]()
