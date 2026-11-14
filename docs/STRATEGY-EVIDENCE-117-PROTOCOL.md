# Strategy evidence117 — fixed research protocol

This phase reviews public primary literature and writes declarations. It does not
implement these rules, admit market data, calculate returns or place orders.
[The evidence review](STRATEGY-EVIDENCE-117-REVIEW.md) records the publications,
limited access and distinctions from our engine. Original copyrighted papers are
not copied into the repository. Publication summaries are short paraphrases.

The authoritative declaration is [research-candidates-117.json](../config/research-candidates-117.json).
All thresholds below are fixed research choices, not inferred optimal values or
paper replications. Existing008/028/030 and113–116 source remains unchanged.

## Completed-session information contract

Use EURUSD daily venue sessions whose boundaries, calendar, source UTC, completeness,
quote age and observation policy have independently qualified evidence. A DailyBar
contains source session start/end, observed midpoint OHLC, final observation time,
availability time and input lineage. The midpoint is `(bid + ask) / 2` from actual
observations. The close is the last qualifying observed midpoint before the end,
available only after that session is complete. A later implementation must freeze
the exact boundary/coverage and latency policy before reading performance.

No guessed UTC offset, resampling of uncertified native clocks, forward-filled
empty sessions, invented weekend prices, interpolation or use of a still-open
session. Reject invalid qualification, duplicate/conflicting sessions, reversed
chronology, nonfinite/nonpositive prices, inconsistent OHLC, incomplete required
sessions and unobservable availability. Scheduled closures must come from the
qualified calendar; a missing trading session does not become a closure. Identical
input replay is idempotent. Features use only bars available by decision time.

All active candidates share253 completed sessions of warmup. Cash is evaluated on
the same dates. Changing future prices or unfinished observations must not change
an earlier decision. Qualification labels in invented fixtures never qualify a
market source. Runtime market admission remains unavailable in118.

## Four fixed hypotheses

T12_D returns `sign(close[-1] / close[-253] - 1)`. Equality abstains. It measures252
completed-session spot-price momentum and updates once per completed session.
It is not a monthly futures/forward excess-return or volatility-scaled portfolio.

MR20_D adapts the existing C03 price reentry rule to daily bars. Use the last21
closes: previous20=`closes[-21:-1]`, current20=`closes[-20:]`; compute each last
close's z-score using its window's arithmetic mean and population standard
deviation. Long if `old_z < -2 <= new_z`; short if `old_z > 2 >= new_z`; otherwise
abstain. A zero standard deviation abstains. Invalid arithmetic rejects the input.
This is a price hypothesis; it is not CPI-based value or PPP.

MIX50_D uses `q = 0.5*T12_D.side + 0.5*MR20_D.side` and `side = sign(q)`.
At an entry, risk fraction=`0.0025*abs(q)`. Opposing sides cancel; one active
component uses0.125%; both agreeing use0.25%; both inactive use0%. The weights
are fixed, unoptimized signal weights, not separate funded accounts. Cash never
trades and accrues no interest in this experiment.

For each active entry, use14 completed true ranges, each including the previous
completed close; arithmetic mean times2 is the initial stop distance. A zero
distance abstains. Use a fixed2R target. No trailing exit or loss-recovery sizing.
Only one aggregate position is permitted. A held position retains its original
stop/target and risk sizing even if the next daily signal changes.

Later execution simulation must use the first eligible observed bid/ask quote
after bar availability, with causal latency and entry spread qualification. At
most one entry opportunity per completed session; if already holding at that
opportunity, do not enter again later in that session. Do not fill at the feature
close, at a future quote, or at an unobserved stop price. Stops and targets use
observed side-specific fills with costs and gap behavior. Estimated stop risk is
not a guaranteed loss cap. Tiny half-risk positions may fall below minimum volume
and must abstain rather than round up. Duplicate and restart handling require
meaningful tests before any simulator adapter is used.

## Costs and account assumptions

Keep the113 hypothetical base/adverse profiles as explicitly named comparison
assumptions, not as discovered broker terms. Base: commission$7 per lot round
turn, slippage0.2pip per fill, financing debit$3 long/$1.50 short per lot at rollover,
no synthetic spread floor. Adverse: $10,0.5pip,$4.50/$2.25,1.2pip spread floor.
Both retain a1.5pip entry spread cap, Wednesday triple rollover at the next UTC
midnight, USD10,000 fresh capital,100,000-unit contract,0.01 minimum/step,1 maximum
lot,30:1 hypothetical leverage,0.25% maximum entry risk and1% UTC-day loss pause.
These values match113 definitions, not the different003 adverse file.

Recorded bid/ask spreads must still be used, including wider exits; do not replace
observed spreads with a favorable constant. Entry risk includes the retained
cost-aware sizing constraints. Financing through weekends, closures and gaps,
open executable equity, margin, daily pause and side-specific slippage must be
reconciled. Actual source/contract/cost/rollover/financing and clock evidence is a
prerequisite to evaluating market performance. If that evidence contradicts these
profiles, declare the comparison unavailable and freeze a separately versioned
protocol before returns; never silently change a profile to improve results.

## Chronology and planned trial budget

One planned batch is4 candidates ×2 cost profiles ×2 chronological partitions =16
cells. These are correlated comparisons, not16 independent discoveries. Preserve
every rejection, no-trade outcome, gain and loss. No parameter grid, weight search,
additional candidate, best-month selection or re-labeling seen data as untouched.

Development and later validation each require at least24 calendar months, with253
qualifying prior-session bars for warmup. Before any return calculation a separate
run manifest must freeze input hashes, exact UTC dates, session/calendar/latency
rules, source/cost evidence, implementation hashes and the complete trial history.
Validation must actually be unseen when frozen.2024 is reused development;2025 is
consumed/excluded; October2026 is quarantined; reserved November–December2026 is
not accessed in117/118 and does not satisfy24 months. No eligible dataset is assigned.

Each cell starts fresh withUSD10,000, with no incoming position. Validation may
warm up on prior prices, without importing development positions or profits.
Boundary liquidation must occur on an actual last eligible observed quote and
include costs; missing executable endpoints make that cell unavailable. Report
the fresh-account holdout design; do not imply one continuous portfolio or sum
capital from different candidates/periods/costs.

## Evaluation criteria and current admission

Report each candidate's trades, wins/losses, payoff ratio, net expectancy, gross
P&L, spread/slippage/commission/financing, executable-equity maximum drawdown,
exposure, turnover, no-trade intervals, quarterly and monthly net returns, largest
trade loss and loss beyond its entry estimate. Report failed qualification and
sample gaps before any metrics. No win-rate target.

A descriptive research screen requires both cost profiles' validation net profit
and net expectancy to be positive, adverse maximum drawdown no more than5%, at
least50 closed validation trades and24 monthly marks. These engineering thresholds
are not a statistical proof or an execution gate. Cash is exempt from trade count.
Below-sample results are insufficient, not successful. Missing qualification is
unavailable, not a numerical fail or a zero return. Any inferential analysis needs
its own methodology frozen before returns; none is computed in117.

Evaluate a mixture beside both standalone components on identical inputs/capital
and disclose its lower risk/exposure when only one component signals. Report signal
agreement, return correlation and loss overlap without assuming independence.
Lower drawdown from spending less risk does not prove a better signal. Claim no
mixture superiority from a single descriptive ranking, gross return or toy path.

Passing this screen merely merits independent research review. Market validation,
forward paper evaluation, strategy selection, automated orders and real-money
execution remain unavailable. No support messages, provider retries, paid services,
broker accounts, SDK connections or MT5 operations are part of this phase.
