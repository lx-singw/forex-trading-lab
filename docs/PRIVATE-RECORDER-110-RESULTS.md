# Private recorder110 — native retest results

The109 recorder completed its intended120-snapshot acquisition within the60-second
budget. The unchanged107 CLI and library independently agree on the complete export,
with a valid hash chain/footer, no pending attempt and no truncated tail.
The matching deployed source, both headers and EX5 were verified before copying.

One closed36,434-byte export was opened read-only with exclusive access and preserved
byte-for-byte in ignored local data. SHA256:
53f382fd8e252b4ca599e852177b7c0dc5b341b53c1be764da9d1237a2d5253c.
No source file, terminal setting or old artifact was modified.

| Observation | Original107 run | Corrected109 retest |
|---|---:|---:|
| Valid observations | 116 | 120 |
| Terminal outcome | Stopped:60-second limit | Complete |
| Recorded completion elapsed | No completion footer | 59.535833 seconds |
| Median read interval | 521.441ms | 500.087ms |
| Minimum read interval | 500.210ms | 500.061ms |
| Maximum read interval | 937.861ms | 521.585ms |
| Adjacent repeated snapshots | 52 | 41 |
| Missing/invalid observations | 0/0 | 0/0 |
| Source reversals / receipt gaps over2s | 0/0 | 0/0 |

The corrected run's119 intervals average500.283ms; every read is at least500ms
after its predecessor. Footer guard count363 matches the expected path. Quote call
median0.002ms,maximum0.070ms. The nominal computer-GMT start label was
2026-10-12T15:53:19. The recorded footer timestamp precedes final IO/close; it is
acquisition timing, not a hard bound on every native call or process shutdown.

This demonstrates that the timing correction worked **in this observed run**.
The runs took place in different market windows. Changes in repetition, spreads
or price activity cannot be attributed to the scheduler or treated as strategy
evidence. Future Windows stalls can still stop the recorder; no hard scheduling,
power-loss durability or complete market-tick delivery guarantee is established.

## Remaining data limits

The120 observations contain41 repeats and79 distinct source millisecond labels.
Raw source labels minus nominal receipt seconds range from10,797.682 to10,800.531
seconds,median10,799.942. No offset is applied. This arithmetic does not certify
UTC, broker timezone, source age or per-side executable freshness.

Observed EURUSD spreads range0–0.1 pip,median0.1 and mean0.0658 pip
(one pip defined as0.0001 price units).41 quotes have equal bid/ask and79 have
positive spread. These short demo quotes do not establish commissions, execution
costs, slippage or suitable historical-cost estimates. Existing cost assumptions
remain unchanged. No trades, returns, win rate or strategy optimization was run.

This is a functioning terminal-local diagnostic path, with evidence consistent
with the guarded deployed script. Its checksum is not independent account/producer
authentication. Actual DEMO guards remain in code and private identity stays in
memory; no account/config/log files were read. Market qualification, paper/order
admission and real-money execution remain false.

## Next concrete work

Prepare a separate **one-hour read-only pilot**, with strict total time/attempt/
file/byte caps and short independently inspectable segments. Its purpose is to
measure continuity, repetitions, clock behavior and spreads over a useful period
before selecting fixed forward paper experiments. Detailed implementation scope:
[FORWARD-CAPTURE-111-PLAN.md](FORWARD-CAPTURE-111-PLAN.md).
That plan is prepared, not implemented or run. No additional launch is needed to
complete this retest inspection.

All518 retained canonical source hashes remain unchanged. This turn processed
evidence only; no new tests or full-suite result are claimed. Prior46 focused
tests/48 account checks/15 schedule boundaries and older2,095 active tests retain
their original results.107–109 evidence and stopped107 capture are preserved.
No SDK, terminal launch, agent script execution, settings/log/account inspection,
provider contact, orders or reserved validation data were used. The user's
private-demo/no-contact scope continues; historical gaps, original strategy/cost
rules, old provider stops, H.10/native090 closures and date reservations stay intact.
