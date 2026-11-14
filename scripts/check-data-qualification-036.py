"""Independent overlap, attribution/budget and unresolved-gate reconstruction."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import runpy
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]


def main():
    api=runpy.run_path(str(ROOT/'scripts/data-qualification-036.py'));ledger=api['verify']()
    assessment=api['sealed'](api['OUTPUT']);research=api['sealed'](ROOT/'reports/data-qualification-036-research.json')
    declaration=json.loads(api['DECLARATION'].read_text())
    assert assessment['ledger_sha256']==api['sha'](api['LEDGER']) and assessment['research_sha256']==api['sha'](ROOT/'reports/data-qualification-036-research.json')
    assert ledger['research_declaration_sha256']==api['sha'](api['DECLARATION'])
    reservation=api['sealed'](ROOT/'reports/data-qualification-036-reservation.json')
    assert reservation==dict(version=ledger['version'],ledger_sha256=api['sha'](api['LEDGER']),maximum_market_requests=0,
        research_budget=dict(search_queries=4,opens=12,finds=8),orders_available=False)
    counts=Counter();queries=[];opens=[];finds=[]
    for i,a in enumerate(research['actions']):
        assert a['action_index']==i and a['kind'] in ('search','open','find')
        assert datetime.fromisoformat(a['retrieved_utc']).utcoffset().total_seconds()==0
        counts[a['kind']]+=1
        if a['kind']=='search':
            assert a['query'] in declaration['search_queries'] and a['domains']==['mql5.com','metatrader5.com']
            queries.append(a['query'])
        else:
            p=urlsplit(a['url']);assert p.scheme=='https' and p.hostname in ('www.mql5.com','mql5.com','www.metatrader5.com','metatrader5.com')
            assert p.username is None and p.password is None and '/forum/' not in p.path
            assert a['url'] in declaration['target_pages']
            if a['kind']=='open':assert a['status'] in ('retrieved','unavailable');opens.append(a['url'])
            else:assert a['url'] in opens and a['pattern'] in declaration['find_patterns'];finds.append((a['url'],a['pattern']))
    assert len(set(queries))==len(queries)<=4 and len(set(opens))==len(opens)<=12 and len(set(finds))==len(finds)<=8
    findings={f['id']:f for f in research['findings']};assert len(findings)==len(research['findings'])
    for f in findings.values():
        assert f['classification'] in ('documented','not_found_in_reviewed_pages','inference','unresolved') and f['summary'] and f['source_urls']
        for url in f['source_urls']:assert any(a['kind']=='open' and a['url']==url and a['status']=='retrieved' for a in research['actions'])
    assert assessment['action_counts']==dict(search_queries=counts['search'],opens=counts['open'],finds=counts['find'],findings=len(findings))
    reader=runpy.run_path(str(ROOT/'scripts/check-fresh-replication-035.py'))
    a=api['sealed'](ROOT/'data/fresh-context-033/capture.json');b=api['sealed'](ROOT/'data/fresh-replication-035/capture.json')
    old=reader['decode'](ROOT/'data/fresh-context-033','ticks',a['reads'][1])
    new=reader['decode'](ROOT/'data/fresh-replication-035','ticks',b['reads'][1])
    bars=reader['decode'](ROOT/'data/fresh-replication-035','bars',b['reads'][2])
    indices=[i for i,r in enumerate(new) if 1791291600000<=r['time_msc']<1791295200000]
    assert len(indices)==len(old)==13769
    fields=('time','bid','ask','last','volume','time_msc','flags','volume_real')
    fields_changed=Counter();transitions=Counter();xors=Counter();changes=[];nonflag=[]
    lookup={}
    for j,r in enumerate(new):lookup.setdefault(tuple(r[k] for k in fields),[]).append(j)
    witnesses=[]
    for i,j in enumerate(indices):
        before,after=old[i],new[j];different=[k for k in fields if before[k]!=after[k]]
        fields_changed.update(different);transitions[(before['flags'],after['flags'])]+=1;xors[before['flags']^after['flags']]+=1
        if any(k!='flags' for k in different):nonflag.append(i)
        if different:changes.append(dict(prior_original_row_index=i,new_original_row_index=j,raw_time_msc=before['time_msc'],
            changed_fields=different,flags_before=before['flags'],flags_after=after['flags'],flag_xor=before['flags']^after['flags']))
        matched=lookup.get(tuple(before[k] for k in fields),[])
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matched,status='matched' if len(matched)==1 else 'ambiguous' if matched else 'missing'))
    expected=dict(old_original_rows=len(old),new_overlapping_rows=len(indices),non_flag_fields_compared=7*len(old),
        all_non_flag_fields_equal=not nonflag,non_flag_mismatch_prior_indices=nonflag,changed_field_counts=dict(sorted(fields_changed.items())),
        flag_xor_histogram=dict(sorted(xors.items())),flag_transitions=[dict(flags_before=a,flags_after=b,rows=n) for (a,b),n in sorted(transitions.items())],
        changed_rows=changes,unchanged_complete_ordinal_pairs=len(old)-len(changes),changed_complete_ordinal_pairs=len(changes),
        complete_witnesses=witnesses,complete_witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        complete_witnesses_missing=sum(w['status']=='missing' for w in witnesses),ambiguous_complete_witnesses=sum(w['status']=='ambiguous' for w in witnesses),
        ordinal_alignment_replaces_complete_identity=False,unknown_flag_bits_interpreted=False)
    assert json.loads(json.dumps(expected))==assessment['overlap']
    prior=api['sealed'](ROOT/'reports/fresh-replication-035-post-result-differences.json')
    for key in ('changed_rows','flag_transitions','flag_xor_histogram','changed_field_counts','all_non_flag_fields_equal'):assert assessment['overlap'][key]==prior[key]
    gates=assessment['qualification_matrix']
    assert [r['gate'] for r in gates]==['original_integrity','relative_feed_prices_volumes','metadata_repeatability','source_clock_sessions','upstream_completeness','historical_executable_costs']
    assert [r['status'] for r in gates]==['observed_pass','observed_pass','observed_failure','unresolved','unresolved','unresolved']
    for gate in gates:
        assert gate['limitation'] and gate['minimal_missing_evidence'] and (gate['local_evidence'] or gate['finding_ids'])
        assert all(p in ledger['bindings'] for p in gate['local_evidence']) and all(f in findings for f in gate['finding_ids'])
    policy=assessment['proposed_data_policy'];assert policy['proposal_only'] is True and policy['implemented'] is False and policy['preserve_every_original_revision'] is True
    for k in ('original_overwrite_permitted','source_blending_permitted','flag_masking_of_originals_permitted','complete_identity_gate_changes_permitted',
              'clock_normalization_permitted','qualified_publication_permitted','performance_testing_permitted','fresh_performance_eligible','annual_eligible','orders_available'):
        assert policy[k] is False
    for report in (assessment,research):assert report['market_requests']==report['strategy_replays']==0 and report['orders_available'] is False
    for k in ('prior_033_diagnostic_passed','prior_035_diagnostic_passed','unknown_flag_bits_interpreted','fresh_performance_eligible','annual_eligible'):assert assessment[k] is False
    assert assessment['binary_fields_compared']==8*(len(old)+len(new)+len(bars))==709616
    assert api['sealed'](ROOT/'reports/fresh-replication-035-checks.json')['diagnostic_passed'] is False
    assert api['sealed'](ROOT/'reports/fresh-context-033-checks.json')['diagnostic_passed'] is False
    api['write'](ROOT/'reports/data-qualification-036-checks.json',dict(kind='independent_qualification_evidence_check_036',checker_passed=True,
        assessment_sha256=api['sha'](api['OUTPUT']),research_sha256=api['sha'](ROOT/'reports/data-qualification-036-research.json'),
        ledger_sha256=api['sha'](api['LEDGER']),action_counts=assessment['action_counts'],binary_fields_checked=709616,
        changed_flag_rows=8368,complete_witnesses_matched=5401,complete_witnesses_missing=8368,gates_checked=6,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,market_requests=0,strategy_replays=0,
        fresh_performance_eligible=False,annual_eligible=False,orders_available=False))
    print(json.dumps(dict(checker_passed=True,fields_checked=709616,gates_checked=6,action_counts=assessment['action_counts'],market_requests=0)))


if __name__=='__main__':main()
