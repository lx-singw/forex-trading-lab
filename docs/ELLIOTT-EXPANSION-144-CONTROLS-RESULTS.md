# Elliott144 — unchanged strategy control adapters

14 November 2026. The approved implementation remains in progress. This increment
adds an invented-input control interface; **it does not admit market data or enable
orders**. It follows the [window/accounting increment](ELLIOTT-EXPANSION-144-WINDOW-RESULTS.md).

## Implemented

`elliott_full/controls.py` derives control inputs from one frozen raw-quote stream,
prepares chronological prefixes and provides common step, report and checkpoint
interfaces. It calls the original replay classes without changing their code,
declarations, stop rules or accounting clocks:

| Control | Original economic engine | Preserved behavior |
| --- | --- | --- |
| `EWPB_D124` | `elliott_execution_125.Account` | Daily close-swing observations from124; observed structural invalidation;125 admission and120 accounting primitives |
| `T12_D` | `daily_fills_120.Replay` | Frozen118 daily trend/ATR features;120 admission, ATR stop and accounting |
| `CASH` | `daily_fills_120.Replay` | No trades or interest; fresh USD10,000 per partition |

Raw input uses the existing strict invented125 format, EURUSD and its declared
2000–2003 clock. Caller-supplied counts, features and account marks are not accepted.
This interface is not a new qualified-market schema. Synthetic DEMO fields in
these fixtures do not certify an actual account; there is no native transport.

The freeze binds the complete input, both partitions, all three controls, both
cost profiles, fresh capital and current/frozen source hashes before replay.
Files/directories are created exclusively. The prepared artifacts retain the
original compiler freezes and original reports, alongside the common report.
Their file hashes are checked before opening an account.

The two chronological partitions each start with fresh capital, no position and
no carried pause or consumed entry. Warmup observations remain unfunded. All
controls see the same execution quotes and derive features from the same available
daily history. Quotes received at/after the partition cutoff are excluded. The
exact declared final quote must be new, fresh and trading; missing, stale and
repeated endpoints prevent preparation even for CASH.

Checkpoint restore verifies current sources and the exact prepared partition, then
uses the original engine's prefix replay and reconstructed-state checks. Duplicate
events are idempotent; conflicting events reject without changing account state.
The common report preserves every original economic field instead of translating
different stop/clock semantics into apparent new-ledger parity.

## Verification

The control suite covers 36 paired account comparisons: six invented paths
(`long_target`, `short_target`, `long_gap`, `short_gap`, `wide_exit`, `quote_guards`)
times three controls times two cost profiles. Every wrapped original report and
state matches a direct run of its frozen engine. Each is also checked by the
existing independent Fraction-based accounting auditor, including marks, fills,
fees, financing, reservations and loss pauses. The direct/wrapped runs are paired
software checks, not independent strategy trials.

Other checks exercise restart before entry, while held and after finish; forged
state with recomputed outer/inner hashes; cross-partition/source-revision rejection;
input/artifact changes; unknown candidates; REAL/CONTEST/unknown synthetic modes;
and invalid endpoints. Changing later prices preserves the development decision
and economic state. Separate freezes legitimately retain different provenance
hashes, which are not treated as economic differences.

**143 tests passed together in 420.127 seconds** on the final runtime revision,
including13 control tests and the130 existing Elliott checks. See the
[test log](../reports/elliott-full-144-controls-verification-001/tests.txt).

```sh
PYTHONPATH=src:tests python3 -m unittest test_elliott_full test_elliott_full_policy test_elliott_full_rulebook test_elliott_full_boundary test_elliott_full_viewer test_elliott_full_discovery test_elliott_full_windows test_elliott_full_crosscheck test_elliott_full_controls -v
```

Compilation and `git diff --check` also pass. The verification directory contains
a source archive and hash manifest covering the Elliott package, current tests,
scripts/config/status documents and the46 declared frozen-control dependencies.
Archive hashes and demonstration source bindings were verified. This is an
evidence snapshot, not a claim of a separately packaged standalone distribution.
The prior six-file legacy arithmetic audit bindings still match unchanged files.

## Reviewable invented examples

A declaration lists four artificial paths before their CLI outcomes: long/short
targets and long/short gap losses. Each retains twelve control accounts across
both partitions and both costs. All outcomes are retained; capital and returns
are not summed as a portfolio. These examples do not estimate win rate or income.

- [Declaration](../reports/elliott-full-144-controls-demo-001/declaration.json)
- [All four example statuses](../reports/elliott-full-144-controls-demo-001/results.json)
- [Long target controls](../reports/elliott-full-144-controls-demo-001/long_target/run/comparison-status.json)
- [Long gap controls](../reports/elliott-full-144-controls-demo-001/long_gap/run/comparison-status.json)
- [Short target controls](../reports/elliott-full-144-controls-demo-001/short_target/run/comparison-status.json)
- [Short gap controls](../reports/elliott-full-144-controls-demo-001/short_gap/run/comparison-status.json)

For an existing labelled invented125 input, use new output paths:

```sh
PYTHONPATH=src python3 scripts/elliott-full-controls.py freeze INPUT.json NEW-FREEZE.json
PYTHONPATH=src python3 scripts/elliott-full-controls.py replay INPUT.json NEW-FREEZE.json NEW-OUTPUT-DIRECTORY
```

Every report accounts for all16 planned comparison cells. Twelve control cells
can produce invented results; the four `EW_FULL_V1` cells explicitly remain
unavailable because the new strategy does not yet have an adapter from this common
raw stream. Independently invented D1/H4/H1 fixtures must not be substituted and
called the same input. All16 **market** statuses remain `UNAVAILABLE`, with no
market returns, including CASH. No strategy is selected from this demonstration.

## Remaining work and activation

These adapters preserve the original source-day financing and original control
entry/exit behavior. They do not eliminate the four source-day/receipt-day timing
differences documented in the previous increment. They do not establish new-ledger
parity for clocks, daily pauses, time exits or off-tick rounding.

Remaining work includes the common qualified source/aggregation/run boundary,
explicit calendar and cost declarations, broader acceptance scenarios and the
disabled native demo transport/reconciliation implementation. Historical/shadow
and bounded native trials still require their declared gates. The full plan is
not complete, and no market advantage has been measured.

No MT5/account/settings operation, price acquisition, reserved-price inspection
or order occurred. Old117–126 files and declarations remain unchanged. The2025
consumed, October quarantine and November–December reserved boundaries remain
unchanged. Orders and real-money execution remain unavailable.
