#ifndef FXDL_PRIVATE_GUARD107
#define FXDL_PRIVATE_GUARD107

// Shared decisions only. Identity is ephemeral and never part of the export.
struct PrivateAccount107
{
   bool query_ok, connected, algo, tester, visible;
   long mode, login;
   string server, currency, symbol, base, quote;
};

int GuardReason107(const PrivateAccount107 &s, const bool identified,
                   const long login, const string server)
{
   if(!s.query_ok) return 2;
   if(!s.connected) return 3;
   if(s.tester) return 4;
   if(s.mode != ACCOUNT_TRADE_MODE_DEMO) return 5;
   if(s.currency != "USD") return 6;
   if(s.algo) return 7;
   if(s.login <= 0 || s.server == "") return 8;
   if(identified && (s.login != login || s.server != server)) return 9;
   if(s.symbol != "EURUSD" || !s.visible || s.base != "EUR" || s.quote != "USD") return 10;
   return 0;
}

int ClockReason107(const long origin_s, const ulong origin_us,
                   const long now_s, const ulong now_us, const string date)
{
   if(date != "2026.10.12") return 11;
   if(origin_s <= 0 || now_s < origin_s || now_us < origin_us) return 12;
   ulong elapsed = now_us-origin_us;
   if(elapsed > 60000000) return 13;
   long drift = (now_s-origin_s)-(long)(elapsed/1000000);
   if(drift < -2 || drift > 2) return 12;
   return 0;
}

int QuoteReason107(const long seconds, const long millis, const double bid,
                   const double ask, const double last, const double real_volume,
                   const bool finite)
{
   if(!finite || seconds <= 0 || seconds > 32535215999 || millis <= 0 ||
      millis > 32535215999999 || millis/1000 != seconds || bid <= 0 ||
      ask < bid || last < 0 || real_volume < 0) return 16;
   return 0;
}
#endif
