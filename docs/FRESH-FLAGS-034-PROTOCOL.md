# Offline flag protocol 034

Implements the unchanged FRESH-FLAGS-034-PLAN.md. No market API is imported or
called by the new audit code. Existing script helpers are loaded as definitions
only; no prior collector run/checker main is invoked. No terminal/network action.

Run scripts/test-fresh-flags-034.py before scripts/fresh-flags-034.py freeze.
Verify all 990 prior bindings, 948 ZIP members and 42 external inputs. New ledger
binds code/tests/protocol/plan/test report, exact 033 snapshot/ledger/checks/review,
all seven 033 originals, all five 032 originals and the immutable independent
033 decoder. Verify this ledger before exclusively reserving audit outputs.
No original rows are processed before freezing; tests use synthetic inputs only.

The primary reader requires exact frozen numeric 60-byte layouts, compares all
eight native/CSV fields plus hashes, rows and byte counts, and never writes to
original folders. Use raw labels only: 1791291600000 <= time_msc < 1791295200000
for hour statistics. Preserve input order, tied labels, duplicates and boundary
identities. Report outside-request identities without inventing a repair.

Fixed flag constants: BID=2, ASK=4, LAST=8, VOLUME=16, BUY=32, SELL=64; known mask
126. Remaining uint32 bits are reported numerically with no interpretation.
Record complete histograms and bid/ask/both/neither counts. Compare each row to
its immediate original predecessor (never a filtered predecessor), listing both
complete records and source indices for every BID/ASK flag-versus-value mismatch.
First original row has no predecessor: no change assertion is possible. Include
it explicitly only in the two definitions named with_first. Report transitions
separately, so first-row inclusion cannot masquerade as an observed change.

Seven definitions are fixed before processing: all events, BID flag, ASK flag,
both flags, neither flag, actual bid changes with first row, actual ask changes
with first row. Compute event indices, bid OHLC and price/count deltas to the H1
bar for each. Empty subsets/unavailable bars get explicit unavailable comparisons.
No mask search or adaptive event definition. Map each complete 032 tick against
all eight 033 fields; keep all matching source indices and report ambiguity.

Run scripts/fresh-flags-034.py run once; reserve an exclusive sealed report first.
It writes sealed reports/fresh-flags-034-audit.json. After completion, run
scripts/check-fresh-flags-034.py. This checker uses the immutable 033 field decoder
plus direct 032 binary/CSV reconstruction, and separate set-based computations
for every histogram, definition, disagreement identity, full-record witness and
comparison. It compares every reconstructed report field and all original hashes.
No new input/output can overwrite a sealed artifact. Preserve failures explicitly.

16 new tests cover masks, unknown bits, first-row uncertainty, both mismatch
directions, ties/duplicates, full-record ambiguity, boundary/outside rows, fixed
subset OHLC/counts, empty bars, chronology/numeric validation, exact binary/CSV
fidelity, mutation detection after rehash, read-only originals, independent
synthetic reconstruction and absence of market API calls in new sources.

Post-audit review and snapshot preserve original 033 diagnostic_passed=false.
Equality for a newly declared fixed count definition is an observational result,
not a replacement 033 success rule or proof of provider algorithm/completeness.
No clock conversion, cost/edge certification, eligibility promotion, returns,
risk/candidate changes or orders. Consumed 2025/reserved Nov–Dec 2026, existing
provider stops, account/privacy constraints and disabled execution remain intact.
