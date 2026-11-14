# Forward capture111 — implementation contract

Fresh policy date2026.10.12; private demo/no-contact direction retained.
One run: at most3,600,000,000 monotonic microseconds,7,200 attempts,64 segments,
4,194,304 bytes total. Minimum500,000us between read starts across every segment.
Rotate after120 resolved valid attempts; never reset run state/chain/global caps.
At most262,144 bytes per segment,2,048 bytes per ASCII CRLF frame. Reserve full
frame bytes before IO; partial/failed writes stop, never refund/retry. No resume.

New FXDL111_V1 format;107 inspector/source/deployment unchanged. SHA256 frames use
previous_chain + TAB + payload + LF, with uppercase64-hex digest appended afterTAB.
Physical CRLF bytes count toward budgets. Global hash chain spans files.

H: format, declared_kind(market_declared or invented_fixture),date,segment,
origin_seconds,origin_us,attempts_before,observed_before,last_read_us,last_wall_s,
last_guard_us,previous_chain. Initial counts/read are0,wall/guard equal origin.
A: consecutive global attempt number, persisted/flushed before quote read.
Q/N: same receipt/native quote fields as107 but global sequence up to7200.
R: attempts,observed,finished_wall_s,finished_us. Rotation requires120 new attempts,
all observations resolved valid; at least one next segment is needed for run completion.
E: attempts,observed,finished_wall_s,finished_us. Complete requires7200/7200.
S: reason,attempts,observed. A stopped run can retain a pending attempt. N requires
matching S15/16. No records after terminal; R can only lead to the next header.

Each run creates a new exclusive directory and sequential Segment111-001.txt files.
Read-only inspector checks names/order, linkage, global counts/clocks/intervals/
bytes, terminal state, integrity and partial final records. No cross-run monotonic
subtraction. Partial final files/pending attempts remain incomplete; no silent reuse.
Headers/footers are consistency claims, not authenticated producer/account proof.

Time/quote guards use raw nominal computer-GMT seconds and monotonic microseconds;
date/backward values/drift beyond2seconds reject. Source timestamps stay raw.
Actual DEMO/USD/connected/Algo-off/non-tester/stable private identity/exact visible
EURUSD checked at startup, reads, boundaries and completion; identity never exported.
Failed after-read guards discard tick. Clock/guard/write faults stop whole run.
One-hour limit S13 is expected bounded termination if7200 cannot fit; don't increase
frequency, catch up or weaken limits. Blocked native IO is not hard-preempted.

Default CollectOneHour=false. No orders/DLL/pipe/SDK/login/network/symbol selection/
terminal settings. No automatic launch, scheduler, support contact or reserved-data
replay. Compile/deploy new owned folder only. Private engineering does not certify
source age/UTC/use rights/execution costs/market qualification/paper/trading edge.
