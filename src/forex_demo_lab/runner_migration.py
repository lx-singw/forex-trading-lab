"""Mechanical runner migration and independent software-control accounting."""
import csv
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal,ROUND_FLOOR
import gzip
import io
import json
from pathlib import Path

from .execution_audit import compare
from .observer_parity import digest

VERSION='executable_fill_equity_019b_v1'
ROOT=Path(__file__).resolve().parents[2]


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Migration site not unique: '+old[:75])
    return text.replace(old,new)


def generated_runner(source):
    source=replace_once(source,'from .research_simulation import ResearchTickSimulator',
        'from .execution_metrics import ExecutableEquityResearchTickSimulator as ResearchTickSimulator, METRIC_VERSION')
    source=replace_once(source,'def load(path):',
        "FIXED = FIXED + ('docs/WALK-FORWARD-020-PLAN.md',)\n\n\ndef load(path):")
    source=replace_once(source,"| {ROOT/'scripts/walk-forward-014.py',ROOT/'scripts/check-walk-forward-014.py'}",
        "| {ROOT/'scripts/walk-forward-014.py',ROOT/'scripts/check-walk-forward-014.py',\n"
        "                     ROOT/'scripts/walk-forward-020.py',ROOT/'scripts/check-walk-forward-020.py',\n"
        "                     ROOT/'scripts/migrate-walk-forward-020.py'}")
    source=source.replace('frozen_chronological_replay_014','frozen_chronological_replay_020')
    source=source.replace('completed_chronological_replay_014','completed_chronological_replay_020')
    source=replace_once(source,"'market_profitability_established': False, 'maximum_scenarios': 40}",
        "'market_profitability_established': False, 'maximum_scenarios': 40,\n"
        "        'runner_version': '020', 'metric_contract': METRIC_VERSION}")
    source=replace_once(source,"raise ValueError('Invalid replay ledger')",
        "raise ValueError('Invalid replay ledger; 020 requires a new freeze')\n"
        "    if ledger.get('runner_version') != '020' or ledger.get('metric_contract') != METRIC_VERSION:\n"
        "        raise ValueError('Runner or execution metric version mismatch')")
    source=replace_once(source,"results.append({'candidate': candidate, 'cost': cost,",
        "results.append({'candidate': candidate, 'cost': cost,\n"
        "            'runner_version': '020', 'metric_contract': METRIC_VERSION,\n"
        "            'peak_tick_equity': sim.peak_tick_equity,")
    source=replace_once(source,'choice.update(training_report_bindings=bindings, ledger_sha256=ledger_hash, synthetic=ledger[\'synthetic\'])',
        "choice.update(training_report_bindings=bindings, ledger_sha256=ledger_hash, synthetic=ledger['synthetic'],\n"
        "                      runner_version='020', metric_contract=METRIC_VERSION)")
    source=replace_once(source,"result = {'kind': 'completed_chronological_replay_020', 'ledger_sha256': ledger_hash,",
        "result = {'kind': 'completed_chronological_replay_020', 'ledger_sha256': ledger_hash,\n"
        "        'runner_version': '020', 'metric_contract': METRIC_VERSION,")
    return '# Migration 020: original 014 body with declared import/metadata/freeze sites only.\n'+source


def generated_cli(source):
    return replace_once(source,'from forex_demo_lab.walk_forward import YEARS, bound, freeze, load, review_gate, run, verify',
        'from forex_demo_lab.walk_forward_metrics import YEARS, bound, freeze, load, review_gate, run, verify')


def challenge(destination):
    """One fixed, sparse invented annual fixture; no strategy calls or market bytes."""
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    years={}
    for year in range(2020,2024):
        rows=[];start=int(datetime(year,1,1,tzinfo=timezone.utc).timestamp())*1000
        for hour in range(520):
            bid=1.101 if hour in (200,201) else 1.099 if hour in (300,301) else 1.1
            rows.append(dict(sequence=len(rows),time_msc=start+hour*3600000,bid=bid,ask=round(bid+.0001,4)))
            if hour in (201,301):
                bid=1.111 if hour==201 else 1.089
                rows.append(dict(sequence=len(rows),time_msc=start+hour*3600000+100,bid=bid,ask=round(bid+.0001,4)))
        path=destination/f'{year}-ticks.csv.gz'
        with path.open('xb') as binary,gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as zipped:
            with io.TextIOWrapper(zipped,encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=['sequence','time_msc','bid','ask']);writer.writeheader();writer.writerows(rows)
        meta=dict(kind='chronological_research_ticks',symbol='EURUSD',year=year,synthetic=True,
                  ticks=len(rows),first_ms=rows[0]['time_msc'],last_ms=rows[-1]['time_msc'],
                  data_sha256=digest(path.read_bytes()),source='fixed 020 synthetic target challenge; sparse January only')
        save(destination/f'{year}-provenance.json',meta)
        years[str(year)]=dict(data=path.name,provenance=f'{year}-provenance.json')
    save(destination/'review.json',dict(kind='synthetic_chronological_fixture',synthetic=True,
                                        performance_evaluation_ready=False,years={str(y):{} for y in range(2020,2024)}))
    save(destination/'bundle.json',dict(kind='chronological_ticks_input',synthetic=True,years=years,review='review.json'))


def save(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def without_metadata(value):
    ignored={'ledger_sha256','selection_sha256','runner_version','metric_contract','peak_tick_equity','max_tick_drawdown'}
    if isinstance(value,dict):return {k:without_metadata(v) for k,v in value.items() if k not in ignored}
    if isinstance(value,list):return [without_metadata(v) for v in value]
    return value


def compare_controls(old,new):
    if set(old)!=set(new) or len(old)!=40:raise ValueError('Scenario comparison inventory differs')
    checks=0;changes=[]
    for name in sorted(old):
        checks+=compare(without_metadata(new[name]),without_metadata(old[name]),label=name)
        before=old[name]['metrics']['max_tick_drawdown'];after=new[name]['metrics']['max_tick_drawdown']
        if after>before+1e-12:raise ValueError('Corrected drawdown unexpectedly increases: '+name)
        if abs(after-before)>1e-12:changes.append(dict(scenario=name,old=before,corrected=after))
    return dict(scenarios=40,unchanged_nonmetric_checks=checks,drawdown_changes=changes)


def equity_path(ticks,row,config):
    """Reconstruct executable marks from recorded fills and quotes, never a strategy."""
    d=lambda v:Decimal(str(v));balance=d(config['initial_equity']);initial=balance
    peak=initial;dd=d(0);position=None;previous_day=None;quarter_marks={};marks=0
    trades=row['trades'];opened={};closed={};carried={}
    ms=lambda stamp:int(datetime.fromisoformat(stamp).timestamp()*1000)
    for index,trade in enumerate(trades):
        opening=ms(trade['opened']);closing=ms(trade['closed'])
        if opening in opened or closing in closed:raise ValueError('Ambiguous fill inventory')
        if opening<row['evaluation_start_ms']:raise ValueError('Warmup trade in independent ledger')
        opened[opening]=(index,trade)
        if trade['reason']!='end_of_sample':closed[closing]=(index,trade)
    seen_open=set();seen_close=set();last=None
    contract=d(config['contract_size']);slip=d(config['slippage_pips'])*d('.0001')

    def close(index,trade,tick,reason):
        nonlocal balance,position
        if position is None or position['index']!=index:raise ValueError('Recorded close has no matching position')
        side=trade['side'];quote=d(tick['bid'] if side==1 else tick['ask'])
        if reason=='target_tick':
            price=d(trade['target'])
            if not (quote>=price if side==1 else quote<=price):raise ValueError('Target quote never triggers')
        else:
            price=quote-d(side)*slip
            if reason=='stop_tick' and not (quote<=d(trade['stop']) if side==1 else quote>=d(trade['stop'])):
                raise ValueError('Stop quote never triggers')
        compare(float(price),float(trade['exit']),label='trade.exit')
        fee=d(trade['lots'])*d(config['commission_per_lot_round_turn'])/2
        gross=d(side)*(price-d(trade['entry']))*d(trade['lots'])*contract
        compare(float(gross),float(trade['gross_pnl']),label='trade.gross_pnl')
        compare(float(position['swap']),float(trade['swap']),label='trade.swap')
        balance+=gross-fee;position=None;seen_close.add(index)

    for tick in ticks:
        stamp=tick['time_msc'];instant=datetime.fromtimestamp(stamp/1000,timezone.utc);today=instant.date()
        if previous_day is not None and previous_day!=today and position is not None:
            prior=previous_day;trade=position['trade']
            rate=d(config['swap_long_per_lot'] if trade['side']==1 else config['swap_short_per_lot'])
            units=0
            while prior<today:
                units+=0 if prior.weekday()>=5 else 3 if prior.weekday()==config['triple_swap_weekday'] else 1
                prior+=timedelta(days=1)
            amount=rate*d(trade['lots'])*d(units);balance+=amount;position['swap']+=amount
        if stamp in opened:
            index,trade=opened[stamp]
            if position is not None:raise ValueError('Independent ledger rejects stacked positions')
            side=trade['side']
            if side not in (1,-1):raise ValueError('Trade direction differs')
            entry=d(tick['ask'] if side==1 else tick['bid'])+d(side)*slip
            compare(float(entry),float(trade['entry']),label='trade.entry')
            distance=abs(d(trade['entry'])-d(trade['stop']))
            fee_per_lot=d(config['commission_per_lot_round_turn'])/2
            risk=(distance+slip)*contract+2*fee_per_lot
            volume=min(balance*d(config['risk_fraction'])/risk,
                       balance/(entry*contract/d(config['leverage'])+fee_per_lot),d(config['lot_max']))
            step=d(config['lot_step']);lots=(volume/step).to_integral_value(rounding=ROUND_FLOOR)*step
            compare(float(lots),float(trade['lots']),label='trade.lots')
            balance-=lots*fee_per_lot;position=dict(index=index,trade=trade,swap=d(0));seen_open.add(index)
        if stamp in closed:
            index,trade=closed[stamp];close(index,trade,tick,trade['reason'])
        equity=balance
        if position is not None:
            trade=position['trade'];side=trade['side'];quote=d(tick['bid'] if side==1 else tick['ask'])
            equity+=d(side)*(quote-d(trade['entry']))*d(trade['lots'])*contract
            # A recorded open position may not survive a modeled trigger.
            if (quote<=d(trade['stop']) if side==1 else quote>=d(trade['stop'])) or (
                    quote>=d(trade['target']) if side==1 else quote<=d(trade['target'])):
                raise ValueError('Position retained after executable trigger')
        peak=max(peak,equity);dd=max(dd,(peak-equity)/peak);marks+=1
        if stamp>=row['evaluation_start_ms']:
            quarter_marks[f'{instant.year}-Q{(instant.month-1)//3+1}']=equity
        previous_day=today;last=tick
    if position is not None:
        index=position['index'];trade=position['trade']
        if trade['reason']!='end_of_sample' or ms(trade['closed'])!=last['time_msc']:
            raise ValueError('Unclosed final position')
        close(index,trade,last,'end_of_sample');peak=max(peak,balance);dd=max(dd,(peak-balance)/peak)
        instant=datetime.fromtimestamp(last['time_msc']/1000,timezone.utc)
        quarter_marks[f'{instant.year}-Q{(instant.month-1)//3+1}']=balance
    if seen_open!=set(range(len(trades))) or seen_close!=set(range(len(trades))):raise ValueError('Unmatched trade times')
    compare(float(balance-initial),float(row['metrics']['net_pnl']),label='metrics.net_pnl')
    compare(float(peak),float(row['peak_tick_equity']),label='peak_tick_equity')
    compare(float(dd),float(row['metrics']['max_tick_drawdown']),label='max_tick_drawdown')
    compare(float(dd),float(row['max_tick_drawdown']),label='max_tick_drawdown')
    previous=initial
    for key,change in sorted(row['quarters'].items()):
        closing=quarter_marks.get(key,previous)
        compare(float(closing-previous),float(change),label='quarter.net_pnl');previous=closing
    return dict(tick_marks=marks,trades=len(trades),peak_tick_equity=float(peak),max_tick_drawdown=float(dd))
