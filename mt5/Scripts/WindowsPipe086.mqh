// Win64 DLL ABI source only. Early imports may load kernel32 even when disabled.
// No flush/seek/WaitNamedPipe or overlapped operation. Mode is queried explicitly.
#ifndef FXDL_WINDOWS_PIPE086_MQH
#define FXDL_WINDOWS_PIPE086_MQH
#import "kernel32.dll"
long CreateFileW(string name,uint access,uint share,long security,uint creation,uint flags,long template_file);
int SetNamedPipeHandleState(long handle,uint &mode,long collection,long timeout);
int GetNamedPipeInfo(long handle,uint &flags,uint &out_bytes,uint &in_bytes,uint &maximum);
int GetNamedPipeHandleStateW(long handle,uint &state,uint &instances,long collection,long timeout,long user,uint user_size);
int ReadFile(long handle,uchar &buffer[],uint bytes,uint &count,long overlapped);
int WriteFile(long handle,uchar &buffer[],uint bytes,uint &count,long overlapped);
int CloseHandle(long handle);
uint GetLastError();
#import
#endif
