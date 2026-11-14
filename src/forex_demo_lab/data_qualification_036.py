"""Offline overlap lineage and bounded primary-documentation evidence review."""
from collections import Counter,defaultdict
from datetime import datetime
from urllib.parse import urlparse

VERSION='qualification_review_036_v1'
FIELDS=('time','bid','ask','last','volume','time_msc','flags','volume_real')
OVERLAP_START,OVERLAP_END=1791291600000,1791295200000
GATES=('original_integrity','relative_feed_prices_volumes','metadata_repeatability',
       'source_clock_sessions','upstream_completeness','historical_executable_costs')


def allowed_url(url,declared):
    p=urlparse(url)
    host=(p.hostname or '').removeprefix('www.')
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443) or host not in declared['allowed_domains']:
        raise ValueError('Only declared primary HTTPS domains permitted')
    if '/forum/' in p.path or not (p.path.startswith('/en/docs/') or p.path.startswith('/en/book/') or host=='metatrader5.com'):
        raise ValueError('Community or undeclared source scope')
    return url


def validate_research(research,declared):
    if research['version']!=VERSION or declared['version']!=VERSION:raise ValueError('Version mismatch')
    if declared['allowed_domains']!=['mql5.com','metatrader5.com'] or (
            declared['maximum_search_queries'],declared['maximum_opens'],declared['maximum_finds'])!=(4,12,8):
        raise ValueError('Research authority or budget changed')
    actions=research['actions'];counts=Counter()
    searches=[];opened=set();finds=[]
    for i,a in enumerate(actions):
        if a['action_index']!=i or a['kind'] not in ('search','open','find'):raise ValueError('Invalid action order or kind')
        stamp=datetime.fromisoformat(a['retrieved_utc'])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds()!=0:raise ValueError('UTC action receipt required')
        counts[a['kind']]+=1
        if a['kind']=='search':
            if a['query'] not in declared['search_queries'] or a['domains']!=declared['allowed_domains']:
                raise ValueError('Undeclared search or domains')
            searches.append(a['query'])
        else:
            url=allowed_url(a['url'],declared)
            if url not in declared['target_pages']:raise ValueError('Undeclared target')
            if a['kind']=='open':
                if url in opened:raise ValueError('Access retry unavailable')
                if a['status'] not in ('retrieved','unavailable'):raise ValueError('Invalid retrieval outcome')
                opened.add(url)
            else:
                if url not in opened or a['pattern'] not in declared['find_patterns']:raise ValueError('Undeclared find or unopened target')
                finds.append((url,a['pattern']))
    if len(searches)!=len(set(searches)) or len(finds)!=len(set(finds)):raise ValueError('Repeated research action')
    for kind,key in (('search','maximum_search_queries'),('open','maximum_opens'),('find','maximum_finds')):
        if counts[kind]>declared[key]:raise ValueError('Research budget exceeded')
    seen=set()
    for finding in research['findings']:
        if finding['id'] in seen:raise ValueError('Duplicate finding identity')
        seen.add(finding['id'])
        if finding['classification'] not in ('documented','not_found_in_reviewed_pages','inference','unresolved'):
            raise ValueError('Unsupported evidence classification')
        if not finding['summary'] or not finding['source_urls']:raise ValueError('Attribution missing')
        for url in finding['source_urls']:
            allowed_url(url,declared)
            if not any(a['kind']=='open' and a['url']==url and a['status']=='retrieved' for a in actions):
                raise ValueError('Finding has no successful primary retrieval')
    if research['market_requests']!=0 or research['strategy_replays']!=0 or research['orders_available'] is not False:
        raise ValueError('Review must have no execution or market requests')
    return dict(search_queries=counts['search'],opens=counts['open'],finds=counts['find'],findings=len(seen))


def overlap(old,new):
    current=[(i,r) for i,r in enumerate(new) if OVERLAP_START<=r['time_msc']<OVERLAP_END]
    if len(old)!=len(current):raise ValueError('Ordinal overlap count differs; cannot assume alignment')
    hist=Counter();xorhist=Counter();fieldhist=Counter();changed=[];lookup=defaultdict(list)
    for i,r in enumerate(new):lookup[tuple(r[k] for k in FIELDS)].append(i)
    witnesses=[];nonflag_mismatch_indices=[]
    for i,(a,(j,b)) in enumerate(zip(old,current)):
        different=[k for k in FIELDS if a[k]!=b[k]]
        fieldhist.update(different);hist[(a['flags'],b['flags'])]+=1;xor=a['flags']^b['flags'];xorhist[xor]+=1
        if any(k!='flags' for k in different):nonflag_mismatch_indices.append(i)
        if different:changed.append(dict(prior_original_row_index=i,new_original_row_index=j,raw_time_msc=a['time_msc'],
            changed_fields=different,flags_before=a['flags'],flags_after=b['flags'],flag_xor=xor))
        matches=lookup[tuple(a[k] for k in FIELDS)]
        witnesses.append(dict(prior_original_row_index=i,matching_original_row_indices=matches,
            status='missing' if not matches else 'ambiguous' if len(matches)>1 else 'matched'))
    return dict(old_original_rows=len(old),new_overlapping_rows=len(current),non_flag_fields_compared=len(old)*7,
        all_non_flag_fields_equal=not nonflag_mismatch_indices,non_flag_mismatch_prior_indices=nonflag_mismatch_indices,
        changed_field_counts=dict(sorted(fieldhist.items())),flag_xor_histogram=dict(sorted(xorhist.items())),
        flag_transitions=[dict(flags_before=a,flags_after=b,rows=n) for (a,b),n in sorted(hist.items())],
        changed_rows=changed,unchanged_complete_ordinal_pairs=len(old)-len(changed),changed_complete_ordinal_pairs=len(changed),
        complete_witnesses=witnesses,complete_witnesses_matched=sum(w['status']=='matched' for w in witnesses),
        complete_witnesses_missing=sum(w['status']=='missing' for w in witnesses),ambiguous_complete_witnesses=sum(w['status']=='ambiguous' for w in witnesses),
        ordinal_alignment_replaces_complete_identity=False,unknown_flag_bits_interpreted=False)


def validate_matrix(matrix,bindings,research):
    if tuple(r['gate'] for r in matrix)!=GATES:raise ValueError('Fixed qualification gates required')
    sources={f['id']:f for f in research['findings']}
    for r in matrix:
        if r['status'] not in ('observed_pass','observed_failure','unresolved'):raise ValueError('Unsupported gate status')
        if r['evidence_class'] not in ('observed_equality','observed_contradiction','absent_provider_evidence','inference'):
            raise ValueError('Unsupported evidence class')
        if not r['local_evidence'] and not r['finding_ids']:raise ValueError('Gate evidence required')
        if any(p not in bindings for p in r['local_evidence']) or any(f not in sources for f in r['finding_ids']):
            raise ValueError('Unbound evidence or finding')
        if not r['limitation'] or not r['minimal_missing_evidence']:raise ValueError('Gate limitations required')
    if matrix[2]['status']!='observed_failure' or any(r['status']!='unresolved' for r in matrix[3:]):
        raise ValueError('Provider qualification cannot be promoted by generic documentation')
    return True


def policy():
    return dict(proposal_only=True,implemented=False,preserve_every_original_revision=True,
        original_overwrite_permitted=False,source_blending_permitted=False,flag_masking_of_originals_permitted=False,
        derived_known_mask_column='Only separately named, hash-bound derived data with complete original lineage; no replacement of full flags',
        complete_identity_gate_changes_permitted=False,clock_normalization_permitted=False,qualified_publication_permitted=False,
        performance_testing_permitted=False,fresh_performance_eligible=False,annual_eligible=False,orders_available=False)
