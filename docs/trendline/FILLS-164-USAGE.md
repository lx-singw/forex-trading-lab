# Level B invented price model — sprint 164

The new trendline/fills.py component calculates hypothetical EURUSD prices from
explicit invented B inputs. It has no account, lot size, cash, submission API or
live mode. All outputs retain B/geometry/profile labels and orders_available=false.
No result qualifies a broker-performance study or demo run.

## Inputs and entry

PriceModel accepts an existing strict163 Declaration and base/adverse profile.
The fixed117 cost declaration is hash-pinned. Its spread floor/slippage match
retained119/120 definitions: base0/0.2 pip, adverse1.2/0.5 pip. Commission/swap
remain inherited hypothetical terms but are not applied by this price component.

Opening contains only declared H1 boundaries, bid, spread and an explicit event
ordinal. Opening.from_hour discards future high/low/close and completed-hour
receipt fields. Using it assumes the historical bid open and the spread field
apply at that open; it does not establish a real quote event or freshness. A
mid-only source returns EXECUTION_SIDE_DATA_UNAVAILABLE, never synthetic bid/ask.

The entry request declares an invented kind, direction, scheduled H4 trigger end,
decision event (time/ordinal), ATR, tick, stop, optional target and E1/E2 exit model.
The model finds the first scheduled H1 open at/after the trigger close, respecting
declared closures. Missing first hour or a late decision cannot substitute a later
price. Same-clock decision/open order must be explicit; equality or reverse order
abstains. An H4 finalization delay can make its next H1 open too early; report that
result rather than assuming zero delay after seeing counts.

Long buys ask+adverse slippage; short sells bid-adverse slippage. Stops round
outward to tick before testing executable exit-side crossing and the inclusive
0.5..2.5ATR and10%-spread/stop windows. E2 targets round toward entry and still
must offer at least2R measured from the modelled fill. E1 has no target. Quote-age
and Level Q absolute spread gates are not claimed by this B approximation.

## Exits and protection

Position is an immutable price/protection request, not an account checkpoint.
It binds the declared calendar/geometry and cost profile. Its initial risk, tick
levels and effective times are validated; E1 stops may tighten prospectively but
never loosen, and E2 keeps its original stop and limit. The component validates
structure; it cannot authenticate a caller's claimed position against an external
account. Phase7 must reconstruct actual simulation state from its input prefix.

- exit_open checks a carried position against the opening bid (long) or ask
  (short). Stops use that price plus adverse market slippage; targets use the
  original limit, with no favourable overshoot or extra slippage. An explicitly
  scheduled market exit uses the opening exit side with adverse slippage.
- exit_hour waits for the completed hour's available_at. A pre-fill bar cannot
  stop a later position; a partial or unordered fill/protection interval is
  UNAVAILABLE. A newly tightened stop is never applied to an earlier range: the
  caller must first process that interval with its original protection.
- A known opening reach precedes later range events. If the position survives
  the open and the later range contains both levels, the stop wins. Intrabar
  stops fill at stop minus/plus adverse slippage; targets at their limit. Exact
  intrabar trigger time stays unknown.
- Entry spread filters never block protection of a carried position. Gap and
  slippage price losses can exceed the initial entry-to-stop price distance;
  outputs disclose that excess. This is not a guaranteed loss cap or total
  account-risk estimate including fees/financing.

The methods are stateless and deterministic. A future runner must ensure one
position/reservation, consumption, no repeated exits/reentry, pending exit
persistence, partition liquidation/entry cutoffs, gap/unknown-coverage policy and
account restart reconciliation.
Calling the same function twice is not duplicate-order prevention. Missing
intervening scheduled data cannot establish survival to a later observation;
these isolated price calculations do not silently certify that path.

## Reproduce the invented exercises

```sh
PYTHONPATH=src python3 scripts/trendline-fill-demo-164.py NEW-OUTPUT-DIRECTORY
PYTHONPATH=src:tests python3 -m unittest test_trendline_fills_164 -v
```

The demo writes16 independent source/row/request/result cases: both directions,
both costs and gap-stop/ambiguous/known-opening-target/late-decision alternatives.
Literal expected prices/reasons are checked before publishing the summary. These
are component exercises, not16 strategy trades or account returns. Files are
exclusive; use a fresh ignored reports/ path. Full-file bindings stay separate
from causal identities, so a valid future suffix cannot rename earlier positions.

The source plan remains unassigned. Phase2 actual-source/calendar/coverage/use
acceptance, and Phase7 strategy/risk/accounting integration, remain open.
