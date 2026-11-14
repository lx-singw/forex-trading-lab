# Strategy combination115 — completed offline prototype

Implemented two fixed agreement rules for unchanged C00/C05/C06 decisions, plus
CASH. UNANIMOUS requires three nonzero votes in the same direction. AGREE2 requires
at least two with no opposing nonzero vote. Both abstain on conflict or insufficient
support. No weights, optimization or winning strategy are selected.

Each rule trades one position in one account. The largest supporting stop distance
enters inherited floor sizing with one account risk budget; member positions,
capital and risks are never added together. Traces retain member votes/reasons,
supporters, entry admission, estimated risk/budget, trades, actual costs and fill
lineage. Existing positions keep their original stop/target protection when later
votes abstain or oppose. Corrected019B equity, costs, daily pause and gap behavior
are inherited from unchanged114/113 classes.

**239 focused tests passed** in 70.710 seconds: 36 new and 203 retained, no
failures/errors/skips. The initial36-test run also passed (48.993 seconds); both
outputs and the tested source archive are preserved. New tests cover all27 vote-side
combinations, malformed votes, maximum supporting stop, actual partial/conflicting
long/short histories, causal future changes, common201-hour warmup, fresh validation,
missing hours, cash, costs/financing, position/risk/spread limits, gap loss, daily
pause, target overshoot, held-position exits and rule-bound restarts. Independent
reference arbitration on the retained114 engine matches prefixes, positions,
decisions, fills, costs, lineage and final metrics across all five cases, both
trading rules, both costs and both partitions.

All532 predecessor source/config/test hashes are unchanged. Four new implementation/
test files make536. Earlier114 control prices/events are reused exactly, with two
new predetermined vote-case paths in the115 generator. No old source, fixture or
result was rewritten. Older2,095 active-suite results are retained, not rerun.

All five invented fixtures/manifests were frozen before demonstration outputs.
All60 rule/cost/partition/case outcomes are reported: 12 positive, 6 negative,
42 zero. CLI summaries agree with saved reports. Cost reference gross minus
spread/slippage/commission/financing reconciles with actual simulated net, and
recorded estimated entry risk stays within its single-account budget.

The table shows hypothetical USD net with closed-trade counts in parentheses.
Each cell starts an independent $10,000 account. Do not aggregate cells into a
portfolio return. These are constructed software checks, not market profits.

| Invented path | Rule | Base development | Base validation | Adverse development | Adverse validation |
| --- | --- | ---: | ---: | ---: | ---: |
| Continuation | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Continuation | AGREE2 | +74.92 (3) | +50.44 (4) | +62.83 (3) | +38.63 (4) |
| Continuation | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Reversal | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Reversal | AGREE2 | -317.66 (2) | -279.87 (3) | -302.76 (2) | -271.10 (3) |
| Reversal | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | AGREE2 | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Flat | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Partial agreement | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Partial agreement | AGREE2 | +35.40 (2) | +35.46 (2) | +35.17 (2) | +35.26 (2) |
| Partial agreement | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Conflicting votes | UNANIMOUS | 0 (0) | +6.70 (1) | 0 (0) | +6.55 (1) |
| Conflicting votes | AGREE2 | -427.35 (1) | +45.24 (2) | -394.24 (1) | +39.24 (2) |
| Conflicting votes | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

The partial-agreement fixture constructs C00/C05 agreement with C06 abstention
at the designated completed history; AGREE2 admits it and UNANIMOUS abstains.
The conflict fixture constructs one opposing vote against two; both abstain at
that decision. A case name describes a designated event, not every hour of its
path. Later votes can agree and enter, which explains trades and losses within
the conflict case. The full reports contain the actual admission votes.

Agreement does not guarantee profit or prevent a held price-gap loss. AGREE2 loses
up to $427.35 (4.2735% of the starting toy account) in the constructed base conflict
development path despite respecting the estimated entry budget. Stops and the
1% daily entry pause cannot guarantee maximum losses through gaps. Some adverse
losses are smaller because cost-aware sizing floors to fewer lots. These outcomes
are not evidence that higher costs help or that either rule is stronger in markets.
UNANIMOUS abstains frequently; no-trade zero returns do not establish a winning edge.

Costs, UTC calendar, financing and exact limit fills remain hypothetical. The last
observed hour is partial. Common observed-hour warmup does not certify continuous
real tick coverage. Input validation may inspect a future suffix; strategy decisions
use preceding completed bars only. Checkpoints enforce rule/source/config and
vote/state consistency, not authentication or broker reconciliation.

Native107/109/111 performance remains unavailable. New diagnostic routing tests
use invented capture encodings; all62 prior native input hashes remain unchanged.
No guessed clock offsets, native return calculation, historical/reserved market
reruns, acquisition, SDK, MT5 launch/settings/log/account inspection, support
contact or orders. Native UTC/age/cost/quality qualification stays unresolved.
Market/paper/order/real-money availability remains false. Private-demo/no-contact
scope persists, and no manual MT5 launch is needed.

Local evidence: `reports/strategy-combination-115-reservation.json`, development
source archive, both test outputs, frozen-demonstration and demonstration reports,
handoff/document review, final source archive and completion review. Fifteen
invented input/manifest/report files are in `data/strategy-combination-115-invented-demo/`.
Reports/data remain ignored local evidence; implementation/docs remain canonical here.

Usage: [STRATEGY-COMBINATION-115-USAGE.md](STRATEGY-COMBINATION-115-USAGE.md).
Next prepared step: [COMBINATION-STRESS-116-PLAN.md](COMBINATION-STRESS-116-PLAN.md).
The earlier prepared115 plan remains historical to this implementation.
