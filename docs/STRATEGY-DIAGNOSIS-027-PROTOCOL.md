# Diagnosis 027 extraction declaration — before calculations

Exact outputs: `reports/strategy-diagnosis-027-ledger.json` (+ SHA seal),
`reports/strategy-diagnosis-027.json` (+ seal),
`reports/strategy-diagnosis-027-table.csv`,
`reports/strategy-diagnosis-027-checks.json` (+ seal),
`reports/strategy-diagnosis-027-tests.json` (+ seal), and final review/source
snapshot JSON/seals/ZIP. Exclusive writes; preserve originals and any failures.

Verify 026 manifest/seal, every binding and archive member, then the 008 archive
SHA/CRC/every member against current original files. Recompute 008's original
module-name/content code digest from its archived module set, not today's larger
module set. Verify exact spec/protocol/runner, all three dataset provenance/data
hashes and matching quality reviews, all 30 report hashes/scenario IDs/ledger
links and summary metrics. Freeze these and diagnosis code/tests before results.
Hash cached tick files but do not parse quotes: logged features suffice for the
declared descriptive questions. No feature reconstruction or strategy replay.

For each trade, independently reconcile `side*(exit-entry)*lots*contract_size`
to gross, `gross-commission+swap` to net, and round-turn/entry commissions to
the frozen configuration. Check stop and 2R target geometry, chronological
nonoverlap, warmup boundaries and aggregate/final cash/return accounting.
No legacy drawdown recalculation or interpretation in this diagnosis.

Define R as `abs(entry-stop)*lots*contract_size`, excluding fees/financing.
Report gross/R, net/R, commission/R and financing debit/R. R is not a guaranteed
loss cap. Stop overshoot uses adverse fill beyond stop; separate imposed exit
slippage from observed quote overshoot using frozen modeled slippage.

Match by entry UTC hour, side and stop distance (absolute tolerance 1e-10 price
units) to a stored nonzero flat-account decision. Require exactly one matching
record for an attribution, preserve missing/ambiguous status otherwise. Each
decision may explain at most one trade. Hour logs explain the signal context,
not an original tick sequence; no same-millisecond tick lineage is inferred.
Recorded features are from the already frozen closed-bar implementation, not
re-estimated from future outcomes. Validate C04 mode against frozen ER cutoffs
and matching reason prefix. No new market-regime claim.

Count every logged reason/branch and nonzero signal, including neutral/no-signal
decisions. Decisions exist only at eligible flat-account contiguous hour starts;
they do not count all hours or signals suppressed while a position is held.
Signals without a matched trade are unfilled/unattributed, not assumed losses
or rejections for a particular reason. Show reported spread-rejection counts and
paused equity points; these do not identify individual rejection causes.

Define rapid re-entry as a next trade within one elapsed hour of the prior exit;
record whether the prior trade lost and whether direction repeats. Longest
loss streak counts consecutive negative-net closed trades within that scenario.
Report all scenario counts, gross/net, mean net R, exits, holding hours, branch
results, stop overshoot and re-entry counts. Base/adverse pairing compares exact
entry timestamp/side identities and records unmatched trades; PnL changes can
reflect a changed trade path, not just subtraction of extra costs.

An independent checker uses Decimal/Fraction arithmetic and separate decision
lookup to verify every trade and branch attribution. Meaningful synthetic tests
cover long/short, invalid accounting/geometry/risk, missing/duplicate/side-mismatched
decisions, zero trades, cost changes, re-entry/streaks and future-log withholding.
Future-log withholding checks attribution stability only; original closed-bar
signal causality is inherited from verified original code, not newly proven from
raw ticks. Tables are descriptive reused-development evidence. No winner, search,
new returns, provider browsing, orders or annual approval.
