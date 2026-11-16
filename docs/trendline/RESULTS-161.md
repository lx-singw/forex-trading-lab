# Sprint 161 — Phase 1 rulebook and invented expectations

16 November 2026 (Africa/Johannesburg). Rulebook and fixture authorship increment
complete; no trendline engine, market replay or native runtime is implemented.
Sprint160 was committed and pushed as b59f81d before this increment began.

## Delivered

- rules-161.json contains34 source-tagged rule records, all24 ambiguity
  resolutions and34 parameter declarations from the protocol, with fixture links.
- golden-161.json contains40 LONG/SHORT pairs (80 explicit scenarios), their
  literal expected outputs and hand calculations. The fixture README indexes
  the rules and explains component versus full-candle evidence.
- Two49-candle invented prefixes exercise pre-existing action/safety structure,
  confirmation timing and hand-calculated ATR/stops. The remaining vectors cover
  rejection boundaries, all eight D1 outcomes, gap losses, sizing/headroom,
  consumption/restart expectations, costs and prospective protection/partition exits.
- Protocol revision2 resolves disabled DLY's at10 expiry and post-rounding target
  qualification before implementation; original160 freeze remains in Git.
- A source reconnaissance note records available leads in response to the user's
  flexible source direction; no old access stop or protected date was reopened.

## Verification

Run `python3 scripts/verify-trendline-fixtures.py` from the repository in WSL.
The retained [summary](verification-161.json) records80 unique scenarios,34 linked
rules, all24 ambiguity/34 parameter records, eight D1 outcomes,20 independent
rational-arithmetic equalities and four crosschecks against the unchanged existing
batch-pivot detector on the full candle fixtures. OHLC bounds also pass.
These counts are fixture checks, not80 passing engine tests or market trades.

The first check found a missing R19 backlink on the unfinished-D1 fixture. The
fixture annotation was corrected before final verification; economic expectations
were unchanged. No broad legacy suite was rerun because frozen runtime was not
changed. Review intended diff and source immutability before commit/push.

## Acceptance and limits

The Phase 1 rulebook and written examples are ready for independent reading.
No second human review has occurred. Component fixtures deliberately declare
pivots/candidate preconditions; they do not establish discovery from candles or
end-to-end execution. Future phases must run them against real implementations
and add integrated constructed paths, rather than treating expected states as
passing software evidence. Viewer-based real examples remain deferred to Phase10.

Source reconnaissance is metadata preparation for Phase 2, not phase acceptance.
No new historical dataset or prospective run is admitted. Current absence of a
permitted source with declared semantics/coverage remains concrete unfinished
work. API price series, local market rows, terminals, accounts and orders were not
accessed. Provider documentation contained incidental undated ticker banners;
their uncertain exposure is recorded, not silently counted as unseen validation.

Protected dates, closed provider routes, expired136, false156 grant, the frozen
Elliott/control graph and unavailable market cells remain in force. Next finish
Phase1 independent readability review and Phase2 source/manifest/bar acceptance;
do not report later phases complete from these fixtures.
