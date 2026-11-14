# Offline quote recorder102

This prototype writes a local SQLite journal of invented bid/ask observations.
It has no broker connection or order API. It cannot admit market data to research
or authorize execution. Existing historical MT5 capture tools are unchanged.

From the repository in WSL:

```sh
python3 scripts/quote-recorder-102.py demo /tmp/my-invented-quotes.sqlite
python3 scripts/quote-recorder-102.py inspect /tmp/my-invented-quotes.sqlite
```

Choose a new output filename with an existing parent directory. Creation refuses
existing files, including damaged journals. Demo writes14 invented2030 events,
closes the recorder after seven and resumes it for the remainder. Inspect verifies
the schema, bounded metadata, event chain, replayed quality decisions and committed
head. It reports counts and diagnostic codes; it does not compute returns.

Each observation separates the source timestamp from its UTC receipt timestamp.
Missing observations get an explicit event with no quote. Invalid input fields are
discarded and represented by fixed codes. Repeated identities do not become new
accepted quotes; changed data under a repeated identity is rejected. Distinct
identities with equal source timestamps remain distinct. Decreasing source/receipt
times, old and future quotes are flagged. Long source/receipt intervals are
diagnostics, not a declaration that a market tick is missing; no filling occurs.

SQLite saves an event and its committed head in one transaction. Resume rebuilds
state from events, preserving duplicate identities and clock watermarks. An append
rechecks committed history under a write lock, so another recorder instance cannot
use stale cached state. A writer-lock error fails without a partial event; a caller
may retry the same invented observation after the lock clears.

Default policy allows1,000 events,1,000ms quote age and flags gaps greater than
2,000ms. Policy is immutable for a journal; do not rewrite its metadata to change
limits. The prototype caps policy at10,000 events/60,000ms age/3,600,000ms gap and
files at16MiB. Full history verification on each append is deliberately bounded;
production throughput and file rotation have not been established.

Receipt timestamps are injected for offline testing. A future qualified collector
must stamp receipt at its own read boundary, verify source-clock semantics and
identity rules, and check the actual demo account type around broker reads. It
must never label market quotes as invented or add a market/live toggle here.
Closing the current H.10 route does not repair the old historical gaps or grant
permission for another native090 experiment. Provider qualification and paper
strategy comparisons remain subsequent work.

Integrity hashes are local consistency checks, not source authentication. Full
SQLite/OS/filesystem durability and recovery from real power loss are not proven.
A valid earlier database snapshot or a comprehensively rewritten history is not
made authentic by its hashes. Tests and demo run in WSL; no Windows MT5 integration
or performance claim follows from these results.
