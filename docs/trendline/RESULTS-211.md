# Sprint 211 · Clock-based publication from source timestamps

19 November 2026. An explicitly modeled clock can publish a shortened
Friday H4 during the weekend closure when every scheduled child H1 is
present at finalization. The prototype uses invented source-only quote rows.
Historical receipt order remains unverified. [Receipt review](RESULTS-210.md)

## Modeled publication

The diagnostic takes an `invented_clock_publication_source` with a `calendar`,
the weekend `h4_end`, an `assumed_delivery_delay_ms`, and source-ordered
`quotes`. Each quote supplies `source_at` in epoch milliseconds, `bid` and
`ask`. The model adds the declared nonnegative delay to each source timestamp.
Sequence follows input order, including ties. These receipt times are generated
by the scenario. Archived source labels alone cannot establish actual receipt
times or bound actual delivery latency.

The effective finalization delay is the greater of the calendar delay and
the assumed delivery delay. Since a child quote belongs to the half-open
source window, all its supplied source rows fall before that modeled
deadline. The existing aggregation publishes the H4 at finalization when
all scheduled H1 children are available. A missing child keeps the parent
unavailable. Quotes at or after the Friday closing boundary, including
Sunday quotes, cannot revise the Friday bar. Qualification would still need
archive coverage and a justified calendar and clock. [Frozen entry rule](PROTOCOL.md#c4-entry-and-data-level-semantics)

The report binds the input, original calendar, modeled calendar and H4
midpoint lineage. It lists unpublished children at the cutoff and shows
the opening check separately. The midpoint is used only for this diagnostic.
The strict opening check requires source and modeled receipt at the scheduled
boundary, using a paired bid and ask if present. Availability of the H4
alone supplies neither a strategy decision nor an opening price. [Opening evidence](RESULTS-205.md)

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline.clock_publication \
  invented-source.json new-report.json --as-of EPOCH_MILLISECONDS
```

## What the Exness summaries can establish

The nine retained January and July Sunday first labels are 17.540–268.088
seconds after the modeled Sunday opening. Under the candidate label mapping,
adding any nonnegative delivery delay leaves **0 of 9** at the exact opening.
The summaries lack the Friday child coverage needed to report a reconstructed
historical H4. The two invented verification cases both publish before Sunday.
The exact source label with zero modeled delivery produces opening evidence.
The later source label with a five-second modeled delivery delay leaves the
opening unavailable. These cases exercise the diagnostic without new market
prices. [January diagnostic](RESULTS-203.md) · [July diagnostic](RESULTS-204.md) · [Calendar check](RESULTS-208.md)

## Verification and disposition

The CLI exercises the exact and late opening cases and binds their input
hashes. All 141 targeted publication, opening, fill, session, coverage and
signal-count tests passed. The canonical Phase 10 preflight still reports
`UNAVAILABLE` with null actual counts. Historical use requires an admitted source and a reviewed
calendar, shortened-bar and availability model. For these sampled weekends,
the exact-quote method supplies no opening price under the modeled schedule.
A separately declared Level B bar-open approximation would need qualified
price and spread construction and timely decision order. No market or
validation files were opened, and no provider message was sent.
