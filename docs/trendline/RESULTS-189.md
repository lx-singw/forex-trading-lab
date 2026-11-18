# Sprint 189 · Provisional pivots, contacts and no-trade reasons

18 November 2026. The saved Level B and Level Q viewer uses hollow diamonds
for provisional H4 pivots and filled diamonds for confirmed pivots. A
candidate must be a strict high or low against the preceding three
contiguous candles and the right-hand candles received so far. Its receipt
evidence shows how many more H4 candles it needs. A tie or stronger right
extreme removes that side when the candle arrives. A gap clears pending
sides when the first publication after the gap arrives. A dual extreme can
have both sides pending, and the confirmed detector excludes it if both
sides survive the full window. Strategy lines continue to use the bound
confirmed detector.

## Inspect a contact or a no-trade reason

On `TRL_BNC_E1`, **Bounce contacts** steps through recorded wick contacts.
The chart marks contacts and blocked approaches differently. Select a mark
to see the H4 receipt, the wick price, the exact distance to the line and
the ATR tolerance. The inspector links the contact to its recorded action
line revision and the setup decision for that receipt.

**No-trade reasons** steps through recorded setup and entry rejections,
blocked contacts and delayed setup reasons. At the setup receipt, the
inspector shows line-search coverage, eligible line counts and counts by
recorded anchor or candidate rejection reason. At an entry receipt it
shows the requested stop, any recorded opening and deadline, and the
entry outcome. Level Q entry evidence also includes the selected quote
when one exists.

## Verification

The 75-receipt invented bounce example shows a formation-bar approach at
H4 index 50, a spacing rejection at 55, and a qualifying contact at 61.
The later H1 opening receipt resolves the reserved attempt as
`STOP_ALREADY_CROSSED`. Cash stays at `$10,000` in this fixture. Separate
pivot tests check the three-receipt countdown, same-prefix agreement,
equal highs, a coverage gap, and a dual extreme.

All 69 targeted tests passed. The four new viewer checks ran alongside
13 retained trendline viewer tests and 52 pivot, bounce and Elliott
viewer tests. Chrome at 1440 × 1000 and 390 × 844 checked the hollow
markers, contact selection, line evidence and no-trade navigation on
Level B. The Level Q run also passed quote, fill and setup-link checks.

The existing viewer export command accepts either the saved Level B or
Level Q replay. [Export and open a replay](RESULTS-188.md#export)

Phase 8 continues with retrospective browsing, ledger exports and manual
annotation comparison. This sprint uses invented replay evidence.
