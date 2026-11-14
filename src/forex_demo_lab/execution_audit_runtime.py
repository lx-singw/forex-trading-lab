"""Drive unchanged engines from fixed synthetic inputs; no broker APIs."""
from datetime import datetime
from .model import Config
from .tick_simulation import TickSimulator
from .research_simulation import ResearchTickSimulator


class InjectedTick019(TickSimulator):
    def __init__(self,config):
        super().__init__(config);self.audit_decisions={}

    def _decision(self):
        return tuple(self.audit_decisions.get(str(self.current['hour']*3600000),(0,0)))


class InjectedResearch019(ResearchTickSimulator):
    def __init__(self,config):
        super().__init__(config,candidate='C04',evaluation_start_ms=0);self.audit_decisions={}

    def _decision(self):
        return tuple(self.audit_decisions.get(str(self.current['hour']*3600000),(0,0)))


def make(case):
    cfg=Config(**case['config'])
    if case['decision_mode']=='actual_c04':
        boundary=case['ticks'][201]['time_msc']
        return ResearchTickSimulator(cfg,candidate='C04',evaluation_start_ms=boundary)
    cls=InjectedTick019 if case['engine']=='tick' else InjectedResearch019
    result=cls(cfg);start=int(datetime.fromisoformat(case['start']).timestamp())*1000
    result.audit_decisions={str(start+d['offset_ms']):[d['side'],float(d['distance'])] for d in case['decisions']}
    return result


def snapshot(sim):
    keys=('side','lots','entry','stop','target','swap')
    trade_keys=('side','lots','entry','exit','reason','gross_pnl','commission','swap','net_pnl')
    return dict(balance=sim.balance,equity=sim.last_equity,daily_reference=sim.day_start_equity,
                peak_tick_equity=sim.peak_tick_equity,max_tick_drawdown=sim.max_tick_drawdown,
                paused=sim.paused,position={k:getattr(sim.position,k) for k in keys} if sim.position else None,
                trades=[{k:t[k] for k in trade_keys} for t in sim.trades])


def restore(sim):
    if isinstance(sim,ResearchTickSimulator):
        return type(sim).restore(sim.checkpoint(),sim.config,candidate=sim.candidate,
                                 evaluation_start_ms=sim.evaluation_start_ms)
    return type(sim).restore(sim.checkpoint(),sim.config)


def run_case(case):
    sim=make(case);trace=[];checkpoints=[]
    for tick in case['ticks']:
        sim.step_tick(tick);trace.append(snapshot(sim));checkpoints.append(sim.checkpoint())
    sim.finish();final=snapshot(sim);complete=sim.checkpoint()
    restarts=[]
    for index,checkpoint in enumerate(checkpoints):
        restored=make(case)
        if isinstance(restored,ResearchTickSimulator):
            restored=type(restored).restore(checkpoint,restored.config,candidate=restored.candidate,
                                           evaluation_start_ms=restored.evaluation_start_ms)
        else:restored=type(restored).restore(checkpoint,restored.config)
        before=restored.checkpoint()
        duplicate=restored.step_tick(case['ticks'][index])
        no_change=before==restored.checkpoint()
        for tick in case['ticks'][index+1:]:restored.step_tick(tick)
        restored.finish();equal=restored.checkpoint()==complete
        finished_before=restored.checkpoint();restored.finish()
        restarts.append(dict(boundary=index,duplicate_return=duplicate,duplicate_no_change=no_change,
                             final_checkpoint_equal=equal,finish_idempotent=finished_before==restored.checkpoint()))
    result=dict(case_id=case['case_id'],engine=case['engine'],trace=trace,final=final,restarts=restarts)
    if case['decision_mode']=='actual_c04':result['decision_log']=sim.decision_log
    return result
