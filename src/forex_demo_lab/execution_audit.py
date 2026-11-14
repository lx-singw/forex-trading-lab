"""Frozen synthetic events and Decimal cash ledger, independent of simulators."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
import json
import math
from pathlib import Path

D = lambda value: Decimal(str(value))
HOUR = 3_600_000
START = datetime(2024, 1, 3, 22, tzinfo=timezone.utc)


def scenarios():
    config = json.loads(Path('config/baseline.json').read_text())
    config['leverage'] = 10.0
    paths = []

    def path(name, side, events, *, distance='.001', overrides=None, midday=False, decisions=None):
        start = START.replace(hour=12) if midday else START
        cfg = {**config, **(overrides or {})}
        points = []
        for sequence, event in enumerate(events):
            time = start + timedelta(milliseconds=event['offset_ms'])
            points.append(dict(sequence=sequence, time_msc=int(time.timestamp())*1000+time.microsecond//1000,
                               bid=event['bid'], ask=event['ask']))
        paths.append(dict(case_id=name, start=start.isoformat(), config=cfg, side=side,
                          distance=distance, decision_mode='injected',
                          decisions=decisions or [{'offset_ms': HOUR, 'side': side, 'distance': distance}],
                          ticks=points, events=[{k:v for k,v in e.items() if k not in ('bid','ask','offset_ms')} for e in events]))

    def event(hour, bid=1.1, ask=None, *, ms=0, open=False, exit=None, reset=False, units=0, paused=False):
        return dict(offset_ms=hour*HOUR+ms, bid=bid, ask=bid+.0001 if ask is None else ask,
                    open=open, exit=exit, reset=reset, rollover_units=units, paused=paused)

    seed = event(0, reset=True)
    opening = event(1, open=True)
    for side in (1,-1):
        label = 'long' if side == 1 else 'short'
        bad = 1.09 if side == 1 else 1.11
        path(label+'_rollover_stop_gap', side, [seed, opening,
             event(2,bad,exit='stop_tick',reset=True,units=3,paused=True)])
        good = 1.104 if side == 1 else 1.096
        path(label+'_target_overshoot', side, [seed, opening, event(1,good,ms=100,exit='target_tick')])
        path(label+'_ask_widening', side, [seed, opening,
             event(1,1.1,1.105,ms=100,exit='stop_tick' if side == -1 else None,paused=side == -1)])
        zero_seed = event(0,1.1,1.1,reset=True)
        zero_open = event(1,1.1,1.1,open=True)
        recovery = 1.1001 if side == 1 else 1.0999
        path(label+'_swap_pause_recovery', side, [zero_seed,zero_open,
             event(2,1.1,1.1,reset=True,units=3,paused=True),
             event(2,recovery,recovery,ms=100,paused=True)],
             overrides=dict(slippage_pips=0.0,daily_loss_fraction=.0001))
        path(label+'_skipped_rollovers', side, [seed,opening,
             event(2,reset=True,units=3),event(98,reset=True,units=2)],distance='.01')
        # Entry spread, slip and commission alone exceed the tighter diagnostic cap.
        path(label+'_entry_cost_pause_target', side, [seed,
             event(1,open=True,paused=True),event(1,good,ms=100,exit='target_tick',paused=True),
             event(2,paused=True),event(3,paused=True)],midday=True,
             overrides=dict(daily_loss_fraction=.0003),
             decisions=[dict(offset_ms=i*HOUR,side=side,distance='.001') for i in (1,2,3)])
        bad = 1.08 if side == 1 else 1.12
        path(label+'_gap_pause_next_day', side, [seed,opening,
             event(2,bad,exit='stop_tick',paused=True),event(3,paused=True),
             event(12,reset=True),event(13,open=True)],midday=True,
             decisions=[dict(offset_ms=i*HOUR,side=side,distance='.001') for i in (1,2,3,12,13)])

    cases = []
    for value in paths:
        for engine in ('tick','research'):
            cases.append({**deepcopy(value), 'case_id':value['case_id']+'_'+engine, 'engine':engine})
    # Actual fixed C04, not the injected execution probe. Last close breaks a flat channel.
    for side in (1,-1):
        start = START; ticks=[]; events=[]
        close = 1.101 if side == 1 else 1.099
        for index in range(202):
            instant = start+timedelta(hours=index)
            price = 1.1 if index < 200 else close
            ticks.append(dict(sequence=index,time_msc=int(instant.timestamp())*1000,bid=price,ask=price+.0001))
            events.append(dict(open=index==201,exit=None,
                               reset=index==0 or instant.date()!=(instant-timedelta(hours=1)).date(),
                               rollover_units=0,paused=False))
        ticks.append(dict(sequence=202,time_msc=ticks[-1]['time_msc']+100,
                          bid=1.105 if side==1 else 1.095,ask=1.1051 if side==1 else 1.0951))
        events.append(dict(open=False,exit='target_tick',reset=False,rollover_units=0,paused=False))
        cases.append(dict(case_id='c04_actual_'+('long' if side==1 else 'short'),engine='research',
                          start=start.isoformat(),config=deepcopy(config),side=side,
                          distance=str(D('.002')/D(14)),decision_mode='actual_c04',decisions=[],
                          ticks=ticks,events=events))
    for case in cases:
        case['expected'] = reference(case)
    return cases


def reference(case):
    """Apply declared events, not price-trigger decisions; independent decimal money."""
    cfg=case['config']; initial=D(cfg['initial_equity']); balance=initial
    position=None; trades=[]; trace=[]; previous_equity=initial; daily_ref=initial; paused=False
    peak=initial; drawdown=D(0)
    slip=D(cfg['slippage_pips'])*D('.0001'); contract=D(cfg['contract_size'])

    def equity(tick):
        if position is None:return balance
        quote=D(tick['bid'] if position['side']==1 else tick['ask'])
        return balance+D(position['side'])*(quote-position['entry'])*position['lots']*contract

    def output(tick):
        return dict(balance=float(balance),equity=float(equity(tick)),daily_reference=float(daily_ref),
                    peak_tick_equity=float(peak),max_tick_drawdown=float(drawdown),
                    paused=paused,position={k:float(v) if isinstance(v,Decimal) else v for k,v in position.items()} if position else None,
                    trades=deepcopy(trades))

    def close(tick,reason):
        nonlocal balance,position
        p=position
        if p is None:raise ValueError('Annotated exit without position')
        price=(p['entry']+D(p['side'])*D(case['distance'])*D(cfg['reward_risk']) if reason=='target_tick'
               else D(tick['bid'] if p['side']==1 else tick['ask'])-D(p['side'])*slip)
        gross=D(p['side'])*(price-p['entry'])*p['lots']*contract
        fee=p['lots']*D(cfg['commission_per_lot_round_turn'])/2
        balance+=gross-fee
        trades.append(dict(side=p['side'],lots=float(p['lots']),entry=float(p['entry']),exit=float(price),
                           reason=reason,gross_pnl=float(gross),commission=float(2*fee),swap=float(p['swap']),
                           net_pnl=float(gross-2*fee+p['swap'])))
        position=None

    if len(case['ticks'])!=len(case['events']) or not case['ticks']:raise ValueError('Event inventory differs')
    previous_ms=None
    for i,(tick,event) in enumerate(zip(case['ticks'],case['events'])):
        instant=datetime.fromtimestamp(tick['time_msc']/1000,timezone.utc)
        if (tick['sequence']!=i or instant.year!=2024 or instant.month!=1 or
                previous_ms is not None and tick['time_msc']<previous_ms):raise ValueError('Synthetic tick bounds/order differ')
        if event['reset']:
            daily_ref=previous_equity;paused=False
        if event['rollover_units']:
            if position is None:raise ValueError('Rollover annotation without position')
            rate=D(cfg['swap_long_per_lot'] if position['side']==1 else cfg['swap_short_per_lot'])
            amount=rate*position['lots']*D(event['rollover_units'])
            balance+=amount;position['swap']+=amount
        if event['open']:
            if position is not None or paused:raise ValueError('Illegal annotated opening')
            side=case['side']; distance=D(case['distance'])
            entry=D(tick['ask'] if side==1 else tick['bid'])+D(side)*slip
            risk_per_lot=(distance+slip)*contract+D(cfg['commission_per_lot_round_turn'])
            risk_volume=balance*D(cfg['risk_fraction'])/risk_per_lot
            margin_volume=balance/(entry*contract/D(cfg['leverage'])+D(cfg['commission_per_lot_round_turn'])/2)
            step=D(cfg['lot_step']); lots=(min(risk_volume,margin_volume,D(cfg['lot_max']))/step).to_integral_value(rounding=ROUND_FLOOR)*step
            if lots<D(cfg['lot_min']):raise ValueError('Annotated size below minimum')
            fee=lots*D(cfg['commission_per_lot_round_turn'])/2;balance-=fee
            position=dict(side=side,lots=lots,entry=entry,stop=entry-D(side)*distance,
                          target=entry+D(side)*distance*D(cfg['reward_risk']),swap=D(0))
        if equity(tick)<=daily_ref*(1-D(cfg['daily_loss_fraction']))+D('1e-9'):paused=True
        if event['exit']:close(tick,event['exit'])
        if equity(tick)<=daily_ref*(1-D(cfg['daily_loss_fraction']))+D('1e-9'):paused=True
        if paused is not event['paused']:raise ValueError('Declared pause disagrees with independent cash ledger: '+case['case_id'])
        mark=equity(tick);peak=max(peak,mark);drawdown=max(drawdown,(peak-mark)/peak)
        trace.append(output(tick));previous_equity=mark;previous_ms=tick['time_msc']
    last=case['ticks'][-1]
    if position is not None:close(last,'end_of_sample')
    if equity(last)<=daily_ref*(1-D(cfg['daily_loss_fraction']))+D('1e-9'):paused=True
    mark=equity(last);peak=max(peak,mark);drawdown=max(drawdown,(peak-mark)/peak)
    return dict(trace=trace,final=output(last))


def compare(actual, expected, *, label='result'):
    """Exact inventories/types, bounded float errors; return number of leaf checks."""
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or set(actual)!=set(expected):raise ValueError(label+': fields differ')
        return sum(compare(actual[k],v,label=label+'.'+k) for k,v in expected.items())
    if isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected):raise ValueError(label+': inventory differs')
        return sum(compare(a,e,label=label+f'[{i}]') for i,(a,e) in enumerate(zip(actual,expected)))
    if type(expected) is float:
        tolerance=1e-12 if label.rsplit('.',1)[-1] in ('lots','entry','stop','target','exit') else 1e-8
        if type(actual) not in (int,float) or not math.isfinite(actual) or abs(actual-expected)>tolerance:
            raise ValueError(label+': numeric value differs')
    elif type(actual) is not type(expected) or actual!=expected:raise ValueError(label+': value differs')
    return 1
