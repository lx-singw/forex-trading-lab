# One-use capture authority046: reviewed primary sources

Reviewed2026-10-06: one query,11 opens (eight distinct pages),three finds. No
market-data HTTP/SDK requests. The following are paraphrases, not full source
copies. Design choices below are inferences, not guarantees made by the sources.

MetaQuotes documents atomic compare-and-set for an existing terminal global
variable; a missing variable causes failure. This can serialize consumption but
does not alone specify safe initialization or prevention of rearming.
https://www.mql5.com/en/docs/globals/globalvariablesetoncondition

Temporary terminal globals disappear on shutdown and are excluded from flush.
https://www.mql5.com/en/docs/globals/globalvariabletemp
Persistent-global flush returns no value; MetaQuotes notes abrupt computer
failure can lose state. Our inference: global-variable CAS alone is insufficient
to prove the full phase budget across restarts/initialization.
https://www.mql5.com/en/docs/globals/globalvariablesflush

MQL FileOpen supports local named pipes without a DLL import. It returns an
invalid handle on failure and requires flush/seek between reading and writing
a pipe. Encoding/framing still needs a native fixture; support is not proof our
integration works. FileFlush has no return value and writes buffered file data.
https://www.mql5.com/en/docs/files/fileopen
https://www.mql5.com/en/docs/files/fileflush

GetTickCount64 measures system uptime in milliseconds, with typical timer
granularity10-16ms. It is not program uptime or an independent UTC reference.
Future authority/client must sample the same Windows uptime source; Python
monotonic_ns cannot simply be assumed numerically equal to this API.
https://www.mql5.com/en/docs/common/gettickcount64

Microsoft documents configurable pipe DACLs; defaults include read access for
Everyone/anonymous, and generic write can imply pipe-instance creation rights.
Use an explicit logon-session DACL/minimum individual rights; no inherited or
default-open permission. Actual permission/peer checks remain future work.
https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights

CreateNamedPipe supports first-instance ownership, automatic remote-client
rejection and overlapped IO. Blocking calls can wait indefinitely; a default
pipe timeout governs WaitNamedPipe, not a general operation deadline. A future
server must explicitly cancel bounded IO, close handles and test MQL disconnect
behavior; choosing PIPE_NOWAIT is not a substitute for asynchronous IO.
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea

Selected design: exclusive durable phase reservation plus one in-memory authority
that burns its allowance before responding, including all uncertain failures.
Native enabled invocations must obtain a new, short-lived receipt from that live
authority every time. There is no permission file or receipt input that the
observer can reuse, and no mechanism to resume/reset a phase. Different terminal
roots, helper death/restart, framing/ACL/peer uncertainty and account changes must
fail closed. This design requires the047 no-market integration fixtures before
any runtime claim. Power-loss filesystem rollback and malicious same-user state
modification remain outside demonstrated guarantees.
