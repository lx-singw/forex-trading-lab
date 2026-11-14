# Trade-path extraction 029 — declaration before calculations

Outputs: `reports/trade-path-029-ledger.json`, per-window
`reports/trade-path-029-{january,april,july}.json`, all-30 summary JSON/table CSV,
checks/tests/review/final-source JSON and source ZIP. JSONs have SHA seals;
exclusive writes preserve every original and failed attempt. No new simulation.

Verify all 786 previous bindings, 752 archive members and 34 external bindings;
verify the 028 ledger, all 30 exact reports/lineage, summary/checks and original
three cached data/provenance/quality reviews. Freeze code/tests/formulas/input
hashes and fixed independent spot-check indices before market extraction.

Each trade includes entry and exit source sequences, inclusive. Confirm exact
source timestamp, side/entry price with imposed entry slippage, and modeled exit
price compatibility. Endpoints must reconcile to original net PnL and swap.
Unmatched sequences, impossible order or out-of-order ticks fail, never silently
drop trades. Trade sequences identify tied milliseconds without a time guess.

For an intermediate quote, hypothetical liquidation price is bid minus imposed
exit slippage for a long, or ask plus imposed exit slippage for a short. Net
liquidation = signed price difference × lots × contract size − full round-trip
commission + accrued financing. The entry fee is included once in the round-trip
fee, not subtracted twice. Financing uses the frozen UTC rollover rule, five
daily charges/week with Wednesday tripled, including dates skipped by a gap.
At the exact modeled exit use its recorded fill; targets cannot receive credit
for an overshooting quote. These are cost-model liquidation estimates, not fills
that a broker promises to deliver.

Initial R = absolute entry-to-stop distance × lots × contract size, excluding
costs. Store signed maximum/minimum net liquidation R, earliest sequence attaining
each extreme (ties keep the first), first strict positive mark, first marks at
>=0.5R and >=1R, and first raw bid/ask crossing of nominal stop. No arbitrary
epsilon at thresholds. Store source sequence/time/bid/ask/accrued swap/exit price
and net value for each witness; inclusive quote count and duration are explicit.
Stopped-trade progress counts require the qualifying sequence strictly before
the exit. Signed maxima may remain negative; no clamping a loss into a gain.

One extraction pass per window serves ten scenarios. All 266 trades and all 30
scenarios remain visible; summaries report stops with prior positive/0.5R/1R
progress, winners, exits, average excursions and largest-winner concentration.
No aggregation into a continuous account, recoverable-profit forecast or optimal
exit. Consumed2025 and reservedNov–Dec2026 stay excluded.

Independent checking uses a second source pass: Fraction arithmetic at every
reported extreme/threshold/endpoint witness; exact source-sequence/time/quote
membership; and every endpoint. Before inspecting paths select the first and
last trade index in each scenario (deduplicate one-trade cases) for full-path
independent float extrema/threshold recomputation using a separate formula and
rollover derivation. This fixed selection includes every window, cost and
candidate; do not replace inconvenient cases after seeing outcomes. Independent
checks are arithmetic/lineage evidence, not proof that recorded data or costs
match historical broker execution.

Pre-extraction tests cover both sides, spread/fees/slippage, daily and Wednesday
financing, weekend/gaps, target cap, stop gaps, tied timestamps/sequence order,
threshold and extreme ties, and invalid endpoints. Freeze after tests. Only after
all diagnostics/checks pass may one later bounded hypothesis be proposed, with
rules/budget fixed before new returns. Orders remain unavailable.
