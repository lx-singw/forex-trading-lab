# Sprint 192 · Phase 9 account isolation and restart

18 November 2026. Every roadmap row now has a corresponding entry in
the Phase 9 working matrix. The audit tracks the existing tests for
success and failure cases and records the remaining native adapter work.
[Phase 9 working matrix](VERIFICATION.md)

## New evidence

| Invented case | Observed result |
| --- | --- |
| Level B interleaved base and adverse costs | Both ledgers reserve their own attempt at the same opening. One run settles a stop gap and pauses entries while the other still reports its held prefix. Repeating each run returns the same account result and preserves the setup checkpoint. |
| Level Q restart after tightening | The E1 stop tightens at its H4 publication. The later gap settles once, at the modeled `1.08498` exit and its receipt. Resuming from the protected hold agrees with the full run, including the earlier ledger prefix and realized loss in excess of the sizing estimate. |
| Level Q restart after a loss pause | The restored pause stays latched as UTC midnight passes. The first applicable next-day receipt publishes a reference effective at midnight using the reconciled cash. Restoring a checkpoint with a changed pause flag fails. |

The Level Q checks reconstruct saved prefixes against their bound tape.
The Level B check alternates evaluations of the same setup replay and
hourly observations under two independent cost profiles.

## Verification

All 45 targeted tests passed. The three new tests took 85.986 seconds.
The 23 retained Level B risk, ledger and exit tests took 154.044 seconds.
The 19 Level Q replay and independent accounting tests took 161.096 seconds.

```sh
PYTHONPATH=src:tests python3 -m unittest test_trendline_verification_192 -v
PYTHONPATH=src:tests python3 -m unittest test_trendline_risk_182 test_trendline_ledger_183 test_trendline_exits_181 -q
PYTHONPATH=src:tests python3 -m unittest test_trendline_quotes_185 test_trendline_quote_acceptance_186 -q
```

Phase 9 remains in progress. The disabled Tori native boundary still
needs direct evidence for actual account types, ambiguous order
acknowledgements, protective stops after partial fills and restart
reconciliation. This sprint uses invented replay evidence.
