# Metadata probe127 preparation results

The fresh private read-only diagnostic is built, tested, compiled and deployed.
**Native execution and actual metadata capture are pending one manual MT5
launch.** The source and deployment do not prove the terminal ran it.

The probe defaults to collection off. When enabled, it requires the actual DEMO
account enum, a connected USD account, Algo Trading off, a stable private account
identity, a non-tester EURUSD chart and an already-visible EUR/USD symbol.
Those checks repeat around every diagnostic read. Identity stays in memory and
never enters output. It has no order-placement, history, SDK, DLL, WebRequest,
login, symbol-selection or terminal-setting API.

The new date envelope is nominal computer-GMT 2026.10.14, 128 queries, 60 seconds
checked on return and 64 KiB in a new terminal-local run folder. A failed
after-read guard discards that queried value and preserves its pending attempt.
The strict offline inspector rejects invalid framing, digest chains, ordering,
nonfinite prices and clock faults. Failed properties are unknown, not zero-cost
assumptions. Stops and partial tails remain incomplete.

## Verification

- All **19 new Python tests** passed, with zero failures, errors or skips.
- All **179 new C++ clock/limit checks** and **48 retained account/quote guard
  checks** passed with warning-as-error compilation.
- The 10-member development source freeze includes the seven new source,
  configuration and test files, the unchanged shared guard and guard test, and
  the reserved plan. All 579 earlier source/configuration/test hashes and 62
  earlier native input hashes are preserved; the source set now contains 586.
- The prior 314 financial/comparison checks remain retained evidence. They were
  not rerun here because financial strategies, costs and risk rules did not
  change.
- One actual MetaEditor invocation produced **0 errors and 0 warnings** and a
  **26,598-byte EX5**. Only this probe and its two headers plus EX5 were copied
  into **Scripts/ForexDemoLab127-1252773ffdf0**.

The initial orchestration failed to write two evidence records because its cwd
included a PowerShell provider prefix unsuitable for .NET file I/O. Compilation
and deployment had already succeeded. The failure record is preserved; recovery
verified the existing staged/deployed file hashes and diagnostics without
recompiling or recopying. The compiler's exit code was not preserved and is
recorded as **null**, not inferred as a success code.

Evidence: [source freeze](../reports/metadata-probe-127-development-source-001.json),
[tests](../reports/metadata-probe-127-tests-001.json),
[recording failure](../reports/metadata-probe-127-orchestration-failure-001.json),
[compilation](../reports/metadata-probe-127-compilation-001.json),
[deployment](../reports/metadata-probe-127-deployment.json).
The final [source closure](../reports/metadata-probe-127-final-source.json) and
[preparation review](../reports/metadata-probe-127-completion-review.json) bind the
handoff and evidence. Those reviews close preparation only.

## What remains unresolved

No actual new quotes, metadata, strategy returns or orders were produced by this
preparation. The two latest-quote reads planned here are not a tick-history
capture. Current reported properties may help interpret later evidence but do
not establish commission, slippage, historical costs or certified clock offsets.
Raw weekly session times are a current template, not a historical calendar.
Neither the hash chain nor a market-declared header authenticates the producer.

All market, forward-paper, order and real-money availability flags remain false.
Historical/provider, H.10 and native090 route stops remain in place. This new
dated probe does not renew old107/111 authority. Consumed 2025, October quarantine
and reserved November–December 2026 data remain untouched. No historical or
reserved replay, support contact, paid service, account creation, SDK connection,
terminal launch, settings change, unrelated file overwrite or actual order
occurred. The user's authorization covers private diagnostics; no separate
licensing clearance is claimed or requested for this preparation.

Next: use the [single-launch instructions](METADATA-PROBE-127-USAGE.md), preserve
and inspect the closed owned export, then decide what its actual evidence
supports. A single metadata observation cannot qualify a profitable strategy or
repair historical gaps.
