# Private recorder108 — observed run

The user's107 launch produced one closed, intact export:35,181 bytes, SHA256
d0af7e0309f4b9960f55aae937cae991214f744e46fbf341ff902383b15b11f8.
Deployed source/header/EX5 match the107 build. The source file was opened read-only
with exclusive access and copied byte-for-byte into ignored local data. No terminal
settings or source files were changed; no SDK, support contact or orders were used.

The unchanged107 CLI and library agree: **116 attempts and116 observations**,
**52 adjacent repeated snapshots**,64 distinct source millisecond labels,
zero missing/invalid quotes,zero source reversals,zero receipt gaps above2seconds,
no pending attempt or truncated tail. The SHA256 chain and stop record validate.
This is a stopped capture, **reason13:60-second elapsed budget exceeded**,
rather than a complete120-snapshot run. It is not silently resumed or marked complete.

The last recorded guard was59,963.387ms after startup. The115 read intervals have
minimum500.210ms,median521.441ms,mean521.410ms and maximum937.861ms.
The quote API call median was0.003ms (maximum0.011ms); after-guard median0.003ms.
The current loop waits in fixed20ms steps, permitting repeated scheduling overshoot.
Measured intervals establish the shortfall; they do not isolate the cause of the
single long interval or prove the operating system can meet future deadlines.

A separate successor should adapt its wait to the remaining interval, keeping
minimum500ms spacing, maximum120 snapshots and60-second stop unchanged.
A short bounded final polling window can reduce sleep quantization, at a small CPU
cost. Genuine stalls must still stop the run. Preserve107 source/export/failure;
do not raise its elapsed limit or reduce its account safeguards.

Raw source labels minus nominal computer-GMT receipt seconds ranged from
10,797.163 to10,800.526 seconds (median10,799.693). This arithmetic is not quote age,
independent UTC certification or proof of a valid timezone conversion. No offset
was applied. The nominal start label was2026-10-12T15:26:42; source labels remain raw.

The observed EURUSD spread was0–0.1 pip (one pip defined as0.0001 price units),
median0 and mean0.0310 pip. **80 snapshots had equal bid and ask**,36 positive
spread. This short demo quote sample does not establish executable prices or
transaction costs, commissions, slippage or full market tick coverage. Existing
simulation cost assumptions remain unchanged.

This is operational evidence consistent with the guarded script path and matching
deployed artifacts; the export is not authenticated account/producer evidence.
The actual account guard is in code; no account IDs or settings were collected.
Market qualification, paper/order admission and real-money execution remain false.
No new financial performance was evaluated and no reserved validation data was used.

No implementation changed during108, so no tests were rerun. The prior37 focused
tests/48 guard checks and2,095 older active tests remain their original results.
Next: build and verify a separate109 scheduler correction, then run one new bounded
diagnostic when available. No external support is required or authorized.
