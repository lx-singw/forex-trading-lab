# Daily fills120 — frozen invented accounting contract

Implement a separate offline adapter for fixed117/118 decisions and119 admission
rules. Preserve those sources. Inputs are invented software fixtures only, not
qualified market observations. No broker interface, orders, credentials, account
identifiers, live toggle, optimization or strategy selection. All117 market cells
remain unassigned. No provider/contact, historical/reserved data or MT5 action.

Strict JSON `FXDL_DAILYFILLS120_V1` declares invented UTC milliseconds, EURUSD,
one118 feature bundle, initial flat USD cash with synthetic trade_mode integer0,
and sequential quotes. Reject contest/real/boolean modes, unknown fields, supplied
equity/free-margin/held positions, nonfinite/boolean numbers, invalid chronology,
conflicting same-source prices, unavailable features and missing required bars.
The invented2000–2003 interval is a fixture restriction, not origin authentication.
Initial positive cash is bounded at USD1 billion; quote limits inherit119.

Use independent accounts for T12_D, MR20_D, MIX50_D and CASH, under the fixed
base/adverse113/119 profiles. Each matrix cell has fresh USD10,000 unless explicitly
declared as a sizing-boundary fixture. Never sum their capitals as a portfolio.
The small fixed generator matrix is long target, short target, long stop, short
stop, long gap, short gap, half risk, opposing signals, warmup, zero range,
weekend financing, release next session, quality guards and minimum capital.
Freeze all inputs, malformed cases, sources and independent reviewer before any
demonstration outputs. These paths are not price forecasts or market trials.

Every request recomputes118 from its available prefix; the first request binds
the exact feature identity for that completed session. Future valid continuation
cannot affect an earlier state. Whole-fixture structural faults can reject loading.
No freely constructed signal, position, equity or free margin is admitted.

Processing is transactional and ordered: bind event/feature; set a new UTC source
day's anchor to the preceding calculated equity; accrue all elapsed financing;
execute an existing stop/target on an executable observed quote; calculate equity
and pause; process the daily entry opportunity; mark any accepted entry. A source
quote is executable only when new, age0..2000ms inclusive and in a declared trading
day. Stale, repeated and closure quotes cannot fill or reprice; financing still
accrues with elapsed source time and the last executable quote is retained. Missing
quotes are never interpolated. Wide spreads and stale features block entry, but
do not block existing-position exits/marks on an executable quote.

Entry additionally requires source strictly after feature decision/availability,
the latest available completed feature and effective spread <=1.5pip. Invalid
entry-quality quotes do not consume the opportunity. The first eligible quote
consumes the completed session's only opportunity, including when held at arrival,
paused, inactive or too small. A position held at arrival prevents same-quote
reentry even if its exit releases the slot. Later quotes cannot retry that session.
The next unconsumed session may enter once an earlier position is accounted closed.
Held size, stop and target never change with later signals.

Retain119 sizing with Decimal precision50 and exact decimal spelling of input and
118 numeric outputs. Economic state/ledger numbers are canonical decimal strings;
no cent rounding. Margin divisions are rounded only by Decimal precision. Preserve
bid; ask=bid+max(observed spread, profile floor). Entry=ask+slippage long or
bid-slippage short. Stop=entry-side*distance; target=entry+side*2distance. Distance
must exceed spread+slippage and all levels be positive. Risk budget=positive
calculated equity*0.0025*118 multiplier. Estimated stop debit per lot is
(distance+exit slippage)*100,000+round-turn fee. Immediate liquidation debit is
(spread+2slippages)*100,000+round-turn fee. Floor to0.01 the minimum of risk-funded
lots, free-margin/(entry*100,000/30+half fee) and1 lot. Never round up; abstain below
minimum or if immediate liquidation would reach the daily99% anchor threshold.

A proposal reserves one slot and is explicitly hypothetically accepted on that
same observed quote. Append separate reservation and entry-fill ledger records;
deduct half commission and transfer the reservation to the single held position.
This is deterministic invented acceptance, not a broker fill claim. Release only
after an observed exit-fill ledger record credits gross P&L, deducts exit commission
and closes that position. Latest identical event and repeated finish are idempotent;
modified or older duplicate events reject. No external acknowledgement is assumed.

An existing long uses bid, short effective ask. Stop breach fills observed quote
minus side*slippage, including adverse gaps; never grant a stop-price improvement.
Target breach fills the original target limit, with no favorable overshoot and no
additional target slippage. Stop is checked first.
An observed positive quote whose assumed adverse slippage produces a nonpositive
exit price rejects transactionally as `nonpositive_exit_price`; no impossible fill.
Spread is embedded in side prices, slippage in entry/stop/market-exit prices and
commissions debited once per fill.
Do not subtract those embedded costs again from gross P&L. Stops are estimates,
not guaranteed maximum losses; gaps and financing can exceed the entry budget.

At each elapsed UTC midnight while held, charge the preceding weekday: Monday,
Tuesday, Thursday and Friday one debit, Wednesday triple, Saturday/Sunday zero.
Record every rollover, including zero-debit weekend records and missing quote days.
Base per-lot debit long$3/short$1.50; adverse$4.50/$2.25. A position opened exactly
at midnight owes no preceding-day debit. Financing reduces cash and is attributed
to the held lot without resizing it. This is a hypothetical calendar convention.

Retain corrected019B equity semantics: between exits, equity=cash plus side-specific
observed unrealized gross P&L; it excludes unincurred market-exit slippage/commission.
On a stop/target breach, use the actual modeled exit price and fee, never the raw
overshooting quote. Invalid quotes retain the last executable price, adjusted for
new financing. Used margin while held is original entry*lots*100,000/30; free margin
is equity minus that margin, possibly negative. There is no guessed margin-call
liquidation. Peak/drawdown and daily pause use these calculated marks. Pause at/below
99% of the day anchor latches until the next source day; recovery cannot clear it.
It blocks new entries, not exits. Nonpositive capital is never increased or reset.

Finish only after all events. If still held, close at the final event's executable
quote with adverse market-exit slippage and half commission; if that endpoint is
stale/repeated/closed, reject `missing_executable_endpoint` without a return report.
Do not liquidate retrospectively at an earlier quote. A flat endpoint is valid.
Boundary close is a declared offline partition liquidation, not a trading signal.
Do not accrue beyond the endpoint. Return and equity summaries are toy ledger
reconciliation only, never win-rate/edge evidence or market acceptance criteria.

Freeze manifest/source/rule/profile/input hashes and strict types. Checkpoint
restore rebuilds only events through the observed cursor, then finish only if the
bound checkpoint says finished. Compare full canonical state: cash, lots, original
levels, financing, margin, equity, pause, consumed identities, reservation and ledger.
Reject forged economic state even with a recomputed checksum. Hashes check local
consistency, not signatures, source authenticity or broker reconciliation.

Tests and a separately frozen rational ledger reviewer must independently check
entry lots/prices, both exit sides/reasons, financing, commissions, balance, margin,
equity and drawdown. Cover adverse gaps, open losses, latched daily pause, held first
opportunity, released reservations, volume/margin boundaries, quality, chronology,
future invariance, restarts and altered checksums. Preserve losses, no-trades,
malformed cases and any failed development checks. No tuning from these outcomes.
