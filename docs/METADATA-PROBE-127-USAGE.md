# Run the read-only metadata probe127

The probe is compiled and deployed, with collection off by default. It can read
current EURUSD metadata and clocks from your existing demo terminal. It cannot
place orders. Its nominal computer-GMT date is **14 October 2026**; a different
date stops collection. Do not alter that limit or launch it on a later day.

## One manual MT5 launch

1. Keep **Algo Trading off**, and use the existing connected USD demo account.
   Open the EURUSD chart and leave EURUSD visible in Market Watch.
2. In **Navigator → Scripts**, right-click and choose **Refresh**.
3. Expand **ForexDemoLab127-1252773ffdf0** and launch
   **ForexDemoMetadataProbe127**.
4. In **Inputs**, set **CollectEvidence = true** and click **OK once**.
5. Let it finish, then tell the assistant **Done**.

The native MT5 interface is unavailable to the assistant's tools, so this launch
needs your click. No permission to trade, support contact, account creation or
Experts-log saving is required.

Reopening a new launch dialog may show the default **false** again. That alone
does not show whether the preceding run completed. Avoid repeated launches.
The run is limited to 128 diagnostic queries and 64 KiB of output. It checks its
60-second elapsed limit when calls return; it cannot interrupt a blocked native
or file operation.

## Output and inspection

A successful file open creates one terminal-local export under:

MQL5/Files/ForexDemoLab127/Run127-…/Metadata127.txt

MT5's **File → Open Data Folder** leads to that MQL5 directory. The script prints
a generic **FXDL127** status in Experts: reason 0 means normal completion;
reason 1 means collection was left off. A stopped or incomplete export is
retained as such. Account identifiers, server strings and credentials are never
exported. Do not send account details or arbitrary terminal logs.

The assistant will copy only this probe's closed export, retain its original
bytes and hash, and inspect it read-only. The offline CLI is:

python3 scripts/metadata-probe-127.py /absolute/path/to/closed/Metadata127.txt

It never initializes MT5 or connects to a broker. Parsing a valid hash chain
does not authenticate the producer or approve the data for trading.

## What this can establish

It preserves current reported contract, volume, margin, leverage and swap
properties; query success/error; a bounded weekly trade-session template; two
latest quotes; and raw terminal/computer clocks with read boundaries. Failed
properties remain unknown. Swap mode and values remain raw and unconverted.

Current specifications do not establish historical costs. Weekly session times
do not certify a historical calendar. Commission, slippage, source UTC, receipt
UTC, quote age and the earlier source-clock mismatch remain unresolved unless
further evidence resolves them. No guessed timezone correction is applied.
Metadata capture does not qualify strategy performance, paper evaluation or
demo execution.

Read [preparation results](METADATA-PROBE-127-RESULTS.md) and the
[reserved plan](METADATA-PROBE-127-PLAN.md). All automated orders remain off.
