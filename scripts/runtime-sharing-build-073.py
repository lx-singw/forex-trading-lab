"""One hidden source-bound compiler process. Never attaches MT5 or an SDK."""
from datetime import datetime,timezone
import json
from itertools import islice
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forex_demo_lab.sharing_build_073 import *
from forex_demo_lab.native_compiler_042 import module_environment


def metadata(shell,budget,policy,cleanup=False):
    if cleanup:
        if budget.counts['metadata_calls']>=LIMITS['metadata_calls']:raise BuildRejected('budget_rejected')
        budget.counts['metadata_calls']+=1
    else:budget.consume('metadata_calls')
    text=r"""$ErrorActionPreference='Stop'
$paths=@('C:\Program Files\MetaTrader 5\terminal64.exe','C:\Program Files\MetaTrader 5\metaeditor64.exe')
$signatures=@($paths | ForEach-Object { Get-AuthenticodeSignature -LiteralPath $_ })
$valid=@($signatures | Where-Object { $_.Status.ToString() -ne 'Valid' -or $null -eq $_.SignerCertificate -or $_.SignerCertificate.Subject -notmatch 'MetaQuotes' }).Count -eq 0
ConvertTo-Json -Compress @{policy=(Get-ExecutionPolicy).ToString();editor_processes=@(Get-Process metaeditor64 -ErrorAction SilentlyContinue).Count;
terminal_build=(Get-Item -LiteralPath $paths[0]).VersionInfo.FileBuildPart;editor_build=(Get-Item -LiteralPath $paths[1]).VersionInfo.FileBuildPart;valid_signatures=$valid}
"""
    result=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-Command',text],
        env=module_environment(shell),capture_output=True,text=True,timeout=15)
    if not cleanup:budget.check()
    if result.returncode!=0:raise BuildRejected('metadata_rejected')
    return metadata073(json.loads(result.stdout),policy)


def hidden(command,editor,timeout):
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    return subprocess.run(command,executable=str(editor),shell=False,capture_output=True,text=True,timeout=timeout,
        startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)


def run():
    if os.name!='nt':raise BuildRejected('metadata_rejected')
    api=runpy.run_path(str(ROOT/'scripts/sharing-build-073.py'))
    sha,sealed,write,bound=(api[k] for k in ('sha','sealed','write','bound'))
    l=api['verify']();checks=sealed(api['CHECKS']);auth=sealed(api['AUTH'])
    assert checks['checker_passed'] and checks['ledger_sha256']==sha(api['LEDGER'])
    assert auth==api['authorization_value'](l) and datetime.now(timezone.utc).date().isoformat()==DATE
    assert sha(Path(sys.executable))==l['python_sha256']
    started=ROOT/'reports/sharing-build-073-started.json';output=ROOT/'reports/sharing-build-073-native.json'
    assert not output.exists()
    b=Budget073(lambda:(time.time_ns()//1000000,time.monotonic_ns()))
    # Exclusive durable marker consumes the one attempt before staging/launch.
    reserve_build073(started,dict(build_reservation_consumed=True,ledger_sha256=sha(api['LEDGER']),
        authorization_sha256=sha(api['AUTH']),maximum_compiler_invocations=1,phase=BUILD_PHASE,orders_available=False))
    directory=None;stage='preflight';trace=[];reason=None;record=None;before=after=None;exit_code=None
    process_completed=False;timeout_owned_process_waited=False;outputs={};log_summary=None
    def enter(name):
        nonlocal stage
        if name not in STAGES or len(trace)>=8:raise BuildRejected('budget_rejected')
        stage=name;trace.append(dict(stage=name,completed=False));b.check()
    def done():trace[-1]['completed']=True
    def images():
        for key in ('terminal','editor','shell','python'):
            if read_bound073(bound(l[key+'_path']),b,136314880)['sha256']!=l[key+'_sha256']:
                raise BuildRejected('binding_rejected')
    try:
        enter('preflight');images();done()
        enter('metadata_before');before=metadata(bound(l['shell_path']),b,l['execution_policy']);done()
        enter('stage');root=Path(l['build_root']);directory=root/('compiler073-'+uuid.uuid4().hex)
        inputs={n:ROOT/n for n in SOURCE_INPUTS}
        stage073(inputs,l['source_contract']['input_bindings'],directory,root,b);done()
        enter('launch_guard');images()
        for n,h in l['source_contract']['input_bindings'].items():
            if read_bound073(ROOT/n,b)['sha256']!=h or read_bound073(directory/Path(n).name,b)['sha256']!=h:
                raise BuildRejected('binding_rejected')
        metadata(bound(l['shell_path']),b,l['execution_policy']);done()
        enter('compiler')
        try:
            exit_code=compile_once073(hidden,bound(l['editor_path']),directory,b);process_completed=True
        except subprocess.TimeoutExpired:
            # subprocess.run kills and waits its owned child on timeout. This
            # does not prove absence of descendants; final metadata must do so.
            timeout_owned_process_waited=True;raise BuildRejected('compiler_timeout') from None
        done()
        enter('outputs')
        allowed={Path(n).name for n in SOURCE_INPUTS}|{ARTIFACT,'compile.log'}
        paths=list(islice(directory.iterdir(),7))
        if len(paths)>6 or any(p.name not in allowed for p in paths):raise BuildRejected('evidence_rejected')
        values={}
        for p in paths:
            v=read_bound073(p,b,collect=p.name=='compile.log');values[p.name]=v
            outputs[api['external_name'](str(p))]=v['sha256']
        for n,h in l['source_contract']['input_bindings'].items():
            if values[Path(n).name]['sha256']!=h:raise BuildRejected('binding_rejected')
        log_text=values['compile.log']['raw'].decode('utf-16',errors='strict')
        record=build_record073(l['source_contract'],exit_code,log_text,values[ARTIFACT],l['editor_sha256'],l['terminal_sha256'])
        log_summary=dict(errors=record['errors'],warnings=record['warnings']);done()
    except BuildRejected as error:reason=error.code
    except (Exception,KeyboardInterrupt):reason='unexpected_failure'
    stopped_stage=stage if reason else None
    # A failed budget/date never suppresses a bounded final editor/policy query.
    try:
        stage='metadata_after';trace.append(dict(stage=stage,completed=False))
        after=metadata(bound(l['shell_path']),b,l['execution_policy'],cleanup=True)
        trace[-1]['completed']=True
    except (Exception,KeyboardInterrupt):
        reason=reason or 'metadata_rejected';stopped_stage=stopped_stage or 'metadata_after'
    try:
        enter('final_audit');images()
        if after is None or before is None or before!=after or record is None or reason:raise BuildRejected('evidence_rejected')
        for n,h in l['source_contract']['input_bindings'].items():
            if read_bound073(ROOT/n,b)['sha256']!=h:raise BuildRejected('binding_rejected')
        done()
    except BuildRejected as error:reason=reason or error.code;stopped_stage=stopped_stage or 'final_audit'
    except (Exception,KeyboardInterrupt):reason=reason or 'unexpected_failure';stopped_stage=stopped_stage or 'final_audit'
    completed=reason is None and record is not None and process_completed and after==before
    write(output,dict(completed=completed,compiled=completed,stop_reason=reason,stopped_stage=stopped_stage,
        ledger_sha256=sha(api['LEDGER']),authorization_sha256=sha(api['AUTH']),started_sha256=sha(started),
        stage_trace=trace,counts=dict(b.counts),build_record=record,output_bindings=outputs,
        metadata_before=before,metadata_after=after,compiler_exit_code=exit_code,compiler_process_completed=process_completed,
        timeout_owned_process_waited=timeout_owned_process_waited,owned_compiler_absent_after=after is not None,
        clean_log_summary=log_summary,execution_policy_changed=False,source_phase=PHASE,build_phase=BUILD_PHASE,
        mt5_runtime_invocations=0,sdk_connections=0,terminal_deployments=0,terminal_log_content_reads=0,
        market_reads=0,orders=0,receipt_permissions=0,orders_available=False,native_mql_verified=False,
        native_publication_verified=False,fresh_performance_eligible=False,annual_eligible=False))
    print(json.dumps(dict(completed=completed,compiler_invocations=b.counts['compiler_invocations'],
        exit_code=exit_code,clean_log_summary=log_summary,stop_reason=reason,stopped_stage=stopped_stage)))


if __name__=='__main__':run()
