"""Freeze and run a strictly offline, exclusive-output flag audit."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/fresh-context-033.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['API']['API']['HANDOFF']
from forex_demo_lab.fresh_flags_034 import VERSION,FLAGS,KNOWN_MASK,DEFINITIONS,START,END,original,analyze

PRIOR=ROOT/'reports/fresh-context-033-final-source.json'
LEDGER=ROOT/'reports/fresh-flags-034-ledger.json'
OUTPUT=ROOT/'reports/fresh-flags-034-audit.json'
RESERVATION=ROOT/'reports/fresh-flags-034-reservation.json'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='41ced0bf0cce6d98bb2a5dfd0d81b07daea6a21f65ef1a9556724bede5981ebc'
    previous=sealed(PRIOR);bindings={};changes={}
    for group,values in previous.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for name,expected in values.items():
            assert name not in bindings
            current=sha(ROOT/name)
            if current!=expected:
                assert allow_handoff and group=='source_bindings' and name in HANDOFF,name
                changes[name]=dict(previous_sha256=expected,current_sha256=current)
            bindings[name]=expected
    external=previous['archive_external_bindings']
    assert len(bindings)==990 and len(external)==42
    assert all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==948 and set(z.namelist())==set(bindings)-set(external)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==bindings[name],name
    assert previous['diagnostic_passed'] is False
    return dict(bindings_verified=990,archived_members_verified=948,external_bindings_verified=42,allowed_handoff_changes=changes)


def freeze():
    checked=prior_verify();tests=sealed(ROOT/'reports/fresh-flags-034-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==457 and tests['new_tests']==16
    old_checks=sealed(ROOT/'reports/fresh-context-033-checks.json')
    assert old_checks['checker_passed'] and old_checks['diagnostic_passed'] is False
    bindings={}
    for pattern in ('src/**/*.py','scripts/*034*.py','scripts/check-fresh-context-033.py',
                    'tests/*034*.py','docs/*034*.md','reports/fresh-flags-034-tests*',
                    'reports/fresh-context-033-final-source.*','reports/fresh-context-033-ledger.*',
                    'reports/fresh-context-033-checks.*','reports/fresh-context-033-review.*',
                    'data/fresh-context-033/*','data/fresh-ticks-032/*'):
        for path in ROOT.glob(pattern):bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    assert not OUTPUT.exists() and not RESERVATION.exists() and not (ROOT/'reports/fresh-flags-034-checks.json').exists()
    write(LEDGER,dict(kind='frozen_offline_flags_034',version=VERSION,bindings=bindings,
        prior_snapshot_verification=checked,start_raw_ms=START,end_raw_ms=END,half_open_hour=True,
        flags=FLAGS,known_mask=KNOWN_MASK,fixed_definitions=DEFINITIONS,expected_witnesses=196,
        maximum_market_requests=0,strategy_replays=0,prior_033_diagnostic_passed=False,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),maximum_market_requests=0)))


def verify():
    ledger=sealed(LEDGER)
    for name,expected in ledger['bindings'].items():assert sha(ROOT/name)==expected,name
    return ledger


def run():
    ledger=verify()
    assert not OUTPUT.exists() and not OUTPUT.with_suffix('.sha256').exists()
    assert not (ROOT/'reports/fresh-flags-034-checks.json').exists()
    write(RESERVATION,dict(version=VERSION,ledger_sha256=sha(LEDGER),maximum_market_requests=0,orders_available=False))
    capture=sealed(ROOT/'data/fresh-context-033/capture.json')
    sample=sealed(ROOT/'data/fresh-ticks-032/capture.json')
    ticks=original(ROOT/'data/fresh-context-033','ticks',capture['reads'][1])
    bars=original(ROOT/'data/fresh-context-033','bars',capture['reads'][2])
    witnesses=original(ROOT/'data/fresh-ticks-032','ticks',sample,sample=True)
    result=analyze(ticks,bars,witnesses)
    result.update(kind='offline_fixed_flag_audit_034',ledger_sha256=sha(LEDGER),
        fields_compared=8*(len(ticks)+len(bars)+len(witnesses)),input_original_bindings={
            n:h for n,h in ledger['bindings'].items() if n.startswith('data/')})
    write(OUTPUT,result)
    print(json.dumps({k:result[k] for k in ('source_rows','witnesses_matched','disagreement_rows',
                      'bid_disagreement_rows','ask_disagreement_rows','market_requests')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','verify','run'))
    {'freeze':freeze,'verify':verify,'run':run}[parser.parse_args().action]()
