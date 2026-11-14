# Run the read-only timing diagnostic130

The tested script is compiled and deployed. It records up to 60 spaced
observations of EURUSD quotes and MT5 clock readings, in roughly one minute.
It has no order-placement capability. Collection defaults off. Its nominal
computer-GMT date must be **15 October 2026**. Do not edit the date or rerun an
old probe to bypass its expired envelope.

## One manual launch

1. Keep **Algo Trading off**, using the existing connected USD demo account.
   Keep the EURUSD chart open and EURUSD visible in Market Watch.
2. In **Navigator → Scripts**, right-click and choose **Refresh**.
3. Open **ForexDemoLab130-0b357a86f0e4 → ForexDemoTimingProbe130**.
4. In Inputs set **CollectEvidence=true**, then click **OK once**.
5. Leave MT5 connected for about one minute, then tell the assistant **Done**.

The assistant's available tools cannot operate the native MT5 interface, so
this launch requires your click. No support contact, account change, log-saving
step or trading permission is needed. A new settings dialog can show the
default false again; that does not establish whether the preceding run finished.
Avoid repeated launches.

Each poll reads clock-before, latest quote, then clock-after. These are separate
guarded reads, not an atomic snapshot. The actual DEMO account enum, stable
private identity, USD account, connection, non-tester, Algo Trading off and
already-visible EUR/USD symbol checks repeat around diagnostic groups and
during waits. Private login/server values stay in memory and are never exported.

## Export and interpretation

The owned terminal-local export is:

MQL5/Files/ForexDemoLab130/Run130-…/Timing130.txt

After completion, the assistant will copy only this probe's closed bounded file
and inspect it read-only. The offline inspector can also be run as:

python3 scripts/timing-probe-130.py /absolute/path/to/closed/Timing130.txt

The reader preserves raw native quote bits, source seconds/milliseconds, unknown
flags, six raw clock values and before/after/guard receipt markers. It reports
source-label advances/reversals, identical adjacent snapshots, observed repeat
spans, clock changes and paired arithmetic for fully completed polls. An
unfinished poll's recorded quote remains visible but is not counted as a
completed pair. Source age remains unknown.

[TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent) refers to the
last quote received for a selected Market Watch symbol and need not be EURUSD.
[TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver) is a
client-calculated server-time estimate affected by computer settings.
[TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt) is calculated using
the computer's local time and daylight-saving settings. Neither those clock
differences nor a repeated quote certify UTC, executable freshness, quote age,
complete tick delivery or a historical timezone rule.

## Bounds and stops

At most 60 polls/180 diagnostic groups, one file, 128 KiB, and 60 elapsed seconds
checked when operations return. Extra guard/time checks are outside the 180
diagnostic groups. Clock groups each contain six getters. Actual first-clock
read starts are at least one second apart. Guarded 50ms waits do not catch up
after a delay. Native calls, Sleep and IO cannot be forcibly interrupted by
these return-time checks; fewer than 60 completed polls may result.

An attempt frame is flushed before each diagnostic group. A failed after-read
guard discards that group's queried values. Existing run folders/files are
refused; there is no restart resume, append-to-old-run or automatic retry.
Digest-linked frames detect accidental changes but do not authenticate the
producer. Stopped/partial files remain stopped/partial.

Generic FXDL130 reason codes: 0 normal completion; 1 collection off; 2 query
guard failure; 3 disconnected; 4 tester; 5 non-demo; 6 non-USD; 7 Algo Trading on;
8 invalid private identity; 9 identity change; 10 symbol guard; 11 date expiry;
12 clock/error; 13 elapsed cap; 14 storage; 15 quote query; 16 invalid quote;
17 self-test; 18 stopped; 19 poll spacing/state; 20 diagnostic count cap.

Read [preparation results](TIMING-PROBE-130-RESULTS.md) and
[the reserved plan](TIMING-PROBE-130-PLAN.md). Orders remain unavailable.
