# Local invented demo — one command

Use Python3.11+ standard library in the canonical WSL checkout. This fixed local
package needs no terminal, broker, credentials or account. All six cases run;
there is no strategy, cost, market-input or live-mode option.

From the repository in WSL:

```bash
python3 scripts/engine-demo-123.py demo data/engine-demo-123-example
```

Or from Windows PowerShell:

```powershell
wsl.exe -d Ubuntu --cd /home/lx_singw/projects/forex-demo-lab python3 scripts/engine-demo-123.py demo data/engine-demo-123-example
```

The output must be a new directory beneath this repository's data/. Open its
`REPORT.md` for all96 toy comparisons, exact unavailable reasons, costs and the
dated readiness inventory. `overview.json` retains full per-account statistics.
The case folders retain original input/freeze, derived quote/bar/fill inputs,
aggregation, full ledgers and cursor0/1/2 checkpoints. Package source/input and
readiness bindings are in `package-frozen.json`; progress is append-only.

If interrupted after the package freeze, resume with the same directory:

```bash
python3 scripts/engine-demo-123.py resume data/engine-demo-123-example
```

Completed cases are verified/rebuilt before continuation. Incomplete partition
attempts remain preserved; the next numbered attempt is used without counting
the partition twice. An interruption before the manifest or before a run owner
marker exists cannot resume: preserve that directory and choose a new output
name. Do not edit or remove artifacts to force recovery. Completed resume is
idempotent. There is no power-loss durability or outside-interference guarantee.

To check a completed package without writing:

```bash
python3 scripts/engine-demo-123.py verify data/engine-demo-123-example
```

Verification checks current source/input/run/checkpoint bindings and reconstructs
completed economics. Unexpected artifacts, changed fixed prices/costs, forged
state, altered reports or qualification claims reject. These checks establish
local consistency, not source authenticity or market qualification.

Run focused package tests:

```bash
PYTHONPATH=src:tests python3 -m unittest test_engine_demo_123 -v
```

The tests reuse the preserved122 matrix as a reference. Two tests rebuild actual
accounting states; expensive calculation is substituted only in the interrupted
package-orchestration test, explicitly documented in its source. A separate full
CLI demonstration and independent rational audits exercise the actual engine.

The saved [readable demo](../data/engine-demo-123-invented-demo/REPORT.md) includes
all gains, losses, cash/no-trade and unavailable cells. Each funded cell starts
fresh atUSD10,000; do not add their capitals or results as a portfolio. Prices,
UTC/calendar and costs remain invented/hypothetical, restricted to2000–2003.
Market/paper validation and all orders remain unavailable. The source audit is
scoped to this fixed offline dependency graph, not a general Python sandbox.

Read [the contract](ENGINE-READINESS-123-PROTOCOL.md) and
[verification results](ENGINE-READINESS-123-RESULTS.md).
