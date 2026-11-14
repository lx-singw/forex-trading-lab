# Private recorder109 — timing retest

The107 run produced116 valid snapshots and stopped at the60-second limit.
The109 recorder changes its wait timing while preserving account guards and
500ms minimum spacing,120-snapshot maximum and60-second stop.

On **12 October 2026**, keep **Algo Trading off**, with the existing USD demo
account connected and an EURUSD chart selected:

1. Refresh **Navigator → Scripts**.
2. Open **ForexDemoLab109-39828a784c0c → ForexDemoPrivateRecorder109**.
3. Set **RecordDiagnosticSnapshots = true**, click **OK**, then wait about a minute.

Every new script instance defaults to false; reopening its Inputs is not a status
check. Run once. The script still rejects other dates, real/contest accounts,
Algo-on/disconnected/tester contexts and changed identity. It has no order capability.
There is no need to save existing Experts logs or contact support.

A closed file appears in **MT5 → File → Open Data Folder → MQL5 → Files →
ForexDemoLab109**, named **Snapshot109-….txt**. The fixed **FXDL109** status line
uses the same reason codes as107:0 complete,1 collection off,13 elapsed stop,
14 file failure. [Full reason table](PRIVATE-RECORDER-107-USAGE.md).

The unchanged inspector accepts the shared107 export format:

```sh
PYTHONPATH=src python3 scripts/private-recorder-107.py /path/to/closed/Snapshot109-file.txt
```

The tighter wait polls its final25ms window, so it uses some CPU during this short
diagnostic. Windows scheduling or a blocked call can still cause a stop. A new run
creates a separate file; stopped files are never overwritten, resumed or relabelled.
Native timing improvement must be measured from this fresh export.

[Observed107 result](PRIVATE-RECORDER-108-RESULTS.md) has intact frames,52 repeats,
raw clock labels about3hours apart and80 equal bid/ask samples. Those limits remain.
No offset correction, execution-cost or profitability assumption has changed.
This is private read-only diagnostic work; market/paper/orders remain unavailable.
