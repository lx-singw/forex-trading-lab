# Elliott-inspired detector — offline usage

Use Python3.11+ standard library in the canonical WSL checkout. No terminal,
broker, account, credentials or installation is needed. This command produces
signal observations on invented daily bars; it cannot execute or report returns.

```bash
cd /home/lx_singw/projects/forex-demo-lab
mkdir -p data/elliott-waves-124-example
python3 scripts/elliott-waves-124.py create-fixture long_breakout data/elliott-waves-124-example/input.json
python3 scripts/elliott-waves-124.py freeze data/elliott-waves-124-example/input.json data/elliott-waves-124-example/frozen.json
python3 scripts/elliott-waves-124.py evaluate data/elliott-waves-124-example/input.json data/elliott-waves-124-example/frozen.json data/elliott-waves-124-example/observations.json
```

Files must be new. The seventeen fixed fixture names are listed by the CLI's
`create-fixture --help`. No parameter, optimization, live-mode or market-data
option exists. Accepted input wrappers reuse118's strict invented daily schema,
calendar and lineages, restricted to2000–2003. Labels/hashes cannot certify origin.

Reports retain confirmed pivots, the current alternating interpretation, every
setup/rejection and each accepted breakout observation. A pivot's source bar
time differs from its later confirmation time. An observation is available only
when its breakout bar actually becomes available; a future fill must wait for
a later eligible observed bid/ask quote. It is never an entry at a historical
pivot, candle high or reconstructed midpoint. No price interpolation is performed.

For incremental checks, use `Replay(input, manifest)`, `step()`, defensive-copy
`state`, `checkpoint()`, `Replay.restore(input, manifest, checkpoint_dictionary)`,
`run()` and `report()`. A report may contain an explicitly unfinished prefix.
Restoration reconstructs only the checkpoint cursor. Latest identical indexed
step is idempotent; altered/older duplicates reject. Checkpoint checksums are
local consistency checks, not authentication or power-loss durability guarantees.

Run focused verification:

```bash
PYTHONPATH=src:tests python3 -m unittest test_elliott_waves_124 test_daily_features_118 -v
```

This is a close-swing adaptation with fixed1% impulse,38.2–61.8% retracement,
ten subsequent trading-bar expiry and253-bar/trend gates. It is not a complete
Elliott Wave implementation or a replication of published neural-network results.
The chart's apparent wave numbering does not prove an upcoming wave3.

Read [the frozen definition](ELLIOTT-WAVES-124-PROTOCOL.md) and
[results](ELLIOTT-WAVES-124-RESULTS.md). Trades and returns remain null; market,
forward-paper, actual-order and real-money execution remain unavailable. Existing
117 strategies are unchanged. The future standalone fill adapter is separately
[prepared in125](ELLIOTT-EXECUTION-125-PLAN.md), not implemented here.
