# One-use capture guard046 results

Implemented a reusable one-use permission authority core and pure MQL receipt
guard, tested entirely offline. Six repeated launch requests issue one permission;
32 simultaneous requests issue one; eight concurrent startups create one authority
for the same reservation. Disabled test clients make no permission or quote call.
The allowance is consumed before request validation, guards, journal or response.
Missing/changed state, invalid account/instrument, expiry, lost response, journal
failure and uncertain quote failure never refund it. Closing the helper or trying
to start again with an existing/empty/corrupt reservation cannot rearm the phase.

654 software tests pass (32 new), zero failures/errors/skips. The exact new MQL
header passes18 synthetic C++ predicates and agrees with the Python receipt check
on500 boundary combinations. ActualDEMO/USD/Algooff/connected/EURUSD checks use
existing account-type guards through injected fake APIs; real and contest modes
are rejected. Private identity changes before/during/after a permission are
rejected by the guard. Reservation/journal/response/summary contain no account
identifiers. Test fixtures are synthetic and do not connect an SDK.

1,386 inputs were frozen before the full regression, including all critical046
sources/protocol/tests/header/harness/research/sealer and Python/G++ executables.
The entire045 prior snapshot verified1,378 current bindings/1,305 archived members/
73 external inputs. Compiler executable hashing does not freeze all operating
system libraries or prove native MT5 compilation. Original042 MQL/EX5 and
044/045 evidence are preserved unchanged.

A primary-source review (one query,11 opens/eight distinct pages,three finds)
examined atomic globals, persistence, uptime, named pipes, permissions and IO
timeouts. CLOCK-UI-SAFETY-046-RESEARCH.md links/paraphrases those official pages
and distinguishes design inference from documentation. Selected transport for
the next phase: an exclusive local one-use authority rather than an observer
recreating counters. Each native enabled invocation must request a fresh receipt;
it cannot load permission from inputs/logs. Reference session limit900 seconds,
receipt validity at most2 seconds with phase/policy/date/uptime bounds.

Native IPC, ACL/peer binding, wire framing, cancellation and transport lifecycle
are NOT implemented or verified here. The new header is a pure predicate, not a
deployed observer. The old042 script still cannot enforce a cross-invocation
budget and must not be rerun. CAPTURE-TRANSPORT-047-PLAN.md declares native
no-market integration/fixtures before any later dated observation. No new native
quote, SDK connection, pipe, MT5 compilation/deployment, history, strategy, order
or terminal setting action occurred in046. Research web reads are separately
reported; there were no market-data HTTP requests.

Limits: exclusive reservation/flush behavior was tested on this offline filesystem,
not certified against power-loss storage rollback or malicious state deletion.
The future worker must bind the canonical reservation root, phase and terminal;
the core is not an authenticated transport or a defense against same-user code
tampering. Different-authority paths can only be excluded by that integration.
Across-process checks cannot prove no switch-and-back between account samples;
the observer must recheck private identity and date before/after the quote.
Native timeout behavior must be demonstrated rather than inferred from docs.

045's six observed native quote reads exceed044's declared one.044 remains
expired/incomplete; its zero companion-collected quote count is not total native
reads. The new passing tests do not repair either outcome or supply profit/edge
evidence. Clock/coverage/cost/flags/033/035 failures remain; historicalUTC/offset
correction and fresh/annual eligibility/orders false. Consumed2025, reserved
Nov-Dec2026 and provider stops are unchanged.
