# Longer paired recorder132 preparation — 18 October2026

The new default-off read-only EURUSD recorder is implemented, tested, compiled
and deployed in its own folder. **No native collection has started.** The
allowed nominal computer-GMT window is19–23 October2026; preparation is on18
October. Old111/130 programs and their expired dates are unchanged.

## Implementation and limits

The recorder adds clock-before/latest-quote/clock-after groups to a longer
bounded observation: at most3,600 polls/10,800 diagnostic groups, minimum
one-second actual first-clock spacing, one hour elapsed checked on returns,
one fresh file and8MiB. Guards repeat during50ms waits and around each group.
Actual DEMO type, private identity continuity, connection, USD/non-tester,
Algo Trading off and visible EUR/USD checks reuse the unchanged107 predicates.
No identifiers leave memory. No order/history/SDK/DLL/WebRequest/settings API.

The exact shared pure state code enforces pending/outcome sequencing, query
and byte bounds, monotonic/drift/date/elapsed checks, no catch-up, and ended
state. Bytes are reserved before IO. Storage failure closes without another
write. New folders/files refuse collisions, with no resume or automatic retry.
Queried values are discarded on an after-read guard failure. Bounds do not
preempt a blocked native/IO call; fewer polls or a partial final pair can result.

The new132 parser preserves original raw dates/schema/values. It reuses131's
numerical quality engine on compatible parsed fields and labels outputs132.
It never rewrites132 bytes into a130 wire envelope. Quality thresholds and
event caps remain fixed; no offset transfer, age correction or strategy tuning.

## Verification

**73 distinct focused Python tests pass**:19 new132,30 retained131 and24
retained130. The new pure state/account simulation passes119,401 C++ checks,
including3,600 ideal polls and72 before/after guard fault paths over all three
read positions. Another48 retained account/quote guard checks pass. Both C++
builds use C++17 with Wall/Wextra/Werror. These are invented/pure checks, with
no native API calls. There are no test failures/errors/skips.

A report review found that rendered invented-data reports needed an explicit
input-kind label. That correction and its assertions were frozen as source
version002; all49 affected132/131 tests passed again. The24 unchanged130 tests
and native C++ checks are retained from001. Native MQL sources did not change,
so no second native compile was needed. First tested source versions remain
preserved. See [verification001](../reports/paired-recorder-132-verification-001.json),
[verification002](../reports/paired-recorder-132-verification-002.json) and
[current source freeze](../reports/paired-recorder-132-development-source-002.json).

Invented coverage includes all five entry dates, allowed and expired midnight
crossings, a full hour, pending/stopped/partial tails, failed after-read guards,
state/query/byte exhaustion, no-catch-up spacing, ended state, source/clock
reversals, nonfinite/crossed quotes, raw native bits/unknown flags, provenance,
event caps and read-only CLI behavior. Fresh-file collision/default-off/native
read-boundary structure is also checked by source inspection; no native
filesystem/runtime trial has occurred yet.

The full invented hour contains3,215,197 bytes,3,600 completed polls and10,800
diagnostic groups. JSON/Markdown CLI results match the library; JSON remains
byte-identical to the first proof. Current Markdown explicitly says
invented_fixture. This is a parser/transport fixture, not observed quotes or
trading performance. See [current proof](../reports/paired-recorder-132-offline-application-review-002.json)
and [invented quality report](../reports/paired-recorder-132-invented-quality-002.md).
The earlier proof files without002 remain preserved as the first version;
use the002 rendered report for the explicit provenance label.

## Native build and deployment

One MetaEditor build, file version5.0.0.6259 with the same recorded compiler hash
as130, produced a fresh20,862-byte EX5 with zero errors and zero warnings.
Its actual exit code is1, retained alongside successful diagnostics and the
artifact hash. Four files are deployed and rechecked in the new
**ForexDemoLab132-deddc9e4e31b** folder. No unrelated files or terminal settings
were overwritten. See [compilation](../reports/paired-recorder-132-compilation-001.json),
[deployment](../reports/paired-recorder-132-deployment.json) and
[hash recheck](../reports/paired-recorder-132-deployed-recheck.json).

All608 prior source/config/test and65 native input hashes are unchanged; seven
new files make615. Prior handoff bodies and sealed evidence are preserved.
No terminal/script launch, SDK connection, support contact, account creation,
historical/reserved strategy replay, P&L or financial/risk/cost/weight change.
October remains quarantined; November–December reserved/untouched;2025 consumed;
historical/provider/H.10/native090 routes stay closed.

Quote age, source/receipt UTC, executable quality, delivery completeness,
complete costs and profitable performance remain unverified. Market/paper/
order/real-money availability remains false. Next is [one manual run during
19–23 October](PAIRED-RECORDER-132-USAGE.md), then preserve and inspect the closed
owned export. The one-hour native result is pending.
