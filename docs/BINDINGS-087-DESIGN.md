# Build preparation and native binding review 087

Declared UTC date: 2026-10-08; local review continues on October 9. Phase
87000000000000000000000000000001. Preserve the immutable 086 reader and its
Oct 8 UTC gate. Verify its final source hash
3af78b9ed29d97e28d808bad79e9efab8eb5dba77293fa10e78980132d0fc469,
2,730 bindings and 2,523 archive members before freezing this stage.

## Build schema and stage

The new build contract binds all 37 candidate source/import/design inputs and
the six exact MQL compilation inputs. It requires the observed compiler exit 1,
one clean zero-error/zero-warning summary, editor/terminal build 6244, independently
pinned image hashes and an artifact of 1–1,048,576 bytes. Duplicate/noncanonical
records, integer booleans, altered nested limits, diagnostic warnings, changed
source, extra output files and surviving editor processes reject. No exit-code
normalization or old artifact reuse is allowed.

Stage087 accepts model callbacks only. Default-off run performs no marker,
clock or backend work. An enabled stage persists an exclusive durable attempt
before staging. It copies six source/header files into a new owned directory,
rehashes every candidate input before launch and after outputs, checks staged
inputs, and attempts final metadata even after failure. Restart, interrupted
compile, timeout or partial marker cannot regain an attempt. Directories and
unrelated files are never overwritten or deleted. Real compiler launching,
process ownership/timeout cleanup and actual metadata acquisition still require
a separate reviewed entry. Modeled compiled records are never native evidence.

## Boot-time corroboration

Microsoft documents Win32_OperatingSystem.LastBootUpTime as the reported time
of the OS's last restart: [OS class](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem).
The fixed local PowerShell script selects that property only through WMI. It
prints exactly one fully specified CIM datetime and no exception/machine/account
information. The parser rejects wildcards, invalid calendars, future values,
excess bytes and unknown offsets, preserves microseconds and converts explicit
offsets to a canonical UTC value. This follows the documented
[CIM datetime format](https://learn.microsoft.com/en-us/windows/win32/wmisdk/cim-datetime).
The chosen local query uses the documented Windows PowerShell 5.1
[Get-WmiObject](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-wmiobject?view=powershell-5.1).

BootReader087 rehashes the pinned shell and script before and after every fresh
query, has 128 query attempts, requires an absent owned child, a 2-second
returned duration and exactly bounded stdout/no stderr. The runner remains
model-only. Actual capped capture, hidden process ownership/kill/wait, module
provenance and provider behavior are unverified and must be implemented/reviewed
before admission. A returned duration check cannot preempt a stalled provider.

This is explicitly a WMI last-restart-time corroborator, not a unique kernel boot
GUID or a substitute for the bound process creation/session/logon and three
clocks. Its stability under restart, resume, fast startup, timezone/clock changes
and WMI behavior has not been measured. Do not mark native boot proof verified.
The reviewed primary NtQuerySystemInformation documentation warns that its
internal interfaces can change; it does not specify the needed boot structure:
[Microsoft API reference](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntquerysysteminformation).
No undocumented numeric-class/layout guess or inferred uptime timestamp is used.

## Guard bridge

FullGuard087 wires the already-owned model metadata SDK to actual-account-type
DEMO/USD/connected/Algo-off/same-account/EURUSD metadata checks, pinned SDK version
and loaded library, fresh terminal/helper process identities, all nine required
image/helper/artifact/config roles and 40 source inputs (37 candidate inputs plus
the new bridge, build module and boot script). It checks identities and account
metadata at both ends, queries boot corroboration afresh, rehashes full bytes via
the injected reader and checks owner/SDK/pin identity. No source/image proof is
cached between calls. The raw 086 adapter separately acquires fresh private pipe,
peer, ACL, descriptor/path and complete ancestor facts inside the same guard.
Real function tables and native_entry087 remain unavailable.

Standalone model guards can pass, but the combined raw adapter/guard/transport
episode fails structurally: raw API calls consume two clock checks each. The
4,096-check cap is exceeded on check 4,097 after 2,048 injected API calls, with
31 outer guards started, 30 valid spans and only two controls completed. Its
episode elapsed is only 5 ms, so this is the clock-sample COUNT budget, not the
60-second deadline or the 1,611 ms latency scenario. No missing successful span
is invented. Five model close attempts and one SDK shutdown complete, with no
remaining fake handles or allocations. Source hashing and API latency are free
in this model; actual work can only add obligations. Fake resource removal is
not proof of native close.

A repeated standalone guard reaches its 1,024 SDK-query cap on guard attempt 86;
85 guards complete. Neither rejection is permission to raise a cap, skip a
guard, cache a proof across guards or widen freshness/hold/time windows. The
next review must reduce redundant acquisition work while preserving every
required fresh proof, then test the full combined episode within these budgets.

## Evidence and closure

Developer refinements precede freeze. Preserve the first 33-test developer run
with one fixture failure (expected 32 metadata queries, observed 24 across two
guards), followed by passing 34-test runs. The fixture correction changes no
runtime guard. One frozen active full regression and one declared 16-case set:
nine build cases, six guard cases and one combined episode. Only the isolated
normal build and normal guard complete; one default-off case and 13 rejections
are expected. Audit, seal and review hashes/archives; update four handoffs.

No actual DLL/WMI/SDK/MT5/MetaEditor/deploy/log/market/order/receipt invocation or
grant. Native boot/guard/compilation/sharing/ACK and profitable edge remain
unverified. All 086 counters and 2s/10s/30–31s/250ms/60s/120s runtime windows stay.
Data, clock, cost, coverage, consumed-2025, reserved Nov–Dec 2026 and provider
exclusions persist. Prior failures/spent markers remain immutable. Next 088 is
unexecuted. No user UI action is required.
