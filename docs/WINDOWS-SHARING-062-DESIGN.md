# Local Windows sharing probe062 design

The new probe measures a regular-file alternative to the unproven pipe boundary
in061. It never authorizes capture or trading. Synthetic bytes contain no047
request/receipt magic; one local native file session is separate from all spent
054/057 allowances and the prior failures remain unchanged.

[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
documents bidirectional sharing compatibility and sharing remaining until close.
Omitting share-write blocks new writers and conflicts with existing writers;
omitting share-delete excludes delete and rename access. CREATE_NEW fails when
a name already exists. The experiment tests these documented results explicitly,
without attempting mutation through a denied writer/delete handle. No security
privileges are enabled.

[ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile)
documents synchronous reads with a NULL OVERLAPPED and that a read beginning
before EOF but extending past it can succeed with only the remaining bytes.
The probe requests85 bytes from a locked84-byte regular file using two separate
reader handles. Synchronous calls are not caller-interruptible here; even an
asynchronous handle can involve blocking. No guaranteed2s/60s native timeout
or cancellation claim is made; measured60s overrun prevents success.

[GetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle)
provides file attributes, size, links and volume/index identity. The probe also
checks the file pointer and creation time on the same held handles. This is
local handle evidence, not persistent identity after handles close. Attribute
and path reparse uncertainty rejects the experiment.

[GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo)
returns owner/DACL information from a handle; allocated security descriptor
memory must be released with LocalFree. The new backend compares the current
token-user SID privately, requires a protected single owner allow ACE, and
checks normalized handle paths. Buffer/handle release uncertainty is reported
and retained rather than silently marked successful. No account identifiers,
SIDs, file IDs, raw paths or upstream exception details appear in reports.

[GetLongPathNameW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getlongpathnamew)
expands short paths to long forms when possible. TEMP can use8.3 names, so
the approved parent is expanded before comparing GetFinalPathNameByHandleW
results. Failure, UNC paths, parent reparse points or length beyond declared
limits stop; no guessed path normalization or alias acceptance.

Injected tests use the same run sequence and declared budgets but no Win32.
The native backend uses explicit32-bit DWORD/BOOL and64-bit handles; pure tests
check the52-byte BY_HANDLE_FILE_INFORMATION layout. Opens are counted before
calls; successful handles are registered before post-call deadline checks so
an overrun cannot hide them from cleanup. Close attempts happen even after
expiry. No retry, speculative flush, event, pipe, SDK or order interface exists.

The current-user owner assumption does not defend against malicious same-logon
code changing permissions or duplicating handles. The snapshot is stable only
while exclusion handles stay held. Native Win32 success does not certify MQL
flags, regular-file publication, ACK transport, restart behavior of a future
publisher or a native call timeout.062 cannot make060/061 ready for deployment.
See WINDOWS-SHARING-062-RUNTIME-PLAN.md for frozen limits and cleanup behavior.
