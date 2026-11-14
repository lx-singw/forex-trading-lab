# Combination stress116 — completed offline checks

Built a fixed adversarial matrix around unchanged115 UNANIMOUS/AGREE2/CASH.
No strategy parameters, member decisions, costs or sizing rules changed. New116
code adds a frozen-matrix runner, explicit invented transformations, an independent
fill/risk/financing/equity ledger, and a restore wrapper that reconstructs the
observed prefix before accepting complete checkpoint state.

**269 focused tests passed**:30 new and239 retained, no failures/errors/skips,
161.827 seconds in unittest (161.901 seconds including runner overhead). The initial
29-test version also passed in98.735 seconds. Review then added strict duplicate
field rejection inside the original inner checkpoint and one regression test.
Both tested source versions and both test outputs are preserved; no executed test
failed. Older2,095 active-suite results are retained, not rerun.

Tests compare all96 paths with the retained114 simulator using independent
agreement arithmetic. Fills/costs/lineage/final metrics and pause state
match. The separate ledger uses reported entry admissions and directly calculates
floor sizing, one risk budget, one-position/spread/pause/stale-hour guards, first
observed stops/targets, side-specific fills, fees and financing through missing
days, executable-fill equity and drawdowns without simulator fill/size/equity
methods. It rejects changed fills, lots, financing, equity and overlapping entries.
It cannot independently discover an omitted strategy entry; the reference-engine
comparison covers that separate concern in these fixed tests.

All26 input/manifest files were frozen before the demonstration. All96 paths passed
independent audits and resumed/final checkpoint equality. Latest duplicate replay
is idempotent. At the predetermined restart points26 paths held a position and
four had a daily pause. All576 checkpoint faults rejected:192 binding failures,
96 boolean-cursor failures,96 obsolete metric failures, and192 reconstructed-state
mismatches from rehashed balance/protection/pause changes. Strict duplicate-field
inner-checkpoint rejection is separately tested. The wrapper replays only the
observed prefix, not future steps; checksums remain consistency checks, not
authentication or broker reconciliation.

All nine malformed inputs rejected with their exact predefined reasons, with no
performance metrics: stale/future labels, missing sequence, conflicting same-source
prices, clock reversal, crossed quote, boolean timestamp, non-invented clock and
duplicate JSON field. Every accepted/rejected case and checkpoint fault remains in
the saved matrix report; there are no filtered verification failures. CLI exit0,
stored counts and summary agree. The demonstration took89.804 seconds.

The table contains all96 outcomes as hypothetical USD net, with trade counts in
parentheses. Each cell starts its own $10,000; never add cells as a portfolio.

| Invented case | Rule | Base development | Base validation | Adverse development | Adverse validation |
| --- | --- | ---: | ---: | ---: | ---: |
| Control | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Control | AGREE2 | +74.92 (3) | +50.44 (4) | +62.83 (3) | +38.63 (4) |
| Control | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Wide entry | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Wide entry | AGREE2 | -5.61 (1) | +50.44 (4) | -8.00 (1) | +38.63 (4) |
| Wide entry | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Wide short | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Wide short | AGREE2 | +74.92 (3) | +48.16 (4) | +62.83 (3) | +38.63 (4) |
| Wide short | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Gap down long | UNANIMOUS | -18.45 (1) | 0 (0) | -18.69 (1) | 0 (0) |
| Gap down long | AGREE2 | -1516.06 (3) | +50.44 (4) | -1418.27 (3) | +38.63 (4) |
| Gap down long | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Gap up short | UNANIMOUS | 0 (0) | -27.63 (1) | 0 (0) | -27.96 (1) |
| Gap up short | AGREE2 | +74.92 (3) | -1480.99 (4) | +62.83 (3) | -1388.87 (4) |
| Gap up short | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Calendar outage | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Calendar outage | AGREE2 | +74.92 (3) | +94.82 (5) | +62.83 (3) | +79.31 (5) |
| Calendar outage | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Missing previous hour | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Missing previous hour | AGREE2 | +74.92 (3) | +50.44 (4) | +62.83 (3) | +38.63 (4) |
| Missing previous hour | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Repeated quote | UNANIMOUS | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| Repeated quote | AGREE2 | +74.92 (3) | +50.44 (4) | +62.83 (3) | +38.63 (4) |
| Repeated quote | CASH | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

There are26 positive,10 negative and60 zero/no-trade paths. These counts are not
market probabilities or win rates. UNANIMOUS can still trade and lose after a gap
changes the observed history. CASH is a reference, not evidence of an edge.

The largest single-trade loss is$1543.09 in AGREE2/base/development gap-down-long,
against a$25 entry estimate. The full path nets-$1516.06 after later trades.
The short gap also breaches its estimate and triggers a daily pause. Twenty
account paths contain a trade loss above its entry budget, including ordinary
discrete stop overshoot and financing; these are not twenty independently observed
market gaps. Entry risk sizing and a1% daily entry pause cannot guarantee maximum
loss through a price gap. Higher costs sometimes reduce dollar losses because
floor sizing admits fewer lots; this is not evidence that costs help.

The wide-entry case blocks early entries and leaves only the later losing trade
in development. In base validation, widening the held short's ask advances its
stop from10:30 to10:00 at hour466 and worsens the path. Adverse costs already
closed that short before the perturbation, so its result is unchanged. Removing
hour201 suppresses entry at202; the first entry moves to203. Identical net in
this case does not mean a missing quote was imputed. Repeated quotes preserve
prices/source timestamps and trades while retaining the extra observations.

The declared151-hour outage preserves the receipt gap and held protection, with
weekday, Wednesday-triple and weekend-zero financing charges. Observed-bar history
changes, producing a later additional trade. Its higher constructed net is not
evidence that outages improve trading or that missing observations are safe.

All536 predecessor source/config/test hashes remain unchanged; five new files make
541. All62 prior native input hashes and prior output bindings are preserved.
Sources, inputs, both test versions, results and handoff history are bound by the
final116 archive/review. Full decision traces have count+canonical SHA256 in the
matrix output and are reproducible through unchanged115 Replay with frozen inputs.

Prices, UTC labels, spreads, financing, leverage and exact target fills remain
invented or hypothetical. No empirical strategy edge, stronger market engine,
winner, weights, probability of loss, maximum-loss guarantee or readiness follows.
Native107/109/111 remain inspect-only; actual clock/age/quality/cost qualification
is unresolved. No network, provider/history/reserved-period reruns, acquisition,
SDK, MT5/settings/accounts/log inspection, support contact or orders occurred.
Market/paper/order/real-money availability stays false. No user launch is needed.

Next is the prepared [strategy evidence117 review](STRATEGY-EVIDENCE-117-PLAN.md):
evaluate published evidence and required data before freezing any new candidate
trials. It is unexecuted and will not tune from these invented outcomes.

Local evidence: `reports/combination-stress-116-*` and
`data/combination-stress-116-invented-demo/matrix-report.json`.
Read the [usage guide](COMBINATION-STRESS-116-USAGE.md) and
[protocol](COMBINATION-STRESS-116-PROTOCOL.md) for reproduction and limits.
