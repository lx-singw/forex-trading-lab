# Context recorder136 future use

Latest — final136 capture inspected (31 October 2026 local).
The fifth closed run reached the four-hour elapsed cap (code13), with13,941
paired quote polls and four complete contexts. No disconnection stop or partial
tail was recorded. There were seven sampling gaps over2s (max5.975541s),9,183
adjacent repeats and an unchanged-quote span over two hours. This establishes
a bounded-duration collection milestone, not four hours of fresh market data.
Original/copy hashes, reader/CLI agreement, independent frame digests and all
five deployed build hashes were verified. Source UTC/freshness and full costs
remain unknown; no strategy returns or orders. The136 date window has expired;
do not restart it or extend its dates. Next: offline coverage/qualification
assessment and a session-aware collection design with frozen data boundaries.
October remains quarantined; November–December reserved/untouched.
Read [final capture results](../reports/context-recorder-136-collection-check-002/RESULTS.md). Earlier preparation/running notes below are historical.


Preparation is complete on24 October2026. **Do not launch collection today.**
The collector's own allowed nominal computer-GMT dates are26–30 October2026.
Do not edit dates, use old scripts, enable Algo Trading or switch accounts to
make a guard pass. No run or reminder is automatically scheduled.

During that new window, for one bounded diagnostic run:

1. Use the existing connected USD **demo** account, an EURUSD chart and visible
   EURUSD in Market Watch. Keep **Algo Trading off**. The script checks actual
   account type and rejects real/contest accounts regardless of server name.
2. Refresh MT5's Navigator → Scripts if needed. Open the new
   **ForexDemoLab136-e89505f1b720** folder and launch
   **ForexDemoContextRecorder136** once.
3. Set **CollectEvidence = true** for that launch and click OK. It only reads
   current metadata/cost/clock/session fields and latest EURUSD quotes. There
   are no orders or historical downloads.
4. Leave the terminal connected and computer awake while it runs, for at most
   four elapsed hours on returning calls. Disconnection, a guard failure,
   elapsed/date/byte limit or manual stop can end it earlier. A blocked native
   call is not forcibly interrupted. Do not launch a second copy as a retry.
5. When the script has ended, keep the closed original **Context136.txt** in
   MT5's Data Folder → MQL5 → Files → ForexDemoLab136 → its new Run136 folder.
   Do not alter, append or combine it with any other run. The generic Experts
   status reports reason/counts without account identifiers.

Scripts run once. Reopening their input dialog can show the default false
again; that does not prove the previous launch failed. Check the generic
status and the fresh owned run file. Code1 means collection was not enabled;
code11 means outside the nominal date window; code13 is the elapsed cap;
code3 indicates reported disconnection; code14 is storage failure; code0 is
normal maximum-count completion. Other guard/status codes are retained for
offline review. None is evidence of profitability or quote freshness.

Only inspect a **closed** export. After preserving it byte-for-byte in a new
canonical data folder, the offline reader can be run from the WSL repository:

```sh
python3 scripts/context-recorder-136.py /absolute/path/to/Context136.txt --format markdown
python3 scripts/context-recorder-136.py /absolute/path/to/Context136.txt --format json
```

The reader does not modify inputs, start MT5, calculate strategy returns or
place orders. Its actual136 header/date schema must remain unchanged; do not
convert it to an older export or135 invented fixture. Empty/failed fee results,
unknown clock offsets/delay and partial snapshots remain explicit unknowns.

The installed script has not yet had a native runtime/IO trial. Four-hour
collection is a diagnostic envelope, not a complete historical dataset or
201-hour warm-up. October remains quarantined and November–December stays
reserved and untouched.
