"""Review the fixed batch and seal sources; no parameter selection or new replay."""
import argparse
import hashlib
import json
import runpy
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT/'scripts/exit-experiment-030.py'))
sha, write, sealed = API['sha'], API['write'], API['sealed']
REVIEW = ROOT/'reports/exit-experiment-030-review.json'
FINAL = ROOT/'reports/exit-experiment-030-final-source.json'


def entry_comparisons(ledger):
    comparisons = []
    for sample in API['SAMPLES']:
        for cost in ('base', 'adverse'):
            for new, control in (('C07', 'C05'), ('C08', 'C06')):
                a = sealed(ROOT/f'reports/strategy-experiment-028-{sample}-{control}-{cost}.json')
                b = sealed(ROOT/f'reports/exit-experiment-030-{sample}-{new}-{cost}.json')
                key = lambda t: (t['opened'],t['side'])
                aa = {key(t):t for t in a['trades']}
                bb = {key(t):(t,p) for t,p in zip(b['trades'],b['protection_lineage'],strict=True)}
                assert len(aa)==len(a['trades']) and len(bb)==len(b['trades'])
                clipped, omitted_targets, retained_targets, protected = [], [], [], []
                for identity,old in aa.items():
                    if old['reason']=='target_tick' and old['net_pnl']>0:
                        if identity not in bb:
                            omitted_targets.append(dict(opened=identity[0],side=identity[1],old_net=old['net_pnl']))
                        else:
                            t,p=bb[identity]
                            if p['arm'] and t['reason']=='stop_tick':
                                clipped.append(dict(opened=identity[0],side=identity[1],old_net=old['net_pnl'],new_net=t['net_pnl'],arm=p['arm']))
                            elif t['reason']=='target_tick':
                                retained_targets.append(dict(opened=identity[0],side=identity[1],old_net=old['net_pnl'],new_net=t['net_pnl']))
                for t,p in bb.values():
                    if p['arm'] and t['reason']=='stop_tick':
                        protected.append(dict(opened=t['opened'],side=t['side'],net_pnl=t['net_pnl'],closed=t['closed']))
                comparisons.append(dict(sample=sample, cost=cost, challenger=new, control=control,
                    shared_entries=len(aa.keys()&bb.keys()), control_only_entries=len(aa.keys()-bb.keys()),
                    new_only_entries=len(bb.keys()-aa.keys()),
                    omitted_entries=[dict(opened=k[0],side=k[1]) for k in sorted(aa.keys()-bb.keys())],
                    new_entries=[dict(opened=k[0],side=k[1]) for k in sorted(bb.keys()-aa.keys())],
                    net_pnl_difference=b['metrics']['net_pnl']-a['metrics']['net_pnl'],
                    tick_drawdown_difference=b['metrics']['max_tick_drawdown']-a['metrics']['max_tick_drawdown'],
                    commission_difference=b['metrics']['commission']-a['metrics']['commission'],
                    swap_difference=b['metrics']['swap']-a['metrics']['swap'],
                    clipped_shared_target_winners=clipped, omitted_target_winners=omitted_targets,
                    retained_shared_target_winners=retained_targets, protected_exits=protected,
                    protected_exit_losses=sum(t['net_pnl'] < -1e-8 for t in protected),
                    armed=sum(p['arm'] is not None for p in b['protection_lineage'])))
    return comparisons


def review():
    prior = API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    summary = sealed(ROOT/'reports/exit-experiment-030-summary.json')
    checks = sealed(ROOT/'reports/exit-experiment-030-checks.json')
    tests = sealed(ROOT/'reports/exit-experiment-030-tests.json')
    synthetic = sealed(ROOT/'reports/exit-experiment-030-synthetic-checks.json')
    assert checks['passed'] and tests['passed'] and synthetic['passed']
    assert checks['summary_sha256'] == sha(ROOT/'reports/exit-experiment-030-summary.json')
    assert checks['ledger_sha256'] == summary['ledger_sha256'] == sha(API['LEDGER'])
    assert len(summary['scenarios']) == checks['scenarios_checked'] == 30
    assert checks['controls_matching_original'] == 18
    assert tests['tests_run'] == tests['tests_passed'] == 384 and tests['new_tests'] == 16
    assert synthetic['cases_checked'] == 16
    assert sum(r['trades'] for r in summary['scenarios']) == checks['trades_checked']
    assert sum(r['armed'] for r in summary['scenarios']) == sum(c['arms_checked'] for c in checks['sample_checks'].values())
    assert checks['trades_checked'] == sum(c['sizing_checked'] for c in checks['sample_checks'].values())
    for sample, checked in checks['sample_checks'].items():
        assert checked['ticks_checked'] == ledger['datasets'][sample]['ticks']
    assert not list(ROOT.glob('reports/exit-experiment-030-*-failure.json'))
    for s in ledger['scenarios']:
        r = sealed(ROOT/('reports/exit-experiment-030-'+s['id']+'.json'))
        assert r['annual_eligible'] is r['orders_available'] is False
        if s['candidate'] in ('C00', 'C05', 'C06'):
            API['control_parity'](r)
    documents = ['docs/EXIT-EXPERIMENT-030-RESULTS.md', 'scripts/finalize-exit-experiment-030.py']
    for name in API['HANDOFF']:
        assert 'EXIT-EXPERIMENT-030-RESULTS.md' in (ROOT/name).read_text(), name
    write(REVIEW, dict(kind='post_independent_development_review_030', passed=True,
        prior_snapshot_verified=prior, input_bindings_verified=len(ledger['bindings']),
        scenarios_checked=30, controls_matching_original=18, trades_checked=checks['trades_checked'],
        sample_checks=checks['sample_checks'], entry_comparisons=entry_comparisons(ledger),
        software_tests_passed=384, synthetic_checker_cases=16,
        documentation_bindings={name: sha(ROOT/name) for name in documents},
        table_sha256=sha(ROOT/'reports/exit-experiment-030-table.csv'),
        annual_eligible=False, market_profitability_established=False,
        selection_authorized=False, orders_available=False,
        next_plan='Qualified fresh chronological data before validation; declare any further development study separately', next_plan_executed=False))
    print(json.dumps(dict(passed=True, controls=18, tests_passed=384, trades=checks['trades_checked'])))


def snapshot():
    checked = sealed(REVIEW)
    assert checked['passed']
    API['prior_verify'](allow_handoff=True)
    ledger = API['verify']()
    for name, expected in checked['documentation_bindings'].items():
        assert sha(ROOT/name) == expected, name
    prior_path = API['PRIOR']
    prior = sealed(prior_path)
    groups = {g: dict(v) for g, v in prior.items() if g.endswith('_bindings') and g != 'archive_external_bindings'}
    for name in API['HANDOFF']:
        groups['source_bindings'][name] = sha(ROOT/name)
    for pattern in ('docs/*030*.md', 'config/research-candidates-030.json', 'scripts/*030*.py',
                    'src/forex_demo_lab/exit_experiment_030.py', 'tests/test_exit_experiment_030.py'):
        for path in ROOT.glob(pattern):
            groups['source_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in ROOT.glob('reports/exit-experiment-030*'):
        assert 'final-source' not in path.name
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    for suffix in ('.json', '.sha256', '.zip'):
        path = prior_path.with_suffix(suffix)
        groups['report_bindings'][path.relative_to(ROOT).as_posix()] = sha(path)
    already = {n: h for values in groups.values() for n, h in values.items()}
    groups['exit_input_bindings'] = {}
    for name, expected in ledger['bindings'].items():
        if name in already:
            assert already[name] == expected, name
        else:
            groups['exit_input_bindings'][name] = expected
    bindings = {n: h for values in groups.values() for n, h in values.items()}
    assert len(bindings) == sum(map(len, groups.values()))
    external = {n: h for n, h in bindings.items() if n.startswith('/') or n.endswith('.zip') or
                (n.startswith('data/') and n.endswith('.gz') and 'synthetic' not in n and 'walk-forward' not in n)}
    internal = {n: h for n, h in bindings.items() if n not in external}
    for name, expected in bindings.items():
        assert sha(ROOT/name) == expected, name
    archive_path = FINAL.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(internal):
            z.write(ROOT/name, name)
    with zipfile.ZipFile(archive_path) as z:
        assert z.testzip() is None and len(z.infolist()) == len(internal)
        assert set(z.namelist()) == set(internal)
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == internal[name], name
    write(FINAL, dict(kind='post_development_experiment_snapshot_030', **groups,
        archive_external_bindings=external, archive_members_verified=len(internal),
        external_bindings_verified=len(external), archive_sha256=sha(archive_path), archive_bytes=archive_path.stat().st_size,
        snapshot_scope='Source/reports/small fixtures archived; prior ZIPs, market gzip/ZIPs and timezone files externally hash-bound, verified and required for rerun',
        previous_snapshot=prior_path.relative_to(ROOT).as_posix(), previous_snapshot_sha256=sha(prior_path),
        completed_utc=datetime.now(timezone.utc).isoformat(), software_tests_passed=384,
        scenarios_checked=30, controls_matching_original=18,
        annual_eligible=False, market_profitability_established=False, selection_authorized=False, orders_available=False,
        next_plan=checked['next_plan'], next_plan_executed=False))
    print(json.dumps(dict(counts={g: len(v) for g, v in groups.items()}, archive_members=len(internal),
                         external_bindings=len(external), manifest_sha256=sha(FINAL))))


def documents():
    ledger = API['verify']()
    summary = sealed(ROOT/'reports/exit-experiment-030-summary.json')
    checks = sealed(ROOT/'reports/exit-experiment-030-checks.json')
    assert checks['passed']
    rows = summary['scenarios']
    comparisons = entry_comparisons(ledger)
    arms = sum(r['armed'] for r in rows)
    exits = sum(r['protected_exits'] for r in rows)
    clipped = sum(len(c['clipped_shared_target_winners']) for c in comparisons)
    omitted_targets = sum(len(c['omitted_target_winners']) for c in comparisons)
    new_entries = sum(c['new_only_entries'] for c in comparisons)
    omitted_entries = sum(c['control_only_entries'] for c in comparisons)
    losses = sum(c['protected_exit_losses'] for c in comparisons)
    better = sum(c['net_pnl_difference']>1e-8 for c in comparisons)
    ticks = sum(c['ticks_checked'] for c in checks['sample_checks'].values())
    marks = sum(c['equity_marks_checked'] for c in checks['sample_checks'].values())
    features = sum(c['closed_bar_features_checked'] for c in checks['sample_checks'].values())
    totals = {(candidate,cost):sum(r['net_pnl'] for r in rows if r['candidate']==candidate and r['cost']==cost)
              for candidate in API['CANDIDATES'] for cost in ('base','adverse')}
    text = ['# Protective-stop experiment 030 — completed', '',
        'The single +0.5R cost-aware protective stop helped April and harmed July. '
        'It is not a generally superior exit or evidence of unseen profitability. '
        'All thirty declared scenarios completed once; no trigger, target or entry tuning.', '',
        f'Compared with their parents, challengers improve {better}/12 cells and worsen {12-better}/12. '
        f'There are {arms} arms and {exits} protected stop exits; {losses} of those exits still lose '
        '(negative net below −/bin/bash.00000001). The level only estimates zero net at arming; '
        'later financing and gaps still create losses.', '',
        f'{clipped} shared original target winners instead hit protected stops; '
        f'{omitted_targets} other original target winners are omitted entries. '
        f'There are {new_entries} new and {omitted_entries} omitted entry identities overall. '
        'These counts overlap across costs/candidates and are not independent trials. '
        'No claim that subtracting old losses reproduces the new strategy.', '',
        '## All declared outcomes', '',
        'Dollar results use separate 0,000 monthly accounts, the common 201-hour warmup, '
        'and the original partial-month 2024 boundaries. CASH is /bin/bash per window/cost. '
        'Corrected drawdown is the maximum tick equity drawdown, including modeled fills.', '',
        '| Scenario | Trades | Net $ | Tick DD % | Armed | Protected exits | Fee $ | Swap $ |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        text.append(f"| {r['scenario']} | {r['trades']} | {r['net_pnl']:+.2f} | {r['corrected_tick_drawdown']*100:.4f} | {r['armed']} | {r['protected_exits']} | {r['commission']:.2f} | {r['swap']:.2f} |")
    text += ['', 'Diagnostic sums across the three separately funded samples (not a continuous '
        'portfolio, annual return, validation or selection score):', '',
        '| Candidate | Base net $ | Adverse net $ |', '|---|---:|---:|']
    for candidate in API['CANDIDATES']:
        text.append(f'| {candidate} | {totals[candidate,"base"]:+.2f} | {totals[candidate,"adverse"]:+.2f} |')
    text += ['', '## Entry and winner comparison', '',
        '| Cell | Delta net $ | Shared | New | Omitted | Clipped targets | Omitted targets |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for c in comparisons:
        text.append(f"| {c['sample']}-{c['challenger']}-{c['cost']} | {c['net_pnl_difference']:+.2f} | {c['shared_entries']} | {c['new_only_entries']} | {c['control_only_entries']} | {len(c['clipped_shared_target_winners'])} | {len(c['omitted_target_winners'])} |")
    text += ['', 'Full identities, old/new winner net values, arm witnesses, protected exits, '
        'fee/swap and drawdown differences are preserved in the sealed review. '
        'The CSV includes win rate, net expectancy, exposure and all thirty costs/results.', '',
        '## Implementation and verification', '',
        'Separate exit_experiment_030.py maps C07→C05 and C08→C06. Inherited fills and '
        'corrected equity marks occur before arming; a moved stop applies only to later source '
        'sequences. Initial stop/distance/dollar R survive separately in protection_lineage. '
        'Targets, risk caps, spread filters, financing, duplicate prevention and daily pauses '
        'remain inherited. New checkpoints reject old versions, other candidates/costs/boundaries.', '',
        '384 software tests pass (16 new) and all sixteen independent synthetic checker cases '
        'pass before freezing returns. The preflight verified all 815 prior bindings, 780 ZIP '
        'members and 35 external inputs; the new ledger freezes 189 bindings. All 18 controls '
        'match every original 028 trade, decision, equity point, fill lineage and corrected metric exactly.', '',
        f'Independent reconstruction checks {checks["trades_checked"]} trade cash/fill/sizing paths, '
        f'{ticks:,} original cached quotes, {marks:,} equity marks and {features:,} closed-bar feature '
        f'records. Every one of the {arms} arms is the first eligible surviving quote; original '
        'stops remain effective until that quote finishes. Cash, financing, commission, '
        'targets, final levels, risk/margin, exposure, pauses and drawdown reconcile.', '',
        'Artifacts: reports/exit-experiment-030-{ledger,tests,synthetic-checks,summary,checks,review,final-source}.json, '
        'thirty scenario JSON/seals and exit-experiment-030-table.csv. Final source ZIP contains '
        'source/reports/small fixtures; prior ZIPs, market gzip/ZIPs and timezone files are '
        'externally hash-bound and required for replay, so it is not self-contained.', '',
        '## Limits and continuation', '',
        'No candidate is promoted. A positive reused sample does not establish an edge. '
        'The threshold was chosen with 029 diagnostics; all three windows are reused development. '
        'Historical clock/session/coverage and executable cost certification remain unresolved. '
        'Annual eligibility stays failed. Consumed 2025 and reserved November–December2026 are untouched. '
        'No downloads, broker connections, account creation, MT5 deployment, martingale, '
        'real-money toggle or order placement occurred.', '',
        'Next: obtain qualified fresh chronological data before validation. Any additional '
        'development hypothesis needs a separately declared bounded plan; repeatedly adjusting '
        'these exits on the same windows cannot establish reliability. Preserve the original '
        'C05/C06 comparisons and this mixed protective-stop result.', '']
    with (ROOT/'docs/EXIT-EXPERIMENT-030-RESULTS.md').open('x') as f:
        f.write('\n'.join(text))
    handoff = (f'Latest — 2026-10-06: protective-stop030 complete. Read `EXIT-EXPERIMENT-030-RESULTS.md`. '
        f'All 30 fixed scenarios completed once; 18 controls exactly reproduce 028 including corrected '
        f'metrics. Challengers improve {better}/12 cells, worsen {12-better}/12; April improves, July worsens. '
        f'{arms} arms / {exits} protected exits ({losses} still negative);{clipped} shared target winners '
        f'clipped, {omitted_targets} target entries omitted. {new_entries} new / {omitted_entries} omitted '
        f'entry identities. C07 diagnostic net sums base {totals["C07","base"]:+.2f} / adverse {totals["C07","adverse"]:+.2f}; '
        f'C08 base {totals["C08","base"]:+.2f} / adverse {totals["C08","adverse"]:+.2f}; separate sample capitals, '
        f'not annual/validation returns. 384 tests (16 new), 16 synthetic cases and independent '
        f'{checks["trades_checked"]} trades / {ticks:,} ticks / {marks:,} marks / {features:,} features pass. '
        'Prior 815 bindings / 780 archive members / 35 external inputs verified; 189 new frozen bindings. '
        'Separate 030 module/checkpoints retain original R and arm after inherited fills for '
        'subsequent sequences only. No selection or further threshold search. Next qualified fresh '
        'chronological data before validation; declare any further development study separately. '
        'Annual gate failed; consumed 2025 / reserved Nov–Dec2026 untouched; no downloads/accounts/MT5 '
        'deployment/orders; real-money execution unavailable. Earlier status below is historical.\n\n')
    for name in API['HANDOFF']:
        path = ROOT/name
        content = path.read_text()
        split = content.index('\n')+1
        path.write_text(content[:split]+'\n'+handoff+content[split:])
    print(json.dumps(dict(documents_written=True, improved_cells=better, arms=arms,
        protected_exits=exits, protected_exit_losses=losses, clipped_target_winners=clipped,
        omitted_target_winners=omitted_targets, new_entries=new_entries, omitted_entries=omitted_entries,
        diagnostic_totals={f'{c}-{cost}':v for (c,cost),v in totals.items()})))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('documents', 'review', 'snapshot'))
    {'documents': documents, 'review': review, 'snapshot': snapshot}[parser.parse_args().action]()
