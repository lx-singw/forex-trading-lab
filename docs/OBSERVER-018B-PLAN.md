# Symbolic initialization contract 018B

Declared 2026-10-06 after preserving first runtime 018. Original 018 ledger,
fixtures, observer body, source archive and failed review stay unchanged.
The first compile had zero errors/warnings and produced all 38 runtime rows.
302/304 fields matched. Wrong-symbol and wrong-period initialization returned
32767; the Python fixture had assumed numeric 2 for the named parameter rejection.
Both original observer decisions correctly rejected initialization. Do not
silently edit expectations or claim the original strict review passed.

Repeat the same frozen inputs in a supplemental harness. Only diagnostic
serialization changes: translate INIT_SUCCEEDED/INIT_FAILED/
INIT_PARAMETERS_INCORRECT to the existing canonical 0/1/2 fixture categories
using their MQL symbolic constants. Also output every raw initialization value,
its EnumToString name and the three compiler-native enum constants in a separate
CSV. A second checker requires the correct symbolic name and raw value for each
case, and checks the unchanged original 304 fields through the original checker.
No hardcoded acceptance of observed 32767, broader allowed return range or
changed strategy/account guard. Bind both outputs, source equivalence, compiler,
launch configuration and prior failed attempt before accepting a repeat.

Freeze generated supplemental source, driver, checker, tests and this plan before
rerun. New unique portable runtime and output, identical safety settings from
018. No account/config copying, primary EA deployment, order code, market data,
cloud agents or optimization. Failed evidence remains preserved. Existing annual
data rejection and performance/demo readiness flags remain false.

The [official OnInit documentation](https://www.mql5.com/en/docs/event_handlers/oninit)
defines named initialization outcomes; nonzero means failed initialization. It
does not specify a numeric value for parameter rejection on that page. This
supplement removes our unsupported integer assumption, with runtime enum evidence.
