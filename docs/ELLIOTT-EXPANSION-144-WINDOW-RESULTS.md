# Elliott144 — longer histories and accounting comparisons

14 November 2026. **The approved implementation remains in progress. Qualified
market validation and order placement remain unavailable.** This increment
continues the [previous rulebook/discovery work](ELLIOTT-EXPANSION-144-RULES-RESULTS.md).

## Rolling pattern scope

The parser now examines the latest 256 confirmed fine pivots instead of refusing
every history after its first 256 pivots. Coarser anchors outside that same source
interval are excluded. Original source-bar indices and confirmation times remain
unchanged. Each decision records the retained pivot count, discarded pivot count,
first retained source bar and whether the left edge was truncated. The report
retains this metadata for inspection.

This is a bounded search scope, not a promise to recover every older parent count.
A pattern whose beginning has left the window is unavailable. Existing grammar,
candidate and depth limits still apply; search exhaustion prevents entries.
Input bars, events, snapshots, consumed opportunities and risk state are **not**
pruned. Total memory and replay time are therefore not bounded by 256 pivots.
The existing batch schema limits still apply.

The public-input regression first discovers an invented EW3 entry from bars and
quotes, then appends 805 invented H1 bars. It crosses the pivot-window boundary
while preserving the exact held position, consumed opportunity and earlier
published snapshot. Bar OHLC does not fabricate an executable stop fill. The
position closes only when a fresh observed quote subsequently reaches its stop,
using the existing gap/cost accounting. This exercises one long constructed path;
it does not establish throughput or coverage for all possible market histories.

## Missing completed parent bars

An old D1/H4 count can no longer supply context after the next parent bar should
have completed but is missing. The decision records `missing_completed_parent_bar`.
H4 context that disagrees with D1 explicitly records that disagreement.

This guard uses the continuous periods declared by the invented wrapper. It does
not infer broker holidays or qualify a session calendar. A market adapter needs
qualified completion/publication and closure rules before admission.

## Differential accounting evidence

The new audit calls the frozen 125 sizing helper and 120 accounting methods with
explicit invented component state. It does not run their entire replay wrappers,
strategy decisions, input-admission rules or native APIs. The old files and
declarations are unchanged and their hashes are checked before and after the audit.

The predeclared common-domain comparisons match for:

- 48 sizing cases: both directions, base/adverse costs, four stop distances and
  three equity levels, including rejection when minimum volume cannot fit risk.
- 24 accounting traces: both directions/profiles with target, gap stop, widened
  exit spread, Wednesday financing, weekend financing and stale-quote cases.
  Comparisons cover cash, executable mark, held status, financing and exit net.
- A separate daily-headroom rejection regression.

These fixtures use aligned tick prices. They do not establish rounding parity
outside that domain, daily-pause or time-exit parity, strategy-control parity,
qualified calendar parity or equality of every intermediate legacy state field.

**Four midnight stale-quote cases retain a known timing difference.** The frozen
ledger advances financing using source day; the new invented ledger advances it
through receipt day even when that quote cannot execute. Thus a stale quote
received just after UTC midnight can debit Wednesday triple financing earlier in
the new ledger. These are reported as `known_timing_difference`, not matches.
The new ledger's behavior has not been silently changed to obtain agreement.
A qualified clock/calendar policy and reconciliation remain necessary before a
market study or execution adapter can rely on this behavior.

- [Declaration before outcomes](../reports/elliott-full-144-legacy-audit-001/declaration.json)
- [All comparisons and retained differences](../reports/elliott-full-144-legacy-audit-001/results.json)

Reproduce in a new output directory from the repository root:

```sh
PYTHONPATH=src:tests python3 scripts/elliott-full-legacy-audit.py reports/NEW-AUDIT-DIRECTORY
```

## Verification and remaining work

**130 tests passed together in 162.316 seconds** on this runtime source revision.
The [full log](../reports/elliott-full-144-window-verification-001/tests.txt)
includes the previously accepted discovery, risk, restart, rulebook, boundary and
viewer checks plus the new window/context/accounting tests:

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full test_elliott_full_policy test_elliott_full_rulebook test_elliott_full_boundary test_elliott_full_viewer test_elliott_full_discovery test_elliott_full_windows test_elliott_full_crosscheck -v
```

The source snapshot and hash manifest in the same verification directory preserve
the Elliott package, test/scripts/config and current status documents. They are a
change/evidence snapshot, not a standalone distribution: the frozen legacy modules
and their transitive dependencies require the original repository. Their audit
hashes are recorded separately. Previous reports retain their own source bindings.

Remaining authorized work includes complete strategy comparison adapters for the
frozen controls, broader nested/fault scenarios, qualified-input/run admission,
the qualified source/cost/calendar declarations and disabled native demo transport
and reconciliation. Shadow and bounded native runs remain conditional on their
declared gates. The full plan is not complete.

All 16 market cells remain unavailable. No MT5/account/settings operation, market
price acquisition, reserved-price inspection or order occurred. The 2025 consumed,
October quarantine and November–December reserved boundaries are unchanged. These
invented examples provide software evidence, not a measured trading advantage or
an estimate of returns.
