# Private recorder107 — results

Client date: 12 October 2026.

The private demo recorder, offline inspector and launch instructions are built,
tested, compiled and deployed. The new script has not been executed in MT5, so
there are no new observed market quotes, current account proofs or trading results.

## Scope correction

The user revoked all contact and asked us to continue private demo engineering.
No support message was sent. The source103 documentary permission prerequisite was
our internal research policy, not a technical requirement for writing this code.
That prerequisite is superseded for this separate private diagnostic scope.
Original103/105/106 evidence is preserved; permission gates are not relabelled as
passed. Use rights remain unverified, with no legal finding or publication claim.
No support outreach or further licensing search is required for this step.

## What changed

Six new canonical implementation/test files provide:

- A self-contained MQL script and shared guard header. No order API, DLL, pipe,
  WebRequest, Python SDK login/initialization, symbol selection or trading toggle.
  Collection defaults off. Actual DEMO/USD/connected/non-tester/Algo-off and stable
  private identity are checked repeatedly; identity stays in memory.
- A terminal-local, separate file for each run. Attempts are written and flushed
  before their quote reads. Failed after-read guards discard the quote. Missing or
  invalid reads stop, and incomplete acquisition cannot silently resume.
- A bounded export carrying raw source seconds/milliseconds, native double bits,
  volume, flags and separate receipt/read/guard clocks. SHA256 chaining detects
  inconsistent edits; a complete footer requires all 120 observations.
- A read-only Python inspector and CLI. Strict counts, boundaries, native values,
  malformed/tampered frames and terminal-state sequencing are checked. Repetition,
  equal-time changed payloads, source reversals and receipt gaps remain visible.

The diagnostic is limited to machine-GMT date2026.10.12,120 latest-value polls,
at least500ms between read starts,60seconds elapsed and256KiB output. A blocked
native call is not hard-preempted. Computer-GMT is not independently certified UTC.
Source-age, provider tick identity, per-side freshness and complete tick delivery
remain unknown; no old three-hour clock offset is applied. Hashes do not establish
producer authenticity, atomic account snapshots or power-loss durability.

## Verification and deployment

- Final focused run: **37 tests passed**, zero failures/errors/skips. The actual
  shared MQL guard decisions also passed **48 C++ checks**, including real/contest
  accounts, account switches, clock faults and invalid quote values.
- Prior34-test development run and source archive are preserved. Three additional
  tests tightened the inspector: missing/invalid reads must be followed by their
  matching stop, and an absent stop stays incomplete.
- Existing MetaEditor compiled the unchanged native source with **0 errors,
  0 warnings**, producing a nonempty18,406-byte EX5. MetaEditor's process exit code
  was1; it is preserved, not presented as zero. Completion, diagnostics and the new
  output artifact establish compile success, matching our existing compiler policy.
- Two staging attempts, one compiler invocation. The first orchestration attempt
  failed before copy/compilation because a provider-qualified PowerShell path was
  unsuitable for .NET; the corrected explicit UNC path used a new isolated stage.
- Only three new files were deployed, with matching SHA256 hashes, into
  **Scripts/ForexDemoLab107-dd8f1187759b**. No old artifacts or settings were
  overwritten. No terminal launch, script execution or order submission occurred.
- All508 retained source hashes remain unchanged; six new files make514 retained
  source bindings. The earlier2,095-test result is retained; no new full-suite
  result is claimed for this isolated component.

Native desktop control is unavailable in this session. The one user step is the
manual launch described in [PRIVATE-RECORDER-107-USAGE.md](PRIVATE-RECORDER-107-USAGE.md).
A fresh native run must still prove file output, startup guards, receipt behavior,
snapshot counts and inspection on this terminal. The portable tests are not that
runtime evidence.

## What follows

Run the one-minute read-only diagnostic, then inspect the closed export and report
the observed quality. Only after the source and timing are adequate can a separate
forward paper experiment compare fixed rules with costs and chronological
development/validation periods. There is no profitability or always-winning claim.
Automated orders remain unavailable. Historical gaps, costs, original strategy
rules, old provider stops, H.10 closure, native090 closure,2025 exclusion, October
quarantine and untouched Nov–Dec2026 validation reservation remain unchanged.

Implementation API references: [native union representation](https://www.mql5.com/en/docs/basis/types/classes),
[SHA256 CryptEncode](https://www.mql5.com/en/docs/common/cryptencode),
[FileOpen sandbox](https://www.mql5.com/en/docs/files/fileopen),
[read/write file flags](https://www.mql5.com/en/docs/constants/io_constants/fileflags)
and [computer-derived TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt).
