# Sprint 184 · Independent Level B accounting comparison

18 November 2026. The comparison runs the retained 120 and 125 accounts
on their invented fixtures and sends compatible observations to the
Level B price kernel, reservation gates and ledger. A separate
rational-arithmetic calculation checks each projected fill, mark, day
reference, commission, margin, financing debit and closing balance.
[Retained 120 results](../DAILY-FILLS-120-RESULTS.md) ·
[Retained 125 results](../ELLIOTT-EXECUTION-125-RESULTS.md)

## Comparison scope

The projection takes executable observations from the retained entry to
its exit. Each becomes a declared one-hour slot with a constant bid and
spread. The projection preserves ordering, UTC weekdays and elapsed
dates. It assigns new intraday times and uses the slot end as its
receipt time. The retained proposal supplies the original stop and
target. The independent calculation derives size and prices from those
levels, the observed bid and ask, and the fixed cost terms. This tests
accounting and opening-price behavior at matched inputs.

The comparisons cover long and short targets, stop reaches, larger gaps
and wide executable exits under both cost profiles. Retained 125 also
supplies a boundary close, a held signal change and a minimum-lot case.
The same-opening gaps check that a held slot blocks competing attempts.
Repeating margin and free-margin quotients from the old precision-50
decimal ledger use the retained USD 10⁻³⁵ tolerance. Finite cash values
and the independent Level B comparisons are exact.

## Observed results

| Case-and-cost comparisons | Count | Result |
| --- | ---: | --- |
| Shared closed-trade inputs | 33 | Entry and exit price, volume, commissions, financing, exact cash and finite equity agree. The matched closing-quote pause also agrees in 32 cases. |
| 125 minimum-volume abstention | 2 | Both profiles floor below the minimum, skip entry and preserve USD 10,000 cash. |
| 120 weekend financing | 2 | The prices and financing per lot agree, with distinct sized volumes. |
| 125 adverse financing closure | 1 | Level B rejects the spread-to-stop ratio at entry. |

The audit rejects deliberate changes to a mark, financing amount, entry
fee, exit price or pause in a retained boundary example.

## Differences on the retained fixtures

- In 120's weekend financing case, its half-risk signal limits its lot
  size. Level B uses the frozen full 0.25 percent risk fraction.
  Opening and closing prices, financing per lot and weekday multipliers
  agree under both cost profiles.
- In 125's extended financing closure, base trade cash and financing
  agree. The retained quote account books elapsed financing against the
  reference from the previous quote. Level B establishes a reference
  each reconciled UTC day through the declared closure. Those reference
  clocks yield different pause states when the market reopens.
- The adverse profile in that closure fixture proceeds in 125.
  Level B's 10 percent spread-to-stop-distance gate rejects its entry.

The projection takes executable quote status from the retained run.
Source age, repeated quotes, quote-before-signal ordering and legacy
feature selection require their original quote stream. Level B's
receipt-clock gaps, unresolved intrahour order and open liability at a
missing liquidation opening have separate invented regression coverage.
The Level Q adapter and its quote-specific verification remain in Phase 7.

## Verification

All 159 targeted tests passed. The six new tests exercised 38
case-and-cost comparisons and five deliberate report changes in 28.592
seconds. The retained 120 and 125 suites ran 89 checks in 122.681 seconds.
The retained Level B tests ran 64 checks in 133.776 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_account_parity_184 -v
PYTHONPATH=src:tests python3 -m unittest test_daily_fills_120 test_elliott_execution_125 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_ledger_183 test_trendline_risk_182 test_trendline_exits_181 test_trendline_fills_164 -q
```
