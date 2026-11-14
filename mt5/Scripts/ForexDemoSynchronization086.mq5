#property strict
#property version "1.000"
#property script_show_inputs
#property description "Default-off synthetic synchronization reader; no market data or orders."
#include "ClockGuard042.mqh"
#include "SynchronizationWire084.mqh"
#include "Synchronization085.mqh"
#include "WindowsPipe086.mqh"
input bool ReadSyntheticEvidence086=false;
input string SourceContract086="";
input string CandidateArtifact086="";
input string PrivateEpisode086="";
const string PHASE086="86000000000000000000000000000001";
struct Private086
{
   bool identified;
   long login,build;
   string server,path,data;
   ulong first_boot,last_boot,first_us,last_us;
   datetime first_utc,last_utc;
   int guards,io;
};
struct Status086
{
   int reason,requests,responses,opens,reads,closes;
   long hold_start,hold_end;
};
void Report086(const Status086 &r)
{
   PrintFormat("FXDL_SYNC086 {\"version\":\"synchronization_reader_086_v1\",\"phase\":\"%s\",\"reason\":%d,\"requests\":%d,\"responses\":%d,\"opens\":%d,\"reads\":%d,\"closes\":%d,\"hold_start\":%I64d,\"hold_end\":%I64d,\"quote_reads\":0,\"history_reads\":0,\"orders\":0,\"receipt_permissions\":0}",
      PHASE086,r.reason,r.requests,r.responses,r.opens,r.reads,r.closes,r.hold_start,r.hold_end);
}
void Account086(ClockAccount042 &s)
{
   s.query_ok=true;
   ResetLastError();s.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.algo_allowed=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.tester=(bool)MQLInfoInteger(MQL_TESTER);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.currency=AccountInfoString(ACCOUNT_CURRENCY);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.login=AccountInfoInteger(ACCOUNT_LOGIN);s.query_ok=s.query_ok && ::GetLastError()==0;
   ResetLastError();s.server=AccountInfoString(ACCOUNT_SERVER);s.query_ok=s.query_ok && ::GetLastError()==0;
}
int Guard086(Private086 &p)
{
   if(IsStopped())return 18;
   if(++p.guards>1024)return 21;
   ClockAccount042 s;Account086(s);
   int reason=AccountReason042(s,p.identified,p.login,p.server);if(reason!=0)return reason;
   bool ok=true;
   ResetLastError();bool visible=(bool)SymbolInfoInteger("EURUSD",SYMBOL_VISIBLE);ok=ok && ::GetLastError()==0;
   ResetLastError();string base=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_BASE);ok=ok && ::GetLastError()==0;
   ResetLastError();string profit=SymbolInfoString("EURUSD",SYMBOL_CURRENCY_PROFIT);ok=ok && ::GetLastError()==0;
   reason=SymbolReason042(ok,visible,base,profit,_Symbol);if(reason!=0)return reason;
   ResetLastError();long build=TerminalInfoInteger(TERMINAL_BUILD);ok=::GetLastError()==0 && build==6244;
   ResetLastError();string path=TerminalInfoString(TERMINAL_PATH);ok=ok && ::GetLastError()==0 && StringLen(path)>0;
   ResetLastError();string data=TerminalInfoString(TERMINAL_DATA_PATH);ok=ok && ::GetLastError()==0 && StringLen(data)>0;
   if(!ok)return 1;
   if(p.identified && (build!=p.build || path!=p.path || data!=p.data))return 26;
   ResetLastError();datetime utc=TimeGMT();if(::GetLastError()!=0 || TimeToString(utc,TIME_DATE)!="2026.10.08")return 10;
   ulong boot=GetTickCount64(),us=GetMicrosecondCount();
   if(boot>9007199254740991 || boot<p.last_boot || us<p.last_us || utc<p.last_utc)return 19;
   if(boot-p.first_boot>=120000 || us-p.first_us>=120000000)return 21;
   long bd=(long)(boot-p.first_boot),ud=(long)((us-p.first_us)/1000),wd=(long)(utc-p.first_utc)*1000;
   if(bd-ud>1000 || ud-bd>1000 || wd-bd>2000 || bd-wd>2000)return 19;
   p.identified=true;p.login=s.login;p.server=s.server;p.build=build;p.path=path;p.data=data;
   p.last_boot=boot;p.last_us=us;p.last_utc=utc;return 0;
}
int Before086(Private086 &p)
{
   if(++p.io>512)return 21;
   return Guard086(p);
}
bool Hex086(const string text,const int count,uchar &raw[],const int offset)
{
   if(StringLen(text)!=count*2)return false;
   const string alphabet="0123456789abcdef";
   for(int i=0;i<count;i++)
   {
      int a=StringFind(alphabet,StringSubstr(text,2*i,1));
      int b=StringFind(alphabet,StringSubstr(text,2*i+1,1));
      if(a<0 || b<0)return false;
      raw[offset+i]=(uchar)(16*a+b);
   }
   return true;
}
int PipeModes086(const long h,Private086 &p)
{
   int reason=Before086(p);if(reason!=0)return reason;
   uint mode=3;bool ok=kernel32::SetNamedPipeHandleState(h,mode,0,0)!=0;
   uint error=ok?0:kernel32::GetLastError();
   reason=Guard086(p);if(reason!=0)return reason;if(!ok || error!=0)return 23;
   uint flags=0,out_bytes=0,in_bytes=0,maximum=0,state=0,instances=0;
   reason=Before086(p);if(reason!=0)return reason;
   ok=kernel32::GetNamedPipeInfo(h,flags,out_bytes,in_bytes,maximum)!=0;
   error=ok?0:kernel32::GetLastError();reason=Guard086(p);if(reason!=0)return reason;
   if(!ok || error!=0 || flags!=4 || maximum!=1)return 23;
   reason=Before086(p);if(reason!=0)return reason;
   ok=kernel32::GetNamedPipeHandleStateW(h,state,instances,0,0,0,0)!=0;
   error=ok?0:kernel32::GetLastError();reason=Guard086(p);if(reason!=0)return reason;
   return ok && error==0 && state==3 && instances==1?0:23;
}
int Receive086(const long h,uchar &raw[],Private086 &p,bool &empty)
{
   empty=false;int reason=Before086(p);if(reason!=0)return reason;
   uint count=0;bool ok=kernel32::ReadFile(h,raw,145,count,0)!=0;
   uint error=ok?0:kernel32::GetLastError();reason=Guard086(p);if(reason!=0)return reason;
   if(!ok && error==232 && count==0){empty=true;return 0;}
   return ok && error==0 && count==144?0:24;
}
int Send086(const long h,uchar &raw[],Private086 &p)
{
   int reason=Before086(p);if(reason!=0)return reason;
   uint count=0;bool ok=kernel32::WriteFile(h,raw,144,count,0)!=0;
   uint error=ok?0:kernel32::GetLastError();reason=Guard086(p);if(reason!=0)return reason;
   // TRUE/zero bytes in nonwaiting message mode means backpressure: no retry.
   return ok && error==0 && count==144?0:24;
}
int Property086(const int h,const bool position,Private086 &p,const long expected)
{
   int reason=Before086(p);if(reason!=0)return reason;
   ResetLastError();ulong v=position?FileTell(h):FileSize(h);int error=::GetLastError();
   reason=Guard086(p);if(reason!=0)return reason;
   return error==0 && v==(ulong)expected?0:23;
}
int Synthetic086(const string folder,Private086 &p,Status086 &r,int &h)
{
   int reason=Before086(p);if(reason!=0)return reason;
   r.opens++;ResetLastError();h=FileOpen(folder+"\\synthetic.bin",FILE_READ|FILE_BIN|FILE_SHARE_READ);int error=::GetLastError();
   if(h!=INVALID_HANDLE && error==0)r.hold_start=(long)GetTickCount64();
   reason=Guard086(p);if(reason!=0)return reason;
   if(h==INVALID_HANDLE || error!=0)return 22;
   reason=Property086(h,false,p,84);if(reason!=0)return reason;
   reason=Property086(h,true,p,0);if(reason!=0)return reason;
   reason=Before086(p);if(reason!=0)return reason;
   uchar raw[84];r.reads++;ResetLastError();uint count=FileReadArray(h,raw,0,84);error=::GetLastError();
   reason=Guard086(p);if(reason!=0)return reason;
   if(error!=0 || count!=84)return 24;
   for(int i=0;i<84;i++)if(raw[i]!=(uchar)((17*i+29)%256))return 24;
   reason=Property086(h,false,p,84);if(reason!=0)return reason;
   return Property086(h,true,p,84);
}
void OnStart()
{
   Status086 r;r.reason=17;r.requests=0;r.responses=0;r.opens=0;r.reads=0;r.closes=0;r.hold_start=0;r.hold_end=0;
   // No account/clock/file/pipe API before this default-off branch.
   if(!ReadSyntheticEvidence086){Report086(r);return;}
   uchar prefix[104];for(int i=0;i<104;i++)prefix[i]=0;
   string magic="FXDL086S";for(int i=0;i<8;i++)prefix[i]=(uchar)StringGetCharacter(magic,i);
   bool bound=Hex086(PHASE086,16,prefix,8) && Hex086(SourceContract086,32,prefix,24) &&
      Hex086(CandidateArtifact086,32,prefix,56) && Hex086(PrivateEpisode086,16,prefix,88);
   bool nonzero=false;for(int i=88;i<104;i++)if(prefix[i]!=0)nonzero=true;
   if(!bound || !nonzero){r.reason=27;Report086(r);return;}
   if(!_IsX64 || !MQLInfoInteger(MQL_DLLS_ALLOWED)){r.reason=30;Report086(r);return;}
   Private086 p;p.identified=false;p.login=0;p.build=0;p.server="";p.path="";p.data="";p.guards=0;p.io=0;
   p.first_boot=GetTickCount64();p.last_boot=p.first_boot;p.first_us=GetMicrosecondCount();p.last_us=p.first_us;
   p.first_utc=TimeGMT();p.last_utc=p.first_utc;
   long pipe=-1;int reader=INVALID_HANDLE;long deadline=0,release=0;bool ready=false,released=false,holding_seen=false,complete=false;
   string folder="ForexDemoSynchronization086-"+PHASE086+"-"+PrivateEpisode086;
   do
   {
      r.reason=Before086(p);if(r.reason!=0)break;
      r.opens++;pipe=kernel32::CreateFileW("\\\\.\\pipe\\"+folder,0xC0000000,0,0,3,0,0);
      int error=pipe==-1?(int)kernel32::GetLastError():0;
      r.reason=Guard086(p);if(r.reason!=0)break;
      if(pipe==-1 || error!=0){r.reason=22;break;}
      r.reason=PipeModes086(pipe,p);if(r.reason!=0)break;
      int sequence=0;
      for(int poll=0;poll<512;poll++)
      {
         // Own clock close has priority BEFORE every pipe read or empty wait.
         r.reason=Guard086(p);if(r.reason!=0)break;
         long now=(long)GetTickCount64();
         if(deadline>0 && now>=deadline){r.reason=21;break;}
         if(released && reader!=INVALID_HANDLE && CloseAction085(now,release,r.hold_start)!=0)
         {
            r.reason=Property086(reader,false,p,84);if(r.reason!=0)break;
            r.reason=Property086(reader,true,p,84);if(r.reason!=0)break;
            r.reason=Before086(p);if(r.reason!=0)break;
            r.closes++;ResetLastError();FileClose(reader);reader=INVALID_HANDLE;error=::GetLastError();
            r.hold_end=(long)GetTickCount64();r.reason=Guard086(p);if(r.reason!=0)break;
            if(error!=0 || CloseAction085(r.hold_end,release,r.hold_start)!=1){r.reason=25;break;}
         }
         uchar raw[145];bool empty=false;
         r.reason=Receive086(pipe,raw,p,empty);if(r.reason!=0)break;
         if(empty){Sleep(100);continue;}
         if(++sequence>64){r.reason=21;break;}r.requests++;
         now=(long)GetTickCount64();int kind=(int)raw[108];
         if(sequence==1)
         {
            deadline=Number084(raw,120,8);
            if(kind!=1 || deadline<=now || deadline>now+60000){r.reason=28;break;}
         }
         Wire084 request;
         r.reason=DecodeWire084(raw,144,prefix,kind,sequence,now,deadline,release,-1,request,true);
         if(r.reason!=0 || request.kind==5 || request.start!=0 || request.end!=0){r.reason=28;break;}
         Wire084 reply;reply.kind=kind;reply.sequence=sequence;reply.deadline=deadline;reply.start=0;reply.end=0;
         if(kind==1 && !ready && !released){ready=true;}
         else if(kind==2 && ready && !released)
         {
            released=true;release=request.issued;
            r.reason=Synthetic086(folder,p,r,reader);if(r.reason!=0)break;
            if(r.hold_start<release || r.hold_start>release+10000){r.reason=29;break;}
            // Release has no response. Its attempt is spent; no restart/retry.
            continue;
         }
         else if(kind==3 && released && !holding_seen && reader!=INVALID_HANDLE && r.hold_end==0)
         {
            holding_seen=true;reply.start=r.hold_start;
         }
         else if(kind==4 && released && holding_seen)
         {
            if(r.hold_end==0){reply.kind=5;}
            else
            {
               if(reader!=INVALID_HANDLE || CloseAction085(r.hold_end,release,r.hold_start)!=1){r.reason=25;break;}
               reply.start=r.hold_start;reply.end=r.hold_end;complete=true;
            }
         }
         else{r.reason=28;break;}
         // Produced after the request and any actual hold/close operation.
         reply.issued=(long)GetTickCount64();
         r.reason=SynchronizationWindow083(reply.kind==5?1:reply.kind,reply.issued,deadline,
            reply.start,reply.end,reply.issued,deadline,release);if(r.reason!=0)break;
         EncodeWire084(raw,prefix,reply);r.responses++;r.reason=Send086(pipe,raw,p);if(r.reason!=0)break;
         if(complete)break;
      }
      if(r.reason==0 && !complete)r.reason=21;
   }while(false);
   // Always attempt each acquired close once, including after a failed guard.
   if(reader!=INVALID_HANDLE){r.closes++;ResetLastError();FileClose(reader);reader=INVALID_HANDLE;if(::GetLastError()!=0 && r.reason==0)r.reason=25;}
   if(pipe!=-1){int before=Guard086(p);r.closes++;
      long owned=pipe;pipe=-1;bool ok=kernel32::CloseHandle(owned)!=0;
      int error=ok?0:(int)kernel32::GetLastError();int after=Guard086(p);
      if(r.reason==0 && (before!=0 || after!=0 || error!=0))r.reason=25;}
   Report086(r);
}
