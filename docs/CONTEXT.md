# Setup context - 2026-09-30

The user wants to explore whether an AI-assisted forex robot can help raise
funds. They previously traded binary options on IQ Option and initially asked
about a win rate above 90%. We explained why win rate is not profitability and
why sustained profits cannot be promised.

The user confirmed being in South Africa and agreed to start with demo money.
They installed MT5 on Windows and created a MetaQuotes-Demo account.
The latest screenshot showed:
- USD 10,000 balance, equity and free margin;
- no open positions;
- EURUSD H1 chart;
- Algo Trading disabled.
The final chosen leverage has not been verified. Do not infer it from balance.
No passwords are needed in chat.

Windows MT5 installation was found at C:\Program Files\MetaTrader 5.
The terminal data folder was found under the user's AppData\Roaming\MetaQuotes\Terminal.
Rediscover the active terminal path before deployment rather than assuming it
is unchanged. Account credentials were not read.

A demo-only rules-based baseline was proposed before any AI work. No EA was
written, compiled, installed or tested before the user redirected the work to
a separate WSL project. Only read-only discovery had been performed.

Latest explicit request: move away from Skilved, create another WSL project
specifically for this, and build everything there.

This repository now holds the scaffold and handoff. The Codex chat itself
remains attached to its existing project until the user opens this new folder
as a project; creating the folder does not move the current chat.

Next implementation task: build a small, inspectable demo-only baseline with
risk controls and a reproducible historical test workflow. Agree on concrete
test settings through sensible defaults; no profitability assumptions.
