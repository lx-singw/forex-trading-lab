// Test prelude/implementation for the Python-generated port of the actual MQL
// reader. No Windows/MT5/DLL calls. Native ABI and MQL compilation NOT proven.
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <string>
using uchar=unsigned char;
using uint=unsigned int;
using string=std::string;
using ulong=unsigned long;
using datetime=long;
static_assert(sizeof(long)==8 && sizeof(uint)==4);
#define FXDL084_CPP
const int ACCOUNT_TRADE_MODE_DEMO=0,INVALID_HANDLE=-1;
enum {TERMINAL_CONNECTED,TERMINAL_TRADE_ALLOWED,TERMINAL_BUILD,TERMINAL_PATH,TERMINAL_DATA_PATH,
 MQL_TESTER,MQL_DLLS_ALLOWED,ACCOUNT_TRADE_MODE,ACCOUNT_CURRENCY,ACCOUNT_LOGIN,ACCOUNT_SERVER,
 SYMBOL_VISIBLE,SYMBOL_CURRENCY_BASE,SYMBOL_CURRENCY_PROFIT,TIME_DATE};
const int FILE_READ=1,FILE_BIN=2,FILE_SHARE_READ=4;
const string _Symbol="EURUSD";const bool _IsX64=true;
ulong boot=100000;int mql_error=0,mode=0,config=0,account_calls=0,native_calls=0,reader_closes=0,pipe_closes=0;
long reader_opened=0,reader_closed=0;int reader_position=0,emitted=0;
ulong GetTickCount64(){return boot;}
ulong GetMicrosecondCount(){return boot*1000;}
datetime TimeGMT(){return 1791460800+(long)(boot-100000)/1000;}
string TimeToString(datetime,int){return "2026.10.08";}
bool IsStopped(){return false;}
void ResetLastError(){mql_error=0;}
int GetLastError(){return mql_error;}
long TerminalInfoInteger(int k){return k==TERMINAL_CONNECTED?1:k==TERMINAL_BUILD?6244:0;}
string TerminalInfoString(int k){return k==TERMINAL_PATH?"C:\\terminal":"C:\\private-data";}
long MQLInfoInteger(int k){return k==MQL_DLLS_ALLOWED?1:0;}
long AccountInfoInteger(int k){++account_calls;return k==ACCOUNT_TRADE_MODE?mode:123;}
string AccountInfoString(int k){return k==ACCOUNT_CURRENCY?"USD":"private-server";}
long SymbolInfoInteger(const string&,int){return 1;}
string SymbolInfoString(const string&,int k){return k==SYMBOL_CURRENCY_BASE?"EUR":"USD";}
int StringLen(const string&s){return (int)s.size();}
string StringSubstr(const string&s,int p,int n){return s.substr(p,n);}
int StringFind(const string&s,const string&v){auto p=s.find(v);return p==string::npos?-1:(int)p;}
int StringGetCharacter(const string&s,int p){return s[p];}
void Sleep(int ms){boot+=ms;}
int FileOpen(const string&,int){boot+=5;reader_opened=(long)boot;return 7;}
ulong FileTell(int){return reader_position;}
ulong FileSize(int){return 84;}
uint FileReadArray(int,uchar *raw,int,uint n){for(uint i=0;i<n;i++)raw[i]=(uchar)((17*i+29)%256);reader_position=84;return n;}
void FileClose(int){++reader_closes;reader_closed=(long)boot;if(config==4)mql_error=5;}
void PrintFormat(const char*,const string&,int reason,int requests,int responses,int opens,int reads,int closes,long start,long end)
{std::cout<<reason<<" "<<requests<<" "<<responses<<" "<<opens<<" "<<reads<<" "<<closes<<" "<<start<<" "<<end<<"\n";}
namespace kernel32 {
long CreateFileW(string,uint,uint,long,uint,uint,long);
int SetNamedPipeHandleState(long,uint&,long,long);
int GetNamedPipeInfo(long,uint&,uint&,uint&,uint&);
int GetNamedPipeHandleStateW(long,uint&,uint&,long,long,long,uint);
int ReadFile(long,uchar*,uint,uint&,long);
int WriteFile(long,uchar*,uint,uint&,long);
int CloseHandle(long);
uint GetLastError();
}
// Generated MQL source is inserted here by the test, with property/input/array
// syntax translated for C++; actual reader body/guards/control flow retained.
// FXDL086_INSERT
namespace kernel32 {
uint err=0;
long CreateFileW(string name,uint access,uint share,long security,uint creation,uint flags,long templ)
{++native_calls;if(name.find("\\\\.\\pipe\\ForexDemoSynchronization086-")!=0 || access!=0xC0000000 || share!=0 || creation!=3)std::abort();return 99;}
int SetNamedPipeHandleState(long,uint&m,long,long){++native_calls;return m==3;}
int GetNamedPipeInfo(long,uint&f,uint&o,uint&i,uint&m){++native_calls;f=4;o=i=1024;m=1;return 1;}
int GetNamedPipeHandleStateW(long,uint&s,uint&i,long,long,long,uint){++native_calls;s=3;i=1;return 1;}
int ReadFile(long,uchar*raw,uint size,uint&count,long)
{
 ++native_calls;if(size!=145)std::abort();
 int kind=emitted<3?emitted+1:4;
 if(emitted>=3 && (config==1 || boot<(ulong)reader_opened+30251)){count=0;err=232;return 0;}
 uchar prefix[104]={0};string magic="FXDL086S";
 for(int i=0;i<8;i++)prefix[i]=(uchar)magic[i];
 Hex086(PHASE086,16,prefix,8);Hex086(SourceContract086,32,prefix,24);
 Hex086(CandidateArtifact086,32,prefix,56);Hex086(PrivateEpisode086,16,prefix,88);
 Wire084 w={kind,++emitted,(long)boot,160000,0,0};EncodeWire084(raw,prefix,w);count=144;err=0;return 1;
}
int WriteFile(long,uchar*,uint size,uint&count,long)
{++native_calls;count=config==2?0:size;err=0;return 1;}
int CloseHandle(long){++native_calls;++pipe_closes;return 1;}
uint GetLastError(){return err;}
}
int main(int argc,char**argv)
{
 config=argc>1?std::atoi(argv[1]):0;mode=config==3?1:0;
 SourceContract086=string(64,'a');CandidateArtifact086=string(64,'b');PrivateEpisode086=string(32,'1');
 ReadSyntheticEvidence086=config!=5;OnStart();
 std::cout<<"stats "<<native_calls<<" "<<account_calls<<" "<<reader_closes<<" "<<pipe_closes<<" "<<reader_opened<<" "<<reader_closed<<"\n";
}
