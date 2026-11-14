# Elliott146 — explicit session observation component

14 November 2026. Implements a separately typed, invented-input calendar and
causal aggregation component from section5 of the approved144 plan. This is one
part of the pending qualified-input work; it does not enable a market runner.

## Implemented behavior

`elliott_sessions_146.py` requires a complete, immutable, bounded UTC schedule.
Every interval is either a declared session or an explicit closure. Session H1
and H4 edges must cover the entire session, agree at parent/child boundaries and
have the declared durations. No offset, holiday or closure is inferred from a
server label or from a lack of prices. Anonymous session labels and a fixed
invented2000–2003 domain separate this contract from an actual market source.

The component supports declared23/24/25-hour days, non-midnight opens and explicitly
opted-in shorter sessions, including a shortened terminal H1 observation. H4 bars
are four hours except the terminal session bucket, which can be shorter. This is
an explicit component profile: other bar alignments and sessions with internal
breaks remain unsupported. These constructed examples verify handling of varied
UTC durations; they do not establish any provider's timezone or DST rules.

Completed H1 observations carry exact window bounds, receipt availability, valid
OHLC and an immutable SHA256 lineage declaration. Derived H4/D1 observations use
every scheduled child exactly once in source order. A missing child blocks its
parent; later prices and nominal session close never fill it. Publication is the
maximum of child receipt times and the scheduled end plus the frozen finalization
hold. A late child can publish a parent only at its actual later availability.
Same-clock publication orders D1, H4, H1 deterministically.

Receipt clocks cannot reverse. A delayed earlier source hour may arrive after a
later hour, without rewriting any earlier published prefix. Duplicate/revised
observations, closed-period observations and mismatched bounds reject before
state changes. The invented scope has a bounded60-second receipt tail; unknown
calendar extensions reject rather than assuming continued closure.

`consecutive()` distinguishes adjacent scheduled bars across a declared closure
from a skipped scheduled bar. Coverage reports distinguish no completed bar from
ready and missing completed observations; any historical missing scheduled bar
keeps that timeframe's coverage blocked, even when a newer bar has arrived.
Complete counts are observed bars, not self-declared warmup counts or admission.

Checkpoints bind the calendar, component/contracts source bytes, receipt clock
and observation journal. Restore reconstructs and validates that journal; altered
calendars, source bindings, duplicate observations and receipt reversals reject.
The checksum detects changes against its bound record; it is not provider
authentication or an independently certified evidence signature.

## Verification and example

**59 tests pass together:31 new session checks and the existing28 study145 checks.**
The prior172 strategy tests were not rerun. Their exact runtime bindings and all46
frozen-control source bindings were compared with the retained172-test snapshot
and are unchanged. This is not a combined231-test invocation.

Checks cover23/24/25-hour and partial sessions, explicit closure adjacency, gaps,
strict boundaries, exact OHLC, lineage, delayed/finalized publication, receipt
versus source ordering, unchanged output at every tested prefix, restart at every
tested prefix, pending finalization, corrupt checkpoints and the public CLI.
Existing market admission still retains all16 cells as unavailable, and the
existing demo submission boundary remains closed.

The public CLI accepts only an output directory and runs its embedded invented
23-hour session /48-hour closure /25-hour session example. It captures the calendar
identity before constructing prices. One child is deliberately delayed until
after the second session: D1 coverage first reports missing, then ready after its
receipt. Continuous and restored paths agree. It computes no trading returns and
accepts no external price file, source, account or calendar argument.

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_sessions_146 test_elliott_study_145 -v
PYTHONPATH=src python3 scripts/elliott-sessions-146.py NEW-OUTPUT-DIRECTORY
```

See the [portable verification record](evidence/elliott-sessions-146/README.md).
The full source snapshot and generated demonstration remain under ignored local
`reports/elliott-sessions-146-verification-001/` and
`reports/elliott-sessions-146-demo-001/` respectively.

## Remaining work

The component is outside `elliott_full/` and is not connected to the strategy,
frozen controls, study145 qualification or native APIs. Existing continuous-UTC
context and setup coverage rules retain their prior behavior. Its report has a
distinct invented kind that the existing replay bundle validator rejects.

OHLC and a lineage hash do not prove underlying quote coverage, original clock
uncertainty, executable bid/ask, actual session evidence or costs. Session-aware
strategy/context coverage and the unchanged-control adapter still need explicit
integration, including a declared policy for late out-of-source-order bars that
cannot rewrite prior decisions. Old controls' UTC daily interface must remain
frozen; unsupported calendar inputs must stay unavailable in that adapter.

Qualified source/calendar/cost/run admission, wider pattern/fault acceptance and
disabled native demo reconciliation remain unfinished. No source or capture dates
are assigned, protected date boundaries are unchanged, and no account/API or
actual market price data was accessed. Orders and market cells remain unavailable.
