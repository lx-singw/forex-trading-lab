# Use the offline evidence summary129

From the repository in WSL, run either command:

python3 scripts/evidence-summary-129.py

python3 scripts/evidence-summary-129.py --format markdown

The default manifest is [config/evidence-summary-129.json](../config/evidence-summary-129.json).
An explicit manifest and root can also be supplied:

python3 scripts/evidence-summary-129.py /absolute/path/to/manifest.json --root /absolute/project/root --format json

The CLI writes only to stdout. It opens no terminal or broker connection and
never changes source files, captured inputs, simulator costs or availability
settings. The three raw formats are reparsed through their retained inspectors.

The strict manifest accepts only three source roles in order: quotes111,
metadata127 and costs128. Each canonical relative file path and lowercase SHA256
is checked before parsing its bounded bytes. Quote segments must be consecutive
within one run. Direct and ancestor symlinks, escaping/arbitrary paths, unknown
keys, wrong source roles, changed hashes, mixed runs and invalid exports reject.
The run-folder origin must match its export header. A valid hash is integrity
evidence, not authenticated producer identity.

Outputs retain original capture dates and statuses, input hashes, query results,
raw properties/rules, margin factors, clock comparisons and six explicit evidence
gaps. Empty commission rules, failed queries and incomplete payloads remain
distinct. Stopped/partial quote evidence is not promoted to a complete dataset.
No quote streams or account identities are joined across runs.

The captured sources are from 12 and 14 October 2026, not a fresh15 October run.
The dated native probes are expired; this offline tool does not renew or launch
them. Existing simulator assumptions are not imported or replaced. Dollar costs,
USD margin requirements, slippage and source age remain unknown. All market,
paper, order and real-money availability flags stay false.

Saved outputs from this phase:
[readable summary](../reports/evidence-summary-129-summary.md) and
[structured summary](../reports/evidence-summary-129-summary.json).
Read [verification/results](EVIDENCE-SUMMARY-129-RESULTS.md) and
[the reserved plan](EVIDENCE-SUMMARY-129-PLAN.md).
