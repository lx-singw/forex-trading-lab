# Daily risk119 — frozen admission contract

Implement admission and cost-aware lot proposals for fixed117/118 daily features
on invented quotes and account marks. No fills, trade P&L, equity curve, quote
aggregation, market data or order API. All117 performance cells stay unrun.
Preserve118 and earlier canonical sources. No provider/contact, SDK or MT5 action.

Strict JSON `FXDL_DAILYRISK119_V1` contains an invented clock/symbol/case, one118
invented daily bundle, an initial invented USD DEMO account, and sequential quotes
with supplied invented executable-equity/free-margin marks. Reject real/contest
synthetic trade modes, unknown fields, boolean numbers, nonfinite values, conflicting
source timestamps and backward/missing sequences. This is not an actual broker
account-type lookup. No input can enable market or real-money execution.

Quotes have positive finite bid/ask, source and receipt times in118's invented
2000–2003 interval. Receipt cannot precede source. Prices are bounded at1,000,000
and account marks at +/-USD1,000,000,000 for fixture safety. Initial equity must
be positive and its availability must precede the first quote. Free margin cannot
exceed nonnegative equity; negative marks may represent an invented depleted
account. A held snapshot is an immutable invented side/volume/entry/stop/target
record with valid geometry and0.01-step volume, at most1 lot. No account identifier,
password or server name is accepted.

Every event recomputes118's decision from its target and bound observed prefix.
The first request for a session binds its exact decision time and feature digest;
later conflicting identities reject. Freely constructed decisions are not accepted.
Reject a feature decision time later than the quote's receipt before computing it.
Complete trading sessions through quote receipt require bars. Future valid prices,
account marks or quotes cannot alter an earlier outcome. Whole-bundle structural
errors may reject the fixture; future records are not applied to current state.

An eligible opportunity requires a new source quote, source strictly after feature
decision/availability, age0..2000ms inclusive, the latest available completed
feature, a declared trading session and effective spread no more than1.5pip.
Before-feature, stale/repeated/closed/wide/stale-feature quotes do not consume an
opportunity. A session's first eligible quote consumes its single opportunity even
when held, paused, inactive, insolvent, lacking margin or below minimum volume.
Later eligible quotes cannot reenter that session. Exact latest event replay is
idempotent; altered duplicates reject. First proposals reserve the aggregate entry
slot across later sessions. They are not positions or fills and are not released
in119. Existing held snapshots never change size/stop/target in response to signals.

Base/adverse profiles match113's fixed hypothetical Config and spread floors.
Base fee$7/lot round turn and0.2pip/fill; adverse$10 and0.5pip/fill with1.2pip
spread floor. Keep contract100,000, leverage30, lots min/step0.01/max1,2R target,
entry risk cap0.25% and daily pause1%. Financing metadata is retained but no
financing accrual occurs here. These are not qualified broker specifications.

Decimal arithmetic uses the exact decimal spelling of JSON numbers. Preserve bid;
effective ask=bid+max(observed spread, declared floor). Entry estimate=effective
ask+slippage for long, bid-slippage for short. Stop=entry-side*118distance;
target=entry+side*2distance. All levels must be positive; distance must exceed
spread+entry slippage. The stop is anchored to the proposed slipped entry, so
spread/entry slippage are not charged a second time to that stop distance.

Budget=positive supplied equity*0.0025*118risk multiplier. Estimated stop loss per
lot=(distance+exit slippage)*contract+round-turn fee. Immediate hypothetical
liquidation debit per lot=(effective spread+2slippages)*contract+round-turn fee.
Margin per lot=entry*contract/leverage. Floor to0.01 the minimum of budget/stop
loss, free margin/(margin+half fee) and1 lot. Abstain below minimum; never round
up or aggregate member budgets. Stop-risk and margin inequalities are checked
before output. Zero-risk decisions abstain without a zero-risk Config.

UTC source-day opening anchor is the preceding supplied executable-equity mark,
including across missing days. Each current supplied mark is checked against99%
of that anchor; at/below it latches pause until a new UTC source day. Recovery
within the same day does not clear pause. Also abstain if the proposal's immediate
hypothetical liquidation debit would reach that threshold. Proposals do not debit
equity or free margin and do not invent fees paid. Marks are fixture inputs, not
calculated or verified liquidation values. A later fill/financing engine must
independently reconcile them before any market evaluation.

Stop-risk budgets are entry estimates, not guaranteed maximum losses: financing,
gaps, changing spreads and actual execution can exceed them. Gapped invented marks
exercise pause logic without manufacturing a stop fill or performance curve.
No martingale or loss-dependent increase in risk multiplier.

Freeze all fixtures, source/test/protocol hashes, rules and profiles before proposal
demonstration. Checkpoint envelopes bind fixture/manifest/profile/candidate/cursor.
Restore rebuilds only the observed prefix and compares complete canonical state
including consumed identities, reservation, pause, marks and outcomes. Reject
altered state with a recomputed checksum, boolean cursor and cross-rule/profile
checkpoints. Checksums are consistency checks, not authentication or broker
reconciliation. Preserve every accepted, abstained and malformed case. No strategy
selection or profit claim follows from these software checks.
