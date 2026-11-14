# Project instructions

- Work in this repository for the forex experiment. Do not edit Skilved.
- Read docs/CONTEXT.md and docs/PLAN.md before implementing.
- Current scope is research, historical simulation and demo accounts only.
- Any execution component must reject real and contest accounts by checking
  the actual account type, not a server name. Recheck before order submission.
- Keep real-money execution unavailable; no live-mode toggle in this phase.
- Keep automated order placement disabled by default. Test historically first.
- Keep credentials and account identifiers out of code, logs and version control.
- Do not promise a win rate or income; report observed evidence and limitations.
- No martingale or increasing stakes to recover losses.
- Position limits, stop-loss handling, duplicate-order prevention and loss limits
  require meaningful tests. Account for gaps, slippage and restart behavior;
  never describe a stop-loss as a guaranteed maximum loss.
- Use chronological evaluation without future-data leakage; include costs.
- Keep canonical source here. Windows MT5 compilation/runtime artifacts may
  be deployed separately. Never overwrite unrelated EAs or terminal settings.
- Do not install paid services or create broker accounts as part of scaffolding.
- Summarize implementation, verification and remaining limitations clearly.
- After every sprint, review all intended changes, make a descriptive commit and
  push to main. Respect the existing generated-data, report and runtime ignore
  rules when committing; keep credentials and account identifiers out of Git.
