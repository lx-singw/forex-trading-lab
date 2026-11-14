"""Seal official findings, unchanged gates, policy proposal and source snapshot."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/data-qualification-036.py'))
sha,write,sealed=API['sha'],API['write'],API['sealed']
HANDOFF=API['HANDOFF']
REVIEW=ROOT/'reports/data-qualification-036-review.json'
FINAL=ROOT/'reports/data-qualification-036-final-source.json'


def evidence():
    ledger=API['verify']();tests=sealed(ROOT/'reports/data-qualification-036-tests.json')
    assessment=sealed(API['OUTPUT']);research=sealed(ROOT/'reports/data-qualification-036-research.json')
    checks=sealed(ROOT/'reports/data-qualification-036-checks.json')
    assert tests['passed'] and tests['tests_run']==tests['tests_passed']==498 and tests['new_tests']==16
    assert checks['checker_passed'] and checks['assessment_sha256']==sha(API['OUTPUT'])
    assert checks['research_sha256']==assessment['research_sha256']==sha(ROOT/'reports/data-qualification-036-research.json')
    assert checks['ledger_sha256']==assessment['ledger_sha256']==sha(API['LEDGER'])
    assert checks['binary_fields_checked']==assessment['binary_fields_compared']==709616
    assert checks['action_counts']==assessment['action_counts']==dict(search_queries=4,opens=8,finds=8,findings=6)
    assert len(research['actions'])==20 and checks['gates_checked']==6
    assert [r['status'] for r in assessment['qualification_matrix']]==['observed_pass','observed_pass','observed_failure','unresolved','unresolved','unresolved']
    o=assessment['overlap'];assert o['all_non_flag_fields_equal'] and o['changed_complete_ordinal_pairs']==8368
    assert o['complete_witnesses_matched']==5401 and o['complete_witnesses_missing']==8368
    assert o['ambiguous_complete_witnesses']==0 and o['ordinal_alignment_replaces_complete_identity'] is False
    assert assessment['proposed_data_policy']['proposal_only'] is True and assessment['proposed_data_policy']['implemented'] is False
    for report in (assessment,checks,research):assert report['market_requests']==report['strategy_replays']==0 and report['orders_available'] is False
    assert sealed(ROOT/'reports/fresh-replication-035-checks.json')['diagnostic_passed'] is False
    assert sealed(ROOT/'reports/fresh-context-033-checks.json')['diagnostic_passed'] is False
    return ledger,assessment,research,checks


def handoff():
    evidence()
    text=('Latest — 2026-10-06: source semantics/qualification review036 complete. Read DATA-QUALIFICATION-036-RESULTS.md. '
        '498 tests (16 new),100 frozen inputs; prior1,049 bindings/1,005 ZIP members/44 external inputs verified. '
        'Zero market calls/connections/terminal actions/history downloads/returns/orders. Four declared queries, '
        'eight official MetaQuotes opens/eight finds, six attributed findings; budgets/primary sources checked. '
        'Official Python example contains128-bearing130/134 flags, but reviewed flag tables do not define128/1024; '
        'remaining bits and revision cause stay unresolved. Docs describe UTC returns and synchronization/partial '
        'history outcomes, not provider-specific certification.709,616 fields/all overlap identities rechecked: '
        'all seven non-flag fields/order stable;8,368 flags revised,5,401 full records match, old033/035 failures retained. '
        'Six gates: original integrity/relative feed observed pass; metadata repeatability observed failure; '
        'clock/session, upstream completeness and historical executable costs unresolved. Raw/derived policy is '
        'a proposal only, no normalization/masking/publication/gate changes. Fresh/annual eligibility false; '
        'consumed2025/reservedNov–Dec2026/provider stops unchanged. Next CLOCK-REFERENCE-037-PLAN.md declares '
        'bounded read-only current clock references and at most one guarded demo quote, not executed. '
        'Earlier entries are historical.\n\n')
    for name in HANDOFF:
        path=ROOT/name;old=path.read_text();split=old.index('\n')+1
        path.write_text(old[:split]+'\n'+text+old[split:])
    print(json.dumps(dict(handoff_updated=True,market_requests=0)))


def review():
    previous=API['prior_verify'](allow_handoff=True);ledger,assessment,research,checks=evidence()
    documents=('docs/DATA-QUALIFICATION-036-RESULTS.md','docs/RAW-DERIVED-POLICY-036.md',
               'docs/CLOCK-REFERENCE-037-PLAN.md','scripts/finalize-data-qualification-036.py')
    for name in HANDOFF:assert 'DATA-QUALIFICATION-036-RESULTS.md' in (ROOT/name).read_text()
    assert 'not executed' in (ROOT/documents[2]).read_text() and 'not implemented' in (ROOT/documents[1]).read_text()
    write(REVIEW,dict(kind='post_source_qualification_review_036',review_integrity_passed=True,
        prior_snapshot_verification=previous,input_bindings_verified=len(ledger['bindings']),
        assessment_sha256=sha(API['OUTPUT']),research_sha256=sha(ROOT/'reports/data-qualification-036-research.json'),
        checks_sha256=sha(ROOT/'reports/data-qualification-036-checks.json'),documentation_bindings={n:sha(ROOT/n) for n in documents},
        software_tests_passed=498,binary_fields_checked=709616,gates_checked=6,action_counts=checks['action_counts'],
        metadata_repeatability_passed=False,source_clock_sessions_qualified=False,upstream_completeness_qualified=False,
        historical_executable_costs_qualified=False,policy_proposal_implemented=False,
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,unknown_flag_bits_interpreted=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=documents[2],next_plan_executed=False))
    print(json.dumps(dict(review_integrity_passed=True,gates_checked=6,market_requests=0,performance_eligible=False)))


def snapshot():
    checked=sealed(REVIEW);assert checked['review_integrity_passed'];API['prior_verify'](allow_handoff=True);ledger=API['verify']()
    for stem,key in (('assessment','assessment_sha256'),('research','research_sha256'),('checks','checks_sha256')):
        assert sha(ROOT/('reports/data-qualification-036-'+stem+'.json'))==checked[key]
    for name,h in checked['documentation_bindings'].items():assert sha(ROOT/name)==h,name
    prior=sealed(API['PRIOR']);groups={g:dict(v) for g,v in prior.items() if g.endswith('_bindings') and g!='archive_external_bindings'}
    for name in HANDOFF:groups['source_bindings'][name]=sha(ROOT/name)
    for pattern in ('docs/*036*.md','docs/CLOCK-REFERENCE-037-PLAN.md','scripts/*036*.py',
                    'src/forex_demo_lab/data_qualification_036.py','tests/*036*.py','config/research-actions-036.json'):
        for path in ROOT.glob(pattern):groups['source_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for path in ROOT.glob('reports/data-qualification-036*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    for suffix in ('.json','.sha256','.zip'):
        path=API['PRIOR'].with_suffix(suffix);groups['report_bindings'][path.relative_to(ROOT).as_posix()]=sha(path)
    groups['qualification_input_bindings']={}
    already={n:h for v in groups.values() for n,h in v.items()}
    for name,h in ledger['bindings'].items():
        if name in already:assert already[name]==h,name
        else:groups['qualification_input_bindings'][name]=h
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
    write(FINAL,dict(kind='post_source_qualification_snapshot_036',**groups,archive_external_bindings=external,
        archive_members_verified=len(internal),external_bindings_verified=len(external),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        snapshot_scope='Sources/reports/small originals archived; older data/ZIPs/timezone/Windows runtime externally hash-bound and required',
        previous_snapshot=API['PRIOR'].relative_to(ROOT).as_posix(),previous_snapshot_sha256=sha(API['PRIOR']),completed_utc=datetime.now(timezone.utc).isoformat(),
        software_tests_passed=498,binary_fields_checked=709616,gates_checked=6,action_counts=checked['action_counts'],
        prior_033_diagnostic_passed=False,prior_035_diagnostic_passed=False,policy_proposal_implemented=False,
        source_clock_sessions_qualified=False,upstream_completeness_qualified=False,historical_executable_costs_qualified=False,
        market_requests=0,strategy_replays=0,fresh_performance_eligible=False,annual_eligible=False,orders_available=False,
        next_plan=checked['next_plan'],next_plan_executed=False))
    print(json.dumps(dict(bindings=len(bindings),archive_members=len(internal),external_bindings=len(external),manifest_sha256=sha(FINAL))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('handoff','review','snapshot'))
    {'handoff':handoff,'review':review,'snapshot':snapshot}[parser.parse_args().action]()
