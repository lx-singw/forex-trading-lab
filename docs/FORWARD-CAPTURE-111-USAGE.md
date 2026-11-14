# Forward capture111 — launch and inspect

This private demo collector records for **up to one hour**, at least500ms between
reads, at most7,200 attempts,64 segments and4MiB total output. It cannot place orders.
The limits span every segment. A time-limit stop (code13) is expected if fewer than
7,200 attempts fit; it does not fabricate or speed up the missing samples.

## Launch once on12 October2026

1. Keep **Algo Trading off**, with your existing USD demo account connected.
   Select the **EURUSD** chart and leave EURUSD visible in Market Watch.
2. Refresh **Navigator → Scripts**. Open
   **ForexDemoLab111-9a123fec6e56 → ForexDemoForwardCapture111**.
3. Set **CollectOneHour = true**, click **OK**, and leave MT5 open and the computer
   awake for about one hour. The collector stops automatically at its limits.

Each new instance defaults to false. Reopening Inputs does not indicate whether a
prior run completed. Start once; there is no need to save or open existing Experts
logs. Native date policy is nominal computer-GMT2026.10.12. A later date rejects.

Real/contest accounts, Algo-on, disconnection, tester contexts and changed private
identity are rejected. No account number/server/credentials are exported.
You can stop the script sooner; the earlier data and any pending attempt stay
visible. A restart always creates a new run rather than resuming the old files.

## Output and status

Use **MT5 → File → Open Data Folder → MQL5 → Files → ForexDemoLab111**.
Each launch that passes startup checks creates its own **Run111-…** folder, with
**Segment111-001.txt**, **Segment111-002.txt**, etc. Closed segments contain
120 valid observations, except the last segment when the run stops earlier.
Hash linkage, sequence, clock ordering and caps continue across segment boundaries.

The fixed **FXDL111** status line reports reason/counts when stopped.
0 means7,200 complete;1 means collection remained off;13 means elapsed cap;
14 means storage/write failure;18 means user/script stop. Codes2–12 and15–17 retain
the [107 meanings](PRIVATE-RECORDER-107-USAGE.md).19 is an invalid state transition,
20 an attempt/segment cap. Files can remain incomplete when a write or process
ends abruptly. Flush/checksums are not power-loss durability or producer proof.

## Inspect a closed run

From this repository in WSL:

```sh
PYTHONPATH=src python3 scripts/forward-capture-111.py /path/to/closed/Run111-folder
```

The CLI reads only, checks all sequential segment files, and prints counts/state/
hashes/repeats/gaps/reversals. It omits quote prices from its summary and does not
connect to MT5. It rejects missing/reordered/mixed/tampered files and improper
completion. A partial final frame/header and pending attempt remain incomplete.
Inspect a stopped run or a copied closed snapshot, not a changing live directory.

Raw source timestamps and computer-GMT receipt labels remain unverified. Repeated
latest snapshots do not represent all ticks; source age and executable freshness
are unknown. No three-hour correction, execution-cost assumption or profit claim
is introduced. Market/paper/order admission and real-money execution stay false.
No external support/contact or paid service is needed for this engineering pilot.
