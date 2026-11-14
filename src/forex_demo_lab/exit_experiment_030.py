"""Single, cost-aware protective stop for offline development replay only."""
from dataclasses import asdict
import json
import math

from .strategy_experiment_028 import Experiment028Simulator, decision

CANDIDATES = ('C00', 'C05', 'C06', 'C07', 'C08')
PARENTS = {'C07': 'C05', 'C08': 'C06'}
VERSION = 'single_protective_stop_030_v1'


def protection(entry, initial_risk, lots, side, swap, bid, ask, config):
    """Return the first eligible level/net; never inspect a subsequent quote."""
    volume = lots*config.contract_size
    slip = config.slippage_pips*.0001
    fee = lots*config.commission_per_lot_round_turn
    quote = bid if side == 1 else ask
    net = side*(quote-side*slip-entry)*volume-fee+swap
    if net < .5*initial_risk:
        return None
    return entry+side*((fee-swap)/volume+slip), net


class Experiment030Simulator(Experiment028Simulator):
    def __init__(self, config, candidate='C00', evaluation_start_ms=0):
        if candidate not in CANDIDATES:
            raise ValueError('Unknown 030 candidate')
        super().__init__(config, PARENTS.get(candidate, candidate), evaluation_start_ms)
        self.candidate = candidate
        self.protection_experiment_version = VERSION
        self.pending_protection = None
        self.protection_lineage = []

    def _decision(self):
        start = self.current['hour']*3600000
        if len(self.history) < 201 or start < self.evaluation_start_ms:
            return 0, 0
        value = decision(PARENTS.get(self.candidate, self.candidate), self.history, self.config)
        self.decision_log.append({'hour_start_ms': start, **asdict(value)})
        return value.side, value.stop_distance

    def _open(self, bar, side, distance):
        had_position = self.position is not None
        super()._open(bar, side, distance)
        if not had_position and self.position is not None:
            p = self.position
            self.pending_protection = dict(initial_stop=p.stop,
                initial_risk=abs(p.entry-p.stop)*p.lots*self.config.contract_size,
                initial_distance=abs(p.entry-p.stop), arm=None)

    def _close(self, bar, exit_price, reason):
        if self.pending_protection is None:
            raise ValueError('Missing original risk lineage')
        original = self.pending_protection
        super()._close(bar, exit_price, reason)
        self.protection_lineage.append(dict(trade_index=len(self.trades)-1, **original))
        self.pending_protection = None

    def step_tick(self, tick):
        accepted = super().step_tick(tick)
        if not accepted or self.candidate not in PARENTS or self.position is None:
            return accepted
        record, p = self.pending_protection, self.position
        if record['arm'] is not None:
            return accepted
        result = protection(p.entry, record['initial_risk'], p.lots, p.side, p.swap,
                            tick['bid'], tick['ask'], self.config)
        if result is None:
            return accepted
        level, net = result
        new = max(p.stop, level) if p.side == 1 else min(p.stop, level)
        quote = tick['bid'] if p.side == 1 else tick['ask']
        if not math.isfinite(new) or new <= 0 or not p.side*(quote-new) > 0 or not p.side*(p.target-new) > 0:
            raise ValueError('Invalid protective stop')
        record['arm'] = dict(sequence=tick['sequence'], time_msc=tick['time_msc'],
            old_stop=p.stop, new_stop=new, initial_risk=record['initial_risk'],
            accrued_swap=p.swap, trigger_net=net)
        p.stop = new
        return accepted

    @classmethod
    def restore(cls, value, config, *, candidate, evaluation_start_ms):
        try:
            state = json.loads(value)['payload']['state']
            if state.get('protection_experiment_version') != VERSION:
                raise ValueError('030 checkpoint version mismatch')
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid 030 checkpoint') from exc
        return super().restore(value, config, candidate=candidate, evaluation_start_ms=evaluation_start_ms)
