#property version "1.000"
#property strict
#property description "Disabled Tori Trendline execution contract"
#include "TrendlineExecution193.mqh"

// Account identity stays in memory. OnStart has no runtime route to the reader.
void ReadTrendlineAccount193(TrendlineAccount193 &account)
{
   ResetLastError();account.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);account.query_ok=GetLastError()==0;
   ResetLastError();account.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);account.query_ok=account.query_ok && GetLastError()==0;
   ResetLastError();account.tester=(bool)MQLInfoInteger(MQL_TESTER);account.query_ok=account.query_ok && GetLastError()==0;
   ResetLastError();account.login=AccountInfoInteger(ACCOUNT_LOGIN);account.query_ok=account.query_ok && GetLastError()==0;
   ResetLastError();account.server=AccountInfoString(ACCOUNT_SERVER);account.query_ok=account.query_ok && GetLastError()==0;
}

void OnStart() {}
