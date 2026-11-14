#ifndef FXDL_CONTEXT_RUN136
#define FXDL_CONTEXT_RUN136
// Pure decisions only; no account API, IO or order capability.
struct ContextRun136
{
   long origin_s,last_s;
   ulong origin_us,last_us,last_poll_us,reserved_bytes;
   int queries,polls,contexts,poll_part,phase,property,day,index;
   bool pending,in_context,ended;
   string pending_tag,pending_key;
};
string IntegerKey136(const int i)
{
   string v[]={"account_leverage","digits","trade_calc_mode","swap_mode","swap_rollover3days",
      "stops_level","freeze_level","execution_mode","order_mode","custom_symbol","subscription_delay","chart_mode"};
   return i>=0 && i<12?v[i]:"";
}
string DoubleKey136(const int i)
{
   string v[]={"point","tick_size","contract_size","tick_value_profit","tick_value_loss","volume_min","volume_max",
      "volume_step","volume_limit","margin_initial","margin_maintenance","swap_long","swap_short","swap_sunday",
      "swap_monday","swap_tuesday","swap_wednesday","swap_thursday","swap_friday","swap_saturday"};
   return i>=0 && i<20?v[i]:"";
}
bool DateAllowed136(const string date)
{
   return date=="2026.10.26" || date=="2026.10.27" || date=="2026.10.28" || date=="2026.10.29" || date=="2026.10.30";
}
void InitCollector136(ContextRun136 &s,const long seconds,const ulong micros)
{
   s.origin_s=seconds;s.last_s=seconds;s.origin_us=micros;s.last_us=micros;s.last_poll_us=0;s.reserved_bytes=0;
   s.queries=0;s.polls=0;s.contexts=0;s.poll_part=0;s.phase=0;s.property=0;s.day=0;s.index=0;
   s.pending=false;s.in_context=false;s.ended=false;s.pending_tag="";s.pending_key="";
}
int CheckCollectorClock136(ContextRun136 &s,const long seconds,const ulong micros,const string date)
{
   if(s.ended) return 19;
   if(!DateAllowed136(date)) return 11;
   if(s.origin_s<=0 || s.origin_us==0 || seconds<s.last_s || micros<s.last_us || micros<s.origin_us) return 12;
   if(micros-s.origin_us>14400000000) return 13;
   long drift=(seconds-s.origin_s)-(long)((micros-s.origin_us)/1000000);
   if(drift < -2 || drift > 2) return 12;
   s.last_s=seconds;s.last_us=micros;return 0;
}
bool ContextDue136(const ContextRun136 &s)
{
   return !s.ended && !s.in_context && !s.pending && s.poll_part==0 && s.polls<14400 &&
          s.polls%3600==0 && s.contexts==s.polls/3600;
}
int BeginContext136(ContextRun136 &s)
{
   if(!ContextDue136(s) || s.contexts>=4) return 19;
   s.contexts++;s.in_context=true;s.phase=0;s.property=0;s.day=0;s.index=0;return 0;
}
void Expected136(const ContextRun136 &s,string &tag,string &key)
{
   tag="";key="";
   if(s.ended || s.polls>=14400) return;
   if(!s.in_context)
   {
      if(ContextDue136(s)) return;
      tag=s.poll_part==1?"T":"C";key=s.poll_part==0?"before":s.poll_part==1?"quote":"after";return;
   }
   if(s.phase==0) {tag="C";key="context_before";}
   if(s.phase==1)
   {
      tag=s.property<12?"I":s.property<32?"D":"V";
      key=s.property<12?IntegerKey136(s.property):s.property<32?DoubleKey136(s.property-12):"currency_margin";
   }
   if(s.phase==2) {tag="W";key=IntegerToString(s.day)+":"+IntegerToString(s.index);}
   if(s.phase==3) {tag="K";key="commissions";}
   if(s.phase==4 || s.phase==5) {tag="M";key=s.phase==4?"buy":"sell";}
   if(s.phase==6) {tag="C";key="context_after";}
}
int NextQuery136(ContextRun136 &s,const string tag,const string key)
{
   if(s.ended || s.pending) return 19;
   if(s.queries<0 || s.queries>=43604 || s.polls>=14400) return 20;
   string expected_tag,expected_key;Expected136(s,expected_tag,expected_key);
   if(tag=="" || tag!=expected_tag || key!=expected_key) return 19;
   s.queries++;s.pending=true;s.pending_tag=tag;s.pending_key=key;return 0;
}
int CompleteQuery136(ContextRun136 &s,const bool succeeded)
{
   if(s.ended || !s.pending) return 19;
   if((s.pending_tag=="C" || s.pending_tag=="T") && !succeeded) return 19;
   if(s.in_context)
   {
      if(s.phase==0) s.phase=1;
      else if(s.phase==1) {s.property++;if(s.property==33) s.phase=2;}
      else if(s.phase==2)
      {
         if(succeeded && s.index<8) s.index++;
         else {s.day++;s.index=0;if(s.day==7) s.phase=3;}
      }
      else if(s.phase>=3 && s.phase<7) s.phase++;
      else return 19;
   }
   else {s.poll_part++;if(s.poll_part==3) {s.poll_part=0;s.polls++;}}
   s.pending=false;return 0;
}
int EndContext136(ContextRun136 &s)
{
   if(s.ended || !s.in_context || s.pending || s.phase!=7) return 19;
   s.in_context=false;return 0;
}
int WaitState136(const ContextRun136 &s)
{
   if(s.ended || s.pending || s.in_context || s.poll_part!=0 || ContextDue136(s)) return 19;
   if(s.polls>=14400) return 20;
   return 0;
}
bool PollReady136(const ContextRun136 &s,const ulong micros)
{
   return WaitState136(s)==0 && micros>=s.origin_us &&
          (s.polls==0 || (micros>=s.last_poll_us && micros-s.last_poll_us>=1000000));
}
int MarkPollStart136(ContextRun136 &s,const ulong micros)
{
   if(s.ended || s.in_context || !s.pending || s.poll_part!=0 || s.pending_tag!="C" || s.pending_key!="before" ||
      micros<s.origin_us || micros<s.last_us || (s.polls>0 && (micros<s.last_poll_us || micros-s.last_poll_us<1000000))) return 19;
   s.last_poll_us=micros;return 0;
}
int ReserveCollectorBytes136(ContextRun136 &s,const ulong length)
{
   if(s.ended) return 19;
   if(length==0 || length>2048 || s.reserved_bytes>33554432 || length>33554432-s.reserved_bytes) return 14;
   s.reserved_bytes+=length;return 0; // No refund/retry after failed IO.
}
void EndCollector136(ContextRun136 &s) {s.ended=true;}
#endif
