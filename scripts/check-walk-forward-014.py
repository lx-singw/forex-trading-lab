"""Independent report arithmetic; never replays a strategy or approves market data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(a,b):
    if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8):
        raise ValueError('Independent accounting differs')


def check(destination):
    destination=Path(destination)
    ledger=load(destination/'ledger.json')
    summary=load(destination/'run'/'summary.json')
    if (sha(destination/'ledger.json') != summary['ledger_sha256']
            or len(summary['scenario_bindings']) != 40 or len(summary['selection_bindings']) != 2):
        raise ValueError('Incomplete or changed replay')
    reports={}
    for name,digest in {**summary['scenario_bindings'],**summary['selection_bindings']}.items():
        path=destination/'run'/name
        if sha(path)!=digest: raise ValueError('Report binding changed')
        reports[name]=load(path)
    open_marks=0
    for name in summary['scenario_bindings']:
        row=reports[name]; config=ledger['configs'][row['cost']]
        initial=config['initial_equity']
        total=0
        for trade in row['trades']:
            gross=trade['side']*(trade['exit']-trade['entry'])*trade['lots']*config['contract_size']
            close(gross,trade['gross_pnl'])
            close(trade['commission'],trade['lots']*config['commission_per_lot_round_turn'])
            close(gross-trade['commission']+trade['swap'],trade['net_pnl'])
            opened=int(datetime.fromisoformat(trade['opened']).timestamp()*1000)
            if opened<row['evaluation_start_ms']: raise ValueError('Trade entered during warmup')
            total+=trade['net_pnl']
        close(total,row['metrics']['net_pnl'])
        close(sum(t['commission'] for t in row['trades']),row['metrics']['commission'])
        close(sum(t['swap'] for t in row['trades']),row['metrics']['swap'])
        previous=initial
        for key in sorted(row['quarters']):
            mark=row['period_closing_marks'].get(key)
            equity=previous
            if mark:
                t=datetime.fromtimestamp(mark['time_msc']/1000,timezone.utc)
                if key != f'{t.year}-Q{(t.month-1)//3+1}': raise ValueError('Boundary mark belongs to another quarter')
                equity=mark['balance']
                position=mark['position']
                if position:
                    open_marks+=1
                    quote=mark['bid'] if position['side']==1 else mark['ask']
                    equity+=position['side']*(quote-position['entry'])*position['lots']*config['contract_size']
                close(equity,mark['equity'])
            close(equity-previous,row['quarters'][key])
            previous=equity
        close(previous-initial,total)
        for year,annual in row['years'].items():
            close(sum(v for k,v in row['quarters'].items() if k.startswith(year)),annual['net_pnl'])
            count=sum(datetime.fromisoformat(t['closed']).year==int(year) for t in row['trades'])
            if count!=annual['closed_trades']: raise ValueError('Annual closed trade count differs')
        close(row['net_winning_trade_sum'],sum(t['net_pnl'] for t in row['trades'] if t['net_pnl']>0))
        close(row['net_losing_trade_sum'],sum(t['net_pnl'] for t in row['trades'] if t['net_pnl']<0))
    for name in summary['selection_bindings']:
        choice=reports[name]
        inputs=[]
        fields=('candidate','cost','training_start','training_end_exclusive','years','quarters',
                'closed_trades','net_winning_trade_sum','net_losing_trade_sum','max_tick_drawdown')
        for source,digest in choice['training_report_bindings'].items():
            if source not in summary['scenario_bindings'] or digest != summary['scenario_bindings'][source]:
                raise ValueError('Choice is not bound to these training reports')
            inputs.append({k:reports[source][k] for k in fields})
        canonical=json.dumps(sorted(inputs,key=lambda r:(r['candidate'],r['cost'])),sort_keys=True,
                             allow_nan=False,separators=(',',':'))
        if hashlib.sha256(canonical.encode()).hexdigest()!=choice['training_inputs_sha256']:
            raise ValueError('Training-only choice input digest differs')
    for selected in summary['selected_tests']:
        if selected['candidate']=='CASH':
            close(selected['metrics']['net_pnl'],0)
            if selected['positive_edge_screen_passed']: raise ValueError('Cash cannot pass the edge screen')
        else:
            name=f"{selected['fold']}-test-{selected['candidate']}-{selected['cost']}.json"
            if selected['metrics'] != reports[name]['metrics']: raise ValueError('Selected test result differs')
    return {'status':'independent_report_arithmetic_matches','scenarios':40,'choices':2,
            'open_position_boundary_marks_checked':open_marks,'synthetic':ledger['synthetic'],
            'summary_sha256':sha(destination/'run'/'summary.json'),
            'market_data_eligibility_verified':False,'demo_execution_ready':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=check(args.destination)
    if args.report:
        with args.report.open('x',encoding='utf-8') as output:
            json.dump(result,output,indent=2,sort_keys=True);output.write('\n')
    print(json.dumps(result,indent=2))
