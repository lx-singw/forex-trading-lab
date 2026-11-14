"""Freeze and verify a versioned metric repair against unchanged 019 paths."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.observer_parity import digest
from forex_demo_lab.execution_audit import compare

OLD=runpy.run_path('scripts/execution-019.py')
LEDGER=Path('reports/execution-019b-ledger.json');ARCHIVE=Path('reports/execution-019b-source.zip')
GENERATED=Path('src/forex_demo_lab/execution_audit_runtime_b.py')
RUN=Path('reports/execution-019b-run.json');REVIEW=Path('reports/execution-019b-review.json')
CODE=['docs/EXECUTION-019B-PLAN.md','src/forex_demo_lab/execution_metrics.py',
      'scripts/execution-019b.py','tests/test_execution_metrics.py']


def generate():
    text=Path('src/forex_demo_lab/execution_audit_runtime.py').read_text()
    old='from .tick_simulation import TickSimulator\nfrom .research_simulation import ResearchTickSimulator'
    new=('from .execution_metrics import ExecutableEquityTickSimulator as TickSimulator\n'
         'from .execution_metrics import ExecutableEquityResearchTickSimulator as ResearchTickSimulator')
    if text.count(old)!=1:raise ValueError('Frozen runtime import site differs')
    return text.replace(old,new).replace('InjectedTick019','InjectedTick019B').replace('InjectedResearch019','InjectedResearch019B')


def prepare():
    OLD['verify']()
    if any(p.exists() for p in (LEDGER,ARCHIVE,GENERATED)):raise FileExistsError('019B already exists')
    failed=json.loads(OLD['REVIEW'].read_text())
    if failed['passed'] or failed['cases']!=30 or failed['cash_position_pause_restart_cases_passed']!=30:
        raise ValueError('Declared original failure differs')
    with GENERATED.open('x') as stream:stream.write(generate())
    names=CODE+[str(GENERATED),str(OLD['LEDGER']),str(OLD['ARCHIVE']),
                 'reports/execution-019-ledger.sha256',str(OLD['RUN']),str(OLD['REVIEW']),
                 'reports/execution-019-checks.json']
    bindings={name:digest(Path(name).read_bytes()) for name in names}
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED) as archive:
        for name in names:archive.write(name,name)
    value=dict(kind='versioned_execution_metric_repair_freeze_019b',source_bindings=bindings,
               archive_sha256=digest(ARCHIVE.read_bytes()),original_019_review_passed=False,
               cases=30,performance_evaluation_ready=False,demo_execution_ready=False)
    OLD['save'](LEDGER,value)
    with Path('reports/execution-019b-ledger.sha256').open('x') as stream:stream.write(digest(LEDGER.read_bytes())+'\n')
    verify();print('019B frozen: unchanged 30 paths and reference expectations; metric repair only.')


def verify():
    OLD['verify']()
    if digest(LEDGER.read_bytes())!=Path('reports/execution-019b-ledger.sha256').read_text().strip():
        raise ValueError('019B ledger seal differs')
    value=json.loads(LEDGER.read_text())
    for name,checksum in value['source_bindings'].items():
        if digest(Path(name).read_bytes())!=checksum:raise ValueError('019B frozen file differs: '+name)
    if digest(ARCHIVE.read_bytes())!=value['archive_sha256']:raise ValueError('019B archive differs')
    if GENERATED.read_text()!=generate():raise ValueError('Supplemental runtime has unrelated changes')
    return value


def run():
    verify()
    if RUN.exists():raise FileExistsError('019B run already exists; preserve it')
    from forex_demo_lab.execution_audit_runtime_b import run_case
    cases=json.loads(OLD['INPUTS'].read_text())
    rows=[run_case(case) for case in cases]
    OLD['save'](RUN,dict(kind='versioned_executable_equity_runtime_019b',
                         ledger_sha256=digest(LEDGER.read_bytes()),cases=rows,
                         market_data_used=False,broker_calls=False,orders_available=False,
                         performance_evaluation_ready=False,demo_execution_ready=False))
    print('019B executed all 30 cases and every checkpoint boundary.')


def strip_metrics(value):
    if isinstance(value,dict):
        return {k:strip_metrics(v) for k,v in value.items() if k not in ('peak_tick_equity','max_tick_drawdown')}
    if isinstance(value,list):return [strip_metrics(v) for v in value]
    return value


def check():
    verify()
    if REVIEW.exists():raise FileExistsError('019B review already exists; preserve it')
    raw=json.loads(RUN.read_text());original=json.loads(OLD['RUN'].read_text())
    if raw['ledger_sha256']!=digest(LEDGER.read_bytes()):raise ValueError('019B run ledger differs')
    unchanged_checks=compare(strip_metrics(raw['cases']),strip_metrics(original['cases']))
    results=OLD['check_rows'](json.loads(OLD['INPUTS'].read_text()),raw['cases'])
    value=dict(kind='independent_versioned_execution_metric_review_019b',
               passed=all(r['passed'] for r in results),cases=len(results),
               cases_passed=sum(r['passed'] for r in results),
               restart_boundaries=sum(r['restart_boundaries'] for r in results),
               unchanged_nonmetric_checks=unchanged_checks,original_019_review_passed=False,
               cases_review=results,run_sha256=digest(RUN.read_bytes()),
               performance_evaluation_ready=False,demo_execution_ready=False)
    OLD['save'](REVIEW,value)
    print(json.dumps({k:v for k,v in value.items() if k!='cases_review'},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','verify','run','check'])
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='verify':verify();print('019/019B sources, paths, original failure and prior evidence intact.')
    elif args.action=='run':run()
    else:check()
