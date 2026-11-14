# Raw and derived data policy proposal 036 — not implemented

Preserve every acquisition as a separate immutable observation: complete native
and numeric CSV records, source row order, request/receipt bounds, numeric SDK
status, runtime/schema/contract metadata and hashes. Retain old and new versions
when any field changes. Never overwrite, merge or silently repair originals.

Full-record identity uses every original field, including the complete flags.
Missing/ambiguous identities and revisions remain explicit. Ordered overlap
comparison is an additional claim with its own checked scope; it cannot replace
complete-record matching or retroactively pass033/035 diagnostics.

If a later declared stage creates derived data, name each transformed field and
bind its source revision/hash and original row identity. A documented known-mask
column would coexist with full original flags and uninterpreted remaining bits.
It must not masquerade as the original flags or prove why those bits changed.
No such column is published or transformation implemented by036.

Keep raw labels separate from any later UTC/session transformation. Independent
clock calibration and provider-specific historical timezone/DST evidence must
precede a new, explicit normalization protocol. Do not subtract a convenient
three-hour offset solely from current quote receipts or generic API documentation.

Current symbol metadata and returned bar spread/volume are observations. They
must not replace date-effective executable bid/ask, fees, swaps, conversion and
slippage evidence. Any later simulation must retain stated cost assumptions,
uncertainty and chronological lineage without consuming reserved data.

This proposal changes no gates, candidates, risk limits, source files, account
settings or strategy returns. Fresh/annual eligibility remains false, orders
unavailable, consumed2025/reservedNov–Dec2026/provider stops unchanged. A later
implementation/acquisition/publication requires a separately bounded plan and
qualification review; no live mode is introduced.
