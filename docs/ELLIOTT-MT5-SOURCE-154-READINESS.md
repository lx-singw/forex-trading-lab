# Elliott154 — identified MT5 recorder and collection readiness

15 November 2026. The user identified `ForexDemoContextRecorder136` in MT5's
Experts Source column. This is a user-reported program name, not an inspection of
the terminal, a verified DEMO account, a newly identified feed supplier or an
existing historical-price export. This sprint reviews source/configuration and
existing documentation only. No terminal, account, log, quote file or price rows
were opened, and no collection or historical download was started.

## What the Experts tab provides

MT5's [official log documentation](https://www.metatrader5.com/en/terminal/help/start_advanced/journal)
describes Experts as a program journal. Its Open command opens the journal folder
and flushes current journal entries to log files. Expert logs are under
`MQL5/Logs`. That operation does not export historical price observations.

For our identified program, the canonical MQL source is a one-shot **script**,
with `CollectEvidence=false` by default. Its generic Experts message is
`FXDL136` followed by reason/query/guard/byte counters. Quotes and context belong
in a separate terminal-local file:

```text
MT5 Data Folder/MQL5/Files/ForexDemoLab136/Run136-.../Context136.txt
```

That is a relative output convention from the source, not a discovered current
file path. No terminal hash, account identifier, server name or credentials are
requested or recorded here. The current process state, input value, last message
and deployment bytes have not been observed.

MT5 separately documents historical bar/tick export through the Symbols dialog's
[Bars and Ticks tabs](https://www.metatrader5.com/en/terminal/help/trading/market_watch).
This is a potential historical-input route, not a collection grant or a finding
that this account supplies qualified history. No symbol/date request or export
was made in this review.

## Current readiness

| Item | Evidence and disposition |
| --- | --- |
| Identified program | User reports `ForexDemoContextRecorder136`; current runtime/deployment remains uninspected |
| Existing collector | Source and config retain26–30 October2026 nominal computer-GMT dates, default-off collection and no orders/history interface |
| Current window | Expired. `DateAllowed136` rejects other dates; reason11 denotes its date guard. No actual reason code was read today |
| Existing output | Five closed October runs were previously reviewed; current files were not reopened |
| Historical usefulness | Coverage137 reported zero qualified H1 bars in every run. Raw samples/repeats do not supply the253-session plus24/24-month Elliott study |
| Newer supervision | 138/140/142/143 contain lifecycle/helper work;143 remains helper-only with invented acquisition events and no native market recorder integration |
| Actual account type | Old136 source queries the actual account enum and maintains private identity continuity. The current account's type has not been queried |
| Feed/source qualification | Applicable source-use, clock/UTC uncertainty, sessions/coverage and complete costs remain unresolved; Experts does not identify these facts |
| Present admission | No actual market study, fresh collection or native order submission is enabled |

The old [136 usage instructions](CONTEXT-RECORDER-136-USAGE.md) explicitly state
that its window has expired and must not be restarted or extended. The later
[137 coverage assessment](COVERAGE-137-RESULTS.md) reports the separate runs without
joining them into continuous history. The [144 plan](ELLIOTT-EXPANSION-144-PLAN.md)
preserves October quarantine, consumed2025 and reserved/untouched November–December.
This review changes none of those boundaries.

The old source's actual-DEMO checks are implementation evidence, not proof of the
currently open account or future native integration. A demo-looking server name,
user description or journal title cannot replace an actual enum check.

## Concrete next engineering slice

Proceed within the already authorized disabled-adapter work from144 and the
[143 handoff](NATIVE-SUPERVISION-143-RESULTS.md). This is preparation, not a request
to launch the old program or an assignment of new capture dates.

1. Connect the138 acquisition lifecycle and140/143 fresh supervision observations
   to a distinct read-only recorder port, initially accepting **invented** clock,
   quote, context and guard inputs. Keep native source access and retries default
   off; retain the original136 sources, wire and archives unchanged.
2. Test source/account/helper faults before and after a pending read, delayed or
   repeated observations, interruptions, context boundaries, storage failure,
   elapsed/byte limits and restart. Preserve partial attempts explicitly; restart
   creates a new job and cannot append to an unfinished capture.
3. Review a separate native binding and isolated compilation only after the pure
   boundary passes. Actual native observations must recheck DEMO enum, private
   identity continuity, connection, non-tester status and required symbol/currency
   predicates; reject REAL, CONTEST, unknown and changed identity. There is no order
   transport or real-money toggle in this work.
4. Before any actual collection, bind the applicable feed/use evidence, data
   boundaries, explicit dates, duration/poll/storage caps, clock/session/context
   evidence and current native build into a separate bounded run plan. Dates and
   provider remain **unassigned** here. A blanket restart, edited136 date list or
   enablement of Algo Trading cannot supply that evidence.

This engineering slice can progress without credentials or a price export. A new
capture could provide operational evidence, but would still need independent
qualification before strategy use. Historical study eligibility remains separate:
253 prior complete sessions, qualifying D1/H4/H1 history and at least24 calendar
months each of development and genuinely unseen validation, with costs and trial
history. Four years of waiting is not assumed; a separately qualified historical
source could serve. None is identified or promised by this review.

The source-use finding is the dated unresolved project finding in
[106](FEED-TERMS-106-RESULTS.md), not a new legal conclusion. Generic MT5 help does
not establish permission for a particular supplier's feed. No provider was
contacted and the existing support draft remains unsent.

## Verification and limits

This is a documentation/source-readiness sprint; no new runtime implementation or
strategy tests are claimed. Static review checked the canonical136 default, date
predicate, actual-account guard query, generic status and output convention;
configuration agrees with its date/cap/default declarations. Existing136/137 and
143 results supply the historical collection/coverage and integration findings.

The [portable review record](evidence/elliott-mt5-source-154/README.md) binds the
reviewed source/configuration/document bytes, records the official documentation
references and preserves the unavailable readiness result. Local verification
checks source hashes and repository links. Trading/runtime and frozen-control
bindings remain unchanged. No old acceptance totals are added to this sprint.

The full Elliott plan remains incomplete. Qualified source/run admission and its
runner, broader strategy acceptance, remaining viewer/visual review and disabled
native reconciliation remain open. All16 actual market cells retain unavailable/
null results, and automated orders and real-money execution remain unavailable.
