#ifndef FXDL_PRIVATE_SCHEDULE109
#define FXDL_PRIVATE_SCHEDULE109

// Pure monotonic decisions, shared with the portable test harness.
// A final polling window reduces sleep overshoot; it cannot bound OS stalls.
int Schedule109(const ulong origin_us, const ulong last_read_us,
                const ulong now_us, bool &ready, int &sleep_ms)
{
   ready=false; sleep_ms=0;
   if(now_us<origin_us || (last_read_us!=0 &&
      (last_read_us<origin_us || now_us<last_read_us))) return 12;
   if(now_us-origin_us>60000000) return 13;
   if(last_read_us==0 || now_us-last_read_us>=500000) {
      ready=true; return 0;
   }
   ulong remaining=500000-(now_us-last_read_us);
   if(remaining>25000) {
      ulong milliseconds=(remaining-25000)/1000;
      sleep_ms=(int)(milliseconds>20?20:milliseconds);
   }
   return 0;
}
#endif
