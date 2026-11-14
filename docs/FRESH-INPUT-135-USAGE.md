# Fresh input135 usage

From the canonical WSL repository, Python3.11 or newer:

```sh
python3 scripts/fresh-input-135.py --format markdown
python3 scripts/fresh-input-135.py --format json
```

The default demonstration creates no files and reads no native capture.
It evaluates the15 fixed invented cases and prints software-check results.
The policy is pinned to the unchanged hypothetical model and cost scenarios.
There is no live, native-admission, fee-override or age-override option.

To inspect one previously frozen invented fixture:

```sh
python3 scripts/fresh-input-135.py \
  --input reports/fresh-input-135/fixtures/bounded_assumptions.json \
  --format markdown
```

Native132 bytes and market_declared headers reject. A rejection produces no
report on stdout and exits with code2. Inputs/policy are read-only.

For an offline consumer, set PYTHONPATH=src and use
`Replay(raw_fixture_bytes, raw_policy_bytes)` from
`forex_demo_lab.fresh_input_135`. Peek exposes the next event; ack returns its
verdict. Store checkpoint bytes with consumer state, or make the consumer
idempotent by causal_prefix_sha256. Restore with
`Replay.restore(raw_fixture_bytes, raw_policy_bytes, checkpoint_bytes)`.
Exact input/policy/source bindings are required. A duplicate immediate ack
returns the same verdict; it does not guarantee exactly-once external effects.

Do not treat hypothetical_input_usable as entry permission. It does not restore
201-hour warm-up, resolve market cost evidence or implement a delivery/fill
queue. A risk_observation_retained flag means the valid original quote remains
visible; it does not itself manage a position. See the full
[contract](FRESH-INPUT-135-CONTRACT.md) for interval and context semantics.

Focused invented-input verification:

```sh
PYTHONPATH=src:tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  test_fresh_input_135 test_paired_replay_133 test_execution_metrics \
  test_tick_simulation
```

No MT5 action, fresh-data collection or renewal of an expired script is needed.
