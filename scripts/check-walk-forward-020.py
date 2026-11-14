"""Bound version checks plus independent trade, period and tick equity arithmetic."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from forex_demo_lab import walk_forward_metrics as wf
from forex_demo_lab.execution_audit import compare
from forex_demo_lab.runner_migration import equity_path,VERSION

spec=importlib.util.spec_from_file_location('independent014',wf.ROOT/'scripts/check-walk-forward-014.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)


def check(destination):
    destination=Path(destination);ledger=wf.verify(destination)
    summary=wf.load(destination/'run/summary.json')
    if (summary.get('kind')!='completed_chronological_replay_020' or summary.get('runner_version')!='020'
            or summary.get('metric_contract')!=VERSION or summary.get('synthetic') is not ledger['synthetic']):
        raise ValueError('020 completion version/role differs')
    expected={f'{fold}-{role}-{candidate}-{cost}.json' for fold in wf.FOLDS for role in ('training','test')
              for candidate in wf.CANDIDATES for cost in wf.COSTS}
    if set(summary['scenario_bindings'])!=expected or set(summary['selection_bindings'])!={'A-selection.json','B-selection.json'}:
        raise ValueError('020 scenario/choice inventory differs')
    accounting=legacy.check(destination)
    rows={name:wf.load(destination/'run'/name) for name in expected}
    tick_marks=0;diagnostics=[]
    for name,row in sorted(rows.items()):
        if (row.get('metric_contract')!=VERSION or row.get('runner_version')!='020'
                or row.get('ledger_sha256')!=summary['ledger_sha256'] or row['synthetic'] is not ledger['synthetic']):
            raise ValueError('Scenario version/role binding differs')
        fold,role,candidate,cost=name[:-5].split('-')
        if row['candidate']!=candidate or row['cost']!=cost:raise ValueError('Scenario identity differs')
        window=ledger['windows'][fold+'-'+role]
        result=equity_path(wf.window_ticks(ledger,window),row,ledger['configs'][cost])
        tick_marks+=result['tick_marks'];diagnostics.append(dict(scenario=name,**result))
    for fold in wf.FOLDS:
        choice=wf.load(destination/'run'/f'{fold}-selection.json')
        names={f'{fold}-training-{c}-{k}.json' for c in wf.CANDIDATES for k in wf.COSTS}
        if (choice.get('runner_version')!='020' or choice.get('metric_contract')!=VERSION
                or set(choice['training_report_bindings'])!=names):raise ValueError('Choice version/training inventory differs')
        selected=wf.select_fold(wf.selection_rows([rows[name] for name in sorted(names)]),fold)
        compare({k:choice[k] for k in selected},selected,label='training_choice')
    if ledger['synthetic'] and (summary['historical_positive_edge_screen_passed'] or summary['demo_execution_ready']):
        raise ValueError('Synthetic completion falsely approves performance/execution')
    return dict(status='independent_versioned_equity_accounting_matches',scenarios=40,choices=2,
                tick_marks_checked=tick_marks,open_position_boundary_marks_checked=accounting['open_position_boundary_marks_checked'],
                metric_contract=VERSION,synthetic=ledger['synthetic'],equity_diagnostics=diagnostics,
                summary_sha256=legacy.sha(destination/'run/summary.json'),
                market_data_eligibility_verified=False,demo_execution_ready=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);parser.add_argument('--report',type=Path)
    args=parser.parse_args();result=check(args.destination)
    if args.report:
        with args.report.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='equity_diagnostics'},sort_keys=True))
