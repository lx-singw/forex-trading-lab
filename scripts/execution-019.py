"""Freeze, run and independently check every synthetic interaction case."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab.observer_parity import digest
from forex_demo_lab.execution_audit import scenarios,reference,compare

LEDGER=Path('reports/execution-019-ledger.json');ARCHIVE=Path('reports/execution-019-source.zip')
INPUTS=Path('reports/execution-019-fixtures.json');RUN=Path('reports/execution-019-run.json')
REVIEW=Path('reports/execution-019-review.json')
CODE=['docs/EXECUTION-019-PLAN.md','src/forex_demo_lab/execution_audit.py',
      'src/forex_demo_lab/execution_audit_runtime.py','scripts/execution-019.py',
      'tests/test_execution_audit.py','src/forex_demo_lab/model.py',
      'src/forex_demo_lab/simulation.py','src/forex_demo_lab/tick_simulation.py',
      'src/forex_demo_lab/research_simulation.py','src/forex_demo_lab/strategies.py',
      'src/forex_demo_lab/observer_parity.py','config/baseline.json',
      'config/research-candidates-008.json']


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def prepare():
    if any(p.exists() for p in (LEDGER,ARCHIVE,INPUTS)):raise FileExistsError('019 already exists')
    prior=json.loads(Path('reports/observer-018-final-source.json').read_text())
    for name in CODE[5:]:
        if digest(Path(name).read_bytes())!=prior['source_bindings'][name]:
            raise ValueError('Original source differs: '+name)
    for name,checksum in prior['report_bindings'].items():
        if digest(Path(name).read_bytes())!=checksum:raise ValueError('Prior report differs: '+name)
    cases=scenarios();save(INPUTS,cases)
    names=CODE+[str(INPUTS),'reports/observer-018-final-source.json']
    bindings={name:digest(Path(name).read_bytes()) for name in names}
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED) as archive:
        for name in names:archive.write(name,name)
    value=dict(kind='synthetic_execution_interaction_freeze_019',cases=len(cases),
               source_bindings=bindings,previous_reports=prior['report_bindings'],
               archive_sha256=digest(ARCHIVE.read_bytes()),
               performance_evaluation_ready=False,demo_execution_ready=False)
    save(LEDGER,value)
    with Path('reports/execution-019-ledger.sha256').open('x') as stream:stream.write(digest(LEDGER.read_bytes())+'\n')
    verify();print(f'019 frozen: {len(cases)} cases; no production path run yet.')


def verify():
    if digest(LEDGER.read_bytes())!=Path('reports/execution-019-ledger.sha256').read_text().strip():
        raise ValueError('019 seal differs')
    ledger=json.loads(LEDGER.read_text())
    for name,checksum in {**ledger['source_bindings'],**ledger['previous_reports']}.items():
        if digest(Path(name).read_bytes())!=checksum:raise ValueError('019 frozen evidence changed: '+name)
    if digest(ARCHIVE.read_bytes())!=ledger['archive_sha256']:raise ValueError('019 source archive differs')
    if json.loads(INPUTS.read_text())!=scenarios():raise ValueError('019 regeneration differs')
    return ledger


def run():
    verify()
    if RUN.exists():raise FileExistsError('Original run already exists; never overwrite')
    from forex_demo_lab.execution_audit_runtime import run_case
    cases=json.loads(INPUTS.read_text())
    rows=[run_case(case) for case in cases]
    save(RUN,dict(kind='original_frozen_execution_runtime_019',ledger_sha256=digest(LEDGER.read_bytes()),
                  cases=rows,market_data_used=False,broker_calls=False,orders_available=False,
                  performance_evaluation_ready=False,demo_execution_ready=False))
    print(f'019 executed all {len(rows)} cases and every restart boundary.')


def failures(actual,expected,label):
    if isinstance(expected,dict) and isinstance(actual,dict) and set(actual)==set(expected):
        return [f for key in expected for f in failures(actual[key],expected[key],label+'.'+key)]
    if isinstance(expected,list) and isinstance(actual,list) and len(actual)==len(expected):
        return [f for i,(a,e) in enumerate(zip(actual,expected)) for f in failures(a,e,label+f'[{i}]')]
    try:compare(actual,expected,label=label)
    except ValueError as exc:return [dict(field=label,actual=actual,expected=expected,reason=str(exc))]
    return []


def check_rows(cases,rows):
    if [r['case_id'] for r in rows]!=[c['case_id'] for c in cases]:raise ValueError('Runtime inventory/order differs')
    results=[]
    for case,row in zip(cases,rows):
        expected=reference(case)
        if case['expected']!=expected:raise ValueError('Frozen reference expectation differs')
        if row['engine']!=case['engine']:raise ValueError('Runtime engine differs')
        differences=failures({k:row[k] for k in ('trace','final')},expected,'result')
        restart_expected=[dict(boundary=i,duplicate_return=False,duplicate_no_change=True,
                               final_checkpoint_equal=True,finish_idempotent=True) for i in range(len(case['ticks']))]
        differences+=failures(row['restarts'],restart_expected,'restarts')
        if case['decision_mode']=='actual_c04':
            log=row['decision_log']
            if (len(log)!=1 or log[0]['side']!=case['side'] or log[0]['reason']!='selector_trend:channel_breakout'
                    or log[0]['features']['selected_mode']!='trend'
                    or log[0]['hour_start_ms']!=case['ticks'][201]['time_msc']):
                differences.append(dict(field='actual_c04_decision',reason='Fixed selector decision differs'))
        cash_failures=[f for f in differences if not any(x in f['field'] for x in ('peak_tick_equity','max_tick_drawdown'))]
        results.append(dict(case_id=case['case_id'],engine=case['engine'],passed=not differences,
                            cash_position_pause_restart_passed=not cash_failures,
                            restart_boundaries=len(row['restarts']),failures=differences))
    return results


def check():
    verify()
    if REVIEW.exists():raise FileExistsError('Original review already exists; preserve it')
    raw=json.loads(RUN.read_text())
    if raw['ledger_sha256']!=digest(LEDGER.read_bytes()):raise ValueError('Run ledger differs')
    rows=check_rows(json.loads(INPUTS.read_text()),raw['cases'])
    result=dict(kind='independent_execution_interaction_review_019',passed=all(r['passed'] for r in rows),
                cases=len(rows),cases_passed=sum(r['passed'] for r in rows),
                cash_position_pause_restart_cases_passed=sum(r['cash_position_pause_restart_passed'] for r in rows),
                restart_boundaries=sum(r['restart_boundaries'] for r in rows),cases_review=rows,
                run_sha256=digest(RUN.read_bytes()),performance_evaluation_ready=False,demo_execution_ready=False)
    save(REVIEW,result)
    print(json.dumps({k:v for k,v in result.items() if k!='cases_review'},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','verify','run','check'])
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='verify':verify();print('019 sources, inputs and prior reports intact.')
    elif args.action=='run':run()
    else:check()
