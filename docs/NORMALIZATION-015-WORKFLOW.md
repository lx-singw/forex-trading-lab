# Diagnostic normalization workflow

Run from this repository in WSL. This workflow makes a separate diagnostic
representation of the already-acquired 2020–2023 quote archives. Original bytes
stay intact. It does not approve annual history or compute strategy returns.

The declared plan is `NORMALIZATION-015-PLAN.md`. The ledger and source archive
are `reports/normalization-015-ledger.json` and
`reports/normalization-015-source.zip`; source changes invalidate the job.

```bash
PYTHONPATH=src python3 scripts/correct-clock-013.py verify
PYTHONPATH=src python3 scripts/normalize-history-015.py verify
```

Run both preflight checks before any reuse and again at completion. The first
checks the archived reader/correction dependency chain; the second checks the
new normalizer and all 48 inputs. Completed-month seals additionally bind
diagnostic output bytes. Neither command certifies annual clock or sessions.

The initial freeze has already been completed. Do not freeze again or duplicate
an active year job. Each year writes distinct source-month folders under
`data/normalization-015`:

```bash
PYTHONPATH=src python3 scripts/normalize-history-015.py run-year --year 2020
PYTHONPATH=src python3 scripts/normalize-history-015.py run-year --year 2021
PYTHONPATH=src python3 scripts/normalize-history-015.py run-year --year 2022
PYTHONPATH=src python3 scripts/normalize-history-015.py run-year --year 2023
```

The four independent year jobs may run concurrently. Within a year, months are
processed sequentially. Resume validates frozen source/evidence plus all hashes
of completed months before reuse. A partial month causes rejection; it must
remain available for diagnosis and requires a separately declared recovery
instead of silent overwrite. Successful provenance and its seal are written
only after the full source stream and row count reconcile.

Each monthly bundle contains:

- `ticks.csv.gz`: diagnostic quotes, original row numbers and candidate labels.
- `inventory.json`: observed hourly bid/ask prices, counts, spreads and gaps.
- `provenance.json`: source/output hashes, exact replay correspondence and limits.
- `seal.json`: provenance hash for completed-month checks.

Only the second exact October replay is collapsed. Original archives retain
both copies. Ordinary duplicates, equal timestamps, volumes and all gaps remain.
Candidate calendar-year edges are retained in their original source-month file.

After all months complete, review all 47 seams and candidate hourly coverage:

```bash
PYTHONPATH=src python3 scripts/normalize-history-015.py review
```

Independently reread CSV, reconstruct bid/ask hourly aggregates and check exact
payload, lineage and candidate-calendar arithmetic for each year:

```bash
python3 scripts/check-normalization-015.py --year 2020
python3 scripts/check-normalization-015.py --year 2021
python3 scripts/check-normalization-015.py --year 2022
python3 scripts/check-normalization-015.py --year 2023
```

These checks write new exclusive reports; do not repeat a completed check into
its existing destination. They verify conversion and aggregation, not source
accuracy or completeness. The weekday quote-free list is a watchlist, not an
authoritative forex session calendar. Weekend-looking gaps remain unclassified.

Files use kind `diagnostic_candidate_ticks_015` and candidate timestamps. The
performance reader requires a different annual format and explicit evidence
for clock, lineage, corroboration and unresolved open-session gaps. This stage
creates neither its approval nor its bundle. Earlier clock and July failures
remain unchanged. Historical costs are still modeled, and orders unavailable.
