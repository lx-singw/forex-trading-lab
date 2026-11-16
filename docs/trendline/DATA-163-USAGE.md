# Phase 2 data boundary — sprint 163

This interface accepts explicit invented Level B fixture files only. It has no
network, credentials, broker transport or market-price admission path. It reuses
the unchanged calendar and aggregation interfaces in elliott_sessions_146.py.

## Metadata plan

The checked-in config/trendline-data-163.json assigns no provider or dates. Its
assessment is metadata lint, not a full study preflight or admission. Complete
self-authored evidence hashes still leave all28 market cells UNAVAILABLE.

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline assess-plan config/trendline-data-163.json
PYTHONPATH=src python3 -m forex_demo_lab.trendline draft-plan NEW-PLAN.json
```

Unknown fields, inconsistent level/geometry/spread claims and malformed values
reject. Consumed/quarantined/reserved dates are diagnosed in warmup as well as
funded scopes, and seen2024 cannot silently become untouched validation. Source
permission, coverage, true prior exposure, minimum study lengths, warmup/trial
budgets and costs still require the separately reviewed study/run preflight.

## Invented input descriptor

The descriptor contains exactly: schema=TRL_DATA_163_V1,
kind=invented_trendline_source, symbol=EURUSD, data_level=B, geometry_basis,
spread_semantics, partition, input_sha256 and calendar. No arbitrary paths,
identifiers, credentials or source-qualification flags are allowed fields.

- bid_only pairs with constant_per_h1_assumption: explicit invented bid candles
  with a constant-within-H1 spread assumption, not verified historical spread.
- mid_candles_source pairs with not_available: supplied invented midpoint candles
  are geometry input only; no executable bid/ask side is fabricated.

The calendar is146's explicit invented2000-2003 schedule with H1/H4 session edges,
D1 boundaries, closures and finalization delay. Declared23/25-hour and partial
sessions are supported; they are not evidence of a real provider's DST calendar.
Every row in the separately supplied hours JSON list contains start, end,
available_at, open, high, low, close and spread_pips. Prices/spreads are bounded
decimal strings; mid-only spread is null. No float, NaN, guessed offset,
interpolated missing child or averaged bid/ask extreme is accepted.

The file SHA binds raw input bytes. Parent lineage binds the fixed geometry/
calendar and observed children; it deliberately excludes the whole-file SHA so
appending a valid future suffix does not rename earlier causal inputs. The full
file/declaration and implementation/protocol hashes remain in the report.

## Loading, publication and validation access

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline inspect-invented SOURCE.json HOURS.json NEW-OUTPUT-DIRECTORY
```

An optional --as-of integer uses the descriptor's millisecond clock. Only rows
available by that cursor are replayed. All supplied rows are checked for a valid
receipt-ordered prefix before use, so malformed future input rejects the dataset;
valid future value changes cannot alter earlier published bars. Equal-receipt
observations retain supplied row order and are included atomically by this
timestamp-only inspection; it does not claim quote-level sequencing precision.

Missing scheduled children block only their affected parents. A late child can
publish a parent at its receipt, never backdate its visibility. Declared closures
are distinguished from missing observations. A rejected duplicate, malformed row
or backward clock leaves the observation state unchanged. Reports identify missing
starts, due/complete counts, B level, geometry basis and execution-data limits.

Validation fixtures need a matching, explicitly written receipt before the hourly
file is opened:

```sh
PYTHONPATH=src python3 -m forex_demo_lab.trendline unlock-invented-validation VALIDATION-SOURCE.json NEW-RECEIPT.json
PYTHONPATH=src python3 -m forex_demo_lab.trendline inspect-invented VALIDATION-SOURCE.json HOURS.json NEW-OUTPUT-DIRECTORY --unlock-receipt NEW-RECEIPT.json
```

The receipt binds descriptor, input SHA and scope. It is a self-authored audit
record for invented software verification, not authenticated user approval,
market-data qualification or permission to access protected prices. Market kinds
are rejected before this branch. No switch promotes a market manifest to a fixture.

Reads are explicitly named and bounded; symlink paths and duplicate JSON keys
reject. New outputs refuse existing files/directories. These are ordinary local
integrity checks, not a hostile-filesystem security guarantee or atomic snapshot.
Large generated inputs/reports remain under ignored reports/ or data/.

## Current limit

This increment publishes bars/coverage. The Level B entry/exit-price model is the
next Phase2 slice, with adverse intrabar ambiguity and no pre-fill stop. There is
no strategy, account ledger, order submission, persisted stream checkpoint or
qualified market reader here. Mid-only geometry, fake terms or an invented
validation unlock cannot satisfy a historical-performance or demo gate.
