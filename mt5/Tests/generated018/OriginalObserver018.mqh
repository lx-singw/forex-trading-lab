datetime last_closed = 0;

bool IsDemoAccount()
{
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      return false;
   ResetLastError();
   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   return GetLastError() == 0 && mode == ACCOUNT_TRADE_MODE_DEMO;
}

int OnInit()
{
   if(!IsDemoAccount())
   {
      Print("Observer rejected: connected demo account required.");
      return INIT_FAILED;
   }
   if(_Symbol != "EURUSD" || _Period != PERIOD_H1)
   {
      Print("Observer requires exact EURUSD symbol on H1.");
      return INIT_PARAMETERS_INCORRECT;
   }
   // Do not replay historical signals on attachment or terminal restart.
   last_closed = iTime(_Symbol, PERIOD_H1, 1);
   Print("Demo observer ready. Order placement is unavailable in this build.");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   // Recheck actual account mode on every tick, including account switches.
   if(!IsDemoAccount())
   {
      Print("Observer stopped: connected demo account check failed.");
      ExpertRemove();
      return;
   }
   MqlRates bars[];
   ArraySetAsSeries(bars, false);
   // Copy only closed candles; physical order is oldest to newest.
   if(CopyRates(_Symbol, PERIOD_H1, 1, 51, bars) != 51)
      return;
   datetime closed = bars[50].time;
   if(closed == last_closed)
      return;
   datetime previous = last_closed;
   last_closed = closed;
   if(previous == 0 || closed - previous != 3600)
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.ask <= 0 || tick.bid <= 0 || tick.ask < tick.bid)
      return;
   // Signals expire at a discontinuity (e.g. weekend), just like the simulator.
   if(iTime(_Symbol, PERIOD_H1, 0) - closed != 3600)
      return;
   if((tick.ask - tick.bid) / 0.0001 > 1.5)
      return;
   // Suppress suggestions if the account already has any position/pending order.
   if(PositionsTotal() != 0 || OrdersTotal() != 0)
      return;
   double fast_old = 0, fast_new = 0, slow_old = 0, slow_new = 0;
   for(int i = 0; i < 50; ++i)
      slow_old += bars[i].close;
   for(int i = 1; i < 51; ++i)
      slow_new += bars[i].close;
   for(int i = 30; i < 50; ++i)
      fast_old += bars[i].close;
   for(int i = 31; i < 51; ++i)
      fast_new += bars[i].close;
   slow_old /= 50.0;
   slow_new /= 50.0;
   fast_old /= 20.0;
   fast_new /= 20.0;
   int side = 0;
   if(fast_old <= slow_old && fast_new > slow_new) side = 1;
   if(fast_old >= slow_old && fast_new < slow_new) side = -1;
   if(side == 0) return;
   double atr = 0;
   for(int i = 37; i < 51; ++i)
      atr += MathMax(bars[i].high - bars[i].low,
                     MathMax(MathAbs(bars[i].high - bars[i-1].close),
                             MathAbs(bars[i].low - bars[i-1].close)));
   atr /= 14.0;
   if(!MathIsValidNumber(atr) || atr <= 0 || !IsDemoAccount())
      return;
   PrintFormat("OBSERVATION ONLY: %s; closed candle %s; 2x ATR distance %.5f. No order sent.",
               side == 1 ? "BUY" : "SELL", TimeToString(closed), 2.0 * atr);
}
