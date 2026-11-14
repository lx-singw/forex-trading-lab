"""Exclusive offline metadata review. No simulation, selector or market API."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT=Path(__file__).resolve().parents[1]
API=runpy.run_path(str(ROOT/'scripts/source-feasibility-090.py'))
sha,sealed,write,bound=(API[k] for k in ('sha','sealed','write','bound'))
HANDOFF,ARCHIVE,ZERO,FALSE=(API[k] for k in ('HANDOFF','ARCHIVE','ZERO','FALSE'))
PREFIX='research-readiness-091';LEDGER=ROOT/f'reports/{PREFIX}-ledger.json'
PRIOR=ROOT/'reports/source-feasibility-090-final-source.json'
REVIEW=ROOT/'reports/source-feasibility-090-completion-review.json'
POLICY=ROOT/'docs/RESEARCH-091-POLICY.md'
PLAN=ROOT/'docs/ARCHIVED-EVIDENCE-092-PLAN.md'
OWN=('scripts/research-readiness-091.py','docs/RESEARCH-091-POLICY.md','docs/ARCHIVED-EVIDENCE-092-PLAN.md')
DOCS=('STRATEGY-RESEARCH-008','COMPARISON-008-RESULTS','HISTORY-009-RESULTS',
    'RECOVERY-010-RESULTS','CLOCK-011-RESULTS','CLOCK-012-RESULTS','CORRECTION-013-RESULTS',
    'WALK-FORWARD-014-RESULTS','NORMALIZATION-015-RESULTS','REFERENCE-016-RESULTS',
    'LABELS-017-RESULTS','WALK-FORWARD-020-RESULTS','SOURCE-INVENTORY-022-RESULTS',
    'EXNESS-COMPARISON-025-RESULTS','EXNESS-EVIDENCE-026-RESULTS',
    'STRATEGY-EXPERIMENT-028-RESULTS','TRADE-PATH-029-RESULTS','EXIT-EXPERIMENT-030-RESULTS',
    'FRESH-DATA-031-RESULTS','FRESH-TICKS-032-RESULTS','FRESH-CONTEXT-033-RESULTS',
    'FRESH-FLAGS-034-RESULTS','FRESH-REPLICATION-035-RESULTS','DATA-QUALIFICATION-036-RESULTS',
    'CLOCK-REFERENCE-037-RESULTS','CLOCK-SEMANTICS-038-RESULTS','RESEARCH-091-PLAN')
REPORTS=('comparison-008-summary','comparison-008-audit','history-009-review','recovery-010-review',
    'correction-013-review','normalization-015-review','reference-016b-review','labels-017-review',
    'walk-forward-020-market-gates/review','strategy-experiment-028-summary',
    'strategy-experiment-028-checks','strategy-experiment-028-review','trade-path-029-summary',
    'exit-experiment-030-summary','exit-experiment-030-checks','exit-experiment-030-review',
    'fresh-data-031-inventory','fresh-data-031-probe','fresh-replication-035-checks',
    'data-qualification-036-assessment','clock-reference-037-checks','clock-semantics-038-audit')
SOURCES=('strategies','selection','walk_forward_metrics','strategy_experiment_028','exit_experiment_030')
INPUTS=tuple([*OWN,*('docs/'+n+'.md' for n in DOCS),
    *('reports/'+n+'.json' for n in REPORTS),*('src/forex_demo_lab/'+n+'.py' for n in SOURCES),
    'config/research-candidates-008.json','config/tick-pilot-003.json','config/tick-pilot-003-adverse.json'])


def load(name):return json.loads((ROOT/name).read_text())
def report(name):return load('reports/'+name+'.json')
def candidates(name):
    tree=ast.parse((ROOT/'src/forex_demo_lab'/f'{name}.py').read_text())
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='CANDIDATES' for t in n.targets)))


def prior():
    API['verify']();r=sealed(PRIOR);v=sealed(REVIEW)
    assert sha(PRIOR)=='3e5d0b2074eff9c1f7893d9f4145f37c883c87b25ea4be09704e0db894e107e3'
    assert v['review_passed'] and v['final_source_sha256']==sha(PRIOR)
    assert (v['bindings_verified'],v['archive_members_verified'],v['tests_passed'])==(2849,2634,1942)
    assert ARCHIVE(PRIOR,r)==2634
    for n,h in r['source_and_evidence_bindings'].items():
        if n not in HANDOFF:assert sha(bound(n))==h,n
    return r


def freeze():
    r=prior();b=dict(r['source_and_evidence_bindings'])
    for n in HANDOFF:b.pop(n,None)
    for p in (PRIOR,PRIOR.with_suffix('.sha256'),PRIOR.with_suffix('.zip'),REVIEW,REVIEW.with_suffix('.sha256')):
        b[p.relative_to(ROOT).as_posix()]=sha(p)
    inputs={n:sha(ROOT/n) for n in INPUTS}
    for n,h in inputs.items():
        if n in b:assert b[n]==h,n
    b.update(inputs)
    write(LEDGER,dict(bindings=b,audit_inputs=inputs,prior_source_sha256=sha(PRIOR),
        policy_sha256=sha(POLICY),next_plan_sha256=sha(PLAN),
        maximum_audits=1,maximum_checks=1,maximum_full_regressions=0,
        latest_retained_tests=1942,tests_run_this_phase=0,new_tests=0,
        historical_price_rows_read=0,strategy_replays=0,new_returns_computed=0,
        prior_failure_records_preserved=True,**ZERO,**FALSE))
    print(json.dumps(dict(frozen=True,bindings=len(b),audit_inputs=len(inputs))))


def verify():
    l=sealed(LEDGER)
    for n,h in l['bindings'].items():assert sha(bound(n))==h,n
    assert l['audit_inputs']=={n:sha(ROOT/n) for n in INPUTS}
    assert l['prior_source_sha256']==sha(PRIOR) and l['policy_sha256']==sha(POLICY)
    assert l['next_plan_sha256']==sha(PLAN)
    return l


def facts():
    s8=report('comparison-008-summary');s28=report('strategy-experiment-028-summary')
    s30=report('exit-experiment-030-summary');r30=report('exit-experiment-030-review')
    rows=[]
    for s in (s8,s28,s30):
        assert len(s['scenarios'])==30
        keys={(x['sample'],x['candidate'],x['cost']) for x in s['scenarios']}
        assert len(keys)==30 and {x[0] for x in keys}=={'january','april','july'}
        assert {x[2] for x in keys}=={'base','adverse'}
    for row in s28['scenarios']:
        if row['candidate'] in ('C05','C06'):
            rows.append({k:row[k] for k in ('sample','candidate','cost','net_pnl','trades','corrected_tick_drawdown')})
    paths=[x for x in report('trade-path-029-summary')['scenarios'] if x['candidate'] in ('C05','C06') and x['net_pnl']>0]
    original=report('history-009-review');norm=report('normalization-015-review')
    q=report('data-qualification-036-assessment');fresh=report('fresh-data-031-inventory')
    snap=report('fresh-data-031-probe')['contract_snapshot']
    matrix=[dict(area=area,status=status,evidence=evidence,missing=missing) for area,status,evidence,missing in (
        ('Risk/fill/restart software','software_verified_not_market_approval',
            ['reports/source-feasibility-090-completion-review.json'],
            'Qualified inputs and historical/executable evidence; synthetic tests grant no returns or orders.'),
        ('Chronological evaluation','implemented_for_C00_through_C04_but_inputs_blocked',
            ['docs/WALK-FORWARD-020-RESULTS.md','reports/walk-forward-020-market-gates/review.json'],
            'Year-specific clock/lineage/corroboration/coverage approval for all2020–2023 years.'),
        ('Challenger integration','C05_through_C08_development_only',
            ['src/forex_demo_lab/strategies.py','src/forex_demo_lab/strategy_experiment_028.py','src/forex_demo_lab/exit_experiment_030.py'],
            'Separate frozen chronological candidate/selection protocol; never silently widen009/020.'),
        ('Observed strategy performance','mixed_reused_development',
            ['reports/comparison-008-summary.json','reports/strategy-experiment-028-summary.json','reports/trade-path-029-summary.json'],
            'Broader qualified chronological evaluation; concentration and adverse-cost evidence, no promotion.'),
        ('Protective stop','mixed_no_general_improvement',
            ['reports/exit-experiment-030-review.json'],
            'No further threshold search on these windows; qualified fresh validation first.'),
        ('Historical time basis','unresolved_source_document_conflict',
            ['docs/HISTORY-009-RESULTS.md','docs/EXNESS-EVIDENCE-026-RESULTS.md','reports/normalization-015-review.json'],
            'Dated provider/file/account clock/DST evidence plus independent corroboration of observed conflicts.'),
        ('Coverage and upstream lineage','unresolved_no_global_approval',
            ['reports/recovery-010-review.json','docs/EXNESS-COMPARISON-025-RESULTS.md','docs/EXNESS-EVIDENCE-026-RESULTS.md'],
            'Source-specific gap/session/outage and feed-contributor evidence; no assumed market closures/blending.'),
        ('Fresh-source qualification','repeatability_failed_clock_unqualified',
            ['reports/fresh-replication-035-checks.json','reports/data-qualification-036-assessment.json','reports/clock-semantics-038-audit.json'],
            'Provider revision/extra-bit semantics, calibrated time basis and upstream completeness.'),
        ('Execution costs','hypothetical_historical_contract_unverified',
            ['config/tick-pilot-003.json','config/tick-pilot-003-adverse.json','reports/fresh-data-031-probe.json'],
            'Date/account-effective fees, swap units/conversion/rollover calendar and executable bid/ask/slippage evidence.'),
        ('Unseen validation','not_completed',
            ['config/research-candidates-008.json','reports/fresh-data-031-inventory.json'],
            'Freeze rules/acceptance before eligible unseen evaluation;2025 remains consumed and Nov–Dec2026 reserved.'),
        ('Native execution','cannot_proceed_under_phase_090_contract',
            ['docs/SOURCE-FEASIBILITY-090-RESULTS.md','reports/source-feasibility-090-completion-review.json'],
            'Closed native branch; no dated reader renewal, terminal experiment or order activation.'))]
    return dict(version='research_readiness_091_v1',kind='offline_frozen_evidence_audit',
        copied_development_rows=rows,comparison008_positive_cases=sum(x['metrics']['net_pnl']>0 for x in s8['scenarios']),
        comparison008_negative_cases=sum(x['metrics']['net_pnl']<0 for x in s8['scenarios']),
        challenger028_positive_cases=sum(x['net_pnl']>0 for x in rows),challenger028_cases=len(rows),
        positive_challenger_cells_negative_without_largest_winner=sum(x['net_excluding_largest_winner']<0 for x in paths),
        positive_challenger_cells=len(paths),
        protection030_improved_cells=sum(x['net_pnl_difference']>0 for x in r30['entry_comparisons']),
        protection030_worsened_cells=sum(x['net_pnl_difference']<0 for x in r30['entry_comparisons']),
        protection030_clipped_target_cases=sum(len(x['clipped_shared_target_winners']) for x in r30['entry_comparisons']),
        observed_case_counts_are_not_independent_trials=True,monthly_capital_is_independent=True,
        annual_chronological_candidates=list(candidates('strategies')),
        development028_candidates=list(candidates('strategy_experiment_028')),
        development030_candidates=list(candidates('exit_experiment_030')),
        original_months=len(original['months']),original_rows_previously_reviewed=original['rows_examined'],
        ordering_failure_months=original['structural_failures'],diagnostic_replay_rows_collapsed=norm['collapsed_replay_rows'],
        unclassified_gaps_over_one_hour=len(norm['gaps_over_one_hour']),
        fresh_catalog_records=len(fresh['records']),qualified_datasets_in_fixed031_catalog=fresh['qualified_fresh_datasets_in_this_catalog'],
        qualification036_statuses={x['gate']:x['status'] for x in q['qualification_matrix']},
        declared_costs={k:load('config/tick-pilot-003'+('' if k=='base' else '-adverse')+'.json') for k in ('base','adverse')},
        saved_current031_contract={k:snap[k] for k in ('swap_mode','swap_long','swap_short','swap_rollover3days','trade_contract_size')},
        current_contract_is_not_historical_cost_certification=True,
        development_windows=['2024 January/April/July partial samples after201 observed hours; repeatedly reused'],
        historical_fold_contract={'A':'2020–2021 training;2022 test','B':'2021–2022 training;2023 test'},
        excluded_data={'2025':'consumed;excluded from optimization','November–December2026':'reserved;unexamined',
            'October':'quarantine and failed historical reviews preserved'},
        matrix=matrix,native_branch_closed_under_contract=True,
        frozen030_document_has_malformed_currency_annotations='/bin/bash' in (ROOT/'docs/EXIT-EXPERIMENT-030-RESULTS.md').read_text(),
        monetary_values_copied_from_hash_bound_json=True,
        historical_price_rows_read=0,strategy_replays=0,new_returns_computed=0,
        selection_authorized=False,candidate_promoted=False,
        latest_retained_tests=1942,tests_run_this_phase=0,new_tests=0,
        next_plan='docs/ARCHIVED-EVIDENCE-092-PLAN.md',next_plan_executed=False,**ZERO,**FALSE)


def validate(r,bindings):
    assert (r['comparison008_positive_cases'],r['comparison008_negative_cases'])==(12,18)
    assert (r['challenger028_positive_cases'],r['challenger028_cases'])==(8,12)
    assert (r['positive_challenger_cells'],r['positive_challenger_cells_negative_without_largest_winner'])==(8,8)
    assert (r['protection030_improved_cells'],r['protection030_worsened_cells'],r['protection030_clipped_target_cases'])==(5,7,12)
    assert r['annual_chronological_candidates']==['C00','C01','C02','C03','C04']
    assert r['development028_candidates']==['C00','C02','C04','C05','C06']
    assert r['development030_candidates']==['C00','C05','C06','C07','C08']
    tree=ast.parse((ROOT/'src/forex_demo_lab/walk_forward_metrics.py').read_text())
    assert any(isinstance(n,ast.ImportFrom) and n.level==1 and n.module=='strategies'
        and any(x.name=='CANDIDATES' for x in n.names) for n in tree.body)
    for cost,fee,slip,long_swap,short_swap in (('base',7,0.2,-3,-1.5),('adverse',10,0.5,-6,-3)):
        cfg=r['declared_costs'][cost]
        assert (cfg['commission_per_lot_round_turn'],cfg['slippage_pips'],cfg['swap_long_per_lot'],cfg['swap_short_per_lot'])==(fee,slip,long_swap,short_swap)
        assert (cfg['initial_equity'],cfg['contract_size'],cfg['lot_step'],cfg['leverage'])==(10000,100000,0.01,10)
        assert (cfg['risk_fraction'],cfg['daily_loss_fraction'],cfg['triple_swap_weekday'],cfg['broker_timezone'])==(0.0025,0.01,2,'Etc/UTC')
    assert (r['original_months'],r['original_rows_previously_reviewed'],r['diagnostic_replay_rows_collapsed'],r['unclassified_gaps_over_one_hour'])==(48,110069388,12679,878)
    assert len(r['ordering_failure_months'])==4
    assert (r['fresh_catalog_records'],r['qualified_datasets_in_fixed031_catalog'])==(14,0)
    assert r['qualification036_statuses']==dict(original_integrity='observed_pass',relative_feed_prices_volumes='observed_pass',
        metadata_repeatability='observed_failure',source_clock_sessions='unresolved',upstream_completeness='unresolved',historical_executable_costs='unresolved')
    for summary,check,prefix in (('comparison-008-summary','comparison-008-audit','comparison-008'),
            ('strategy-experiment-028-summary','strategy-experiment-028-checks','strategy-experiment-028'),
            ('exit-experiment-030-summary','exit-experiment-030-checks','exit-experiment-030')):
        s=report(summary);c=report(check)
        assert c['summary_sha256']==sha(ROOT/f'reports/{summary}.json')
        for row in s['scenarios']:
            assert bindings[f"reports/{prefix}-{row['scenario']}.json"]==row['report_sha256']
    for name in ('history-009-review','recovery-010-review','normalization-015-review','reference-016b-review','labels-017-review'):
        assert report(name)['performance_evaluation_ready'] is False
    for name in ('strategy-experiment-028-summary','exit-experiment-030-summary','data-qualification-036-assessment','clock-semantics-038-audit'):
        v=report(name);assert v['annual_eligible'] is False and v['orders_available'] is False
    gates=report('walk-forward-020-market-gates/review')
    assert len(gates['cases'])==3 and all(x['status']=='blocked_before_data_iteration_and_performance' and not x['output_created'] for x in gates['cases'])
    assert len(r['matrix'])==11 and len({x['area'] for x in r['matrix']})==11
    for row in r['matrix']:
        for n in row['evidence']:assert n in bindings or n=='reports/source-feasibility-090-completion-review.json'
    assert r['observed_case_counts_are_not_independent_trials'] and r['monthly_capital_is_independent']
    assert r['native_branch_closed_under_contract'] and not r['selection_authorized'] and not r['candidate_promoted']
    assert r['frozen030_document_has_malformed_currency_annotations'] and r['monetary_values_copied_from_hash_bound_json']
    assert (r['latest_retained_tests'],r['tests_run_this_phase'],r['new_tests'])==(1942,0,0)
    assert (r['historical_price_rows_read'],r['strategy_replays'],r['new_returns_computed'])==(0,0,0)
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v


def audit():
    l=verify()
    write(ROOT/f'reports/{PREFIX}-audit-started.json',dict(audit_consumed=True,ledger_sha256=sha(LEDGER),**ZERO,**FALSE))
    r=facts();validate(r,l['bindings']);r['ledger_sha256']=sha(LEDGER)
    write(ROOT/f'reports/{PREFIX}-audit.json',r)
    print(json.dumps(dict(audited=True,matrix_rows=11,new_returns=0,new_tests=0)))


def check():
    l=verify();r=sealed(ROOT/f'reports/{PREFIX}-audit.json')
    assert r['ledger_sha256']==sha(LEDGER);validate(r,l['bindings'])
    assert {k:v for k,v in r.items() if k!='ledger_sha256'}==facts()
    write(ROOT/f'reports/{PREFIX}-checks.json',dict(checks_passed=True,audit_sha256=sha(ROOT/f'reports/{PREFIX}-audit.json'),
        ledger_sha256=sha(LEDGER),audit_inputs_verified=len(l['audit_inputs']),matrix_rows=11,
        latest_retained_tests=1942,tests_run_this_phase=0,new_tests=0,prior_failure_records_preserved=True,
        historical_price_rows_read=0,strategy_replays=0,new_returns_computed=0,**ZERO,**FALSE))
    print(json.dumps(dict(checks_passed=True,audit_inputs=len(l['audit_inputs']),tests_run=0)))


def seal():
    l=verify();c=sealed(ROOT/f'reports/{PREFIX}-checks.json');assert c['checks_passed'] and c['ledger_sha256']==sha(LEDGER)
    r=sealed(ROOT/f'reports/{PREFIX}-audit.json');result=ROOT/'docs/RESEARCH-091-RESULTS.md'
    with result.open('x') as f:f.write(result_text(r))
    b=dict(l['bindings'])
    for n in HANDOFF:
        p=ROOT/n;s=p.read_text();i=s.index('\n')+1;p.write_text(s[:i]+'\n'+LATEST_TEXT+s[i:]);b[n]=sha(p)
    b[result.relative_to(ROOT).as_posix()]=sha(result)
    for pattern in (f'reports/{PREFIX}-*.json',f'reports/{PREFIX}-*.sha256'):
        for p in ROOT.glob(pattern):b[p.relative_to(ROOT).as_posix()]=sha(p)
    for n,h in b.items():assert sha(bound(n))==h,n
    external={n:h for n,h in b.items() if n.startswith('/') or n.endswith('.zip') or
        n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n}
    internal={n:h for n,h in b.items() if n not in external};final=ROOT/f'reports/{PREFIX}-final-source.json'
    with zipfile.ZipFile(final.with_suffix('.zip'),'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in sorted(internal):z.write(ROOT/n,n)
    record=dict(source_and_evidence_bindings=b,archive_external_bindings=external,
        archive_sha256=sha(final.with_suffix('.zip')),archive_members_verified=len(internal),
        latest_retained_tests=1942,tests_run_this_phase=0,new_tests=0,matrix_rows=11,
        native_experiment_can_proceed=False,next_plan_executed=False,
        historical_price_rows_read=0,strategy_replays=0,new_returns_computed=0,**ZERO,**FALSE)
    ARCHIVE(final,record);write(final,record)
    print(json.dumps(dict(sealed=True,bindings=len(b),members=len(internal),sha256=sha(final))))


def review():
    l=verify();f=ROOT/f'reports/{PREFIX}-final-source.json';r=sealed(f);b=r['source_and_evidence_bindings']
    for n,h in b.items():assert sha(bound(n))==h,n
    members=ARCHIVE(f,r);assert all(b.get(n)==h for n,h in l['bindings'].items())
    c=sealed(ROOT/f'reports/{PREFIX}-checks.json');a=sealed(ROOT/f'reports/{PREFIX}-audit.json')
    assert c['checks_passed'] and c['ledger_sha256']==a['ledger_sha256']==sha(LEDGER)
    assert c['audit_sha256']==sha(ROOT/f'reports/{PREFIX}-audit.json');validate(a,b)
    assert (ROOT/'docs/RESEARCH-091-RESULTS.md').read_text()==result_text(a)
    assert not r['next_plan_executed'] and not r['native_experiment_can_proceed']
    for k,v in {**ZERO,**FALSE}.items():assert type(r[k]) is type(v) and r[k]==v
    write(ROOT/f'reports/{PREFIX}-completion-review.json',dict(review_passed=True,final_source_sha256=sha(f),
        bindings_verified=len(b),archive_members_verified=members,frozen_inputs_verified=len(l['bindings']),
        frozen_input_coverage_complete=True,audit_inputs_verified=len(l['audit_inputs']),matrix_rows=11,
        latest_retained_tests=1942,tests_run_this_phase=0,new_tests=0,prior_failure_records_preserved=True,
        next_plan_sha256=sha(PLAN),next_plan_executed=False,historical_price_rows_read=0,
        strategy_replays=0,new_returns_computed=0,**ZERO,**FALSE))
    print(json.dumps(dict(review_passed=True,bindings=len(b),members=members,matrix_rows=11,tests_run=0)))


def result_text(r):
    lines=['# Historical research readiness091 — complete, 2026-10-09','',
        'Some reused development samples gained after modeled costs. A robust unseen edge is unproven.',
        'The useful next prerequisite is dated source-clock/session evidence, followed by unresolved',
        'coverage, lineage and executable costs. No further terminal experiment is planned.','',
        '## Readiness matrix','', '| Area | Status | Missing evidence or next requirement |',
        '| --- | --- | --- |']
    for x in r['matrix']:lines.append('| '+x['area']+' | '+x['status'].replace('_',' ')+' | '+x['missing']+' |')
    lines.extend(['','Every row cites exact hash-bound evidence in `reports/research-readiness-091-audit.json`.',
        'Software/metadata integrity is distinct from data eligibility, trading performance and execution.','',
        '## Existing challenger results','',
        'These values are copied from028, not new replays. Each partial2024 window has separate',
        '$10,000 starting capital and 201 observed warmup hours. Costs and candidates reuse observations.',
        'No continuous investment return or independent-trial claim.','',
        '| Window | Candidate | Base net USD | Adverse net USD | Trades base/adverse |',
        '| --- | --- | ---: | ---: | ---: |'])
    for sample in ('january','april','july'):
        for candidate in ('C05','C06'):
            rows={x['cost']:x for x in r['copied_development_rows'] if x['sample']==sample and x['candidate']==candidate}
            lines.append(f"| {sample.title()} | {candidate} | {rows['base']['net_pnl']:+.2f} | {rows['adverse']['net_pnl']:+.2f} | {rows['base']['trades']}/{rows['adverse']['trades']} |")
    lines.extend(['',
        'Phase 008 recorded 12 positive and 18 negative cases. C05/C06 have 8 positive cells among 12, but',
        'both lose in April. All 8 positive challenger cells turn negative in phase 029 when their largest',
        'winner is excluded; this is a concentration diagnostic, not a rule to remove trades.',
        'Phase 028 already reports C05 diagnostic sums +$20.71 base /+$3.13 adverse across separately',
        'funded samples, not validation returns. C05 has 18 trades per cost setting, not a large sample.',
        'Phase 030 protection improves 5/12 and worsens 7/12 comparisons, clipping 12 shared target-winner',
        'cases. April improves; July worsens. No candidate is selected or promoted.','',
        'The annual phase-020 runner and selector still support C00–C04; C05–C08 exist in separate development',
        'engines. They require a separate frozen chronological protocol, not a silent config change.','',
        '## Data-use and evidence boundaries','',
        '| Data scope | Use already made | Current status |',
        '| --- | --- | --- |',
        '|2020–2023, all 48 months |110,069,388 rows inspected for quality; 12,679 replay rows collapsed only in diagnostics | Annual returns uncomputed; four original October ordering failures and 878 unclassified gaps over one hour remain |',
        '|2022/2023 chronological tests | Planned folds A: 2020–2021→2022 and B: 2021–2022→2023; software exercised with invented inputs | Market gate rejects 015/016B/017 before price iteration; no annual market approval |',
        '|2024 January/April/July | Repeated partial-window development in 008/028/029/030 | Already seen; further tuning cannot create unseen validation |',
        '|October | Existing quarantine/failed historical reviews | No reinterpretation or performance use |',
        '|2025 | Holdout already consumed | Excluded from optimization |',
        '|November–December 2026 | Reserved future validation | Unexamined; no scheduling/acquisition/use |',
        '|031–038 source samples | Integrity, relative-price, flags and clock diagnostics | Zero qualified datasets in the fixed 14-record catalog from 031; not an exhaustive statement about all sources |','',
        'Phase 015 monotonic chronology does not certify UTC. Phase 010 broker recovery has a truncated July hour;',
        'phase 025 independent-provider presence confirms disputed intervals contain quotes, without closing',
        'global clock/session/upstream gates. Phase 026 current documentation did not establish dated target',
        'applicability. Phase 035 full-record repeatability fails for 8,368 flags despite stable overlap prices.',
        'Phase 036 retains 2 observed passes, 1 failure and 3 unresolved requirements. Phases 037/038 support a',
        'roughly three-hour raw-label disagreement with coarse references, not a historical offset correction.','',
        '## Cost assumptions','',
        '| Assumption | Base | Adverse | Historical verification |',
        '| --- | ---: | ---: | --- |',
        '|Round-trip commission USD/lot |7 |10 | Hypothetical, not dated/account-certified |',
        '|Modeled slippage pips |0.2 |0.5 | Hypothetical; source bid/ask alone does not certify fills |',
        '|Long/short modeled daily swap USD/lot |-3/-1.5 |-6/-3 | Date, units/conversion and rollover calendar unverified |',
        '|Contract/lot/risk context |100,000 units; 0.01 lot step; 1:10 leverage | Same | Research assumptions; 0.25% estimated trade risk, 1% daily entry pause and one aggregate position retained |','',
        'The saved phase-031 current symbol contract has swap_mode=1 and different raw swap values. Those',
        'numbers must not be substituted as historical USD fees. Platform and Python weekday numbers',
        'use different conventions; numerical 2 versus 3 is not alone proof of a weekday mismatch.',
        'No cost/calendar rule changes here. Stops remain subject to gaps/slippage and financing.','',
        '## Verification and next step','',
        'Phase 090 closure verified: 2,849 bindings/2,634 archive members. Fixed metadata input hashes, all 90',
        '008/028/030 scenario-report links, checker→summary hashes, candidate source inventories,',
        'false eligibility flags and the three original phase-020 market rejections independently checked.',
        'No original tick/bar dataset decoding or simulation/selector invocation. Retained suite: 1,942 passing',
        'tests from phase 090. No full regression or new unit tests in this metadata/document review.',
        'Frozen phase-030 prose has malformed currency annotations; it is preserved. Monetary values here',
        'come from hash-bound JSON summaries and the correct phase-028 capital declaration. No old file repair.',
        '',
        'Next `ARCHIVED-EVIDENCE-092-PLAN.md` declares a bounded dated official-origin document-index',
        'and snapshot review. Phase 026 did not query indexes; bounded negative search is not proof that old',
        'documents do not exist. This is the selected next evidence gap, not renewed native work.',
        'The plan is frozen and unexecuted; no web/index/provider/quote request in phase 091.',
        '',
        'Every prior failure/date/spent marker and data/cost/clock/coverage/provider exclusion remains.',
        'The phase-090 native source-proof contract stays infeasible. Zero actual DLL/WMI/SDK/MT5/compiler/',
        'deploy/log/market/orders/receipts/grants or new returns/selection. Eligibility, execution and',
        'orders stay false; real-money mode and martingale unavailable. Source/evidence/four handoffs',
        'sealed and reviewed. No UI action is required.',''])
    return '\n'.join(lines)


LATEST_TEXT=('Latest — 2026-10-09 local/UTC: offline historical research readiness091 sealed; read RESEARCH-091-RESULTS.md. '
    '11-row matrix distinguishes verified software, mixed reused after-cost development, failed/unresolved data '
    'and missing validation.00812/30 positive;028 C05/C068/12 positive but both lose April, all8 positive cells '
    'concentrated in their largest winner;030 protection improves5/12,worsens7/12,clips12 target-winner cases. '
    'No new returns/selection/promotion. Annual020 remains C00–C04; C05–C08 development only and require '
    'separate chronological protocol.2020–2023 UTC/session/coverage/upstream and historical costs unqualified; '
    '031 catalog0/14 qualified,035 repeatability failure/036 gaps/037–038 clock disagreement preserved. '
    '2024 samples reused,2025 consumed/excluded,Nov–Dec2026 reserved,October quarantine/provider stops intact. '
    'Declared7/10USD commission,0.2/0.5pip slippage and swap scenarios remain hypothetical; current031 '
    'properties do not certify old costs. Frozen030 malformed currency prose preserved; JSON figures used. '
    '0902849 bindings/2634 members verified;90 scenario-report/checker-summary links and eligibility/candidate '
    'inventories checked. Latest retained1942 tests from090; no full/new tests in091. Native090 contract '
    'infeasible/branch closed; no renewal/terminal experiment. Zero actual web/native/DLL/WMI/SDK/MT5/compiler/ '
    'deploy/log/market/orders/receipts/grants or new returns. Runtime/eligibility/orders unavailable. '
    'Next092 bounded dated official-origin clock/session archive discovery unexecuted; no UI action. '
    'Earlier entries historical.'+chr(10)+chr(10))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('freeze','verify','audit','check','seal','review'))
    dict(freeze=freeze,verify=lambda:print(len(verify()['bindings'])),audit=audit,check=check,
        seal=seal,review=review)[p.parse_args().action]()
