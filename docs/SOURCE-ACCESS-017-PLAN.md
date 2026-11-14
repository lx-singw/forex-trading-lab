# Bid/ask source feasibility — 2026-10-06, before provider metadata requests

Supplement LABELS-017 primary-source research, without quote downloads.
FXCM's own TickData README lists weekly EURUSD archives for 2019–2023 and UTC
timestamps. The repository's main README instead asks for an email request.
Preserve this conflict; neither page establishes present download availability.
TrueFX's own historical page requires login/registration; do not register,
authenticate, create an account or message either provider. Dukascopy stays
stopped after 011. Existing HistData/broker evidence remains ineligible.

Use exactly one ordinary HTTPS HEAD request per URL below, sequentially, timeout
30 seconds; no response body, automatic retry, GET fallback or identity change.
Stop all further FXCM archive requests on 403 or 429. Record URL, timestamp,
status, content type/length and transport errors in separate exclusive outcomes.
Only these metadata fields are needed; do not log account identifiers/cookies.

- https://tickdata.fxcorporate.com/EURUSD/2023/12.csv.gz
- https://tickdata.fxcorporate.com/EURUSD/2023/13.csv.gz
- https://tickdata.fxcorporate.com/EURUSD/2023/28.csv.gz

These documented year/week resources are potential coverage for the March
transition and July14. Actual date bounds and the provider's week convention
are not established by HEAD or assumed from ISO week numbering. HTTP200 proves
only a successful metadata response, not valid quote bytes, complete coverage,
independent upstream provenance or executable spreads. A future acquisition
must separately declare file/byte/request bounds, parse UTC bid/ask strictly,
preserve originals/lineage and review full data chronology/gaps before use.

No paid service, account creation, emails, orders, terminal settings, source
blending, annual approval or performance evaluation. No 2025/reserved 2026 data.
