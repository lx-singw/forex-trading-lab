"""Versioned offline diagnostics; original frozen execution classes remain intact."""
import json

from .tick_simulation import TickSimulator
from .research_simulation import ResearchTickSimulator

METRIC_VERSION = 'executable_fill_equity_019b_v1'


class _ExecutableFillEquity:
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.execution_metric_version=METRIC_VERSION

    def _mark(self,bid,ask):
        equity=self.equity(bid,ask-bid)
        p=self.position
        if p is not None:
            quote=bid if p.side==1 else ask
            stop=quote<=p.stop if p.side==1 else quote>=p.stop
            target=quote>=p.target if p.side==1 else quote<=p.target
            if stop or target:
                price=quote-p.side*self.config.slippage_pips*.0001 if stop else p.target
                gross=p.side*(price-p.entry)*p.lots*self.config.contract_size
                exit_fee=p.lots*self.config.commission_per_lot_round_turn/2
                # Preview the fill already modeled on this quote, including its fee.
                # Keep execution itself in inherited step_tick/_close.
                equity=self.balance+gross-exit_fee
        self.peak_tick_equity=max(self.peak_tick_equity,equity)
        self.max_tick_drawdown=max(self.max_tick_drawdown,(self.peak_tick_equity-equity)/self.peak_tick_equity)
        self.observe_loss(equity)
        self.last_equity=equity

    @classmethod
    def restore(cls,value,config,**kwargs):
        try:
            state=json.loads(value)['payload']['state']
            if state.get('execution_metric_version')!=METRIC_VERSION:
                raise ValueError('Execution metric checkpoint version mismatch; replay required')
        except (KeyError,TypeError,json.JSONDecodeError) as exc:
            raise ValueError('Invalid execution metric checkpoint') from exc
        return super().restore(value,config,**kwargs)


class ExecutableEquityTickSimulator(_ExecutableFillEquity,TickSimulator):
    """Offline baseline with fill-consistent peak and tick drawdown."""


class ExecutableEquityResearchTickSimulator(_ExecutableFillEquity,ResearchTickSimulator):
    """Offline fixed candidates with the same versioned equity diagnostic."""
