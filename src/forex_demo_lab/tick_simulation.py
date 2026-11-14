"""Full offline tick replay of the fixed closed-H1 baseline; no broker APIs."""
from datetime import datetime, timedelta, timezone
import math
from types import SimpleNamespace

from .model import Bar, signal
from .simulation import Simulator


class TickSimulator(Simulator):
    def __init__(self, config):
        super().__init__(config)
        if config.broker_timezone != "Etc/UTC":
            raise ValueError("Tick pilot supports explicitly assumed UTC daily reset only")
        self.current = None
        self.last_tick = None
        self.peak_tick_equity = config.initial_equity
        self.max_tick_drawdown = 0.0
        self.signals_observed = 0
        self.spread_rejections = 0

    def _mark(self, bid, ask):
        equity = self.equity(bid,ask-bid)
        self.peak_tick_equity = max(self.peak_tick_equity,equity)
        self.max_tick_drawdown = max(self.max_tick_drawdown,(self.peak_tick_equity-equity)/self.peak_tick_equity)
        self.observe_loss(equity)
        self.last_equity = equity

    def _history_limit(self):
        return self.config.slow + 1

    def _decision(self):
        return signal(self.history, self.config)

    def _complete_hour(self):
        c=self.current
        if c is None:return
        time=datetime.fromtimestamp(c["hour"]*3600,timezone.utc)
        self.history.append(Bar(time,c["open"],c["high"],c["low"],c["close"],c["spread_pips"]))
        self.history=self.history[-self._history_limit():]
        self.curve.append({"time":time.isoformat(),"equity":self.last_equity,"paused":self.paused})
        if c["exposed"]:self.exposed_bars+=1

    def step_tick(self, tick):
        if self.finished:raise ValueError("Simulation already finalized")
        if (set(tick)!={"sequence","time_msc","bid","ask"} or type(tick["sequence"]) is not int
                or type(tick["time_msc"]) is not int or tick["time_msc"]<0
                or not all(math.isfinite(tick[s]) for s in ("bid","ask")) or not 0<tick["bid"]<=tick["ask"]):
            raise ValueError("Invalid tick")
        if self.last_tick:
            if tick==self.last_tick:return False
            if tick["sequence"]!=self.last_tick["sequence"]+1 or tick["time_msc"]<self.last_tick["time_msc"]:
                raise ValueError("Conflicting, missing or out-of-order tick")
        elif tick["sequence"]!=0:
            raise ValueError("Tick sequence must start at zero")
        bid,ask=tick["bid"],tick["ask"]
        hour=tick["time_msc"]//3_600_000
        instant=datetime.fromtimestamp(tick["time_msc"]/1000,timezone.utc)
        new_hour=self.current is None or hour!=self.current["hour"]
        had_position=self.position is not None
        if new_hour:
            self._complete_hour()
            opening=Bar(datetime.fromtimestamp(hour*3600,timezone.utc),bid,bid,bid,bid,(ask-bid)/.0001)
            self._new_day(opening)
            self.current={"hour":hour,"open":bid,"high":bid,"low":bid,"close":bid,
                          "spread_pips":opening.spread_pips,"exposed":had_position}
        self._mark(bid,ask)
        if new_hour and not had_position and self.history and opening.time-self.history[-1].time==timedelta(hours=1):
            side,distance=self._decision()
            if side:
                self.signals_observed+=1
                if opening.spread_pips>self.config.max_spread_pips:self.spread_rejections+=1
                self._open(opening,side,distance)
                if self.position:self.position.opened=instant.isoformat()
        if self.position:
            self.current["exposed"]=True
            p=self.position
            quote=bid if p.side==1 else ask
            stopped=quote<=p.stop if p.side==1 else quote>=p.stop
            targeted=quote>=p.target if p.side==1 else quote<=p.target
            if stopped:
                self._close(SimpleNamespace(time=instant),quote-p.side*self.config.slippage_pips*.0001,"stop_tick")
            elif targeted:
                self._close(SimpleNamespace(time=instant),p.target,"target_tick")
        self.current["high"]=max(self.current["high"],bid)
        self.current["low"]=min(self.current["low"],bid)
        self.current["close"]=bid
        self._mark(bid,ask)
        self.last_tick=dict(tick)
        return True

    def finish(self):
        if self.finished:return
        if self.position:
            p=self.position;t=self.last_tick
            quote=t["bid"] if p.side==1 else t["ask"]
            self._close(SimpleNamespace(time=datetime.fromtimestamp(t["time_msc"]/1000,timezone.utc)),
                        quote-p.side*self.config.slippage_pips*.0001,"end_of_sample")
            self._mark(t["bid"],t["ask"])
        self._complete_hour()
        self.finished=True

    def metrics(self):
        return {**super().metrics(),"max_tick_drawdown":self.max_tick_drawdown,
                "signals_observed":self.signals_observed,"spread_rejections":self.spread_rejections,
                "ticks_processed":self.last_tick["sequence"]+1 if self.last_tick else 0}
