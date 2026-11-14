"""Preserve failed full-record replication, supplementary differences and snapshot."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/fresh-replication-035.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['API']['API']['HANDOFF']
REVIEW=ROOT/'reports/fresh-replication-035-review.json'
FINAL=ROOT/'reports/fresh-replication-035-final-source.json'
DIFFERENCES=ROOT/'reports/fresh-replication-035-post-result-differences.json'
from forex_demo_lab.replication_analysis_035 import original


def overlap():
    API['verify']();capture=sealed(API['OUTPUT']/'capture.json')
    previous=sealed(ROOT/'data/fresh-context-033/capture.json')
    old=original(ROOT/'data/fresh-context-033','ticks',previous['reads'][1])
    new=original(API['OUTPUT'],'ticks',capture['reads'][1])
    current=[(i,r) for i,r in enumerate(new) if 1791291600000<=r['time_msc']<1791295200000]
    assert len(old)==len(current)==13769
    counts=Counter();transitions=Counter();xors=Counter();changes=[]
    fields=('time','bid','ask','last','volume','time_msc','flags','volume_real')
    for i,(before,(j,after)) in enumerate(zip(old,current)):
        different=[k for k in fields if before[k]!=after[k]]
        counts.update(different);transitions[(before['flags'],after['flags'])]+=1
        xor=before['flags']^after['flags'];xors[xor]+=1
        if different:
            changes.append(dict(prior_original_row_index=i,new_original_row_index=j,raw_time_msc=before['time_msc'],
                changed_fields=different,flags_before=before['flags'],flags_after=after['flags'],flag_xor=xor))
        assert all(before[k]==after[k] for k in fields if k!='flags')
    assert dict(counts)=={'flags':8368} and dict(xors)=={128:8368,0:5401}
    assert dict(transitions)=={(1026,1154):4346,(1030,1158):4022,(1028,1028):5401}
    return dict(kind='post_result_ordinal_overlap_differences_035',post_result_observation=True,not_a_revised_gate=True,
        complete_identity_matching_replaced=False,ordinal_alignment_scope='One saved overlap, every non-flag field and original order checked',
        previous_capture_sha256=sha(ROOT/'data/fresh-context-033/capture.json'),new_capture_sha256=sha(API['OUTPUT']/'capture.json'),
        old_original_rows=13769,new_overlapping_rows=13769,non_flag_fields_compared=7*13769,
        all_non_flag_fields_equal=True,changed_field_counts=dict(counts),flag_xor_histogram=dict(sorted(xors.items())),
        flag_transitions=[dict(flags_before=a,flags_after=b,rows=n) for (a,b),n in sorted(transitions.items())],
        changed_rows=changes,unchanged_complete_ordinal_pairs=5401,changed_complete_ordinal_pairs=8368,
        unknown_flag_bits_interpreted=False,prior_033_diagnostic_passed=False,diagnostic_passed=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)


def differences():
    result=overlap();write(DIFFERENCES,result)
    print(json.dumps(dict(all_non_flag_fields_equal=True,changed_flags=8368,complete_pairs_unchanged=5401,diagnostic_passed=False)))


def evidence():
    ledger=API['verify']();tests=sealed(ROOT/'reports/fresh-replication-035-tests.json')
    capture=sealed(API['OUTPUT']/'capture.json');analysis=sealed(ROOT/'reports/fresh-replication-035-analysis.json')
    checks=sealed(ROOT/'reports/fresh-replication-035-checks.json');diff=sealed(DIFFERENCES)
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==482 and tests['new_tests']==25
    assert capture['status']=='four_source_hours_originals_preserved_and_rows_valid' and capture['requests']==3
    assert checks['checker_passed'] and checks['diagnostic_passed'] is False and analysis['diagnostic_passed'] is False
    assert checks['ledger_sha256']==analysis['ledger_sha256']==sha(API['LEDGER'])
    assert checks['analysis_sha256']==sha(ROOT/'reports/fresh-replication-035-analysis.json')
    assert checks['rows_checked']==analysis['source_rows']==74929 and checks['bars_checked']==4
    assert checks['binary_fields_checked']==709616
    assert checks['witnesses_matched']==analysis['witnesses_matched']==5401
    assert checks['missing_witnesses']==analysis['missing_witnesses']==8368 and checks['ambiguous_witnesses']==0
    assert analysis['all_four_relative_hypotheses_passed'] is True
    assert [h['hour_event_rows'] for h in analysis['hours']]==[24381,19788,16991,13769]
    assert [h['category_counts']['bid_flags'] for h in analysis['hours']]==[16257,12941,11033,8368]
    assert [h['bid_disagreement_rows'] for h in analysis['hours']]==[44,45,53,54]
    assert all(h['ask_disagreement_rows']==0 and h['relative_bid_price_count_hypothesis_passed'] for h in analysis['hours'])
    assert checks['disagreement_rows']==analysis['disagreement_rows']==196
    assert not checks['tick_audit']['error_counts'] and not checks['bar_audit']['errors']
    assert json.loads(json.dumps(overlap()))==diff
    outputs={}
    for name,expected in checks['original_bindings'].items():
        path=API['OUTPUT']/name;assert sha(path)==expected,name
        outputs[path.relative_to(ROOT).as_posix()]=expected
    assert set(checks['original_bindings'])=={p.name for p in API['OUTPUT'].iterdir()}
    assert sum(p.stat().st_size for p in API['OUTPUT'].iterdir())==8743924<=ledger['maximum_evidence_bytes']
    elapsed=0
    for r in capture['reads']:
        before,after=r['receipt_before'],r['receipt_after']
        for value in (before,after):assert datetime.fromtimestamp(value['utc_ms']/1000,timezone.utc).date().isoformat()==ledger['date']
        assert after['utc_ms']>=before['utc_ms'] and after['monotonic_ns']-before['monotonic_ns']==r['elapsed_ns']>=0
        assert r['api_error_code']==1
        if r['kind']!='horizon':assert r['elapsed_ns']<=60000000000;elapsed+=r['elapsed_ns']
    assert elapsed==capture['history_elapsed_ns']==checks['history_elapsed_ns']==1296873000
    qualification=sealed(ROOT/'reports/fresh-replication-035-qualification.json')
    assert qualification['relative_feed_collection_permitted'] is True and qualification['performance_testing_permitted'] is False
    assert sha(ROOT/'reports/fresh-replication-035-qualification.json')==ledger['qualification_review_sha256']
    assert sealed(ROOT/'reports/fresh-context-033-checks.json')['diagnostic_passed'] is False
    return ledger,capture,analysis,checks,outputs


def handoff():
    evidence()
    text=('Latest — 2026-10-06: four-source-hour replication035 collected and independently checked. '
        'Read FRESH-REPLICATION-035-RESULTS.md. Exactly three guarded demo reads preserve74,929 ticks/four bars. '
        'All four relative bid-OHLC/BID-count hypotheses pass, but complete-record replication fails: '
        'only5,401/13,769 saved033 records match;8,368 flags gained bit128. Every overlapping timestamp, '
        'price and other non-flag field/order agrees in a separate post-result ordinal comparison; '
        'both revisions preserved and original full-identity rule unchanged. Extra bits1024/128 remain '
        'uninterpreted.196 bid flag/value disagreements (44/45/53/54 by hour), zero ask disagreements. '
        '709,616 fields and all analytical reconstructions pass integrity checks.482 tests (25 new); '
        '83 frozen inputs; prior1,014 bindings/971 ZIP members/43 external inputs verified. '
        'Pre-acquisition qualification review keeps clock/completeness/cost gates unresolved and '
        'performance testing unavailable. ActualDEMO/USD/Algo off/private stable identity; no IDs exported. '
        'No retries/orders/returns/strategy changes. Fresh/annual eligibility false,033 failure retained, '
        'consumed2025/reservedNov–Dec2026/provider stops unchanged. Next DATA-QUALIFICATION-036-PLAN.md '
        'is bounded official-documentation/evidence-gap review without market calls, declared not executed. '
        'Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True,diagnostic_passed=False)))


def review():
    previous=API['prior_verify'](allow_handoff=True);ledger,capture,analysis,checks,outputs=evidence()
    documents=('docs/FRESH-REPLICATION-035-RESULTS.md','docs/DATA-QUALIFICATION-036-PLAN.md','scripts/finalize-fresh-replication-035.py')
    for name in HANDOFF:assert 'FRESH-REPLICATION-035-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/documents[1]).read_text()
    write(REVIEW,dict(kind='post_four_source_hour_review_035',review_integrity_passed=True,diagnostic_passed=False,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),output_bindings=outputs,
        analysis_sha256=sha(ROOT/'reports/fresh-replication-035-analysis.json'),checks_sha256=sha(ROOT/'reports/fresh-replication-035-checks.json'),
        post_result_differences_sha256=sha(DIFFERENCES),documentation_bindings={n:sha(ROOT/n) for n in documents},
        software_tests_passed=482,market_requests=3,rows_checked=74929,bars_checked=4,binary_fields_checked=709616,
        witnesses_matched=5401,missing_complete_witnesses=8368,ambiguous_witnesses=0,all_four_relative_hypotheses_passed=True,
        all_overlap_non_flag_fields_equal=True,overlapping_flag_changes=8368,unknown_flag_bits_interpreted=False,
        prior_033_diagnostic_passed=False,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=documents[1],next_plan_executed=False))
    print(json.dumps(dict(review_integrity_passed=True,diagnostic_passed=False,overlapping_flag_changes=8368)))


def snapshot():
    checked=sealed(REVIEW);assert checked['review_integrity_passed'] and checked['diagnostic_passed'] is False
    API['prior_verify'](allow_handoff=True);ledger=API['verify']()
    for path,key in (('analysis','analysis_sha256'),('checks','checks_sha256'),('post-result-differences','post_result_differences_sha256')):
        assert sha(ROOT/('reports/fresh-replication-035-'+path+'.json'))==checked[key]
    for name,h in (checked['documentation_bindings']|checked['output_bindings']).items():assert sha(ROOT/name)==h,name
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*035*.md','docs/DATA-QUALIFICATION-036-PLAN.md','scripts/*035*.py',
                    'src/forex_demo_lab/*035.py','tests/*035*.py'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/fresh-replication-035*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    groups['four_hour_input_bindings']={p.relative_to(ROOT).as_posix():sha(p) for p in API['OUTPUT'].iterdir() if p.is_file()}
    already={n:h for v in groups.values() for n,h in v.items()}
    for name,h in ledger['bindings'].items():
        if name in already:assert already[name]==h,name
        else:groups['four_hour_input_bindings'][name]=h
    bindings={n:h for v in groups.values() for n,h in v.items()};assert len(bindings)==sum(map(len,groups.values()))
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
    write(FINAL,dict(kind='post_four_source_hour_replication_snapshot_035',**groups,archive_external_bindings=external,
        archive_members_verified=len(internal),external_bindings_verified=len(external),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),completed_utc=datetime.now(timezone.utc).isoformat(),
        software_tests_passed=482,market_requests=3,rows_checked=74929,bars_checked=4,binary_fields_checked=709616,
        checker_integrity_passed=True,diagnostic_passed=False,all_four_relative_hypotheses_passed=True,
        witnesses_matched=5401,missing_complete_witnesses=8368,overlapping_flag_changes=8368,unknown_flag_bits_interpreted=False,
        prior_033_diagnostic_passed=False,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('differences','handoff','review','snapshot'))
    {'differences':differences,'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
