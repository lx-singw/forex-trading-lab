# Offline paired replay133 usage

Run from the canonical WSL repository with Python 3.11 or newer:

```sh
python3 scripts/paired-replay-133.py --format markdown
python3 scripts/paired-replay-133.py --format json
```

The default hash-pinned manifest selects the 20 and 23 October132 captures
separately. The CLI reads local files and prints an audit. It does not modify
the capture, write state, connect to MT5, wait in real time or place orders.
An invalid input produces a generic rejection with exit code2 and no audit.

For a local consumer, use the pull cursor through the Python module:

```python
from pathlib import Path
from forex_demo_lab.paired_replay_133 import Replay

raw = Path(capture_path).read_bytes()  # one closed, bounded132 file
cursor = Replay(raw)
while (packet := cursor.peek()) is not None:
    # Inspect the completed poll in recorder order. Any scheduling must retain
    # replay_offset_us and actual gaps; these markers are not verified UTC.
    inspect_packet(packet)
    cursor.ack(packet)
    checkpoint_bytes = cursor.checkpoint()
audit = cursor.report()  # final audit requires an exhausted cursor
```

Set PYTHONPATH=src when importing from a checkout without an installed package.
Restore with `Replay.restore(raw, checkpoint_bytes)` using the identical raw
file and source version. The checkpoint contains committed progress only.
Persist consumer state and cursor together, or make the consumer idempotent by
event_id. A crash between consumer work and ack may redeliver the same packet;
the adapter alone cannot guarantee exactly-once downstream effects. An older
ack is not a substitute for ordered processing.

Packets preserve native quote fields, before/after raw clocks and receipt
markers. The chosen replay clock is the after-group guard marker, relative to
this run's own origin. The quote receipt interval is also present separately.
Do not relabel either as certified UTC, source age, executable freshness or
network latency. Do not join runs or remove repeated snapshots as duplicates.
Incomplete final polls are quarantined and counted, rather than fabricated.
Source-label reversals are retained in recorder order and flagged.

The production module deliberately has no financial-time conversion. Its
financial_tick method always rejects. The invented UTC embedding in the test
file is only a synthetic risk-engine harness and must not be applied to native
captures. No real-money or order-placement switch exists.

Focused verification, with invented inputs:

```sh
PYTHONPATH=src:tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  test_paired_replay_133 test_paired_capture_132 test_execution_metrics \
  test_tick_simulation test_simulation
```
