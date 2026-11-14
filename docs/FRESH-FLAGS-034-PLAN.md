# Offline quote-flag consistency 034 — declared, not executed

033 preserved 13,769 ticks and one H1 bar. All 196 complete 032 records and four
bid OHLC prices agree, but its frozen total-event versus tick_volume comparison
failed (13,769 versus 8,368). Do not change or rerun that comparison.

Freeze new code/tests/protocol and exact 033 snapshot, ledger, originals, checks
and review before processing rows. This is an offline infrastructure diagnostic
informed by 033; no strategy/performance experiment or unseen validation claim.
No native API connection/read, terminal action, download or provider retry.

Use only the complete sealed 033 tick/bar originals and 032 sample originals.
Decode and independently compare all numeric CSV/native binary fields and
original identities. Fixed documented flag constants are BID=2, ASK=4, LAST=8,
VOLUME=16, BUY=32, SELL=64, with no interpretation of remaining bits. Sources:
https://www.mql5.com/en/docs/constants/structures/mqltick and
https://www.mql5.com/en/book/applications/timeseries/timeseries_ticks_mqltick,
checked after 033 returned. Do not infer unknown bit 1024 from forum speculation.

For the explicit half-open raw-label hour, calculate complete flag histogram,
BID/ASK/both/neither counts, known versus remaining masks, and actual consecutive
bid/ask value changes. First row has no predecessor and is separately reported.
List every row identity where BID/ASK flags differ from observed value changes,
including same-millisecond events, without reorder/repair/filtering originals.
Map all 032 complete records to 033 identities again; report ambiguous matches.
Compare H1 tick_volume separately to total events, BID flags and actual bid-value
change count. Equality is a relative hypothesis test, not broker algorithm proof.
Reconstruct bid OHLC for each applicable fixed event definition and report
differences; no search for a mask/definition which makes the bar pass.

Test mask logic, first-row uncertainty, ties, duplicate identities, known/unknown
bits, value/flag disagreement, boundary handling, all-field fidelity, immutability
and no market APIs. Full regression must pass before freezing. Exclusive outputs
under reports/fresh-flags-034-* with seals, independent reconstruction, review
and final source snapshot. Originals stay untouched.

Keep 033 diagnostic_passed=false and fresh/annual eligibility false. No clock
normalization, source blending, cost certification, threshold/risk/candidate
changes or returns. Consumed 2025/reserved Nov–Dec 2026 and provider stops remain
untouched. No orders, real-money toggle, paid services, accounts or contacts.
Larger acquisition still needs a subsequent bounded plan and qualification
review; one hour's flag equality cannot lower data-quality or execution gates.
