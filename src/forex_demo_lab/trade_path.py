"""Frozen trade excursion attribution; no signal generation or order APIs."""
from datetime import datetime, timezone
import math


def milliseconds(text):
    dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('Explicit offset required')
    delta = dt.astimezone(timezone.utc)-datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days*86400000+delta.seconds*1000+delta.microseconds//1000


def same(a, b, tolerance=1e-8):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b) > tolerance:
        raise ValueError('Endpoint or source compatibility mismatch')


class TradePath:
    def __init__(self, trade, lineage, config):
        self.trade, self.lineage, self.config = trade, lineage, config
        self.start, self.end = lineage['entry_sequence'], lineage['exit_sequence']
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start <= self.end:
            raise ValueError('Invalid fill sequences')
        if trade['side'] not in (-1, 1) or trade['lots'] <= 0 or config['broker_timezone'] != 'Etc/UTC':
            raise ValueError('Invalid direction/volume/rollover')
        self.risk = abs(trade['entry']-trade['stop'])*trade['lots']*config['contract_size']
        if not math.isfinite(self.risk) or self.risk <= 0 or trade['side']*(trade['entry']-trade['stop']) <= 0:
            raise ValueError('Invalid initial risk')
        same(trade['commission'], trade['lots']*config['commission_per_lot_round_turn'])
        same(trade['entry_commission'], trade['commission']/2)
        self.swap, self.day, self.last_sequence, self.last_time = 0.0, None, None, None
        self.count = 0
        self.witnesses = {}

    def step(self, tick):
        seq, ms = tick['sequence'], tick['time_msc']
        if not self.start <= seq <= self.end or (self.last_sequence is None and seq != self.start) or (
                self.last_sequence is not None and seq != self.last_sequence+1):
            raise ValueError('Missing or out-of-order trade quote')
        if self.last_time is not None and ms < self.last_time:
            raise ValueError('Backward trade timestamp')
        if not all(math.isfinite(tick[k]) for k in ('bid', 'ask')) or not 0 < tick['bid'] <= tick['ask']:
            raise ValueError('Invalid trade quote')
        t, c = self.trade, self.config
        if seq == self.start:
            if ms != milliseconds(t['opened']):
                raise ValueError('Entry timestamp mismatch')
            expected = (tick['ask'] if t['side'] == 1 else tick['bid'])+t['side']*c['slippage_pips']*.0001
            same(expected, t['entry'], 1e-10)
        day = ms//86400000
        if self.day is not None and day != self.day:
            rate = c['swap_long_per_lot'] if t['side'] == 1 else c['swap_short_per_lot']
            for previous in range(self.day, day):
                weekday = (previous+3)%7
                multiplier = 0 if weekday >= 5 else 3 if weekday == c['triple_swap_weekday'] else 1
                self.swap += rate*t['lots']*multiplier
        self.day = day
        raw = tick['bid'] if t['side'] == 1 else tick['ask']
        price = raw-t['side']*c['slippage_pips']*.0001
        stop_region = t['side']*(raw-t['stop']) <= 0
        target_region = t['side']*(raw-t['target']) >= 0
        if seq < self.end and (stop_region or target_region):
            raise ValueError('Trade persisted beyond inherited exit boundary')
        if seq == self.end:
            if ms != milliseconds(t['closed']):
                raise ValueError('Exit timestamp mismatch')
            if t['reason'] == 'target_tick':
                if not target_region:
                    raise ValueError('Unreached target fill')
                price = t['target']
            elif t['reason'] == 'stop_tick':
                if not stop_region:
                    raise ValueError('Unreached stop fill')
            elif t['reason'] != 'end_of_sample':
                raise ValueError('Unknown modeled exit')
            same(price, t['exit'], 1e-10)
            same(self.swap, t['swap'])
        net = t['side']*(price-t['entry'])*t['lots']*c['contract_size']-t['commission']+self.swap
        value = dict(sequence=seq, time_msc=ms, bid=tick['bid'], ask=tick['ask'],
                     accrued_swap=self.swap, liquidation_price=price, net_pnl=net, net_r=net/self.risk)
        if 'maximum' not in self.witnesses or net > self.witnesses['maximum']['net_pnl']:
            self.witnesses['maximum'] = value
        if 'minimum' not in self.witnesses or net < self.witnesses['minimum']['net_pnl']:
            self.witnesses['minimum'] = value
        for key, hit in (('positive', net > 0), ('half_r', net >= .5*self.risk),
                         ('one_r', net >= self.risk), ('stop_region', stop_region)):
            if hit and key not in self.witnesses:
                self.witnesses[key] = value
        if seq == self.end:
            same(net, t['net_pnl'])
            self.witnesses['endpoint'] = value
        self.last_sequence, self.last_time = seq, ms
        self.count += 1

    def finish(self):
        if self.last_sequence != self.end or self.count != self.end-self.start+1:
            raise ValueError('Incomplete trade path')
        t = self.trade
        prior = lambda key: key in self.witnesses and self.witnesses[key]['sequence'] < self.end
        return dict(trade_index=self.lineage['trade_index'], side=t['side'],
            entry_sequence=self.start, exit_sequence=self.end, quote_count=self.count,
            opened=t['opened'], closed=t['closed'], exit_reason=t['reason'],
            net_pnl=t['net_pnl'], initial_cash_risk=self.risk,
            maximum_net_r=self.witnesses['maximum']['net_r'], minimum_net_r=self.witnesses['minimum']['net_r'],
            prior_positive=prior('positive'), prior_half_r=prior('half_r'), prior_one_r=prior('one_r'),
            duration_hours=(milliseconds(t['closed'])-milliseconds(t['opened']))/3600000,
            first_positive_hours=(self.witnesses['positive']['time_msc']-milliseconds(t['opened']))/3600000 if 'positive' in self.witnesses else None,
            first_stop_region_hours=(self.witnesses['stop_region']['time_msc']-milliseconds(t['opened']))/3600000 if 'stop_region' in self.witnesses else None,
            witnesses=self.witnesses)
