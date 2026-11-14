# Manual MT5 UI steps for the guarded043 companion

Automatic MT5 clicks failed twice with `coordinate input geometry is unavailable`.
Leave the current demo account open, exactEURUSD chart, Algo Trading off. Do not
switch accounts, enable automated trading or run the script until the companion
has verified guards and reported its corresponding arm. Never send login/server/
account identifiers, screenshots containing them or whole terminal logs.

1. In Navigator, right-click Scripts → Refresh. Expand
   ForexDemoLab042-30316606657a4ce89da64f8b8d23c610 and confirm
   ForexDemoClockObserver042 is visible. Do not run it yet.
2. Once the agent starts the tested companion with tty=true, it verifies the
   existing actualDEMO/USD/Algooff account/date/instrument/private identity and
   unchanged deployed EX5. Only after `armed, enabled=false`: double-click the
   named script on the existingEURUSD chart. In Inputs confirm
   CollectClockEvidence=false, leave Common permissions unchanged, click OK once.
   Reply that this single disabled run is done. No retries; if an unexpected
   permission/security/account dialog appears, cancel and report it.
3. The companion collects only the exact sanitized native record. It must prove
   reason17/quote_reads0. Only after `armed, enabled=true`: open the same script
   once, change only CollectClockEvidence=true in Inputs, confirm true, click OK
   once. Keep global Algo Trading off and Common permissions unchanged. Reply
   that this single enabled run is done. Do not run again if outcome is unclear.
4. The companion collects its single native record, rechecks guards and finishes/
   shuts down. It computes relative clock brackets and seals all sanitized results.

Fixed GMT-rendered date2026.10.06. On another date, stop before activation; the
agent must declare/test a separately versioned date-specific preparation instead
of automatically retargeting this frozen artifact. No Nov–Dec2026/2025 access.
Native relative clocks do not certify historicalUTC or authorize a constant offset
correction. Capture defaults false; no quote/history/order API is available in
the companion. No live mode, strategies or automated order activation included.
