"""Freeze and run offline qualification review; browsing is separately recorded."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
API=runpy.run_path(str(ROOT/'scripts/fresh-replication-035.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['API']['API']['HANDOFF']
from forex_demo_lab.data_qualification_036 import VERSION,overlap,validate_research,validate_matrix,policy
from forex_demo_lab.replication_analysis_035 import original

PRIOR=ROOT/'reports/fresh-replication-035-final-source.json'
LEDGER=ROOT/'reports/data-qualification-036-ledger.json'
DECLARATION=ROOT/'config/research-actions-036.json'
OUTPUT=ROOT/'reports/data-qualification-036-assessment.json'


def prior_verify(allow_handoff=False):
    assert sha(PRIOR)=='0ff4bb84aa084502f4e069a5625f1da4dc2b59f6aea3ba82d5356320eada6174'
    previous=sealed(PRIOR);bindings={};changes={}
    for group,values in previous.items():
        if not group.endswith('_bindings') or group=='archive_external_bindings':continue
        for name,h in values.items():
            assert name not in bindings;current=sha(ROOT/name)
            if current!=h:
                assert allow_handoff and group=='source_bindings' and name in HANDOFF,name
                changes[name]=dict(previous_sha256=h,current_sha256=current)
            bindings[name]=h
    external=previous['archive_external_bindings']
    assert len(bindings)==1049 and len(external)==44 and all(bindings[n]==h for n,h in external.items())
    assert sha(PRIOR.with_suffix('.zip'))==previous['archive_sha256']
    with zipfile.ZipFile(PRIOR.with_suffix('.zip')) as z:
        assert z.testzip() is None and len(z.infolist())==1005 and set(z.namelist())==set(bindings)-set(external)
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==bindings[n],n
    assert previous['diagnostic_passed'] is False
    return dict(bindings_verified=1049,archived_members_verified=1005,external_bindings_verified=44,allowed_handoff_changes=changes)


def freeze():
    checked=prior_verify();tests=sealed(ROOT/'reports/data-qualification-036-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==498 and tests['new_tests']==16
    bindings={}
    for pattern in ('src/**/*.py','scripts/*036*.py','scripts/check-fresh-replication-035.py',
                    'scripts/check-fresh-context-033.py','tests/*036*.py','docs/*036*.md','config/research-actions-036.json',
                    'reports/data-qualification-036-tests*','reports/fresh-replication-035-*',
                    'reports/fresh-flags-034-audit.*','reports/fresh-flags-034-checks.*','reports/fresh-flags-034-review.*',
                    'reports/fresh-data-031-probe.*','reports/fresh-data-031-checks.*',
                    'docs/FRESH-DATA-031-RESULTS.md','docs/FRESH-REPLICATION-035-RESULTS.md',
                    'data/fresh-context-033/*','data/fresh-replication-035/*'):
        for path in ROOT.glob(pattern):bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    for name in ('reservation','research','assessment','checks'):
        assert not (ROOT/('reports/data-qualification-036-'+name+'.json')).exists()
    declared=json.loads(DECLARATION.read_text())
    write(LEDGER,dict(kind='frozen_offline_qualification_review_036',version=VERSION,bindings=bindings,
        prior_snapshot_verification=checked,research_declaration_sha256=sha(DECLARATION),
        maximum_search_queries=4,maximum_opens=12,maximum_finds=8,
        declared_search_queries=declared['search_queries'],declared_target_pages=declared['target_pages'],
        maximum_market_requests=0,prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    write(ROOT/'reports/data-qualification-036-reservation.json',dict(version=VERSION,ledger_sha256=sha(LEDGER),
        maximum_market_requests=0,research_budget=dict(search_queries=4,opens=12,finds=8),orders_available=False))
    print(json.dumps(dict(frozen=True,bindings=len(bindings),maximum_market_requests=0)))


def verify():
    ledger=sealed(LEDGER)
    for name,h in ledger['bindings'].items():assert sha(ROOT/name)==h,name
    return ledger


def matrix():
    return [
        dict(gate='original_integrity',status='observed_pass',evidence_class='observed_equality',
            local_evidence=['reports/fresh-replication-035-checks.json'],finding_ids=[],
            limitation='Exact native/CSV hashes and fields prove preservation of returned observations, not upstream completeness.',
            minimal_missing_evidence='No missing field-fidelity evidence within the saved scope; retain original hashes and both revisions.'),
        dict(gate='relative_feed_prices_volumes',status='observed_pass',evidence_class='observed_equality',
            local_evidence=['reports/fresh-replication-035-analysis.json','reports/fresh-flags-034-audit.json'],finding_ids=['flag_definitions','bar_fields'],
            limitation='Four same-feed OHLC/BID-count equalities and stable overlap prices do not prove independent history or provider algorithm.',
            minimal_missing_evidence='Independent provider/time evidence and broader predeclared chronological coverage before claiming anything beyond relative agreement.'),
        dict(gate='metadata_repeatability',status='observed_failure',evidence_class='observed_contradiction',
            local_evidence=['reports/fresh-replication-035-checks.json','reports/fresh-replication-035-post-result-differences.json'],finding_ids=['additional_flag_bits','synchronization'],
            limitation='8368 complete records differ in flags by bit128. Generic synchronization documentation does not identify the cause or certify bit semantics.',
            minimal_missing_evidence='Authoritative definitions for remaining bits and provider/runtime revision semantics; separately planned repeatability evidence. Preserve failures and both originals.'),
        dict(gate='source_clock_sessions',status='unresolved',evidence_class='absent_provider_evidence',
            local_evidence=['reports/fresh-data-031-probe.json','reports/fresh-data-031-checks.json'],finding_ids=['utc_contract'],
            limitation='Generic API UTC expectations do not certify raw labels about three hours ahead of local receipts. Local reference calibration and provider historical session meaning remain unverified.',
            minimal_missing_evidence='Calibrated independent UTC reference plus provider-specific simultaneous timestamp and historical timezone/DST/session evidence; no constant-offset correction from these observations.'),
        dict(gate='upstream_completeness',status='unresolved',evidence_class='absent_provider_evidence',
            local_evidence=['reports/fresh-replication-035-qualification.json','reports/fresh-replication-035-checks.json'],finding_ids=['synchronization'],
            limitation='SDK success, continuous source ordering, maximum gaps and same-feed bar agreement do not prove every upstream event was delivered.',
            minimal_missing_evidence='Provider coverage/completeness provenance, explained session closures/gaps and independently reconciled event history, with documented SDK synchronization outcomes.'),
        dict(gate='historical_executable_costs',status='unresolved',evidence_class='absent_provider_evidence',
            local_evidence=['data/fresh-replication-035/capture.json','reports/fresh-replication-035-qualification.json'],finding_ids=['bar_fields','current_symbol_units'],
            limitation='Historical bid/ask observations and zero bar spread/real_volume plus current tick-value/swap fields do not supply historical executable commissions, conversion, swaps or slippage.',
            minimal_missing_evidence='Date-effective demo-contract fee/swap/unit/conversion schedules and executable bid/ask provenance; calibrated execution assumptions and bounded demo evidence only after qualification.')]


def run():
    ledger=verify();research=sealed(ROOT/'reports/data-qualification-036-research.json')
    declared=json.loads(DECLARATION.read_text());counts=validate_research(research,declared)
    old_capture=sealed(ROOT/'data/fresh-context-033/capture.json');new_capture=sealed(ROOT/'data/fresh-replication-035/capture.json')
    old=original(ROOT/'data/fresh-context-033','ticks',old_capture['reads'][1])
    new=original(ROOT/'data/fresh-replication-035','ticks',new_capture['reads'][1])
    bars=original(ROOT/'data/fresh-replication-035','bars',new_capture['reads'][2])
    reviewed=overlap(old,new);prior=sealed(ROOT/'reports/fresh-replication-035-post-result-differences.json')
    for key in ('old_original_rows','new_overlapping_rows','non_flag_fields_compared','all_non_flag_fields_equal',
                'changed_field_counts','flag_xor_histogram','flag_transitions','changed_rows',
                'unchanged_complete_ordinal_pairs','changed_complete_ordinal_pairs'):
        assert json.loads(json.dumps(reviewed[key]))==prior[key],key
    gates=matrix();validate_matrix(gates,ledger['bindings'],research)
    assert reviewed['complete_witnesses_matched']==5401 and reviewed['complete_witnesses_missing']==8368
    assert sealed(ROOT/'reports/fresh-replication-035-checks.json')['diagnostic_passed'] is False
    write(OUTPUT,dict(kind='offline_source_qualification_assessment_036',version=VERSION,
        ledger_sha256=sha(LEDGER),research_sha256=sha(ROOT/'reports/data-qualification-036-research.json'),
        action_counts=counts,overlap=reviewed,qualification_matrix=gates,proposed_data_policy=policy(),
        binary_fields_compared=8*(len(old)+len(new)+len(bars)),prior_033_diagnostic_passed=False,
        prior_035_diagnostic_passed=False,unknown_flag_bits_interpreted=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(assessment_written=True,fields_compared=8*(len(old)+len(new)+len(bars)),
        changed_flags=len(reviewed['changed_rows']),action_counts=counts,performance_eligible=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','verify','run'))
    {'freeze':freeze,'verify':verify,'run':run}[parser.parse_args().action]()
