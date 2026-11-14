"""Offline flag findings, unchanged prior failure, review and final snapshot."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-flags-034.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['HANDOFF']
REVIEW=ROOT/'reports/fresh-flags-034-review.json'
FINAL=ROOT/'reports/fresh-flags-034-final-source.json'


def evidence():
    ledger=API['verify']();audit=sealed(API['OUTPUT']);checks=sealed(ROOT/'reports/fresh-flags-034-checks.json')
    tests=sealed(ROOT/'reports/fresh-flags-034-tests.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==457 and tests['new_tests']==16
    assert checks['checker_passed'] and checks['audit_sha256']==sha(API['OUTPUT']) and checks['ledger_sha256']==sha(API['LEDGER'])
    assert checks['binary_fields_checked']==audit['fields_compared']==111728
    assert audit['source_rows']==audit['half_open_hour_rows']==13769
    assert audit['witnesses_matched']==196 and audit['ambiguous_witnesses']==audit['missing_witnesses']==0
    assert audit['disagreement_rows']==audit['bid_disagreement_rows']==53 and audit['ask_disagreement_rows']==0
    assert all(d['bid_flag'] and not d['bid_value_changed'] and d['mismatched_fields']==['bid'] for d in audit['flag_value_disagreements'])
    assert audit['same_millisecond_disagreement_rows']==0 and audit['remaining_mask_histogram']=={'1024':13769}
    assert audit['bid_value_change_transitions']==8314 and audit['ask_value_change_transitions']==9423
    assert audit['category_counts']==dict(bid_flags=8368,ask_flags=9423,both_flags=4022,neither_flag=0)
    comparisons={c['definition']:c for c in audit['fixed_definition_comparisons']}
    assert tuple(comparisons)==tuple(ledger['fixed_definitions'])
    assert comparisons['all']['volume_difference']==5401 and comparisons['bid_flag']['volume_difference']==0
    assert comparisons['bid_value_change_with_first']['volume_difference']==-53
    assert not comparisons['all']['bar_price_differences'] and not comparisons['bid_flag']['bar_price_differences']
    assert sealed(ROOT/'reports/fresh-context-033-checks.json')['diagnostic_passed'] is False
    assert sealed(API['PRIOR'])['diagnostic_passed'] is False
    for report in (audit,checks):
        for name in ('market_requests','strategy_replays'):assert report[name]==0
        for name in ('prior_033_diagnostic_passed','fresh_performance_eligible','annual_eligible','orders_available'):assert report[name] is False
    for name,h in audit['input_original_bindings'].items():assert sha(ROOT/name)==h,name
    return ledger,audit,checks,tests


def handoff():
    evidence()
    text=('Latest — 2026-10-06: offline quote-flag audit034 complete. Read FRESH-FLAGS-034-RESULTS.md. '
        'H1 volume8,368 equals BID-flag rows; full13,769 events include5,401 ASK-only rows. '
        'All53 bid flag/value disagreements are flagged unchanged values; no ask disagreements. '
        '8,314 observed bid transitions plus one first-row uncertainty gives8,315; do not substitute '
        'value changes for flags. Unknown bit1024 appears in every row and stays uninterpreted. '
        'All seven predeclared definitions reported; all196 complete032 records match uniquely. '
        'Independent111,728 original fields and every report reconstruction pass.457 tests (16 new), '
        '73 frozen inputs; prior990 bindings/948 ZIP members/42 external inputs verified. '
        'Zero market requests/connections/terminal actions/downloads/returns/orders. '
        '033 diagnostic remains false; same-feed count equality does not certify completeness, '
        'clock/session/costs or edge. Fresh/annual eligibility false; consumed2025/reservedNov–Dec2026 '
        'and provider stops untouched. Next FRESH-REPLICATION-035-PLAN.md declares one guarded '
        'four-source-hour replication, not executed. Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True,market_requests=0)))


def review():
    previous=API['prior_verify'](allow_handoff=True);ledger,audit,checks,tests=evidence()
    documents=('docs/FRESH-FLAGS-034-RESULTS.md','docs/FRESH-REPLICATION-035-PLAN.md','scripts/finalize-fresh-flags-034.py')
    for name in HANDOFF:assert 'FRESH-FLAGS-034-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/documents[1]).read_text()
    write(REVIEW,dict(kind='post_offline_flags_review_034',passed=True,prior_snapshot_verification=previous,
        input_bindings_verified=len(ledger['bindings']),audit_sha256=sha(API['OUTPUT']),
        checks_sha256=sha(ROOT/'reports/fresh-flags-034-checks.json'),input_original_bindings=audit['input_original_bindings'],
        documentation_bindings={n:sha(ROOT/n) for n in documents},software_tests_passed=457,
        binary_fields_checked=111728,witnesses_matched=196,disagreement_rows=53,
        fixed_definition_comparisons=[{k:v for k,v in c.items() if k!='original_row_indices'} for c in audit['fixed_definition_comparisons']],
        prior_033_diagnostic_passed=False,unknown_bits_interpreted=False,market_requests=0,strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,next_plan=documents[1],next_plan_executed=False))
    print(json.dumps(dict(passed=True,market_requests=0,disagreement_rows=53)))


def snapshot():
    checked=sealed(REVIEW);assert checked['passed'];API['prior_verify'](allow_handoff=True);ledger=API['verify']()
    assert sha(API['OUTPUT'])==checked['audit_sha256'] and sha(ROOT/'reports/fresh-flags-034-checks.json')==checked['checks_sha256']
    for name,h in (checked['documentation_bindings']|checked['input_original_bindings']).items():assert sha(ROOT/name)==h,name
    prior=sealed(API['PRIOR'])
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*034*.md','docs/FRESH-REPLICATION-035-PLAN.md','scripts/*034*.py',
                    'src/forex_demo_lab/fresh_flags_034.py','tests/test_fresh_flags_034.py'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/fresh-flags-034*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    groups['offline_flag_input_bindings']={}
    already={n:h for v in groups.values() for n,h in v.items()}
    for name,h in ledger['bindings'].items():
        if name in already:assert already[name]==h,name
        else:groups['offline_flag_input_bindings'][name]=h
    bindings={n:h for v in groups.values() for n,h in v.items()}
    assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for name,h in bindings.items():assert sha(ROOT/name)==h,name
    archive=FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal) and set(z.namelist())==set(internal)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==internal[name],name
    write(FINAL,dict(kind='post_offline_quote_flags_snapshot_034',**groups,archive_external_bindings=external,
        archive_members_verified=len(internal),external_bindings_verified=len(external),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),
        completed_utc=datetime.now(timezone.utc).isoformat(),software_tests_passed=457,binary_fields_checked=111728,
        witnesses_matched=196,disagreement_rows=53,prior_033_diagnostic_passed=False,unknown_bits_interpreted=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
