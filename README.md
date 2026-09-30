# Forex Demo Lab

A standalone WSL project for researching, backtesting and eventually running a demo-only forex robot.

Status: project scaffold only. No trading robot, broker connection, or validated strategy has been implemented. No performance claims.

## Workspace

- Linux: /home/lx_singw/projects/forex-demo-lab
- Windows: \\wsl.localhost\Ubuntu\home\lx_singw\projects\forex-demo-lab
- This repository is independent of Skilved.

## Development approach

Keep all source code, tests, research and documentation here in WSL.
The existing MetaTrader 5 terminal remains on Windows. MQL5 source belongs
in mt5/Experts; later, an explicit deployment script can copy and compile it
in the Windows terminal's data directory. Windows runtime copies are build
artifacts, not the source of truth. Do not assume the MT5 Python integration
runs natively in WSL.

Start with a transparent rules-based baseline on EURUSD H1. Evaluate it on
historical data with realistic costs and a chronological holdout, then
forward-test on a demo account. Add AI only if its incremental value can be
measured against the baseline.

## Layout

- src/forex_demo_lab/: future Python research and analysis code
- mt5/Experts/: future MQL5 Expert Advisor source
- tests/: meaningful risk-control and data-integrity tests
- scripts/: future export, deployment and reporting utilities
- data/: local datasets (ignored except README)
- reports/: generated results (ignored except README)
- docs/CONTEXT.md: handoff from the setup conversation
- docs/PLAN.md: proposed implementation milestones

## Continue development

Read AGENTS.md, docs/CONTEXT.md and docs/PLAN.md first.
Python 3.12.3 and Git 2.43.0 were detected in Ubuntu on 2026-09-30.
No third-party packages have been installed for this project.

## Evaluation

Track net return after costs, maximum drawdown, number of trades,
win rate, average win/loss and exposure. Separate strategy development,
holdout results and live demo results. A high win rate alone is not evidence
of profitability. Historical and demo results do not guarantee future returns.
