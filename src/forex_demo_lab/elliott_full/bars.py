"""Sampled midpoint bars with explicit finalization. Invented replay only."""
from .contracts import Bar, D, digest

PERIOD = {"H1":3600000,"H4":14400000,"D1":86400000}


def aggregate(quotes, timeframe, start, available, max_gap_ms=2000):
    if timeframe not in PERIOD or type(start) is not int or type(available) is not int:
        raise ValueError("bar boundary")
    end = start+PERIOD[timeframe]
    if available < end or type(max_gap_ms) is not int or not 0 < max_gap_ms <= 2000:
        raise ValueError("finalizer/coverage policy")
    selected = [q for q in quotes if start <= q.source < end]
    if not selected or any(q.time > available or q.time-q.source > 2000 or not q.session_open for q in selected):
        raise ValueError("missing/unavailable observations")
    if selected[0].source-start > max_gap_ms or end-selected[-1].source > max_gap_ms:
        raise ValueError("edge coverage")
    if any(b.source <= a.source or b.source-a.source > max_gap_ms or b.time < a.time or b.sequence <= a.sequence for a,b in zip(selected,selected[1:])):
        raise ValueError("coverage/order")
    midpoint = [(q.bid+q.ask)/2 for q in selected]
    return Bar(timeframe,start,end,available,midpoint[0],max(midpoint),min(midpoint),midpoint[-1],
               digest([q.record() for q in selected]))
