#ifndef FXDL_CLOCK_GUARD_042
#define FXDL_CLOCK_GUARD_042

// Pure decisions shared by the MQL script and the synthetic C++ harness.
// Account identity is ephemeral and must never enter diagnostic output.
struct ClockAccount042
{
   bool query_ok;
   bool connected;
   bool algo_allowed;
   bool tester;
   long mode;
   string currency;
   long login;
   string server;
};

int AccountReason042(const ClockAccount042 &s, const bool identified,
                     const long login, const string server)
{
   if(!s.query_ok) return 1;
   if(!s.connected) return 2;
   if(s.tester) return 3;
   if(s.mode != ACCOUNT_TRADE_MODE_DEMO) return 4;
   if(s.currency != "USD") return 5;
   if(s.algo_allowed) return 6;
   if(s.login <= 0 || StringLen(s.server) == 0) return 7;
   if(identified && (s.login != login || s.server != server)) return 8;
   return 0;
}

int SymbolReason042(const bool query_ok, const bool visible,
                    const string base, const string profit, const string symbol)
{
   if(!query_ok || !visible || base != "EUR" || profit != "USD" || symbol != "EURUSD") return 9;
   return 0;
}

struct ClockReading042
{
   long current_s;
   long calculated_server_s;
   long gmt_s;
   long local_s;
};

int ReadingReason042(const ClockReading042 &b, const ClockReading042 &a,
                     const ulong before_us, const ulong after_us,
                     const long tick_s, const long tick_ms,
                     const double bid, const double ask, const bool finite_prices,
                     const string before_date, const string after_date)
{
   if(before_date != "2026.10.06" || after_date != "2026.10.06") return 10;
   if(b.current_s > 32535215999 || b.calculated_server_s > 32535215999 || b.gmt_s > 32535215999 || b.local_s > 32535215999 ||
      a.current_s > 32535215999 || a.calculated_server_s > 32535215999 || a.gmt_s > 32535215999 || a.local_s > 32535215999 ||
      tick_s > 32535215999 || tick_ms > 32535215999999) return 11;
   if(b.current_s <= 0 || b.calculated_server_s <= 0 || b.gmt_s <= 0 || b.local_s <= 0 ||
      a.current_s < b.current_s || a.calculated_server_s < b.calculated_server_s ||
      a.gmt_s < b.gmt_s || a.local_s < b.local_s || after_us < before_us) return 11;
   if(after_us - before_us > 15000000) return 12;
   if(!finite_prices || bid <= 0 || ask < bid || tick_s <= 0 || tick_ms <= 0 || tick_ms / 1000 != tick_s) return 13;
   // Server quote age is relative evidence only; never compare as certified UTC.
   long age_ms = a.current_s * 1000 - tick_ms;
   if(age_ms < -2000 || age_ms > 60000) return 14;
   long local_delta = tick_ms - a.gmt_s * 1000;
   if(local_delta < -86400000 || local_delta > 86400000) return 15;
   long elapsed_s = (long)((after_us - before_us) / 1000000);
   long wall_delta = a.gmt_s - b.gmt_s;
   if(wall_delta - elapsed_s < -2 || wall_delta - elapsed_s > 2) return 16;
   return 0;
}
#endif
