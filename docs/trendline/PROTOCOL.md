# TRL_V1 research protocol

Frozen in sprint 160 on 16 November 2026 (Africa/Johannesburg), before any
trendline market prices, counts or returns were inspected. Full roadmap approved
by the user; phases remain milestones containing one or more numbered sprints.

## Authority and scope

The imported [revision-2 specification](../tori_trendline_strategy_full/TORI-TRENDLINE-STRATEGY-SPEC.md)
and [full roadmap](../tori_trendline_strategy_full/TORI-TRENDLINE-BUILD-ROADMAP.md)
are retained unchanged as source proposals. This protocol records the Phase 0
decisions and takes precedence where it explicitly resolves their ambiguities.
No strategy, phase or acceptance requirement is silently removed. A later change
to economic rules needs a dated decision, a new protocol/config revision and a
recorded trial before its results are inspected. A hash identifies bytes; it does
not qualify a source, authenticate a claim or prove an untouched holdout.

TRL_V1 is a mechanical strategy inspired by Tori Trades, not a reconstruction of
her discretionary trading. This phase permits research, historical simulation
and invented fixtures. Orders remain unavailable. There is no real-money mode,
live toggle, recovery sizing, martingale, averaging down or pyramiding.

## Phase 0 decisions

| ID | Frozen decision |
| --- | --- |
| D1 | EURUSD first, USD accounting. Additional instruments require a declaration before their outcomes. |
| D2 | H4 setups, derived from H1; completed D1 for the context variant. |
| D3 | Baseline context off; D1 table is a separate strategy. W1/MN and connected chains are later optional trials. |
| D4 | All five initial strategies retained, built in order: TRL_BRK3_E1, TRL_FXR_M, TRL_BRK2_E1, TRL_BNC_E1, TRL_BRK3_E1_D1. |
| D5 | Strict penetration allowance zero, no touch exception and no retroactive restoration. |
| D6 | Core stop uses current safety-line value plus outward buffer. Only FXR_M projects four bars ahead. |
| D7 | Risk fraction 0.0025 of positive executable equity, floored lots; daily entry pause 0.01. Not a pure rescaling of trades. |
| D8 | Pyramiding off. One held position/reservation per account. |
| D9 | Level B for development, signal counting and separately labelled behaviour research. Level Q required for qualified execution research/demo gates. No market source, dates or geometry basis is assigned today. Invented data are software evidence only. |
| D10 | Retain lab base/adverse cost definitions and accounting. Hypothetical terms cannot become verified broker costs. |
| D11 | Inherit all existing date/exposure/provider restrictions below. No new acquisition window or holdout assigned. |
| D12 | Experiment A independent accounts; B paired exits on identical BRK3 entries/stops/sizes; C combined portfolio deferred. |
| D13 | Consume each opportunity at the trigger, including skips, expiry, abstention and no fill. Preserve through restart and alias merges. |
| D14 | Initial 28 qualified comparison cells plus declared paired analysis; at most one separately frozen hypothetical-cost sensitivity batch of the same shape. Count every variant, revision and attempted alternative. |
| D15 | At least 60 entry-eligible opportunities per strategy in development for feasibility. Counts are not closed trades or evidence of an edge. |
| D16 | DLY remains declared, disabled and outside initial market trials. Phase 10 may propose a separately frozen trial from NO_SAFETY_LINE counts before returns. |

These defaults are implementation decisions within the user's approval of the
full roadmap. No missing source fact or data permission is inferred from that
approval. Research implementation approval does not activate a demo run.

## Parameters

This is the frozen P-xx table from specification 7.2 with explicit operational
clarifications below. One machine-readable config will be introduced with its
loader; do not maintain a second independently editable parameter declaration.

| ID | Parameter | Value |
| --- | --- | --- |
| P-01 | TF_SETUP | H4 |
| P-02 | TF_CONTEXT | D1 |
| P-03 | PIV_RADIUS | 3, strict extrema; equal and dual-extreme bars excluded |
| P-04 | MIN_TAP_SPACING | 6 bar indices, earliest accepted wins |
| P-05 | Touches | BRK3/FXR_M >=3; BRK2 exactly 2; BNC >=2 prior |
| P-06 | AGE_MIN_BARS | 30 H4; D1 context 15 D1 |
| P-06b | FORMATION_MIN_BARS | 90 H4, FXR_M only |
| P-07 | TOUCH_TOL | 0.25 times ATR_SMA14 at each pivot's confirmation; frozen per pivot |
| P-08 | PEN_ALLOW | 0 ticks |
| P-09 | MAX_ANGLE_DEG | 45, approximate FXR_M chart-normalisation test |
| P-10 | ANGLE_WINDOW_BARS | 390, complete history required for this test |
| P-11 | CHART_ASPECT | 0.5 |
| P-12 | MAX_SLOPE_ATR_PER_BAR | 0.5, ATR at evaluation bar |
| P-13 | BREAK_MARGIN | 1 tick |
| P-14 | SAFETY_MIN_TOUCHES | 2 |
| P-15 | STOP_PROJ_BARS | 0 core; 4 FXR_M |
| P-16 | STOP_BUFFER | max(1 tick, 0.10 times ATR_SMA14) |
| P-17 | MIN_STOP_ATR / MAX_STOP_ATR | 0.5 / 2.5, inclusive |
| P-18 | MAX_SPREAD_STOP_FRAC | 0.10, inclusive |
| P-19 | Eligibility expiry | next declared H4 close, exclusive |
| P-20 | TP_R_MIN | 2.0 |
| P-21 | RISK_FRAC | 0.0025 |
| P-22 | DAILY_LOSS_PAUSE | 0.01 of UTC-day reference executable equity |
| P-23 | MAX_CONCURRENT | 1 per independent account |
| P-24 | Attempt consumption | trigger |
| P-25 | CONTEXT_GATE | off baseline; D1 variant only |
| P-26 | Level Q limits | age <=2s; spread <=1.5 pips |
| P-27 | MAX_HOLD | none, except partition liquidation policy |
| P-28 | LINE_LOOKBACK_BARS | 600 H4 (or 600 D1 for D1 line engine), before cap |
| P-29 | PIVOT_CAP | 256 per kind; excess blocks this snapshot, never silently truncates |
| P-30 | RETIRE_AFTER_BARS | retire after >500 valid untriggered bars |
| P-31 | CONTEXT_MAX_ATR | 3 times ATR_SMA14(D1) |
| P-32 | MAX_CHASE_ATR | 1.0, disabled DLY only |
| P-33 | SETUP_EXPIRY_BARS | 10 H4, disabled DLY only |

ATR_SMA14 is the arithmetic mean of 14 true ranges with prior close, not RMA.
All geometry, comparisons and rounding use decimal/rational arithmetic. No float
epsilon or rounding may erase a penetration. A chart-angle approximation is not
a faithful reproduction of chart pixels. Missing/zero ATR or incomplete required
angle history blocks eligibility with a diagnostic.

## Source ambiguities resolved

| ID | Binding resolution |
| --- | --- |
| A-01 | Confirmed same-kind pivots, correct-side distance within frozen tolerance, chronological spacing; C1 resolves anchors. |
| A-02 | Any strict penetration kills the line; no pivot/touch exemption or later restoration. |
| A-03 | Close beyond by >=1 tick, previous close at/on opposite side, pre-existing formation. |
| A-04 | Enumerate all eligible lines; consume all simultaneous triggers; opposing sides abstain, same side ranks; unresolved economic ties abstain. |
| A-05 | BRK2 exactly 2; BRK3/FXR_M >=3; BNC >=2 prior, disjoint break categories per line. |
| A-06 | Age 30 H4 for core; formation span 90 H4 for FXR_M; use declared bar indices, not elapsed weekend hours. |
| A-07 | Fixed approximate angle and ATR-slope tests; no zoom-dependent tuning. |
| A-08 | Missing safety line abstains baseline; only declared disabled DLY may wait. |
| A-09 | Opposing line >=2 touches, correct side, confirmed and unpoked through trigger bar, C3. |
| A-10 | Entry-side stop distance 0.5 to 2.5 ATR; spread <=0.10 distance. |
| A-11 | Current buffered core line; four-bar projected buffered FXR_M line; reject crossed stops. |
| A-12 | E1 hard stop, favourable-only trail and next-quote close-beyond exit; E2 initial hard stop plus S/R target, no trail. |
| A-13 | Fixed lowest-price-anchored clusters, >=2 observations, median, nearest target >=2R; C7 resolves source wording. |
| A-14 | Adds off. |
| A-15 | Context off baseline; D1 table variant, no self-reference. |
| A-16 | Source-specific declared calendar and availability; never infer from server name. |
| A-17 | Exclude trigger bar only for the action-line break test; apply C3 to safety/context. |
| A-18 | Newly eligible after a prior close beyond -> MISSED_BREAK; no backdated entry. |
| A-19 | Immutable revisions, recompute on confirmations; check penetration each completed bar; stable geometry/group history. |
| A-20 | EURUSD first; futures/metals findings do not establish EURUSD results. |
| A-21 | Consume at trigger, before context, reservation and execution filters. |
| A-22 | Distinct Q/B input, geometry, execution and result labels. B cannot satisfy demo gate. |
| A-23 | Six-bar spacing is FXR origin only for FXR_M, borrowed convention elsewhere. |
| A-24 | Ordinary completed bounce contact is distinct from confirmed pivot touch; never wait for future confirmation to backdate entry. |

## Implementation clarifications

### C1. Anchor spacing

Start with A and process every available same-kind pivot chronologically. Accept
only correct-side, within-tolerance pivots at least six indices after the previous
accepted touch. B has no spacing override. If B is skipped, reject that candidate
pair as ANCHOR_SPACING_CONFLICT. This preserves earliest-wins spacing and ensures
both anchors of an admitted candidate really count. Fixture: indices A=0, C=8,
B=12 on the same line accept 0,8 and reject pair (0,12); do not count 0,8,12.

### C2. Deduplication and ranking

Deduplicate only fully validated candidate pairs sharing exactly the same ordered
touch set. Prefer an existing validated pair joining earliest/latest touches if
it produces exactly that set. Otherwise use the existing validated candidate with
least summed absolute touch distance, then canonical geometry id. Never invent a
new line by reanchoring without rerunning touches, spacing, penetration, age/span
and slope checks. Drop strict subsets only within the same strategy eligibility
profile; deduplication must not erase an exactly-two-touch BRK2 candidate because
a separate BRK3 profile has more touches. Canonical ids settle geometry/display
ties only, never an economic trade tie.

### C3. Completed-bar order and line eligibility

Publish completed bars at available_at in a stable, recorded event order. Derive
confirmations only from available observations. Evaluate action-line breaks using
lines formed before this bar and no penetration in earlier completed bars. A
penetration on this action bar with no qualifying close-break makes it POKED.
A bounce requires no penetration on its own contact bar. A proposed safety or
D1 context line must survive penetration checks INCLUDING the current completed
bar: the action-break exception cannot make a wick-poked safety line eligible.
All groups triggering now are consumed before selection/filters. Newly confirmed
geometry/revisions cannot generate a break on their own formation bar. Late
availability never creates an entry at an already passed bar open.

### C4. Entry and data-level semantics

Q requires a recorded eligible observation after the decision is available;
source and receipt order must both support causality/freshness. Same timestamps
need an explicit sequence; unresolved material ordering abstains. B enters at the
first scheduled H1 open at/after the H4 close, only if the decision was available
by that open in declared event order. Missing/late data -> unavailable opportunity,
not a later favourable substitute. Geometry may be bid_only or supplied mid
candles, but B execution additionally needs bid bars and declared spread semantics
or separately supplied executable-side bars. Mid candles alone cannot produce a
bid/ask ledger. Never average separate bid/ask extremes into a midpoint.

Initial stop geometry/ATR is frozen at the decision, then crossed-stop,
distance/spread, sizing, margin, pause and reservation gates are rechecked at the
entry observation. First eligible execution attempt is final; no blind retries.
Protection/exit checks continue even when entry filters fail. A stop cannot execute
before a fill. Stops tightened from a completed bar apply only to later events;
they are never tested against that bar's earlier range. Preserve the old hard stop
until any replacement is effective. E1 close-beyond schedules exit before changing
the line; selection of a new line cannot cancel that exit. Replacement lines must
form after entry; unresolved safety-selection ties abstain, not use parser order.

### C5. Partition endpoints

Funded intervals are [start,end). Before replay, the run manifest must declare a
liquidation_at inside that partition: default start of its last scheduled complete
H1 slot. New entries stop at liquidation_at. A held position exits on the first
eligible exit observation at/after liquidation_at and strictly before end. Q uses
observed bid/ask, B uses that declared slot's open. If no such observation exists,
report OPEN_AT_BOUNDARY; never use a later held-out quote or retrospectively choose
the best/last quote. Keep its marked equity and open liability visible, exclude it
from closed-trade statistics, and mark the cell unavailable. Stops/financing still
apply until liquidation. No incoming position/profits cross into validation.

### C6. Signal counting

Phase 10 counts line triggers and entry-eligible opportunities using frozen
geometry, safety, spread and stop rules, BEFORE account occupancy, lot/margin,
realised equity and exit-dependent loss pauses. Call them opportunities, not
executed trades. Report every filter denominator and NO_SAFETY_LINE share. Actual
entries/closed trades and capacity effects belong to Phase 11 simulation. The
60-opportunity gate does not guarantee 50 closed validation trades. Do not compute
or hide P&L to claim an outcome-free count.

### C7. Levels, controls and comparison interpretation

S/R clusters are anchored at their lowest member, not transitive single-linkage:
prices 0,0.2,0.4 with tolerance 0.25 give {0,0.2} and {0.4}, not one chain. Dedup
the same physical H4/D1 extreme by occurrence and price, not all historical equal
prices. Paired exit analysis uses a common entry stream and fixed initial sizes;
report counterfactual overlapping holds explicitly, without claiming an executable
one-position portfolio. Frozen T12_D/CASH controls need compatible qualified input;
incompatible Level B control cells are UNAVAILABLE, never silently reimplemented.

## Data, costs and study admission

2024 remains already-seen development; 2025 consumed/excluded; October 2026
quarantined; November-December 2026 reserved/untouched. These restrictions include
warmup access. Older 2020-2023 input qualification remains unresolved. Closed
provider/native090/attach-only SDK routes stay closed. Recorder136 remains expired;
156's immutable grant stays false. This protocol assigns no source, dates, native
runtime trial, capture window, terminal or account. No recursive data discovery.

Study admission needs 253 complete eligible prior bars on each required D1/H4/H1
timeframe plus all history needed by an active rule (including the 390-bar angle
window), 24 calendar months development and 24 genuinely unseen validation, with
declared timezone/DST, session boundaries, costs and source-use/lineage evidence.
Source aliases, file hashes and explicit permitted scopes go into a separate run
manifest before prices/returns; unknowns remain unknown. Level B permission does
not relax protected dates or qualify a provider. Qualification and complete trial
history require review; self-declarations alone cannot admit a market study.

Experiment A retains five strategies, T12_D and CASH, two cost profiles, two
partitions (28 cells). Hypothetical profiles retain commission USD7/10 per
round-turn lot, slippage 0.2/0.5 pip per fill and adverse spread floor 1.2 pips;
commission, financing, contract and margin terms require exact pre-run declarations
from existing definitions or explicitly labelled hypothetical assumptions.
Spread/slippage count once. Swaps, triple rollover, gaps and risk exceedances are
reported. Stops and entry pauses are not guaranteed loss caps.

Screen: positive net profit/expectancy under both validation costs, observed adverse
drawdown <=5%, >=50 closed validation trades and 24 monthly marks. Missing evidence
is UNAVAILABLE; too few trades INSUFFICIENT; economic failure FAIL. A pass earns
research review only. Inferential claims need a separately frozen uncertainty
method accounting for correlated trades and every attempted alternative.

## Phase gates and operational scope

Follow phases 0-12 in order; phase 13 tracks are optional as written. Software can
be built/tested on invented fixtures, but a data-dependent phase cannot be declared
complete without its required admitted input. Record partial progress and the
concrete blocker rather than bypassing the gate. Verification accompanies each
increment; Phase 9 remains the complete acceptance matrix. Phase 10 retains its
position after software acceptance, as the approved full roadmap specifies.

Phase 12 requires qualified Q historical evidence, then a separately frozen shadow
window (proposed 60 scheduled sessions, >=20 closed trades and zero unexplained
operational faults); no extending a window just to pass. A future native boundary
must default off, reject actual REAL/CONTEST/unknown enums, check actual DEMO and
continuity again before every submission/modification/cancellation, reconcile
restart/partial/ambiguous fills and preserve protective stops. Native transport is
separate from research. No real-money toggle, credentials, identity-derived hashes,
paid services, broker-account creation or unrelated terminal changes are permitted.
An actual bounded demo run requires the user's specific enablement at that stage.

Every completed sprint: review intended diff, run relevant verification, document
scope/limits, commit descriptively and push main. Generated prices/reports/runtime
artifacts remain ignored. Do not alter frozen Elliott/control/evidence sources.

## Acceptance and current state

Phase 0 is complete when decisions, all A-01..A-24 resolutions, the parameter
table, clarifications, repository reuse inventory and pause/resume note are reviewed
and committed. No test-suite count or market result is claimed for a document
freeze. Phase 1 next supplies a rulebook and independently hand-computed invented
fixtures before any trendline implementation. All five strategies remain in scope.

## Dated clarification — protocol revision 2, sprint 161

16 November 2026, before TRL market counts/returns or engine implementation.
The disabled DLY branch expires when elapsed H4 bars >=10, before considering a
new safety line on that bar. This follows the roadmap's explicit at10 transition;
the illustrative pseudocode's >10 is not authoritative. Target rounding toward
entry must be followed by the >=2R check; rounding cannot turn a sub-2R target
into a qualifying one. No numerical parameter changes, variant activation or
market trial occurred. Revision1 remains recoverable at sprint160's commit.

## Dated clarification — protocol revision 3, sprint 164

16 November 2026, before any TRL market counts/returns. A Level B historical H1
open is an explicit price/spread and event-order assumption, not evidence that a
completed H1 row was received at its opening time. A decision arriving after the
first scheduled H1 open cannot fill that passed open. Nonzero finalization delays
can therefore make every otherwise eligible entry late; do not reset them to
obtain trades. The later range is usable only after the hour is available.

For a position already held before an opening event, a stop/target reached at
that opening precedes the unresolved later range. Targets fill at their original
limit with no favourable gap overshoot or extra slippage, matching retained120
accounting. A stop gap fills the opening exit-side price with adverse market
slippage. Only if neither level was reached at the opening and both are reached
within the later unresolved range does the adverse stop win. This clarifies the
spec's 'always adverse' as an intrabar ambiguity rule, not permission to ignore a
known preceding opening event. Newly filled positions use only the post-open range.

This is a documented pre-market interpretation, not evidence of executable quote
timing, a favourable path selection or a new market trial. The price kernel applies
spread/slippage; commissions, financing, account sizing/reservations, daily loss
latches, sequence/restart reconciliation and native orders remain separate work.

## Dated clarification — protocol revision 4, sprint 166

16 November 2026. Reconcile the original roadmap's section0 ('Phases1 to9 are
software. Phase10 is the first contact with data') and Phase2's software acceptance
bullets with the overly restrictive status notes from160-165. Actual source
admission is not a prerequisite for implementing/testing Phase3-9 on invented
inputs. Phase2 engineering criteria are accepted on the labelled163-165 software
evidence; its actual source/use/calendar/coverage admission remains open. This
does not mark real data qualified or silently complete its missing evidence.

Continue software phases in order after their engineering checks pass. Before
any actual development counts, price replay, historical study, collection or
demo step, the appropriate source/run/date/clock/cost/exposure gates still apply.
No protected data, stopped provider route, grant, account or order is unlocked.
The market gates, all five strategies, parameter values and economic rules are
unchanged. This corrects workflow ordering, not market acceptance.

## Dated clarification — protocol revision 5, sprint170

17 November2026, before any TRL market counts/returns. Implement automatic group
identity using169's exact-touch groups. A new selected touch set receives a fresh
group unless it is exactly the union of prior registered same-profile/frame/kind
strict-subset groups. That exact-union case is an alias merge: union consumed
state with the new representative. A set containing a touch not represented by
those prior groups remains genuinely new, even if its confirmation preceded its
first eligibility. Exact-touch geometry aliases already share a group. A mere
strict-subset retirement is not by itself permission to merge opportunities.
Use registered history before the current bar, including terminal/consumed groups;
do not let same-bar registration order decide whether an opportunity is new.

On each completed publication, stage declared pre-existing trigger consumption
before current-bar pokes, then age retirement, new validated registrations/alias
merges and strict-superset retirements. A poke takes precedence over age retirement.
Declared triggers remain an interface, not detected setups. Search incompleteness
blocks eligibility/new registration/trigger admission but cannot suppress an
observable poke or age retirement. Missing interval coverage blocks eligibility;
it does not fabricate a wick or reopen a terminal instance. Known calendar closures
preserve bar-index adjacency. Lifecycle VALID history and current entry eligibility
are separate; neither grants an entry. Automatic setup predicates remain Phase6.

This records the deterministic group/transition interpretation before automatic
engine fixtures, with the same five strategies, parameter values and zero market
trials. The initial market study remains unassigned/unrun; all source/run gates,
protected dates/routes, grants and orders-off are unchanged. Engineering version
TRL_ENGINE_170_V1 binds this revision; no prior source/outcome record is rewritten.

## Dated clarification for sprint 172, protocol revision 6

17 November 2026. Evaluate the D1 bias at the latest available completed daily
bar. Here price means that bar's close, and each line is valued at that bar's
scheduled D1 index. A line must be strictly below or above the close on its
respective side and at most three daily ATRs away, including the boundary.
Report all equally near line IDs in display order by ID. Equal distances
within one side have the same effect on bias.

H4 reads the D1 snapshot at the H4 publication time. The existing aggregation
order publishes D1 before H4 when receipt times tie. Before a subsequent
session is due, use the latest completed D1 snapshot. An overdue missing
session makes the context unavailable. A calendar closure adds no due session.
Missing history resets D1 indicator warm-up and line coverage according to the
existing line engine. An unavailable or zero daily ATR and an incomplete
search also make the bias unavailable.

This interpretation was recorded before the sprint's invented replay checks.
Only TRL_BRK3_E1_D1 uses the table. W1 and MN remain later extensions.

## Dated clarification for sprint 173, protocol revision 7

17 November 2026. For the first BRK3 setup increment, compare the previous
scheduled H4 close with the same action ray at the previous index. The
current close must reach one declared price tick beyond the ray, inclusive.
When a selected action geometry would first qualify but its current close is
already beyond the ray, record MISSED_BREAK even inside one tick. Its current
penetration prevents future use of that geometry.

Use a separate H4 lifecycle for opposing safety lines with the core slope rule
and two or more confirmed touches. The 30-bar minimum applies to core action
lines. G35's safety line is 28 bars old at the trigger, as expected under the
separate safety requirement. Check the current wick. Rank strictly correct-side
lines by distance from the trigger close, then by descending touch count.
Equal safety scores abstain with SAFETY_LINE_TIE. Consume all current triggers
first. Resolve opposing directions and economic rank ties before evaluating
the selected setup's safety and optional D1 gate, without falling back to a
lower-ranked setup. The core stop uses the current (unprojected) value and
outward tick rounding. Entry-observation checks remain a separate increment.

## Dated clarification for sprint 174, protocol revision 8

18 November 2026. Resolve each READY BRK3 setup against the first scheduled
H1 open at or after the trigger close. In the invented Level B sequence, a
completed H4 decision received at the same timestamp precedes the assumed
H1 open. A later receipt misses that open. Use the next scheduled H4 close
as the exclusive opening deadline, including across declared closures.

The completed H1 row supplies evidence for its assumed bid open and spread.
Use only rows received by the replay cutoff and by the next scheduled H4
close. Process receipts at that close before recording an expiry. An absent
first row stays pending before this deadline. At expiry a missing or delayed
first row ends the attempt with MISSING_ENTRY_BAR. No later opening replaces
it. Freeze the trigger's exact ATR and stop. Apply the inherited hypothetical
spread floor and slippage and check the exit-side price against protection
before the distance and spread gates. These are price-only invented outcomes.

## Implementation note for sprint 175

18 November 2026. FXR_M uses the existing FXR action profile for the
90-bar formation span and both slope gates. It selects opposing safety
using the current candle and the same full-wick protection profile as BRK3.
Freeze both the current safety value and its value four scheduled H4
indices ahead. Buffer and round the projected value outward using the
trigger ATR and declared price tick.

The invented Level B adapter applies the existing opening schedule, expiry,
and price checks with exit model E2. If those checks pass, report
E2_TARGET_SELECTION_UNAVAILABLE until the Phase 7 support and resistance
finder can supply a qualifying fixed target. The setup has consumed its
opportunity. No fill is recorded without the required target.

## Implementation note for sprint 177

18 November 2026. BNC uses the current completed H4 ATR for the contact
band. Its support low or resistance high must be on the correct side,
including equality, within one quarter ATR. Its close must be strictly
on the correct side. The trigger requires a pre-existing eligible line
and at least six scheduled indices since the last accepted confirmed
touch and the last observed approach.

An approach satisfies the wick and close conditions on a currently
selected line, including its formation bar and a bar blocked by spacing.
It resets spacing when observed. Do not backfill approaches for geometry
that was unavailable at the time. Match prior approaches by unchanged
geometry or resolved opportunity group. Use the contact line as E1
protection at its current value with the standard buffer and outward tick
rounding. Consume qualifying groups at the completed contact before
ranking or entry price checks.

## Implementation note for sprint 178

18 November 2026. The declared DLY profile is available to invented replay
through an explicit opt-in. Scope the initial break geometry and consumed
group to that profile. Start waiting only when the selected break lacks
protection. When safety already exists, use the immediate E1 path. Each
waiting record keeps its own original trigger, direction and action ray.

The tenth scheduled H4 close is the exclusive waiting deadline. If the
source ends sooner, its final scheduled H4 close bounds the wait. At each
observed bar, check expiry, required coverage and search, a close back across
the original ray, and travel strictly greater than the current one-ATR limit
before selecting safety. Equality at the ray or chase boundary passes those
respective guards. A gap invalidates a pending wait because the earlier
invalidation order is unavailable. DLY uses the context-off declaration.

The first valid protection gives the decision close, its ATR and its
rounded E1 stop. If several pending or fresh setups reach a decision on
the same bar, apply the existing opposing-direction and economic tie rules.
Enter through the existing Level B checks on the first scheduled opening
after that decision. The report can show an elapsed deadline without a
synthetic bar. Checkpoints reconstruct from the supplied bar prefix and
require explicit DLY opt-in on restore. The initial study grid excludes DLY.

## Implementation note for sprint 180

18 November 2026. Freeze FXR's level candidates at the completed trigger
using the inclusive last 500 scheduled H4 indices and one quarter of its
current ATR. Use confirmed H4 and published D1 pivots visible at that
frontier. Resolve each D1 extreme to a unique H4 child with the same exact
price using the observed daily children. Report and omit unresolved daily
extremes. Deduplicate matching kind, H4 occurrence and price. Preserve equal
prices at distinct occurrences.

At the first eligible opening, run the usual spread, slippage and stop
checks. Select the nearest profitable-side cluster median whose target,
rounded toward entry, is at least twice the exact slippage-adjusted initial
stop distance away. Continue to a farther eligible level when rounding
leaves one too close. If none qualifies, skip with NO_VALID_TARGET.
The accepted E2 price position fixes its stop and target at entry.

## Implementation note for sprint 181

18 November 2026. Price-only exit paths are evaluated separately for
the modeled entry attempts. Each path uses the declared H1 schedule and
the completed rows visible at its receipt cutoff. Start with the opening
fill, then evaluate the entry hour's range under its original protection.
Each further range uses the protection effective at that hour's open.
An H4 receipt can affect the first scheduled open at or after its actual
availability. Declared closures preserve scheduled adjacency. An absent
completed hour blocks later claims about the path.

For E1, a completed post-entry close beyond the held ray latches the
market exit before considering a change of protection. An observed poke
that closes inside freezes the hard stop while the held ray continues to
govern close-beyond. An unpoked held line can tighten its stop. Eligible
same-side replacements must have formed after entry and provide a
strictly more protective rounded stop. An unresolved replacement tie
preserves the held line. E2 retains its opening stop and target.

The invented exit path defaults liquidation to the final declared H1
open or uses an explicitly selected scheduled opening. It excludes
price candidates at or after that cutoff. A missing liquidation row
at the partition end leaves the path OPEN_AT_BOUNDARY with its last
known exit-side mark. Opening stop and target hits keep precedence over
scheduled market exits. The exit path is reconstructed from the source
prefix and setup checkpoint before account integration.

## Implementation note for sprint 182

18 November 2026. An optional invented Level B risk report uses one
reservation or held position for a single strategy, cost profile and
partition. Reserve at the first scheduled opening after setup eligibility,
then settle the attempt when the opening row is observed or the window
expires. An occupied opening is terminal for that attempt. A held path
releases capacity only at receipt of its closing evidence. This preserves
occupancy on an opening that closes the held position. Missing exit
evidence leaves capacity occupied.

The risk increment takes explicit USD equity, free margin, UTC-day
reference and pause snapshots at the scheduled openings. A missing
snapshot abstains. A pause observed in the snapshots persists through
the UTC day. Size against the frozen 0.25 percent risk budget, available
margin, 99 percent reference floor and inherited lot bounds. Floor the
minimum of those limits to the volume step. Estimated stop loss includes
the modeled entry price, exit slippage and round-turn commission. The
snapshot mechanism supplies test inputs before the independent cash,
cost, equity and rollover ledger is built.

## Implementation note for sprint 183

18 November 2026. The optional invented Level B ledger starts each
strategy, cost profile and partition at the frozen hypothetical USD
10,000. It sizes from reconciled cash when flat. A modeled fill posts
half the round-turn commission. Closed trades post gross price P&L,
the remaining half and the total financing already charged to cash.
Their net loss is compared with the original sized stop estimate.

Held equity uses bid or ask as appropriate. At the end of a completed
H1 that the position survives, the adverse range observation can latch
the same-day entry pause. It cannot establish an exact intrahour time.
The pause and equity also follow opening and closing marks and debits.
The next UTC day uses the reconciled previous executable equity before
its first financing debit, including known exposure over a declared
closure. Wednesday rolls three units and weekend days zero.

When a held H1 straddles UTC midnight without a boundary mark, financing
can be charged for proven continuing exposure, but entries require a
later valid day reference. An intrahour exit straddling the boundary
leaves the position unresolved because rollover order is unknown.
Unresolved paths retain the last exit-side mark and open commission
liability. Financing is posted only through reconciled exposure.
Same-opening entry remains blocked and cash becomes reusable only
when the closing observation has arrived.

## Implementation note for sprint 185

18 November 2026. The invented Level Q adapter uses ordered bid and ask
observations. Geometry uses the per-quote midpoint, aggregated into
scheduled H1 slots and completed H4 and D1 publications. A slot seals at
its declared finalization time. Empty slots remain missing. The invented
tape provides clock and sequence fixtures for software verification.

An entry quote must have source time strictly after the setup receipt.
Quote receipt must precede expiry and liquidation. Explicit sequence
orders quote observations at an equal timestamp. They must be within
two seconds of source time and inside their declared session. Repeated
identical observations at one source timestamp do not advance execution.
The effective spread cap of 1.5 pips determines entry observation
eligibility. Stop, distance, size, and capacity checks settle the first
eligible attempt. A held position uses fresh bid and ask even on a wide
spread and blocks admission on the quote that closes it.

E1 updates require a publication strictly before the quote's source
time. An H4 overlapping entry can latch a close-beyond exit. Whole-bar
trailing and wick checks start with the first fully post-entry H4.
Liquidation requires an eligible source observation at or after the
declared cutoff, with receipt inside the partition. A missing close
leaves the last mark and open liability. UTC day reference resets require
a fresh prior boundary mark or a fresh closing mark carried through a
declared closure. Checkpoints bind and reconstruct the attempted tape
prefix, settings and account state.
