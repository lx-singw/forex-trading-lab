# Forward input eligibility134 usage

From the canonical WSL repository, with Python3.11 or newer:

```sh
python3 scripts/forward-eligibility-134.py --format markdown
python3 scripts/forward-eligibility-134.py --format json
```

The default manifest pins the existing133 quote manifest and the separate127
metadata and128 cost files. The CLI checks local bytes through their frozen
readers and prints an assessment. It does not write captures/state, collect
quotes, connect to a terminal, construct a financial simulator or place orders.
Bad input yields a generic rejection, exit code2 and no assessment on stdout.

The report contains separate run audits, actual marker spans and a geometric
upper bound on whole H1 intervals, current reported context, unchanged
hypothetical model/cost scenarios, prospective planning counts and concrete
evidence requirements. The available observations cannot qualify themselves
for strategy evaluation. There is no override or manual qualification switch.

The library entry point is `assess(root, raw_manifest_bytes)` in
`forex_demo_lab.forward_eligibility_134`; set PYTHONPATH=src for a checkout.
The supplied manifest must match the documented schema and bind the actual
input hashes. It cannot insert time corrections, account joins, claimed fees,
qualification flags or alternative planning counts. New source contracts or
protocol changes need a separately reviewed implementation, rather than
editing old captures or their pinned manifests.

Focused invented-input checks:

```sh
PYTHONPATH=src:tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  test_forward_eligibility_134 test_paired_replay_133 test_paired_capture_132 \
  test_metadata_probe_127 test_cost_probe_128
```

The 1,161-hour engineering target does not schedule collection or establish
statistical sufficiency. October remains quarantined; November–December stays
reserved and untouched. No MT5 click or rerun of an expired script is needed.
