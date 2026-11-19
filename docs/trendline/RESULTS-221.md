# Sprint 221 · Separate opening evidence for Level B

19 November 2026. The historical Level B counter now takes completed
bid bars and opening evidence from separate arrays in one reviewed input.
A completed bar still contributes to H4 and D1 geometry when its opening
evidence is absent or late. An entry still uses the first scheduled H1
slot and the reviewed decision order. [Protocol C4](PROTOCOL.md#c4-entry-and-data-level-semantics)

## Reviewed input

Use manifest schema `TRL_PHASE10_INPUT_221_V1`. The path fields, tick size
and same-time ordering policy from Sprint 218 still apply. The plan's
`input_sha256` binds the exact bytes of the whole `price_file`. Its JSON
object has two arrays. [Manifest details](RESULTS-218.md)

- `hours` carries `start`, `end`, `available_at`, and bid `open`, `high`,
  `low` and `close`. The timestamps are UTC epoch milliseconds. Price
  fields are decimal strings. An hour has no spread field in this format.
- `openings` carries zero or one record per scheduled H1 window in start
  order, with `kind`, `start`, `end`, `bid`, `source_at` and
  `available_at`. For `paired_quote`, supply `ask` and both source and
  receipt timestamps. The spread in pips is derived from the pair, and
  both timestamps must equal the scheduled start for entry eligibility.
  For `bar_open_assumption`, supply `spread_pips` and a null
  `source_at`. Its completed-bar receipt is subject to the plan's
  finalization delay. This method requires independently reviewed
  evidence for its opening price, spread and timing assumptions.

Each record matches the reviewed H1 start and end exactly. The
`historical-input` receipt reports opening coverage at the development
cutoff alongside H1, H4 and D1 coverage. Rebuild older research bundles
with deliberate opening records and review the new digest before use.
Move bid OHLC into `hours` and supply opening records wherever supported
by evidence.

## Counting and verification

The counter distinguishes missing evidence, a late source quote, a late
receipt and evidence beyond the setup deadline. It uses the frozen price
filters only once the scheduled opening has passed those checks. A later
H1 record cannot replace a missing opening. The existing same-time order
and liquidation checks apply. The historical count report uses schema
`TRL_PHASE10_COUNT_221_V1`.

The command fixture verified one BRK3 opportunity under each cost
profile using its explicitly modeled opening. A second run with that one
opening removed retained the geometry, trigger and entry attempt, and
recorded zero eligible entries in those cells. The next scheduled hour
still had opening evidence. Additional checks cover a boundary pair, late
source and receipt clocks, exact spread derivation, an opening without a
completed bar, expiry and invalid input.

All 136 targeted tests passed. The canonical metadata report matched
Sprint 220 byte for byte and Phase 10 remains `UNAVAILABLE`.
The manifest review list is empty.
Exness still needs independent source qualification and an opening
method supported by the exact series. This sprint used fabricated input.
[Calendar and source review](RESULTS-220.md)
