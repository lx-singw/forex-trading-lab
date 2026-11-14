"""Freeze three software experiments; compare preserved and corrected runners."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab import walk_forward as old
from forex_demo_lab.observer_parity import digest
from forex_demo_lab.runner_migration import generated_runner,generated_cli,challenge,save,compare_controls,VERSION

LEDGER=Path('reports/walk-forward-020-ledger.json');ARCHIVE=Path('reports/walk-forward-020-source.zip')
MODULE=Path('src/forex_demo_lab/walk_forward_metrics.py');CLI=Path('scripts/walk-forward-020.py')
DATA=Path('data/walk-forward-020-challenge')
EXPERIMENTS=dict(compat=Path('reports/walk-forward-020-compat'),
                 legacy_challenge=Path('reports/walk-forward-020-challenge-legacy'),
                 corrected_challenge=Path('reports/walk-forward-020-challenge'))
CODE=['docs/WALK-FORWARD-020-PLAN.md','src/forex_demo_lab/runner_migration.py',
      'scripts/migrate-walk-forward-020.py','scripts/check-walk-forward-020.py',
      'tests/test_walk_forward_metrics.py','src/forex_demo_lab/execution_metrics.py',
      'src/forex_demo_lab/walk_forward.py','src/forex_demo_lab/selection.py',
      'scripts/walk-forward-014.py','scripts/check-walk-forward-014.py']


def new_runner():
    from forex_demo_lab import walk_forward_metrics
    return walk_forward_metrics


def checker():
    spec=importlib.util.spec_from_file_location('independent020','scripts/check-walk-forward-020.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def prepare():
    if any(p.exists() for p in (LEDGER,ARCHIVE,MODULE,CLI,DATA,*EXPERIMENTS.values())):
        raise FileExistsError('020 already exists; preserve all attempts')
    old.verify('reports/walk-forward-014-synthetic')
    prior=json.loads(Path('reports/execution-019-final-source.json').read_text())
    for name in CODE[5:]:
        if digest(Path(name).read_bytes())!=prior['source_bindings'][name]:raise ValueError('Preserved source changed: '+name)
    for name,checksum in prior['report_bindings'].items():
        if digest(Path(name).read_bytes())!=checksum:raise ValueError('Prior report changed: '+name)
    with MODULE.open('x') as stream:stream.write(generated_runner(Path(CODE[6]).read_text()))
    with CLI.open('x') as stream:stream.write(generated_cli(Path(CODE[8]).read_text()))
    challenge(DATA);wf=new_runner()
    wf.freeze('data/walk-forward-014-synthetic/bundle.json',EXPERIMENTS['compat'])
    old.freeze(DATA/'bundle.json',EXPERIMENTS['legacy_challenge'])
    wf.freeze(DATA/'bundle.json',EXPERIMENTS['corrected_challenge'])
    names=CODE+[str(MODULE),str(CLI),'reports/execution-019-final-source.json']
    names += [str(p) for p in sorted(DATA.iterdir()) if p.is_file()]
    for dest in EXPERIMENTS.values():names += [str(dest/p) for p in ('ledger.json','seal.json','source.zip')]
    # Bind every old compatibility result and synthetic input, not just its summary.
    baseline=old.load('reports/walk-forward-014-synthetic/ledger.json')
    extra={str(p):digest(Path(p).read_bytes()) for p in baseline['input_bindings']}
    extra.update({str(p):digest(p.read_bytes()) for p in Path('reports/walk-forward-014-synthetic/run').iterdir() if p.is_file()})
    bindings={name:digest(Path(name).read_bytes()) for name in names}
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED) as zipped:
        for name in names:zipped.write(name,name)
    save(LEDGER,dict(kind='corrected_runner_migration_freeze_020',source_bindings=bindings,
         previous_reports=prior['report_bindings'],compatibility_bindings=extra,
         archive_sha256=digest(ARCHIVE.read_bytes()),metric_contract=VERSION,
         software_accounts=120,maximum_candidates=5,performance_evaluation_ready=False,demo_execution_ready=False))
    with Path('reports/walk-forward-020-ledger.sha256').open('x') as stream:stream.write(digest(LEDGER.read_bytes())+'\n')
    verify();print('020 frozen: three experiments, 120 software accounts; no new replay yet.')


def verify():
    if digest(LEDGER.read_bytes())!=Path('reports/walk-forward-020-ledger.sha256').read_text().strip():raise ValueError('020 seal differs')
    value=json.loads(LEDGER.read_text())
    for name,checksum in {**value['source_bindings'],**value['previous_reports'],**value['compatibility_bindings']}.items():
        if digest(Path(name).read_bytes())!=checksum:raise ValueError('020 frozen evidence changed: '+name)
    if digest(ARCHIVE.read_bytes())!=value['archive_sha256']:raise ValueError('020 archive differs')
    if MODULE.read_text()!=generated_runner(Path(CODE[6]).read_text()):raise ValueError('Runner has undeclared changes')
    if CLI.read_text()!=generated_cli(Path(CODE[8]).read_text()):raise ValueError('CLI has undeclared changes')
    old.verify('reports/walk-forward-014-synthetic');old.verify(EXPERIMENTS['legacy_challenge'])
    for name in ('compat','corrected_challenge'):new_runner().verify(EXPERIMENTS[name])
    return value


def run():
    verify()
    # Each run preserves partial output; all three freezes precede any replay.
    for name in ('compat','legacy_challenge','corrected_challenge'):
        runner=old if name=='legacy_challenge' else new_runner()
        result=runner.run(EXPERIMENTS[name]);print(name+': '+str(len(result['scenario_bindings']))+' software scenarios')


def reports(destination):
    destination=Path(destination);summary=old.load(destination/'run/summary.json')
    for name,checksum in {**summary['scenario_bindings'],**summary['selection_bindings']}.items():
        if digest((destination/'run'/name).read_bytes())!=checksum:raise ValueError('Report binding differs')
    return {name:old.load(destination/'run'/name) for name in summary['scenario_bindings']}


def check():
    verify();path=Path('reports/walk-forward-020-review.json')
    if path.exists():raise FileExistsError('020 review exists; do not overwrite')
    independent=checker();reviews={}
    for name in ('compat','corrected_challenge'):
        result=independent.check(EXPERIMENTS[name]);reviews[name]=result
        save(Path(f'reports/walk-forward-020-{name}-independent.json'),result)
    shadow=independent.legacy.check(EXPERIMENTS['legacy_challenge'])
    save(Path('reports/walk-forward-020-legacy-challenge-independent.json'),shadow)
    compatibility=compare_controls(reports('reports/walk-forward-014-synthetic'),reports(EXPERIMENTS['compat']))
    changes=compare_controls(reports(EXPERIMENTS['legacy_challenge']),reports(EXPERIMENTS['corrected_challenge']))
    targets=sum(t['reason']=='target_tick' for row in reports(EXPERIMENTS['corrected_challenge']).values() for t in row['trades'])
    if not changes['drawdown_changes'] or targets==0:raise ValueError('Challenge did not exercise metric correction')
    choices={name:{fold:old.load(dest/'run'/f'{fold}-selection.json')['selected'] for fold in old.FOLDS}
             for name,dest in EXPERIMENTS.items()}
    result=dict(kind='independent_corrected_runner_migration_review_020',passed=True,
                compared_scenarios=80,software_accounts=120,compatibility=compatibility,
                challenge=changes,challenge_target_fills=targets,choices=choices,
                corrected_tick_marks_checked=sum(r['tick_marks_checked'] for r in reviews.values()),
                metric_contract=VERSION,market_profitability_established=False,
                performance_evaluation_ready=False,demo_execution_ready=False)
    save(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('compatibility','challenge')},sort_keys=True))


def gates():
    verify();root=Path('reports/walk-forward-020-market-gates');root.mkdir(exist_ok=False)
    cases=[]
    for label,review in (('normalization015','reports/normalization-015-review.json'),
                         ('reference016b','reports/reference-016b-review.json'),
                         ('labels017','reports/labels-017-review.json')):
        bundle=root/(label+'-bundle.json')
        relative=Path(review).resolve().as_posix()
        save(bundle,dict(kind='chronological_ticks_input',synthetic=False,review=relative,
                         years={str(y):dict(data='NO_MARKET_READ_020.gz',provenance='NO_MARKET_READ_020.json') for y in old.YEARS}))
        destination=root/(label+'-rejected')
        try:new_runner().freeze(bundle,destination)
        except ValueError as exc:
            if 'Annual data review' not in str(exc) or destination.exists():raise
            cases.append(dict(review=review,review_sha256=digest(Path(review).read_bytes()),
                              status='blocked_before_data_iteration_and_performance',reason=str(exc),output_created=False))
        else:raise ValueError('Blocked historical review was accepted')
    result=dict(kind='actual_020_market_path_rejections',cases=cases,
                synthetic_sentinel_datasets_not_created=True,performance_evaluation_ready=False,demo_execution_ready=False)
    save(root/'review.json',result);print('020 rejects all three existing historical reviews before data/performance.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','verify','run','check','gates'])
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='verify':verify();print('020 migration, original 014/019 and previous reports intact.')
    elif args.action=='run':run()
    elif args.action=='check':check()
    else:gates()
