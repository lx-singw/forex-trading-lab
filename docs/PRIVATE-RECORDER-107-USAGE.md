# Private recorder107 — launch and inspect

This is a private demo snapshot diagnostic. It cannot place orders. No support
contact or new broker account is needed for this engineering step.

## Run once on 12 October 2026

1. Leave MT5 **Algo Trading off**, connected to your existing USD demo account.
   Select the **EURUSD** chart; EURUSD must already be visible in Market Watch.
2. In **Navigator → Scripts**, right-click **Scripts → Refresh**. Expand
   **ForexDemoLab107-dd8f1187759b** and open **ForexDemoPrivateRecorder107**.
3. In **Inputs**, set **RecordDiagnosticSnapshots = true**, then click **OK**.
   Allow about one minute for the script to finish. Do not enable Algo Trading.

Collection defaults to false for every new script instance. Opening the script
again may show false; that does not tell us whether the previous run succeeded.
Each run creates a separate file, so do not relaunch merely to check the setting.
This is a fresh date-bound diagnostic for computer-GMT date 2026.10.12. A later
date is rejected. Old observer/pipe scripts do not need to be run.

The actual account type is checked by the script, independently of the account
name shown in the window. Real, contest, disconnected, tester, Algo-on or changed
account contexts are rejected. No terminal settings are changed by this script.

## Find the result

Use **MT5 → File → Open Data Folder**, then
**MQL5 → Files → ForexDemoLab107**. A run that passes startup checks writes a
**Snapshot107-….txt** file. Wait until the script finishes before inspecting it.
The file contains no account number, server name or credentials.

The fixed **FXDL107** status line in MT5's Experts tab gives a reason code and
counts. No need to open/save the existing Experts log for this test.

| Code | Meaning |
|---|---|
| 0 | All 120 snapshots completed; offline inspection still required |
| 1 | Input false: collection did not run |
| 2–4 | Property query, connection or tester guard failed |
| 5 | Actual account is not DEMO |
| 6–10 | Currency, Algo Trading, identity or EURUSD context failed |
| 11–13 | Date, clock ordering/drift or elapsed budget failed |
| 14 | File/checksum/write/flush operation failed |
| 15–16 | Quote read failed or returned invalid values |
| 17 | Runtime SHA256/native-double self-check failed |
| 18 | Script was stopped |

A failed after-read guard discards that quote. A pending attempt or missing footer
remains visible after interruption. Restart never resumes or overwrites the old
file. A new run is a separate segment.

## Inspect a closed export

From this repository in WSL:

```sh
PYTHONPATH=src python3 scripts/private-recorder-107.py /path/to/closed/Snapshot107-file.txt
```

The CLI only reads the supplied file. It reports counts, hash-chain validity,
completion/stop state, repeated snapshots, changed payloads at equal source times,
source-label reversals and receipt gaps. It omits quote prices from its printed
summary. Invalid/unreadable files return a fixed error without printing private
paths or arbitrary exceptions.

A complete export proves only consistency with this format. Hashes do not prove
who produced it or that the current account/clock was trustworthy. Computer-GMT
receipt seconds and raw broker source labels remain unverified; no offset is
guessed. Repeated snapshots are retained, and source age is unknown. Latest-value
polling does not deliver every market tick.

The inspector never grants market-data qualification, paper evaluation, orders or
real-money execution. This diagnostic is preparation for forward testing; it does
not repair historical gaps or establish profitability.
