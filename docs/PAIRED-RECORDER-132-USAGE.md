# Run the one-hour read-only paired recorder132

The tested script is compiled and deployed. It records EURUSD bid/ask quotes,
source labels, computer receipt markers and clock-before/clock-after groups.
It has no order-placement interface and collection defaults off.

**Run once during19–23 October2026, starting Monday19 October. Do not start it
on18 October.** The program checks MT5's reported computer-GMT date at entry
and throughout the run. Use a daytime hour in South Africa to avoid a midnight
boundary. These dates bound this experiment; they do not certify market hours
or UTC. Do not edit old scripts or this window to bypass a rejection.

## One manual launch during the allowed window

1. Keep **Algo Trading off** on the existing connected **USD demo account**.
   Keep an EURUSD chart open and EURUSD visible in Market Watch.
2. In **Navigator → Scripts**, right-click and choose **Refresh**.
3. Open **ForexDemoLab132-deddc9e4e31b → ForexDemoPairedRecorder132**.
4. In Inputs set **CollectEvidence=true**, then click **OK once**.
5. Leave MT5 open, connected and the computer awake for about one hour.
   Keep Algo Trading off. When the run finishes, tell the assistant **Done**.

No log-saving step, account change, trading permission or support contact is
needed. A later new Inputs dialog may show the default false again; it does
not establish whether the earlier run completed. Avoid repeated launches.
Preparation did not start MT5 or the recorder; the future launch is manual.

The program checks the actual DEMO account enum, connected/non-tester state,
USD currency, stable private identity, Algo Trading off and already-visible
EUR/USD symbol before/after each diagnostic group and during guarded waits.
Private login/server values stay in memory and never enter output. A failed
after-read guard discards that group's queried values.

## Bounds and stopping

Up to3,600 polls /10,800 diagnostic groups, at least one second between actual
first-clock read starts, a one-hour elapsed cap checked when calls return,
one file and8MiB. Each poll sequentially reads six clocks, one latest quote,
then six clocks. Extra account/time guards are outside the diagnostic-group
count. Guarded50ms waits do not catch up after delays. Native calls, sleep and
IO cannot be forcibly interrupted by the return-time checks.

Fewer than3,600 polls can result from normal elapsed-limit code13. That is a
valid stopped prefix if its framing and guards validate, with any unfinished
pair reported separately. A stop frame does not carry its own receipt marker.
Stopping/removing the script or closing MT5 can leave an incomplete prefix or
partial tail; the reader preserves valid prior records and reports the tail.

Attempts are flushed before queries. Pending/outcome sequencing, byte
reservation and ended-state rules prevent continuing an interrupted run.
Existing folders/files are refused; there is no resume or append-to-old-run.
On storage failure the program closes without another write attempt, so a
stop frame may be absent. No automatic retry follows a fault.

## Owned export and offline quality report

MQL5/Files/ForexDemoLab132/Run132-…/Paired132.txt

After the run, the assistant will preserve only the closed bounded owned
export and inspect its exact bytes. The offline commands are:

```sh
python3 scripts/paired-recorder-132.py /absolute/path/to/closed/Paired132.txt
python3 scripts/paired-recorder-132.py /absolute/path/to/closed/Paired132.txt --format markdown
```

The new132 wire reader retains raw dates, clock fields, native quote bits and
unknown flags. It does not rewrite the file into an old130 envelope. The shared
131 numerical quality engine computes repeats, source-label reversals,
sampling gaps and paired arithmetic from compatible validated fields; every
result is explicitly labeled132. Rendered reports show invented_fixture or
market_declared provenance. Hashes and declarations do not authenticate the
producer. The fixed two-second sampling-gap notice and128-event detail cap
remain unchanged; all events still contribute to counters.

Raw source/server/computer clock differences and observed repeat spans do not
certify quote age, UTC, executable freshness, complete tick delivery or
historical timezone rules. No timezone offset is applied. A valid wire prefix
does not establish market-data admission, costs or profitability. All paper/
order/real-money availability remains false.

Generic FXDL132 codes:0 complete;1 collection off;2 query guard;3 disconnected;
4 tester;5 non-demo;6 non-USD;7 Algo Trading on;8 invalid private identity;
9 identity changed;10 symbol guard;11 date outside window;12 clock/error;
13 elapsed cap;14 storage;15 quote query;16 invalid quote;17 self-test;
18 stopped;19 state/spacing;20 diagnostic count. No identifiers are printed.

Read [preparation results](PAIRED-RECORDER-132-RESULTS.md) and
[the reserved plan](PAIRED-RECORDER-132-PLAN.md). No collection has run yet.
