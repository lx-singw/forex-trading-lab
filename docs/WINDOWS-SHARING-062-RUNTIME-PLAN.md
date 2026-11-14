# Frozen local sharing probe062 — 2026-10-07

Phase62000000000000000000000000000001 is a synthetic probe identity, not a
capture permission. Verify061 closure, new062 source and interpreter bindings,
one frozen975-test regression and preparation checker before reserving runtime.
Native runtime is one exclusive started report; reserve before loading the new
Win32 backend. No restart/retry/refund after any native failure. Current UTC
date must still be2026-10-07 at reservation and throughout the experiment.

Use existing pinned Windows Python, SHA256
b70275ad94210fce7548761143be5e177769721045e287bb6c80aac3f928c65b.
No MetaTrader5 import/attach/compiler/deployment/logs, native pipes, actual
receipts/permissions, account queries/identifiers, quotes/history/strategy/orders
or settings changes. No external HTTP calls or broker accounts.

Limits: one native session,60s measured overall including cleanup, one newly
created directory below local TEMP, at most two files (implementation uses one),
16 explicit token/CreateFile handle-open attempts, one84-byte WriteFile and
two ReadFile calls each requesting85 bytes. Expected normal count is8 opens
(one token and seven file/directory attempts), five successful handles closed,
three ERROR_SHARING_VIOLATION rejections and two84-byte reads. No event handles,
overlapped IO, retry or flush. Native calls may block: record elapsed overruns
after return; this is not preemption or a guaranteed wall-time maximum.

Prepare the directory with current-user owner and protected owner-only DACL;
reject UNC paths and reparse parents. Expand short TEMP paths using documented
GetLongPathNameW. Hold a directory handle denying deletion and verify normalized
handle path/owner/DACL/no-reparse evidence. File uses CREATE_NEW, explicit
private security and OPEN_REPARSE_POINT; never overwrite any existing file.
Check same-handle volume/index/creation identity, size, link count and pointer,
without exporting identities/SIDs/path strings. Only exact approved own paths
are opened. Parent checks are repeated; same-logon owner trust remains.

Write fixed synthetic bytes once. Require a read-only share-read seal to fail
while the writer is held; close the writer without retry. Seal read-only with
share-read, open a second reader, and verify both bind the same84-byte file.
Attempt writer and DELETE-access opens; require actual sharing_violation,
not generic access_denied. Do not write/delete/rename through those attempts.
Read85 from each held reader; require exact84 matching synthetic bytes and
unchanged identity/size with position84 afterward.

Always attempt one CloseHandle for every successfully opened handle, including
token and directory, even after a measured deadline. Close failure stops success
and retains ownership in process memory; never retry an uncertain handle or
claim closed. Process teardown may ultimately release such handles. Release
allocated security buffers; failed LocalFree also prevents success and retains
the pointer. No pending asynchronous operations or event cleanup is expected.

Retain the one dedicated directory and synthetic file, including on failure;
no recursive deletion or deletion of unrelated files. The exact84-byte content
and observed SHA are bound to the sanitized result, not treated as immutable
after all handles close. No raw native handles, SID, file IDs or local paths
are exported. Preserve stopped/failed source and runtime before any later phase.

After this one run, independently check counters, sharing categories, byte
counts/digest, closure, source/test/runtime hashes and complete predecessor
archive coverage. Win32 success cannot certify MQL FileOpen sharing, snapshot
publication/ACK, blocking timeouts or transport repair. Keep native MQL/capture
activation unavailable. Old failures and all market gates/reserved data remain.
