# Demo source103 — read-only qualification contract

The existing MT5 demo feed is a conditional candidate for forward quote snapshots.
It is **not qualified for connection or paper evaluation**. This contract is a
requirements document; no runtime reads it as an activation switch. The invented
102 recorder and all legacy dated/native admission rules remain unchanged.
The machine-readable counterpart is `config/demo-source-103.json`.

## Candidate and admission gates

| Gate | Required evidence | Present disposition |
| --- | --- | --- |
| Permitted source use | Applicable permission for local automated collection, retention and research; public redistribution evaluated separately | Unverified; API documentation is not a feed license |
| Attachment without side effects | A demonstrably permitted mechanism that cannot launch a terminal, select/login to an account, change settings or enable trading | Blocked for the proposed SDK attach-only claim |
| Runtime feasibility and provenance | Separately scoped source/build/runtime evidence and bounded cleanup/deadline behavior | Unverified; native090 closed and expired probes cannot be reused |
| Actual demo account | Exact DEMO enum and stable private identity checked before/after each read and at completion; reject real, contest, unknown and boolean modes | General API documented; no current runtime proof |
| Terminal/instrument | Connected, Algo Trading off, exact already-visible EURUSD, EUR/USD contract currencies and USD account | Previously observed in031; current state unverified |
| Receipt clocks | Read-boundary UTC and monotonic measurements, independent wall-clock quality, reversal/jump handling and session boundaries | Old037 evidence is limited and dated; current clock unverified |
| Source clock | Preserve raw seconds/milliseconds; identify actual time basis and uncertainty with source-specific evidence | Unresolved; old observations disagree with generic UTC documentation |
| Observation identity | Locally unique committed observation sequence; honest snapshot repetition and source-identity limits | Design defined; no new implementation/runtime proof |
| Durable recording | Atomic append, restart, corruption, interruption, disk/lock failure and bounded output behavior |102 passes invented tests; market schema/adapter not implemented |
| Data quality and coverage | Frozen diagnostics, staleness rules, gap/disconnect accounting and known sampling limitations | Unverified for a fresh feed; polling cannot prove every tick |
| Point-in-time evaluation | Decisions see only already received and committed observations; late history stays late | Design required; no forward replay performed |
| Fixed research protocol | Costs, sampling-compatible strategies, frozen development/untouched validation roles and independent checks | Subsequent work; no strategy tuning or selection here |

Connection for a bounded **diagnostic** capture would require permitted use,
safe attachment, runtime feasibility/provenance, actual demo/terminal guards,
tested storage and a declared clock/date/budget envelope. Such records would stay
quarantined if source UTC/age or other research gates were unresolved. Diagnostic
capture is also disabled in103; it cannot be authorized by changing this JSON.

Paper snapshot evaluation additionally requires qualified clock/availability,
quality, costs and sampling-compatible fixed rules. Tick-path evaluation needs
separate tick delivery/identity/repeatability evidence; snapshots cannot pass it.
Demo orders require the unchanged historical/strategy/risk/execution safeguards
and an independent execution stage. Real-money execution remains unavailable.

## What the reviewed API establishes

[symbol_info_tick](https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfotick_py)
reads the latest tick or returns None. Polling can repeat a cached observation and
miss intervening updates. It is not a complete subscription stream.

[copy_ticks_from](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py)
is a date/count history request with documented UTC conventions. Those conventions
do not resolve the saved clock discrepancy. Later recovered data first becomes
available to our system at recovery receipt, never at its earlier source label.
No history request is authorized by103.

[account_info](https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py)
returns account properties including private fields. Use an allowlist, never a
full tuple dump. The documented
[account modes](https://www.mql5.com/en/docs/constants/environment_state/accountinformation)
separate DEMO, CONTEST and REAL. A server name or trade permission flag cannot
replace the actual type check. Before/after checks detect observed changes but
cannot guarantee an atomic account state throughout every native call.

[initialize](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py)
can launch the terminal if needed and can use stored account settings. Neither an
explicit executable path nor a prior process-presence check establishes attach-only
behavior. Do not call it under an assertion that terminal launch is impossible.
No attempt was made to change this rule or revive native090.

[MqlTick](https://www.mql5.com/en/docs/constants/structures/mqltick)
contains seconds/milliseconds, prices, volumes and flags, with populated unchanged
fields. It has no documented broker event sequence in this structure. One update
timestamp does not certify both bid and ask were newly updated or still executable.
The old unknown flags/revisions remain uninterpreted.

## Recording and chronology requirements

An eventual market journal must be separate from invented102. Its immutable
metadata identifies a source role, symbol, snapshot sampling mode, API/runtime
versions, contract digest and declared session. It must state `synthetic=false`
and truthfully record unverified clock/coverage states, without account IDs,
server identities, credentials or private process paths in public artifacts.

Each attempted read gets a persisted local observation sequence and collector
session ID. Store raw source seconds/milliseconds, declared native price encoding
and Decimal conversion, allowlisted original tick flags/fields, bid/ask, UTC and
monotonic boundaries immediately before/after the acquisition, guard outcome and
fixed diagnostic codes. Stamp receipt at the read boundary, not later during
batch writing; never copy a source label into the receipt field. Arbitrary input
and exception text are discarded. Output and storage bounds must be frozen before
the first attempt; exhaustion stops without overwriting or silently rotating.

Local observation sequence is **not broker tick identity**. Retain every attempted
poll. Equal allowlisted raw payloads mean repeated snapshots, not proven duplicate
market events. Same source time with different payloads remains distinct. Later
metadata changes create a new observation and diagnostic, never mutate earlier
records. Do not deduplicate history solely by millisecond, price hash or poll ID.

Keep wall-clock and monotonic boundaries distinct. A formatted UTC receipt is
not independent proof that the machine clock is accurate. Monotonic values are
comparable only within a declared process/session; restart creates a new segment
while the committed journal sequence continues. Persist the restart/disconnect
gap and retain prior segment watermarks. Do not infer elapsed time across boots
from a monotonic subtraction.

Reject malformed/crossed/nonpositive/nonfinite quotes. Missing and failed reads
remain explicit events. Receipt clock reversal/discontinuity, identity/account change, guard failure,
schema/corruption, deadline/size/budget exhaustion and durable-write failure stop
collection and preserve prior committed evidence, without automatic reconnect or
retry. Long intervals are gap diagnostics, not proof of a missing tick or market
closure. Never fill gaps or carry prices forward as newly received observations.

Keep source age unknown until its clock basis is verified. Repeated-snapshot
duration is separately measurable within a session, but cannot prove source quote
age, executable liquidity or freshness of both price sides. Do not subtract an
assumed three-hour offset, mask unknown flag bits or loosen thresholds to admit
observed samples. A later plan must freeze age/gap policies before its data.

For forward paper decisions, use only committed records available before the
decision. Preserve acquisition return, guard completion and journal availability
order; a replay must not act at source time before those steps. History received
after disconnect is a later availability batch. Keep observed prices separate
from hypothetical fills, costs and slippage; no statement of actual execution
quality follows from demo quotes.

## Next work and preserved exclusions

The useful next implementation is a **broker-free collector boundary** with an
injected quote/guard/clock interface and a separate honest market-shaped journal.
Test account switches, terminal exit, clock jumps, repeated snapshots, equal-time
updates, late history, restart gaps and disk failure with invented inputs. Its
actual broker entry must remain disabled. This can establish adapter behavior;
it cannot solve source permission, clock certification or safe attachment.

A connection plan must identify a permitted feasible attachment mechanism and
fresh evidence for its scope; another automatic SDK initialize or recycled old
native episode is not an acceptable next test. No provider/account/payment or
new external-source search is declared here. H.10 stays closed under current
evidence.003 costs,028/030 rules, all historical gates and old provider/failure
stops remain.2025 is excluded,November–December2026 remains reserved and October
quarantined. Connecting/collecting does not itself admit validation data or orders.
