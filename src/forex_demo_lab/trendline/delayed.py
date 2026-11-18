"""Frozen trigger evidence and waiting bounds for invented DLY setups."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from . import lifecycle

EXPIRY_BARS = 10


@dataclass(frozen=True)
class AwaitingSafety:
    line_state: lifecycle.State
    trigger_index: int
    trigger_frame_id: str
    trigger_close: Decimal
    expires_at: int

    @property
    def direction(self):
        return "LONG" if self.line_state.line.ray.kind == "resistance" else "SHORT"

    def guard(self, bar, index, atr, *, data_gap, search_incomplete):
        if index - self.trigger_index >= EXPIRY_BARS or bar.available >= self.expires_at:
            return "EXPIRED", "DLY_EXPIRED"
        if data_gap:
            return "INVALIDATED", "DATA_GAP"
        if search_incomplete:
            return "INVALIDATED", "SEARCH_INCOMPLETE"
        if self.line_state.line.ray.correct_side_distance(index, bar.close) > 0:
            return "INVALIDATED", "FAILED_BREAK"
        if atr is None:
            return "INVALIDATED", "ATR_UNAVAILABLE"
        move = Fraction(bar.close) - Fraction(self.trigger_close)
        if (move if self.direction == "LONG" else -move) > atr:
            return "INVALIDATED", "CHASE_LIMIT"
        return None

    def record(self, state, reason=None):
        return {
            "line_id": self.line_state.line_id,
            "group_id": self.line_state.group_id,
            "direction": self.direction,
            "trigger_index": self.trigger_index,
            "trigger_frame_id": self.trigger_frame_id,
            "trigger_close": str(self.trigger_close),
            "expires_at": self.expires_at,
            "state": state,
            "reason": reason,
        }
