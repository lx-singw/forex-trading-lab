# Source decision105 — no current collection route admitted

Review completed on the client date 2026-10-12. The recorder104 remains
invented-only. This review admits no broker connection, market collection, paper
evaluation or orders. The useful result is a route decision, not more model code.

## Route decision

| Route | Disposition | Reason |
| --- | --- | --- |
| Python SDK with an attach-only requirement | Reject under the current requirement | The documented initialization can launch a terminal and use stored account state. An earlier process check can race; no attach-only switch has been established. |
| Closed native090 pipe/bridge | Keep closed | Its frozen source-proof contract is infeasible. No cap, date, proof or authority is renewed. |
| Terminal-owned local file exporter | Design candidate only | MQL supports terminal-local files. A self-contained program could avoid Python initialization and the old pipe/DLL architecture. No such exporter has been implemented, compiled, deployed or proved here. |

The Python conclusion retains the103 evidence from the official
[initialize documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py);
that page was not requested again. It does not mean every initialization launches
a terminal, or that an old run did so. It means the current no-launch requirement
is not established by that API.

[FileOpen](https://www.mql5.com/en/docs/files/fileopen) documents a terminal file
sandbox and a separate shared-terminal location. A proposed exporter would use a
new terminal-local output folder, without shared files, DLLs, named pipes, login,
symbol selection or Python initialization. This is a design inference. Files
would still need ownership, collision, encoding, incomplete-write, restart,
privacy and cleanup checks; documentation does not prove bounded IO or crash
durability. The old090 sources and authority cannot be renamed into this route.
Any distinct design needs its own dependency/provenance and feasibility review.

## Permission finding

The official [Getting Started help](https://www.metatrader5.com/en/terminal/help/startworking)
describes demo accounts as supporting training and strategy testing. The bounded
search found application purchase/rental documentation and programming manuals,
rather than applicable feed retention terms. No source-specific permission for
automated capture, private local storage and research was obtained.

That is an unmet source-use gate in
[the103 contract](DEMO-SOURCE-103-CONTRACT.md), not a finding that recording is
illegal or forbidden. A platform help page is not proof of the supplier, agreement
or redistribution rights for this particular feed. We did not inspect an account,
accepted terminal agreement or private provider state. Additional results returned
automatically beyond the considered search subset were ignored. No general claim
that relevant terms are absent or unobtainable follows from this search.

The finite next evidence task is to identify the applicable existing-feed terms,
including the official legal-information lead visible on the help page, or obtain
written scope clarification. No legal link was followed in this frozen review.
No provider contact has been sent or authorized.

A ready-to-use clarification request is below. It contains no account identity
and is **unsent**:

> Does the agreement for the existing demo EUR/USD feed permit an automated,
> read-only diagnostic capture of at most120 latest bid/ask snapshots over
> at most60 seconds, stored locally for private algorithm research? Please identify
> the applicable terms, any retention/export restrictions and whether this also
> permits future longer paper-testing captures. No quotes would be redistributed,
> published, sold or used for automated order placement in this proposed capture.
> Separately, is there dated documentation for the tick timestamp timezone,
> daylight-saving rules and revisions, and are the quotes indicative or executable?

A response must cover the actual source and intended use; a different product's
license cannot pass the gate. The numeric capture limits above are a proposed
request scope, not a runtime grant or a new acquisition plan. A bounded grant
would not automatically cover longer recording or redistribution.

## Clock finding

[TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent) is server-derived
last-quote time. Outside OnTick it can refer to another selected Market Watch
symbol. It is unsuitable as an independent EUR/USD UTC receipt clock.

[TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver) is calculated
in the client and depends on computer time settings.
[TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt) derives GMT from the
computer's local clock and daylight-saving handling. Their agreement does not
establish an independent UTC reference. Tester clock values are simulated, so
tester agreement cannot certify a running feed.

These definitions do not resolve the saved031/037 approximately-three-hour
disagreement or prove its cause. Keep raw source seconds/milliseconds without
subtracting a guessed offset. Receipt clock provenance, uncertainty and clock-jump
detection need fresh evidence. Dated source-specific timezone/DST evidence remains
necessary before source-age or paper admission. Monotonic duration can measure
elapsed intervals within a qualified segment; it cannot certify UTC. A later
file import has a later import receipt and cannot be backdated as an earlier
strategy-visible journal commit.

## What happens next

Obtain applicable source-use evidence first. If it supports the intended scope,
review the distinct terminal-owned exporter and an explicit bounded runtime plan.
That plan must meet current actual DEMO checks around reads, private identity
continuity, connected/Algo-off/symbol guards, receipt clocks, feasible provenance,
cleanup and honest storage. Source-clock uncertainty may remain quarantined in
diagnostics only as allowed by103; it cannot become paper evidence by relabeling.

No additional invented collector or strategy tuning is needed to decide these
external gates. If permission cannot be established, keep this feed unqualified
and assess a different explicitly permitted source under a separate plan. Fresh
snapshots cannot repair the old historical gaps or full-record repeatability failure.

## Verification and preserved scope

Two exact searches, five successful documentation opens and seven sealed
action/outcome pairs; five search results considered, never more than the first
three per query. No finds, linked follow-ups, screenshots, retries, feeds,
downloads, API/archive acquisition, provider contact, accounts, payment or
terminal action. Narrow paraphrases only; incidental example values ignored.

Before research verified104's59 source/evidence bindings and57 archive members,
its completion review and all508 retained source hashes. This stage changes
documentation/reports and the four handoff introductions only. Prior handoff
bytes are retained. Independent closure checks verify bindings, archive,
action budget and unchanged source hashes. The2,095 passing active104 tests are
retained, not rerun; there is no implementation change to test.

All13 source103 gates remain unpromoted. H.10 and native090 stay closed under
present evidence; provider stops, old failures, costs, fixed rules, consumed2025,
reserved November–December2026 and quarantined October remain. No actual
SDK/native/MT5/compiler/deployment/log/settings/UI work, market rows, strategy
replays, new returns or orders. Real-money execution remains unavailable.
No replacement search or runtime experiment is declared by this closure.
Local evidence hashes check byte consistency, not source authenticity or license.
