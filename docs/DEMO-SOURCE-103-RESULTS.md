# Demo source103 — qualification contract prepared; connection blocked

Prepared the concrete read-only demo-source contract in
[DEMO-SOURCE-103-CONTRACT.md](DEMO-SOURCE-103-CONTRACT.md) and
[config/demo-source-103.json](../config/demo-source-103.json).
The existing MT5 demo feed remains a conditional candidate for forward snapshots.
No feed is qualified for connection, paper evaluation or execution by this result.

## Findings that affect the implementation

The official [initialize documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py)
says the SDK can launch a terminal when needed and use stored account settings.
An explicit terminal path is not an attach-only guarantee. A process check before
initialization can race with exit; the old031 precheck therefore does not establish
a general guarantee that initialization cannot launch. This is a documented
capability and design inference, not a claim that an old run actually relaunched.
The proposed attach-only SDK entry remains blocked. No new initialization ran.

[symbol_info_tick](https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfotick_py)
provides the latest tick, so polls can repeat snapshots and miss intervening
updates. [MqlTick](https://www.mql5.com/en/docs/constants/structures/mqltick)
lists no broker event sequence; its populated fields need not all have changed.
Local observation numbers and equal payloads cannot prove unique provider events,
complete delivery or fresh executable prices on both sides. The contract retains
each attempted poll, repeated snapshots and distinct equal-time updates honestly.

The generic [history API](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py)
documents UTC conventions. It does not resolve the saved031/037 roughly-three-hour
clock disagreement. Raw source labels stay raw; no assumed offset is applied.
Recovered history, if separately permitted later, would become available at its
later receipt time and could not be replayed as known at the original tick time.

[account_info](https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py)
exposes current properties including private identity, while the
[account enumeration](https://www.mql5.com/en/docs/constants/environment_state/accountinformation)
distinguishes demo, contest and real. The contract requires exact actual DEMO
checks around reads, private identity comparison and allowlisted outputs, with
no whole-account dump. A server name or trading-permission flag is insufficient.
No present account was queried or inferred from an old screenshot.

## Qualification disposition

The contract defines 13 admission gates, separate diagnostic/snapshot/tick-path
evaluation requirements, read-boundary UTC/monotonic receipt fields, source-clock
uncertainty, per-session restart semantics, fixed diagnostics, durable bounded
storage and point-in-time availability. Every gate remains unsatisfied; the
contract has no runtime consumer or activation authority. Requirements are not
evidence that they have passed.

Permitted automated feed use, side-effect-free attachment, feasible runtime
provenance/cleanup, current account/clock evidence and a separate market journal
remain missing.102 proves bounded invented journal behavior only. Native090 is
closed, dated031 is expired, and the generic API documentation does not repair
the old033/035 full-record repeatability failure or unknown flag bits.

## Verification and scope

Six predeclared official documentation pages were opened successfully, once each,
with six sealed reservation/outcome pairs. Zero searches, finds, linked opens,
screenshots, retries, raw feeds, dataset/archive/API acquisition, provider contact,
accounts or payments. Only narrow paraphrases are saved; incidental example
prices, identity and credential values were ignored. No private/native/terminal
state or new market rows were inspected.

Verified the102 closure:44 bindings,43 archive members,504 retained source hashes,
and its retained101 archive. Independent checks validate the contract references,
dependency graph, false admission states, documented outcomes, budget and exact
preservation of the predecessor/four handoff contents. All504 previous sources
and all frozen102 evidence remain unchanged apart from the four handoffs whose
prior bytes are preserved. One new configuration contract is hash-bound.

The2,044 passing active102 tests are retained, not rerun: this stage adds no
collector implementation or tests. No MT5/SDK connection, native call, compiler,
deployment, log/UI action, strategy replay, returns or order occurred. H.10 remains
closed under present evidence. Existing costs/rules, historical gates, old stops
and failures,2025 exclusion,November–December2026 reservation and October quarantine
remain. Automated orders are off; real-money execution is unavailable.

The next useful implementation is the broker-free collector boundary described
in the contract, using invented account/quote/clock facts and a separate honest
schema. Its real broker entry stays disabled. This tests adapter failure and
chronology behavior while a permitted feasible attachment route and source-specific
evidence remain necessary for connection. No replacement external search or new
native experiment is declared by this closure.
