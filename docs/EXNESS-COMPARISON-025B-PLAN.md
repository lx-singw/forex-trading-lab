# Independent checker archive supplement 025B

Declared after 025's preserved independent-check failure, before 025B execution.
The original checker asserted HistData ZIPs contained only their quote CSV.
Metadata-only inspection instead found, in each original ZIP, the expected CSV
followed by a same-basename .txt member: March CSV88,497,474/text16,392 bytes;
July CSV59,875,257/text13,871 bytes. Both are unencrypted. See sealed
reports/exness-comparison-025-check-attempt.json. No additional network requests.

Keep original checker, ledger, primary review and selected-row lineage unchanged.
Derive a separate checker with only an archive guard replacement, companion
validation helper, supplemental binding verification and separately named
output/kind/ledger reference. Require precisely [declared CSV, same-basename TXT]
in original central-directory order; no unexpected, duplicate, nested, encrypted
or alternate members. Total declared size <=128 MiB, TXT declared/actual size
<=64 KiB. Read TXT boundedly only to verify bytes/CRC/size, never as quotes or
calendar evidence. Existing complete CSV stream reading still verifies its CRC.

No quote/timestamp/price/parser/aggregation/window/tail/criterion changes. Exact
derivation must pass before and after; original script hash is retained. Freeze
new plan, derivation/checker/tests, original ledger/seal/review/seal/lineage,
metadata failure/seal before rerunning. Synthetic tests exercise exact members,
unexpected/oversized/encrypted companions, corrupt companion CRC and derivation.
The checker must again independently rebuild all selected original events,
lineage, hours, minutes, distances and question answers, without primary reader
or aggregation imports. Preserve separate output/seal, including supplemental
ledger hash. Never overwrite the failed attempt or primary comparison outputs.

Annual eligibility, absolute UTC/sessions, upstream independence, executable
costs and profitable edge remain unresolved. No data blending, performance
evaluation, new requests, provider contact, accounts or orders.
