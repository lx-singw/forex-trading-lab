"""Preserve the fixed volume discrepancy, handoff, review and source snapshot."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-context-033.py'))
CHECK=runpy.run_path(str(ROOT/'scripts/check-fresh-context-033.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
REVIEW=ROOT/'reports/fresh-context-033-review.json'
FINAL=ROOT/'reports/fresh-context-033-final-source.json'
HANDOFF=API['API']['API']['HANDOFF']


def evidence():
    ledger=API['verify']()
    tests=sealed(ROOT/'reports/fresh-context-033-tests.json')
    checks=sealed(ROOT/'reports/fresh-context-033-checks.json')
    capture=sealed(API['OUTPUT']/'capture.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==441 and tests['new_tests']==25
    assert checks['checker_passed'] and checks['diagnostic_passed'] is False
    assert checks['ledger_sha256']==sha(API['LEDGER'])
    assert checks['rows_checked']==13769 and checks['bars_checked']==1 and checks['binary_fields_checked']==110160
    assert checks['witnesses_matched']==196 and checks['ambiguous_witnesses']==checks['missing_witnesses']==0
    assert checks['market_requests']==capture['requests']==3
    assert capture['status']=='source_hour_originals_preserved_and_rows_valid'
    assert checks['bar_differences']==[dict(field='tick_volume',reconstructed=13769,recorded=8368,difference=5401)]
    assert not checks['tick_audit']['error_counts'] and not checks['bar_audit']['errors']
    outputs={}
    for name,expected in checks['original_bindings'].items():
        path=API['OUTPUT']/name;assert sha(path)==expected,name
        outputs[path.relative_to(ROOT).as_posix()]=expected
    assert set(checks['original_bindings'])=={p.name for p in API['OUTPUT'].iterdir()}
    assert sum(p.stat().st_size for p in API['OUTPUT'].iterdir())==1611633<=ledger['maximum_evidence_bytes']
    ticks=CHECK['decode'](API['OUTPUT'],'ticks',capture['reads'][1])
    bars=CHECK['decode'](API['OUTPUT'],'bars',capture['reads'][2])
    assert CHECK['tick_audit'](ticks)==checks['tick_audit'] and CHECK['bars_audit'](bars)==checks['bar_audit']
    elapsed=0
    for r in capture['reads']:
        before,after=r['receipt_before'],r['receipt_after']
        for v in (before,after):assert datetime.fromtimestamp(v['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
        assert after['utc_ms']>=before['utc_ms'] and after['monotonic_ns']-before['monotonic_ns']==r['elapsed_ns']>=0
        assert r['api_error_code']==1
        if r['kind']!='horizon':
            assert r['elapsed_ns']<=60000000000;elapsed+=r['elapsed_ns']
    assert elapsed==capture['history_elapsed_ns']==checks['history_elapsed_ns']==1012700
    flag_counts=dict(sorted(Counter(r['flags'] for r in ticks).items()))
    assert flag_counts=={1026:4346,1028:5401,1030:4022}
    bid_flags=sum(bool(r['flags']&2) for r in ticks)
    changes=sum(a['bid']!=b['bid'] for a,b in zip(ticks,ticks[1:]))
    assert bid_flags==8368 and changes==8314
    return ledger,tests,checks,capture,outputs,dict(
        post_result_observation=True,not_a_revised_gate=True,flag_histogram=flag_counts,
        bid_flag_rows=bid_flags,bid_value_change_transitions=changes,first_row_without_predecessor=1,
        unknown_mask_observed=1024,unknown_mask_interpreted=False,market_requests=0,
        sdk_constants_inspected_without_connection=dict(BID=2,ASK=4,LAST=8,VOLUME=16,BUY=32,SELL=64),
        official_documentation_searches=1,
        sources=['https://www.mql5.com/en/docs/constants/structures/mqltick',
                 'https://www.mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick'])


def handoff():
    evidence()
    text=('Latest — 2026-10-06: source-hour context033 collected and integrity-checked. '
        'Read FRESH-CONTEXT-033-RESULTS.md. Exactly three guarded reads preserve13,769 ticks '
        'and one H1 bar; all196 complete032 records match uniquely and all four bid OHLC '
        'prices agree. Frozen diagnostic fails tick_volume:13,769 events versus8,368 recorded '
        '(difference5,401), retained unchanged. Checker integrity passes110,160 fields; '
        '441 software tests pass (25 new). No row errors or exact duplicate transitions; '
        '30 tied transitions,26.114s maximum observed gap. Combined native history0.0010127s. '
        '65 frozen inputs; prior963 bindings/922 archive members/41 external inputs verified. '
        'Post-result flag counts suggest bid-flag volume, but unknown bit1024 and flagged '
        'versus value-change differences remain; no revised success gate. ActualDEMO/USD, '
        'Algo off, stable private identity; no IDs exported. Fresh/annual eligibility false; '
        'clock/completeness/cost qualification unresolved. No orders or strategy returns. '
        'Consumed2025/reservedNov–Dec2026/provider stops unchanged. Next FRESH-FLAGS-034-PLAN.md '
        'is an entirely offline flag/count audit, declared not executed. Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True,diagnostic_passed=False)))


def review():
    previous=API['prior_verify'](allow_handoff=True)
    ledger,tests,checks,capture,outputs,flags=evidence()
    documents=('docs/FRESH-CONTEXT-033-RESULTS.md','docs/FRESH-FLAGS-034-PLAN.md','scripts/finalize-fresh-context-033.py')
    for name in HANDOFF:assert 'FRESH-CONTEXT-033-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/documents[1]).read_text()
    write(REVIEW,dict(kind='post_source_hour_review_033',review_integrity_passed=True,diagnostic_passed=False,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),output_bindings=outputs,
        checks_sha256=sha(ROOT/'reports/fresh-context-033-checks.json'),
        documentation_bindings={name:sha(ROOT/name) for name in documents},software_tests_passed=441,
        market_requests=3,rows_checked=13769,bars_checked=1,binary_fields_checked=110160,witnesses_matched=196,
        volume_disagreement_preserved=checks['bar_differences'],post_result_flag_observation=flags,
        strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=documents[1],next_plan_executed=False))
    print(json.dumps(dict(review_integrity_passed=True,diagnostic_passed=False,volume_disagreement=5401)))


def snapshot():
    checked=sealed(REVIEW);assert checked['review_integrity_passed'] and checked['diagnostic_passed'] is False
    API['prior_verify'](allow_handoff=True);ledger=API['verify']()
    assert sha(ROOT/'reports/fresh-context-033-checks.json')==checked['checks_sha256']
    for name,expected in (checked['documentation_bindings']|checked['output_bindings']).items():assert sha(ROOT/name)==expected,name
    prior=sealed(API['PRIOR'])
    groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*033*.md','docs/FRESH-FLAGS-034-PLAN.md','scripts/*033*.py',
                    'src/forex_demo_lab/fresh_context_033.py','tests/test_fresh_context_033.py'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/fresh-context-033*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    groups['source_hour_input_bindings']={}
    for path in API['OUTPUT'].iterdir():
        assert path.is_file();groups['source_hour_input_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    already={n:h for v in groups.values() for n,h in v.items()}
    for name,expected in ledger['bindings'].items():
        if name in already:assert already[name]==expected,name
        else:groups['source_hour_input_bindings'][name]=expected
    bindings={n:h for v in groups.values() for n,h in v.items()}
    assert len(bindings)==sum(map(len,groups.values()))
    external={n:h for n,h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
              n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in bindings.items() if n not in external}
    for name,expected in bindings.items():assert sha(ROOT/name)==expected,name
    archive=FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.infolist())==len(internal) and set(z.namelist())==set(internal)
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==internal[name],name
    write(FINAL,dict(kind='post_source_hour_context_snapshot_033',**groups,
        archive_external_bindings=external,archive_members_verified=len(internal),external_bindings_verified=len(external),
        archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),
        completed_utc=datetime.now(timezone.utc).isoformat(),software_tests_passed=441,market_requests=3,
        rows_checked=13769,bars_checked=1,binary_fields_checked=110160,witnesses_matched=196,
        checker_integrity_passed=True,diagnostic_passed=False,volume_difference=5401,strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
