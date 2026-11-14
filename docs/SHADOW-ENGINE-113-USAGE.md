# Shadow engine113 — offline usage

This prototype evaluates **invented quotes only**. It has no broker connection or
order capability. Existing MT5 captures can be inspected, but always return
`performance_unavailable` with their diagnostic status and counts.

From this repository in WSL, create a new local directory, then run:

```sh
mkdir data/my-shadow113-check
python3 scripts/shadow-engine-113.py create-fixture continuation data/my-shadow113-check/continuation.json
python3 scripts/shadow-engine-113.py freeze data/my-shadow113-check/continuation.json data/my-shadow113-check/continuation-frozen.json
python3 scripts/shadow-engine-113.py evaluate data/my-shadow113-check/continuation.json data/my-shadow113-check/continuation-frozen.json data/my-shadow113-check/continuation-report.json
```

Repeat with the predefined `reversal` case and new filenames. Report both cases;
these deliberately constructed paths check software behavior, not a market edge.
Each report contains base/adverse costs and separate development/validation spans.
The earlier span can warm up indicators; validation starts with fresh capital and
no position. The final partial hour is labeled. No future quote supplies an earlier
signal or a development exit.

Inputs, baseline JSON, code and cost settings are bound in the manifest. Changed
inputs/code/config reject; outputs are created exclusively and cannot overwrite
existing artifacts. After a code change, create a new manifest and report, preserving
the originals. Fixtures have explicit invented UTC clocks and quote-age assumptions.
No such interpretation is applied to native captures.

For a copied, closed111 run:

```sh
python3 scripts/shadow-engine-113.py inspect-capture data/forward-capture-112/Run111-1791828959-1048132859-1108 --format 111
```

For107/109 use their exact file path and `--format 107` or `--format 109`.
This performs read-only format/hash/sequence inspection and prints diagnostics.
It never constructs a simulator or computes native performance. Even an invented
label inside a capture cannot unlock this route. No MT5 launch is needed.

The Python `Replay` API supports incremental `step(event)`, `checkpoint()` and
`Replay.restore(fixture_path, manifest_path, checkpoint, scenario, partition)`.
Finish/report only after the partition is exhausted. Replaying the latest identical
event is a no-op; conflicting, missing, older or non-frozen events reject. A restored
checkpoint must match the same fixture, manifest, scenario, partition and corrected
019B equity-metric version. This is software restart handling, not broker reconciliation
or tamper-proof storage. Public input views are defensive copies.

Cost totals reconcile reference gross minus spread, slippage, commission and
financing to actual simulated net P&L. Gross reference uses entry midpoint and
market-exit midpoint; a modeled target-limit exit uses its exact fill reference.
It is an accounting decomposition, not a hypothetical frictionless trade outcome.
Stops use the next observed exit quote plus adverse slippage; gaps can exceed risk
estimates. The simulator's daily pause blocks entries and does not cap losses.

Saved final demonstrations are under `data/shadow-engine-113-invented-demo-r3/`.
Earlier versions remain preserved and their manifests reject under changed code.
Real-money execution and automated orders remain unavailable. Read
[SHADOW-ENGINE-113-RESULTS.md](SHADOW-ENGINE-113-RESULTS.md) for observed checks and limits.
