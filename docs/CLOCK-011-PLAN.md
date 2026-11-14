# Independent UTC source probe 011 — 2026-10-01

Preserve failed 007/009/010 reviews, source files and all prior returns. This
stage acquires independent reference quotes and diagnoses clocks; no strategy
returns, source blending, orders, paid services or account creation.

## Bounded public access

Try one ordinary HTTPS request to the public legacy hourly Dukascopy path
`https://datafeed.dukascopy.com/datafeed/EURUSD/2023/06/14/19h_ticks.bi5`.
This is July 14 19:00 UTC in the legacy convention; the month is zero-based.
The earlier widget's 429 remains recorded. This is a separate bounded attempt
at public archives; no retry, proxy, alternate identity, credentials or access
workaround. Stop this provider's acquisition on 403/429 or any other request
failure, preserve the response code and do not switch to Requester Pays S3.

Keep original compressed bytes, request URL, response status, time, length and
SHA256. Reject redirects to another origin, oversized responses, malformed
LZMA, trailing/partial binary records, invalid prices/volumes, timestamp offsets
outside the requested hour and any backward event. Preserve equal-ms records.
Interpret only legacy hourly records, never the daily format. Decode 20-byte
big-endian `milliseconds, ask, bid, ask_volume, bid_volume`, EURUSD prices
divided by 100,000. Validate that offsets fit one hour before aggregating.

Primary provider format reference:
https://www.dukascopy.com/wiki/en/development/data-export/ . It documents UTC
for the current daily format and explicitly warns that legacy files may use
milliseconds from the hour. The URL clock interpretation must also be checked
empirically; the guide alone does not certify our legacy data.

## If the public file is available

Acquire only these additional EURUSD UTC hours, one sequential stream:

- July 14, 2023: 18,20,21 (19 is the probe). This covers the incomplete broker
  hour and its adjacent period without modifying either original source.
- July 7, 2023: 11,12,13. Official employment release at 12:30 UTC:
  https://www.bls.gov/news.release/archives/empsit_07072023.htm . Compare minute
  30 in all three hours. Record every value; a legacy UTC anchor requires the
  12:30 minute to have positive range/count and at least 3x the range and 2x
  the count of both 11:30 and 13:30, with positive controls. A failed or
  inconclusive screen blocks clock approval; no alternate event or relaxation.
- October 29–30, 2023 UTC: October 29 hours 22,23 and October 30 hours 00,01.
  Inspect chronological quotes across the previously recorded source reversal.

All eleven requested files form a diagnostic reference, not complete years
or an independent holdout. Preserve all empty files and failures. Compute
bid/ask aggregates, relative close differences and source bounds, but do not
approve an annual mapping from these few windows. Do not sort or remove the
repeated October hour. Any new normalization needs separately declared scope,
sequence-aware mapping tests and sufficient evidence for that scope.
