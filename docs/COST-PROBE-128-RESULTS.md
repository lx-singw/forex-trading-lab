# Cost probe128 preparation results

Both documented API signatures compile in the installed MetaEditor, and the
bounded read-only collector is built, tested, compiled and deployed.
**The demo feed's actual commission rules and margin factors are still pending
one manual native launch.** Compiler support does not establish runtime query
success or cost completeness.

The isolated signature fixtures have empty OnStart functions and were neither
deployed nor executed. The actual collector calls SymbolInfoCommissions and
SymbolInfoMarginRate, preserving reported units, tier fields and application
conditions. It calculates no fees or margin requirement in dollars.
[MetaQuotes commission API](https://www.mql5.com/en/docs/marketinformation/symbolinfocommissions)
[MetaQuotes margin API](https://www.mql5.com/en/docs/marketinformation/symbolinfomarginrate)

The native API reports -1 on failure and 0 when no rules are reported. The
inspector retains failure, empty successful response, complete reported rules
and incomplete rule payload as separate states. Zero reported rules is not
claimed to establish zero costs. Success with an error code is treated as
failure and its native returned count retained. Raw conditions, tiers and
currencies stay uninterpreted until sufficient evidence supports a model.
[MetaQuotes commission return semantics](https://www.mql5.com/en/docs/marketinformation/symbolinfocommissions)

## Safety and bounds

The collector defaults off and enforces actual demo enum, connected USD account,
Algo Trading off, stable private identity, non-tester and already-visible EURUSD
with EUR/USD currencies around every query and again before rule serialization.
A failed after-read guard emits no queried values. Partial serialization remains
incomplete. Identity is kept in memory only; no account identifier, server string
or arbitrary diagnostic text enters exports or logs.

The new nominal computer-GMT envelope is 2026.10.14, five diagnostic queries,
eight rules, 16 tiers each, 128 total tiers, 64 KiB and 60 seconds checked on
return. Native allocation and blocked calls cannot be interrupted by these
post-return bounds. Currency output is empty or three uppercase letters; all
double bits are retained and nonfinite values rejected. Margin factors must be
finite and nonnegative. Failed margin values remain unknown rather than zero.

It uses a new owned terminal-local folder and nontruncating open, preserves
attempts before reads and chained frames/end/stop evidence, and adds no resume
or automatic retry. It has no SDK, DLL, WebRequest, history, order-placement,
account/login, symbol-selection or settings API.

## Verification and deployment

- **44 Python tests pass**: 25 new cost-probe tests and 19 retained metadata
  inspector tests. Zero failures, errors or skips.
- **92 new C++ boundary checks and 48 retained account/quote guard checks pass**,
  with warning-as-error compilation. Actual demo/real/contest decisions use the
  unchanged shared107 predicates.
- The 11-member source freeze binds all seven new source/config/test files,
  the shared guard and guard test, retained native-bit decoder and reserved plan.
  All 586 prior source/config/test and 63 native input hashes are retained.
  The source/config/test set now contains 593.
- Two signature builds and one collector build report **0 errors, 0 warnings**.
  Compiler exit code **1** is retained for each; build success is established
  by the diagnostic summary and fresh nonempty artifact, rather than treating
  that process code as an ordinary zero-is-success convention.
- MetaEditor file version is **5.0.0.6259**. Its hash remains unchanged between
  this phase's compatibility checks and collector compilation. It differs from
  the compiler hash recorded in127; no compiler or terminal update was performed
  by the assistant, and the cause of that change was not investigated.
- The collector EX5 contains **24,722 bytes**. Only its MQ5, CostBounds128 header,
  unchanged PrivateGuard107 header and EX5 are deployed into
  **Scripts/ForexDemoLab128-27eeb9d91d0a**.

Evidence: [compatibility checks](../reports/cost-probe-128-compatibility.json),
[source freeze](../reports/cost-probe-128-development-source-001.json),
[tests](../reports/cost-probe-128-tests-001.json),
[collector compilation](../reports/cost-probe-128-compilation-001.json),
[deployment](../reports/cost-probe-128-deployment.json).
The [final source closure](../reports/cost-probe-128-final-source.json) and
[preparation review](../reports/cost-probe-128-completion-review.json) close
preparation, not native data qualification.

## Next and remaining limitations

Use the [single-launch instructions](COST-PROBE-128-USAGE.md), then preserve and
inspect the closed owned export. No current fee rates were acquired in this
preparation. No market returns, strategy tuning, financial-rule changes,
historical/reserved replay, source-time conversion, support contact, paid service,
account creation, settings change, SDK connection, unrelated overwrite or order
occurred. The prior financial tests remain retained and were not rerun.

Market, paper, order and real-money availability remains false. Commission/
margin metadata alone cannot certify historical terms, slippage, quote freshness,
clocks, calendar coverage or strategy performance. October stays quarantined,
November–December2026 reserved and2025 consumed. Closed historical/provider,
H.10 and native090 routes and old dated107/111 authority remain unchanged.
