# Metadata127 native capture results — 14 October 2026

The requested manual launch produced one closed, complete export. The frozen
inspector accepts it, and its CLI and library agree. Independent review of the
original bytes agrees on every query outcome, property, clock group, session
and quote. The original 11,627 bytes are retained unchanged.

There are 100 digest-linked frames: one header, 49 attempt/outcome pairs and a
normal end record. All 49 outcomes are present. **42 queries succeeded**; seven
session-index queries returned false with error 4307. All **33 metadata
properties succeeded**. No pending attempt, partial tail or session truncation
was found. Recorded origin-to-end elapsed time is 5.815 milliseconds; this is
not a general latency or interruption guarantee.

The complete export, its location alongside the matching deployed program, its
file times and the user's launch confirmation provide runtime evidence for this
diagnostic. The unkeyed digest chain is integrity evidence, not authenticated
producer identity or independent proof of every account guard evaluation.

## Current reported metadata

| Property | Reported value |
|---|---:|
| Account leverage | 10, meaning 1:10 |
| Contract size | 100,000 |
| Digits | 5 |
| Point / tick size | 0.00001 / 0.00001 |
| Tick value for profit / loss | 1 / 1 |
| Minimum / maximum / step volume | 0.01 / 500 / 0.01 |
| Volume limit | 0 |
| Initial / maintenance margin fields | 0 / 0 |
| Margin currency | EUR |
| Long / short swap values | -0.7 / -1 |
| Swap mode | raw enum 1 |
| Three-day rollover day | raw enum 3 |
| Sunday–Saturday swap ratios | 0, 1, 1, 3, 1, 1, 0 |
| Custom symbol / subscription delay flags | 0 / 0 |

These are current reported fields, not certified historical contract terms.
The swap enumeration identifies points mode; the day enumeration identifies
Wednesday. The reported ratios also show Wednesday's factor 3. No USD financing
charge is inferred here. Zero margin fields do not mean margin-free trading,
and a reported zero volume limit does not replace the bot's own position limits.
[MetaQuotes symbol-property reference](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)

The five successful weekly session rows report 0–86,400 raw seconds for Monday
through Friday. Sunday's and Saturday's index 0, and each weekday's index 1,
return error 4307. The documented meaning is an invalid session index. This is
not a certified holiday/closure calendar.
[MetaQuotes runtime errors](https://www.mql5.com/en/docs/constants/errorswarnings/errorcodes)
The session API reports times relative to midnight and says to ignore the date.
No UTC session conversion is made.
[MetaQuotes session API](https://www.mql5.com/en/docs/marketinformation/symbolinfosessiontrade)

## Clock-domain evidence

Both clock groups contain the same numeric labels:

| Clock | Raw seconds | Label rendered without a timezone claim |
|---|---:|---|
| TimeGMT | 1,791,996,049 | 2026-10-14 16:40:49 |
| TimeLocal | 1,792,003,249 | 2026-10-14 18:40:49 |
| TimeCurrent | 1,792,006,849 | 2026-10-14 19:40:49 |
| TimeTradeServer | 1,792,006,849 | 2026-10-14 19:40:49 |

The server-versus-computer-GMT numeric difference is exactly **10,800 seconds**;
the local-versus-GMT difference is 7,200 seconds. Reported GMT offset is -7,200
and daylight-savings adjustment is 0.

TimeCurrent is a server-generated latest-quote time for any selected symbol.
[MetaQuotes TimeCurrent](https://www.mql5.com/en/docs/dateandtime/timecurrent)
TimeTradeServer is a client-calculated estimate affected by computer settings.
[MetaQuotes TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver)
TimeGMT derives from the computer's local time and DST.
[MetaQuotes TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt)

**Inference:** these observations support a server/computer clock-domain
difference as an explanation for the earlier roughly three-hour discrepancy.
They do not prove bad prices, a three-hour quote age, a certified UTC offset,
the broker's timezone rules or their historical/DST behavior. No timestamps are
shifted, and old captures remain unchanged.

Both EURUSD reads returned the same source millisecond label 1,792,006,848,893
and bid/ask 1.11184 / 1.11184, with raw flags 1028. The raw source-minus-GMT
receipt difference is 10,799.893 seconds. Relative to the recorded TimeCurrent
label it is -107 milliseconds; this arithmetic is not an executable quote-age
estimate, since TimeCurrent can belong to another selected symbol. The two
quote reads were only 3.624 milliseconds apart. Their equality does not
establish a frozen feed, and their zero reported spread is not a zero-cost
trading assumption. Unknown flag bits remain unclassified.

## Preservation and availability

The native file was read using an exclusive read handle and copied byte-for-byte
into ignored canonical storage. A later native hash recheck must agree.
All 586 source/config/test files, 62 earlier native inputs and the preparation
records are retained. No source or financial rules changed, so the prior
19 Python tests, 179 new C++ checks, 48 shared-guard checks and earlier financial
checks remain retained evidence rather than newly rerun tests.

[Inventory](../reports/metadata-probe-127-capture-inventory.json),
[inspection](../reports/metadata-probe-127-capture-inspection.json),
[independent metrics](../reports/metadata-probe-127-capture-independent-metrics.json),
[read-only review](../reports/metadata-probe-127-capture-readonly-review.json).
The [capture source closure](../reports/metadata-probe-127-capture-final-source.json)
and [completion review](../reports/metadata-probe-127-capture-completion-review.json)
preserve this capture and the previous handoff bodies.

This observation does not repair historical gaps or qualify commission,
slippage, quote freshness, UTC, calendar coverage or strategy performance.
Market, forward-paper, order and real-money availability remain false.
No strategy returns were computed and no orders were placed. No contacts,
accounts, paid services, terminal settings, SDK initialization or historical/
reserved replay were used. October remains quarantined, November–December 2026
reserved and 2025 consumed. The old dated capture routes are not renewed.

## Next concrete work

Check the installed compiler's support for the documented read-only
SymbolInfoCommissions API before preparing a bounded, default-off diagnostic
for current commission rules and directional margin rates. A reported empty
rule list must stay distinct from a failed query and from proven zero trading
costs. This native capability is documented; its availability in the installed
compiler and demo feed has not yet been checked.
[MetaQuotes commission API](https://www.mql5.com/en/docs/marketinformation/symbolinfocommissions)
[MetaQuotes margin-rate API](https://www.mql5.com/en/docs/marketinformation/symbolinfomarginrate)

Further source-time work should observe quote and clock labels together over a
short bounded interval, retaining raw values and receipt boundaries. That can
test the clock-domain hypothesis without changing old data or claiming UTC
certification. No further MT5 launch is needed to finish this capture review.
