# Fixed combination stress116 protocol

Frozen before116 evaluation. Software checks use invented UTC labels and prices.
Reuse115 UNANIMOUS/AGREE2/CASH and unchanged C00/C05/C06, costs, 201 observed closed
hours, single-position sizing, stop/target fills and corrected019B equity. Keep
all536 predecessor source/config/test files and prior outputs unchanged.

The source is115's continuation generator: 576 hours from2001-01-01T00:00Z,
development begins hour201 and ends before288; validation begins288 with earlier
hours for warmup only. Each cost/partition/rule starts with its own USD10000.
No optimization, portfolio addition, weighting or choice of a winner.

Exactly eight accepted cases, all other quote fields retained:

1. `control`: unchanged continuation, renamed case.
2. `wide_entry`: ask = bid +0.0003 at every event of hours201 through227 inclusive.
3. `wide_short`: ask = bid +0.0003 only at the first quote of hour466.
4. `gap_down_long`: bid =1.05 plus the original within-hour bid wiggle, ask = bid
   +0.0001 throughout hour203. Following hours retain original prices.
5. `gap_up_short`: same construction at hour491, with base bid1.15.
6. `calendar_outage`: omit every event in hours300 through450 inclusive. Preserve
   receipt/source timestamps and the resulting gap. Generated retained events
   get new consecutive sequence numbers; this is an explicit synthetic fixture
   construction, never a repair to an externally broken sequence.
7. `missing_previous_hour`: omit all events in hour201, same declared resequencing.
8. `repeated_quote`: insert an unchanged-source/price quote500ms after the first
   quote of hours202 and490. Resequence the generated fixture. Age remains550ms.

Exactly nine rejected input cases, each based on unmodified continuation with a
new case name. Change event1 unless stated otherwise: stale source = receipt-2001;
future source = receipt+1; broken sequence =2; conflicting same-source price =
event0 bid/ask plus0.00001, source =event0 source, receipt =event0 receipt+500;
clock reversal =event0 receipt/source minus1; crossed ask =bid-0.0001; boolean
source =true. Non-invented clock changes the top-level clock to `broker_server`.
Duplicate JSON field inserts a second top-level `clock` key with the same value.
Expected reasons respectively: invented_quote_age, invented_quote_age,
event_order, same_source_time_changed, event_order, invalid_quote, integer_range,
invented114_fixture_required, duplicate_json_field. No simulator or performance
metrics for rejected inputs. Hash all raw bytes, including invalid inputs.

Freeze exact generated input bytes,115 manifests,116 source/protocol hashes,
definitions, rules, costs and partitions before any matrix output. Load only the
fixed file names in one local matrix directory; reject changed input/code/manifest,
symlinks, excess sizes, extra/omitted definitions and malformed JSON. Creation and
report writing are exclusive; partial artifacts remain visible and cannot resume.

Eight accepted cases x two costs x two partitions x three rules =96 paths.
For each path checkpoint immediately after the first quote at/beyond hour203
(development) or491 (validation), then resume; also restore its final checkpoint.
Latest-event replay is idempotent. Report equality includes trades, decisions,
costs, equity, risk and state traces. Record whether position/pause was active.

For every valid prefix checkpoint test six faults: wrong outer checksum,
cross-rule restore, boolean cursor with recomputed checksum, altered balance+1
with recomputed inner/outer checksums, obsolete metric version with recomputed
checksums, and altered stop+0.0001 when held (otherwise toggle paused) with
recomputed checksums. All576 reject. Validate a good checkpoint first so an
unrelated failure cannot masquerade as a passed rejection check.

116 checked restore first applies115 structural/binding checks, then reconstructs
only the frozen observed prefix and compares complete simulator payload and
cursor/repeats. This detects state modifications even with recomputed checksums.
It is bounded offline reconstruction, not authentication or broker reconciliation.
No future quote may influence prefix state or strategy decisions.

An independent ledger (without calling simulator fills, size_lots or equity
methods) checks reported entry lineage/admission, one position, floor sizing,
one risk budget, margin/spread/pause/stale-hour guards, first observed stop/target
exit, side-specific fills/slippage, commissions, UTC weekday/triple financing
through missing days, executable-fill equity, daily pauses and drawdowns. It uses
reported entry admissions; separate tests compare decisions/fills/metrics to the
retained114 engine with independent agreement arithmetic. This does not constitute
an independent market-data source or empirical strategy validation.

Report every accepted and rejected case, gains, losses, zero/no-trade outcomes,
audit/restart failures and rejection reasons. Compress full decision lists to
count+canonical SHA256 in the matrix report; preserve trade admissions/lineage
and reproduce full traces using unchanged115 Replay with frozen inputs. Fail
overall verification on any mismatch; never filter a failed or negative path.
Archive sources before each test version, retain failures, and bind final artifacts.

Stops and daily pauses cannot guarantee maximum loss through gaps. Hypothetical
financing, spreads, leverage and commissions remain assumptions. Synthetic results
cannot establish profitability, win rate, loss probability or market readiness.
Native107/109/111 remain inspect-only. No network, provider/history/reserved-period
reruns, acquisition, SDK, MT5, accounts/settings/logs, support contact, orders,
paper/market promotion or real-money execution. No user launch required.
