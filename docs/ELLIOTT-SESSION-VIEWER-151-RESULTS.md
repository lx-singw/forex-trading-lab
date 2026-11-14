# Elliott151 — session-aware saved-report viewer

15 November 2026. Adds a local, read-only viewer for the saved EW_FULL_V1 accounts
from the invented session149 comparison pipeline. No trading/runtime, risk, cost,
fixture-generator or frozen-control source changes. Packaging includes the new
HTML template. This advances stage D of the144 plan; it does not complete the
original plan or qualify market performance.

## What can be inspected

The new CLI accepts an existing prepared partition and base/adverse profile,
validates its current source and input-file bindings, then writes a new directory
outside that partition. The export contains standalone `replay.html` and a
`manifest.json` identifying report, prepared inputs, runtime, viewer and HTML bytes.
Existing files are never overwritten. The report reader has a256MiB limit and
rejects live/market/control-account labels and unfinished or misaligned records.

The cursor follows the recorded publication and raw quote order. H1/H4/D1 candles
and snapshots are available only after their own publication row. Same-timestamp
publications cannot borrow later frame snapshots or fills. Entry/exit effects and
the corresponding quote check appear atomically. Financing appears when the quote
was received, retaining its original effective date in the evidence. Final cash
and later fills are not backfilled into earlier cursor states.

Controls navigate signals, fills, skipped H1 decisions and quote checks. The chart
shows available candles, confirmed count anchors, original protection levels and
fills. The count selector preserves every recorded interpretation's order; it
does not prefer the newest terminal or rerank counts using later results. Context,
coverage, search/window diagnostics, signals, quote gates and cancellation reasons
are inspectable. Missing anchors in the bounded saved node list remain unplotted.
Cancellation records lack an event ordinal, so they appear conservatively after
all other events at their recorded timestamp; this timing limitation is explicit.

No remote assets, analytics or network calls are used. JSON is escaped before
embedding, content is inserted as text, and the page's content security policy
disables connections and external resources. The viewer displays recorded evidence;
it does not independently recompute or authenticate trading decisions. Hashes
identify saved bytes and their declared provenance.

## Verification

**99 targeted tests passed together, zero failures/errors, in12.924seconds:**18 new
viewer checks and81 relevant existing viewer, session, preflight, boundary and
accounting checks. Sources stayed unchanged during the run. The full prior trading
suites were not rerun and their totals are not added to this invocation.

The new checks cover future publication/count/pivot/signal rejection, same-clock
visibility, receipt-time financing, future exit/bar changes, position/cash rewind,
conservative cancellation ordering, retained ranking, source/input mismatch,
non-overwriting exports, script escaping, public CLI and rejected live options.
Node executes the shipped JavaScript cursor projection against the Python reference.
A minimal DOM harness also exercises navigation, evidence text and SVG construction;
it is not a browser-layout test. Export plumbing tests use a deliberately assembled
saved-report harness and do not count as new strategy-entry acceptance.

Eight saved sprint150 accounts were exported: EW3 long target, EW3 short gap,
EW5 long gap and EW5 short target, each under base/adverse costs. All report hashes
match150's published inventory. The trading source graph, including the46 frozen
control bindings, matches150 exactly. These are existing constructed-price results,
not eight newly replayed strategy accounts. Their JavaScript checks reach signals,
alternate counts, both position directions, target/gap exits, H4/D1 views, skipped
decisions and rewind. **144 real-report cursor/frame projections** match the Python
reference exactly. A wheel build contains the exact viewer module and HTML template.

Browser security rejected the local-file preview. No alternative browser route
was attempted. **Visual layout and browser interaction remain unverified** in this
session; the JavaScript harness does not replace that review.

Final evidence is under
`reports/elliott-session-viewer-151-verification-002/`. Verification001 preserves
the earlier98-check/export snapshot;002 includes the final bounded reader, initial
selector state, additional JavaScript control check and all final exports. The
[portable evidence](evidence/elliott-session-viewer-151/README.md) contains the final
test log, source hashes, export checks, packaging check and verification summary.
Large HTML, wheel and source artifacts remain ignored.

## Open the local examples

| Constructed case | Base-cost viewer |
| --- | --- |
| EW3 long target | [Replay](../reports/elliott-session-viewer-151-verification-002/viewers/ew3_long_target-base/replay.html) |
| EW3 short gap loss | [Replay](../reports/elliott-session-viewer-151-verification-002/viewers/ew3_short_gap-base/replay.html) |
| EW5 long gap loss | [Replay](../reports/elliott-session-viewer-151-verification-002/viewers/ew5_long_gap-base/replay.html) |
| EW5 short target | [Replay](../reports/elliott-session-viewer-151-verification-002/viewers/ew5_short_target-base/replay.html) |

Choose **Signals**, then **Next**, to reach the automatically recorded setup.
Choose **Entries and exits**, then **Next**, to inspect its fill and exit. Use
**Skipped H1 decisions** from the first event to inspect a recorded no-trade reason.
Select H4/D1 or a recorded count alternate to inspect its evidence. Cash and fills
rewind with the cursor. The browser holds the complete saved dataset locally;
the cursor governs the default view, not access to the HTML's underlying data.

```sh
PYTHONPATH=src:tests python3 scripts/elliott-session-viewer-151.py reports/elliott-session-acceptance-150-verification-001/matrix/ew3_short_gap/run/development NEW-VIEWER-DIRECTORY --profile adverse
PYTHONPATH=src:tests python3 -m unittest test_elliott_session_viewer_151 test_elliott_full_viewer test_elliott_sessions_146 test_elliott_study_145 test_elliott_full_boundary test_elliott_full_crosscheck -v
```

## Remaining scope

Only saved EW_FULL session149 accounts are supported; control viewers and direct
147/148 checkpoint import are not added. Exports are approximately28–43MB per
account and can use substantial browser memory. Only recorded confirmed pivots,
bounded pattern nodes and interpretation anchors are shown. Provisional pivots and
full nested child-tree exploration remain future viewer work. Visual review,
broader nested/fault/variable-session acceptance, qualified source/use/clock/DST/
coverage/cost/contract/margin/conversion/prior-trial admission, a qualified
chronological runner and disabled native demo reconciliation remain unfinished.

All16 actual market cells remain unavailable with null returns; native submissions
remain unavailable. Sparse invented quotes do not establish complete intrabar
paths or true drawdown. Financing and UTC timing limitations are unchanged.
No actual source, market prices, acquisition dates, accounts, terminals or
credentials were accessed or assigned. Protected periods, closed routes and expired
capture restrictions remain unchanged. There is no real-money execution mode.
