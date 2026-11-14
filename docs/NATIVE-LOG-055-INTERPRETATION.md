# Native054 returned no reply data

Separate055 audit found one native054 record: requests1, reason23, reply_bytes0,
decode_reason1 (wrong length), receipt_valid=false, quote_reads/orders0. This is
not an expiry diagnosis: the native decoder rejects the length before inspecting
time bounds. The independently retained helper trace reached reply_write and
immediately rejected that operation in94 microseconds, after encoding84 bytes.
The attempted84 bytes were never confirmed as written.

The frozen native source calls FileClose immediately after FileReadArray returns,
then checks its account and decodes the result. Therefore the native script
closed its own handle after its zero-element read. This sequence points to the
native read/connection lifetime as the next investigation target. It does not
prove the exact interprocess timing, raw Windows error or why the read returned
zero. Do not say the2s receipt expired or the user selected the wrong input.

Primary documentation reviewed (three page opens, no searches):

- [MQL5 FileReadArray](https://www.mql5.com/en/docs/files/filereadarray) returns
  the number of array elements read; the uchar array makes the reported count a
  byte count. The documentation does not establish why this pipe read returned0.
- [MQL5 FileReadInteger](https://www.mql5.com/en/docs/files/filereadinteger)
  supports an explicit byte size. It is a potential alternative to test, not a
  documented cure for this particular failure.
- [Microsoft WriteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile)
  documents asynchronous writes and retrieving GetLastError on failure. The
  frozen backend discarded that numeric detail, so it cannot be recovered now.

Next capture strict whitelisted native read/error categories and Windows write
error categories, with synthetic backend tests and a bounded delivery protocol
review before any fresh MT5 trial. Assess exact84-byte read versus current85-byte
read and a bounded receipt-consumption acknowledgment. Preserve exact frame/
binding/receipt/account guards; do not extend receipts, add an unbounded flush or
pretend a successful write proves the client consumed the frame. No native read
change or acknowledgment protocol was executed in055. Any experiment needs a
new fixed phase/date, tests and clean compilation before manual use.

The frozen055 sealer copied a historical title saying Separate051; its body and
all audit/checker bindings identify original054. This title is a transcription
error, not evidence from another run. Preserve that frozen source; this additive
interpretation states the correct identity. Original054 remains failed; the
disabled proof passed, repeat unarmed, one permission consumed, SDK/IO closed,
no price/history/order calls. All prior failures and market gates remain.
