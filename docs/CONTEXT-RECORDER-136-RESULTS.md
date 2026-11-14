# Context recorder136 preparation results

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


Completed 24 October2026. The separate default-off read-only EURUSD collector
is implemented, tested, compiled and installed in its own Scripts folder.
**It has not been run.** Its new nominal computer-GMT window is26–30 October;
today is outside that window. No earlier dated program or data was renewed.

The collector combines raw per-run context and paired quotes in one new136
wire format. It captures33 current metadata properties, bounded weekly session
queries, commission rules/tiers, buy/sell margin factors and before/after raw
clocks before polling, then repeats context after every3,600 completed polls.
These are sequential observations from one guarded run, not an atomic account
contract, producer authentication or a promise of future terms.

Each quote poll records clock-before/latest-quote/clock-after. Limits are
14,400 polls, four context blocks,43,604 queries, one fresh file/32MiB and at
most four elapsed hours checked when calls return. Actual first-clock starts
are at least one second apart, with50ms guarded waits and no catch-up.
Blocked API/IO calls are not forcibly interrupted; runs can stop early and
can contain a pending attempt, context/rule payload or unfinished final pair.
The context refresh interval is a poll count, not a guaranteed wall-clock hour.

Actual account enum DEMO, identity continuity, connection, USD, non-tester,
Algo Trading off and visible EUR/USD checks reuse unchanged107 predicates.
They run before and after native reads and during waits/commission serialization.
After-read failure discards queried values. Identity stays in memory; wire and
status contain no login, server or credentials. Real/contest account names
cannot bypass the actual-type guard. There is no order, history, SDK, DLL,
network, settings or symbol-selection capability.

Storage uses a new owned run folder and fresh file, digest-linked bounded
frames, attempt-before-query records and explicit context boundaries. It
refuses collisions and append/resume, reserves bytes before IO and never
refunds/retries failed storage. Storage failure closes without another write.
The reader preserves raw numeric bits, flags, query failures, empty commission
rules, partial rule payloads, changing context, repeats and sampling gaps.
Incomplete context/pair status is explicit; a valid prefix is not promoted to
full completion.

Unknown source offset, receipt UTC uncertainty, quote age, post-marker delivery
delay, executable freshness, complete costs and holiday calendar remain unknown.
Reported empty commissions or zero margin fields do not establish zero costs.
The136 reader does not rewrite bytes into127/128/132 or135 formats, import a
hypothetical cost model, apply clock corrections or qualify strategy input.

**101 Python tests passed**, including15 new136 tests plus the unchanged135
contract and127/128/132 readers. They cover full-count/context refresh, raw
values and changed properties, dates/midnight boundaries, every small prefix,
pending outcomes/tiers, empty/failed fees, maximum rules/tiers, gaps/repeats/
reversals, invalid rehashed wire, malformed framing, premature completion and
read-only/sanitized CLI behavior. Native scope/guard/read/IO ordering is also
checked by source inspection. Actual native filesystem failure behavior has
not yet been exercised.

The exact shared pure state/account code compiles as C++17 with Wall/Wextra/
Werror and passes **490,030 checks**:14,400 ideal polls, four maximal contexts,
all43,604 queries,120 selected before/after guard-fault paths, date/elapsed/
spacing/query/byte bounds, pending/ended state and no failed-write refund.
These are pure invented checks with zero native calls, not an MT5 runtime test.
Financial/risk/cost/weight implementations stay unchanged; their earlier
financial verification is retained rather than newly claimed here.

The frozen maximum invented file is13,184,940 bytes and87,762 physical frames:
43,604 attempts/outcomes,14,400 complete quote pairs, four contexts,32 commission
rules and512 tiers. CLI JSON/Markdown match the library; repeated JSON is
identical. A separate original-frame walk verifies all checksums, frame/tag
counts, outcome receipt markers, quote bits, context boundaries and reported
property changes. This proves local format consistency, not producer identity
or market performance. [Reader proof](../reports/context-recorder-136-application.json),
[reference review](../reports/context-recorder-136-reference-review.json),
[Python tests](../reports/context-recorder-136-tests-001.json),
[C++ checks](../reports/context-recorder-136-CXX-tests-001.json).

The installed MetaEditor5.0.0.6283 compiled the frozen four-file dependency set
in an isolated owned Windows build folder. Diagnostics show **zero errors and
zero warnings**, producing a37,794-byte EX5. Its exit code1, compiler/source/
artifact hashes and raw diagnostics are retained; success is based on the
diagnostics and matching artifact, not exit code alone. This compiler differs
from the earlier6259 build and has its own recorded hash.
[Compilation](../reports/context-recorder-136-compilation-001.json).

Five exact files were installed without overwrite in
**ForexDemoLab136-e89505f1b720**. All deployed hashes were rechecked; the earlier
owned132 files are unchanged. No terminal launch, script execution or settings
change occurred. [Deployment](../reports/context-recorder-136-deployment.json),
[recheck](../reports/context-recorder-136-deployed-recheck.json).

All627 older source/config/test and68 native input hashes remain unchanged.
Seven new source/config/test files make634. Full prior handoff bodies and
source/evidence are preserved. There was no SDK connection, contact, account/
service creation, actual order, strategy/P&L/selection or reserved-data replay.
October stays quarantined; November–December reserved/untouched;2025 consumed;
closed routes stay closed. Market/paper/order/real-money admission stays false.

Next is one bounded manual observation during the new26–30 October window,
then preservation and inspection of its closed owned export. See
[future-use instructions](CONTEXT-RECORDER-136-USAGE.md). No collection is
scheduled, and no MT5 action is needed today. Even a successful four-hour run
would not provide201-hour strategy warm-up or resolve all clock/cost gaps.
