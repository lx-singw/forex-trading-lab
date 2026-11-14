# Bounded protective-stop experiment 030 — not executed

029 found some meaningful favorable progress before stops, but most stopped
cases never reached +0.5R. Under adverse costs C05 has five of eleven stops
with prior +0.5R; C06 has five of seventeen. Each profitable challenger window
also becomes negative when its largest winner is removed. A protective exit
could reduce reversals while clipping essential winners; neither effect may be
assumed. This is one development hypothesis, not recovered-profit accounting.

Exactly five candidates × three existing 2024 windows × two frozen costs =
30 scenario outputs, plus arithmetic CASH. Controls are unchanged C00, C05 and
C06 from 028. C07 is C05 plus the single rule below; C08 is C06 plus that rule.
Twelve challenger and eighteen control cases. No other trigger, trailing rule,
target, time exit, window or parameter grid within this budget. The 0.5R trigger
was chosen using the declared 029 descriptive thresholds and observed cases;
this is informed reuse of development data, not an independent selection.

## Exact rule to specify and test before new returns

Retain initial entry/stop distance, volume and initial R in dollars at the
original fill. Preserve the existing 2R target and all risk/cost/sizing controls.
Process inherited stop/target fills on each ordered quote first. Only if the
position remains open, calculate hypothetical executable net liquidation using
bid/ask, imposed exit slippage, full round-trip fee and financing accrued so far.

On the first surviving quote whose net liquidation is >=0.5 initial R, arm a
single stop adjustment. Let `v = lots * contract_size`, `s` be +1 long / -1
short, and `fee` the full round-trip commission. Compute:

`protection_price = entry + s * ((fee - accrued_swap) / v + slippage_pips * 0.0001)`

Move the old stop only toward the current market: max(old, protection) for long,
min(old, protection) for short. Check valid price, monotonic tightening and that
the level remains behind the triggering bid/ask and before the original target.
It takes effect on subsequent source sequences; do not inspect the next quote,
reorder tied timestamps or retroactively change a fill on the arming quote.
Apply the inherited adverse stop fill/slippage/gap behavior. Move once only;
later financing does not move it again. Record the arming sequence/time, old/new
stop, initial risk, current financing and model liquidation at the trigger.

The protection level estimates zero net at that moment under declared costs.
Gaps, slippage and further financing can still make the trade lose; never call
it a guaranteed break-even or maximum-loss stop. Do not exit immediately at
the trigger, increase stakes or widen stops to recover losses.

## Preservation, tests and evaluation

Implement separate versioned classes/config/runner; preserve 028/029 originals.
Freeze exact inputs/code/rules/output paths before returns, after tests and all
029 snapshot bindings verify. Common 201-hour warmup and original evaluation
boundaries/data/provenance/development reviews stay fixed. Corrected executable
equity marking remains mandatory, with new checkpoint metadata rejecting legacy
or different-candidate state. No annual-runner gate or candidate acceptance change.

Meaningful tests: long/short trigger equality, bid/ask/fees/financing arithmetic,
no arming before threshold, fills before arming, target priority, tied-sequence
causality, one-time monotonic change, gap loss after protection, financing after
arming, duplicate/restart behavior and strict risk/position/loss limits. Preserve
actual initial stop separately from moved stop in reports, so initial R cannot
be recomputed incorrectly from a protective level beyond entry.

Controls must match every original 028 trade, decision, cash/cost and corrected
metric, with only declared metadata/lineage additions. Preserve any mismatch and
stop claims until a separately declared repair explains it. Independent checks
must reconcile all cash/fees/fills/stop changes and verify that arming uses no
future quote. Report all thirty outcomes, protected exits, target winners lost,
new/omitted entry identities, drawdown and adverse sensitivity. A changed exit
changes later position availability and cash; replay it rather than subtracting
old losses. No automatic winner or deployment even if a reused cell improves.

Annual eligibility remains failed. Exclude consumed2025/reservedNov–Dec2026;
no new downloads, accounts, provider contact, martingale or execution. Orders
remain unavailable. Further chronological testing requires qualified data;
repeated improvements on these three windows cannot establish a reliable edge.
