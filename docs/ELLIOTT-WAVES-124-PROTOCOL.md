# EWPB_D124 — frozen causal close-swing hypothesis

This is one Elliott-inspired daily pullback/breakout rule. It does not recognize
all Elliott degrees, a complete five/three-wave structure, diagonals/extensions
or a uniquely correct wave count. LabelsP0/P1/P2 denote confirmed close swings;
calling them wave1/wave2 is a hypothesis, not proof of a future wave3. No future
wave3/5 relation is used to decide an earlier entry. Parameters below are fixed
engineering research choices, not optimized or guaranteed by Fibonacci theory.

The strict wrapper `FXDL_EW124_V1` has kind `invented_wave_detector`, invented UTC
clock, EURUSD, case and a same-case118 invented daily bundle. All118 calendar,
OHLC, lineage, bounds and availability checks apply. Every required trading bar
through the target must exist and be available; closures supply no bar. Retain
the complete selected prefix, at most800 sessions, not only253 bars. Prices are
positive and at most1,000,000; selected bar availability never decreases. Unknown
fields, flags, identifiers/accounts/positions, duplicate JSON, boolean numbers,
market labels and clocks outside2000–2003 reject. Valid future bars may be present
but contribute no price arithmetic/state; structurally invalid future rows reject.

At completed trading barj, confirm centerj−1 as a low if its close is strictly
below both neighbors, or high if strictly above both. Equality never confirms.
Confirmation occurs at barj's actual availability, not the center's observation
or scheduled session close. Calendar closures do not count as trading neighbors.
Append every confirmed pivot immutably. In a separate alternating swing chain,
same-kind pivots replace the last swing only if more extreme; equal/less extreme
ones are ignored. This updates current interpretation without rewriting the
confirmed-pivot journal or previously published outputs.

Consider the latest three alternating swingsP0/P1/P2 once each by content identity.
Long: low/high/low, P0.close<P2.close<P1.close; short is its mirror. Impulse magnitude
`abs(P1.close−P0.close)/P0.close` must be at least0.01. Retracement measured in closes
is within[0.382,0.618], inclusive. Use Decimal precision50 over the string
representation of validated JSON numbers;118's float parser does not preserve
arbitrary-precision original JSON literals. These bands are a chosen approximation, not a
claim that every valid Elliott correction must satisfy them.

The long breakout level is P1's observed bar high; short uses its low. The
prospective invalidation is the minimum observed low from P1 through P2 inclusive
for long, or maximum high for short. It must remain strictly inside P0's observed
low/high origin. If the confirmation bar already breaches invalidation or closes
beyond the breakout, discard the pattern; no backdated or late catch-up signal.
Equality with breakout is allowed at formation; its crossing is strictly beyond.

Keep one active setup slot. An occupied slot discards another considered pattern,
which is never retried. On each later completed bar, check invalidation first
(`low<=stop` long, `high>=stop` short), then expiry after10 subsequent trading bars,
then a closing-price crossing from at/before to strictly beyond the breakout level.
An OHLC bar that touches invalidation and closes beyond breakout is invalidated;
unknown intrabar order never earns the favorable interpretation. Formation and
breakout cannot occur on the same bar. Age10 may trigger; age11 expires.

Consume a crossed setup once even if held by warmup or trend gates. Require253
observed completed trading bars at breakout. Trend is the sign of current close
minus the253rd latest close (252-session direction), and must equal setup side.
Zero/opposite trend suppresses the observation. These are feature gates only;
there is no account, position, funded entry, stop execution or risk sizing here.

An accepted observation contains side, pattern/pivot identities, observation and
confirmation/decision times, observed close, breakout and prospective invalidation,
trend direction, observed-bar/calendar-prefix lineage and fixed-rule hash. Preserve
rejections, pivots, replacements, setup arms, invalidations, expiry and suppression.
Duplicate latest step is idempotent; altered/older duplicate events reject.
Restore binds input, manifest and cursor, reconstructs only the observed prefix,
and compares complete canonical state. Rehashed economic/feature edits and boolean
cursors reject. Hashes are local consistency checks, not source authentication.

The detector never reports trades, wins, returns, lots, entry fill or target fill.
The separately planned standalone cost-aware experiment would execute only on a
fresh eligible observed bid/ask quote strictly after signal availability, using
unchanged base/adverse cost profiles, one aggregate position,0.25% maximum entry
risk,1% daily entry pause and a2R target from its actual modeled entry/invalidation
distance. That adapter is unimplemented and untested in124. Stops cannot guarantee
maximum loss through gaps. No mixture or order-placement capability is introduced.

Keep117's16 market cells unassigned. A separately tracked future standalone
EWPB_D124 experiment plans four additional cells (two costs × two chronological
partitions), also unassigned/unrun. Existing qualified-data/clock/cost and24-month
development/24-month genuinely untouched validation requirements remain unchanged.
No tuning from invented outcomes; future inferential analysis must account for
the expanded trial history. Market/paper/order/real-money admission remains false.

Prior discussion consulted [Elliott Wave International's introduction](https://www.elliottwave.com/free/introduction-to-the-wave-principle/),
which acknowledges multiple valid interpretations. The indexed publisher abstract
of [Jarusek, Volna and Kotyrba2022](https://doi.org/10.1016/j.neunet.2021.10.024)
reports a distinct neural-network/multi-currency approach; full methodology was
not retrieved or reproduced. Neither source validates this detector's thresholds.
