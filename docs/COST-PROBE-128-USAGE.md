# Run the read-only cost probe128

The tested component is compiled and deployed. It reads current reported
commission rules and buy/sell margin factors from your existing demo terminal.
It cannot submit orders. Collection defaults off. Its nominal computer-GMT date
must be **14 October 2026**; do not rerun it on a later day or edit its date limit.

## One manual launch

1. Keep **Algo Trading off**, using the existing connected USD demo account.
   Keep the EURUSD chart open and EURUSD visible in Market Watch.
2. In **Navigator → Scripts**, right-click and choose **Refresh**.
3. Open **ForexDemoLab128-27eeb9d91d0a → ForexDemoCostProbe128**.
4. Set **CollectEvidence=true** in Inputs, then click **OK once**.
5. Let the script finish and tell the assistant **Done**.

The assistant's tools cannot operate the native MT5 interface, so your click is
needed. No support contact, permission to trade, account change or log-saving
step is required. Reopening a new dialog may show the default false; this does
not establish whether the preceding run completed. Avoid repeated launches.

The native program checks the actual DEMO account type, connected USD account,
stable private identity, Algo Trading off, non-tester and visible EUR/USD symbol
around each query. Identity never enters the export. It stops on guard, clock,
storage, numeric/currency-validation or rule/tier-bound failure.

## Export and inspection

The single export is terminal-local:

MQL5/Files/ForexDemoLab128/Run128-…/Costs128.txt

File → Open Data Folder in MT5 opens the containing MQL5 location. The assistant
will preserve only this probe's closed owned export and inspect it read-only.
The offline CLI is:

python3 scripts/cost-probe-128.py /absolute/path/to/closed/Costs128.txt

An FXDL128 status line uses generic reason codes: 0 normal completion, 1 default
collection off, 21 excess rule count, 22 excess tier count; other codes cover
guard, clock, storage and invalid-value failures. No arbitrary strings or
identifiers are printed. A stopped or partial export remains incomplete.

## Bounds and interpretation

At most five diagnostic API queries are attempted: clock-before, commissions,
buy margin factors, sell margin factors and clock-after. Accepted output allows
eight rules, 16 tiers per rule, 128 total tiers, 64 KiB and a 60-second elapsed
limit checked when operations return. Native calls may allocate arrays or block
before validation; this is not a hard native allocation/time interruption bound.

Rule currencies, conditions, units, tier values, minimums, maximums and ranges
remain raw. Negative commission values are preserved; unknown enum values are
not assigned new semantics. Empty currency fields stay empty/unknown. Margin
factors are not dollar margin requirements. There is no fee conversion or
financial simulation in this diagnostic.

The inspector distinguishes incomplete rule payloads, failed queries,
successfully reported empty rule lists and successfully reported rules. None
establishes zero trading costs, historical costs, slippage, authenticated
producer identity or approved paper/trading data. Raw clock groups receive no
timezone adjustment.

Read [preparation results](COST-PROBE-128-RESULTS.md) and
[the reserved plan](COST-PROBE-128-PLAN.md). All automated orders remain off.
