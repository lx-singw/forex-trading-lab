# Chronological runner 014 — implementation protocol, 2026-10-02

Implement HISTORY-009-PLAN.md unchanged: folds A (2020–2021 selection, 2022
test) and B (2021–2022 selection, 2023 test), five C00–C04 controls under frozen
base/adverse costs, 40 runs. No new strategy or parameter search. This stage
implements software using invented data; real data remains blocked by annual
clock and coverage defects. No downloads, broker calls or order functionality.

Freeze a new source archive, exact input hashes and window bounds before replay.
Require all four years, all twelve source months per real year, year-specific
review approval, zero unresolved open-session gaps, source lineage and bound
clock/price evidence. A global pass cannot override a failed year. Review files
must explicitly bind provenance and tick bytes and preserve the research
history. The reviewer, not this runner, must establish clock and completeness;
booleans or hashing cannot establish those facts. Existing diagnostic reports
do not implement this approval schema. Do not write an approval for current
market inputs or fabricate normalized data to make them pass.

Normalized annual gzip CSV uses sequence,time_msc,bid,ask. Provenance includes
kind=chronological_research_ticks, symbol=EURUSD, year, synthetic, ticks,
first_ms,last_ms and data_sha256. Verify every row, sequence, timestamp, quote,
month, annual bounds and count before freezing. Keep all observed rows and
same-ms quotes. Inventory gaps and observed hours. Bind external review evidence
and original source files by hash. Market review kind=chronological_data_review
requires performance_evaluation_ready=true, synthetic=false and years 2020–2023.
Each year needs matching data/provenance hashes, performance_evaluation_ready,
clock_verified, independent_corroboration_passed, source_lineage_reviewed,
zero unresolved_open_session_gaps and source_months listing all twelve months.
Evidence bindings must use absolute paths, be nonempty and match their bytes. Costs remain
the frozen modeled scenarios, not claimed verified broker terms.

Synthetic inputs require explicit synthetic provenance and a distinct review
kind=synthetic_chronological_fixture with performance_evaluation_ready=false.
Output must remain labelled invented software evidence with market approval
false. Never accept synthetic inputs via the market path or mix the two roles.

Every window resets to $10,000 with no position. Use the preceding 201 observed
closed H1 bars for 2021/2022/2023; freeze the exact warmup start. For 2020, the
first 201 observed bars are warmup and evaluation begins at observed hour 202.
Never trade during warmup. Carry positions within a training window, including
quarter/year boundaries, then close at the last actual quote before its end.
Marks at the last quote before each boundary measure period equity; closing
costs at the final quote belong to that final period. Include empty quarters as
zero observed equity change and disclose their observations. Assign closed
trades by close time. Record quote, balance and open-position state at each
observed quarter end for an independent equity/charge arithmetic checker. Reconcile periods and trades to final net P&L; no restarted
annual returns may be concatenated into a claimed portfolio result.

Save ten training reports, then exclusive-create a training-only selection
record with their hashes. Only after this record exists may test replay begin.
Publish all ten test controls even when the choice is cash. Cash earns zero
interest and fails the positive-edge screen. Choice A cannot be revised after
2022; choice B uses 2022 only as its declared training year. Screens and ties use
the existing selection.py implementation. Final screen requires both chosen
years positive at both costs, at least 20 trades/year and tick drawdown<=10%.

Refuse changed inputs, evidence, code or configurations; refuse existing run
folders and partial-run restart. Preserve incomplete folders for inspection;
never resume without a separate declared recovery protocol. A completion
manifest is written only after all 40 reports and both choices reconcile.
Meaningful tests must cover future-data exclusion, locked choice ordering,
marked open positions and costs across boundaries, warmup, same-ms ordering,
changed evidence, blocked years, cash fallback and partial/duplicate output.
Keep 008/009/012/013 evidence untouched; 2025 remains excluded and future
November–December 2026 remains reserved. No execution approval follows.
