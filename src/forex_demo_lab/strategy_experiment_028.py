"""Fixed offline challengers, inherited risk controls and corrected fill equity."""
from dataclasses import asdict
import json

from .execution_metrics import ExecutableEquityResearchTickSimulator
from .strategies import Decision, decide

CANDIDATES = ('C00', 'C02', 'C04', 'C05', 'C06')
VERSION = 'fixed_challengers_028_v1'


def decision(candidate, history, config):
    if candidate not in CANDIDATES:
        raise ValueError('Unknown 028 candidate')
    if candidate in ('C00', 'C02', 'C04'):
        return decide(candidate, history, config)
    if len(history) < 201:
        return Decision(0, 0, 'warmup', {})
    if candidate == 'C05':
        original = decide('C04', history, config)
        if original.features.get('selected_mode') == 'trend':
            return Decision(original.side, original.stop_distance, 'trend_only:'+original.reason, original.features)
        return Decision(0, original.stop_distance, 'trend_only_abstain:'+original.reason, original.features)
    original = decide('C02', history, config)
    closes = [bar.close for bar in history]
    fast, slow = sum(closes[-50:])/50, sum(closes[-200:])/200
    direction = 1 if fast > slow else -1 if fast < slow else 0
    features = {**original.features, 'sma50': fast, 'sma200': slow, 'slow_direction': direction}
    confirmed = original.side != 0 and original.side == direction
    reason = 'confirmed_breakout' if confirmed else 'no_breakout' if not original.side else 'slow_direction_disagreement'
    return Decision(original.side if confirmed else 0, original.stop_distance, reason, features)


class Experiment028Simulator(ExecutableEquityResearchTickSimulator):
    """No execution API. Fill sequences support independent tick-equity checks."""
    def __init__(self, config, candidate='C00', evaluation_start_ms=0):
        if candidate not in CANDIDATES:
            raise ValueError('Unknown 028 candidate')
        super().__init__(config, 'C00', evaluation_start_ms)
        self.candidate = candidate
        self.strategy_experiment_version = VERSION
        self.processing_tick = None
        self.pending_entry_sequence = None
        self.fill_lineage = []

    def _decision(self):
        start = self.current['hour']*3600000
        if len(self.history) < 201 or start < self.evaluation_start_ms:
            return 0, 0
        value = decision(self.candidate, self.history, self.config)
        self.decision_log.append({'hour_start_ms': start, **asdict(value)})
        return value.side, value.stop_distance

    def step_tick(self, tick):
        self.processing_tick = tick
        try:
            return super().step_tick(tick)
        finally:
            self.processing_tick = None

    def _open(self, bar, side, distance):
        had_position = self.position is not None
        super()._open(bar, side, distance)
        if not had_position and self.position is not None:
            self.pending_entry_sequence = self.processing_tick['sequence']

    def _close(self, bar, exit_price, reason):
        tick = self.processing_tick if self.processing_tick is not None else self.last_tick
        entry = self.pending_entry_sequence
        if entry is None or tick is None:
            raise ValueError('Missing fill sequence lineage')
        super()._close(bar, exit_price, reason)
        self.fill_lineage.append(dict(trade_index=len(self.trades)-1,
                                      entry_sequence=entry, exit_sequence=tick['sequence']))
        self.pending_entry_sequence = None

    @classmethod
    def restore(cls, value, config, *, candidate, evaluation_start_ms):
        try:
            state = json.loads(value)['payload']['state']
            if state.get('strategy_experiment_version') != VERSION:
                raise ValueError('028 checkpoint version mismatch')
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid 028 checkpoint') from exc
        return super().restore(value, config, candidate=candidate, evaluation_start_ms=evaluation_start_ms)
