# Acquisition budget review 088

Review date 2026-10-09 UTC, phase 88000000000000000000000000000001.
This phase reviews the existing acquisition layout; it does not implement a
replacement native adapter or reader. Preserve the sealed 087 source hash
3e23a791727b8232071e6f77832dbcadc104cd0a3770b4a35facc6585262df83,
2,762 bindings and 2,553 archive members, including every prior failed result
and spent marker. Oct 8 fixtures are historical simulations only. The frozen
Oct 8 gate is not moved, patched or bypassed for current runtime admission.

## Count feasibility

The successful typed schedule (without raw acquisition or full bridge) contains
70 guards: two startup, 52 control, eight wire and eight wait guards. The first
guard precedes the factory, leaving 69 inspections of owned resources. This
schedule reference does not establish combined raw success.

Each raw inspection uses at least 34 calls before any ancestor work: four
descriptor/path proofs each use file information, final path and three security
queries (20); two fresh path opens (2); pipe modes (2), security (3) and peer
acquisition (7). With two root ancestors, complete repeated walks add 30 calls,
giving the observed 64. CloseHandle and LocalFree are cleanup operations outside
Api086.call and are excluded from this count, not omitted from cleanup.

Even granting all ancestor acquisition zero cost, 69 inspections require 2,346
API calls and 4,693 clock checks including meter initialization. The unchanged
4,096-check cap permits 2,047 fully bracketed calls. This intentionally optimistic
floor excludes factory, control IO, wire IO and cleanup. It is not a feasible
proof, not a lower bound for every possible Windows API architecture, and not a
timing measurement. It disproves ancestry-only deduplication as a sufficient
correction of the existing layout. No such optimized adapter is implemented.

The current duplication also requires 139 bridge calls (cap96), 1,668 SDK queries
(cap1,024) and 208 boot queries (cap128). Raw acquisition fails first; no later
budget is claimed to have physically run past its cap. The independently
repeated SDK bridge still rejects attempt86 with 1,024 queries. A future design
must address all these counts together, while retaining each required fresh
proof inside every actual guard. No cross-guard proof cache, invented valid span,
weaker peer check, cap increase or longer window is permitted here.

## Coupled historical tests

The six-control target uses the unchanged raw callable API, transport and full
087 bridge with a historical Oct 8 clock. The fixture improves descriptor
semantics: open handles retain their object identity while new path opens see
replacement objects. Replacement is injected inside an inspection after its
root descriptor proof and before fresh path acquisition. File/root/ancestor
replacement, reparse ancestry, ACL and raw peer changes reject. Real/contest/
changed demo account and source changes between the outer and inner bridge
checks also reject. No rejected inspection earns a valid span.

The fixture models sharing error32 for independent write/delete opens during
the reader hold, but the unmodified combined model still stops after two pre
controls at API call2,048/check4,097. It never reaches those independent opens.
Their physical behavior and a complete raw episode remain unproven. Fake handle
and allocation cleanup and one owned SDK shutdown are tested; native cleanup
is not inferred from fake resource removal.

## Build and boot review

The six-input Stage087 source remains model-only. Its independently pinned image
callbacks and returned absent-editor metadata do not implement a real launcher,
bounded capture or timeout kill/wait. The fixed WMI script queries the local OS
last-restart time. Shell/script hashes and NoProfile do not bind every dynamically
loaded PowerShell module, WMI provider, COM component or child module. The runner
accepts modeled bounded output and an absent-child result; there is still no
native capped capture/owned timeout implementation. Restart, resume, fast
startup and clock-adjustment behavior have not been measured. No compiler/WMI
query is run in this review and no unique kernel boot GUID is asserted.

Primary references retained from 087:
[OS last restart property](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem),
[CIM datetime](https://learn.microsoft.com/en-us/windows/win32/wmisdk/cim-datetime),
[local WMI query](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-wmiobject?view=powershell-5.1).
Those references do not establish the missing native ownership, provenance or
timing evidence. The existing 1,611ms guard / 60,870ms episode failure remains.

## Dated requirements and closure

Prepare a fresh Oct 9 phase/reader REQUIREMENTS record binding all 37 old inputs,
six old compile inputs, this review and all unchanged 2s/10s/30–31s/250ms/60s/120s
windows. It explicitly says new reader implemented/compiled=false, entry=false,
runtime=false and orders=false. Requirements cannot admit runtime on any date;
they do not renew the old reader. A runnable dated reader is deferred until a
feasible acquisition architecture is justified and tested.

Freeze once, run one full 084 R2 active suite and one declared evidence set,
audit, seal and independently review. Keep developer observations separately.
No actual DLL/SDK/MT5/compiler/deploy/log/WMI/market/order/receipt calls or grants.
Real/contest rejection, Algo off, default off, no live toggle/martingale, and all
data/cost/clock/coverage/consumed-2025/reserved-Nov–Dec/provider exclusions remain.
No user UI action is required. The next plan is an architectural feasibility
review, not authorization to run an expired or unproved reader.
