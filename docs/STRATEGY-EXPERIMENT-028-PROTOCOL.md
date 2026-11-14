# Experiment 028 pre-return protocol

The fixed plan and `config/research-candidates-028.json` define all five candidates,
three existing development windows, two costs and 30-scenario budget. No adaptive
rerun. All original 008 controls/code/reports and 027 diagnosis are preserved.

Before quote replay, freeze `reports/strategy-experiment-028-ledger.json` and SHA
seal, with code/test/spec/protocol/input/control report hashes. Verify all 700
027 bindings, 667 archive members, 33 external bindings, original 008 archive
members and all exact 2024 data/review/config bindings. Existing quality reviews
authorize only already-seen development, never annual validation. No new dates,
quotes, broker connection, consumed2025 or reservedNov–Dec2026 access.

Outputs are exclusively `reports/strategy-experiment-028-{sample}-{candidate}-{cost}.json`
for the exact 30 scenario IDs, one summary/table, independent checks, tests and
final review/source snapshot (JSONs have SHA seals). Each scenario records full
trades, eligible decision log, evaluation equity curve, corrected metrics, and
entry/exit sequence lineage separately from the original trade fields. Fill
lineage observes inherited fills without changing execution, risk or sizing.
Record sample failures separately and halt claims if input/control parity fails.

Use one cached ordered tick stream per sample and ten isolated simulator accounts.
Independent sample workers may run concurrently; no repeated quote passes to
search parameters. Shared 201-bar warmup and evaluation boundaries from 008;
cash starts independently at the frozen initial equity. Arithmetic CASH is zero.
No annual gate changes; new challengers cannot be accepted by the annual runner.

Simulator inherits corrected executable-fill equity 019B. Checkpoints require
both the corrected metric marker and the 028 strategy marker, rejecting legacy
state. Decisions use preceding completed H1 bars only. Controls' trades, decisions,
cash/cost metrics and curve times/paused states must match 008. Equity/drawdown
values may differ only from corrected marking and must be independently checked.
No tuning or strategy repair after inspecting returns within this declaration.

Report every scenario: net return, net dollars, trade count, expectancy, win rate,
corrected tick drawdown, exposure, gross before commission/financing, commissions,
financing, signal/abstention reasons and control/new entry identity differences.
Gross still includes spread/slippage. No independent-trial or continuous-return
claim. Independent accounting checks trade geometry/gross/fees/net/cash, original
control parity, and correct tick equity using source sequence lineage and its own
cash/financing/fill-mark calculation. No optimistic mark beyond a modeled exit.

Pre-return tests cover pure challenger decisions/causality, threshold/equality/
warmup/zero path, inherited position/sizing/spread/stop/daily-pause behavior,
duplicate/restart/legacy rejection and metric overshoot correction. Freeze after
tests before returns; run the full regression suite once after implementation.
Report all failures, sample sizes and adverse-cost sensitivity. A profitable
development cell is not a validated edge or authorization for demo orders.
