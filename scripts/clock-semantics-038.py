"""Freeze/reserve offline clock audit, documentation and isolated compilation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
OLD=runpy.run_path(str(ROOT/'scripts/clock-reference-037.py'))
sha,write,sealed=OLD['sha'],OLD['write'],OLD['sealed']
HANDOFF=OLD['HANDOFF'];bound_path=OLD['bound_path']
from forex_demo_lab.clock_semantics_038 import VERSION,native_clocks,receipt_intervals,research_valid
from forex_demo_lab.replication_analysis_035 import original

PRIOR=ROOT/'reports/clock-reference-037-final-source.json'
LEDGER=ROOT/'reports/clock-semantics-038-ledger.json'
RESERVATION=ROOT/'reports/clock-semantics-038-reservation.json'
OUTPUT=ROOT/'reports/clock-semantics-038-audit.json'
RESEARCH=ROOT/'reports/clock-semantics-038-research.json'
COMPILE=ROOT/'reports/clock-semantics-038-compile.json'
DECLARATION=ROOT/'config/research-actions-038.json'
MQL='mt5/Scripts/ForexDemoClockObserver038.mq5'
HEADER='mt5/Scripts/ClockGuard038.mqh'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='3440b22897d03b27ba39647b6dc69bd7204e7b84d7f21e88c9804614a45ace63'
    prior=sealed(PRIOR);bindings={};changes={}
    for group,values in prior.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for name,h in values.items():
            assert name not in bindings
            current=sha(bound_path(name))
            if current!=h:
                assert allow_handoff and group=='source_bindings' and name in HANDOFF,name
                changes[name]=dict(previous_sha256=h,current_sha256=current)
            bindings[name]=h
    external=prior['archive_external_bindings']
    assert len(bindings)==1101 and len(external)==46 and all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==prior['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1055 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert prior['fresh_performance_eligible'] is prior['annual_eligible'] is prior['orders_available'] is False
    return dict(bindings_verified=1101,archived_members_verified=1055,external_bindings_verified=46,
                allowed_handoff_changes=changes)


def freeze():
    assert os.name!='nt'
    prior=prior_verify();tests=sealed(ROOT/'reports/clock-semantics-038-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==546 and tests['new_tests']==24
    bindings={}
    for pattern in ('src/**/*.py','scripts/*038*','tests/*038*.py','docs/*038*.md','mt5/Scripts/*038*',
                    'mt5/Tests/ClockGuard038.cpp','config/research-actions-038.json',
                    'reports/clock-semantics-038-tests*','reports/clock-reference-037-*',
                    'reports/fresh-data-031-probe.*','reports/fresh-data-031-checks.*',
                    'data/fresh-context-033/*','data/fresh-replication-035/*'):
        for p in ROOT.glob(pattern):bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    compiler=Path('/mnt/c/Program Files/MetaTrader 5/metaeditor64.exe')
    cpp=Path(shutil.which('g++')).resolve();bindings[str(cpp)]=sha(cpp)
    if compiler.is_file():bindings[str(compiler)]=sha(compiler)
    old=sealed(ROOT/'reports/fresh-replication-035-ledger.json')
    for n,h in old['bindings'].items():
        if n.startswith('/mnt/'):
            assert sha(bound_path(n))==h;bindings[n]=h
    for stem in ('ledger','reservation','research','audit','compile','compile-reservation','checks','review','final-source'):
        assert not (ROOT/('reports/clock-semantics-038-'+stem+'.json')).exists()
    declaration=json.loads(DECLARATION.read_text())
    write(LEDGER,dict(version=VERSION,bindings=bindings,prior_snapshot_verification=prior,
        compiler_path=str(compiler),compiler_available=compiler.is_file(),cpp_compiler_path=str(cpp),
        research_budgets=declaration['budgets'],maximum_compilations=1,maximum_market_requests=0,
        maximum_native_connections=0,observer_runtime_authorized=False,orders_available=False,
        fresh_performance_eligible=False,annual_eligible=False))
    write(RESERVATION,dict(version=VERSION,ledger_sha256=sha(LEDGER),research_budgets=declaration['budgets'],
        maximum_compilations=1,market_requests=0,native_connections=0,observer_runtime_authorized=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),compiler_available=compiler.is_file())))


def verify():
    ledger=sealed(LEDGER)
    for name,h in ledger['bindings'].items():assert sha(bound_path(name))==h,name
    assert sealed(RESERVATION)['ledger_sha256']==sha(LEDGER)
    return ledger


def run():
    verify();research=sealed(RESEARCH);counts=research_valid(research,json.loads(DECLARATION.read_text()))
    results=[];fields=0
    for stage,folder in ((33,'data/fresh-context-033'),(35,'data/fresh-replication-035')):
        capture=sealed(ROOT/folder/'capture.json');meta=capture['reads'][1]
        rows=original(ROOT/folder,'ticks',meta);blob=(ROOT/folder/'ticks.bin').read_bytes()
        result=native_clocks(blob)
        assert result['rows']==len(rows)
        for i,row in enumerate(rows):
            import struct
            assert row['time']==struct.unpack_from('<q',blob,i*60)[0]
            assert row['time_msc']==struct.unpack_from('<q',blob,i*60+40)[0]
        results.append(dict(stage=stage,original_folder=folder,binary_sha256=sha(ROOT/folder/'ticks.bin'),**result))
        fields+=8*len(rows)
    old=sealed(ROOT/'reports/fresh-data-031-probe.json');current=sealed(ROOT/'reports/clock-reference-037-capture.json')
    comparisons=[dict(stage=31,**receipt_intervals(old['observations'])),
                 dict(stage=37,**receipt_intervals([current['quote']]))]
    assert old['clock_summary']['raw_minus_receipt_lower_ms']==comparisons[0]['envelope_ms'][0]
    assert old['clock_summary']['raw_minus_receipt_upper_ms']==comparisons[0]['envelope_ms'][1]
    assert current['comparison']['raw_minus_receipt_ms']==comparisons[1]['envelope_ms']
    write(OUTPUT,dict(version=VERSION,ledger_sha256=sha(LEDGER),research_sha256=sha(RESEARCH),
        action_counts=counts,native_fields=results,receipt_comparisons=comparisons,
        prior_public_reference_comparison=current['comparison'],native_csv_fields_verified=fields,
        saved_tick_rows=sum(r['rows'] for r in results),clock_fields_decoded=sum(r['clock_fields_decoded'] for r in results),
        market_requests=0,native_connections=0,historical_downloads=0,strategy_replays=0,orders_available=False,
        raw_labels_normalized=False,unknown_bits_interpreted=False,source_clock_sessions_qualified=False,
        upstream_completeness_qualified=False,historical_executable_costs_qualified=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,observer_runtime_executed=False))
    print(json.dumps(dict(audit_written=True,native_csv_fields_verified=fields,saved_tick_rows=sum(r['rows'] for r in results))))


def external_name(path):
    p=Path(path)
    if os.name=='nt':
        p=p.resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
    return str(p)


def compile_observer():
    ledger=verify();assert os.name=='nt'
    reserved=ROOT/'reports/clock-semantics-038-compile-reservation.json'
    assert not COMPILE.exists() and not reserved.exists()
    write(reserved,dict(version=VERSION,ledger_sha256=sha(LEDGER),maximum_compilations=1,
        observer_attachment_authorized=False,terminal_launch_authorized=False,orders_available=False))
    result=dict(outcome='compiler_unavailable',compiled=False,errors=None,warnings=None,process_completed=None)
    outputs={}
    if ledger['compiler_available']:
        try:
            command=subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'scripts/compile-clock-observer-038.ps1')],
                capture_output=True,text=True,timeout=75,check=True)
            private=json.loads(command.stdout)
            assert private['outcome'] in ('compiled','compile_failed','compiler_timeout','compiler_unavailable')
            result={k:private.get(k) for k in ('outcome','compiled','errors','warnings','process_completed')}
            for key in ('source','header','log','executable'):
                p=Path(private[key])
                expected_root=Path(os.environ['LOCALAPPDATA'])/'ForexDemoLab'/'builds'
                assert p.resolve().is_relative_to(expected_root.resolve())
                assert p.parent.name.startswith('clock038-')
                if p.is_file():outputs[external_name(p)]=sha(p)
            assert sha(Path(private['source']))==sha(ROOT/MQL) and sha(Path(private['header']))==sha(ROOT/HEADER)
            if result['compiled']:
                assert result['errors']==result['warnings']==0 and Path(private['executable']).stat().st_size>0
        except Exception:
            result=dict(outcome='compiler_driver_failure_details_redacted',compiled=False,
                        errors=None,warnings=None,process_completed=None)
    write(COMPILE,dict(version=VERSION,ledger_sha256=sha(LEDGER),reservation_sha256=sha(reserved),
        compiler_available=ledger['compiler_available'],compilation_attempts=int(ledger['compiler_available']),
        source_sha256=sha(ROOT/MQL),header_sha256=sha(ROOT/HEADER),output_bindings=outputs,
        **result,observer_attached=False,observer_runtime_executed=False,market_requests=0,native_connections=0,
        orders_available=False))
    print(json.dumps(dict(outcome=result['outcome'],compiled=result['compiled'],errors=result['errors'],warnings=result['warnings'],
                         observer_runtime_executed=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','verify','run','compile'))
    {'freeze':freeze,'verify':lambda:print(json.dumps(dict(verified=len(verify()['bindings'])))),
     'run':run,'compile':compile_observer}[parser.parse_args().action]()
