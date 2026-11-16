# Source review165 — candidate identified, history not admitted

16 November 2026. Followed [the bounded slice](SOURCE-165-PLAN.md):3 discovery
searches,3 primary-page opens,4 text finds and1 unauthenticated metadata-URL
attempt. No price-series request, download, account signup, purchase, provider
message, credential-file scan, native run or order action.

## What the new evidence supports

The current [Twelve Data pricing page](https://twelvedata.com/pricing) lists Basic
as free, with internal non-display use and forex data. This improves the free
access/use lead; it does not establish EURUSD H1 history, its bid/ask semantics,
the applicable retention period or actual entitlement for this project.

The [personal/commercial-use guidance](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage)
describes research/testing uses for individual plans and separately discusses
programmatic internal-AI use under Pro. How those statements apply to this
agent-assisted research still needs review; no conclusion that a paid plan is
required or that Basic covers every intended use is made.

The [terms, sections2.2-2.3](https://twelvedata.com/terms) tie storage/non-display
permissions to plan conditions and documented retention limits. This source
cannot become admitted merely from a free-pricing headline. These are dated
document observations, not a legal opinion or a permanent finding about permission.

The previously inspected [composite-feed description](https://support.twelvedata.com/en/articles/12528665-how-the-composite-currency-feed-works)
still supports a composite-midpoint lead. It does not certify the historical H1
endpoint's exact fields or supply broker bid candles and entry spreads. Treat a
mid-only export as geometry evidence; the current protocol cannot manufacture
executable bid/ask prices from it.

## Metadata-access result

The one attempted URL was Twelve Data's earliest_timestamp endpoint with
symbol=EUR/USD and interval=1h, without a key, account identifier or date query.
The web tool reported that the URL was not accessible via that tool. No provider
HTTP response or metadata body was established. This is not a certified401/403,
a finding of forbidden access, or proof that the service is unavailable.
No retry, alternate transport or price request followed.

The specifically named TWELVEDATA_API_KEY variable was absent from this WSL
process environment. Its value was never disclosed, and credential files and
Windows/private account state were not inspected. This does not establish that
the user has no export or access configured elsewhere.

Discovery also returned third-party Dukascopy/FXCM-derived downloaders and paid
or short-trial products. They were not opened, installed or run. A new client or
mirror is not permission to bypass a stopped upstream route. No market source
was substituted through these results.

Provider pages/search displays included incidental undated EURUSD banners or
illustrative rows. Their dates/basis are not certified; no values are copied
here or used for research. Record this in the exposure review instead of silently
claiming that an overlapping validation scope remains untouched.

## Concrete remaining dependency

Phase2 needs an explicitly identified, permitted historical export/access with
source/time/price/spread/coverage evidence and a reviewed chronological scope.
The [canonical source/run plan](../../config/trendline-study-v1.json) is ready to
record those facts and test restrictions; it currently assigns none.

An existing EURUSD H1 bid-plus-entry-spread export, or another permitted source
with compatible executable-side evidence, is actionable. A Twelve Data export
or working access is a candidate for checking geometry/history, with execution
semantics still to establish. Keep keys in private local configuration, never
chat, code, reports or Git.

New prospective collection remains a possible separately qualified route. It
requires the outstanding native/source/date/run work and cannot provide years
of already-existing history today. No grant or capture dates are renewed here.
Actual-source qualification is the remaining Phase2 dependency; further invented
strategy components cannot supply the missing external evidence.
