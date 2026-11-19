# Sprint 210 · Weekend publication receipt review

19 November 2026. The retained evidence reviewed contains no paired record
of a completed Friday H4 becoming visible and the Sunday H1 opening on the
same receipt clock. The offline audit now checks what such a record could
establish. The quote-dependent and clock-based scenarios remain conditional.
[Weekend publication timing](RESULTS-209.md)

## What the retained evidence establishes

| Evidence | Recorded | Missing for this decision |
| --- | --- | --- |
| January and July 2022 Exness summaries | Source labels for nine last-Friday and first-Sunday observations. All nine Sunday labels follow the modeled H1 opening. | Strategy-visible H4 completion, a shared receipt clock and complete intervening update coverage. [January](RESULTS-203.md) · [July](RESULTS-204.md) · [Calendar check](RESULTS-208.md) |
| October 2026 timing and paired recorder probes | Bounded latest-quote polls and before/after clocks. The two completed one-hour probes ran on separate weekdays and retain polling gaps. | A complete Friday-to-Sunday trace with H4 visibility checks. Snapshot repeats and silence between polls cannot exclude source updates. [Timing probe](../TIMING-PROBE-130-CAPTURE-RESULTS.md) · [Paired runs](../PAIRED-RECORDER-132-CAPTURE-002-RESULTS.md) |
| October 2026 context recorder and coverage review | Five separate guarded sessions. The last Friday capture spans just under four hours between first and last completed receipt markers. The coverage review qualified zero H1 bars. | Friday completion and Sunday opening in the same trace. These runs stay in their quarantined scope. [Context recorder](../CONTEXT-RECORDER-136-RESULTS.md) · [Coverage](../COVERAGE-137-RESULTS.md) |
| Native helper trial | Four Windows owner/helper trials using invented data and operational fault cases. | MT5 bar or quote observations. The retired collection window and false collection grant remain in effect. [Native helper trial](../RECORDER-NATIVE-158-RESULTS.md) |

## Receipt audit

The command takes an `invented_weekend_publication_trace` with a `calendar`,
an `h4_end`, and ordered `events` on one declared clock. The H4 close and
its first scheduled H1 opening must border a declared weekend. Each event
has a `kind`, `time` in epoch milliseconds, and an `ordinal` that orders
events sharing a timestamp. All H4 observations refer to the declared bar.

| Event kind | Meaning |
| --- | --- |
| `h4_unavailable` | A successful check found the target H4 had yet to become visible as complete. A failed query supplies no such observation. |
| `h4_completed` | A successful check saw the target H4 as complete. The audit keeps the first such receipt. |
| `eurusd_update` | A witnessed update, separate from a poll of an unchanged quote. The audit records the first update and the first at or after the opening, and counts observed updates earlier than the opening. |
| `scheduled_h1_open` | An optional ordered marker for the H1 deadline. It carries no price. A completion at that timestamp without an opening marker leaves the order unresolved. |

The report compares observed H4 availability to the scheduled opening.
When the last unavailable check is before the deadline and the first
completed check is after it, the poll gap leaves actual publication order
unresolved. A trace with no completed observation reports an unknown
completion. An early H4 observation alone establishes neither a strategy
decision nor an eligible opening price. No missing event is synthesized.
[Frozen entry order](PROTOCOL.md#c4-entry-and-data-level-semantics)

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline.weekend_publication \
  invented-trace.json new-report.json
```

## Verification and disposition

The audit uses a strict event schema, binds its input hash and rejects
reordered, conflicting and out-of-scope traces. Invented early and late
examples reproduce their respective observations and input hashes. All 80
targeted timing, opening, fill, signal-count and coverage tests passed.
The canonical Phase 10 status remains `UNAVAILABLE` with null actual counts.
This sprint opened only retained documentation and metadata and ran invented tests. No
native capture, provider contact or new study window was initiated.

Any future observation needs the exact completed bar identity and an
opening marker plus intervening EURUSD receipts on the same clock. It
would describe its own feed and dates. Historical qualification still
needs evidence for the proposed archive.
