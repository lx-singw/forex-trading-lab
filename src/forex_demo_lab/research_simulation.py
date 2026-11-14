"""One candidate per offline account, with common warmup and inherited risk controls."""
from dataclasses import asdict
from datetime import datetime

from .strategies import CANDIDATES, decide
from .tick_simulation import TickSimulator


class ResearchTickSimulator(TickSimulator):
    def __init__(self, config, candidate="C00", evaluation_start_ms=0):
        super().__init__(config)
        if candidate not in CANDIDATES:
            raise ValueError("Unknown candidate")
        if type(evaluation_start_ms) is not int or evaluation_start_ms < 0 or evaluation_start_ms % 3600000:
            raise ValueError("Evaluation start must be an explicit hourly millisecond boundary")
        self.candidate = candidate
        self.evaluation_start_ms = evaluation_start_ms
        self.decision_log = []

    def _history_limit(self):
        return 201

    def _decision(self):
        start = self.current["hour"] * 3600000
        if len(self.history) < 201 or start < self.evaluation_start_ms:
            return 0, 0
        decision = decide(self.candidate, self.history, self.config)
        self.decision_log.append({"hour_start_ms": start, **asdict(decision)})
        return decision.side, decision.stop_distance

    def metrics(self):
        result = super().metrics()
        evaluated = sum(int(datetime.fromisoformat(p["time"]).timestamp() * 1000)
                        >= self.evaluation_start_ms for p in self.curve)
        result.update(evaluation_hours=evaluated, warmup_hours=len(self.curve) - evaluated,
                      bar_exposure=self.exposed_bars / evaluated if evaluated else 0)
        return result

    @classmethod
    def restore(cls, value, config, *, candidate, evaluation_start_ms):
        result = super().restore(value, config)
        if result.candidate != candidate or result.evaluation_start_ms != evaluation_start_ms:
            raise ValueError("Checkpoint candidate or evaluation boundary mismatch")
        return result
