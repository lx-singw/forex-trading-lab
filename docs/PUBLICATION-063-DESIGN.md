# Offline publication and acknowledgment063

Scope: injected file capabilities and temporary synthetic047 reservations only.
No SDK, terminal attachment, native file adapter, compiler, deployment, scripts,
log reread, quotes, history, strategy or orders. Baseline975 tests plus42 new
publication tests. Freeze source before one full regression. Prior062 native
success and earlier failed trials remain immutable. A repeated read-only062
review command reached its exclusive existing-report write and was refused;
no report changed and no native session was repeated. The new controller
verifies that closure without invoking its report-producing action.

## Publication protocol

There is no rename or readiness-marker assumption. A producer exclusively
creates one response file, records its private identity and verifies its empty
state, writes exactly84 bytes, verifies size and position, and closes its writer.
It then acquires a read-only handle sharing only reads, verifies the SAME file
identity, trusted owner/sandbox/no-reparse/single-link state, exact size, and
exact bytes. Only after this seal is established may the consumer open its
read-only handle. The consumer independently checks identity/size/position,
bytes and held write/delete exclusion before and after reading. A replacement
between writer close and seal acquisition fails; this design does not prevent
that gap or claim atomic publication. Existing files fail CREATE_NEW and are
never overwritten, adopted, removed or replayed.

047 issuance is unchanged: a one-use allowance burns before validation and
delivery and an exclusive reservation blocks restart. The response must pass
the frozen047 phase/policy/permission/UTC/boot decoder. Slow full guards before
issuance belong to the900s session; publication after issuance and all ACK work
share the original maximum2s receipt lifetime. Full guard checks run before and
after every injected operation, including snapshots. No identity-hash caching
or reduction of eventual native account/process/image/logon checks is proposed.

ACK is a separate exclusively created40-byte file: existing060 magic plus the
SHA256 of the exact response. It follows the same write/close/seal/read protocol.
The response seal and consumer handle remain held through ACK checks and final
pre-cleanup validation. Both files must retain the same identities, sizes,
positions, privacy and exclusion proofs. Missing, stale, corrupt, partial or
lost ACK fails without refund. Cleanup runs even after expired clocks or proof
failure. Unconfirmed handle closure or retained operations invalidate completion.
Once handles close, leftover files are inert evidence: no restart/resume path.

Finite budgets: two create attempts, two writes, two writer-close attempts, two
seals, two consumer opens, four reads and32 snapshots; each attempt burns before
guard/call. No polling, flush or sleep loop. The injected adapter must register
handles before any post-acquisition failure, close only its own handles once,
retain uncertain handles until process teardown and report uncertainty. Calls
can block; checking clocks after return detects lateness but cannot preempt IO.
Successful cleanup is checked against the same receipt deadline.

The reference model trusts injected capabilities; it does not establish OS
proof, authenticated signaling, actual MQL-to-Win32 handle mapping, durability
after power loss or coordinated native ACK publication. Same-user malicious
processes are outside an owner-only ACL's protection. The protocol carries no
market data and no accepted model receipt can activate native capture.

## Native MQL feasibility and next experiment

MetaQuotes documents FILE_READ as opening an existing file, FILE_BIN as binary
mode, FILE_SHARE_READ as shared readers and FILE_SHARE_WRITE separately.
FILE_WRITE can recreate a file at zero size. Use exactly
FILE_READ|FILE_BIN|FILE_SHARE_READ (133) in the later synthetic reader; omit
FILE_COMMON, all write flags and string conversion. Paths resolve inside that
terminal's MQL5\Files sandbox. These declarations alone do not prove the
installed build's Windows access/share mapping.
[MQL flags](https://www.mql5.com/en/docs/constants/io_constants/fileflags),
[FileOpen](https://www.mql5.com/en/docs/files/fileopen).

Windows sharing compatibility checks both existing and new handles; exclusion
lasts while handles stay open. Stage062 measured one84-byte write (not184
bytes), two84-byte reads, writer/delete sharing violations and closed handles
in its synthetic Windows case. A later MQL probe must corroborate the same
contract while both Windows and MQL readers are present, using actual error32
for attempted writer/delete opens rather than interpreting access denial as
sharing proof. [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

064 preparation will freeze default-off synthetic MQL reader source, fresh
phase/date, strict actual DEMO/USD/Algooff guards, full private Windows image/
process/account/logon/sandbox checks and bounded launch/IO/compiler/deploy/log
budgets before any native action. Its84 bytes must deliberately lack047 receipt
magic. It tests sharing only, not this receipt/ACK protocol. The MQL handle must
remain open through a bounded observation interval; Windows checks the held
file throughout. No SDK/terminal actions are authorized by063 design itself.
See NATIVE-SHARING-064-PLAN.md. If native sharing fails, preserve that stop and
do not manufacture a permission or accept partial data.

Clock/cost/coverage/flag qualification,033/035 failures, consumed2025 holdout,
reserved Nov–Dec2026 and provider stops remain. Fresh and annual performance
eligibility and automated orders remain false. Transport tests imply no profit.
