# Keep-awake139 standalone usage

This helper only requests temporary prevention of idle sleep. It does not
start MT5, record prices, qualify source data or enable trading. It is separate
from the expired136 program and the invented138 acquisition model.

The current Windows executable and its SHA256 are recorded in
`reports/keep-awake-139/compilation.json`. Canonical C# remains in this
repository; Windows build artifacts are in a dedicated local temporary build
folder. No installation or startup entry was created.

From a Windows PowerShell terminal, set `$helperExe` to the recorded
`helper_path`, verify its SHA256 against `helper_sha256`, then:

```powershell
# Disabled: reports off and exits without power queries or a power request.
& $helperExe

# Explicit short standalone diagnostic, on mains power.
& $helperExe --enable --seconds 30
```

Duration accepts1–14,400 seconds and defaults60 seconds when enablement is
explicit. There is no background schedule, retry or automatic renewal.
The program returns fixed JSON and exits with0 for off, expiry or cancellation;
configuration, power, API and cleanup failures use2. Inspect acknowledgements
separately rather than assuming a successful final status proves uninterrupted
power-request effectiveness.

Named cancellation and readiness options are for a supervisor/test harness:
`--cancel-event Local\ForexDemoLab139Cancel-<32 lowercase hex characters>` and
`--ready-event Local\ForexDemoLab139Ready-<32 lowercase hex characters>`.
Those Windows events must already exist in the same session. Missing/invalid
events reject setup before request creation. Names are random non-identity
tokens, never account-derived values. A readiness signal occurs only after
SetRequest acknowledges. A supervisor must retain cancellation handles until
the child has finished and must link owner loss to child termination; a parent
exit alone does not provide that behavior.

Ctrl+C is handled where console hosting permits it, but the retained native
test verified named cancellation, not Ctrl+C. Terminating the helper process
closes its kernel handles via Windows; a forced exit may not run managed
cleanup or emit a receipt. Never terminate another process by name to stop
this helper. The native test terminated only the exact child it had created.

Build with the already-installed Microsoft.NET Framework C# compiler, target
x64, console executable, warnings as errors, explicit framework references to
mscorlib/System/System.Core/System.Web/System.Web.Extensions, and the two
canonical files `src/windows/KeepAwake139.cs` and
`src/windows/KeepAwake139Program.cs`. Use a new owned local build folder and
record source/binary hashes. No unsigned PowerShell entry script, policy
override, elevation, downloaded compiler or SDK is required.

Do not treat the helper as a guarantee against user-directed sleep, policy
overrides, lid closure, power/network loss or a stalled call. Source clocks,
session calendar, costs and sufficient observed history remain separate
requirements. No fresh collection is scheduled or authorized by these usage
instructions, and November–December data remains reserved/untouched.
