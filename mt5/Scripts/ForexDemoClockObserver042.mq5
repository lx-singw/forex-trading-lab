#property copyright "Forex Demo Lab"
#property version "1.000"
#property strict
#property script_show_inputs
#property description "One-shot demo clock evidence. Disabled by default; cannot place orders."
#include "ClockGuard042.mqh"

input bool CollectClockEvidence = false;

void StopClock042(const int reason, const int reads)
{
   // Fixed numeric reasons; no account identifiers or native exception text.
   PrintFormat("FXDL_CLOCK042 {\"version\":\"clock_observer_042_v1\",\"accepted\":false,\"reason_code\":%d,\"quote_reads\":%d}", reason, reads);
}

void ReadAccount042(ClockAccount042 &s)
{
   s.query_ok = true;
   ResetLastError(); s.connected = (bool)TerminalInfoInteger(TERMINAL_CONNECTED); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.algo_allowed = (bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.tester = (bool)MQLInfoInteger(MQL_TESTER); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.mode = AccountInfoInteger(ACCOUNT_TRADE_MODE); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.currency = AccountInfoString(ACCOUNT_CURRENCY); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.login = AccountInfoInteger(ACCOUNT_LOGIN); s.query_ok = s.query_ok && GetLastError() == 0;
   ResetLastError(); s.server = AccountInfoString(ACCOUNT_SERVER); s.query_ok = s.query_ok && GetLastError() == 0;
}

bool ReadClocks042(ClockReading042 &s)
{
   ResetLastError(); s.current_s = (long)TimeCurrent(); if(GetLastError() != 0) return false;
   ResetLastError(); s.calculated_server_s = (long)TimeTradeServer(); if(GetLastError() != 0) return false;
   ResetLastError(); s.gmt_s = (long)TimeGMT(); if(GetLastError() != 0) return false;
   ResetLastError(); s.local_s = (long)TimeLocal(); if(GetLastError() != 0) return false;
   return true;
}

void OnStart()
{
   if(!CollectClockEvidence) { StopClock042(17, 0); return; }
   ClockAccount042 state;
   ReadAccount042(state);
   int reason = AccountReason042(state, false, 0, "");
   if(reason != 0) { StopClock042(reason, 0); return; }
   long identity_login = state.login;
   string identity_server = state.server;
   bool symbol_ok = true;
   ResetLastError(); bool visible = (bool)SymbolInfoInteger("EURUSD", SYMBOL_VISIBLE); symbol_ok = symbol_ok && GetLastError() == 0;
   ResetLastError(); string base = SymbolInfoString("EURUSD", SYMBOL_CURRENCY_BASE); symbol_ok = symbol_ok && GetLastError() == 0;
   ResetLastError(); string profit = SymbolInfoString("EURUSD", SYMBOL_CURRENCY_PROFIT); symbol_ok = symbol_ok && GetLastError() == 0;
   reason = SymbolReason042(symbol_ok, visible, base, profit, _Symbol);
   if(reason != 0) { StopClock042(reason, 0); return; }
   ReadAccount042(state);
   reason = AccountReason042(state, true, identity_login, identity_server);
   if(reason != 0) { StopClock042(reason, 0); return; }
   ulong before_us = GetMicrosecondCount();
   ClockReading042 before, after;
   if(!ReadClocks042(before)) { StopClock042(18, 0); return; }
   if(TimeToString((datetime)before.gmt_s, TIME_DATE) != "2026.10.06") { StopClock042(10, 0); return; }
   ReadAccount042(state);
   reason = AccountReason042(state, true, identity_login, identity_server);
   if(reason != 0) { StopClock042(reason, 0); return; }
   MqlTick tick;
   ResetLastError(); bool tick_ok = SymbolInfoTick("EURUSD", tick); int tick_error = GetLastError();
   ReadAccount042(state);
   reason = AccountReason042(state, true, identity_login, identity_server);
   if(reason != 0) { StopClock042(reason, 1); return; }
   if(!tick_ok || tick_error != 0) { StopClock042(19, 1); return; }
   if(!ReadClocks042(after)) { StopClock042(18, 1); return; }
   ulong after_us = GetMicrosecondCount();
   reason = ReadingReason042(before, after, before_us, after_us, (long)tick.time, tick.time_msc,
      tick.bid, tick.ask, MathIsValidNumber(tick.bid) && MathIsValidNumber(tick.ask),
      TimeToString((datetime)before.gmt_s, TIME_DATE), TimeToString((datetime)after.gmt_s, TIME_DATE));
   if(reason != 0) { StopClock042(reason, 1); return; }
   ReadAccount042(state);
   reason = AccountReason042(state, true, identity_login, identity_server);
   if(reason != 0) { StopClock042(reason, 1); return; }
   // Completion date check is separate from clock sampling. No continuous handler.
   if(TimeToString(TimeGMT(), TIME_DATE) != "2026.10.06") { StopClock042(10, 1); return; }
   PrintFormat("FXDL_CLOCK042 {\"version\":\"clock_observer_042_v1\",\"accepted\":true,\"reason_code\":0,\"quote_reads\":1,\"guard_checks\":5,\"time_current_before_s\":%I64d,\"time_current_after_s\":%I64d,\"calculated_server_before_s\":%I64d,\"calculated_server_after_s\":%I64d,\"gmt_before_s\":%I64d,\"gmt_after_s\":%I64d,\"local_before_s\":%I64d,\"local_after_s\":%I64d,\"tick_time_s\":%I64d,\"tick_time_msc\":%I64d,\"bid\":%.17g,\"ask\":%.17g,\"tick_flags\":%u,\"elapsed_us\":%I64u}",
      before.current_s, after.current_s, before.calculated_server_s, after.calculated_server_s,
      before.gmt_s, after.gmt_s, before.local_s, after.local_s, (long)tick.time, tick.time_msc,
      tick.bid, tick.ask, tick.flags, after_us - before_us);
}
